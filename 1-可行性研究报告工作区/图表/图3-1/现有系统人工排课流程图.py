# -*- coding: utf-8 -*-
"""图 3-1 现有系统（人工排课方式）处理流程与数据流程图，双面板：
(a) 处理流程（算法流程图，教学秘书为人工主体）；(b) 数据流程（人工系统 DFD-0）。
风格与图 2-1 同源；配色 business。矢量 SVG → svgBlip 注入 Word；PNG 目检/兜底。"""
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
ax.set_xlim(0, 100); ax.set_ylim(-3, 100)
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

def diamond(cx, cy, w, h, text):
    ax.add_patch(Polygon([(cx, cy + h/2), (cx + w/2, cy), (cx, cy - h/2), (cx - w/2, cy)],
                         closed=True, fc="#FDF1E2", ec=ACCENT, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs if False else 9.5, color=C_TEXT, zorder=4)

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

def loop(pts, lbl, lx, ly):
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i+1][0]], [pts[i][1], pts[i+1][1]],
                color=C_LOOP, lw=1.0, ls=(0, (4, 2)), zorder=2)
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=C_LOOP, lw=1.0,
                                ls=(0, (4, 2)), shrinkA=0, shrinkB=0), zorder=2)
    ax.text(lx, ly, lbl, ha="center", va="center", fontsize=9, color=C_LOOP, zorder=4)

def branch(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, zorder=4)

def dlabel(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, linespacing=1.35, zorder=4)

# ============ 面板 (a) 处理流程（车道 x=24，人工主体 = 教学秘书） ============
X = 24
capsule(X, 93, 12, 5, "开始")
box(X, 84, 18, 6, "接收教学任务")
box(X, 74.5, 20, 6, "Excel 整理基础表", key=True)
box(X, 65, 18, 6, "经验试排课表", key=True)
box(X, 55.5, 18, 6, "人工检查冲突")
diamond(X, 44, 22, 9, "发现冲突？")
box(X, 32.5, 24, 6, "群消息下发课表截图")
box(X, 23, 16, 6, "教师提出调课")
box(X, 13.5, 20, 6, "手工改表并通知", key=True)
capsule(X, 7, 12, 5, "学期结束")

arrow((X, 90.5), (X, 87))
arrow((X, 81), (X, 77.5))
arrow((X, 71.5), (X, 68))
arrow((X, 62), (X, 58.5))
arrow((X, 52.5), (X, 48.5))
arrow((X, 39.5), (X, 35.5)); branch(X + 2.5, 37.5, "否")
arrow((X, 29.5), (X, 26))
arrow((X, 20), (X, 16.5))
arrow((X, 10.5), (X, 9.3))

loop([(13, 44), (8, 44), (8, 65), (15, 65)], "是", 6.5, 54.5)

dlabel(39.5, 88.5, "教学任务")
dlabel(39.5, 79.2, "课程、教师、" + NL + "教室信息")
dlabel(39.5, 69.8, "四张基础表" + NL + "（Excel）")
dlabel(39.5, 60.3, "候选课表")
dlabel(39.5, 50.8, "疑似冲突清单")
dlabel(39.5, 37.8, "定稿课表")
dlabel(39.5, 27.8, "课表截图" + NL + "群消息")
dlabel(39.5, 8.8, "逐个通知")

ax.text(X, 1.2, "(a) 处理流程", ha="center", va="center", fontsize=10, color=C_TEXT)

# ============ 面板 (b) 数据流程（人工系统 DFD-0，x 54–98） ============
ext(75, 90, 16, 8, "教务处")
store(75, 74, 42, "D1  教学秘书个人 Excel")
box(75, 58, 26, 10, "1" + NL + "人工整理与试排", key=True)
ext(75, 42, 12, 8, "教师")
box(75, 26, 26, 10, "2" + NL + "手工改表与通知", key=True)
ext(75, 10, 12, 8, "学生")

arrow((75, 86), (75, 77)); dlabel(81, 81.5, "教学任务")
arrow((75, 71), (75, 63)); dlabel(81, 67, "四张基础表")
arrow((75, 53), (75, 47)); dlabel(81, 50, "课表截图、群消息")
arrow((75, 38), (75, 31)); dlabel(81, 34.5, "调课需求" + NL + "（口头/群消息）")
arrow((75, 21), (75, 14)); dlabel(81, 17.5, "变更通知")
ax.text(75, 1.2, "(b) 数据流程", ha="center", va="center", fontsize=10, color=C_TEXT)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "现有系统人工排课_business_20261029"
fig.savefig(HERE / ("图3-1_" + stem + ".svg"))
fig.savefig(HERE / ("图3-1_" + stem + "_目检.png"), dpi=600)
plt.close(fig)
print("SVG/PNG 已输出")
