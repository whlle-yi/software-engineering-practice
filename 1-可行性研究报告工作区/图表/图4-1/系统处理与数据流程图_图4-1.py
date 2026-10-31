# -*- coding: utf-8 -*-
"""图 4-1 系统处理流程图与数据流程图，双面板：(a) 处理流程 (b) 数据流程。

(a) 算法流程图（TD，期初排课 → 学期调课全周期）：胶囊起止、矩形处理、
    菱形判断（是/否）、虚线回流绕左外侧。
(b) 顶层数据流程图 DFD-0：直角矩形=外部实体、圆角矩形=加工（1/2）、
    双横线开口框=数据存储（D1/D2）。
配色 business（与图 1-1 全局一致）。矢量 SVG → svgBlip 注入 Word；PNG 目检/兜底。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path(r"C:\Users\32530\.zcode\skills\pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
C_LOOP = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 5.6
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(4, 98); ax.set_ylim(-4, 100)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def capsule(cx, cy, w, h, text):
    # 胶囊 = 矩形 + 两端圆形端盖（基本图元，绕开 Word SVG 渲染器对大圆弧路径的缺陷）
    from matplotlib.patches import Circle, Rectangle
    cr = h / 2
    ax.add_patch(Rectangle((cx - w/2 + cr, cy - cr), w - 2*cr, h, fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.add_patch(Circle((cx - w/2 + cr, cy), cr, fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.add_patch(Circle((cx + w/2 - cr, cy), cr, fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color="white", zorder=4)

def box(cx, cy, w, h, text, key=False, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=0.8",
                                fc=PRIMARY if key else "white",
                                ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color="white" if key else C_TEXT, linespacing=1.3, zorder=4)

def diamond(cx, cy, w, h, text):
    ax.add_patch(Polygon([(cx, cy + h/2), (cx + w/2, cy), (cx, cy - h/2), (cx - w/2, cy)],
                         closed=True, fc="#FDF1E2", ec=ACCENT, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color=C_TEXT, zorder=4)

def ext(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(Rectangle((cx - w/2, cy - h/2), w, h, fc="white", ec=C_LOOP, lw=1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def store(cx, cy, w, text, fs=9.5):
    h = 6
    ax.plot([cx - w/2, cx + w/2], [cy + h/2, cy + h/2], color=C_LOOP, lw=1.3, zorder=3)
    ax.plot([cx - w/2, cx + w/2], [cy - h/2, cy - h/2], color=C_LOOP, lw=1.3, zorder=3)
    ax.plot([cx - w/2 + 0.8, cx - w/2 + 0.8], [cy - h/2, cy + h/2], color=C_LOOP, lw=1.1, zorder=3)
    ax.text(cx - w/2 + 2, cy, text, ha="left", va="center", fontsize=fs, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)

def loop(pts, lbl, lx, ly):
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i+1][0]], [pts[i][1], pts[i+1][1]],
                color=C_LOOP, lw=1.0, ls=(0, (4, 2)), zorder=2)
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=C_LOOP, lw=1.0,
                                ls=(0, (4, 2)), shrinkA=0, shrinkB=0), zorder=2)
    ax.text(lx, ly, lbl, ha="center", va="center", fontsize=9, color=C_LOOP, zorder=4)

def branch(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, zorder=4)

def label(x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=9, color=C_FLOW, linespacing=1.35, zorder=4)

# ================ 面板 (a) 处理流程（车道 x=22） ================
X = 27
capsule(X, 93, 12, 5, "开始")
box(X, 84, 28, 6, "导入基础数据与排课约束")
box(X, 75, 20, 6, "自动排课", key=True)
diamond(X, 64, 26, 9, "存在硬冲突？")
box(X, 51, 20, 6, "发布课表")
box(X, 40, 28, 6, "教师提交调课申请")
diamond(X, 29, 26, 9, "审核通过？")
box(X, 18, 26, 6, "局部重排并通知", key=True)
capsule(X, 8, 12, 5, "结束")

arrow((X, 90.5), (X, 87))
arrow((X, 81), (X, 78))
arrow((X, 72), (X, 68.5))
arrow((X, 59.5), (X, 54)); branch(X + 2.5, 56.5, "否")
arrow((X, 48), (X, 43))
arrow((X, 37), (X, 33.5))
arrow((X, 26), (X, 21)); branch(X + 2.5, 23.5, "是")
arrow((X, 15), (X, 10.5))
loop([(14, 64), (8, 64), (8, 75), (17, 75)], "是", 10.8, 66.3)
loop([(14, 29), (5, 29), (5, 40), (13, 40)], "否", 9.2, 31.3)
ax.text(X, 1.2, "(a) 处理流程", ha="center", va="center", fontsize=10, color=C_TEXT)

# ================ 面板 (b) 数据流程（DFD-0，x 46–98） ================
ext(58, 90, 15, 8, "教务主系统")                    # x50.5–65.5 y86–94
store(76, 76, 40, "D1  基础数据与约束")              # 线 x56–96 y73/79
ext(58, 60, 15, 8, "教室管理部门")                   # y56–64
box(76, 50, 18, 10, "1\n自动排课引擎", key=True)     # x67–85 y45–55
store(76, 28, 40, "D2  课表库")                     # 线 x56–96 y25/31
ext(49, 50, 13, 8, "教务管理员")                    # x42.5–55.5 y46–54
ext(91, 10, 11, 8, "教师")                          # x85.5–96.5 y10–18
box(72, 12, 20, 10, "2\n调课审核与重排", key=True)   # x62–82 y7–17
ext(46, 12, 11, 8, "学生")                          # x42.5–53.5 y8–16

arrow((58, 86), (58, 79)); label(49.5, 82.5, "教学计划\n选课名单")
arrow((58, 64), (58, 73)); label(49.5, 68.5, "教室\n资源数据")
arrow((76, 73), (76, 55)); label(82.5, 64, "基础数据")
arrow((76, 45), (76, 31)); label(83, 38, "无冲突课表")
arrow((67, 52), (55.5, 52)); label(61, 54.3, "冲突报告")
arrow((55.5, 48), (67, 48)); label(61, 43.5, "运行指令")
arrow((90, 25), (90, 14)); label(80.5, 21.5, "课表查询")
arrow((72, 25), (72, 17)); label(66.5, 21, "更新课表")
arrow((82, 13), (85.5, 13)); label(85, 15.5, "变更通知")
arrow((85.5, 9), (82, 9)); label(88.5, 3.8, "调课申请")
arrow((62, 12), (51.5, 12)); label(56.75, 9.6, "变更通知")
ax.text(70, 1.2, "(b) 数据流程", ha="center", va="center", fontsize=10, color=C_TEXT)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "处理与数据流_business_20261029"  # 输出 图4-1_<stem>.*
fig.savefig(HERE / f"图4-1_{stem}.svg")
fig.savefig(HERE / f"图4-1_{stem}_目检.png", dpi=600)
plt.close(fig)
print("SVG/PNG 已输出")
