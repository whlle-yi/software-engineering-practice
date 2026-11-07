# -*- coding: utf-8 -*-
"""图 3-3 现有系统每学期费用构成（环图）——可行性研究报告 3.3 节配图
数据：调课 15 人天/0.71 万、排课 8 人天/0.38 万、答疑 2 人天/0.10 万（合计约 1.2 万元/学期）
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

SKILL_ROOT = Path(r"C:/Users/32530/.zcode/skills/pretty-charts")
plt.style.use(SKILL_ROOT / "references" / "assets" / "matplotlib" / "business.mplstyle")
PAL = json.loads((SKILL_ROOT / "references" / "assets" / "palettes" / "business.json").read_text("utf-8"))

# 项目规范覆盖：西文/数字 Times New Roman；中文用 SimHei——SimSun 在本机 matplotlib
# （3.11.2 + simsun.ttc）下渲染为空白，且泳道图/DFD 等既有图均用 SimHei，保持全套图一致。
# 必须直排 font.family 列表：本机 matplotlib 对 font.sans-serif 回退链解析失效（纯 SimHei 链也出豆腐）
plt.rcParams["font.family"] = ["Times New Roman", "SimHei"]

# ── 数据（与 3.3 正文一致，按数值降序） ──
names = ["调课环节", "排课环节", "课表答疑"]
vals  = np.array([0.71, 0.38, 0.10])          # 万元/学期
mdays = [15, 8, 2]                             # 人天/学期
total = vals.sum()                             # 1.19 ≈ 1.2（约数口径）
pcts  = vals / total * 100
colors = [PAL["primary"], PAL["categorical"][1], PAL["categorical"][2]]

fig, ax = plt.subplots(figsize=(5.6, 3.8))
ax.set_aspect("equal")

wedges, _ = ax.pie(
    vals, startangle=90, counterclock=False,          # 12 点起、顺时针、按值降序
    colors=colors,
    wedgeprops={"width": 0.42, "edgecolor": PAL["background"], "linewidth": 2},
)

# 每块外侧直标：名称 + 人天 + 万元 + 占比（不用图例）
for w, name, md, v, p in zip(wedges, names, mdays, vals, pcts):
    ang = (w.theta1 + w.theta2) / 2
    x, y = np.cos(np.deg2rad(ang)) * 1.12, np.sin(np.deg2rad(ang)) * 1.12
    ha = "center" if abs(x) < 0.15 else ("left" if x > 0 else "right")
    ax.annotate(f"{name}（{md} 人天）\n{v:.2f} 万元，占 {p:.0f}%",
                (x, y), ha=ha, va="center", fontsize=9.5,
                color=PAL["text"]["label"], linespacing=1.5)

# 中心放总量
ax.text(0, 0.10, "约 1.2 万元", ha="center", va="center",
        fontsize=14, fontweight="bold", color=PAL["text"]["title"])
ax.text(0, -0.18, "每学期", ha="center", va="center",
        fontsize=8.5, color=PAL["subtext"])

ax.set_xlim(-1.75, 1.75)
ax.set_ylim(-1.35, 1.45)

OUT = Path(__file__).resolve().parent
fig.savefig(OUT / "图3-3_现有系统费用构成_v2_20261108.png", dpi=600, bbox_inches="tight")
plt.close(fig)
print("saved")
