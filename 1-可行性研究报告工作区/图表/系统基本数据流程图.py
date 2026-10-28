# -*- coding: utf-8 -*-
"""图 2-1 系统基本处理流程与数据流程图（顶层 DFD-0，T2 报告级 / business）。

矢量源 SVG（文字转轮廓）→ svgBlip 注入 Word；PNG 仅供目检与兜底。
布局：全正交连线（水平/垂直）。DFD 形状语义：直角矩形=外部实体、
圆角矩形=加工（编号 1/2）、双横线开口框=数据存储（D1/D2）；箭头 = 数据流向。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path(r"C:\Users\32530\.zcode\skills\pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

C_PROC = PALETTE["primary"]
C_PROC_FILL = "#DEEBF7"
C_EXT = PALETTE["neutral"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 5.0
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.axis("off")

def ext(cx, cy, w, h, text, fs=10):
    ax.add_patch(Rectangle((cx - w/2, cy - h/2), w, h, fc="white", ec=C_EXT, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def proc(cx, cy, w, h, text, fs=10):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=1.5",
                                fc=C_PROC_FILL, ec=C_PROC, lw=1.8, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT,
            linespacing=1.3, zorder=4)

def store(cx, cy, w, text, fs=10):
    """数据存储：双横线（上下边）、左侧竖线短标，文字在横线间。"""
    h = 6
    ax.plot([cx - w/2, cx + w/2], [cy + h/2, cy + h/2], color=C_EXT, lw=1.3, zorder=3)
    ax.plot([cx - w/2, cx + w/2], [cy - h/2, cy - h/2], color=C_EXT, lw=1.3, zorder=3)
    ax.plot([cx - w/2 + 0.8, cx - w/2 + 0.8], [cy - h/2, cy + h/2], color=C_EXT, lw=1.1, zorder=3)
    ax.text(cx - w/2 + 2, cy, text, ha="left", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0), zorder=2)

def label(x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=9, color=C_FLOW, linespacing=1.35, zorder=4)

# ---- 节点 ----
ext(10, 85, 13, 9, "教务主系统")                 # x3.5–16.5 y80.5–89.5
store(40, 85, 36, "D1  基础数据与约束")           # 线 x22–58 y82/88
proc(40, 55, 16, 12, "1\n自动排课引擎")           # x32–48 y49–61
store(72, 55, 34, "D2  课表库")                  # 线 x55–89 y52/58
ext(88, 74, 13, 8, "教师")                       # x81.5–94.5 y70–78
ext(30, 66, 14, 8, "教室管理部门")                # x23–37 y62–70
ext(12, 55, 13, 9, "教务管理员")                  # x5.5–18.5 y50.5–59.5
proc(55, 25, 17, 10, "2\n调课审核与重排")         # x46.5–63.5 y20–30
ext(18, 25, 13, 8, "学生")                       # x11.5–24.5 y21–29

# ---- 数据流 ----
arrow((16.5, 85), (21.5, 85))            # 教务主系统 → D1
label(10, 76, "教学计划\n选课名单")
arrow((30, 70), (30, 82))                # 教室管理部门 → D1（垂直上行）
label(36.5, 76, "教室\n资源数据")
arrow((40, 82), (40, 61))                # D1 → 加工1
label(46, 71.5, "基础数据\n与约束")
arrow((48, 55), (55, 55))                # 加工1 → D2
label(51.5, 60.5, "无冲突\n课表")
arrow((86, 52), (86, 70))                # D2 → 教师
label(79.5, 61, "课表查询")
arrow((92, 70), (92, 30))                # 教师垂直下行
arrow((92, 30), (63.5, 30))              # → 水平入加工2
label(78.5, 33.5, "调课/代课申请")
arrow((62, 30), (62, 52))                # 加工2 → D2
label(67.5, 41, "更新课表")
arrow((46.5, 25), (24.5, 25))            # 加工2 → 学生
label(35.5, 27.5, "变更通知")
arrow((32, 58), (18.5, 58))              # 加工1 → 管理员
label(25, 61, "冲突报告")
arrow((18.5, 52), (32, 52))              # 管理员 → 加工1
label(25, 48.5, "运行指令")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "基本数据流_business_20261029"
fig.savefig(HERE / f"图2-1_{stem}.svg")
fig.savefig(HERE / f"图2-1_{stem}_目检.png", dpi=200)
plt.close(fig)
print("SVG/PNG 已输出")
