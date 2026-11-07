# -*- coding: utf-8 -*-
"""图 3-1 顶层数据流图（DFD 顶层，需求规格说明书 3.1 节）。
规范：特定图指定方法/数据流程图制作方法.md——白底、深蓝 #1B3770、加工=圆（顶层不编号）、
外部实体=方框、数据流必须命名；指向加工圆的箭头按圆周交点计算。"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

HERE = Path(__file__).resolve().parent
BLUE = "#1B3770"
NL = chr(10)

plt.rcParams.update({"font.family": ["Times New Roman", "SimHei"], "savefig.bbox": None})

FIG_W, FIG_H = 6.1, 4.4
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1, 99)
ax.set_ylim(8, 90)
ax.axis("off")


def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc="white", ec=BLUE, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=BLUE, zorder=4)


def rim(cx, cy, r, tx, ty):
    """圆周交点：从圆心指向 (tx,ty)，返回箭头应落的圆周点。"""
    dx, dy = tx - cx, ty - cy
    L = (dx * dx + dy * dy) ** 0.5
    return cx + r * dx / L, cy + r * dy / L


def hx(y, side):
    """水平进/出圆的弦点：side -1 左 / +1 右（正交流用此，禁止斜进）。"""
    dx = (R * R - (y - CY) ** 2) ** 0.5
    return CX + side * dx, y


def vy(x, side):
    """垂直进/出圆的弦点：side -1 下 / +1 上。"""
    dy = (R * R - (x - CX) ** 2) ** 0.5
    return x, CY + side * dy


def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.1,
                                shrinkA=0, shrinkB=0), zorder=2)


def seg(p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=BLUE, lw=1.1, zorder=2)


def label(x, y, text, ha="left"):
    ax.text(x, y, text, ha=ha, va="center", fontsize=9, color=BLUE, zorder=4)


# ---- 中央加工（顶层：一个加工，不编号）----
CX, CY, R = 50, 52, 13
ax.add_patch(Circle((CX, CY), R, fc="white", ec=BLUE, lw=1.2, zorder=3))
ax.text(CX, CY + 3.4, "PiAgent赋能的", ha="center", va="center", fontsize=9.5, color=BLUE, zorder=4)
ax.text(CX, CY - 3.4, "高校排课系统", ha="center", va="center", fontsize=9.5, color=BLUE, zorder=4)

# ---- 外部实体 ----
ext(16, 81, 20, 9, "教务主系统")
ext(84, 81, 20, 9, "教务发布渠道")
ext(16, 20, 18, 9, "教务管理员")
ext(45, 16, 16, 9, "教师")
ext(82, 16, 16, 9, "学生")

# ---- 数据流（端点按圆周交点；每条已命名）----
# 教务主系统 → 系统（教学计划/选课名单）：下行后水平进入圆周
seg((16, 76.5), (16, 56))
arrow((16, 56), hx(56, -1))
label(14.5, 66.5, "教学计划" + NL + "选课名单", ha="right")
# 系统 → 教务发布渠道（课表发布数据）：圆周右侧出
seg(hx(58, 1), (84, 58))
arrow((84, 58), (84, 76.5))
label(66.5, 60.2, "课表发布数据")
# 教务管理员 → 系统（基础数据·约束/审核指令）
seg((22, 24.5), (22, 46))
arrow((22, 46), hx(46, -1))
label(23.5, 35, "基础数据·约束" + NL + "审核指令")
# 系统 → 教务管理员（冲突检测报告）：圆周左侧出
seg(hx(52, -1), (10, 52))
seg((10, 52), (10, 27.5))
arrow((10, 27.5), (10, 24.5))
label(21, 49.6, "冲突检测报告", ha="center")
# 教师 → 系统（调课申请）：垂直进入圆周
arrow((45, 20.5), vy(45, -1))
label(43.5, 32, "调课申请", ha="right")
# 系统 → 教师（审核结果/课表通知）：圆周右下出
arrow(vy(51, -1), (51, 20.5))
label(52.5, 32, "审核结果" + NL + "课表通知")
# 学生 → 系统（冲突反馈）：上行后水平进入圆周
seg((78, 20.5), (78, 46))
arrow((78, 46), hx(46, 1))
label(76.5, 31, "冲突反馈", ha="right")
# 系统 → 学生（课表·变更通知）：圆周右侧出、下行进学生顶
seg(hx(52, 1), (86, 52))
seg((86, 52), (86, 23.5))
arrow((86, 23.5), (86, 20.5))
label(88, 36, "课表·变更" + NL + "通知")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "顶层数据流图_20261107"
fig.savefig(HERE / ("图3-1_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
