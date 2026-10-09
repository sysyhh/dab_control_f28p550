"""Render the onboarding guide to a self-contained offline HTML companion.

Run with the existing onnx_env Python, which has Markdown==3.10.2 installed.
No external scripts, fonts or stylesheets are used by the delivered HTML.
"""
from pathlib import Path
import hashlib
import html
import json
import markdown

HERE = Path(__file__).resolve().parent
DOCS = HERE.parent / "dab_control_f28p550/docs"
ASSETS = DOCS / "assets"
ASSETS.mkdir(exist_ok=True)
SOURCE = DOCS / "DAB_F28P550_guide_zh.md"

def svg_start(width, height, title):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title">
<title id="title">{html.escape(title)}</title>
<defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="#58708a"/></marker></defs>
<rect width="100%" height="100%" fill="#f5f8fc" rx="18"/>
<style>text{{font-family:'Microsoft YaHei','Noto Sans CJK SC',sans-serif;fill:#19354f}} .label{{font-size:20px;font-weight:600}} .small{{font-size:16px}} .muted{{fill:#577086}}</style>'''

def box(x, y, w, h, title, detail="", color="#e2eefb"):
    parts = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{color}" stroke="#c0d2e2"/>',
             f'<text class="label" x="{x+w/2}" y="{y+34}" text-anchor="middle">{html.escape(title)}</text>']
    for i, line in enumerate(detail.split("\n")):
        if line:
            parts.append(f'<text class="small" x="{x+w/2}" y="{y+61+i*23}" text-anchor="middle">{html.escape(line)}</text>')
    return "".join(parts)

def arrow(x1, y1, x2, y2):
    return f'<path d="M{x1},{y1} L{x2},{y2}" stroke="#58708a" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>'

def label(x, y, text, small=True):
    return f'<text class="{"small" if small else "label"}" x="{x}" y="{y}">{html.escape(text)}</text>'

parts = [svg_start(1100, 570, "DAB 运行关系：外设采样、控制中断、PWM 装载与主循环")]
parts += [label(28, 38, "固定节拍的采样与控制", False),
          box(30, 68, 215, 104, "EPWM1 / ADC", "零点触发；两 ADC\n周期顶点读四项结果"),
          box(288, 68, 220, 104, "10 kHz 控制中断", "检查数据与保护\n软启动 / 可选 PI / NN 缓存"),
          box(555, 68, 218, 104, "完整 PWM 参数包", "寄存器值 + 原参数\n序号 + 等待期限"),
          box(818, 68, 250, 104, "EPWM7 提交与装载", "主零点 / 从同步\n四个桥臂 EPWM7/4/5/10")]
parts += [arrow(245, 120, 288, 120), arrow(508, 120, 555, 120), arrow(773, 120, 818, 120)]
parts += [label(28, 235, "主循环：推理、请求和遥测", False),
          box(30, 264, 268, 104, "NN 后台服务", "默认 FPU；未来 NPU\n只发布完整、有效的结果", "#e5f3eb"),
          box(348, 264, 268, 104, "启停与故障请求", "状态 + ADC + NN + 保护\n共同决定是否接受", "#e5f3eb"),
          box(666, 264, 402, 104, "SCI 队列 + 看门狗", "不等待串口空间；有新控制进度才喂狗\n默认 10 Hz 三通道显示", "#e5f3eb")]
parts += ['<path d="M298,315 H322 V194 H398 V178" stroke="#58708a" stroke-width="2.5" fill="none" marker-end="url(#arrow)"/>',
          label(160, 206, "结果缓存"), arrow(480, 264, 430, 178)]
parts += [box(30, 429, 1038, 100, "外部故障直接关闭输出", "GPIO60 → Input XBAR1 → TZ1 → 四路 OST；不依赖 CPU 中断执行", "#fff0e1"),
          label(31, 556, "图示为当前软件关系；引脚、实际关断延迟与四桥波形需实板确认。")]
(ASSETS / "runtime.svg").write_text("".join(parts)+"</svg>", encoding="utf-8")

parts = [svg_start(1100, 540, "EPWM1 采样、读取及控制时序：每周期 100 微秒")]
parts += [label(28, 40, "EPWM1：7500 上下计数，TBCLK=150 MHz", False)]
parts += ['<path d="M150,219 L575,89 L1000,219" fill="none" stroke="#377fc1" stroke-width="4"/>',
          '<path d="M150,233 L1000,233" fill="none" stroke="#a8becf" stroke-width="2"/>']
for x, t in [(150, "0 μs / ZERO"), (575, "50 μs / PERIOD"), (1000, "100 μs / ZERO")]:
    parts += [f'<path d="M{x},72 L{x},450" stroke="#c9d6e2" stroke-width="1.5" stroke-dasharray="6 5"/>',
              f'<text class="small" x="{x}" y="{60}" text-anchor="middle">{t}</text>']
parts += [label(172, 180, "向上计数"), label(719, 205, "向下计数"),
          box(60, 270, 320, 103, "SOCA 同时触发 A/B", "各 ADC 的 SOC0 → SOC1\n等待 EOC1（不是四项同时采样）"),
          box(413, 270, 355, 103, "EPWM1 控制中断", "检查完成和溢出、读结果\n保护 → 控制 → 保存 PWM 请求"),
          label(50, 415, "数据采样比正常读取早约 50 μs；数据年龄时间戳记录的是读取结束。"),
          label(50, 448, "下一次零点前保留 150 个计数（约 1 μs）的读取检查余量。"),
          label(50, 497, "功率 PWM 独立运行于 15～60 kHz，EPWM7 装载边界另行确认；此图未按比例表示 ADC 转换耗时。")]
(ASSETS / "timing.svg").write_text("".join(parts)+"</svg>", encoding="utf-8")

parts = [svg_start(1100, 530, "DAB 状态：待机、软启动、运行和人工故障清除")]
parts += [label(28, 40, "输出释放由首包装载与保护条件共同决定", False),
          box(35, 99, 265, 110, "STANDBY / 待机", "输出关闭\n默认启动被板确认门控阻止"),
          box(415, 99, 265, 110, "SOFT_START / 软启动", "首包确认后释放\n按新装载序号渐变"),
          box(795, 99, 265, 110, "RUN / 运行", "持续检查采样、NN 和期限\n不等于闭环已验证")]
parts += [arrow(300, 148, 415, 148), label(312, 122, "启动通过"),
          arrow(680, 148, 795, 148), label(688, 122, "渐变完成"),
          box(415, 334, 265, 110, "FAULT / 故障", "保持关断及首次记录\n新故障脉冲重启恢复等待", "#fff0e1"),
          arrow(548, 209, 548, 334), label(563, 278, "任何故障"),
          '<path d="M925,209 V388 H682" fill="none" stroke="#58708a" stroke-width="2.5" marker-end="url(#arrow)"/>',
          '<path d="M415,389 H270 V211" fill="none" stroke="#58708a" stroke-width="2.5" marker-end="url(#arrow)"/>',
          label(34, 305, "连续正常 ≥5 ms"), label(34, 332, "+ ADC 连续 50 帧"), label(34, 359, "+ 人工清除"),
          label(30, 488, "正常停止 → STANDBY；故障中停止仍保持 FAULT；清除成功也不会自动启动。")]
(ASSETS / "states.svg").write_text("".join(parts)+"</svg>", encoding="utf-8")

raw = SOURCE.read_text(encoding="utf-8")
md = markdown.Markdown(extensions=["tables", "fenced_code", "toc"], extension_configs={"toc": {"toc_depth": "2-3"}})
body = md.convert(raw).replace('href="NN_timing_guide_zh.md"', 'href="NN_timing_guide_zh.html"').replace('href="NPU_integration_guide_zh.md"', 'href="NPU_integration_guide_zh.html"')
css = '''
:root{--ink:#203648;--muted:#526b7d;--blue:#1766a4;--line:#d7e2eb;--panel:#f1f6fb}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}
body{margin:0;background:#f8fafc;color:var(--ink);font:16px/1.8 'Microsoft YaHei','Noto Sans CJK SC',sans-serif}
.shell{display:grid;grid-template-columns:290px minmax(0,1fr);max-width:1500px;margin:auto}
nav{position:sticky;top:0;height:100vh;overflow:auto;padding:26px 20px;border-right:1px solid var(--line);background:var(--panel)}
.brand{font-size:20px;font-weight:700;line-height:1.5;margin-bottom:14px}.badge{font-size:12px;background:#fff1db;color:#795524;padding:4px 8px;border-radius:4px}
nav ul{list-style:none;padding-left:0}nav li{margin:6px 0}nav li li{font-size:13px;padding-left:13px}nav a{color:#294d69;text-decoration:none;display:block;line-height:1.6;padding:3px 0}nav a:hover{color:var(--blue);text-decoration:underline}
main{min-width:0;padding:42px 48px 75px;background:white}h1{font-size:32px;line-height:1.5;margin:0 0 20px}h2{font-size:25px;padding-top:22px;margin:40px 0 18px;border-top:2px solid var(--line);line-height:1.6}h3{font-size:20px;margin-top:30px}
p{margin:15px 0}a{color:var(--blue);text-underline-offset:3px}strong{color:#183f61}code{font-family:Consolas,monospace;font-size:.9em;background:#eef3f8;padding:2px 4px;border-radius:3px;overflow-wrap:anywhere}
pre{background:#edf3f8;border-left:4px solid #739bbd;padding:18px;overflow:auto;font-size:14px;line-height:1.7}pre code{background:transparent;padding:0;overflow-wrap:normal}
.table-scroll{overflow-x:auto;margin:20px 0}table{width:100%;border-collapse:collapse;min-width:580px;font-size:14px;line-height:1.75}th,td{padding:10px 12px;border:1px solid var(--line);vertical-align:top}th{background:#e9f2fa;text-align:left}tbody tr:nth-child(even){background:#f8fbfe}td code{font-size:12px}
img{display:block;width:100%;max-width:1100px;height:auto;margin:25px auto;border:1px solid var(--line);border-radius:12px}
li{margin:8px 0}footer{margin-top:45px;padding-top:20px;border-top:1px solid var(--line);color:var(--muted);font-size:13px;overflow-wrap:anywhere}
.tools{display:flex;gap:8px;flex-wrap:wrap;margin:14px 0}button{border:1px solid #bdd0e0;border-radius:5px;background:white;color:#284a65;padding:7px 12px;cursor:pointer;font:inherit;font-size:13px}button:hover{background:#e3eef8}
input{width:100%;padding:10px;border:1px solid #bdd0e0;border-radius:5px;font:inherit;font-size:14px}#search-status{font-size:12px;min-height:22px;color:#526b7d}.search-hit{background:#ffe9a0;border-radius:3px;color:inherit}.search-current{background:#ffca56;outline:2px solid #b7791f}
@media(max-width:1000px){.shell{grid-template-columns:245px minmax(0,1fr)}main{padding:32px 24px}nav{padding:20px 14px}}
@media(max-width:740px){.shell{display:block}nav{position:relative;height:auto;max-height:420px;border-right:0;border-bottom:1px solid var(--line)}main{padding:25px 17px}h1{font-size:26px}h2{font-size:22px}}
@media print{body{background:white;font:10pt/1.6 'Microsoft YaHei',sans-serif}.shell{display:block}nav{display:none}main{padding:0}h1{font-size:20pt}h2{font-size:15pt;break-after:avoid}h3{font-size:12pt;break-after:avoid}.table-scroll{overflow:visible}table{min-width:0;font-size:9pt}th,td{padding:5px}tr{break-inside:avoid}pre,img{break-inside:avoid}a{color:#203648;text-decoration:none}.search-hit,.search-current{background:none;outline:none}}
'''
script = '''
document.querySelectorAll('main table').forEach(table=>{const wrap=document.createElement('div');wrap.className='table-scroll';table.before(wrap);wrap.append(table)});
const article=document.getElementById('article'),query=document.getElementById('query'),status=document.getElementById('search-status');let hits=[],index=-1;
function clearSearch(){article.querySelectorAll('mark.search-hit').forEach(mark=>mark.replaceWith(document.createTextNode(mark.textContent)));article.normalize();hits=[];index=-1;status.textContent=''}
function nextHit(){if(!hits.length)return;if(index>=0)hits[index].classList.remove('search-current');index=(index+1)%hits.length;hits[index].classList.add('search-current');hits[index].scrollIntoView({block:'center',behavior:'smooth'});status.textContent=`${index+1} / ${hits.length} 处匹配`}
function search(){clearSearch();const q=query.value.trim();if(!q)return;const walker=document.createTreeWalker(article,NodeFilter.SHOW_TEXT);const nodes=[];while(walker.nextNode())nodes.push(walker.currentNode);nodes.forEach(node=>{const text=node.textContent,lower=text.toLowerCase(),needle=q.toLowerCase();let from=0,pos=lower.indexOf(needle);if(pos<0)return;const frag=document.createDocumentFragment();while(pos>=0){frag.append(document.createTextNode(text.slice(from,pos)));const mark=document.createElement('mark');mark.className='search-hit';mark.textContent=text.slice(pos,pos+q.length);frag.append(mark);hits.push(mark);from=pos+q.length;pos=lower.indexOf(needle,from)}frag.append(document.createTextNode(text.slice(from)));node.replaceWith(frag)});status.textContent=hits.length?`${hits.length} 处匹配`:'未找到';nextHit()}
document.getElementById('search').addEventListener('click',search);document.getElementById('next').addEventListener('click',nextHit);document.getElementById('clear').addEventListener('click',()=>{query.value='';clearSearch()});query.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();search()}});document.getElementById('print').addEventListener('click',()=>window.print());
'''
sha = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
document = f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>F28P550 DAB · 上手与配置说明</title><style>{css}</style></head>
<body><div class="shell"><nav aria-label="文档目录"><div class="brand">F28P550 DAB<br>上手与配置说明</div><span class="badge">2026-10-09 · NPU 核对与计时版</span><p style="font-size:13px">FPU 基准已验证<br>NPU 已接入，实板数值和计时待核对</p><label for="query" style="font-size:13px">在文档中查找</label><input id="query" type="search" placeholder="例如：ADC、软启动、B09"><div class="tools"><button id="search">查找</button><button id="next">下一处</button><button id="clear">清除</button><button id="print">打印 / 保存 PDF</button></div><div id="search-status" aria-live="polite"></div>{md.toc}<p><a href="DAB_F28P550_guide_zh.md">Markdown 原稿</a></p></nav>
<main><article id="article">{body}</article><footer>离线阅读：不加载网络脚本、字体或样式。资料链接需要联网。<br>来源文件 SHA-256：{sha}</footer></main></div><script>{script}</script></body></html>'''
(DOCS / "DAB_F28P550_guide_zh.html").write_text(document, encoding="utf-8")
(DOCS / "guide_manifest.json").write_text(json.dumps({
    "date": "2026-10-09", "source": SOURCE.name, "source_sha256": sha,
    "html_sha256": hashlib.sha256((DOCS / "DAB_F28P550_guide_zh.html").read_bytes()).hexdigest(),
    "renderer": "Python-Markdown " + markdown.__version__,
    "offline_assets": ["assets/runtime.svg", "assets/timing.svg", "assets/states.svg"],
    "asset_sha256": {"assets/"+p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(ASSETS.glob("*.svg"))},
    "chapters": 17, "board_acceptance_items": 17
}, ensure_ascii=False, indent=2), encoding="utf-8")
print("Guide rendered: Markdown, offline HTML, three SVG diagrams and manifest")

for name in ("NN_timing_guide_zh", "NPU_integration_guide_zh"):
    source = DOCS / (name + ".md")
    renderer = markdown.Markdown(extensions=["tables", "fenced_code", "toc"])
    content = renderer.convert(source.read_text(encoding="utf-8"))
    for related in ("NN_timing_guide_zh", "NPU_integration_guide_zh", "DAB_F28P550_guide_zh"):
        content = content.replace(f'href="{related}.md"', f'href="{related}.html"')
    title = "NN 耗时统计" if name.startswith("NN_") else "DAB NPU 接入与开发板核对"
    output = f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>{css}</style></head><body><div class="shell"><nav aria-label="文档目录"><div class="brand">{title}</div>{renderer.toc}<p><a href="DAB_F28P550_guide_zh.html">返回上手说明</a></p><p><a href="{source.name}">Markdown 原稿</a></p></nav><main>{content}<footer>2026-10-09 · 离线文档；实际开发板数值与耗时待核对。<br>来源 SHA-256：{hashlib.sha256(source.read_bytes()).hexdigest()}</footer></main></div></body></html>'''
    (DOCS / (name + ".html")).write_text(output, encoding="utf-8")
    print("Rendered", name)
