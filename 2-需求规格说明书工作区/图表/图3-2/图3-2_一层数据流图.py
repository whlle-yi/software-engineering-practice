# -*- coding: utf-8 -*-
"""图 3-2 一层数据流图（DFD 1 层，需求规格说明书 3.1 节）。
4 个加工（1 基础数据管理 / 2 排课与冲突检测 / 3 调课审核与重排 / 4 课表查询与通知）、
3 个数据存储（D1 基础数据与约束 / D2 课表库 / D3 调课记录）与外部实体。
符号约定：矩形=外部实体，圆角框=加工（编号），双横线=数据存储，箭头=数据流。
风格与图 3-1 同源；配色 business。"""
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
ax.set_ylim(1, 97)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def proc(cx, cy, w, h, num, text, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=1.0",
                                fc=PRIMARY, ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy + 2.3, num, ha="center", va="center", fontsize=9.5,
            color="white", zorder=4)
    ax.text(cx, cy - 2.5, text, ha="center", va="center", fontsize=fs,
            color="white", zorder=4)

def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w/2, cy - h/2), w, h, fc="white", ec=C_EXT, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def store(cx, cy, w, text, fs=9.5):
    h = 6
    ax.plot([cx - w/2, cx + w/2], [cy + h/2, cy + h/2], color=C_EXT, lw=1.3, zorder=3)
    ax.plot([cx - w/2, cx + w/2], [cy - h/2, cy - h/2], color=C_EXT, lw=1.3, zorder=3)
    ax.plot([cx - w/2 + 0.8, cx - w/2 + 0.8], [cy - h/2, cy + h/2], color=C_EXT, lw=1.1, zorder=3)
    ax.text(cx - w/2 + 2, cy, text, ha="left", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)

def seg(p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=C_FLOW, lw=1.1, zorder=2)

def label(x, y, text, ha="left"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=9, color=C_FLOW, zorder=4)

# ---- 加工（中央链 + 右列）----
proc(50, 88, 26, 9, "1", "基础数据管理")
proc(50, 58, 24, 11, "2", "排课与冲突检测")
proc(85, 52, 20, 12, "3", "调课审核" + NL + "与重排")
proc(50, 24, 24, 11, "4", "课表查询与通知")

# ---- 数据存储 ----
store(50, 72, 26, "D1  基础数据与约束")
store(50, 40, 24, "D2  课表库")
store(79, 19, 18, "D3  调课记录")

# ---- 外部实体 ----
ext(13, 88, 20, 9, "教务主系统")
ext(13, 56, 18, 9, "教务管理员")
ext(90, 8, 16, 8.5, "教师")
ext(50, 8.5, 16, 8, "学生")

# ---- 中央链数据流 ----
arrow((23, 88), (37, 88)); label(30, 90.3, "教学计划数据", ha="center")
arrow((50, 83.5), (50, 75)); label(51.5, 79.2, "基础数据入库")
arrow((50, 69), (50, 63.5)); label(48.5, 65.8, "排课输入", ha="right")
arrow((50, 52.5), (50, 43)); label(48.5, 47.8, "无冲突课表", ha="right")
arrow((50, 37), (50, 29.5)); label(51.5, 33.2, "课表数据")

# ---- 左侧：管理员 ----
seg((13, 60.5), (13, 79)); seg((13, 79), (40, 79)); arrow((40, 79), (40, 83.5))
label(14.5, 75.5, "教室数据·约束配置")
arrow((38, 55), (22, 55)); label(30, 57, "冲突检测报告", ha="center")
seg((17, 60.5), (17, 68)); seg((17, 68), (85, 68)); arrow((85, 68), (85, 58))
label(24, 69.6, "审核指令", ha="center")

# ---- 右列：调课闭环 ----
seg((62, 42), (68, 42)); seg((68, 42), (68, 52)); arrow((68, 52), (75, 52))
label(66.5, 47, "课表读取", ha="right")
seg((75, 49), (71, 49)); seg((71, 49), (71, 40)); arrow((71, 40), (62, 40))
label(72.5, 43.8, "重排结果")
arrow((77, 46), (77, 22)); label(75.5, 32, "审核记录", ha="right")
arrow((93, 12.25), (93, 46)); label(91.5, 30, "调课申请", ha="right")
seg((62, 21), (67, 21)); seg((67, 21), (67, 2.5)); seg((67, 2.5), (90, 2.5))
arrow((90, 2.5), (90, 3.75))
label(74, 4.5, "调课通知", ha="center")

# ---- 底部：学生 ----
arrow((46, 18.5), (46, 12.5)); label(44.5, 16.5, "课表·变更通知", ha="right")
arrow((54, 12.5), (54, 18.5)); label(55.5, 13.5, "冲突反馈")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "一层数据流图_business_20261031"
fig.savefig(HERE / ("图3-2_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
