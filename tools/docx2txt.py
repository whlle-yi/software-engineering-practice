import zipfile, re, sys, io
from xml.etree import ElementTree as ET

W = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'

def para_text(p):
    parts = []
    for node in p.iter():
        if node.tag == W + 't':
            parts.append(node.text or '')
        elif node.tag == W + 'tab':
            parts.append('\t')
        elif node.tag == W + 'br':
            parts.append('\n')
    return ''.join(parts)

def style_of(p):
    ppr = p.find(W + 'pPr')
    if ppr is None:
        return ''
    ps = ppr.find(W + 'pStyle')
    if ps is None:
        return ''
    return ps.get(W + 'val') or ''

def extract(path):
    z = zipfile.ZipFile(path)
    root = ET.fromstring(z.read('word/document.xml'))
    body = root.find(W + 'body')
    out = []
    for child in body:
        if child.tag == W + 'p':
            t = para_text(child).strip()
            if t:
                st = style_of(child)
                out.append((st, t))
        elif child.tag == W + 'tbl':
            out.append(('TABLE_BEGIN', ''))
            for tr in child.findall(W + 'tr'):
                cells = []
                for tc in tr.findall(W + 'tc'):
                    cells.append(' '.join(para_text(p).strip() for p in tc.findall(W + 'p')).strip())
                out.append(('ROW', ' | '.join(cells)))
            out.append(('TABLE_END', ''))
    return out

if __name__ == '__main__':
    rows = extract(sys.argv[1])
    for st, t in rows:
        if st in ('TABLE_BEGIN', 'TABLE_END', 'ROW'):
            print(f'[{st}] {t}')
        else:
            print(f'<{st}> {t}')
