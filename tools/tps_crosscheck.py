#!/usr/bin/env python3
"""Cross-check the dashboard's single-stream tok/s against a real client stream.

Runs one streaming completion against vLLM while sampling the dashboard's
/data endpoint. Prints the client tok/s (usage.completion_tokens divided by
the stream span) and the dashboard samples taken mid-stream.

Pass criteria: dashboard tok_s sits within ~±20% of the client value while
running > 0, and reads null once the stream ends (running back to 0).
"""
import json
import os
import threading
import time
import urllib.request

def _engine_base():
    """Engine URL: $DGXDASH_ENGINE, else config.yaml next to the repo, else localhost."""
    env = os.environ.get("DGXDASH_ENGINE")
    if env:
        return env.rstrip("/")
    cfg = os.environ.get("DGXDASH_CONFIG") or os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config.yaml")
    try:
        import yaml
        with open(cfg) as f:
            base = ((yaml.safe_load(f) or {}).get("llm_engine") or {}).get("base_url") or ""
        if base:
            return base.rstrip("/")
    except Exception:
        pass
    return "http://127.0.0.1:8888"


VLLM = _engine_base()                              # inference engine (from config)
DASH = os.environ.get("DGXDASH_URL", "http://127.0.0.1:8090/data")  # this dashboard
PROMPT = "寫一篇800字關於香港街頭小食文化嘅深度文章。"
MAX_TOKENS = 1200
SAMPLES = 9
SAMPLE_EVERY = 1.5


def model_id():
    with urllib.request.urlopen(VLLM + "/v1/models", timeout=5) as r:
        return json.load(r)["data"][0]["id"]


def main():
    model = model_id()
    res = {"client_toks": None, "dash": []}

    def stream():
        body = {"model": model,
                "messages": [{"role": "user", "content": PROMPT}],
                "stream": True,
                "stream_options": {"include_usage": True},
                "max_tokens": MAX_TOKENS}
        req = urllib.request.Request(
            VLLM + "/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        first = last = None
        usage = None
        with urllib.request.urlopen(req, timeout=300) as r:
            for raw in r:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                payload = line[5:].strip()
                if payload == "[DONE]":
                    break
                try:
                    j = json.loads(payload)
                except Exception:
                    continue
                if j.get("usage"):
                    usage = j["usage"]
                if not (j.get("choices") or []):
                    continue
                ts = time.time()
                if first is None:
                    first = ts
                last = ts
        if usage and last and last > first:
            res["client_toks"] = round(usage["completion_tokens"] / (last - first), 1)

    th = threading.Thread(target=stream)
    th.start()
    for _ in range(SAMPLES):
        time.sleep(SAMPLE_EVERY)
        try:
            v = json.load(urllib.request.urlopen(DASH, timeout=25))["vllm"]
            res["dash"].append((v.get("tok_s"), v.get("running")))
        except Exception as e:
            res["dash"].append(f"err:{e}")
    th.join()
    print("model:", model)
    print("client tok/s (usage/duration):", res["client_toks"])
    print("dashboard (tok_s, running):", res["dash"])


if __name__ == "__main__":
    main()
