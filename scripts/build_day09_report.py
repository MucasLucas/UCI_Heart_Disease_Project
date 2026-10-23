"""Render the reviewed Day 9 Markdown report without loading data or models.

Install reportlab in a separate reporting environment, then run from any directory.
"""
import html
import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, Image,
)

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'reports/day09/report.md'
OUTPUT = ROOT / 'reports/day09/report.pdf'
WIDTH = 516
INK = colors.HexColor('#152B3C')
TEAL = colors.HexColor('#216B82')


def register_fonts():
    """Use portable built-in fonts unless all DejaVu faces are installed."""
    folder = Path('/usr/share/fonts/truetype/dejavu')
    files = {'Report': 'DejaVuSans.ttf', 'ReportBold': 'DejaVuSans-Bold.ttf',
             'ReportItalic': 'DejaVuSans-Oblique.ttf',
             'ReportBoldItalic': 'DejaVuSans-BoldOblique.ttf'}
    if not all((folder / name).exists() for name in files.values()):
        return 'Helvetica', 'Helvetica-Bold'
    for name, file in files.items():
        pdfmetrics.registerFont(TTFont(name, str(folder / file)))
    pdfmetrics.registerFontFamily('Report', normal='Report', bold='ReportBold',
                                 italic='ReportItalic', boldItalic='ReportBoldItalic')
    return 'Report', 'ReportBold'


def inline(text):
    # Preserve balanced parentheses in DOI links, and escape all source HTML.
    pattern = r'\[([^\]]+)\]\(((?:[^()\s]|\([^()]*\))+)\)'
    links = []
    def capture(match):
        label, url = match.groups()
        # The report includes only public HTTPS citations.
        if not url.startswith('https://'):
            return match.group(0)
        links.append(f'<link href="{html.escape(url, quote=True)}" color="#216B82">'
                     f'{html.escape(label)}</link>')
        return f'LINKTOKEN{len(links)-1}END'
    text = re.sub(pattern, capture, text)
    text = html.escape(text)
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    for i, link in enumerate(links):
        text = text.replace(f'LINKTOKEN{i}END', link)
    return text


def build():
    normal, bold = register_fonts()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='BodyReport', fontName=normal, fontSize=8.7,
        leading=12.2, textColor=INK, spaceAfter=8, allowWidows=0, allowOrphans=0))
    styles.add(ParagraphStyle(name='TitleReport', fontName=bold, fontSize=24,
        leading=29, textColor=INK, spaceAfter=17))
    styles.add(ParagraphStyle(name='SectionReport', fontName=bold, fontSize=14,
        leading=18, textColor=TEAL, spaceBefore=3, spaceAfter=11, keepWithNext=True))
    styles.add(ParagraphStyle(name='TableReport', fontName=normal, fontSize=7.4,
        leading=10, textColor=INK, spaceAfter=0))
    styles.add(ParagraphStyle(name='TableHeadReport', parent=styles['TableReport'],
        fontName=bold, textColor=colors.white))
    styles.add(ParagraphStyle(name='ReferenceReport', parent=styles['BodyReport'], fontSize=7.6, leading=10, spaceAfter=5))
    in_references = False
    flow = []
    lines = SOURCE.read_text(encoding='utf-8').splitlines()
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line == '<!-- pagebreak -->':
            flow.append(PageBreak()); i += 1; continue
        if line.startswith('# '):
            flow.append(Paragraph(inline(line[2:]), styles['TitleReport'])); i += 1; continue
        if line.startswith('## '):
            if line == '## References and attribution': in_references = True
            flow.append(Paragraph(inline(line[3:]), styles['SectionReport'])); i += 1; continue
        if line.startswith('|'):
            rows = []
            while i < len(lines) and lines[i].strip().startswith('|'):
                cells = [x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?', x) for x in cells):
                    rows.append(cells)
                i += 1
            n = len(rows[0])
            if any(len(row) != n for row in rows):
                raise ValueError('Unequal table column counts')
            if n == 2: weights = [1.1, 3.1]
            elif n == 3: weights = [1.65, 1.4, 1.4]
            elif n == 4: weights = [1, 1.45, 1.55, 1.55]
            elif n == 5 and rows[0][0] == 'Analysis cohort': weights = [1.1, .32, 1.3, 1.3, 1.32]
            elif n == 5: weights = [1, .78, .8, 1.65, 1.2]
            else: weights = [1.35, 1.15] + [0.85] * (n-2)
            widths = [WIDTH * x / sum(weights) for x in weights]
            data = [[Paragraph(inline(cell), styles['TableHeadReport' if j == 0 else 'TableReport'])
                     for cell in row] for j, row in enumerate(rows)]
            t = Table(data, colWidths=widths, repeatRows=1, hAlign='LEFT')
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), INK),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor('#F0F5F7'), colors.white]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LINEBELOW', (0, -1), (-1, -1), .4, colors.HexColor('#CDDCE2')),
            ]))
            flow.extend([t, Spacer(1, 10)]); continue
        if line.startswith('!['):
            match = re.fullmatch(r'!\[(.*?)\]\((.*?)\)', line)
            if not match:
                raise ValueError(f'Invalid image: {line}')
            path = (SOURCE.parent / match.group(2)).resolve()
            if not path.is_file():
                raise FileNotFoundError(path)
            w, h = ImageReader(str(path)).getSize()
            limit = 420 if path.name == 'global_shap.png' else 475 if path.name == 'local_shap.png' else WIDTH
            image = Image(str(path), width=limit, height=h*limit/w)
            image.hAlign = 'CENTER'
            flow.extend([image, Spacer(1, 7)]); i += 1; continue
        paragraph = [line]; i += 1
        while i < len(lines) and lines[i].strip():
            paragraph.append(lines[i].strip()); i += 1
        flow.append(Paragraph(inline(' '.join(paragraph)), styles['ReferenceReport' if in_references else 'BodyReport']))

    def furniture(canvas, doc):
        canvas.saveState()
        canvas.setStrokeColor(colors.HexColor('#CDDCE2'))
        canvas.line(48, 748, 564, 748)
        canvas.setFillColor(TEAL); canvas.setFont(normal, 7)
        canvas.drawString(48, 759, 'LUCAS MEDINA  /  UCI HEART DISEASE')
        canvas.drawRightString(564, 759, 'DAY 9 RESEARCH REPORT')
        canvas.setFillColor(INK)
        canvas.drawString(48, 30, 'Existing CAD | Retrospective educational study | October 22, 2026')
        canvas.drawRightString(564, 30, str(doc.page))
        canvas.restoreState()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=(612, 792),
        leftMargin=48, rightMargin=48, topMargin=57, bottomMargin=48,
        title='Existing CAD: frozen-model evaluation across UCI cohorts',
        author='Lucas Medina', subject='Retrospective educational CAD classification study')
    doc.build(flow, onFirstPage=furniture, onLaterPages=furniture)
    print(OUTPUT)


if __name__ == '__main__':
    build()
