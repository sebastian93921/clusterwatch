PAGE = """<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>DGX Spark cluster · TP=2</title>
<style>
:root{
 --bg:#0a0c11;--panel:#11161f;--panel-2:#0d1219;--line:#222b37;--line-soft:rgba(255,255,255,.055);
 --ink:#eef3f9;--ink-dim:#8b98a8;--ink-faint:#5d6875;
 --a:#5ec8ff;--b:#5ee0b4;--c:#ffb45c;--d:#ff86ad;--v:#bda8ff;
 --hot:#ffb45c;--crit:#ff5f6d;--ok:#5ee0b4;
}
*{box-sizing:border-box}
html{background:var(--bg)}
body{margin:0;padding:30px 26px 48px;color:var(--ink);max-width:1420px;margin-inline:auto;
 font:400 13px/1.6 "Inter",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
 font-variant-numeric:tabular-nums;
 background:
  radial-gradient(1100px 520px at 8% -12%,rgba(94,200,255,.10),transparent 62%),
  radial-gradient(900px 460px at 96% -10%,rgba(189,168,255,.09),transparent 60%),
  var(--bg);
 -webkit-font-smoothing:antialiased}
header{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;
 padding-bottom:16px;margin-bottom:22px;border-bottom:1px solid var(--line-soft)}
.brand{display:flex;align-items:center;gap:12px;min-width:0}
.mark{width:30px;height:30px;border-radius:9px;flex:0 0 auto;
 background:linear-gradient(150deg,var(--a),var(--v));box-shadow:0 6px 18px rgba(94,200,255,.28);
 display:grid;place-items:center;font-size:15px;color:#0a0c11;font-weight:800}
h1{font-size:21px;font-weight:680;margin:0;letter-spacing:-.2px}
.sub{display:flex;align-items:center;gap:8px;margin-top:3px;flex-wrap:wrap}
.badge{font-size:11px;color:var(--b);border:1px solid rgba(94,224,180,.28);
 background:rgba(94,224,180,.08);padding:2.5px 10px;border-radius:999px;font-weight:600}
#ts{color:var(--ink-dim);font-size:11px}
.live{display:inline-flex;align-items:center;gap:6px;font-size:11px;color:var(--ink-dim)}
.live i{width:6px;height:6px;border-radius:50%;background:var(--ok);box-shadow:0 0 0 3px rgba(94,224,180,.16);
 animation:pulse 2.4s ease-in-out infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:.45}}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;align-items:stretch}
.card{background:linear-gradient(178deg,rgba(255,255,255,.055),rgba(255,255,255,.018) 42%,rgba(0,0,0,.16));
 border:1px solid var(--line);border-radius:16px;padding:17px 18px 15px;
 box-shadow:0 1px 0 rgba(255,255,255,.06) inset,0 14px 34px -18px rgba(0,0,0,.9);
 transition:border-color .18s ease,transform .18s ease,box-shadow .18s ease}
.card:hover{border-color:#2c3746;transform:translateY(-1px);
 box-shadow:0 1px 0 rgba(255,255,255,.07) inset,0 22px 44px -20px rgba(0,0,0,.95)}
.card.engine{grid-column:1/-1}
.card>h2{display:flex;align-items:center;gap:8px;font-size:11.5px;font-weight:650;margin:0 0 13px;
 text-transform:uppercase;letter-spacing:1.1px;color:#cfdae6}
.dot{width:7px;height:7px;border-radius:50%;background:var(--ac,var(--b));flex:0 0 auto;
 box-shadow:0 0 0 3px rgba(94,224,180,.15)}
.dot.idle{background:var(--c);box-shadow:0 0 0 3px rgba(255,180,92,.15)}
.tag{margin-left:auto;font-size:10px;letter-spacing:.6px;color:var(--ink-faint);font-weight:500;
 text-transform:uppercase}
.kpis{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:13px}
.kpi{border:1px solid var(--line-soft);border-radius:12px;padding:10px 12px;
 background:linear-gradient(180deg,rgba(255,255,255,.045),rgba(0,0,0,.14))}
.kpi b{display:block;font-size:24px;font-weight:680;line-height:1.1;letter-spacing:-.6px}
.kpi b small{font-size:11px;font-weight:600;color:var(--ink-dim);margin-left:2px;letter-spacing:0}
.kpi s{display:block;text-decoration:none;font-size:9.5px;color:var(--ink-dim);
 letter-spacing:.7px;text-transform:uppercase;margin-top:5px}
.meter{display:flex;align-items:center;gap:9px;margin:2px 0 8px}
.meter span{font-size:9.5px;color:var(--ink-faint);letter-spacing:.7px;text-transform:uppercase;
 min-width:34px}
.bar{flex:1;height:5px;border-radius:99px;background:rgba(255,255,255,.06);overflow:hidden}
.bar i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,var(--a),#8fd7ff);
 box-shadow:0 0 12px rgba(94,200,255,.35)}
.bar i.g{background:linear-gradient(90deg,var(--b),#9df3d0);box-shadow:0 0 12px rgba(94,224,180,.3)}
.bar i.o{background:linear-gradient(90deg,var(--c),#ffd39b);box-shadow:0 0 12px rgba(255,180,92,.3)}
.bar i.p{background:linear-gradient(90deg,var(--v),#d8c9ff);box-shadow:0 0 12px rgba(189,168,255,.3)}
.meter em{font-style:normal;font-size:10.5px;color:var(--ink-dim);min-width:38px;text-align:right}
.sect{font-size:9.5px;letter-spacing:.9px;text-transform:uppercase;color:var(--ink-faint);
 margin:12px 0 6px;display:flex;align-items:center;gap:8px}
.sect::after{content:"";flex:1;height:1px;background:var(--line-soft)}
.tgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px}
.chip{border:1px solid var(--line-soft);border-radius:9px;padding:6px 8px;
 background:rgba(0,0,0,.24);font-size:10px;line-height:1.3;min-width:0;overflow:hidden}
.chip b{display:block;font-size:13.5px;font-weight:680;letter-spacing:-.2px}
.chip b small{font-size:9px;font-weight:600;color:var(--ink-dim);margin-left:1px}
.chip s{display:block;text-decoration:none;color:var(--ink-faint);font-size:8.5px;
 letter-spacing:.4px;text-transform:uppercase;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.chip.hot{border-color:rgba(255,180,92,.34);background:rgba(255,180,92,.08)}
.chip.hot b{color:var(--hot)}
.chip.crit{border-color:rgba(255,95,109,.42);background:rgba(255,95,109,.1)}
.chip.crit b{color:var(--crit)}
.rows{display:grid;grid-template-columns:1fr;gap:0}
.row{display:flex;justify-content:space-between;gap:12px;padding:5px 0;
 border-top:1px solid var(--line-soft)}
.row:first-child{border-top:0}
.row span:first-child{color:var(--ink-dim);font-size:11.5px}
.row span:last-child{font-weight:650;text-align:right;white-space:nowrap;font-size:12px}
.row.wrap span:last-child{white-space:normal;word-break:break-word;line-height:1.45}
.pill{display:inline-block;padding:1px 8px;border-radius:999px;font-size:10px;font-weight:650;
 letter-spacing:.4px;text-transform:uppercase}
.pill.on{color:#062b1e;background:var(--ok)}
.pill.off{color:#2a1c04;background:var(--c)}
.chart{margin:0}
.chart figcaption{font-size:9.5px;color:var(--ink-faint);letter-spacing:.8px;text-transform:uppercase;
 margin-bottom:5px}
svg{width:100%;height:auto;display:block}
.leg{font-size:10px;color:var(--ink-dim);margin-top:5px;display:flex;flex-wrap:wrap;gap:10px}
.leg em{font-style:normal;font-weight:650}
.leg i{display:inline-block;width:7px;height:7px;border-radius:2px;margin-right:5px;vertical-align:1px}
.engine-body{display:grid;grid-template-columns:minmax(0,1.05fr) minmax(0,1fr);gap:18px}
.note{font-size:10.5px;color:var(--ink-faint);margin-top:14px;padding-top:12px;
 border-top:1px solid var(--line-soft)}
@media(max-width:1299px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:1080px){.engine-body{grid-template-columns:1fr}}
@media(max-width:700px){.grid{grid-template-columns:1fr}}
@media(max-width:640px){body{padding:20px 14px 32px}.kpis{grid-template-columns:1fr}
 .tgrid{grid-template-columns:repeat(2,minmax(0,1fr))}h1{font-size:18px}}
</style></head><body>
<header>
 <div class="brand">
  <div class="mark">◈</div>
  <div>
   <h1>DGX Spark cluster</h1>
   <div class="sub"><span class="badge">N/A · vLLM TP=2</span><span id="ts"></span></div>
  </div>
 </div>
 <div class="live"><i></i>live · 5 s refresh</div>
</header>
<div id="app"></div>
<script>
const H={},MAX=72;
const T=['#5ec8ff','#5ee0b4','#ffb45c','#ff86ad','#bda8ff'];
function push(k,v){const a=H[k]||(H[k]=[]);a.push(v);if(a.length>MAX)a.shift();return a}
function num(v){return v==null?null:+v}
function densify(s){let last=null;return (s||[]).map(v=>{const n=num(v);if(n!=null)last=n;return last==null?0:last})}
function chart(series,labels,colors,w=430,h=104){
 series=series.map(densify);
 const pts=series.flat().map(num).filter(v=>v!=null);
 if(pts.length<2)return '<div class="leg">collecting…</div>';
 let mn=Math.min(...pts),mx=Math.max(...pts);if(mn===mx){mn-=1;mx+=1}
 const p=10,iw=w-p*2,ih=h-p*2-6,n=Math.max(...series.map(s=>s.length));
 const X=i=>p+(n<2?iw/2:i/(n-1)*iw),Y=v=>p+ih-(num(v)-mn)/(mx-mn)*ih;
 let g='';
 for(let i=0;i<4;i++){const y=p+ih*i/3;
  g+=`<line x1="${p}" y1="${y.toFixed(1)}" x2="${w-p}" y2="${y.toFixed(1)}" stroke="rgba(255,255,255,.05)" stroke-dasharray="${i===3?'0':'2 4'}"/>`}
 const gid='g'+Math.random().toString(36).slice(2,7);
 let defs=`<defs><linearGradient id="${gid}" x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stop-color="${colors[0]}" stop-opacity=".34"/>
  <stop offset="100%" stop-color="${colors[0]}" stop-opacity="0"/></linearGradient></defs>`;
 let b='';
 series.forEach((s,si)=>{
  const d=s.map((v,i)=>(i?'L':'M')+X(i).toFixed(1)+' '+Y(v).toFixed(1)).join(' ');
  const area=d+` L${X(s.length-1).toFixed(1)} ${(p+ih).toFixed(1)} L${X(0).toFixed(1)} ${(p+ih).toFixed(1)} Z`;
  if(si===0)b+=`<path d="${area}" fill="url(#${gid})" stroke="none"/>`;
  const last=s.map((v,i)=>({v,i})).filter(o=>num(o.v)!=null).pop();
  b+=`<path d="${d}" fill="none" stroke="${colors[si]}" stroke-width="1.8"
      stroke-linejoin="round" stroke-linecap="round"/>`;
  if(last){const cx=X(last.i).toFixed(1),cy=Y(last.v).toFixed(1);
   b+=`<circle cx="${cx}" cy="${cy}" r="6" fill="${colors[si]}" opacity=".18"/>`;
   b+=`<circle cx="${cx}" cy="${cy}" r="2.6" fill="${colors[si]}"/>`}});
 const fmt=v=>v==null?'–':(Math.abs(v)<10?v.toFixed(1):Math.round(v));
 let t=`<text x="${p}" y="${h-1}" fill="#6b7787" font-size="8.5">${fmt(mn)}</text>`+
       `<text x="${w-p}" y="${p}" fill="#6b7787" font-size="8.5" text-anchor="end">${fmt(mx)}</text>`;
 const lg=labels.map((l,i)=>{const v=series[i][series[i].length-1];
  return `<span><i style="background:${colors[i]}"></i>${l} <em style="color:#eef3f9">${fmt(num(v))}</em></span>`}).join('');
 return `<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none">${defs}${g}${b}${t}</svg>`+
        `<div class="leg">${lg}</div>`}
function fig(cap,inner){return `<figure class="chart">${cap?`<figcaption>${cap}</figcaption>`:''}${inner}</figure>`}
function fmtSec(s){if(s==null)return'–';if(s<90)return s+' s';if(s<5400)return (s/60).toFixed(1)+' min';return (s/3600).toFixed(2)+' h ('+Math.round(s)+' s)'}
function row(k,v,cls){return `<div class="row ${cls||''}"><span>${k}</span><span>${v}</span></div>`}
function meter(label,pct,cls){const w=Math.max(0,Math.min(100,pct||0));
 return `<div class="meter"><span>${label}</span><div class="bar"><i class="${cls||''}" style="width:${w}%"></i></div><em>${pct==null?'–':pct+'%'}</em></div>`}
function nodeCard(d,id,accent){
 push(id+'_t',num(d.temp_max));push(id+'_m',num(d.mem_used_gb));push(id+'_c',num(d.cpu_pct));
 const nv=Object.entries(d.nvme||{});
 const disk=d.disk&&d.disk['/'];
 function chipHTML(k,v,cls){return `<div class="chip ${cls||''}"><b>${v}<small>°C</small></b><s>${k}</s></div>`}
 function tempCls(v,crit){if(crit&&v>=crit-3)return 'crit';if(crit&&v>=crit-10)return 'hot';return ''}
 const tkeys=Object.entries(d.temps||{});
 const socCrit=(d.crit||{}).soc;
 const tgrid=tkeys.length?'<div class="tgrid">'+tkeys.map(([k,v])=>chipHTML(k,v,tempCls(v,socCrit))).join('')+'</div>'
  :'<div class="leg">no thermal sensors exposed</div>';
 const nvCrit=(d.crit||{}).nvme;
 const nvgrid=nv.length?'<div class="tgrid">'+nv.map(([k,v])=>chipHTML('NVMe '+k,v,tempCls(v,nvCrit))).join('')+'</div>':''; 
 return `<div class="card" style="--ac:${accent||'#5ec8ff'}"><h2><i class="dot"></i>${id}<span class="tag">node</span></h2>
 <div class="kpis">
  <div class="kpi"><b>${d.cpu_pct==null?'–':d.cpu_pct}<small>%</small></b><s>CPU · ${d.cpu_cores} cores</s></div>
  <div class="kpi"><b style="color:${(d.temp_peak_1h||0)>=80?'var(--c)':'var(--ink)'}">${d.temp_peak_1h==null?'n/a':d.temp_peak_1h}<small>°C</small></b><s>SoC peak · 1 h (now ${d.temp_max==null?'n/a':d.temp_max})</s></div>
 </div>
 ${meter('CPU',d.cpu_pct,'')}${meter('RAM',d.mem_pct,'g')}
 <div class="sect">thermal sensors</div>${tgrid}${nv.length?'<div class="sect">storage</div>'+nvgrid:''}
 <div class="sect">system</div>
 <div class="rows">
  ${row('Load 1/5/15m',d.load.filter(x=>x!=null).join(' · '))}
  ${row('RAM',(d.mem_used_gb)+' / '+d.mem_total_gb+' GB')}
  ${row('Disk /',disk?disk[0]+' / '+disk[1]+' GB':'–')}
  ${row('Uptime',d.uptime_h+' h')}
  ${row('Net RX',d.net_rx_mb+' MB')}
  ${d.gpu?row('GPU','util '+d.gpu.util_pct+'% · '+d.gpu.power_w+' W · '+d.gpu.sm_mhz+' MHz · '+d.gpu.temp_c+' °C'):''}
 </div>
 <div class="sect">trends</div>
 ${fig('SoC temperature trend',chart([H[id+'_t']],['°C'],[T[0]]))}
 ${fig('RAM GB vs CPU %',chart([H[id+'_m'],H[id+'_c']],['RAM','CPU'],[T[1],T[2]]))}
</div>`}
function vllmCard(v){
 push('tps',num(v.tok_s));push('itl',num(v.itl_ms));push('kv',num(v.kv_pct));push('acc',num(v.accept_rate));
 const done=v.requests_done||{},live=(v.running||0)>0;
 const doneStr=done.total!=null?done.total+' total':((done.stop||0)+' stop · '+(done.length||0)+' length');
 const gpu=[v.gpu_util!=null?'gpu_util '+v.gpu_util:null,v.rss_mb!=null?v.rss_mb+' MiB RSS':null].filter(Boolean).join(' · ');
 const status=`<span class="pill ${live?'on':'off'}">${live?'generating':'idle'}</span>`;
 return `<div class="card engine"><h2><i class="dot ${live?'':'idle'}"></i>${v.engine||'LLM'} engine<span class="tag">serving</span></h2>
 <div class="engine-body">
  <div>
   <div class="kpis">
    <div class="kpi"><b style="color:${T[1]}">${v.tok_s_peak_1h==null?'n/a':v.tok_s_peak_1h}<small>tok/s</small></b><s>peak · 1 h (now ${v.tok_s==null?'n/a':v.tok_s})</s></div>
    <div class="kpi"><b style="color:${T[0]}">${v.itl_ms==null?'–':v.itl_ms}<small>ms</small></b><s>step time · ITL</s></div>
   </div>
   ${meter('KV',v.kv_pct,'p')}
   <div class="rows">
    ${row('Model',v.model,'wrap')}
    ${v.model_root?row('Checkpoint',v.model_root,'wrap'):''}
    ${row('Status',status)}
    ${row('Running / waiting',v.running+' / '+v.waiting)}
    ${row('KV cache used',v.kv_pct+' %')}
    ${v.tok_per_step==null?'':row('Tokens / step (MTP)',v.tok_per_step)}
    ${v.accept_rate==null?'':row('Draft accept rate',v.accept_rate)}
    ${v.ttft_ms==null?'':row('TTFT mean',v.ttft_ms+' ms')}
    ${row('Prefix cache hit',v.prefix_hit_pct==null?'–':v.prefix_hit_pct+' %')}
    ${row('Prompt / generated',(Math.round((v.prompt_tokens||0)/1e6)+' M')+' / '+(Math.round((v.gen_tokens||0)/1e3)+' k'))}
    ${row('Requests done',doneStr)}
    ${gpu?row('Engine',gpu):''}
    ${v.streams?row('Streams',v.streams):''}
    ${v.prefill_s==null?'':row('Prefill time',fmtSec(v.prefill_s))}
    ${v.decode_s==null?'':row('Decode time',fmtSec(v.decode_s))}
   </div>
  </div>
  <div>
   <div class="sect">live throughput</div>
   ${fig('Decode throughput',chart([(()=>{const hs=v.hist||{};return (Array.isArray(hs.tps)&&hs.tps.length>1)?hs.tps:(H.tps||[])})(),],['tok/s'],[T[1]]))}
   ${fig('Step time vs KV cache',chart([(()=>{const hs=v.hist||{};return (Array.isArray(hs.itl)&&hs.itl.length>1)?hs.itl:(H.itl||[])})(),(()=>{const hs=v.hist||{};return (Array.isArray(hs.kv)&&hs.kv.length>1)?hs.kv:(H.kv||[])})(),],['ITL ms','KV %'],[T[2],T[3]]))}
   ${fig('MTP accept rate',chart([(()=>{const hs=v.hist||{};return (Array.isArray(hs.acc)&&hs.acc.length>1)?hs.acc:(H.acc||[])})(),],['accept'],[T[4]]))}
  </div>
 </div>
 <div class="note">Sources: node_exporter :9100 (spark, edgexpert, this VM, mini pc) · engine /metrics + /health + /v1/models · 1 h peaks from a rolling server-side window.</div>
</div>`}
function rows(o){let s='';for(const[k,v]of Object.entries(o)){if(v==null)continue;s+=`<div class="row"><span>${k}</span><span>${v}</span></div>`}return s}
async function up(){
 const d=await (await fetch('/data',{cache:'no-store'})).json();
 document.getElementById('ts').textContent='updated '+new Date(d.ts*1000).toLocaleTimeString();
 document.querySelector('.badge').textContent=(d.engine.model||'?')+' · '+(d.engine.engine||'LLM')+' TP=2';
 document.getElementById('app').innerHTML='<div class="grid">'+
  ((d.nodes&&d.nodes.length)?d.nodes:[d.spark,d.edge,d.oracle,d.mini])
   .filter(Boolean).map(n=>nodeCard(n,n.label||n.key,n.accent)).join('')+
  vllmCard(d.engine||{})+'</div>'}
up();setInterval(up,5000);
if(location.search.indexOf('probe')>-1)setTimeout(()=>{
 const cs=[...document.querySelectorAll('.card')].map(c=>{const r=c.getBoundingClientRect();
  return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),h:Math.round(r.height)}});
 const over=[...document.querySelectorAll('*')].filter(e=>e.scrollWidth>e.clientWidth+2&&e.clientWidth>0)
  .map(e=>e.className||e.tagName).slice(0,8);
 let ov=[];for(let i=0;i<cs.length;i++)for(let j=i+1;j<cs.length;j++){
  const a=cs[i],b=cs[j];
  if(a.x<b.x+b.w&&b.x<a.x+a.w&&a.y<b.y+b.h&&b.y<a.y+a.h)ov.push(i+'x'+j)}
 document.title=JSON.stringify({vw:innerWidth,cards:cs,overflow:over,overlaps:ov,
  deadRight:Math.round(innerWidth-Math.max(...cs.map(c=>c.x+c.w))),
  scrollH:document.documentElement.scrollHeight})},1500);
</script></body></html>"""
