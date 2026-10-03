# -*- coding: utf-8 -*-
"""
跨时区家庭日程同步网页
用 Python + Streamlit 写成，方便在浏览器里预览。
暂时不连接数据库，日程和排班都用字典 / 列表里的假数据。
"""

from datetime import datetime, timedelta, time
from zoneinfo import ZoneInfo  # Python 自带的时区库，能自动处理夏令时

import streamlit as st


# ============================================================
# 1. 页面基础设置
# ============================================================
st.set_page_config(
    page_title="跨时区家庭日程",
    page_icon="🗓️",
    layout="wide",  # 宽屏布局，方便左右两列对照
)

# 绿色提示条的样式（页面最上方会用到）
st.markdown(
    """
    <style>
    .shared-rest-banner {
        background: linear-gradient(90deg, #16a34a, #22c55e);
        color: white;
        padding: 1.1rem 1.4rem;
        border-radius: 14px;
        font-size: 1.25rem;
        font-weight: 700;
        text-align: center;
        box-shadow: 0 8px 20px rgba(22, 163, 74, 0.28);
        margin-bottom: 0.8rem;
    }
    .clock-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 0.75rem 0.9rem;
        margin-bottom: 0.6rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 2. 时区：英国会自动在 GMT / BST 之间切换，北京全年 UTC+8
# ============================================================
# Europe/London：冬天是 GMT（格林尼治时间，UTC+0）
#                夏天是 BST（英国夏令时，UTC+1）
# 我们不用自己算哪一天换时，ZoneInfo 会按官方规则自动切换。
UK_TZ = ZoneInfo("Europe/London")
CN_TZ = ZoneInfo("Asia/Shanghai")  # 北京时间，没有夏令时


# ============================================================
# 3. 假数据：英国这边的示例日程（以后可以改成真实日历）
#    每条日程包含：标题、开始时间、结束时间（都按英国本地时间理解）
# ============================================================
DEFAULT_UK_EVENTS = [
    {"title": "网课", "start": "09:00", "end": "11:00"},
    {"title": "超市采购", "start": "12:30", "end": "13:30"},
    {"title": "兼职", "start": "14:00", "end": "18:00"},
]


# 父母排班对应的“上班小时”（按北京时间的整点小时，0~23）
# 不在这个列表里的小时，就当成休息。
PARENT_SHIFT_WORK_HOURS = {
    "早班": list(range(8, 16)),   # 北京时间 08:00–16:00 上班
    "晚班": list(range(16, 24)),  # 北京时间 16:00–24:00 上班
    "休息": [],                   # 全天不上班
}


# ============================================================
# 4. 小工具函数：时间换算、日程判断
# ============================================================
def parse_hhmm(text: str) -> time:
    """把 '09:00' 这种字符串转成 time 对象。"""
    hour, minute = text.split(":")
    return time(int(hour), int(minute))


def uk_label(moment: datetime) -> str:
    """
    根据当前英国时间，显示 GMT 还是 BST。
    moment.dst() 大于 0 就说明正在夏令时。
    """
    is_bst = moment.dst() and moment.dst() != timedelta(0)
    return "BST（夏令时）" if is_bst else "GMT（冬令时）"


def hour_has_uk_event(uk_dt: datetime, events: list[dict]) -> bool:
    """
    判断某个英国时间点，是否落在任何一条英国日程里。
    用“半开区间”：包含开始时间，不包含结束时间。
    例如 09:00–11:00 的课，11:00 整点已经下课，算空闲。
    """
    clock = uk_dt.time()
    for event in events:
        start = parse_hhmm(event["start"])
        end = parse_hhmm(event["end"])
        if start <= clock < end:
            return True
    return False


def parent_is_resting(cn_dt: datetime, shift: str) -> bool:
    """判断某个北京时间点，父母是否处于休息（不上班）。"""
    work_hours = PARENT_SHIFT_WORK_HOURS.get(shift, [])
    return cn_dt.hour not in work_hours


def merge_ranges(slots: list[datetime]) -> list[tuple[datetime, datetime]]:
    """
    把连续的整点空闲时段合并成区间。
    例如 20:00、21:00、22:00 会合并成 20:00–23:00。
    """
    if not slots:
        return []

    ranges = []
    start = slots[0]
    prev = slots[0]
    for current in slots[1:]:
        # 相邻整点：相差正好 1 小时
        if current - prev == timedelta(hours=1):
            prev = current
        else:
            ranges.append((start, prev + timedelta(hours=1)))
            start = current
            prev = current
    ranges.append((start, prev + timedelta(hours=1)))
    return ranges


def format_range(start: datetime, end: datetime, tz) -> str:
    """把一个时间区间格式化成 20:00–22:00 这样的文字。"""
    local_start = start.astimezone(tz)
    local_end = end.astimezone(tz)
    return f"{local_start.strftime('%H:%M')}–{local_end.strftime('%H:%M')}"


def find_shared_rest(
    selected_date,
    uk_events: list[dict],
    parent_shift: str,
) -> list[tuple[datetime, datetime]]:
    """
    核心逻辑：
    1. 把选定那天的每个英国整点拿出来（00:00 到 23:00）
    2. 如果这个整点英国没有日程
    3. 并且换算成北京时间后，父母处于休息
    4. 就把这个整点记下来，最后合并成连续区间
    """
    free_hours = []
    for hour in range(24):
        uk_dt = datetime.combine(selected_date, time(hour, 0), tzinfo=UK_TZ)
        cn_dt = uk_dt.astimezone(CN_TZ)
        uk_free = not hour_has_uk_event(uk_dt, uk_events)
        parents_rest = parent_is_resting(cn_dt, parent_shift)
        if uk_free and parents_rest:
            free_hours.append(uk_dt)
    return merge_ranges(free_hours)


# ============================================================
# 5. 用 session_state 记住页面上的假数据
#    Streamlit 每次点按钮都会重新跑一遍脚本，
#    不存进 session_state 的话，改动会丢失。
# ============================================================
if "uk_events" not in st.session_state:
    st.session_state.uk_events = [event.copy() for event in DEFAULT_UK_EVENTS]


# ============================================================
# 6. 左侧栏：当前英国时间（自动 GMT/BST）和北京时间
# ============================================================
now_utc = datetime.now(tz=ZoneInfo("UTC"))
now_uk = now_utc.astimezone(UK_TZ)
now_cn = now_utc.astimezone(CN_TZ)

with st.sidebar:
    st.header("时区时钟")
    st.caption("英国时间由系统自动判断今天是冬令时还是夏令时。")

    st.markdown(
        f"""
        <div class="clock-card">
            <div>🇬🇧 我在英国</div>
            <div style="font-size:1.6rem;font-weight:700;">
                {now_uk.strftime("%H:%M:%S")}
            </div>
            <div>{now_uk.strftime("%Y-%m-%d")} · {uk_label(now_uk)}</div>
        </div>
        <div class="clock-card">
            <div>🇨🇳 父母在北京</div>
            <div style="font-size:1.6rem;font-weight:700;">
                {now_cn.strftime("%H:%M:%S")}
            </div>
            <div>{now_cn.strftime("%Y-%m-%d")} · 北京时间（UTC+8）</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 注意：now_uk 和 now_cn 是“同一瞬间”的两个钟面。
    # 直接相减会得到 0。要比较的是两边相对 UTC 的偏移。
    # 夏令时 BST：北京快 7 小时；冬令时 GMT：北京快 8 小时。
    offset_hours = int(
        (now_cn.utcoffset() - now_uk.utcoffset()).total_seconds() // 3600
    )
    st.info(f"现在北京比英国快 **{offset_hours} 小时**。")

    st.divider()
    st.subheader("预览哪一天")
    selected_date = st.date_input(
        "选择日期（英国日历）",
        value=now_uk.date(),
        help="换一天可以看看夏令时/冬令时或不同排班下的对照效果。",
    )

    st.caption("提示：点浏览器刷新，或改一下侧边栏选项，时钟会更新。")


# ============================================================
# 7. 页面最上方先留一个“空位”
#    Streamlit 是从上到下执行的。排班按钮在右列，
#    所以这里先占位，等右列选完排班后再把绿色提示填进来。
# ============================================================
if "parent_shift" not in st.session_state:
    st.session_state.parent_shift = "休息"

st.title("跨时区家庭日程同步")
st.caption("左列是你在英国的时间，右列是父母在中国的时间。绿色提示来自两边都空闲的时段。")
banner_slot = st.empty()


# ============================================================
# 8. 主界面两列：英国日程 | 中国父母日程
# ============================================================
left_col, right_col = st.columns(2, gap="large")

with left_col:
    st.subheader("我在英国的日程")
    st.write(f"按英国本地时间显示 · 今天规则是 **{uk_label(now_uk)}**")

    # 用表格把每条日程同时标出对应的北京时间，方便对照
    table_rows = []
    for event in st.session_state.uk_events:
        start_uk = datetime.combine(
            selected_date, parse_hhmm(event["start"]), tzinfo=UK_TZ
        )
        end_uk = datetime.combine(
            selected_date, parse_hhmm(event["end"]), tzinfo=UK_TZ
        )
        table_rows.append(
            {
                "事项": event["title"],
                "英国时间": f"{event['start']}–{event['end']}",
                "对应北京时间": (
                    f"{start_uk.astimezone(CN_TZ).strftime('%H:%M')}"
                    f"–{end_uk.astimezone(CN_TZ).strftime('%H:%M')}"
                ),
            }
        )

    if table_rows:
        st.dataframe(table_rows, hide_index=True, width="stretch")
    else:
        st.success("这一天英国日程是空的，全部时段都可以用来找共同休息。")

    st.markdown("##### 添加一条假日程（预览用）")
    with st.form("add_uk_event", clear_on_submit=True):
        new_title = st.text_input("事项名称", placeholder="例如：去图书馆")
        c1, c2 = st.columns(2)
        new_start = c1.time_input("开始（英国时间）", value=time(19, 0))
        new_end = c2.time_input("结束（英国时间）", value=time(20, 0))
        submitted = st.form_submit_button("加入英国日程")
        if submitted:
            if not new_title.strip():
                st.error("请先填写事项名称。")
            elif new_end <= new_start:
                st.error("结束时间需要晚于开始时间。")
            else:
                st.session_state.uk_events.append(
                    {
                        "title": new_title.strip(),
                        "start": new_start.strftime("%H:%M"),
                        "end": new_end.strftime("%H:%M"),
                    }
                )
                st.rerun()  # 立刻刷新页面，绿色提示会重新计算

    if st.session_state.uk_events:
        st.markdown("##### 删除一条日程")
        labels = [
            f"{item['title']}（{item['start']}–{item['end']}）"
            for item in st.session_state.uk_events
        ]
        to_delete = st.selectbox("选择要删除的事项", labels)
        if st.button("删除选中事项"):
            index = labels.index(to_delete)
            st.session_state.uk_events.pop(index)
            st.rerun()

    if st.button("恢复默认假数据"):
        st.session_state.uk_events = [event.copy() for event in DEFAULT_UK_EVENTS]
        st.rerun()


with right_col:
    st.subheader("父母在中国的日程")
    st.write("目前用按钮模拟排班，不接入真实日历。")

    st.markdown("##### 今天父母的排班")
    # 三个按钮：早班 / 晚班 / 休息
    b1, b2, b3 = st.columns(3)
    if b1.button("早班", width="stretch"):
        st.session_state.parent_shift = "早班"
        st.rerun()
    if b2.button("晚班", width="stretch"):
        st.session_state.parent_shift = "晚班"
        st.rerun()
    if b3.button("休息", width="stretch"):
        st.session_state.parent_shift = "休息"
        st.rerun()

    # 下拉菜单也可以改排班，和按钮指向同一个变量
    st.session_state.parent_shift = st.selectbox(
        "或用下拉菜单选择排班",
        options=["早班", "晚班", "休息"],
        index=["早班", "晚班", "休息"].index(st.session_state.parent_shift),
    )

    shift = st.session_state.parent_shift
    work_hours = PARENT_SHIFT_WORK_HOURS[shift]
    if shift == "休息":
        st.success("父母今天全天休息。")
    else:
        start_h = min(work_hours)
        end_h = max(work_hours) + 1
        st.info(f"父母今天是 **{shift}**：北京时间 {start_h:02d}:00–{end_h:02d}:00 上班，其余时间休息。")

    # 按“英国这一天的每个整点”换算北京时间，再看父母忙不忙
    timeline = []
    for hour in range(24):
        uk_dt = datetime.combine(selected_date, time(hour, 0), tzinfo=UK_TZ)
        cn_dt = uk_dt.astimezone(CN_TZ)
        status = "休息" if parent_is_resting(cn_dt, shift) else "上班"
        timeline.append(
            {
                "英国时间": uk_dt.strftime("%H:%M"),
                "对应北京时间": cn_dt.strftime("%H:%M"),
                "父母状态": status,
            }
        )
    st.dataframe(timeline, hide_index=True, width="stretch", height=420)


# ============================================================
# 9. 右列排班已经选好，现在计算并填入最上方的绿色提示
# ============================================================
shared_ranges = find_shared_rest(
    selected_date,
    st.session_state.uk_events,
    st.session_state.parent_shift,
)

now_is_shared = False
if selected_date == now_uk.date():
    now_is_shared = (not hour_has_uk_event(now_uk, st.session_state.uk_events)) and (
        parent_is_resting(now_cn, st.session_state.parent_shift)
    )

if shared_ranges:
    pieces = []
    for start, end in shared_ranges:
        uk_text = format_range(start, end, UK_TZ)
        cn_text = format_range(start, end, CN_TZ)
        pieces.append(f"英国 {uk_text}（北京 {cn_text}）")
    banner_text = "你们现在的共同休息时间是：" + "；".join(pieces)
    if now_is_shared:
        banner_text = "🟢 此刻可以联系家人！" + banner_text
    banner_slot.markdown(
        f'<div class="shared-rest-banner">{banner_text}</div>',
        unsafe_allow_html=True,
    )
else:
    banner_slot.warning(
        "这一天暂时没有找到共同休息时段。可以试试把父母排班改成「休息」，或删掉几条英国日程。"
    )


# ============================================================
# 10. 底部：按小时对照表，帮助看懂“为什么提示这些时间”
# ============================================================
st.divider()
st.subheader("按小时对照（英国整点 → 北京时间）")

compare_rows = []
for hour in range(24):
    uk_dt = datetime.combine(selected_date, time(hour, 0), tzinfo=UK_TZ)
    cn_dt = uk_dt.astimezone(CN_TZ)
    uk_busy = hour_has_uk_event(uk_dt, st.session_state.uk_events)
    parents_rest = parent_is_resting(cn_dt, st.session_state.parent_shift)
    if (not uk_busy) and parents_rest:
        result = "共同休息"
    elif uk_busy:
        result = "英国有日程"
    else:
        result = "父母在上班"

    compare_rows.append(
        {
            "英国时间": uk_dt.strftime("%H:%M"),
            "北京时间": cn_dt.strftime("%H:%M"),
            "英国是否空闲": "空闲" if not uk_busy else "有事",
            "父母是否休息": "休息" if parents_rest else "上班",
            "判断结果": result,
        }
    )

st.dataframe(compare_rows, hide_index=True, width="stretch")
st.caption(
    "判断规则：英国这一小时没有日程，并且换算成北京时间后父母不上班 → 记为共同休息。"
)
import streamlit as st

st.title("👨‍👩‍👧‍👦 家庭日历 App")
st.write("欢迎来到我们的家庭专属日历！网页发布成功！")
