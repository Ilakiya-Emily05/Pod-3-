import os
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def convert_md_to_pdf(md_file, pdf_file):
    styles = getSampleStyleSheet()
    
    # Custom styles
    h1_style = styles['Heading1']
    h2_style = styles['Heading2']
    h3_style = styles['Heading3']
    body_style = styles['Normal']
    code_style = ParagraphStyle(
        'Code',
        parent=body_style,
        fontName='Courier',
        fontSize=9,
        leading=11,
        borderPadding=5,
        backColor=colors.lightgrey,
    )

    doc = SimpleDocTemplate(pdf_file, pagesize=letter)
    story = []

    with open(md_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    in_code_block = False
    code_content = []

    for line in lines:
        stripped = line.strip()
        
        # Handle code blocks
        if stripped.startswith('```'):
            if not in_code_block:
                in_code_block = True
                code_content = []
            else:
                in_code_block = False
                story.append(Preformatted('\n'.join(code_content), code_style))
                story.append(Spacer(1, 12))
            continue
        
        if in_code_block:
            code_content.append(line.rstrip())
            continue

        if not stripped:
            story.append(Spacer(1, 12))
            continue

        # Headers
        if stripped.startswith('# '):
            story.append(Paragraph(stripped[2:], h1_style))
            story.append(Spacer(1, 12))
        elif stripped.startswith('## '):
            story.append(Paragraph(stripped[3:], h2_style))
            story.append(Spacer(1, 10))
        elif stripped.startswith('### '):
            story.append(Paragraph(stripped[4:], h3_style))
            story.append(Spacer(1, 8))
        # Bullet points
        elif stripped.startswith('- ') or stripped.startswith('* '):
            story.append(Paragraph(f"• {stripped[2:]}", body_style))
            story.append(Spacer(1, 6))
        # Normal text
        else:
            story.append(Paragraph(line, body_style))
            story.append(Spacer(1, 6))

    doc.build(story)

if __name__ == "__main__":
    artifact_dir = r"C:\Users\HP\.gemini\antigravity\brain\ba34ca51-520e-42dd-a3df-f9b13db8609f"
    md_path = os.path.join(artifact_dir, "api_report.md")
    pdf_path = os.path.join(artifact_dir, "api_report.pdf")
    
    convert_md_to_pdf(md_path, pdf_path)
    print(f"Generated PDF at: {pdf_path}")
