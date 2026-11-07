# -*- coding: utf-8 -*-
"""图 3-2 现有系统（人工排课方式）数据流程图（DFD 0 层）。
规范：特定图指定方法/数据流程图制作方法.md——白底、深蓝 #1B3770、加工=圆（编号+动宾）、
数据存储=双横线（编号+名称）、每条数据流必须命名；圆周交点进圆。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

HERE = Path(__file__).resolve().parent
BLUE = "#1B3770"

plt.rcParams.update({"font.family": ["Times New Roman", "SimHei"], "savefig.bbox": None})

fig, ax = plt.subplots(figsize=(6.1, 5.0))
ax.set_xlim(1, 78.5)
ax.set_ylim(5.5, 74.5)
ax.axis("off")


def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc="white", ec=BLUE, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=BLUE, zorder=4)


def proc(cx, cy, r, num, name):
    ax.add_patch(Circle((cx, cy), r, fc="white", ec=BLUE, lw=1.1, zorder=3))
    ax.text(cx, cy + r * 0.44, num, ha="center", va="center", fontsize=9, color=BLUE, zorder=4)
    ax.text(cx, cy - r * 0.34, name, ha="center", va="center", fontsize=8.5,
            color=BLUE, linespacing=1.15, zorder=4)


def store(cx, cy, w, text, fs=8.5):
    ax.plot([cx - w / 2, cx + w / 2], [cy + 3, cy + 3], color=BLUE, lw=1.0, zorder=3)
    ax.plot([cx - w / 2, cx + w / 2], [cy - 3, cy - 3], color=BLUE, lw=1.0, zorder=3)
    ax.text(cx - w / 2 + 2, cy, text, ha="left", va="center", fontsize=fs, color=BLUE, zorder=4)


def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.1,
                                shrinkA=0, shrinkB=0), zorder=2)


def label(x, y, text, ha="center", rotation=0):
    ax.text(x, y, text, ha=ha, va="center", fontsize=8.5, color=BLUE,
            rotation=rotation, zorder=4)


# ---- 外部实体 / 加工 / 数据存储 ----
ext(10, 65, 14, 8, "教务处")
proc(38, 65, 8, "1", "人工整理\n与试排")
ext(70, 65, 14, 8, "任课教师")
store(38, 40, 26, "D1  教学秘书个人 Excel")
proc(38, 15, 8, "2", "手工改表\n与通知")
ext(14, 15, 14, 8, "学生")

# ---- 数据流（全部命名；圆周交点进圆）----
arrow((17, 65), (30, 65))                      # 教务处→1
label(23.5, 67, "教学任务")
arrow((46, 65), (63, 65))                      # 1→任课教师
label(54.5, 67, "课表截图、群消息")
elbow_t = [(70, 61), (70, 15), (46, 15)]       # 任课教师→2
for i in range(len(elbow_t) - 2):
    ax.plot([elbow_t[i][0], elbow_t[i + 1][0]], [elbow_t[i][1], elbow_t[i + 1][1]],
            color=BLUE, lw=1.1, zorder=2)
arrow(elbow_t[-2], elbow_t[-1])
label(67.8, 38, "调课需求", rotation=90)
arrow((30, 15), (21, 15))                      # 2→学生
label(25.5, 17, "变更通知")
arrow((38, 57), (38, 43))                      # 1→D1
label(34.5, 50, "试排课表与基础数据", rotation=90)
arrow((38, 23), (38, 37))                      # 2→D1
label(39.8, 30, "改后课表", rotation=90)

OUT = HERE / "现有系统数据流程图_20261107_目检.png"
fig.savefig(OUT, dpi=600)
plt.close(fig)
print("已输出:", OUT)
