# -*- coding: utf-8 -*-
"""图 2-1 期初排课与调课处理流程图（概要设计说明书 2.3）。
TD 主轴两阶段：期初排课（导入→约束→求解→检测→发布）+ 学期调课闭环（申请→审核→局部重排）。
风格与可行性报告/SRS 配图同源；配色 business；600dpi PNG 注入 docx。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Polygon

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
C_EXT = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]
NL = chr(10)

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 9.0
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1, 99)
ax.set_ylim(0, 101)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)
ARROW_A = dict(arrowstyle="-|>", color=ACCENT, lw=1.1, shrinkA=0, shrinkB=0)


def capsule(cx, cy, w, h, text, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0,rounding_size=%.2f" % (h / 2),
                                fc="white", ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)


def box(cx, cy, w, h, text, key=False, fs=9.5):
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.25,rounding_size=0.6",
                                fc=PRIMARY if key else "white",
                                ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color="white" if key else C_TEXT, linespacing=1.25, zorder=4)


def para(cx, cy, w, h, text, fs=9.5):
    """平行四边形：输入/输出。"""
    sk = h * 0.55
    pts = [(cx - w / 2 + sk, cy - h / 2), (cx + w / 2, cy - h / 2),
           (cx + w / 2 - sk, cy + h / 2), (cx - w / 2, cy + h / 2)]
    ax.add_patch(Polygon(pts, closed=True, fc="white", ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx + sk * 0.25, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)


def diamond(cx, cy, w, h, text, fs=9.5):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, fc="white", ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)


def arrow(p0, p1, accent=False, dashed=False):
    st = dict(ARROW_A if accent else ARROW)
    if dashed:
        st["linestyle"] = (0, (4, 3))
    ax.annotate("", xy=p1, xytext=p0, arrowprops=st, zorder=2)


def seg(p0, p1, accent=False, dashed=False):
    st = dict(color=ACCENT if accent else C_FLOW, lw=1.1, zorder=2)
    if dashed:
        st["linestyle"] = (0, (4, 3))
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], **st)


def label(x, y, text, ha="left", fs=9, color=None):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs,
            color=color or C_FLOW, zorder=4)


def phase(x0, y0, w, h, title):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=C_EXT, lw=1.0,
                           linestyle=(0, (4, 3)), zorder=1))
    ax.text(x0 + 1.5, y0 + h - 2.5, title, ha="left", va="center",
            fontsize=10, color=C_TEXT, zorder=4)


# ============ 阶段一：期初排课（虚线框 y 34-100）============
phase(3, 34, 94, 66, "阶段一 · 期初排课")

capsule(47, 96.5, 14, 5.5, "开始")
para(47, 89, 34, 6.8, "导入教学计划" + NL + "与基础数据")
box(47, 81, 28, 6.5, "配置排课约束")
box(47, 72.5, 28, 6.5, "运行排课引擎求解", key=True)
box(47, 64.5, 28, 6, "冲突检测（全量扫描）")
diamond(47, 55, 19, 11, "存在硬冲突？")
box(47, 45.5, 24, 6, "预览确认课表")
para(47, 38.5, 28, 5.5, "发布课表并通知师生")

# 左侧旁支：PiAgent 偏好
para(13.5, 89, 21, 6, "教师偏好描述", fs=9.5)
box(13.5, 81, 21, 7, "PiAgent 提取" + NL + "（管理员确认）", fs=9.5)

# 右侧异常通道：调整约束
box(79, 55, 20, 6.5, "调整约束或" + NL + "基础数据", fs=9.5)

# 主线箭头
arrow((47, 93.75), (47, 92.4))
arrow((47, 85.6), (47, 84.25))
arrow((47, 77.75), (47, 76.25))
arrow((47, 69.25), (47, 67.75))
arrow((47, 61.5), (47, 60.5))
label(48.4, 49.9, "否")
arrow((47, 49.5), (47, 48.5))
arrow((47, 42.5), (47, 41.25))

# 旁支与异常通道
arrow((13.5, 86), (13.5, 84.5))
arrow((24, 81), (33, 81))
label(24.8, 82.4, "确认后并入", fs=9.5)
arrow((56.5, 55), (69, 55))
label(58, 56.2, "是")
# 回流：调整 → 重新求解（绕外侧虚线）
seg((79, 58.25), (79, 72.5), accent=True, dashed=True)
arrow((79, 72.5), (61, 72.5), accent=True, dashed=True)
label(80.2, 65, "调整后重试", color=ACCENT, fs=9.5)

# ============ 阶段二：学期调课闭环（虚线框 y 0.5-31.5）============
phase(3, 0.5, 94, 31, "阶段二 · 学期调课闭环")

para(16, 24, 24, 6, "教师提交调课申请", fs=9.5)
box(41, 24, 20, 6, "管理员审核", fs=9.5)
diamond(66, 24, 15, 10, "通过？", fs=9.5)
box(84, 24, 18, 6.5, "局部重排" + NL + "并复检冲突", fs=9.5)
para(84, 13, 24, 6, "更新课表并推送通知", fs=9.5)
box(41, 12, 24, 6, "退回申请（附意见）", fs=9.5)

arrow((28, 24), (31, 24), accent=True)
arrow((51, 24), (58.5, 24), accent=True)
arrow((73.5, 24), (75, 24), accent=True)
label(74.3, 25.6, "是", color=ACCENT)
arrow((84, 20.75), (84, 16), accent=True)
# 否：退回
arrow((66, 19), (66, 12), accent=True)
label(67.2, 17.5, "否", color=ACCENT)
seg((66, 12), (53, 12), accent=True)
# 退回流：回到申请（绕外侧虚线）
seg((29, 12), (14, 12), accent=True, dashed=True)
arrow((14, 12), (14, 21), accent=True, dashed=True)
label(15, 16.5, "修改后重新提交", color=ACCENT, fs=9.5)

fig.subplots_adjust(left=0.01, right=0.99, top=0.995, bottom=0.005)
stem = "期初排课与调课处理流程图_business_20261114"
fig.savefig(HERE / ("图2-1_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
