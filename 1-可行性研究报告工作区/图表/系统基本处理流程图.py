# -*- coding: utf-8 -*-
"""图 2-1 系统基本处理流程图，双面板：(a) 期初排课 (b) 学期调课。

算法流程图风格（pretty-charts diagrams.md 流程图规范）：
TD 单列车道；起止 = 圆角胶囊；处理 = 矩形；判断 = 菱形（分支标"是/否"）；
回流 = 虚线绕外侧。配色 business（与图 1-1 全局一致）：primary 实心关键节点、
accent 菱形、neutral 虚线。矢量源 SVG（文字转轮廓）→ svgBlip 注入 Word；PNG 目检/兜底。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path(r"C:\Users\32530\.zcode\skills\pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
C_LOOP = PALETTE["text"]["tick"]     # 回流虚线与"否"
C_FLOW = PALETTE["text"]["label"]    # 实线箭头
C_TEXT = PALETTE["text"]["title"]

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 4.3
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(5, 100); ax.set_ylim(18, 100)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def capsule(cx, cy, w, h, text):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle=f"round,pad=0.3,rounding_size={h/2 - 0.3}",
                                fc=PRIMARY, ec=PRIMARY, lw=1.0, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color="white", zorder=4)

def box(cx, cy, w, h, text, key=False):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=0.8",
                                fc=PRIMARY if key else "white",
                                ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5,
            color="white" if key else C_TEXT, zorder=4)

def diamond(cx, cy, w, h, text):
    ax.add_patch(Polygon([(cx, cy + h/2), (cx + w/2, cy), (cx, cy - h/2), (cx - w/2, cy)],
                         closed=True, fc="#FDF1E2", ec=ACCENT, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=9.5, color=C_TEXT, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)

def loop(pts, lbl, lx, ly):
    """正交回流虚线：pts 依次连线，末段带箭头。"""
    for i in range(len(pts) - 2):
        ax.plot([pts[i][0], pts[i+1][0]], [pts[i][1], pts[i+1][1]],
                color=C_LOOP, lw=1.0, ls=(0, (4, 2)), zorder=2)
    ax.annotate("", xy=pts[-1], xytext=pts[-2],
                arrowprops=dict(arrowstyle="-|>", color=C_LOOP, lw=1.0,
                                ls=(0, (4, 2)), shrinkA=0, shrinkB=0), zorder=2)
    ax.text(lx, ly, lbl, ha="center", va="center", fontsize=9, color=C_LOOP, zorder=4)

def branch(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, zorder=4)

# ================= 面板 (a) 期初排课（车道 x=25） =================
X = 25
capsule(X, 94, 13, 5, "开始")
box(X, 85, 30, 6, "导入教学计划与基础数据")
box(X, 76, 24, 6, "配置排课约束")
box(X, 67, 20, 6, "自动排课", key=True)
diamond(X, 54.5, 24, 11, "冲突检测")
box(X, 41, 20, 6, "发布课表")
capsule(X, 31, 13, 5, "结束")

arrow((X, 91.5), (X, 88))
arrow((X, 82), (X, 79))
arrow((X, 73), (X, 70))
arrow((X, 64), (X, 60))
arrow((X, 49), (X, 44)); branch(X + 2.5, 46.5, "是")
arrow((X, 38), (X, 33.5))
loop([(37, 54.5), (47, 54.5), (47, 67), (35.5, 67)], "否，调整后重排", 47, 72.5)
ax.text(X, 22.5, "(a) 期初排课", ha="center", va="center", fontsize=10, color=C_TEXT)

# ================= 面板 (b) 学期调课（车道 x=75） =================
X = 75
capsule(X, 94, 13, 5, "开始")
box(X, 85, 28, 6, "教师提交调课申请")
diamond(X, 71, 24, 11, "管理员审核")
box(X, 57, 30, 6, "局部重排与冲突检测", key=True)
box(X, 46, 20, 6, "通知师生")
capsule(X, 35, 13, 5, "结束")

arrow((X, 91.5), (X, 88))
arrow((X, 82), (X, 76.5))
arrow((X, 65.5), (X, 60))
arrow((X, 54), (X, 49)); branch(X + 2.5, 51.5, "是")
arrow((X, 43), (X, 37.5))
loop([(87, 71), (95, 71), (95, 85), (89.5, 85)], "否，退回修改", 95, 78.5)
ax.text(X, 22.5, "(b) 学期调课", ha="center", va="center", fontsize=10, color=C_TEXT)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "处理流程_business_20261029"
fig.savefig(HERE / f"图2-1_{stem}.svg")
fig.savefig(HERE / f"图2-1_{stem}_目检.png", dpi=200)
plt.close(fig)
print("SVG/PNG 已输出")
