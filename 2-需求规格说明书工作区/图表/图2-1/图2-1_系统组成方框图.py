# -*- coding: utf-8 -*-
"""图 2-1 系统组成方框图（需求规格说明书 2.1 目标节）。
本系统四个组成模块 + 外部系统（教务主系统/发布渠道）+ 三类用户的联系与接口。
风格与可行性报告图 2-1/3-1/4-1 同源；配色 business；600dpi PNG 注入 docx。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
C_EXT = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]
NL = chr(10)

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 5.9
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1, 99)
ax.set_ylim(3, 100)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def box(cx, cy, w, h, text, key=False, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=0.8",
                                fc=PRIMARY if key else "white",
                                ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color="white" if key else C_TEXT, linespacing=1.3, zorder=4)

def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w/2, cy - h/2), w, h, fc="white", ec=C_EXT, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)

def seg(p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=C_FLOW, lw=1.1, zorder=2)

def label(x, y, text, ha="left"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=9, color=C_FLOW, zorder=4)

# ---- 系统边界（虚线框）----
ax.add_patch(Rectangle((4, 24), 92, 50, fill=False, ec=C_EXT, lw=1.1,
                       linestyle=(0, (4, 3)), zorder=1))
ax.text(50, 70.5, "高校智能排课系统（B/S 架构）", ha="center", va="center",
        fontsize=10.5, color=C_TEXT, zorder=4)

# ---- 顶部外部系统 ----
ext(20, 92, 22, 9, "教务主系统")
ext(80, 92, 22, 9, "教务发布渠道")

# ---- 系统模块 2×2 ----
box(20, 58, 26, 11, "基础数据管理")
box(62, 58, 30, 11, "排课引擎与" + NL + "冲突检测", key=True)
box(20, 32, 26, 11, "调课审核与通知")
box(62, 32, 24, 11, "课表查询与发布")

# ---- 模块间数据流 ----
arrow((33, 58), (47, 58))
arrow((62, 52.5), (62, 37.5))
seg((33, 35), (48, 35)); arrow((48, 35), (48, 52.5)); label(40, 36.8, "局部重排", ha="center")
arrow((33, 32), (50, 32))

# ---- 外部系统接口 ----
arrow((20, 87.5), (20, 63.5)); label(21.5, 76, "教学计划数据")
seg((74, 35), (80, 35)); arrow((80, 35), (80, 87.5))

# ---- 底部用户 ----
ext(16, 10, 16, 9, "教师")
ext(40, 10, 20, 9, "教务管理员")
ext(64, 10, 16, 9, "学生")

arrow((16, 14.5), (16, 26.5)); label(17.5, 20, "调课申请")
arrow((44, 14.5), (44, 24)); label(45.5, 20, "维护·配置·审核")
arrow((36, 24), (36, 14.5)); label(34.5, 16.8, "冲突报告", ha="right")
arrow((64, 26.5), (64, 14.5)); label(65.5, 20, "课表·变更通知")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "系统组成方框图_business_20261031"
fig.savefig(HERE / ("图2-1_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
