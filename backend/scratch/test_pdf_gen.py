import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

def generate_resume_pdf(fields: dict, output_path: str):
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
    
    primary_color = colors.HexColor("#0F172A")
    secondary_color = colors.HexColor("#475569")
    accent_color = colors.HexColor("#06B6D4") # Cyan
    
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
        fontSize=10,
        leading=14,
        textColor=secondary_color,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    section_heading_style = ParagraphStyle(
        'ResumeSectionHeading',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        leading=16,
        textColor=primary_color,
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True
    )
    
    body_style = ParagraphStyle(
        'ResumeBody',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor("#1E293B"),
        spaceAfter=6
    )
    
    name = fields.get("name", "Applicant Name")
    contact = fields.get("contact", "")
    education = fields.get("education", "")
    experience = fields.get("experience", "")
    skills = fields.get("skills", "")
    
    story.append(Paragraph(name, name_style))
    contact_formatted = contact.replace(" | ", "  •  ")
    story.append(Paragraph(contact_formatted, contact_style))
    
    def add_section(title, content):
        if not content:
            return
        story.append(Paragraph(title.upper(), section_heading_style))
        story.append(HRFlowable(width="100%", thickness=1, color=accent_color, spaceBefore=2, spaceAfter=8))
        
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
                    leftIndent=15,
                    firstLineIndent=-10,
                    spaceAfter=4
                )))
            else:
                story.append(Paragraph(line_str, body_style))
        story.append(Spacer(1, 10))

    add_section("Experience", experience)
    add_section("Education", education)
    add_section("Skills", skills)
    
    doc.build(story)
    print(f"PDF generated successfully at {output_path}")

if __name__ == "__main__":
    fields = {
        "name": "SAKSHI CHAUHAN",
        "contact": "(+91)-7017400147 | India | sakshichauhan64771@gmail.com | linkedin.com/in/sakshi-chauhan-704973326",
        "education": "B.Tech in Computer Science\nXYZ University (2021-2025)\nGPA: 8.5",
        "experience": "IT Support Intern at ABC Corp\n- Managed desktop troubleshooting and software deployment.\n- Resolved network issues for over 50 users.",
        "skills": "Python, JavaScript, React, FastAPI, SQL, Git, Linux"
    }
    generate_resume_pdf(fields, "test_resume.pdf")
