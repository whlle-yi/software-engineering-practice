# -*- coding: utf-8 -*-
"""图 2-1 系统基本数据流程图（顶层 DFD-0 简略版，T2 报告级 / business）。

最基本的数据流程：一条横向主链（教务主系统 → D1 基础数据与约束 → 1 自动排课引擎
→ D2 课表库 → 发布渠道）+ 下排调课链（教师 → 2 手工改表与通知 → 学生）与
管理/查询支线。风格与图 4-1 同源；矢量 SVG → svgBlip 注入 Word；PNG 目检/兜底。
布局教训已内建：xlim 收紧到内容包围盒、标签净空 ≥2 单位、换行用 NL=chr(10)。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path("C:/Users/32530/.zcode/skills/pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

PRIMARY = PALETTE["primary"]
C_LOOP = PALETTE["text"]["tick"]
C_FLOW = PALETTE["text"]["label"]
C_TEXT = PALETTE["text"]["title"]
NL = chr(10)

plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 3.9
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 100); ax.set_ylim(20, 90)
ax.axis("off")

ARROW = dict(arrowstyle="-|>", color=C_FLOW, lw=1.1, shrinkA=0, shrinkB=0)

def capsule(cx, cy, w, h, text):
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

def label(x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=9, color=C_FLOW, linespacing=1.35, zorder=4)

def dlabel(x, y, text):
    ax.text(x, y, text, ha="left", va="center", fontsize=9, color=C_FLOW, zorder=4)

# ---- 主链（y=80）----
ext(7, 80, 13, 8, "教务主系统")                 # x0.5–13.5 y76–84
store(31, 80, 20, "D1  基础数据与约束")          # 线 x21–41
box(56, 80, 18, 10, "1" + NL + "自动排课引擎", key=True)   # x47–65 y75–85
store(77, 80, 20, "D2  课表库")                 # 线 x67–87
ext(94, 80, 11, 8, "发布渠道")                  # x88.5–99.5

arrow((13.5, 80), (21, 80)); label(17, 84.5, "教学任务")
arrow((42, 80), (47, 80))
arrow((65, 80), (67, 80))
arrow((87, 80), (88.5, 80)); label(87.8, 74.5, "课表发布")

# ---- 管理支线 ----
ext(48, 52, 14, 8, "教务管理员")                # x41–55 y48–56
arrow((51, 73), (51, 56.5)); dlabel(45, 64.5, "冲突报告")
arrow((55, 56.5), (55, 73)); dlabel(57, 64.5, "运行指令")

# ---- 教室数据支线 ----
ext(28, 52, 14, 8, "教室管理部门")               # x21–35 y48–56
arrow((28, 56), (28, 75)); dlabel(34, 66, "教室资源数据")

# ---- 调课链（y=28）----
box(52, 28, 20, 10, "2" + NL + "手工改表与通知", key=True)   # x42–62 y23–33
ext(80, 28, 12, 8, "教师")                      # 占位（下行同位复用见下）
ext(20, 28, 12, 8, "学生")                      # x14–26 y24–32

arrow((80, 77), (80, 33)); dlabel(85.5, 55, "课表查询")
arrow((74, 28), (62, 28)); dlabel(68, 30.5, "调课/代课申请")
arrow((42, 28), (26, 28)); dlabel(34, 30.5, "变更通知")
arrow((58, 23), (58, 60)); arrow((58, 60), (72, 60)); arrow((72, 60), (72, 75))
dlabel(64, 58.5, "更新课表")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "基本数据流_business_20261029"
fig.savefig(HERE / ("图2-1_" + stem + ".svg"))
fig.savefig(HERE / ("图2-1_" + stem + "_目检.png"), dpi=200)
plt.close(fig)
print("SVG/PNG 已输出")
