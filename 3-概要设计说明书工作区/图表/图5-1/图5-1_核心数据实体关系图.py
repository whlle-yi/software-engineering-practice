# -*- coding: utf-8 -*-
"""图 5-1 核心数据实体关系图（概要设计说明书 5.1）。
三域：基础数据 / 排课业务 / 约束与偏好；连线标注 1:N 一对多。
风格与可行性报告/SRS 配图同源；配色 business；600dpi PNG 注入 docx。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
C_EXT = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 6.2
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 100)
ax.set_ylim(0, 100)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)


def entity(cx, cy, text, w=20, h=7, key=False):
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2), w, h, fc="white",
                           ec=ACCENT if key else PRIMARY, lw=1.3 if key else 1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color=C_TEXT, zorder=4)


def domain(x0, y0, w, h, title, ty, tx):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=C_EXT, lw=1.0,
                           linestyle=(0, (4, 3)), zorder=1))
    ax.text(tx, ty, title, ha="left", va="center", fontsize=9.5, color=C_TEXT, zorder=4)


def edge(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)


def seg(p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=C_FLOW, lw=1.1, zorder=2)


def rel(x, y, rot=0):
    ax.text(x, y, "1:N", ha="center", va="center", fontsize=9.5, color=C_FLOW,
            rotation=rot, zorder=4)


# ---- 域分组 ----
domain(4, 20, 27, 74, "基础数据", 91, 6)
domain(36, 4, 30, 92, "排课业务", 6.5, 38)
domain(69, 36, 28, 60, "约束与偏好", 93.5, 71)

# ---- 实体 ----
entity(17, 84, "课程")
entity(17, 69, "教师")
entity(17, 54, "班级")
entity(17, 39, "学生")
entity(17, 24, "教室")
entity(51, 90, "学期")
entity(51, 68, "开课任务", w=22)
entity(51, 44, "课表记录", w=22, key=True)
entity(51, 18, "调课申请", w=24)
entity(84, 88, "约束配置", w=22)
entity(84, 60, "教师偏好", w=22, key=True)

# ---- 关系（1:N）----
edge((17, 50.5), (17, 42.5)); rel(19.5, 46.5)                       # 班级→学生
seg((27, 84), (44, 84)); edge((44, 84), (44, 71.5)); rel(35.5, 85.3)  # 课程→开课任务
edge((27, 69), (40, 69)); rel(33.5, 70.3)                           # 教师→开课任务
seg((27, 52), (48, 52)); edge((48, 52), (48, 64.5)); rel(37.5, 53.3)  # 班级→开课任务
edge((51, 86.5), (51, 71.5)); rel(53.2, 79)                         # 学期→开课任务
edge((61, 88.5), (73, 88.5)); rel(67, 89.8)                         # 学期→约束配置
seg((61, 87), (70.5, 87)); seg((70.5, 87), (70.5, 60.5))
edge((70.5, 60.5), (73, 60.5)); rel(72.8, 74, rot=90)               # 学期→教师偏好
seg((27, 67), (33, 67)); seg((33, 67), (33, 58.5))
edge((33, 58.5), (73, 58.5)); rel(52, 59.8)                         # 教师→教师偏好
edge((51, 64.5), (51, 47.5)); rel(53.2, 56)                         # 开课任务→课表记录
seg((27, 26), (44, 26)); edge((44, 26), (44, 40.5)); rel(46.2, 33)  # 教室→课表记录
edge((51, 40.5), (51, 21.5)); rel(53.2, 31)                         # 课表记录→调课申请
seg((7, 69), (1.5, 69)); seg((1.5, 69), (1.5, 15.5))
edge((1.5, 15.5), (39, 15.5)); rel(20, 16.9)                        # 教师→调课申请

# 图例
ax.text(2, 1.2, "矩形＝数据实体（详见 5.1 节表）　1:N＝一对多　虚线框＝数据域　橙描边＝设计重点实体",
        ha="left", va="center", fontsize=9.5, color=C_EXT, zorder=4)

fig.subplots_adjust(left=0.01, right=0.99, top=0.995, bottom=0.005)
stem = "核心数据实体关系图_business_20261114"
fig.savefig(HERE / ("图5-1_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
