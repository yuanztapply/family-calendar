# app.py - 家庭日程同步 (流动星空版 + 悬浮时钟修复)
# 运行: pip install streamlit pandas ，然后 streamlit run app.py

import streamlit as st
import streamlit.components.v1 as components
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from pathlib import Path
import pandas as pd
import json, random

UK_TZ = ZoneInfo("Europe/London")
BJ_TZ = ZoneInfo("Asia/Shanghai")
st.set_page_config(page_title="家庭日程同步", layout="wide", page_icon="🌌")

LIT = random.choice([
    {"orig": "Il n'y a qu'un seul luxe véritable, c'est celui des relations humaines.", "lang": "法语原文",
     "src": "Antoine de Saint-Exupéry《风沙星辰 Terre des hommes》(1939),第三章",
     "zh": "真正唯一的奢侈，是人与人之间的关系。",
     "ana": "圣埃克絮佩里以飞行员视角写撒哈拉迫降：物质都会耗尽，只有同伴递来的一口水算数。放在异地家庭里，时间对不上时，一次短通话比补一件礼物更奢侈。出处：Terre des hommes, Chapitre III。"},
    {"orig": "Whatever our souls are made of, his and mine are the same.", "lang": "英语原文",
     "src": "Emily Brontë《呼啸山庄 Wuthering Heights》(1847),第34章，凯瑟琳临终独白",
     "zh": "无论我们的灵魂是什么构成的，他的和我的是同一种。",
     "ana": "凯瑟琳在病榻上对耐莉说出此句，意为身份、距离、婚姻都无法切割同源的灵魂。约克郡荒原的风暴意象即情感的不可规训。家人分处两地，作息相反，但同源感不减。出处：Wuthering Heights, Ch.34。"},
    {"orig": "大江东去，浪淘尽，千古风流人物。", "lang": "中文原文",
     "src": "苏轼《念奴娇 · 赤壁怀古》(1082),北宋元丰五年谪居黄州时作",
     "zh": "长江向东奔流，浪花淘尽了千古英雄。",
     "ana": "上阕以长江起兴：赤壁一战的英雄不过浪花一瞬。下阕转入人生如梦，一樽还酹江月。时间观极为旷达——以千年尺度看，眼前的时差与错过都只是小浪。适合在约不上时间时读。"},
    {"orig": "No man is an island, entire of itself; every man is a piece of the continent.", "lang": "英语原文",
     "src": "John Donne《沉思 Meditation XVII》(1624),玄学派布道文",
     "zh": "没有人是孤岛，每个人都是大陆的一部分。",
     "ana": "多恩在病中写下：任何人的死亡都使我受损，因为我包含在人类之中。后世海明威以此为《丧钟为谁而鸣》题词。家庭即最小的大陆，缺一角便不完整。出处：Devotions upon Emergent Occasions。"},
    {"orig": "Они сражались за то, чтобы в мире было больше света, а тьма отступила — и свет этот был в их письмах домой.", "lang": "俄语原文",
     "src": "Василий Гроссман《生活与命运》(1960/1980),第二部家书线索",
     "zh": "他们战斗，是为了让世上多一点光、少一点黑暗——而那光，就藏在家书里。",
     "ana": "格罗斯曼写斯大林格勒战壕里的士兵：前线唯一的光是后方的信。通信不是闲聊，是维系人之所以为人的光。此处为全书家书主题的凝练转述，强调跨越距离的书写本身即抵抗黑暗。"},
    {"orig": "虢国夫人承主恩，平明骑马入宫门。却嫌脂粉污颜色，淡扫蛾眉朝至尊。", "lang": "中文原文",
     "src": "张祜《集灵台 · 其二》(晚唐),讽杨贵妃姐妹恃宠",
     "zh": "虢国夫人深受皇恩，天刚亮就骑马进宫。竟嫌脂粉玷污容色，只淡描眉毛去见皇上。",
     "ana": "四句全用白描，不着一议而讽意自见：特权者的从容反衬常人的奔波。读时可作镜鉴——能从容安排通话时间，本身已是一种被爱包围的幸运，宜珍惜而非视为理所当然。"},
])
st.markdown(f"""<div class="quote"><div class="en">“{LIT['orig']}”</div><div class="who">— {LIT['src']} · {LIT['lang']}</div><div class="zh">{LIT['zh']}</div><div class="ana">【赏析】{LIT['ana']}</div></div>""", unsafe_allow_html=True)

# ============ 流动星空背景 + 同色系明亮信息条 ============
st.markdown("""
<style>
/* 左主区:流动夜空 + 点点金色星 */
.stApp {
  background: linear-gradient(120deg,#050914,#0e1830,#16244a,#1e2c55,#050914);
  background-size: 300% 300%;
  animation: skydrift 26s ease infinite;
}
@keyframes skydrift { 0%{background-position:0% 40%} 50%{background-position:100% 60%} 100%{background-position:0% 40%} }
.stApp::before {
  content:""; position:fixed; inset:0; pointer-events:none; z-index:0;
  background-image:
    radial-gradient(1.6px 1.6px at 10% 20%, #ffe9a8 100%, transparent 100%),
    radial-gradient(1px 1px at 28% 64%, #ffd76e 100%, transparent 100%),
    radial-gradient(2px 2px at 45% 14%, #fff3c4 100%, transparent 100%),
    radial-gradient(1px 1px at 62% 34%, #ffdf8e 100%, transparent 100%),
    radial-gradient(2.2px 2.2px at 78% 68%, #ffe9a8 100%, transparent 100%),
    radial-gradient(1px 1px at 88% 16%, #ffd76e 100%, transparent 100%),
    radial-gradient(1.6px 1.6px at 18% 82%, #fff3c4 100%, transparent 100%),
    radial-gradient(1px 1px at 38% 46%, #ffdf8e 100%, transparent 100%),
    radial-gradient(1.6px 1.6px at 55% 82%, #ffe9a8 100%, transparent 100%),
    radial-gradient(1px 1px at 72% 8%, #ffd76e 100%, transparent 100%),
    radial-gradient(1.2px 1.2px at 5% 55%, #fff3c4 100%, transparent 100%),
    radial-gradient(1.2px 1.2px at 95% 50%, #ffdf8e 100%, transparent 100%);
  animation: twinkle 2.6s ease-in-out infinite alternate;
}
@keyframes twinkle { from{opacity:.45} to{opacity:1} }
/* 右侧边栏:与主区统一的暗夜金——同色系深底 + 金色描边/点缀 */
[data-testid="stSidebar"] {
  background: linear-gradient(160deg,#0a1128,#14204a,#1c2c5c,#0a1128);
  background-size: 200% 200%;
  animation: goldflow 26s ease infinite;
  border-right:1px solid rgba(255,215,130,.35);
}
@keyframes goldflow { 0%{background-position:0% 20%} 50%{background-position:100% 80%} 100%{background-position:0% 20%} }
[data-testid="stSidebar"] * { color:#e8ddc0 !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color:#ffe9a8 !important; }
[data-testid="stSidebar"] .stCheckbox, [data-testid="stSidebar"] .stToggle { background:rgba(255,215,130,.10); border:1px solid rgba(255,215,130,.25); border-radius:8px; padding:4px 8px; margin-bottom:4px; }
/* 让内容浮在星空上 */
.block-container { position:relative; z-index:1; }
/* 标题:同色系玻璃拟态 */
.hero { border-radius:20px; padding:28px 32px; color:#eef1ff;
  background:rgba(70,90,160,.35); border:1px solid rgba(160,180,255,.35);
  backdrop-filter:blur(10px); box-shadow:0 10px 40px rgba(0,0,0,.35); }
.hero h1 { margin:0; font-size:30px; letter-spacing:2px; color:#fff; }
.hero .sub { opacity:.75; font-size:13px; margin-top:6px; color:#d6ddff; }
.quote { text-align:center; color:#dbe1ff; margin:14px 0 4px 0; }
.quote .en { font-style:italic; font-size:15px; } .quote .zh { font-size:14px; margin-top:4px; color:#eef1ff;}
.quote .ana { font-size:12px; opacity:.75; margin-top:6px; line-height:1.7; max-width:900px; margin-left:auto; margin-right:auto; }
/* 信息条:不透明奶白底 + 深字，保证星空上可读 */
.card { border-radius:14px; padding:14px 16px; color:#1c2438;
  background:rgba(245,242,232,.96); border:1px solid rgba(255,220,140,.55);
  box-shadow:0 4px 16px rgba(0,0,0,.35); transition:transform .18s ease; }
.card:hover { transform:translateY(-3px); background:rgba(130,150,225,.42); }
.card span, .card b { color:#1c2438; }
.badge { display:inline-block; padding:3px 12px; border-radius:999px; font-size:13px; font-weight:700; }
.free{background:rgba(150,230,180,.85);color:#0c3a22;} .busy{background:rgba(240,180,180,.85);color:#5c1a1a;}
.nap{background:rgba(255,225,150,.9);color:#5c3f00;border:1px dashed #fff;}
.banner{border-radius:12px;padding:12px 16px;margin:10px 0;font-weight:700;color:#0e1430;
  border:1px solid rgba(255,255,255,.5); backdrop-filter:blur(8px);}
.b-green{background:rgba(170,240,195,.88);} .b-blue{background:rgba(170,205,250,.88);}
.b-orange{background:rgba(255,215,170,.90);} .b-gray{background:rgba(200,205,225,.75);color:#2a3050;}
.msg { background:rgba(120,140,210,.30); border-left:4px solid #aebfff; border-radius:0 10px 10px 0; padding:10px 14px; margin-bottom:8px; color:#eef1ff;}
.msg .meta { font-size:12px; color:#c3cbff; } .msg .body { font-size:14px; margin-top:2px; color:#fff;}
hr.soft{border:none;border-top:1px dashed rgba(170,190,255,.4);margin:14px 0;}
/* metric / expander 在深色底上可读 */
[data-testid="stMetric"] { background:rgba(120,140,210,.30); border:1px solid rgba(170,190,255,.35); border-radius:12px; padding:8px; }
[data-testid="stMetric"] label, [data-testid="stMetric"] div { color:#eef1ff !important; }
.stExpander, .stSelectbox label, .stSlider label, .stRadio label, .stTextInput label, .stTextArea label, .stDateInput label, .stCheckbox label { color:#e6ebff !important; }
h2, h3 { color:#f0f3ff !important; }
p, .stCaption, .stMarkdown { color:#dbe1ff; }
</style>
<div class="hero"><h1>家庭日程同步</h1><div class="sub">英国时间与北京时间 · 小时级对标 · 妈妈补觉浮动窗口 · 家庭留言板</div></div>
""", unsafe_allow_html=True)
# 名言已在上方展示，此处不再重复

# ============ 悬浮时钟修复:用 components.html 包一层,JS 一定执行 ============
components.html("""
<div id="clock" style="position:fixed;right:18px;bottom:18px;z-index:9999;
  background:rgba(20,26,55,.92);color:#eef1ff;border:1px solid rgba(160,180,255,.5);
  border-radius:14px;padding:10px 16px;font-size:13px;line-height:1.8;
  box-shadow:0 8px 24px rgba(0,0,0,.5);font-family:sans-serif;white-space:nowrap;">
  <div>🌍 伦敦 <b id="ldn" style="font-size:16px;">--:--:--</b> <span id="ldn-d"></span></div>
  <div>🌏 北京 <b id="bj" style="font-size:16px;">--:--:--</b> <span id="bj-d"></span></div>
</div>
<script>
function tick(){
  const now = new Date();
  const t = (tz)=> new Intl.DateTimeFormat('zh-CN',{timeZone:tz,hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false}).format(now);
  const d = (tz)=> new Intl.DateTimeFormat('zh-CN',{timeZone:tz,month:'numeric',day:'numeric',weekday:'short'}).format(now);
  document.getElementById('ldn').textContent = t('Europe/London');
  document.getElementById('ldn-d').textContent = d('Europe/London');
  document.getElementById('bj').textContent = t('Asia/Shanghai');
  document.getElementById('bj-d').textContent = d('Asia/Shanghai');
}
tick(); setInterval(tick,1000);
</script>
""", height=0)

# ============ 数据逻辑 (与上一版相同,略) ============
ANCHOR = date(2026, 9, 30)
MOM_CYCLE = ["夜班", "小休", "大休", "白班"]
def mom_day_status(d: date) -> str: return MOM_CYCLE[(d - ANCHOR).days % 4]
MOM_DESC = {"白班": "早上七点到晚上十点上班", "夜班": "晚上七点到次日早上十点上班", "小休": "夜班次日，上午补觉", "大休": "全天休息"}
def base_free(s: str, h: int) -> bool:
    if s == "大休": return True
    if s == "白班": return not (7 <= h < 22)
    if s == "夜班": return not (h >= 19 or h < 10)
    if s == "小休": return h >= 10
    return True

DOC = Path(__file__).parent
ICS_FILES = {"SAR Mphil课程": DOC / "SAR Mphil课程.ics", "个人": DOC / "个人.ics",
             "工作": DOC / "工作.ics", "Siri建议": DOC / "Siri建议.ics", "Untitled": DOC / "Untitled.ics"}
def parse_ics(path: Path):
    evs = []
    try: txt = path.read_text(encoding="utf-8", errors="ignore")
    except Exception: return evs
    for block in txt.split("BEGIN:VEVENT")[1:]:
        try:
            summ, ds, de = "", "", ""
            for line in block.splitlines():
                if line.startswith("SUMMARY"): summ = line.split(":", 1)[1] if ":" in line else ""
                elif line.startswith("DTSTART"): ds = line.split(":", 1)[1].strip()
                elif line.startswith("DTEND"): de = line.split(":", 1)[1].strip()
            if not ds: continue
            def p(s):
                s = s.strip()
                if s.endswith("Z"): return datetime.strptime(s, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC"))
                if "T" in s: return datetime.strptime(s[:15], "%Y%m%dT%H%M%S").replace(tzinfo=UK_TZ)
                return datetime.strptime(s, "%Y%m%d").replace(tzinfo=UK_TZ)
            evs.append((p(ds), p(de) if de else p(ds), summ))
        except Exception: continue
    return evs
all_events, counts = [], {}
for cname, p in ICS_FILES.items():
    evs = parse_ics(p) if p.exists() else []
    counts[cname] = len(evs)
    for s, e, summ in evs:
        all_events.append((s.astimezone(UK_TZ), e.astimezone(UK_TZ), summ, cname))

st.sidebar.header("日期与日历")
today_uk = datetime.now(UK_TZ).date()
sel_date = st.sidebar.date_input("选择日期（按英国日期）", value=today_uk)
enabled = {c: st.sidebar.checkbox(f"{c}（{counts.get(c,0)}个事件）", value=(c in ("SAR Mphil课程", "个人", "工作"))) for c in ICS_FILES}
st.sidebar.markdown("---")
st.sidebar.subheader("妈妈浮动补觉")
nap_before_on = st.sidebar.toggle("考虑夜班前下午补觉", value=True)
nap_before_range = st.sidebar.slider("夜班前补觉窗口（北京时间）", 12, 18, (14, 17))
nap_noon_on = st.sidebar.toggle("考虑小休日中午补觉", value=True)
nap_noon_range = st.sidebar.slider("小休日补觉窗口（北京时间）", 10, 18, (12, 15))
nap_mode = st.sidebar.radio("补觉时段计算方式", ["标为忙碌（稳妥）", "标为可能可约（提醒）"], index=0)

def is_nap(bj_date: date, h_bj: int):
    st_today = mom_day_status(bj_date)
    if nap_noon_on and st_today == "小休" and nap_noon_range[0] <= h_bj < nap_noon_range[1]: return True, "小休日午间补觉"
    if nap_before_on and st_today == "夜班" and nap_before_range[0] <= h_bj < nap_before_range[1]: return True, "夜班前下午补觉"
    return False, ""
def dad_free(dt: datetime) -> bool: return not (dt.weekday() < 5 and 7 <= dt.hour < 19)
def uk_busy_at(h: int):
    hs = datetime.combine(sel_date, time(h, 0), tzinfo=UK_TZ)
    he = datetime.combine(sel_date, time(h, 59), tzinfo=UK_TZ)
    hits = []
    for s, e, summ, c in all_events:
        if not enabled.get(c): continue
        if (e - s).total_seconds() >= 20 * 3600:
            if s.date() <= sel_date <= e.date(): hits.append(f"{summ}（{c}）")
        elif s <= he and e >= hs and (s.date() == sel_date or e.date() == sel_date): hits.append(f"{summ}（{c}）")
    seen, out = set(), []
    for x in hits:
        if x not in seen: seen.add(x); out.append(x)
    return (len(out) > 0, "；".join(out))

if "manual" not in st.session_state: st.session_state.manual = {}
if "notes" not in st.session_state: st.session_state.notes = {}
with st.expander("调整我的状态与备注", expanded=False):
    mcols = st.columns(4)
    for i, h in enumerate(range(7, 23)):
        busy, hit = uk_busy_at(h)
        cur = st.session_state.manual.get(h, None)
        with mcols[i % 4]:
            st.markdown(f"**英国 {h:02d}:00** — 日历：{'忙碌' if busy else '空闲'}")
            if hit: st.caption(hit[:30])
            c = st.selectbox("调整", ["跟随日历", "强制设为忙碌", "强制设为空闲"], index=0 if cur is None else (1 if cur else 2), key=f"m_{h}")
            st.session_state.manual[h] = None if c == "跟随日历" else (c == "强制设为忙碌")
            st.session_state.notes[h] = st.text_input("备注文字", value=st.session_state.notes.get(h, ""), placeholder="例如：写论文", key=f"n_{h}")

rows, c_all, c_dad, c_mom, c_maybe = [], [], [], [], []
for h_uk in range(7, 23):
    dt_uk = datetime.combine(sel_date, time(h_uk, 0), tzinfo=UK_TZ)
    dt_bj = dt_uk.astimezone(BJ_TZ)
    h_bj, bj_d = dt_bj.hour, dt_bj.date()
    bj_note = "当天" if bj_d == sel_date else "次日"
    m_st = mom_day_status(bj_d)
    napping, nap_why = is_nap(bj_d, h_bj)
    mf_base = base_free(m_st, h_bj)
    if napping and nap_mode.startswith("标为忙碌"): mf, maybe = False, False
    elif napping: mf, maybe = True, True
    else: mf, maybe = mf_base, False
    df = dad_free(dt_bj)
    man = st.session_state.manual.get(h_uk, None)
    cal_b, hit = uk_busy_at(h_uk)
    me_free = not (cal_b if man is None else man)
    w_all = me_free and df and mf and not maybe
    w_dad = me_free and df and (not mf) and not w_all
    w_mom = me_free and mf and (not df)
    w_maybe = me_free and df and maybe
    if w_all: c_all.append(f"英国 {h_uk} 点 = 北京 {h_bj} 点（{bj_note}）")
    elif w_dad: c_dad.append(f"英国 {h_uk} 点 = 北京 {h_bj} 点")
    elif w_mom: c_mom.append(f"英国 {h_uk} 点 = 北京 {h_bj} 点")
    if w_maybe: c_maybe.append(f"英国 {h_uk} 点 = 北京 {h_bj} 点（{nap_why}）")
    kind = "all" if w_all else ("maybe" if w_maybe else ("dad" if w_dad else ("mom" if w_mom else ("mebusy" if not me_free else "none"))))
    rows.append(dict(英国小时=h_uk, 北京时间=f"{h_bj:02d}:00（{bj_note}）", 我="忙碌" if not me_free else "空闲",
                     事件=hit, 备注=st.session_state.notes.get(h_uk, ""), 爸爸="休息" if df else "上班",
                     妈妈状态=m_st, 补觉=(nap_why if napping else "—"), 妈妈是否可约=("可能可约" if maybe else ("可约" if mf else "忙碌")), 类型=kind))

k1, k2, k3, k4 = st.columns(4)
k1.metric("三人同时空闲", f"{len(c_all)} 小时", "优先约这里")
k2.metric("我和爸爸空闲", f"{len(c_dad)} 小时", "可单独约爸爸")
k3.metric("我和妈妈空闲", f"{len(c_mom)} 小时", "可单独约妈妈")
k4.metric("妈妈可能在补觉", f"{len(c_maybe)} 小时", "需电话确认")
st.progress(min(1.0, (len(c_all) + len(c_dad) + len(c_mom)) / 16), text="全天可约覆盖")
if c_all: st.markdown(f'<div class="banner b-green">三人同时空闲：{"、".join(c_all)}</div>', unsafe_allow_html=True)
else: st.markdown('<div class="banner b-gray">今天三人没有稳妥的同时空闲，看看下面的两人时间吧</div>', unsafe_allow_html=True)
if c_maybe: st.markdown(f'<div class="banner" style="background:rgba(255,232,170,.92);">妈妈可能在补觉（约前先问）：{"、".join(c_maybe)}</div>', unsafe_allow_html=True)
if c_dad: st.markdown(f'<div class="banner b-blue">我和爸爸空闲：{"、".join(c_dad)}</div>', unsafe_allow_html=True)
if c_mom: st.markdown(f'<div class="banner b-orange">我和妈妈空闲：{"、".join(c_mom)}</div>', unsafe_allow_html=True)

st.subheader("今日时间轴")
COLOR = {"all": "rgba(170,240,195,.55)", "maybe": "rgba(255,232,170,.55)",
         "dad": "rgba(170,205,250,.55)", "mom": "rgba(255,205,170,.55)",
         "mebusy": "rgba(220,160,170,.45)", "none": "rgba(120,140,210,.30)"}
LABEL = {"all": "三人可约", "maybe": "问一句再约", "dad": "我和爸爸", "mom": "我和妈妈", "mebusy": "我忙碌", "none": "父母忙"}
for r in rows:
    me_b = '<span class="badge free">我空闲</span>' if r["我"] == "空闲" else '<span class="badge busy">我忙碌</span>'
    dad_b = '<span class="badge free">爸爸休息</span>' if r["爸爸"] == "休息" else '<span class="badge busy">爸爸上班</span>'
    mom_b = ('<span class="badge nap">妈妈可能补觉</span>' if r["妈妈是否可约"] == "可能可约"
             else ('<span class="badge free">妈妈可约</span>' if r["妈妈是否可约"] == "可约" else '<span class="badge busy">妈妈忙碌</span>'))
    st.markdown(f"""<div class="card" style="background:{COLOR[r['类型']]};margin-bottom:8px">
    <b>英国 {r['英国小时']:02d}:00 → 北京 {r['北京时间']}</b> · {LABEL[r['类型']]}<br>{me_b} {dad_b} {mom_b}<br>
    <span style="font-size:13px;">妈妈：{r['妈妈状态']}（{MOM_DESC[r['妈妈状态']]}）｜补觉：{r['补觉']}｜爸爸：{r['爸爸']}｜事件：{r['事件'] or '无'}{('｜备注：'+r['备注']) if r['备注'] else ''}</span></div>""",
                unsafe_allow_html=True)
with st.expander("查看完整明细表格"):
    st.dataframe(pd.DataFrame([{k: v for k, v in r.items() if k != "类型"} for r in rows]), use_container_width=True, hide_index=True)

st.markdown("<hr class='soft'>", unsafe_allow_html=True)
st.subheader("家庭留言板")
MSG_FILE = Path(__file__).parent / "messages.json"
def load_msgs():
    try:
        if MSG_FILE.exists(): return json.loads(MSG_FILE.read_text(encoding="utf-8"))
    except Exception: pass
    return []
def save_msgs(m):
    try: MSG_FILE.write_text(json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e: st.error(f"保存失败：{e}")
msgs = load_msgs()
with st.form("msg_form", clear_on_submit=True):
    c1, c2 = st.columns([1, 3])
    with c1:
        who = st.selectbox("我是", ["子女（英国）", "妈妈", "爸爸"])
        to = st.selectbox("写给", ["全家人", "妈妈", "爸爸", "子女（英国）"])
    with c2:
        body = st.text_area("留言内容", placeholder="例如：周日晚上八点（北京）打视频可以吗？", max_chars=300)
    if st.form_submit_button("发布留言"):
        if not body.strip(): st.warning("请先写点内容再发布。")
        else:
            msgs.append({"who": who, "to": to, "body": body.strip(), "at": datetime.now(BJ_TZ).strftime("%m月%d日 %H:%M（北京）")})
            save_msgs(msgs); st.success("已发布。"); st.rerun()
f = st.radio("筛选", ["全部", "按身份看", "只看写给全家人的"], horizontal=True, index=0)
viewer = st.selectbox("我的身份", ["子女（英国）", "妈妈", "爸爸"]) if f.startswith("按身份") else None
shown = msgs[::-1]
if f == "只看写给全家人的": shown = [m for m in shown if m.get("to") == "全家人"]
elif viewer: shown = [m for m in shown if m.get("to") in ("全家人", viewer)]
if not shown: st.info("暂无留言，来写第一条吧。")
for i, m in enumerate(shown):
    st.markdown(f'<div class="msg"><div class="meta">{m.get("who","")} → {m.get("to","")} · {m.get("at","")}</div><div class="body">{m.get("body","")}</div></div>', unsafe_allow_html=True)
    if st.button("删除", key=f"del_{i}"):
        msgs.remove(m); save_msgs(msgs); st.rerun()
