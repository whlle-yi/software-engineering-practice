# -*- coding: utf-8 -*-
"""图 3-1 顶层数据流图（DFD 顶层，需求规格说明书 3.1 节）。
单一加工「0 高校排课系统（PiAgent 赋能）」与 5 类外部实体的数据流动。
符号约定：矩形=外部实体，圆角框=加工，箭头=数据流。配色 business。
（2026-11-01 收紧垂直布局：顶/底外部实体向中央靠拢，画布压扁）"""
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

FIG_W, FIG_H = 6.1, 4.4
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1, 99)
ax.set_ylim(8, 90)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def proc(cx, cy, w, h, num, text):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=1.2",
                                fc=PRIMARY, ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy + 2.2, num, ha="center", va="center", fontsize=10,
            color="white", fontweight="bold", zorder=4)
    ax.text(cx, cy - 2.6, text, ha="center", va="center", fontsize=10,
            color="white", zorder=4)

def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w/2, cy - h/2), w, h, fc="white", ec=C_EXT, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)

def seg(p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=C_FLOW, lw=1.1, zorder=2)

def label(x, y, text, ha="left"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=9, color=C_FLOW, zorder=4)

# ---- 中央加工 ----
proc(50, 52, 34, 16, "0", "高校排课系统\n（PiAgent 赋能）")

# ---- 外部实体 ----
ext(16, 81, 20, 9, "教务主系统")
ext(84, 81, 20, 9, "教务发布渠道")
ext(16, 20, 18, 9, "教务管理员")
ext(45, 16, 16, 9, "教师")
ext(82, 16, 16, 9, "学生")

# ---- 数据流 ----
# 教务主系统 → 系统
seg((16, 76.5), (16, 56)); arrow((16, 56), (33, 56))
label(14.5, 66.5, "教学计划" + NL + "选课名单", ha="right")
# 系统 → 教务发布渠道
seg((67, 58), (84, 58)); arrow((84, 58), (84, 76.5))
label(68, 60.2, "课表发布数据")
# 管理员 → 系统（内侧上行）/ 系统 → 管理员（外侧下行），两线不交叉
seg((22, 24.5), (22, 46)); arrow((22, 46), (33, 46))
label(23.5, 35, "基础数据·约束" + NL + "审核指令")
seg((33, 52), (10, 52)); seg((10, 52), (10, 27.5)); arrow((10, 27.5), (10, 24.5))
label(21, 49.6, "冲突检测报告", ha="center")
# 教师 → 系统 / 系统 → 教师
arrow((45, 20.5), (45, 44)); label(43.5, 32, "调课申请", ha="right")
arrow((51, 44), (51, 20.5))
label(52.5, 32, "审核结果" + NL + "课表通知")
# 学生 → 系统 / 系统 → 学生
seg((78, 20.5), (78, 46)); arrow((78, 46), (67, 46))
label(76.5, 31, "冲突反馈", ha="right")
seg((67, 52), (86, 52)); seg((86, 52), (86, 23.5)); arrow((86, 23.5), (86, 20.5))
label(88, 36, "课表·变更" + NL + "通知")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "顶层数据流图_business_20261031"
fig.savefig(HERE / ("图3-1_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
