# -*- coding: utf-8 -*-
"""图 1-1 高校智能排课系统与其他系统/机构的往来关系图（T2 报告级 / business）。

矢量源 SVG（文字转轮廓）→ LibreOffice 转 EMF → 插入 Word；PNG 仅供目检。
布局：全正交连线（水平/垂直），双向往来 = 两条平行线（间距 ≥4），箭头 = 数据流向。
坐标体系 100×100，节点锚点按框边缘精确计算。
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
SKILL_ROOT = Path(r"C:\Users\32530\.zcode\skills\pretty-charts")
PALETTE = json.loads((SKILL_ROOT / "references/assets/palettes/business.json").read_text(encoding="utf-8"))

C_SYS = PALETTE["primary"]        # 中心系统边框
C_SYS_FILL = "#DEEBF7"            # 中心系统浅填充（sequential[1]，同色板）
C_EXT = PALETTE["neutral"]        # 外部实体边框
C_FLOW = PALETTE["text"]["label"] # 箭头与流标签
C_TEXT = PALETTE["text"]["title"]

# 字体逐字回退（实测 font.family 直排字体名列表才生效）：
# 西文/数字 → Times New Roman；中文 → 黑体 SimHei（宋体 simsun.ttc 为集合字体，
# matplotlib 回退链不支持 ttc；数据图中文字体用黑体符合 common.md 字体表）
plt.rcParams.update({
    "font.family": ["Times New Roman", "SimHei"],
    "svg.fonttype": "path",
    "savefig.bbox": None,
})

FIG_W, FIG_H = 6.1, 4.4
fig, ax = plt.subplots(figsize=(FIG_W, FIG_H))
ax.set_xlim(0, 100); ax.set_ylim(0, 100)
ax.axis("off")

def node(cx, cy, w, h, text, central=False, fs=10.5):
    ax.add_patch(FancyBboxPatch((cx - w/2, cy - h/2), w, h,
                                boxstyle="round,pad=0.3,rounding_size=1.5",
                                fc="#DEEBF7" if central else "white",
                                ec=C_SYS if central else C_EXT,
                                lw=1.8 if central else 1.1, zorder=3))
    ax.text(cx, cy, text, ha="center", va="center", fontsize=fs,
            color=C_TEXT, linespacing=1.4, zorder=4)

def arrow(p0, p1):
    ax.annotate("", xy=p1, xytext=p0,
                arrowprops=dict(arrowstyle="-|>", color=C_FLOW, lw=1.1,
                                shrinkA=0, shrinkB=0), zorder=2)

def label(x, y, text):
    ax.text(x, y, text, ha="center", va="center", fontsize=9,
            color=C_FLOW, linespacing=1.35, zorder=4)

# ---- 节点（中心 1 + 外部 6）----
node(50, 50, 22, 16, "高校智能排课\n系统", central=True)      # 框 x39–61 y42–58
node(13, 57, 22, 8, "教务主系统")                              # x2–24 y53–61
node(13, 43, 22, 8, "教室管理部门")                            # x2–24 y39–47
node(50, 88, 20, 9, "教务管理员")                              # x40–60 y83.5–92.5
node(87, 57, 18, 9, "教务信息\n发布渠道")                      # x78–96 y52.5–61.5
node(87, 43, 18, 9, "任课教师")                                # x78–96 y38.5–47.5
node(50, 12, 20, 9, "学生")                                    # x40–60 y7.5–16.5

# ---- 数据流（全正交；每条有标签；双向往来 = 平行线）----
arrow((24, 57), (39, 57))                     # 教务主系统 → 系统
label(31, 61.5, "教学计划\n选课名单")
arrow((24, 43), (39, 43))                     # 教室管理部门 → 系统
label(31, 38.5, "教室资源数据")

arrow((47, 83.5), (47, 58))                   # 管理员 → 系统（下行）
label(35, 70.5, "基础数据、约束配置\n调课审核指令")
arrow((53, 58), (53, 83.5))                   # 系统 → 管理员（上行）
label(62, 70.5, "冲突报告\n待审申请")

arrow((61, 57), (78, 57))                     # 系统 → 发布渠道
label(69, 61.5, "课表发布")

arrow((77, 45), (61, 45))                     # 教师 → 系统（左行）
label(69, 47.5, "调课/代课申请")
arrow((61, 41), (77, 41))                     # 系统 → 教师（右行）
label(69, 38.5, "课表、审核结果")

arrow((47, 42), (47, 16.5))                   # 系统 → 学生（下行）
label(36, 29, "课表、\n变更通知")
arrow((53, 16.5), (53, 42))                   # 学生 → 系统（上行）
label(62, 29, "时间冲突反馈")

fig.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.01)
stem = "往来关系_business_20261029"
fig.savefig(HERE / f"图1-1_{stem}.svg")
fig.savefig(HERE / f"图1-1_{stem}_目检.png", dpi=600)
plt.close(fig)
print("SVG/PNG 已输出")
