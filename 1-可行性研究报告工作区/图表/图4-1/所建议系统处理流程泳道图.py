# -*- coding: utf-8 -*-
"""图 4-1 所建议系统处理流程图（泳道图）——可行性研究报告 4.2 节。
四泳道（教务管理员/排课系统/任课教师/学生），覆盖期初排课与学期调课两个阶段
（阶段间以虚线分界，左侧标注）。规范：特定图指定方法/处理流程图制作方法.md。"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

NAVY, STEP, RED = "#001F5F", "#DEEBF7", "#D34F4F"
BG, LINE, TEXT, EXC = "#F5F8FC", "#CED4E0", "#121212", "#FAE7E7"
plt.rcParams.update({"font.family": ["Times New Roman", "SimHei"]})

H = 146
fig, ax = plt.subplots(figsize=(6.4, 9.34))
ax.set_xlim(0, 100); ax.set_ylim(0, H); ax.axis("off")

# ---- 泳道 ----
LANES = ["教务管理员", "排课系统", "任课教师", "学生"]
LW = 100 / len(LANES)
CX = [i * LW + LW / 2 for i in range(len(LANES))]
for i, name in enumerate(LANES):
    x0 = i * LW
    ax.add_patch(Rectangle((x0, 0), LW, H - 8, fc=BG, ec="none", zorder=1))
    if i:
        ax.plot([x0, x0], [0, H - 8], color=LINE, lw=0.8, zorder=2)
    ax.add_patch(Rectangle((x0 + 1, H - 8), LW - 2, 7, fc=NAVY, ec="none", zorder=3))
    ax.text(x0 + LW / 2, H - 4.5, name, ha="center", va="center",
            fontsize=10, color="white", fontweight="bold", zorder=4)

# ---- 图元 ----
def node(cx, cy, w, h, text, style="step"):
    if style == "end":
        fc, ec, tc = NAVY, NAVY, "white"
    elif style == "exc":
        fc, ec, tc = EXC, RED, RED
    else:
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

A, S, T, U = CX          # 四泳道中心 x：12.5 / 37.5 / 62.5 / 87.5
W, DH = 17, 6            # 节点宽、节点高

# ---- 阶段分界（虚线 + 左侧标注）----
ax.plot([0, 100], [52, 52], color=LINE, lw=1.0, ls=(0, (4, 3)), zorder=2)
ax.text(2.5, 55.2, "期初排课", ha="left", va="center", fontsize=8.5,
        color="#666666", zorder=4,
        bbox=dict(fc="white", ec="none", pad=0.5))
ax.text(2.5, 48.8, "学期调课", ha="left", va="center", fontsize=8.5,
        color="#666666", zorder=4,
        bbox=dict(fc="white", ec="none", pad=0.5))

# ---- 阶段一：期初排课 ----
node(A, 128, W, DH, "导入教学计划\n维护基础数据")
node(A, 118, W, DH, "配置排课约束")
node(A, 108, W, DH, "运行排课引擎")
node(S, 108, W, DH, "生成候选课表")
node(S, 98, W, DH, "全量冲突检测")
diamond(S, 85.5, 15, 10, "存在冲突？")
node(A, 85.5, W, DH, "调整约束\n重新排课", style="exc")
node(A, 72, W, DH, "确认并发布课表")
node(S, 62, W, DH, "发布课表\n开放四视图查询")
node(T, 62, W, DH, "教师自助\n查询课表")
node(U, 62, W, DH, "学生自助\n查询课表")

# ---- 阶段二：学期调课 ----
node(T, 40, W, DH, "提交调课申请")
node(A, 40, W, DH, "审核调课申请")
diamond(A, 28, 14, 10, "通过？")
node(T, 28, W, DH, "退回申请\n注明原因", style="exc")
node(S, 15, W, DH, "局部重排与\n冲突检测")
node(S, 5, W, DH, "更新课表\n推送变更通知")
node(U, 5, W, DH, "接收变更通知")
node(A, 5, W, DH, "调课办结\n全程留痕", style="end")

# ---- 连线（端点落缘，仅末段带箭头）----
elbow([(A, 125), (A, 121)])                                        # 导入→配置
elbow([(A, 115), (A, 111)])                                        # 配置→运行
elbow([(A + W / 2, 108), (S - W / 2, 108)])                        # 运行→生成
elbow([(S, 105), (S, 101)])                                        # 生成→检测
elbow([(S, 95), (S, 90.5)])                                        # 检测→判断
elbow([(S - 7.5, 85.5), (A + W / 2, 85.5)])                        # 是→调整约束
branch(S - 10.5, 87.6, "是")
elbow([(A, 88.5), (A, 105)])                                       # 调整→重跑引擎（回环上行）
elbow([(S, 80.5), (S, 72), (A + W / 2, 72)])                       # 否→确认发布
branch(S + 1, 76.5, "否")
elbow([(A, 69), (A, 62), (S - W / 2, 62)])                         # 确认→发布
elbow([(S + W / 2, 62), (T - W / 2, 62)])                          # 发布→教师查询
elbow([(T + W / 2, 62), (U - W / 2, 62)])                          # 教师查询→学生查询

elbow([(T - W / 2, 40), (A + W / 2, 40)])                          # 提交申请→审核
elbow([(A, 35), (A, 33)])                                          # 审核→判断
elbow([(A + 7, 28), (T - W / 2, 28)])                              # 否→退回
branch(A + 8, 30.1, "否")
elbow([(A, 23), (A, 15), (S - W / 2, 15)])                         # 是→局部重排
branch(A + 1, 19.5, "是")
elbow([(S, 12), (S, 8)])                                           # 重排→更新推送
elbow([(S + W / 2, 5), (U - W / 2, 5)])                            # 推送→学生接收
elbow([(S - W / 2, 5), (A + W / 2, 5)])                            # 更新→办结留痕

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
OUT = r"D:\AAA-课程\软件工程实践\1-可行性研究报告工作区\图表\图4-1\所建议系统处理流程泳道图_20261108.png"
fig.savefig(OUT, dpi=600)
plt.close(fig)
print("已输出:", OUT)
