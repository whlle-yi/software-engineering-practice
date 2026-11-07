# -*- coding: utf-8 -*-
"""图 3-1 现有系统（人工排课方式）处理流程图（泳道图）。
规范：特定图指定方法/处理流程图制作方法.md（配色实测自老师参考图）。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

NAVY, STEP, RED = "#001F5F", "#DEEBF7", "#D34F4F"
BG, LINE, TEXT, EXC = "#F5F8FC", "#CED4E0", "#121212", "#FAE7E7"
plt.rcParams.update({"font.family": ["Times New Roman", "SimHei"]})

fig, ax = plt.subplots(figsize=(6.1, 5.6))
ax.set_xlim(0, 100); ax.set_ylim(4, 92); ax.axis("off")

# ---- 泳道 ----
LANES = ["教学秘书", "任课教师", "学生"]
LW = 100 / len(LANES)
CX = [i * LW + LW / 2 for i in range(len(LANES))]
for i, name in enumerate(LANES):
    x0 = i * LW
    ax.add_patch(Rectangle((x0, 0), LW, 92, fc=BG, ec="none", zorder=1))
    if i:
        ax.plot([x0, x0], [0, 92], color=LINE, lw=0.8, zorder=2)
    ax.add_patch(Rectangle((x0 + 1, 84), LW - 2, 7, fc=NAVY, ec="none", zorder=3))
    ax.text(x0 + LW / 2, 87.5, name, ha="center", va="center",
            fontsize=10, color="white", fontweight="bold", zorder=4)

# ---- 图元 ----
def node(cx, cy, w, h, text, style="step"):
    if style == "end":
        fc, ec, tc = NAVY, NAVY, "white"
    elif style == "step":
        fc, ec, tc = STEP, NAVY, TEXT
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                 boxstyle="round,pad=0.3,rounding_size=0.8",
                 fc=fc, ec=ec, lw=0.8, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=8.8,
            color=tc, linespacing=1.2, zorder=4)

def diamond(cx, cy, w, h, text):
    ax.add_patch(Polygon([(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)],
                 closed=True, fc=STEP, ec=NAVY, lw=0.9, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=8.8, color=RED, zorder=4)

def elbow(pts):
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i + 1][0]], [pts[i][1], pts[i + 1][1]],
                color=NAVY, lw=1.1, zorder=2)
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=NAVY, lw=1.1,
                                shrinkA=0, shrinkB=0), zorder=2)

def branch(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=8.5, color=RED, zorder=4)

# ---- 节点（秘书列 cx=16.7，教师列 50，学生列 83.3；节点宽 21，菱形宽 20）----
S, T, U = CX
node(S, 75, 21, 6, "接收教学任务\nExcel 整理基础表")            # 开始
node(S, 66.5, 21, 6, "凭经验试排课表")
node(S, 58, 21, 6, "人工检查冲突")
diamond(S, 47.5, 20, 10, "存在冲突？")
node(S, 36, 21, 6, "课表截图\n微信群下发")
node(T, 36, 21, 6, "查看课表，需调整时\n电话/微信提出调课")
node(S, 27.5, 21, 6, "手工改表，逐个通知")
node(U, 19, 21, 6, "接收课表截图\n与变更通知")
node(S, 10.5, 21, 6, "学期结束", style="end")

# ---- 连线（端点全部落缘）----
elbow([(S, 72), (S, 69.5)])                       # 开始→试排
elbow([(S, 63.5), (S, 61)])                       # 试排→检查
elbow([(S, 55), (S, 52.5)])                       # 检查→判断
elbow([(S - 10, 47.5), (4, 47.5), (4, 66.5), (S - 10.5, 66.5)])   # 是→回试排
branch(1.2, 56.5, "是")
elbow([(S, 42.5), (S, 39)])                       # 否→下发
branch(S + 1, 40.5, "否")
elbow([(S + 10.5, 36), (T - 10.5, 36)])           # 下发→教师查看
elbow([(T, 33), (T, 27.5), (S + 10.5, 27.5)])     # 教师提出→手工改表
elbow([(S, 24.5), (S, 19), (U - 10.5, 19)])       # 改表通知→学生接收
elbow([(U, 16), (U, 10.5), (S + 10.5, 10.5)])     # 学生→学期结束

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
OUT = r"D:\AAA-课程\软件工程实践\1-可行性研究报告工作区\图表\图3-1\现有系统处理流程泳道图_20261107.png"
fig.savefig(OUT, dpi=600)
plt.close(fig)
print("已输出:", OUT)
