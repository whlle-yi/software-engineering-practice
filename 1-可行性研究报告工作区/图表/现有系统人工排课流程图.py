# -*- coding: utf-8 -*-
"""图 3-1 现有系统（人工排课方式）处理流程图（T2 报告级 / business）。

流程图风格与图 2-1 同源：胶囊起止、矩形处理、菱形判断（是/否）、虚线回环。
主语 = 教学秘书（人工）；箭头标签标注数据载体（Excel 表、截图、群消息），
体现人工系统的数据流程。配色 business：primary 实心 = 人工瓶颈环节；
accent 菱形判断；neutral 虚线回环。矢量 SVG → svgBlip 注入 Word；PNG 目检/兜底。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path(r"C:\Users\32530\.zcode\skills\pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
C_LOOP = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 3.6, 5.4
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(24, 68); ax.set_ylim(3, 96)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def capsule(cx, cy, w, h, text):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle=f"round,pad=0.3,rounding_size={h/2 - 0.3}",
                                fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color="white", zorder=4)

def box(cx, cy, w, h, text, key=False, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=0.8",
                                fc=PRIMARY if key else "white",
                                ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color="white" if key else C_TEXT, zorder=4)

def diamond(cx, cy, w, h, text):
    ax.add_patch(Polygon([(cx, cy + h/2), (cx + w/2, cy), (cx, cy - h/2), (cx - w/2, cy)],
                         closed=True, fc="#FDF1E2", ec=ACCENT, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)

def branch(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, zorder=4)

def loop(pts):
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i+1][0]], [pts[i][1], pts[i+1][1]],
                color=C_LOOP, lw=1.0, ls=(0, (4, 2)), zorder=2)
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=C_LOOP, lw=1.0,
                                ls=(0, (4, 2)), shrinkA=0, shrinkB=0), zorder=2)

def dlabel(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, linespacing=1.35, zorder=4)

# ---- 节点（主语 = 教学秘书，人工处理）----
capsule(42.5, 93, 12, 5, "开始")
box(42.5, 84, 18, 6, "接收教学任务")
box(42.5, 74.5, 20, 6, "Excel 整理基础表", key=True)
box(42.5, 65, 18, 6, "经验试排课表", key=True)
box(42.5, 55.5, 18, 6, "人工检查冲突")
diamond(42.5, 44, 22, 9, "发现冲突？")
box(42.5, 32.5, 24, 6, "群消息下发课表截图")
box(42.5, 23, 16, 6, "教师提出调课")
box(42.5, 13.5, 20, 6, "手工改表并通知", key=True)
capsule(42.5, 5, 12, 5, "学期结束")

# ---- 处理流（箭头 = 步骤顺序）----
arrow((42.5, 90.5), (42.5, 87))
arrow((42.5, 81), (42.5, 77.5))
arrow((42.5, 71.5), (42.5, 68))
arrow((42.5, 62), (42.5, 58.5))
arrow((42.5, 52.5), (42.5, 48.5))
arrow((42.5, 39.5), (42.5, 35.5)); branch(44.5, 37.5, "否")
arrow((42.5, 29.5), (42.5, 26))
arrow((42.5, 20), (42.5, 16.5))
arrow((42.5, 10.5), (42.5, 7.5))

# ---- 冲突回环（是 → 调整后重排，绕左）----
loop([(31.5, 44), (27, 44), (27, 65), (33.5, 65)])
branch(28.5, 55, "是")

# ---- 数据载体标签（箭头右侧，体现人工系统的数据流程）----
dlabel(55.5, 88.7, "教学任务")
dlabel(55.5, 79.2, "课程、教师、\n教室信息")
dlabel(55.5, 69.8, "四张基础表\n（Excel）")
dlabel(55.5, 60.3, "候选课表")
dlabel(55.5, 50.8, "疑似冲突清单")
dlabel(55.5, 37.8, "定稿课表")
dlabel(55.5, 27.8, "课表截图\n群消息")
dlabel(55.5, 18.3, "调课需求\n（口头/群消息）")
dlabel(55.5, 8.8, "逐个通知")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "现有系统人工排课_business_20261029"
fig.savefig(HERE / f"图3-1_{stem}.svg")
fig.savefig(HERE / f"图3-1_{stem}_目检.png", dpi=200)
plt.close(fig)
print("SVG/PNG 已输出")
