"""Render the one-page executive summary; never reads a model or raw data."""
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'reports/day10/executive_summary.pdf'


def main():
    source = ROOT / 'reports/day10/executive_summary.md'
    font_root = Path('/usr/share/fonts/truetype/dejavu')
    regular, bold = 'Helvetica', 'Helvetica-Bold'
    if (font_root/'DejaVuSans.ttf').exists():
        pdfmetrics.registerFont(TTFont('DejaVu', str(font_root/'DejaVuSans.ttf')))
        pdfmetrics.registerFont(TTFont('DejaVuBold', str(font_root/'DejaVuSans-Bold.ttf')))
        regular, bold = 'DejaVu', 'DejaVuBold'
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('BodySmall', fontName=regular, fontSize=9, leading=12, spaceAfter=6))
    styles.add(ParagraphStyle('SectionSmall', fontName=bold, fontSize=10, leading=12, spaceBefore=6, spaceAfter=5, textColor=colors.HexColor('#155e75')))
    styles.add(ParagraphStyle('SummaryTitle', fontName=bold, fontSize=19, leading=22, spaceAfter=8, textColor=colors.HexColor('#0f172a')))
    doc = SimpleDocTemplate(str(OUT), pagesize=(8.5*inch,11*inch), rightMargin=43,leftMargin=43,topMargin=33,bottomMargin=30,
                            title='UCI Heart Disease | Executive Summary', author='Lucas Medina')
    story=[]; block=[]; table=[]
    def flush():
        if block:
            story.append(Paragraph(escape(' '.join(block)).replace('**',''),styles['BodySmall']))
            block.clear()
    def flush_table():
        if table:
            rows=[[Paragraph(escape(cell),styles['BodySmall']) for cell in row] for row in table]
            grid=Table(rows,colWidths=[108,30,160,102,101])
            grid.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e0f2fe')),('VALIGN',(0,0),(-1,-1),'TOP'),
                                     ('LINEBELOW',(0,0),(-1,0),0.5,colors.HexColor('#94a3b8')),('BOTTOMPADDING',(0,0),(-1,-1),3),('TOPPADDING',(0,0),(-1,-1),3)]))
            story.extend([grid,Spacer(1,6)]);table.clear()
    for line in source.read_text().splitlines():
        if line.startswith('|'):
            flush()
            if not set(line.replace('|','').replace(':','').strip()) <= {'-',' '}:
                table.append([c.strip() for c in line.strip('|').split('|')])
        else:
            flush_table()
            if line.startswith('# '): flush();story.append(Paragraph(escape(line[2:]),styles['SummaryTitle']))
            elif line.startswith('## '): flush();story.append(Paragraph(escape(line[3:]),styles['SectionSmall']))
            elif not line.strip():flush()
            else:block.append(line.strip())
    flush();flush_table()
    def footer(canvas, doc):
        canvas.setFont('Helvetica',7)
        canvas.setFillColor(colors.HexColor('#475569'))
        canvas.drawString(43,19,'Educational research | Frozen c06 | Accepted-model reproduction pending')
        canvas.drawRightString(569,19,str(doc.page))
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)


if __name__ == '__main__':
    main()
