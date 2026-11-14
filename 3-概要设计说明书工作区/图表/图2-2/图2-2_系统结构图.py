# -*- coding: utf-8 -*-
"""图 2-2 系统结构图（概要设计说明书 2.4）。
B/S 分层结构：用户层 → 表示层（浏览器端）→ 应用服务层（M1–M7）→ 公共服务层（M8）→ 数据与外部服务。
依赖只向下；风格与可行性报告/SRS 配图同源；配色 business；600dpi PNG 注入 docx。"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Ellipse

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
C_EXT = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]
NL = chr(10)

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 5.4
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(1, 99)
ax.set_ylim(14, 101)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)


def box(cx, cy, w, h, text, key=False, ext=False, fs=9.5):
    ec = C_EXT if ext else PRIMARY
    ax.add_patch(FancyBboxPatch((cx - w / 2, cy - h / 2), w, h,
                                boxstyle="round,pad=0.25,rounding_size=0.6",
                                fc="white", ec=ec, lw=1.2, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color=C_TEXT, linespacing=1.25, zorder=4)


def cylinder(cx, cy, w, h, text, fs=9.5):
    """数据存储圆柱。"""
    rh = h * 0.28
    ax.add_patch(Rectangle((cx - w / 2, cy - h / 2 + rh / 2), w, h - rh,
                           fc="white", ec="none", zorder=3))
    ax.add_patch(Ellipse((cx, cy - h / 2 + rh / 2), w, rh, fc="white", ec=C_EXT, lw=1.1, zorder=3))
    ax.plot([cx - w / 2, cx - w / 2], [cy - h / 2 + rh / 2, cy + h / 2 - rh / 2],
            color=C_EXT, lw=1.1, zorder=3)
    ax.plot([cx + w / 2, cx + w / 2], [cy - h / 2 + rh / 2, cy + h / 2 - rh / 2],
            color=C_EXT, lw=1.1, zorder=3)
    ax.add_patch(Ellipse((cx, cy + h / 2 - rh / 2), w, rh, fc="white", ec=C_EXT, lw=1.1, zorder=4))
    ax.text(cx, cy - rh * 0.2, text, ha="center", va="center", fontsize=fs, color=C_TEXT, zorder=4)


def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0, arrowprops=ARROW, zorder=2)


def seg(p0, p1):
    ax.plot([p0[0], p1[0]], [p0[1], p1[1]], color=C_FLOW, lw=1.1, zorder=2)


def label(x, y, text, ha="left", fs=9.5, color=None):
    ax.text(x, y, text, ha=ha, va="center", fontsize=fs,
            color=color or C_FLOW, zorder=4)


def layer(x0, y0, w, h, title):
    ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=C_EXT, lw=1.0,
                           linestyle=(0, (4, 3)), zorder=1))
    ax.text(x0 + 1.5, y0 + h - 2.2, title, ha="left", va="center",
            fontsize=9.5, color=C_TEXT, zorder=4)


# ---- 用户层 ----
box(20, 94, 18, 7, "教务管理员", ext=True)
box(50, 94, 16, 7, "任课教师", ext=True)
box(80, 94, 16, 7, "学生", ext=True)

# ---- 表示层 ----
layer(4, 74, 86, 12, "表示层 · 浏览器端（Vue 3 单页应用）")
box(20, 78.5, 24, 6, "管理员工作台")
box(50, 78.5, 20, 6, "教师界面")
box(80, 78.5, 20, 6, "学生界面")
arrow((20, 90.5), (20, 86))
arrow((50, 90.5), (50, 86))
arrow((80, 90.5), (80, 86))

# ---- 应用服务层 ----
layer(4, 48, 86, 20, "应用服务层（后端）")
box(15, 59.5, 18.5, 6.5, "M1 用户与" + NL + "权限管理", fs=9.5)
box(36.5, 59.5, 18.5, 6.5, "M2 基础数据" + NL + "管理", fs=9.5)
box(58, 59.5, 18.5, 6.5, "M3 排课约束" + NL + "配置", fs=9.5)
box(79.5, 59.5, 18.5, 6.5, "M4 自动排课" + NL + "引擎", key=True, fs=9.5)
box(15, 51.5, 18.5, 6.5, "M5 调课申请" + NL + "与审核", fs=9.5)
box(36.5, 51.5, 18.5, 6.5, "M6 课表查询" + NL + "与通知", fs=9.5)
box(58, 51.5, 19, 6.5, "M7 PiAgent" + NL + "智能体", fs=9.5)
arrow((50, 74), (50, 68))
label(51.5, 71, "HTTP / REST")

# ---- 公共服务层 ----
layer(4, 34, 86, 10, "公共服务层")
box(44, 37.5, 44, 5.5, "M8 数据访问与审计（公用程序）", fs=9.5)
arrow((44, 48), (44, 44))

# ---- 数据与外部服务 ----
cylinder(20, 27, 20, 9, "MySQL 8.0")
box(47, 27, 22, 7, "教务文件接口")
box(78, 27, 20, 8, "外部大模型 API", ext=True)
arrow((20, 34.5), (20, 31.5))
label(21, 33, "JDBC")
arrow((47, 34.5), (47, 30.5))
label(48, 32.5, "导入/导出")
# M7 直连外部模型 API（不经过 M8）
seg((67.5, 51.5), (95.5, 51.5))
seg((95.5, 51.5), (95.5, 27))
arrow((95.5, 27), (88, 27))
label(91.3, 24.5, "HTTPS", ha="center")

# 图例
label(3.5, 17, "实线箭头＝调用／数据访问（自上而下）　灰描边＝外部系统　虚线框＝逻辑分层　圆柱＝数据库",
      fs=8.5, color=C_EXT)

fig.subplots_adjust(left=0.01, right=0.99, top=0.995, bottom=0.005)
stem = "系统结构图_business_20261114"
fig.savefig(HERE / ("图2-2_" + stem + ".png"), dpi=600)
plt.close(fig)
print("PNG 已输出")
