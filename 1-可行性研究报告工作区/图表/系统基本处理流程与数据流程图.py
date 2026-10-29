# -*- coding: utf-8 -*-
"""图 2-1 系统基本处理流程与数据流程图，双面板（简略版）：
(a) 处理流程（简略算法流程图）；(b) 数据流程（简略 DFD-0）。
详细版见 图 4-1（4.2 节）。风格与图 4-1 同源；配色 business。
矢量 SVG → svgBlip 注入 Word；PNG 目检/兜底。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, Circle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
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

# ============ 面板 (a) 处理流程（简略，车道 x=24） ============
X = 24
capsule(X, 93, 11, 5, "开始")
box(X, 84.5, 26, 6, "导入基础数据与排课约束")
box(X, 75.5, 18, 6, "自动排课", key=True)
box(X, 66.5, 20, 6, "冲突检测与修正")
box(X, 57.5, 16, 6, "发布课表")
box(X, 48.5, 24, 6, "教师提交调课申请")
box(X, 39.5, 22, 6, "审核与局部重排", key=True)
box(X, 30.5, 16, 6, "通知师生")
capsule(X, 21.5, 11, 5, "结束")
arrow((X, 90.5), (X, 87.5))
arrow((X, 81.5), (X, 78.5))
arrow((X, 72.5), (X, 69.5))
arrow((X, 63.5), (X, 60.5))
arrow((X, 54.5), (X, 51.5))
arrow((X, 45.5), (X, 42.5))
arrow((X, 36.5), (X, 33.5))
arrow((X, 27.5), (X, 24))
ax.text(X, 14.5, "(a) 处理流程", ha="center", va="center", fontsize=10, color=C_TEXT)

# ============ 面板 (b) 数据流程（简略 DFD-0，x 50–98） ============
ext(75, 92, 14, 8, "教务主系统")
store(75, 78, 34, "D1  基础数据与约束")
box(75, 62, 20, 10, "1" + NL + "自动排课引擎", key=True)
store(75, 46, 30, "D2  课表库")
ext(52, 62, 14, 8, "教务管理员")
box(75, 24, 20, 10, "2" + NL + "手工改表与通知", key=True)
ext(52, 26, 12, 8, "教师")
ext(75, 10, 12, 8, "学生")

arrow((75, 88), (75, 81)); dlabel(81, 84.5, "教学任务")
arrow((75, 71), (75, 67)); dlabel(81, 69, "四张基础表")
arrow((66, 62), (59, 62)); dlabel(62.5, 64.5, "冲突报告")
arrow((59, 58), (66, 58)); dlabel(62.5, 55.5, "运行指令")
arrow((75, 53), (75, 51))
arrow((75, 41), (75, 37)); dlabel(81, 39, "课表查询、变更通知")
arrow((75, 29), (75, 29))
arrow((69, 26), (64, 26)); dlabel(66.5, 28.5, "调课申请")
arrow((75, 19), (75, 14)); dlabel(81, 16.5, "变更通知")
ax.text(75, 2.5, "(b) 数据流程", ha="center", va="center", fontsize=10, color=C_TEXT)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "基本处理与数据流_business_20261029"
fig.savefig(HERE / ("图2-1_" + stem + ".svg"))
fig.savefig(HERE / ("图2-1_" + stem + "_目检.png"), dpi=200)
plt.close(fig)
print("SVG/PNG 已输出")
