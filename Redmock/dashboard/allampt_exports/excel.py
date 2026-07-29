import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from django.utils import timezone

def generate_attempts_excel(queryset, company, response):
    """
    Generate a professional Excel (.xlsx) report of test attempts.

    Args:
        queryset : Attempt queryset (already filtered)
        company  : Company instance
        response : Django HttpResponse (content_type set to openpyxl type)
    """
    # Create workbook and select active worksheet
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Test Attempts"

    # Ensure grid lines are visible
    ws.views.sheetView[0].showGridLines = True

    # Styling Palette (Hex codes without '#')
    C_HEADER_BG = "0077B6"       # Mid accent blue
    C_HEADER_TEXT = "FFFFFF"     # White text
    C_TITLE_TEXT = "03045E"      # Deep Navy
    C_ZEBRA_BG = "F4FDFF"        # Light alternate strip tint
    C_BORDER_COLOR = "E0F2FE"    # Faint divider border

    # Font styles
    font_title = Font(name="Calibri", size=16, bold=True, color=C_TITLE_TEXT)
    font_subtitle = Font(name="Calibri", size=10, italic=True, color="555555")
    font_header = Font(name="Calibri", size=11, bold=True, color=C_HEADER_TEXT)
    font_data = Font(name="Calibri", size=11)

    # Alignment styles
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # Border styles
    thin_border = Border(
        left=Side(style='thin', color=C_BORDER_COLOR),
        right=Side(style='thin', color=C_BORDER_COLOR),
        top=Side(style='thin', color=C_BORDER_COLOR),
        bottom=Side(style='thin', color=C_BORDER_COLOR)
    )

    # Row fills
    fill_header = PatternFill(start_color=C_HEADER_BG, end_color=C_HEADER_BG, fill_type="solid")
    fill_zebra = PatternFill(start_color=C_ZEBRA_BG, end_color=C_ZEBRA_BG, fill_type="solid")

    # Title block
    ws['A1'] = f"{company.name} – Test Attempts Report"
    ws['A1'].font = font_title
    ws.row_dimensions[1].height = 25

    generated_str = timezone.now().strftime("%B %d, %Y  %I:%M %p")
    ws['A2'] = f"Generated on {generated_str}"
    ws['A2'].font = font_subtitle
    ws.row_dimensions[2].height = 18

    # Blank row
    ws.row_dimensions[3].height = 15

    # Headers definition
    headers = [
        "Attempt ID",
        "Candidate Name",
        "Candidate Email",
        "Session Type",
        "Test Category",
        "Difficulty Level",
        "Total Questions",
        "Correct Answers",
        "Wrong Answers",
        "Score (%)",
        "Date Attempted"
    ]

    header_row_num = 4
    ws.row_dimensions[header_row_num].height = 25

    # Write headers
    for col_idx, header in enumerate(headers, 1):
        cell = ws.cell(row=header_row_num, column=col_idx, value=header)
        cell.font = font_header
        cell.fill = fill_header
        cell.alignment = align_center

    # Write data rows
    current_row = 5
    for attempt in queryset:
        local_created = timezone.localtime(attempt.created_at)
        formatted_date = local_created.strftime("%b %d, %Y, %I:%M %p")

        # Color-coded score formatting (fonts)
        pct = float(attempt.percentage)
        if pct >= 70:
            font_score = Font(name="Calibri", size=11, bold=True, color="166534") # Green
        elif pct >= 50:
            font_score = Font(name="Calibri", size=11, bold=True, color="92400E") # Amber
        else:
            font_score = Font(name="Calibri", size=11, bold=True, color="991B1B") # Red

        # Insert values
        ws.cell(row=current_row, column=1, value=attempt.pk).alignment = align_center
        ws.cell(row=current_row, column=2, value=attempt.candidate.name).alignment = align_left
        ws.cell(row=current_row, column=3, value=attempt.candidate.email).alignment = align_left
        ws.cell(row=current_row, column=4, value=attempt.get_session_type_display()).alignment = align_center
        ws.cell(row=current_row, column=5, value=attempt.get_test_category_display()).alignment = align_left
        ws.cell(row=current_row, column=6, value=attempt.level.capitalize()).alignment = align_center
        ws.cell(row=current_row, column=7, value=attempt.question_count).alignment = align_right
        ws.cell(row=current_row, column=8, value=attempt.correct_count).alignment = align_right
        ws.cell(row=current_row, column=9, value=attempt.wrong_count).alignment = align_right

        score_cell = ws.cell(row=current_row, column=10, value=pct / 100.0)
        score_cell.number_format = '0.0%'
        score_cell.font = font_score
        score_cell.alignment = align_right

        ws.cell(row=current_row, column=11, value=formatted_date).alignment = align_center

        # Zebra striping & border styles for non-score cells
        use_zebra = (current_row % 2 == 0)
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=current_row, column=col_idx)
            cell.border = thin_border
            if col_idx != 10: # Keep score font colored
                cell.font = font_data
            if use_zebra:
                cell.fill = fill_zebra

        ws.row_dimensions[current_row].height = 20
        current_row += 1

    # Auto-adjust column widths based on content
    for col in ws.columns:
        max_len = 0
        col_letter = get_column_letter(col[0].column)
        # Avoid including the title / subtitle rows when calculating column widths
        for cell in col[3:]: # start from header row
            if cell.value:
                # Format checks
                if cell.number_format == '0.0%' and isinstance(cell.value, float):
                    max_len = max(max_len, 6) # e.g. "100.0%"
                else:
                    max_len = max(max_len, len(str(cell.value)))
        ws.column_dimensions[col_letter].width = max(max_len + 4, 12)

    # Save to response object (Django HttpResponse is file-like)
    wb.save(response)
