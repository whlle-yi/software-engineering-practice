# -*- coding: utf-8 -*-
"""图 4-2 所建议系统数据流程图（DFD 0 层，可行性研究报告 4.2 节；结构与需求说明书图 3-2 保持一致）。
4 个加工（1 基础数据管理 / 2 排课与冲突检测 / 3 调课审核与重排 / 4 课表查询与通知）、
3 个数据存储（D1 基础数据与约束 / D2 课表库 / D3 调课记录）与外部实体。
规范：特定图指定方法/数据流程图制作方法.md——白底、深蓝 #1B3770、加工=圆（编号+名称）、
数据存储=双横线（编号+名称）、每条数据流必须命名；指向加工圆的箭头按圆周交点计算。"""
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

HERE = Path(__file__).resolve().parent
BLUE = "#1B3770"
NL = chr(10)

plt.rcParams.update({"font.family": ["Times New Roman", "SimHei"], "savefig.bbox": None})

FIG_W, FIG_H = 6.1, 5.9
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1, 99)
ax.set_ylim(1, 97)
ax.axis("off")


def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc="white", ec=BLUE, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=BLUE, zorder=4)


def rim(cx, cy, r, tx, ty):
    """圆周交点：从圆心指向 (tx,ty)，返回箭头应落的圆周点。"""
    dx, dy = tx - cx, ty - cy
    L = (dx * dx + dy * dy) ** 0.5
    return cx + r * dx / L, cy + r * dy / L


def proc(cx, cy, r, num, name):
    ax.add_patch(Circle((cx, cy), r, fc="white", ec=BLUE, lw=1.1, zorder=3))
    ax.text(cx, cy + r * 0.45, num, ha="center", va="center", fontsize=9, color=BLUE, zorder=4)
    ax.text(cx, cy - r * 0.45, name, ha="center", va="center", fontsize=8.5, color=BLUE, zorder=4)


def store(cx, cy, w, text, fs=9):
    """数据存储：双横线（左端开口），文字置于两线之间。"""
    ax.plot([cx - w / 2, cx + w / 2], [cy + 3, cy + 3], color=BLUE, lw=1.0, zorder=3)
    ax.plot([cx - w / 2, cx + w / 2], [cy - 3, cy - 3], color=BLUE, lw=1.0, zorder=3)
    ax.text(cx - w / 2 + 2, cy, text, ha="left", va="center", fontsize=fs, color=BLUE, zorder=4)


def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=BLUE, lw=1.1,
                                shrinkA=0, shrinkB=0), zorder=2)


def seg(p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=BLUE, lw=1.1, zorder=2)


def label(x, y, text, ha="center", rotation=0):
    ax.text(x, y, text, ha=ha, va="center", fontsize=8.5, color=BLUE,
            rotation=rotation, zorder=4)


# ---- 加工（圆：编号 + 名称）----
P1 = (50, 88, 9)      # 1 基础数据管理
P2 = (50, 58, 9.5)    # 2 排课与冲突检测
P3 = (85, 52, 8.5)    # 3 调课审核与重排
P4 = (50, 24, 9.5)    # 4 课表查询与通知
proc(*P1[:2], P1[2], "1", "基础数据管理")
proc(*P2[:2], P2[2], "2", "排课与冲突检测")
proc(*P3[:2], P3[2], "3", "调课审核与重排")
proc(*P4[:2], P4[2], "4", "课表查询与通知")

# ---- 数据存储（双横线）----
store(50, 40, 24, "D2  课表库")
store(79, 19, 18, "D3  调课记录")
store(50, 73, 26, "D1  基础数据与约束")

# ---- 外部实体 ----
ext(13, 88, 20, 9, "教务主系统")
ext(13, 56, 18, 9, "教务管理员")
ext(91, 8, 16, 8, "教师")
ext(50, 7, 16, 8, "学生")
ext(13, 27, 16, 8, "教务发布渠道")

# ---- 中央链（每条流已命名）----
arrow((23, 88), (P1[0] - P1[2], 88))                       # 教务主系统→1
label(30, 90.3, "教学计划" + NL + "选课名单")
arrow((50, P1[1] - P1[2]), (50, 76))                       # 1→D1
label(52.5, 77.5, "基础数据", ha="left")
arrow((50, 70), (P2[0], P2[1] + P2[2]))                    # D1→2
label(52.5, 68.8, "基础数据与约束", ha="left")
arrow((50, P2[1] - P2[2]), (50, 43))                       # 2→D2
label(52.5, 45.8, "课表", ha="left")
arrow((50, 37), (P4[0], P4[1] + P4[2]))                    # D2→4
label(52.5, 35.3, "课表", ha="left")

# ---- 左侧：管理员 / 发布渠道 ----
seg((13, 60.5), (13, 79))
seg((13, 79), (41, 79))
arrow((41, 79), (41, 88))                                   # 管理员→1（W 点进入）
label(27, 80.8, "教室数据·约束配置")
arrow((P2[0] - P2[2], 58), (22, 58))                       # 2→管理员
label(31, 59.8, "冲突检测报告")
seg((13, 60.5), (13, 71))
seg((13, 71), (85, 71))
arrow((85, 71), rim(*P3[:2], P3[2], 85, 71))               # 管理员→3
label(24, 72.3, "审核指令")
arrow((P4[0] - P4[2], 24), (21, 24))                       # 4→发布渠道
label(30, 25.8, "课表发布数据")

# ---- 右列：调课闭环 ----
seg((P2[0] + P2[2], 58), (68, 58))                         # 2→3（中段无箭头）
seg((68, 58), (68, 53.5))
arrow((68, 53.5), (76.63, 53.5))
label(61, 60.3, "无冲突课表")
seg((76.5, 50.5), (66, 50.5))                               # 3→2
arrow((66, 50.5), (55.83, 50.5))
label(66, 48, "重排指令")
arrow((85, P3[1] - P3[2]), (85, 22))                       # 3→D3
label(83.2, 32, "调课记录", ha="center", rotation=90)
arrow((90, 12.25), (90, 45.13))                             # 教师→3
label(88.5, 27, "调课申请", ha="center", rotation=90)
seg((P3[0] + P3[2], 52), (96, 52))
seg((96, 52), (96, 12.25))                                 # 3→教师
arrow((96, 52), (96, 12.25))
label(97.3, 27, "调课通知", ha="center", rotation=90)

# ---- 底部：学生 ----
arrow((P4[0], P4[1] - P4[2]), (50, 11))                    # 4→学生
label(44, 12, "课表·变更通知", ha="right")
arrow((54, 11), (54, 15.38))                                # 学生→4
label(55.5, 13, "冲突反馈", ha="left")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "0层数据流图_20261108"
fig.savefig(HERE / ("图4-2_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
