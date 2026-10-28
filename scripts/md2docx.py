# -*- coding: utf-8 -*-
"""
md2docx.py (v2) —— 课程文档 md → docx 生成器（v2，入库于 scripts/）

继承 v1（.workbuddy/tools/md2docx.py）的全部机制：不新建文档，在老师模板副本上
加工，段落用模板原段 deepcopy 作原型，保证格式零漂移；目录 TOC 域由 Word COM 更新。

v2 新增：
  1. 行内格式：**粗体**、*斜体*（正文、列表、表格单元格均支持）
  2. 图片：![图 3-1 处理流程图](图表/xxx.png)，独立成行；图题在图下方居中（GB 惯例），
     路径相对 md 所在目录解析；图宽自动压缩到版心宽度内
  3. 表格单元格不再强制 ascii=宋体（v1 会把数字也排成宋体），改为只设 eastAsia=宋体，
     西文/数字继承模板 docDefaults 的 Times New Roman

md 书写契约（必须遵守，否则生成结果不符）：
  - `##/###/####` → 标题1/2/3；`#` 是文档标题，被忽略
  - `## 封面` 节必须有，封面表只认：项目组长/学号、项目组员/学号×3、班级、项目名称、
    指导教师、开课学期（"YYYY 至 YYYY 学年第 N 学期"）、完成时间（"YYYY 年 M 月 D 日"）
    ——**拿不到的字段留空**，脚本保持模板空白原样；填占位字符会原样印进 docx
  - `- ` 列表转"（1）（2）"手打编号；`<!-- -->` 整段丢弃；`>` 引用行与 `---` 分隔线忽略
  - 表题在表格上一行单独写"表 x-y 标题"；图题写在图片语法的 [] 内（生成在图下方）
  - 不要用 ** 之外的其他行内 markdown（如 `代码`、~~删除线~~，不支持且会原样泄漏）

用法：
  python md2docx.py <input.md> <output.docx> [--template 模板.docx]
"""
import copy
import os
import re
import sys
import time

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Pt


# ---------------------------------------------------------------- 工具函数 ----


def width_units(s: str) -> int:
    """显示宽度：全角/中日韩字符算 2，半角算 1。用于保持封面空格占位宽度。"""
    import unicodedata
    n = 0
    for ch in s:
        n += 2 if unicodedata.east_asian_width(ch) in ("W", "F", "A") else 1
    return n


def pad_to(value: str, original_gap: str) -> str:
    """把 value 居中填进原文的空白区（用户要求：填入内容在下划线内居中）。

    保持总显示宽度不变：左右各补一半空格（余数归右侧）；
    value 比间隙宽时原样返回——value 自带下划线格式，下划线随之加长。
    """
    if not value:
        return original_gap
    target = width_units(original_gap)
    gap_now = width_units(value)
    if gap_now >= target:
        return value
    spare = target - gap_now
    lead = spare // 2
    return " " * lead + value + " " * (spare - lead)


def _orig_ul_segments(p):
    """把段落原始 run 合并为 [(是否下划线, 文本)] 连续段。"""
    segs = []
    for r in p.findall(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        u = rPr.find(qn("w:u")) if rPr is not None else None
        ul = u is not None and u.get(qn("w:val")) not in (None, "none")
        t = "".join(tt.text or "" for tt in r.findall(qn("w:t")))
        if not t:
            continue
        if segs and segs[-1][0] == ul:
            segs[-1][1] += t
        else:
            segs.append([ul, t])
    return segs


def _fill_gap(orig, gs, ge, val):
    """填一个间隙 [gs,ge)：值只填进**原本就带下划线**的子段（居中），
    非下划线子段（标签间距、下划线前的缓冲空格）原样保留。
    这保证下划线起始/结束位置与模板逐字符一致；无值时间隙原样保留。"""
    subs = []  # [(ul, piece)]
    pos = 0
    for ul, t in orig:
        a, b = pos, pos + len(t)
        pos = b
        if b <= gs or a >= ge:
            continue
        piece = t[max(gs - a, 0): max(ge - a, 0)]
        if subs and subs[-1][0] == ul:
            subs[-1][1] += piece
        else:
            subs.append([ul, piece])

    ul_text = "".join(t for ul, t in subs if ul)
    # 注意：填空区本身就是一串空格，不能以 strip() 判断，只需存在下划线子段
    filled = pad_to(val, ul_text) if (val.strip() and ul_text) else None

    out = []
    done_ul = False
    for ul, t in subs:
        if not ul:
            out.append((False, t))
        elif filled is not None:
            if not done_ul:
                out.append((True, filled))
                done_ul = True
            # 有值时其余 ul 子段已并入 filled，跳过
        else:
            out.append((True, t))
    return out


def segments_of(p_el, labels, values):
    """按模板原始下划线结构定位填空区并填值，返回 [(是否划线, 文本)]。

    values 按间隙位置索引：n 个标签对应 n+1 个间隙（行首、标签之间…、行尾）。
    与 v1 的差异：v1 把每个间隙整段压成一个下划线 run，会抹掉模板里
    "下划线前的非下划线缓冲空格"、并给"班    级"这类标签间距误加下划线；
    v2 按原始 run 的下划线结构分子段填值，起始位置与模板逐字符一致。
    （签名与 v1 不同：第一个参数是段落 lxml 元素，不是文本）
    """
    orig = _orig_ul_segments(p_el)
    text = "".join(t for _, t in orig)

    spans = []
    cursor = 0
    for lab in labels:
        i = text.find(lab, cursor)
        if i < 0:
            raise ValueError(f"标签 {lab!r} 未在行 {text!r} 中找到")
        spans.append((i, i + len(lab)))
        cursor = i + len(lab)

    segs = []
    pos = 0
    for k, (s, e) in enumerate(spans):
        segs.extend(_fill_gap(orig, pos, s, values[k] if k < len(values) else ""))
        segs.append((False, text[s:e]))
        pos = e
    segs.extend(_fill_gap(orig, pos, len(text),
                          values[len(spans)] if len(values) > len(spans) else ""))
    return segs


def _rewrite_runs(p, segments):
    """按 [(是否划线, 文本)] 逐段重建 run，保留 pPr 与下划线约定。

    模板封面用「标签不划线 + 填空区划线」构成下划线填空式，
    因此填值时必须区分两类 run，不能压成一段。
    """
    pPr = p.find(qn("w:pPr"))
    label_rPr = _rpr_of(p, False)
    blank_rPr = _rpr_of(p, True)
    if blank_rPr is None:
        blank_rPr = label_rPr
    for child in list(p):
        if child is not pPr:
            p.remove(child)
    for underlined, text in segments:
        if not text:
            continue
        rPr = blank_rPr if underlined else label_rPr
        r = p.makeelement(qn("w:r"), {})
        if rPr is not None:
            r.append(copy.deepcopy(rPr))
        t = r.makeelement(qn("w:t"), {})
        t.set(qn("xml:space"), "preserve")
        t.text = text
        r.append(t)
        p.append(r)


def _rpr_of(p, want_underline):
    """取段落中第一个"有/无下划线"的 run 的 rPr，作为还原格式的模板。"""
    fallback = None
    for r in p.findall(qn("w:r")):
        rPr = r.find(qn("w:rPr"))
        u = rPr.find(qn("w:u")) if rPr is not None else None
        has_u = u is not None and u.get(qn("w:val")) not in (None, "none")
        if fallback is None and rPr is not None:
            fallback = rPr
        if has_u == want_underline and rPr is not None:
            return copy.deepcopy(rPr)
    return copy.deepcopy(fallback) if fallback is not None else None


# ------------------------------------------------------------- 行内格式 ----

INLINE_RE = re.compile(r"(\*\*[^*]+\*\*|\*[^*\*]+\*)")


def parse_inline(text):
    """'**粗**与*斜*及普通' → [(文本, bold, italic), ...]"""
    segs = []
    for part in INLINE_RE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) >= 5:
            segs.append((part[2:-2], True, False))
        elif part.startswith("*") and part.endswith("*") and len(part) >= 3:
            segs.append((part[1:-1], False, True))
        else:
            segs.append((part, False, False))
    return segs or [(text, False, False)]


def _tune_rpr(rPr, bold, italic):
    """在克隆来的 rPr 上叠加 b/i 标记（已存在则跳过）。"""
    if rPr is None:
        return
    if bold:
        for tag in ("w:b", "w:bCs"):
            if rPr.find(qn(tag)) is None:
                rPr.append(rPr.makeelement(qn(tag), {}))
    if italic:
        if rPr.find(qn("w:i")) is None:
            rPr.append(rPr.makeelement(qn("w:i"), {}))


def clone_run(run_proto, text, bold=False, italic=False):
    """以模板 run 为原型克隆一个 run，只换文字；可叠加粗斜体。"""
    if run_proto is not None:
        r = copy.deepcopy(run_proto)
    else:
        r = None
    if r is None:
        r = run_proto.makeelement(qn("w:r"), {}) if run_proto is not None else None
    if r is None:
        raise RuntimeError("run 原型缺失")
    for c in list(r):
        if c.tag != qn("w:rPr"):
            r.remove(c)
    rPr = r.find(qn("w:rPr"))
    _tune_rpr(rPr, bold, italic)
    t = r.makeelement(qn("w:t"), {})
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    return r


def clone_para(proto_p, run_proto, text):
    """以模板段落为原型克隆一个新段落，按行内标记拆 run；pPr 完全继承。"""
    p = copy.deepcopy(proto_p)
    for child in list(p):
        if child.tag != qn("w:pPr"):
            p.remove(child)
    for t, bold, italic in parse_inline(text):
        p.append(clone_run(run_proto, t, bold, italic))
    return p


# ---------------------------------------------------------------- md 解析 ----

IMG_RE = re.compile(r"^!\[([^\]]*)\]\(([^)]+)\)$")
CJK_TITLE_RE = re.compile(r"^(\d+(?:\.\d+)*)\s*(.+)$")


def norm_heading(text: str) -> str:
    """'1 引言' → '1引言'，与模板原样一致（编号后不留空格）。"""
    m = CJK_TITLE_RE.match(text.strip())
    return f"{m.group(1)}{m.group(2).strip()}" if m else text.strip()


def parse_md(path):
    """返回 (cover, blocks)。blocks 为 [(kind, payload)]，
    kind ∈ h1/h2/h3/p/li/table/img。"""
    with open(path, encoding="utf-8") as f:
        lines = f.read().splitlines()

    cover = {}
    blocks = []
    i = 0
    in_comment = False
    in_cover = False
    cover_members = []
    pending_caption = None

    while i < len(lines):
        raw = lines[i]
        line = raw.rstrip()
        stripped = line.strip()

        # HTML 注释（可能跨行）：写作提示，绝不能进正文
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            i += 1
            continue
        if stripped.startswith("<!--"):
            if "-->" not in stripped:
                in_comment = True
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        # 一级标题 = 文档标题，模板已有，跳过
        if stripped.startswith("# "):
            i += 1
            continue

        # 分隔线、引用块、元信息
        if stripped in ("---", "***") or stripped.startswith(">"):
            i += 1
            continue

        # 图片（独立成行）
        m = IMG_RE.match(stripped)
        if m:
            blocks.append(("img", {"caption": m.group(1).strip(), "path": m.group(2).strip()}))
            i += 1
            continue

        # 标题
        m = re.match(r"^(#{2,4})\s+(.*)$", stripped)
        if m:
            level = len(m.group(1)) - 1  # ## → 1
            title = norm_heading(m.group(2))
            if level == 1 and title == "封面":
                in_cover = True
                i += 1
                continue
            in_cover = False
            blocks.append((f"h{level}", title))
            i += 1
            continue

        # 表格
        if stripped.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                if not all(re.fullmatch(r":?-{2,}:?", c) for c in cells):
                    rows.append(cells)
                i += 1
            if rows:
                if in_cover:
                    for r in rows[1:]:
                        if len(r) < 2:
                            continue
                        k, v = r[0].strip(), r[1].strip()
                        if k.startswith("项目组员"):
                            cover_members.append(v)
                        elif k.startswith("项目组长"):
                            cover["组长"] = v
                        elif k == "班级":
                            cover["班级"] = v
                        elif k == "项目名称":
                            cover["项目名称"] = v
                        elif k == "指导教师":
                            cover["指导教师"] = v
                        elif k == "开课学期":
                            cover["开课学期"] = v
                        elif k == "完成时间":
                            cover["完成时间"] = v
                else:
                    blocks.append(("table", {"caption": pending_caption, "rows": rows}))
                    pending_caption = None
            continue

        # 列表
        if re.match(r"^[-*+]\s+", stripped):
            blocks.append(("li", re.sub(r"^[-*+]\s+", "", stripped)))
            i += 1
            continue

        # 表题（紧邻表格的上一行，形如 "表 6-1 投资估算表"）
        if re.match(r"^表\s*\d+[-－]\d+\s", stripped):
            pending_caption = stripped
            i += 1
            continue

        # 普通段落
        if not in_cover:
            blocks.append(("p", stripped))
        i += 1

    cover["组员"] = cover_members
    return cover, blocks


# ---------------------------------------------------------------- 生成 docx --

COVER_SLOTS = {
    11: (["项目组长", "学号"], "组长"),
    12: (["项目组员", "学号"], "member"),
    13: (["学号"], "member"),
    14: (["学号"], "member"),
    17: (["项目名称"], "项目名称"),
    18: (["指导教师"], "指导教师"),
}


def build(template: str, md_path: str, out_path: str):
    cover, blocks = parse_md(md_path)
    md_dir = os.path.dirname(os.path.abspath(md_path))
    doc = Document(template)
    paras = doc.paragraphs

    # ---------- 1. 封面 ----------
    def split_pair(s):
        if not s:
            return "", ""
        parts = [p.strip() for p in re.split(r"[/／]", s)]
        return (parts[0], parts[1] if len(parts) > 1 else "")

    leader = split_pair(cover.get("组长", ""))
    members = [split_pair(m) for m in cover.get("组员", [])]
    members += [("", "")] * (3 - len(members))

    slot_values = {
        11: ["", leader[0], leader[1]],
        12: ["", members[0][0], members[0][1]],
        13: [members[1][0], members[1][1]],
        14: [members[2][0], members[2][1]],
        17: ["", cover.get("项目名称", "")],
        18: ["", cover.get("指导教师", "")],
    }
    for idx, (labels, _key) in COVER_SLOTS.items():
        vals = slot_values[idx]
        if not any(v.strip() for v in vals):
            continue  # 全空则保持模板原样
        p = paras[idx]
        try:
            _rewrite_runs(p._p, segments_of(p._p, labels, vals))
        except ValueError as e:
            print(f"  ! 封面第 {idx} 行填失败：{e}")

    # 班级：模板里是 '班    级      xxx班'，把含 xxx 的填空区整段换掉。
    # 只在值里完全不含"班"字时才自动补"班"（如"软件2101"→"软件2101班"）；
    # "计算机拔尖班241"这类班级名本身含"班"，不能再补，否则成"…241班"。
    cls = cover.get("班级", "")
    if cls:
        if "班" not in cls:
            cls += "班"
        p = paras[16]
        _rewrite_runs(p._p, segments_of(p._p, ["班", "级"], ["", "", cls]))

    # 开课学期：'开课学期  至  学年第  学期'
    term_raw = cover.get("开课学期", "")
    if term_raw:
        m = re.search(r"(\d{4})\s*至\s*(\d{4})\s*学年\s*第\s*([0-9一二三四五六七八九1-9]+)\s*学期", term_raw)
        if m:
            p = paras[19]
            _rewrite_runs(
                p._p,
                segments_of(p._p, ["开课学期", "至", "学年第", "学期"],
                            ["", m.group(1), m.group(2), m.group(3), ""]),
            )

    # 完成时间：'  完成时间  年  月  日'
    date_raw = cover.get("完成时间", "")
    if date_raw:
        m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月\s*(\d{1,2})\s*日", date_raw)
        if m:
            p = paras[20]
            _rewrite_runs(
                p._p,
                segments_of(p._p, ["完成时间", "年", "月", "日"],
                            ["  ", m.group(1), m.group(2), m.group(3), ""]),
            )

    # ---------- 2. 取原型段落（删除前先留样本） ----------
    def find_proto(pred):
        for p in doc.paragraphs:
            if pred(p):
                return p._p
        return None

    h1_proto = find_proto(lambda p: p.style.name == "Heading 1")
    h2_proto = find_proto(lambda p: p.style.name == "Heading 2")
    h3_proto = find_proto(lambda p: p.style.name == "Heading 3")
    body_proto = None
    for p in doc.paragraphs:
        if p.style.name == "Normal" and p.text.startswith("说明编写本可行性研究报告的目的"):
            body_proto = p._p
            break
    if body_proto is None:  # 兜底：取正文第一个 Normal 段
        for p in doc.paragraphs:
            if p.style.name == "Normal" and len(p.text.strip()) > 20:
                body_proto = p._p
                break

    def run_proto_of(p_el):
        if p_el is None:
            return None
        r = p_el.find(qn("w:r"))
        return copy.deepcopy(r) if r is not None else None

    h1_r, h2_r, h3_r, body_r = (run_proto_of(h1_proto), run_proto_of(h2_proto),
                                run_proto_of(h3_proto), run_proto_of(body_proto))

    # ---------- 3. 清空正文（保留文档标题段与分节符） ----------
    body = doc.element.body
    p_children = [c for c in body if c.tag == qn("w:p")]
    # 模板正文从第 76 段（0 基）开始；75 段是文档标题，74 段带分节符
    keep_upto = 75
    for p in p_children[keep_upto + 1:]:
        body.remove(p)

    sectPr = body.find(qn("w:sectPr"))

    def add(el):
        sectPr.addprevious(el)

    # ---------- 4. 按 md 重建正文 ----------
    li_counter = [0]
    for kind, payload in blocks:
        if kind == "h1":
            add(clone_para(h1_proto, h1_r, payload))
            li_counter[0] = 0
        elif kind == "h2":
            add(clone_para(h2_proto, h2_r, payload))
            li_counter[0] = 0
        elif kind == "h3":
            add(clone_para(h3_proto, h3_r, payload))
            li_counter[0] = 0
        elif kind == "p":
            add(clone_para(body_proto, body_r, payload))
        elif kind == "li":
            li_counter[0] += 1
            add(clone_para(body_proto, body_r, f"（{li_counter[0]}）{payload}"))
        elif kind == "table":
            add_table(doc, body, sectPr, payload)
        elif kind == "img":
            add_image(doc, body, sectPr, payload, md_dir)

    doc.save(out_path)
    return out_path


def _caption_para(text):
    """题注段（表题/图题共用）：五号、居中。"""
    from docx.oxml import OxmlElement
    p = OxmlElement("w:p")
    pPr = OxmlElement("w:pPr")
    jc = OxmlElement("w:jc")
    jc.set(qn("w:val"), "center")
    pPr.append(jc)
    spacing = OxmlElement("w:spacing")
    spacing.set(qn("w:line"), "300")
    spacing.set(qn("w:lineRule"), "auto")
    pPr.append(spacing)
    p.append(pPr)
    r = OxmlElement("w:r")
    rPr = OxmlElement("w:rPr")
    sz = OxmlElement("w:sz")
    sz.set(qn("w:val"), "21")  # 10.5pt 五号
    rPr.append(sz)
    r.append(rPr)
    t = OxmlElement("w:t")
    t.set(qn("xml:space"), "preserve")
    t.text = text
    r.append(t)
    p.append(r)
    return p


def add_image(doc, body, sectPr, payload, base_dir):
    """插入图片：居中、宽度压缩到版心内；图题在图下方居中（GB 惯例）。

    图片路径相对 md 所在目录解析；图片段/题注段先建后挪到 sectPr 之前。
    """
    from docx.oxml import OxmlElement

    path = payload["path"]
    if not os.path.isabs(path):
        path = os.path.join(base_dir, path)
    if not os.path.exists(path):
        print(f"  ! 图片不存在，已跳过：{path}")
        return

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    pic = run.add_picture(path)
    sect = doc.sections[0]
    usable = sect.page_width - sect.left_margin - sect.right_margin
    if usable and pic.width > usable:
        scale = usable / pic.width
        pic.width = int(pic.width * scale)
        pic.height = int(pic.height * scale)
    el = p._p
    el.getparent().remove(el)
    sectPr.addprevious(el)

    cap = payload.get("caption")
    if cap:
        sectPr.addprevious(_caption_para(cap))


def add_table(doc, body, sectPr, payload):
    """插入 md 表格：五号、居中、细边框；表题在上方居中。

    单元格 west 字体不强制（西文/数字继承模板 docDefaults 的 Times New Roman），
    只设 eastAsia=宋体；支持单元格内 **粗体**。
    """
    from docx.oxml import OxmlElement

    caption = payload.get("caption")
    rows = payload["rows"]

    if caption:
        sectPr.addprevious(_caption_para(caption))

    ncol = max(len(r) for r in rows)
    table = doc.add_table(rows=len(rows), cols=ncol)
    table.style = doc.styles["Normal Table"]
    table.alignment = 1  # center

    # 细边框
    tbl = table._tbl
    tblPr = tbl.tblPr
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement(f"w:{edge}")
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:space"), "0")
        e.set(qn("w:color"), "000000")
        borders.append(e)
    tblPr.append(borders)

    for ri, row in enumerate(rows):
        for ci in range(ncol):
            cell = table.cell(ri, ci)
            cell.text = ""
            para = cell.paragraphs[0]
            para.alignment = WD_ALIGN_PARAGRAPH.CENTER
            raw = row[ci] if ci < len(row) else ""
            for text, bold, _italic in parse_inline(raw):
                run = para.add_run(text)
                run.font.size = Pt(10.5)
                run.font.bold = True if (bold or ri == 0) else None
                rPr = run._element.get_or_add_rPr()
                rFonts = rPr.find(qn("w:rFonts"))
                if rFonts is None:
                    rFonts = OxmlElement("w:rFonts")
                    rPr.insert(0, rFonts)
                rFonts.set(qn("w:eastAsia"), "宋体")

    # add_table 会把表追加在 sectPr 之后，挪到 sectPr 之前
    sectPr.addprevious(tbl)


# ---------------------------------------------------------------- 更新目录 ----

def _word_session():
    import win32com.client as win32

    word = win32.gencache.EnsureDispatch("Word.Application")
    word.Visible = False
    word.DisplayAlerts = False
    return word


def _with_retry(fn, attempts=3, delay=1.5):
    """Word 连续两次启动之间偶发 RPC 不可用，重试即可。"""
    last = None
    for k in range(attempts):
        try:
            return fn()
        except Exception as e:  # noqa: BLE001
            last = e
            if k < attempts - 1:
                time.sleep(delay)
    raise last


def rebuild_toc(path):
    """第一遍：让 Word 重建 TOC 域（条目、超链接、页码全部重算）。"""
    def _run():
        word = _word_session()
        doc = None
        try:
            doc = word.Documents.Open(os.path.abspath(path))
            doc.Fields.Update()
            for toc in doc.TablesOfContents:
                toc.Update()
            doc.Repaginate()
            pages = doc.ComputeStatistics(2)
            doc.Save()
            return pages
        finally:
            if doc is not None:
                doc.Close(0)
            word.Quit()

    return _with_retry(_run)


def restore_toc_styles(path):
    """把 Word 新建的 toc 1/2/3 样式改回模板的 目录 1/2/3。

    Word 重建目录时不认模板里的中文样式名，会另建一套内置 toc N 样式，
    导致加粗、段间距、缩进全部丢失。此处按层级改回，并删除多余样式。
    """
    doc = Document(path)
    fixed = 0
    for p in doc.paragraphs:
        name = p.style.name
        m = re.fullmatch(r"toc\s+(\d)", name or "", re.IGNORECASE)
        if not m:
            continue
        target = f"目录 {m.group(1)}"
        try:
            p.style = doc.styles[target]
            fixed += 1
        except KeyError:
            pass

    for s in list(doc.styles):
        if re.fullmatch(r"toc\s+\d", s.name or "", re.IGNORECASE):
            s.element.getparent().remove(s.element)

    doc.save(path)
    return fixed


def refresh_page_numbers(path):
    """第二遍：只刷新目录页码，不重建条目，避免样式再次被换掉。"""
    def _run():
        word = _word_session()
        doc = None
        try:
            doc = word.Documents.Open(os.path.abspath(path))
            for toc in doc.TablesOfContents:
                toc.UpdatePageNumbers()
            doc.Repaginate()
            pages = doc.ComputeStatistics(2)
            doc.Save()
            return pages
        finally:
            if doc is not None:
                doc.Close(0)
            word.Quit()

    return _with_retry(_run)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    # 默认模板：课程根 .workbuddy/tools/可行性报告模板.docx（按脚本位置解析，任意 CWD 可跑）
    here = os.path.dirname(os.path.abspath(__file__))
    template = os.path.normpath(os.path.join(here, "..", ".workbuddy", "tools", "可行性报告模板.docx"))
    if "--template" in sys.argv:
        template = sys.argv[sys.argv.index("--template") + 1]
        args = [a for a in args if a != template]

    if len(args) < 2:
        print(__doc__)
        sys.exit(1)

    md_path, out_path = args[0], args[1]
    print(f"[1/4] 生成 → {out_path}")
    build(template, md_path, out_path)

    try:
        print("[2/4] 重建目录（Word 更新 TOC 域）")
        pages = rebuild_toc(out_path)
        print(f"      完成，共 {pages} 页")

        print("[3/4] 还原本地化目录样式（目录 1/2/3）")
        n = restore_toc_styles(out_path)
        print(f"      已修正 {n} 条目录条目")

        print("[4/4] 仅刷新目录页码")
        pages = refresh_page_numbers(out_path)
        print(f"      完成，共 {pages} 页")
    except Exception as e:
        print(f"      ! 失败：{e}")
        print("      ! 文档已生成，但目录可能仍是模板旧值，需在 Word 中 Ctrl+A F9 手动更新")
        sys.exit(2)


if __name__ == "__main__":
    main()
