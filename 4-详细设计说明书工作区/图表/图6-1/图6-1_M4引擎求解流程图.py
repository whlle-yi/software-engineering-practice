# -*- coding: utf-8 -*-
"""图 6-1 M4 自动排课引擎求解流程图（详细设计说明书 6.7 流程逻辑）。
TD 主轴：约束建模→贪心构造初始解→启发式优化（遗传/退火）→冲突检测→输出；
异常出口：不可行报告（左）、防御性回退（右）。配色 business；600dpi PNG。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
C_EXT = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]
NL = chr(10)

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 8.2
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1, 99)
ax.set_ylim(0, 101)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)
ARROW_A = dict(arrowstyle="-|>", color=ACCENT, lw=1.1, shrinkA=0, shrinkB=0)


def capsule(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0,rounding_size=%.2f" % (h / 2),
                                fc="white", ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)


def box(cx, cy, w, h, text, key=False, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.25,rounding_size=0.6",
                                fc=PRIMARY if key else "white",
                                ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color="white" if key else C_TEXT, linespacing=1.3, zorder=4)


def diamond(cx, cy, w, h, text, fs=9):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, fc="white", ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT,
            linespacing=1.25, zorder=4)


def arrow(p0, p1, accent=False, dashed=False):
    st = dict(ARROW_A if accent else ARROW)
    if dashed:
        st["linestyle"] = (0, (4, 3))
    ax.annotate("", xy=p1, xytext=p0, arrowprops=st, zorder=2)


def seg(p0, p1, accent=False, dashed=False):
    st = dict(color=ACCENT if accent else C_FLOW, lw=1.1, zorder=2)
    if dashed:
        st["linestyle"] = (0, (4, 3))
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], **st)


def label(x, y, text, ha="left", fs=9.5, color=None):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs,
            color=color or C_FLOW, zorder=4)


# ---- 主轴（x=46）----
capsule(46, 97, 14, 5.5, "开始")
box(46, 89, 30, 6.5, "读取约束集与基础数据")
box(46, 80.5, 30, 7.5, "约束建模：变量＝课程—时段" + NL + "—教室三元组，硬／软约束分级")
box(46, 71.5, 30, 6.5, "构造初始可行解（贪心＋回溯）", key=True)
diamond(46, 61.5, 20, 11, "初始解构造" + NL + "成功？")
box(46, 51, 30, 7.5, "软约束寻优（遗传／模拟退火，" + NL + "策略可配置）", key=True)
diamond(46, 40.5, 22, 11, "达到迭代上限" + NL + "或收敛？")
box(46, 30, 30, 6.5, "冲突检测（硬约束全量扫描）")
diamond(46, 20.5, 18, 11, "硬冲突＝0？")
para_out = (46, 9.5)

# ---- 输出（平行四边形）----
sk = 3.3
pts = [(46 - 15 + sk, 6.5), (46 + 15, 6.5), (46 + 15 - sk, 12.5), (46 - 15, 12.5)]
ax.add_patch(Polygon(pts, closed=True, fc="white", ec=PRIMARY, lw=1.2, zorder=3))
ax.text(46 + sk * 0.25, 9.5, "输出课表解与优化报告", ha="center", va="center",
        fontsize=9.5, color=C_TEXT, zorder=4)

# ---- 异常出口 ----
box(13, 61.5, 22, 7, "报告不可行：" + NL + "冲突约束提示", fs=9)
box(81, 30, 22, 7, "记录冲突并回退" + NL + "本轮改动", fs=9)

# ---- 主线箭头 ----
arrow((46, 94.25), (46, 92.25))
arrow((46, 85.75), (46, 84.25))
arrow((46, 76.75), (46, 75.25))
arrow((46, 68.25), (46, 67))
label(47.3, 67.6, "")
arrow((46, 56), (46, 54.75))
arrow((46, 47.25), (46, 46))
arrow((46, 35), (46, 33.25))
label(47.3, 34.1, "是")
arrow((46, 26.75), (46, 26))
label(47.3, 25.6, "是")
arrow((46, 15), (46, 12.5))
label(47.3, 13.8, "是")

# ---- 循环回路：未收敛 → 回寻优（虚线，右侧绕外）----
seg((57, 40.5), (66, 40.5), dashed=True)
seg((66, 40.5), (66, 51), dashed=True)
arrow((66, 51), (61, 51), dashed=True)
label(58.5, 41.7, "否")

# ---- 异常出口箭头 ----
arrow((36, 61.5), (24, 61.5))
label(37.5, 62.7, "否", color=ACCENT)
arrow((81, 26.5), (81, 26.5 - 0.0))
seg((55, 20.5), (81, 20.5))
arrow((81, 20.5), (81, 26.5), accent=True)
label(56.5, 21.7, "否", color=ACCENT)
seg((81, 33.5), (81, 49))
arrow((81, 49), (61, 49), accent=True, dashed=True)
label(82.2, 41, "回退后继续寻优", color=ACCENT, fs=9)

fig.subplots_adjust(left=0.01, right=0.99, top=0.995, bottom=0.005)
stem = "M4引擎求解流程图_business_20261114"
fig.savefig(HERE / ("图6-1_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
