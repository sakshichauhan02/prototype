import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

def generate_resume_pdf(fields: dict, output_path: str):
    """
    Generates a beautifully styled professional resume PDF using ReportLab.
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Elegant Slate and Cyan palette
    primary_color = colors.HexColor("#0F172A")
    secondary_color = colors.HexColor("#475569")
    accent_color = colors.HexColor("#06B6D4") # Cyan accent
    
    name_style = ParagraphStyle(
        'ResumeName',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=24,
        leading=28,
        textColor=primary_color,
        alignment=TA_CENTER,
        spaceAfter=4
    )
    
    contact_style = ParagraphStyle(
        'ResumeContact',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=secondary_color,
        alignment=TA_CENTER,
        spaceAfter=12
    )
    
    section_heading_style = ParagraphStyle(
        'ResumeSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=primary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=4
    )
    
    name = fields.get("name", "Applicant Name")
    contact = fields.get("contact", "")
    education = fields.get("education", "")
    experience = fields.get("experience", "")
    skills = fields.get("skills", "")
    
    # Add Header Elements
    story.append(Paragraph(name, name_style))
    contact_formatted = contact.replace(" | ", "  •  ")
    story.append(Paragraph(contact_formatted, contact_style))
    
    def add_section(title, content):
        if not content:
            return
        story.append(Paragraph(title.upper(), section_heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=1, spaceAfter=6))
        
        lines = content.split('\n')
        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue
            if line_str.startswith('-') or line_str.startswith('*'):
                bullet_content = line_str[1:].strip()
                story.append(Paragraph(f"• {bullet_content}", ParagraphStyle(
                    'ResumeBullet',
                    parent=body_style,
                    leftIndent=12,
                    firstLineIndent=-8,
                    spaceAfter=3
                )))
            else:
                story.append(Paragraph(line_str, body_style))
        story.append(Spacer(1, 8))

    add_section("Experience", experience)
    add_section("Education", education)
    add_section("Skills", skills)
    
    doc.build(story)
