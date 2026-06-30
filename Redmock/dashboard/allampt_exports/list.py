import datetime
from django.utils import timezone
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_attempts_pdf(queryset, company, response):
    # Printable width: letter is 612 x 792. Margins 36 each side, so 540 pt width.
    doc = SimpleDocTemplate(
        response,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        name='DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#03045e'),
        spaceAfter=4
    )
    
    meta_style = ParagraphStyle(
        name='DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        leading=13,
        textColor=colors.HexColor('#008fd1'),
        spaceAfter=15
    )
    
    summary_style = ParagraphStyle(
        name='DocSummary',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#075985'),
        spaceAfter=15
    )
    
    # Add title and header info
    story.append(Paragraph(f"{company.name} - Test Attempts Report", title_style))
    current_time_str = timezone.now().strftime("%B %d, %Y, %I:%M %p")
    story.append(Paragraph(f"Generated on {current_time_str}", meta_style))
    
    total_count = queryset.count()
    story.append(Paragraph(f"Total Attempts matching filters: {total_count}", summary_style))
    story.append(Spacer(1, 5))
    
    # Column width distribution (Sum = 540 pt)
    col_widths = [220, 100, 100, 120]
    
    # Table Header Row
    header_style = ParagraphStyle(
        name='TableHeader',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=12,
        textColor=colors.white
    )
    
    data = [[
        Paragraph("Candidate", header_style),
        Paragraph("Level", header_style),
        Paragraph("Percentage", header_style),
        Paragraph("Date Attempted", header_style)
    ]]
    
    # Table content styles
    name_style = ParagraphStyle(
        name='CandidateName',
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=colors.HexColor('#03045e')
    )
    
    email_style = ParagraphStyle(
        name='CandidateEmail',
        fontName='Helvetica',
        fontSize=8,
        leading=11,
        textColor=colors.HexColor('#008fd1')
    )
    
    level_style = ParagraphStyle(
        name='AttemptLevel',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#075985')
    )
    
    percentage_style = ParagraphStyle(
        name='AttemptPercentage',
        fontName='Helvetica-Bold',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#03045e')
    )
    
    date_style = ParagraphStyle(
        name='AttemptDate',
        fontName='Helvetica',
        fontSize=9,
        leading=12,
        textColor=colors.HexColor('#075985')
    )
    
    for attempt in queryset:
        candidate_cell = [
            Paragraph(attempt.candidate.name, name_style),
            Paragraph(attempt.candidate.email, email_style)
        ]
        
        level_cell = Paragraph(attempt.level.capitalize(), level_style)
        percentage_cell = Paragraph(f"{attempt.percentage}%", percentage_style)
        
        # Localize date to settings.TIME_ZONE / current timezone
        local_created = timezone.localtime(attempt.created_at)
        formatted_date = local_created.strftime("%b %d, %Y, %I:%M %p")
        date_cell = Paragraph(formatted_date, date_style)
        
        data.append([candidate_cell, level_cell, percentage_cell, date_cell])
        
    # Build Table
    t = Table(data, colWidths=col_widths, repeatRows=1)
    
    # Table Styles: Match dashboard palette (deep blue header, alternating rows)
    t_style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0077b6')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('TOPPADDING', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ('TOPPADDING', (0, 1), (-1, -1), 8),
        ('LINEBELOW', (0, 0), (-1, 0), 1.5, colors.HexColor('#023e8a')),
        ('LINEBELOW', (0, 1), (-1, -1), 0.5, colors.HexColor('#e0f2fe')),
    ])
    
    # Alternating Row Background
    for i in range(1, len(data)):
        if i % 2 == 0:
            t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f4fdff'))
        else:
            t_style.add('BACKGROUND', (0, i), (-1, i), colors.white)
            
    t.setStyle(t_style)
    story.append(t)
    
    doc.build(story)
