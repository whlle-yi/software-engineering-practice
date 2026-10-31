# -*- coding: utf-8 -*-
"""图 2-1 系统基本处理流程与数据流程图，双面板（最基本/简略版）：
(a) 处理流程（简略流程图，5 个主步骤）；(b) 数据流程（简略 DFD-0，5 元素纵链）。
详细版见 图 4-1（4.2 节）。风格与图 4-1 同源；配色 business。
矢量 SVG → svgBlip 注入 Word；PNG 目检/兜底。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
C_LOOP = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]
NL = chr(10)

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 5.6
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def capsule(cx, cy, w, h, text):
    cr = h / 2
    ax.add_patch(Rectangle((cx - w/2 + cr, cy - cr), w - 2*cr, h, fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.add_patch(Circle((cx - w/2 + cr, cy), cr, fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.add_patch(Circle((cx + w/2 - cr, cy), cr, fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color="white", zorder=4)

def box(cx, cy, w, h, text, key=False, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=0.8",
                                fc=PRIMARY if key else "white",
                                ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color="white" if key else C_TEXT, linespacing=1.3, zorder=4)

def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w/2, cy - h/2), w, h, fc="white", ec=C_LOOP, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def store(cx, cy, w, text, fs=9.5):
    h = 6
    ax.plot([cx - w/2, cx + w/2], [cy + h/2, cy + h/2], color=C_LOOP, lw=1.3, zorder=3)
    ax.plot([cx - w/2, cx + w/2], [cy - h/2, cy - h/2], color=C_LOOP, lw=1.3, zorder=3)
    ax.plot([cx - w/2 + 0.8, cx - w/2 + 0.8], [cy - h/2, cy + h/2], color=C_LOOP, lw=1.1, zorder=3)
    ax.text(cx - w/2 + 2, cy, text, ha="left", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)

def dlabel(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, zorder=4)

# ============ 面板 (a) 处理流程（简略，车道 x=24，5 个主步骤） ============
X = 24
capsule(X, 92, 11, 5, "开始")
box(X, 82, 26, 6, "导入基础数据与排课约束")
box(X, 72, 22, 6, "自动排课与冲突检测", key=True)
box(X, 62, 16, 6, "发布课表")
box(X, 52, 26, 6, "调课审核与重排并通知", key=True)
capsule(X, 42, 11, 5, "结束")

arrow((X, 89.5), (X, 85))
arrow((X, 79), (X, 75))
arrow((X, 69), (X, 65))
arrow((X, 59), (X, 55))
arrow((X, 49), (X, 44.5))
ax.text(X, 36, "(a) 处理流程", ha="center", va="center", fontsize=10, color=C_TEXT)

# ============ 面板 (b) 数据流程（简略 DFD-0，纵链 x=75） ============
ext(75, 92, 14, 8, "教务主系统")
store(75, 76, 34, "D1  基础数据与约束")
box(75, 60, 24, 10, "1" + NL + "自动排课与重排引擎", key=True)
store(75, 44, 30, "D2  课表库")
ext(60, 26, 12, 8, "教师")                       # x54–66 y22–30
ext(88, 26, 12, 8, "学生")                       # x82–94 y22–30

arrow((75, 88), (75, 79)); dlabel(81, 83.5, "教学任务")
arrow((75, 73), (75, 65)); dlabel(81, 69, "四张基础表")
arrow((75, 55), (75, 47))
arrow((75, 41), (75, 36))
arrow((75, 36), (60, 36)); arrow((60, 36), (60, 30)); dlabel(64.5, 37.5, "课表查询")
arrow((75, 36), (90, 36)); arrow((90, 36), (90, 30)); dlabel(85, 37.5, "变更通知")
arrow((54, 26), (65, 26))
ax.text(75, 3.2, "(b) 数据流程", ha="center", va="center", fontsize=10, color=C_TEXT)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "基本处理与数据流_business_20261029"
fig.savefig(HERE / ("图2-1_" + stem + ".svg"))
fig.savefig(HERE / ("图2-1_" + stem + "_目检.png"), dpi=600)
plt.close(fig)
print("SVG/PNG 已输出")
