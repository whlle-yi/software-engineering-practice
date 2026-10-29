# -*- coding: utf-8 -*-
"""图 3-1 现有系统（人工排课方式）处理流程与数据流程图，双面板：
(a) 处理流程（算法流程图，期初排课 → 学期调课全周期，教学秘书为人工主体）
(b) 数据流程（人工系统 DFD-0：外部实体 + 人工加工 + 秘书个人 Excel 存储）
流程图风格与图 2-1 同源（diagrams.md 流程图规范）；配色 business（与图 1-1/2-1 全局一致）。
矢量 SVG（文字转轮廓）→ svgBlip 注入 Word；PNG 目检/兜底。
注意：脚本内两行文本的换行一律写 BS+'n'（chr 构造），避免工具层转义问题。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Rectangle, Circle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path(r"C:\Users\32530\.zcode\skills\pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
ACCENT = PALETTE["accent"]
C_LOOP = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]
BS = chr(92)  # 反斜杠：用于源内构造 "\n" 转义

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 5.6
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1.5, 100); ax.set_ylim(-4, 100)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def capsule(cx, cy, w, h, text):
    # 基本图元拼装（矩形+两端圆），绕开 Word SVG 渲染器对大圆弧路径的缺陷
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

def dlabel(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, linespacing=1.35, zorder=4)

# ================ 面板 (a) 处理流程（车道 x=27，人工主体 = 教学秘书） ================
X = 27
capsule(X, 93, 12, 5, "开始")
box(X, 84, 18, 6, "接收教学任务")
box(X, 74.5, 20, 6, "Excel 整理基础表", key=True)
box(X, 65, 18, 6, "经验试排课表", key=True)
box(X, 55.5, 18, 6, "人工检查冲突")
diamond(X, 44, 22, 9, "发现冲突？")
box(X, 32.5, 24, 6, "群消息下发课表截图")
box(X, 23, 16, 6, "教师提出调课")
box(X, 13.5, 20, 6, "手工改表并通知", key=True)
capsule(X, 7, 12, 5, "学期结束")

arrow((X, 90.5), (X, 87))
arrow((X, 81), (X, 77.5))
arrow((X, 71.5), (X, 68))
arrow((X, 62), (X, 58.5))
arrow((X, 52.5), (X, 48.5))
arrow((X, 39.5), (X, 35.5)); branch(X + 2.5, 37.5, "否")
arrow((X, 29.5), (X, 26))
arrow((X, 20), (X, 16.5))
arrow((X, 10.5), (X, 9.5))

loop([(16, 44), (8, 44), (8, 65), (17, 65)], "否", 6.2, 54.5)
branch(5.8, 54.5, "是")

dlabel(43, 88.5, "教学任务")
dlabel(43, 79.2, "课程、教师、教室信息")
dlabel(43, 69.8, "四张基础表（Excel）")
dlabel(43, 60.3, "候选课表")
dlabel(43, 50.8, "疑似冲突清单")
dlabel(43, 37.8, "定稿课表")
dlabel(43, 27.8, "课表截图、群消息")
dlabel(43, 18.3, "调课需求（口头/群消息）")
dlabel(43, 8.8, "逐个通知")

ax.text(X, 1.2, "(a) 处理流程", ha="center", va="center", fontsize=10, color=C_TEXT)

# ================ 面板 (b) 数据流程（人工系统 DFD-0，独立纵列 x=76） ================
ext(76, 92, 14, 8, "教务处")                        # x69–83 y88–96
store(76, 78, 32, "D1  教学秘书个人 Excel")          # 线 x60–92 y75/81
box(76, 62, 22, 10, "1" + chr(10) + "人工整理与试排", key=True)   # x65–87 y57–67
ext(76, 40, 12, 8, "教师")                          # x70–82 y36–44
box(76, 22, 22, 10, "2" + chr(10) + "手工改表与通知", key=True)   # x65–87 y17–27
ext(76, 6, 11, 8, "学生")                           # x70.5–81.5 y2–10

arrow((76, 88), (76, 81)); dlabel(82, 84.5, "教学任务")
arrow((76, 75), (76, 67)); dlabel(82, 71, "四张基础表")
arrow((76, 57), (76, 44)); dlabel(82, 50.5, "课表截图、" + chr(10) + "群消息")
arrow((76, 36), (76, 27)); dlabel(82, 31.5, "调课需求" + chr(10) + "（口头/群消息）")
arrow((76, 17), (76, 10)); dlabel(82, 13.5, "变更通知")
ax.text(76, 2.5, "(b) 数据流程", ha="center", va="center", fontsize=10, color=C_TEXT)

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "现有系统人工排课_business_20261029"
fig.savefig(HERE / f"图3-1_{stem}.svg")
fig.savefig(HERE / f"图3-1_{stem}_目检.png", dpi=200)
plt.close(fig)
print("SVG/PNG 已输出")
