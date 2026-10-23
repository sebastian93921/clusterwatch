# DGX Spark dual-node status dashboard (stdlib only). Port 8090.
# /   -> HTML page (English, SVG graphs)
# /data -> aggregated JSON
import json
import os
import yaml
import re
import threading
import time
import urllib.request
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

# ---- configuration -----------------------------------------------------------
# Every host / engine / history setting is loaded from config.yaml (see README.md).
# Nothing below is hardcoded: edit config.yaml, then restart the service.
CFG_PATH = os.environ.get("DGXDASH_CONFIG") or os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "config.yaml")

DEFAULTS = {
    "server": {"bind": "0.0.0.0", "port": 8090, "refresh_seconds": 5,
               "page_title": "DGX Spark cluster · TP=2"},
    "hosts": [],
    "llm_engine": {"base_url": "", "metrics_path": "/metrics", "health_path": "/health",
                   "models_path": "/v1/models", "model": None,
                   "context_window_fallback": 500000, "scrape_interval_s": 0.8,
                   "timeout_s": 5, "enabled": True},
    "comfyui": {"base_url": "", "system_stats_path": "/system_stats", "queue_path": "/queue",
                "cache_seconds": 30, "enabled": True},
    "history": {"peaks_window_s": 3600, "short_samples": 72,
                "short_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "dash_hist.json"),
                "long_interval_s": 60, "long_retention_minutes": 10080,
                "long_path": os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_long.json")},
    "thresholds": {"soc_hot_c": 85, "soc_crit_c": 95, "nvme_hot_c": 70, "nvme_crit_c": 80},
}


def _merge(base, over):
    out = dict(base)
    for k, v in (over or {}).items():
        out[k] = _merge(base[k], v) if isinstance(base.get(k), dict) and isinstance(v, dict) else v
    return out


def load_config(path=CFG_PATH):
    try:
        with open(path) as fh:
            raw = yaml.safe_load(fh) or {}
    except Exception as exc:
        print(f"[config] cannot read {path}: {exc} — using defaults", flush=True)
        raw = {}
    cfg = _merge(DEFAULTS, raw)
    cfg["_path"] = path
    return cfg


CFG = load_config()
SRV = CFG["server"]
ENG_CFG = CFG["llm_engine"]
COMFY_CFG = CFG["comfyui"]
HIST_CFG = CFG["history"]
THR = CFG["thresholds"]

HOSTS = [h for h in (CFG.get("hosts") or [])
         if h.get("enabled", True) and h.get("node_exporter") and h.get("key")]
NODE_ORDER = [h["key"] for h in HOSTS]
NODES = {h["key"]: h["node_exporter"] for h in HOSTS}
NODE_META = {h["key"]: {"label": h.get("label") or h["key"], "role": h.get("role"),
                        "accent": h.get("accent") or "#5ec8ff"} for h in HOSTS}

ENGINE_BASE = (ENG_CFG.get("base_url") or "").rstrip("/")
ENGINE = (ENGINE_BASE + (ENG_CFG.get("metrics_path") or "/metrics")) if ENGINE_BASE else ""
ENGINE_ENABLED = bool(ENG_CFG.get("enabled", True)) and bool(ENGINE_BASE)
# TensorFold exposes no context_length / pool size. Measured empirically
# (kv_cache_usage_ratio = stream tokens / context window) ~500k. Re-run
# ctx_probe.py after a model swap; /health context_length wins when present.
CTX_WINDOW_FALLBACK = int(ENG_CFG.get("context_window_fallback") or 500000)
SCRAPE_GAP = float(ENG_CFG.get("scrape_interval_s") or 0.8)
HTTP_TIMEOUT = float(ENG_CFG.get("timeout_s") or 5)


def fetch(url):
    try:
        with urllib.request.urlopen(url, timeout=HTTP_TIMEOUT) as r:
            return r.read().decode()
    except Exception:
        return ""


def parse(txt):
    out = {}
    for line in txt.splitlines():
        if not line or line.startswith("#"):
            continue
        m = re.match(r"([^\s{]+)(?:\{(.*?)\})?\s+(\S+)", line)
        if not m:
            continue
        name, labels, val = m.group(1), m.group(2) or "", m.group(3)
        try:
            f = float(val)
        except ValueError:
            continue
        out.setdefault(name, []).append((labels, f))
    return out


def first(m, name, **match):
    for labels, val in m.get(name, []):
        if all(f'{k}="{v}"' in labels for k, v in match.items()):
            return val
    return None


def summ(m, name, **match):
    t = 0.0
    for labels, val in m.get(name, []):
        if all(f'{k}="{v}"' in labels for k, v in match.items()):
            t += val
    return t


def make(m1, m2):
    now = time.time()
    mem_t = first(m2, "node_memory_MemTotal_bytes") or 0
    mem_a = first(m2, "node_memory_MemAvailable_bytes") or 0
    boot = first(m2, "node_boot_time_seconds")
    temps = {}
    for labels, val in m2.get("node_thermal_zone_temp", []):
        z = re.search(r'zone="([^"]*)"', labels)
        ty = re.search(r'type="([^"]*)"', labels)
        if z:
            temps[(ty.group(1) if ty else "zone") + z.group(1)] = val
    nvme = {}
    crits = {}
    for labels, val in m2.get("node_hwmon_temp_celsius", []):
        c = re.search(r'chip="([^"]*)"', labels)
        s = re.search(r'sensor="([^"]*)"', labels)
        if not (c and s):
            continue
        chip = c.group(1)
        if "nvme" in chip:
            nvme[s.group(1)] = val
        elif chip.startswith(("0000:", "0002:")):
            # GPU/SoC package sensors on the PCIe root complexes
            temps["gpupkg" + chip.split("_")[-1]] = val
        elif chip.startswith("pci0000:"):
            # x86 CPU package temp (coretemp/PCH thermal subtree)
            temps["cpu"] = val
        elif chip.startswith("ieee80211"):
            temps["wifi"] = val
    for labels, val in m2.get("node_hwmon_temp_crit_celsius", []):
        c = re.search(r'chip="([^"]*)"', labels)
        if not c:
            continue
        chip = c.group(1)
        if "nvme" in chip:
            crits["nvme"] = min(crits.get("nvme", 999), val)
        elif chip.startswith(("0000:", "0002:")):
            crits["gpupkg"] = min(crits.get("gpupkg", 999), val)
    disk = {}
    for labels, val in m2.get("node_filesystem_size_bytes", []):
        mp = re.search(r'mountpoint="([^"]*)"', labels)
        fst = re.search(r'fstype="([^"]*)"', labels)
        if mp and fst and fst.group(1) != "tmpfs" and mp.group(1) in ("/", "/home"):
            disk[mp.group(1)] = [None, val / 2**30]
    for labels, val in m2.get("node_filesystem_avail_bytes", []):
        mp = re.search(r'mountpoint="([^"]*)"', labels)
        if mp and mp.group(1) in disk:
            disk[mp.group(1)][0] = disk[mp.group(1)][1] - val / 2**30
    d_idle = summ(m2, "node_cpu_seconds_total", mode="idle") - summ(m1, "node_cpu_seconds_total", mode="idle")
    d_tot = summ(m2, "node_cpu_seconds_total") - summ(m1, "node_cpu_seconds_total")
    cpus = len({l for l, _ in m2.get("node_cpu_seconds_total", []) if 'mode="idle"' in l})
    return {
        "load": [first(m2, "node_load1"), first(m2, "node_load5"), first(m2, "node_load15")],
        "cpu_pct": round(100 * (1 - d_idle / d_tot), 1) if d_tot > 0 else None,
        "cpu_cores": cpus,
        "mem_total_gb": round(mem_t / 2**30, 1),
        "mem_used_gb": round((mem_t - mem_a) / 2**30, 1),
        "mem_pct": round(100 * (mem_t - mem_a) / mem_t, 1) if mem_t else None,
        "temps": {k: round(v, 1) for k, v in temps.items()},
        "temp_max": round(max(temps.values()), 1) if temps else None,
        "nvme": {k: round(v, 1) for k, v in nvme.items()},
        "crit": dict(crits, soc=THR.get("soc_crit_c"),
                     nvme=crits.get("nvme") or THR.get("nvme_crit_c")),
        "disk": {k: [round(u, 1), round(t, 1)] for k, (u, t) in disk.items()},
        "uptime_h": round((now - boot) / 3600, 1) if boot else None,
        "net_rx_mb": round(summ(m2, "node_network_receive_bytes_total") / 2**20, 1),
    }


GPU_HOSTS = {h["key"]: (h.get("gpu") or {}).get("ssh") for h in HOSTS
             if (h.get("gpu") or {}).get("ssh")}
GPU_VIA = {h["key"]: (h.get("gpu") or {}).get("via") for h in HOSTS}

# SSH key used only for the optional nvidia-smi probe (HTTP-only design does not
# need it). Configurable so the repo is not tied to one user's home directory.
SSH_KEY = os.path.expanduser((CFG.get("ssh") or {}).get("key") or "~/.ssh/id_ed25519")


GPU_WARNED = set()


def gpu_view():
    # nvidia-smi on both DGX boxes. spark is reachable directly from here;
    # edge only accepts spark's key, so query it through the spark chain.
    out = {}
    for name, host in GPU_HOSTS.items():
        q = "utilization.gpu,utilization.memory,power.draw,clocks.sm,temperature.gpu"
        via = GPU_VIA.get(name)
        if via:
            cmd = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes",
                   "-o", "ConnectTimeout=5", via,
                   f"ssh -i ~/.ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=accept-new {host} 'nvidia-smi --query-gpu={q} --format=csv,noheader,nounits'"]
        else:
            cmd = ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes",
                   "-o", "ConnectTimeout=5", host, f"nvidia-smi --query-gpu={q} --format=csv,noheader,nounits"]
        try:
            import subprocess
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=12)
            line = r.stdout.strip().splitlines()[0]
            vals = [x.strip() for x in line.split(",")]
            out[name] = {"util_pct": int(vals[0]), "mem_bw_pct": int(vals[1]),
                         "power_w": float(vals[2]), "sm_mhz": int(vals[3]), "temp_c": float(vals[4])}
        except Exception as e:
            out[name] = None
            if name not in GPU_WARNED:
                GPU_WARNED.add(name)
                print(f"[gpu] nvidia-smi probe failed for {name} ({host}): "
                      f"{e.__class__.__name__}: {e} | key={SSH_KEY}", flush=True)
    return out


GPU_CACHE = {"t": 0.0, "v": {}}
GPU_LOCK = threading.Lock()


def gpu_view_cached():
    """nvidia-smi over SSH is slow, so cache it; TTL is configurable via ssh.gpu_cache_s."""
    if not GPU_HOSTS:
        return {}
    ttl = float((CFG.get("ssh") or {}).get("gpu_cache_s") or 15)
    with GPU_LOCK:
        if GPU_CACHE["v"] and time.time() - GPU_CACHE["t"] < ttl:
            return GPU_CACHE["v"]
        v = gpu_view()
        GPU_CACHE.update({"t": time.time(), "v": v})
        return v


def vllm_view(v1, v2, dt):
    m = v2
    g = lambda n: first(m, n) or 0
    # model identity: read live from /v1/models — root is the real checkpoint
    try:
        mm = json.loads(fetch(ENGINE_BASE + (ENG_CFG.get("models_path") or "/v1/models")))
        d0 = (mm.get("data") or [{}])[0]
        served, root = d0.get("id"), d0.get("root")
    except Exception:
        served = root = None
    itl_s, itl_c = g("vllm:inter_token_latency_seconds_sum"), g("vllm:inter_token_latency_seconds_count")
    ttft_s, ttft_c = g("vllm:time_to_first_token_seconds_sum"), g("vllm:time_to_first_token_seconds_count")
    drafts, acc, dtk = g("vllm:spec_decode_num_drafts_total"), g("vllm:spec_decode_num_accepted_tokens_total"), g("vllm:spec_decode_num_draft_tokens_total")
    hits, qrs = g("vllm:prefix_cache_hits_total"), g("vllm:prefix_cache_queries_total")
    cfg = {}
    for labels, _ in m.get("vllm:cache_config_info", []):
        cfg = dict(re.findall(r'(\w+)="([^"]*)"', labels))
    succ = {}
    for labels, val in m.get("vllm:request_success_total", []):
        r = re.search(r'finished_reason="([^"]*)"', labels)
        if r:
            succ[r.group(1)] = val
    itl_ms = round(1000 * itl_s / itl_c, 1) if itl_c else None
    # single-stream tok/s = window rate, not lifetime averages:
    #   Δgeneration_tokens / Δt, split per running request
    gen2 = g("vllm:generation_tokens_total")
    gen1 = first(v1, "vllm:generation_tokens_total") or 0
    run2 = g("vllm:num_requests_running")
    run1 = first(v1, "vllm:num_requests_running") or 0
    tps = None
    if dt > 0 and gen2 > gen1 and max(run1, run2) > 0:
        tps = round((gen2 - gen1) / dt / max(run1, run2), 1)
    return {
        "model": served or "?",
        "model_root": root or "?",
        "running": g("vllm:num_requests_running"),
        "waiting": g("vllm:num_requests_waiting"),
        "kv_pct": round(g("vllm:kv_cache_usage_perc") * 100, 2),
        "itl_ms": itl_ms,
        "tok_s": tps,
        "ttft_ms": round(1000 * ttft_s / ttft_c, 1) if ttft_c else None,
        "tok_per_step": round(1 + acc / drafts, 3) if drafts else None,
        "accept_rate": round(acc / dtk, 3) if dtk else None,
        "prefix_hit_pct": round(100 * hits / qrs, 1) if qrs else None,
        "prompt_tokens": g("vllm:prompt_tokens_total"),
        "gen_tokens": g("vllm:generation_tokens_total"),
        "requests_done": succ,
        "rss_mb": round(g("process_resident_memory_bytes") / 2**20, 1),
        "gpu_util": cfg.get("gpu_memory_utilization"),
        "kv_tokens": cfg.get("kv_cache_size_tokens"),
        "cache_dtype": cfg.get("cache_dtype"),
    }


# TensorFold's generation counter only advances when requests FINISH, so a raw
# Δ over one scrape window spikes when several complete together (bogus peaks).
# Anchor at idle->active transition, flush when load ends or every >=10 s.
TF_RATE = {"gen": None, "ts": None, "last": None, "active": False, "peak": 0}
# sparkDash-style live decode rate: finished-request tokens plus still-decoding
# tokens rises exactly with produced tokens, so the window diff is the real rate.
# /health's decode_tokens_per_second is smoothed and keeps reading nonzero while
# idle, so it is only a fallback.
TF_LIVE = {"sum": None, "ts": None, "last": None}


def _tf_live_rate(gen_total, gen_running):
    now = time.time()
    cur = (gen_total or 0) + (gen_running or 0)
    st = TF_LIVE
    if st["sum"] is None or cur < st["sum"]:      # first sample, or engine restart
        st.update(sum=cur, ts=now)
        return st["last"]
    dt = now - st["ts"]
    if dt >= 3:
        st["last"] = round((cur - st["sum"]) / dt, 1) if cur > st["sum"] else 0.0
        st.update(sum=cur, ts=now)
    return st["last"]


def _tf_tps(gen_now, running):
    now = time.time()
    st = TF_RATE
    g0, t0 = st["gen"], st["ts"]
    act = bool(running)
    if g0 is None or gen_now < g0:          # first sight, or engine restart reset
        st.update(gen=gen_now, ts=now, active=act, peak=running or 0)
        return st["last"]
    dt = now - t0
    st["peak"] = max(st["peak"], running or 0)
    emit = (st["active"] and not act) or (act and dt >= 10)
    if emit and dt > 0 and gen_now > g0:
        st["last"] = round((gen_now - g0) / dt / max(1, st["peak"] or 1), 1)
    if emit or not act:                      # re-anchor after flush and while idle
        st.update(gen=gen_now, ts=now, active=act, peak=running or 0)
    return st["last"]


def tensorfold_view(v1, v2, dt):
    m = v2
    g = lambda n: first(m, n) or 0
    try:
        h = json.loads(fetch(ENGINE_BASE + (ENG_CFG.get("health_path") or "/health")))
    except Exception:
        h = {}
    try:
        mm = json.loads(fetch(ENGINE.replace("/metrics", "/v1/models")))
        served = (mm.get("data") or [{}])[0].get("id")
    except Exception:
        served = None
    live = h.get("live") or {}
    mem = h.get("memory") or {}
    gen2 = g("tensorfold:generation_tokens_total")
    run2, run1 = g("tensorfold:requests_running"), first(v1, "tensorfold:requests_running") or 0
    # live decode rate from the engine's own counters (sparkDash method) — the sum of
    # finished-request tokens and still-decoding tokens rises exactly with produced
    # tokens, so its window diff is the real rate; 0 when idle, not a stale EMA.
    in_flight = g("tensorfold:generation_tokens_running")
    tps = _tf_live_rate(gen2, in_flight)
    if tps is None:
        live_tps = live.get("decode_tokens_per_second")
        tps = round(live_tps, 1) if isinstance(live_tps, (int, float)) and live_tps > 0 else None
    # ITL: per-output-token histogram (new) -> decode/complete (old)
    itl_s, itl_c = g("tensorfold:request_time_per_output_token_seconds_sum"), g("tensorfold:request_time_per_output_token_seconds_count")
    if itl_c:
        itl_ms = round(1000 * itl_s / itl_c, 1)
    else:
        dec_s = h.get("decode_seconds_total") or g("tensorfold:request_decode_seconds_sum")
        gen_tot = h.get("completion_tokens_total") or gen2
        itl_ms = round(1000 * dec_s / gen_tot, 1) if gen_tot else None
    ttft_s, ttft_c = g("tensorfold:time_to_first_token_seconds_sum"), g("tensorfold:time_to_first_token_seconds_count")
    drafted = h.get("drafted_total") or g("tensorfold:mtp_drafted_total")
    accepted = h.get("accepted_total") or g("tensorfold:mtp_accepted_total")
    rounds = h.get("rounds_total") or g("tensorfold:decode_rounds_total")
    prompt = h.get("prompt_tokens_total") or g("tensorfold:prompt_tokens_total")
    cached = h.get("cached_tokens_total") or 0
    pool, free = h.get("pool_tokens") or 0, h.get("pool_free_tokens") or 0
    kv_ratio = g("tensorfold:kv_cache_usage_ratio")
    st = h.get("streams") or {}
    if rounds and accepted:
        tok_step = round(1 + accepted / rounds, 3)   # 1 target token + accepted drafts per round
    elif rounds and drafted:
        tok_step = round(drafted / rounds, 3)
    else:
        tok_step = None
    if live:
        streams = (f"{live.get('connections', 0)} conn · waiting {live.get('waiting', 0)}"
                   f" · max {h.get('max_batch_size', '?')}" + (" · WARMING" if h.get("warming") else ""))
    else:
        streams = f"{st.get('decoding', 0)} dec · {st.get('prefilling', 0)} prefill · max {st.get('max', '?')}"
    e2e_c = g("tensorfold:e2e_request_latency_seconds_count")
    return {
        "engine": "TensorFold",
        "model": served or h.get("model") or "?",
        "model_root": None,
        "running": h.get("requests_running", g("tensorfold:requests_running")),
        "waiting": h.get("requests_waiting", g("tensorfold:requests_waiting")),
        "kv_pct": round(100 * kv_ratio, 2) if kv_ratio else (round(100 * (pool - free) / pool, 2) if pool else 0),
        "itl_ms": itl_ms,
        "tok_s": tps,
        "ttft_ms": round(1000 * ttft_s / ttft_c, 1) if ttft_c else None,
        "tok_per_step": tok_step,
        "accept_rate": round(accepted / drafted, 3) if drafted else None,
        "prefix_hit_pct": round(100 * cached / prompt, 1) if (prompt and cached) else None,
        "prompt_tokens": prompt,
        "gen_tokens": h.get("completion_tokens_total") or gen2,
        "requests_done": {"total": e2e_c or h.get("requests_total", 0)},
        "rss_mb": round(mem["active"] / 1048576, 1) if mem.get("active") else None,
        "gpu_util": None,
        "kv_tokens": None,
        "cache_dtype": None,
        "ctx_window": h.get("context_length") or CTX_WINDOW_FALLBACK,
        "max_streams": h.get("max_batch_size"),
        "kv_max_tokens": (h.get("context_length") or CTX_WINDOW_FALLBACK) * (h.get("max_batch_size") or 1),
        "streams": streams,
        "prefill_s": round(g("tensorfold:request_prefill_seconds_sum"), 1),
        "decode_s": round(g("tensorfold:request_decode_seconds_sum"), 1),
        "in_flight": g("tensorfold:generation_tokens_running"),
    }


def engine_view(v1, v2, dt):
    try:
        h = json.loads(fetch(ENGINE_BASE + (ENG_CFG.get("health_path") or "/health")))
    except Exception:
        h = {}
    # detect by metric namespace too: newer TensorFold builds dropped the
    # "backend" key from /health, so the old check alone silently fell back to vLLM
    is_tf = h.get("backend") == "tensorfold" or any(k.startswith("tensorfold:") for k in v1)
    if is_tf:
        return tensorfold_view(v1, v2, dt)
    v = vllm_view(v1, v2, dt)
    v["engine"] = "vLLM"
    return v


def build():
    keys = list(NODE_ORDER)
    s1 = {k: parse(fetch(NODES[k])) for k in keys}
    v1 = parse(fetch(ENGINE)) if ENGINE_ENABLED else {}
    ta = time.perf_counter()          # engine counters snapshot ~now (end of scrape 1)
    time.sleep(SCRAPE_GAP)
    s2 = {k: parse(fetch(NODES[k])) for k in keys}
    v2 = parse(fetch(ENGINE)) if ENGINE_ENABLED else {}
    tb = time.perf_counter()          # snapshot 2 (~now) -> dt = sleep + scrape latency
    # real elapsed time between the two metric snapshots (includes fetch latency)
    gp = gpu_view_cached()
    out = {"ts": round(time.time(), 1), "nodes": []}
    for k in keys:
        d = make(s1[k], s2[k])
        meta = NODE_META.get(k, {})
        d.update({"key": k, "label": meta.get("label"), "role": meta.get("role"),
                  "accent": meta.get("accent")})
        if gp.get(k):
            d["gpu"] = gp[k]
        out["nodes"].append(d)
        out[k] = d            # flat alias kept for cron jobs and older clients
    out["engine"] = engine_view(v1, v2, tb - ta) if ENGINE_ENABLED else {"engine": None, "enabled": False}
    return out


# ---- 1-hour peak tracker -----------------------------------------------------
# ring buffers of (ts, soc_temp_per_node, tok_s) sampled once per /data build;
# peaks are maxima over samples newer than 3600 s (falls back to all samples
# while the buffer is younger than 1 h).
PEAKS = {k: deque() for k in NODE_ORDER}
PEAKS["tok_s"] = deque()
PEAK_WINDOW = float(HIST_CFG.get("peaks_window_s") or 3600)
PEAK_LOCK = threading.Lock()


def _prune(q, now):
    while q and now - q[0][0] > PEAK_WINDOW:
        q.popleft()


def update_peaks(data):
    now = data["ts"]
    with PEAK_LOCK:
        for node in NODE_ORDER:
            d = data.get(node) or {}
            v = d.get("temp_max")
            q = PEAKS[node]
            if v is not None:
                q.append((now, v))
                _prune(q, now)
            # always expose the field: peak over retained window, None only if never seen
            d["temp_peak_1h"] = max(x for _, x in q) if q else None
        eng = data.get("engine") or {}
        tps = eng.get("tok_s")
        q = PEAKS["tok_s"]
        if tps is not None:
            q.append((now, tps))
            _prune(q, now)
        eng["tok_s_peak_1h"] = max(x for _, x in q) if q else None
        update_hist(eng)
    return data


# ---- rolling sample history (survives page reload AND service restart) -------
# The charts used to live only in browser memory, so every reload wiped them and
# an idle engine (tok_s None) left them stuck on "collecting…". Keep the last 72
# samples server-side on disk instead.
HIST_PATH = HIST_CFG.get("short_path") or "dash_hist.json"
HIST_MAX = int(HIST_CFG.get("short_samples") or 72)
HIST_LOCK = threading.Lock()
HIST_KEYS = (("tps", "tok_s"), ("itl", "itl_ms"), ("kv", "kv_pct"), ("acc", "accept_rate"))
try:
    with open(HIST_PATH) as _f:
        _raw = json.load(_f)
    HIST = {k: [x if isinstance(x, (int, float)) else None for x in (_raw.get(k) or [])][-HIST_MAX:]
            for k, _ in HIST_KEYS}
except Exception:
    HIST = {k: [] for k, _ in HIST_KEYS}


def update_hist(eng):
    """Append one sample per /data build and expose it to the page."""
    with HIST_LOCK:
        for key, field in HIST_KEYS:
            v = eng.get(field)
            if v is not None:
                try:
                    v = float(v)
                except (TypeError, ValueError):
                    v = None
            HIST[key].append(v)
            del HIST[key][:-HIST_MAX]
        try:
            tmp = HIST_PATH + ".tmp"
            with open(tmp, "w") as fh:
                json.dump(HIST, fh)
            os.replace(tmp, HIST_PATH)
        except Exception:
            pass
        eng["hist"] = {k: list(v) for k, v in HIST.items()}


# ---- long-range thermal sampler -------------------------------------------------
# The browser only keeps a short window, so a background thread samples the cluster
# once a minute and retains 7 days of minute resolution for the Thermal tab.
LONG_PATH = HIST_CFG.get("long_path") or "temp_long.json"
LONG = {"ts": []}
for _k in NODE_ORDER:
    LONG[_k] = []
    LONG[_k + "_nvme"] = []
    LONG[_k + "_cpu"] = []
LONG_MAX = int(HIST_CFG.get("long_retention_minutes") or 10080)
LONG_INTERVAL = float(HIST_CFG.get("long_interval_s") or 60)
LONG_LOCK = threading.Lock()


def _load_long():
    try:
        with open(LONG_PATH) as fh:
            d = json.load(fh)
        with LONG_LOCK:
            for k in LONG:
                LONG[k] = list(d.get(k, []))[-LONG_MAX:]
    except Exception:
        pass


def _save_long():
    tmp = LONG_PATH + ".tmp"
    try:
        with LONG_LOCK:
            snap = {k: list(v) for k, v in LONG.items()}
        with open(tmp, "w") as fh:
            json.dump(snap, fh)
        os.replace(tmp, LONG_PATH)
    except Exception:
        pass


def sampler():
    _load_long()
    while True:
        try:
            d = build()
            with LONG_LOCK:
                LONG["ts"].append(round(d["ts"]))
                for key in NODE_ORDER:
                    n = d.get(key) or {}
                    LONG[key].append(n.get("temp_max"))
                    nv = n.get("nvme") or {}
                    LONG[key + "_nvme"].append(max(nv.values()) if nv else None)
                    LONG[key + "_cpu"].append(n.get("cpu_pct"))
                for k in LONG:
                    if len(LONG[k]) > LONG_MAX:
                        del LONG[k][:-LONG_MAX]
            _save_long()
        except Exception:
            pass
        time.sleep(LONG_INTERVAL)


def hist_view(r):
    """Decimated, max-aggregated view of the long history (peaks survive downsampling)."""
    now = time.time()
    start = now - r
    step = 60 if r <= 86400 else 300
    keys = tuple(x for k in NODE_ORDER for x in (k, k + "_nvme"))
    with LONG_LOCK:
        ts = list(LONG["ts"])
        series = {k: list(LONG[k]) for k in keys}
    buckets = {}
    for i, t in enumerate(ts):
        if t < start:
            continue
        b = int((t - start) // step)
        cur = buckets.setdefault(b, {})
        for k in keys:
            v = series[k][i] if i < len(series[k]) else None
            if v is None:
                continue
            if k not in cur or v > cur[k]:
                cur[k] = v
    order = sorted(buckets)
    out = {"r": r, "step": step, "ts": [int(start + b * step + step / 2) for b in order]}
    for k in keys:
        out[k] = [buckets[b].get(k) for b in order]
    return out


COMFY = (COMFY_CFG.get("base_url") or "").rstrip("/")
COMFY_ON = bool(COMFY_CFG.get("enabled", True)) and bool(COMFY)
COMFY_TTL = float(COMFY_CFG.get("cache_seconds") or 30)


COMFY_CACHE = {"ts": 0.0, "val": None}


def comfy_view():
    if not COMFY_ON:
        return {"up": False, "enabled": False}
    if time.time() - COMFY_CACHE["ts"] < COMFY_TTL and COMFY_CACHE["val"] is not None:
        return COMFY_CACHE["val"]
    val = _comfy_probe()
    COMFY_CACHE.update(ts=time.time(), val=val)
    return val


def _comfy_probe():
    try:
        st = json.loads(fetch(COMFY + (COMFY_CFG.get("system_stats_path") or "/system_stats")))
    except Exception:
        return {"up": False}
    sysinfo = st.get("system") or {}
    out = {"up": True, "version": sysinfo.get("comfyui_version")}
    if sysinfo.get("ram_total"):
        out["ram_total"] = sysinfo["ram_total"]
        out["ram_used"] = sysinfo["ram_total"] - (sysinfo.get("ram_free") or 0)
    devs = st.get("devices") or []
    if devs:
        d0 = devs[0]
        out["vram_total"] = d0.get("vram_total")
        out["vram_used"] = (d0.get("vram_total") or 0) - (d0.get("vram_free") or 0)
        out["devices"] = ", ".join(str(x.get("name")) for x in devs)
    try:
        q = json.loads(fetch(COMFY + (COMFY_CFG.get("queue_path") or "/queue")))
        out["running"] = len(q.get("queue_running") or [])
        out["pending"] = len(q.get("queue_pending") or [])
    except Exception:
        pass
    return out

from dash_page import PAGE


class H(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?")[0] in ("/", "/index.html"):
            page = PAGE.replace("setInterval(up,5000)",
                                f"setInterval(up,{int(float(SRV.get('refresh_seconds') or 5) * 1000)})")
            if SRV.get("page_title"):
                page = page.replace("<title>DGX Spark cluster · TP=2</title>",
                                    f"<title>{SRV['page_title']}</title>")
            body, ctype = page.encode(), "text/html; charset=utf-8"
        elif self.path.startswith("/hist"):
            m = re.search(r"[?&]r=(\d+)", self.path)
            body, ctype = json.dumps(hist_view(int(m.group(1)) if m else 86400)).encode(), "application/json"
        else:
            data = update_peaks(build())
            data["comfy"] = comfy_view()
            body, ctype = json.dumps(data).encode(), "application/json"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    threading.Thread(target=sampler, daemon=True).start()
    print(f"[dgxdash] config={CFG_PATH} hosts={NODE_ORDER} engine={ENGINE if ENGINE_ENABLED else 'disabled'} "
          f"listening on {SRV.get('bind')}:{SRV.get('port')}", flush=True)
    ThreadingHTTPServer((SRV.get("bind") or "0.0.0.0", int(SRV.get("port") or 8090)), H).serve_forever()
