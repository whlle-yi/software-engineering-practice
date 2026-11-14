# -*- coding: utf-8 -*-
"""图 9-1 M7 PiAgent 函数调用处理流程图（详细设计说明书 9.7 流程逻辑）。
TD：鉴权→LLM 调用→校验→写操作确认/查询回答；异常出口：越权/超时降级/校验失败。
配色 business；600dpi PNG。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle

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

FIG_W, FIG_H = 6.1, 8.6
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


def box(cx, cy, w, h, text, key=False, ext=False, fs=9.5):
    ec = C_EXT if ext else PRIMARY
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.25,rounding_size=0.6",
                                fc=PRIMARY if key else "white",
                                ec=ec, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color=C_TEXT, linespacing=1.3, zorder=4)


def diamond(cx, cy, w, h, text, fs=9):
    pts = [(cx, cy + h / 2), (cx + w / 2, cy), (cx, cy - h / 2), (cx - w / 2, cy)]
    ax.add_patch(Polygon(pts, closed=True, fc="white", ec=PRIMARY, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs, color=C_TEXT,
            linespacing=1.25, zorder=4)


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


def label(x, y, text, ha="left", fs=9.5, color=None):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs,
            color=color or C_FLOW, zorder=4)


# ---- 主轴（x=50）----
capsule(50, 97.5, 14, 5.5, "开始")
box(50, 90, 30, 6, "接收管理员自然语言指令")
box(50, 82.5, 26, 6, "权限校验（经 M1）")
diamond(50, 73.5, 18, 10, "管理员角色？")
box(50, 63, 30, 7, "调用外部大模型 API" + NL + "（意图识别与参数提取）", key=True)
diamond(50, 53, 21, 10.5, "30 秒内正常" + NL + "返回？")
box(50, 42.5, 26, 6, "结构化校验工具调用参数")
diamond(50, 33.5, 18, 10, "校验通过？")
diamond(50, 21.5, 21, 10.5, "是写操作？")

# ---- 写操作支线（左）----
box(16, 21.5, 24, 7, "生成待确认项返回" + NL + "管理员确认", fs=9)
box(16, 10, 24, 6.5, "经 M8 落库并返回结果", fs=9)
# ---- 查询支线（右）----
box(84, 21.5, 25, 7, "调用查询类白名单" + NL + "工具（M2/M3/M4/M6）", fs=9)
box(84, 10, 24, 6.5, "组织自然语言回答返回", fs=9)

# ---- 异常出口 ----
box(85, 73.5, 24, 6.5, "返回越权提示并留痕", fs=9)
box(85, 53, 24, 6.5, "降级停用并明确提示", fs=9)
box(85, 33.5, 24, 6.5, "提示重述或修正后重试", fs=9)

# ---- 主线箭头 ----
arrow((50, 94.75), (50, 93))
arrow((50, 87), (50, 85.5))
arrow((50, 79.5), (50, 78.5))
arrow((50, 68.5), (50, 67.25))
label(51.3, 67.9, "是")
arrow((50, 59.5), (50, 58.25))
arrow((50, 47.75), (50, 45.5))
label(51.3, 46.6, "是")
arrow((50, 39.5), (50, 38.5))
arrow((50, 28.5), (50, 26.75))
label(51.3, 27.6, "是")

# ---- 分支箭头 ----
arrow((41, 73.5), (73, 73.5), accent=True)
label(42.5, 70.4, "否", color=ACCENT)
arrow((60.5, 53), (73, 53), accent=True)
label(62, 54.2, "否", color=ACCENT)
arrow((59, 33.5), (73, 33.5), accent=True)
label(60.5, 34.7, "否", color=ACCENT)
# 写操作（左）
arrow((39.5, 21.5), (28, 21.5))
label(41, 22.7, "是")
arrow((16, 18), (16, 13.25))
# 查询（右）
arrow((60.5, 21.5), (71.5, 21.5))
label(61.8, 22.7, "否")
arrow((84, 18), (84, 13.25))

fig.subplots_adjust(left=0.01, right=0.99, top=0.995, bottom=0.005)
stem = "M7PiAgent处理流程图_business_20261114"
fig.savefig(HERE / ("图9-1_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
