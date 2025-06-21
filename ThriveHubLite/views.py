from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.http import HttpResponse
from django.conf import settings
from calls.models import CallSession, Caller, SiteConfig
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from django.db.models.functions import ExtractYear
import calendar
import csv
import os
import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Font
from openpyxl.chart import BarChart, Reference, PieChart
from openpyxl.chart.label import DataLabelList
from openpyxl.drawing.image import Image as XLImage
from io import BytesIO


GENDER_LABELS = {
    'male': 'Male',
    'female': 'Female',
    'lgbtq': 'LGBTQ++',
    'na': 'N/A',
}
GENDER_COLORS = {
    'Male': '#4C8CAF',
    'Female': '#F48FB1',
    'LGBTQ++': '#F7A6B8',
    'N/A': '#CBDDD5'
}
month_names = list(enumerate(calendar.month_name))[1:]


@login_required
def dashboard(request):
    # Filter: Year & Month from query params or fallback to current
    year = int(request.GET.get('year', datetime.now().year))
    month = request.GET.get('month')
    selected_month = int(month) if month else None
    selected_year = year

    current_start = datetime(year, selected_month or 1, 1)
    prev_start = current_start - relativedelta(months=1)

    # Logs this period
    logs = CallSession.objects.filter(date__year=year)
    if month:
        logs = logs.filter(date__month=month)

    # Logs previous period
    prev_logs = CallSession.objects.filter(
        date__year=prev_start.year,
        date__month=prev_start.month
    )

    # Total Calls
    total_calls = logs.count()
    prev_total_calls = prev_logs.count()
    delta_total = total_calls - prev_total_calls
    trend_total = "up" if delta_total > 0 else "down" if delta_total < 0 else "flat"

    # Most Common Age & Age Cluster
    common_age_data = logs.values('caller__age').annotate(count=Count('id')).order_by('-count').first()
    common_age = common_age_data['caller__age'] if common_age_data else None
    age_range = (common_age - 2, common_age + 2) if common_age else (None, None)

    # High Risk %
    high_risk = logs.filter(risk_level="high").count()
    high_risk_percent = round((high_risk / total_calls * 100), 1) if total_calls else 0

    # Gender distribution
    gender_data = logs.values('caller__gender').annotate(count=Count('id')).order_by('caller__gender')
    gender_labels = [GENDER_LABELS.get(g['caller__gender'], 'Other') for g in gender_data]
    gender_counts = [g['count'] for g in gender_data]
    gender_colors = [GENDER_COLORS.get(label, '#999999') for label in gender_labels]

    # Top 10 Reasons
    reasons_data = logs.values('reasons_for_calling__label') \
        .annotate(count=Count('id')).order_by('-count')[:10]
    top_reasons = []
    max_count = reasons_data[0]['count'] if reasons_data else 1
    base_colors = ['#4CAF8B', '#81C9B3', '#2F6657', '#CBDDD5', '#94BFB1']
    for i, item in enumerate(reasons_data):
        top_reasons.append({
            'label': item['reasons_for_calling__label'] or "Unspecified",
            'count': item['count'],
            'percent': int(item['count'] / max_count * 100),
            'color': base_colors[i % len(base_colors)],
        })

    # Monthly Shift Breakdown
    monthly_raw = logs.values('date__month', 'shift').annotate(count=Count('id'))
    monthly_shifts = defaultdict(lambda: {'6-2': 0, '2-10': 0, '10-6': 0, '8-4': 0})
    for item in monthly_raw:
        monthly_shifts[item['date__month']][item['shift']] = item['count']
    shift_chart_data = {
        'labels': [calendar.month_abbr[i] for i in range(1, 13)],
        '6-2': [monthly_shifts[i]['6-2'] for i in range(1, 13)],
        '2-10': [monthly_shifts[i]['2-10'] for i in range(1, 13)],
        '10-6': [monthly_shifts[i]['10-6'] for i in range(1, 13)],
        '8-4': [monthly_shifts[i]['8-4'] for i in range(1, 13)],
    }

    # Years for filter dropdown
    years = CallSession.objects.annotate(year=ExtractYear('date')) \
        .values_list('year', flat=True).distinct().order_by('year')

    context = {
        'total_calls': total_calls,
        'prev_total_calls': prev_total_calls,
        'total_delta': abs(delta_total),
        'total_trend': trend_total,
        'common_age': common_age,
        'age_range': age_range,
        'high_risk_percent': high_risk_percent,
        'gender_labels': gender_labels,
        'gender_counts': gender_counts,
        'gender_colors': gender_colors,
        'top_reasons': top_reasons,
        'shift_chart_data': shift_chart_data,
        'selected_year': year,
        'selected_month': selected_month,
        'years': years,
        'month_names': month_names,
    }
    return render(request, 'dashboard.html', context)


@login_required
def export_calls(request):
    year = int(request.GET.get('year', datetime.now().year))
    month = request.GET.get('month')

    calls = CallSession.objects.filter(date__year=year)
    if month:
        calls = calls.filter(date__month=month)

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="calls_{year}_{month or "all"}.csv"'

    writer = csv.writer(response)
    writer.writerow(["Date", "Shift", "Caller", "Risk Level", "Age", "Gender", "Status"])

    for c in calls.select_related('caller'):
        writer.writerow([
            c.date,
            c.shift,
            c.caller.name,
            c.risk_level,
            c.caller.age,
            c.caller.get_gender_display(),
            c.caller.get_status_display(),
        ])

    return response


@login_required
def export_soi_excel(request):
    year = int(request.GET.get('year', datetime.now().year))
    month = request.GET.get('month')
    config = SiteConfig.objects.first()

    calls = CallSession.objects.select_related('caller', 'responder').filter(date__year=year)
    if month:
        calls = calls.filter(date__month=month)

    # SHEET 2 – SOI (horizontal table)
    soi_data = []
    for c in calls:
        soi_data.append({
            "Responder": c.responder.first_name if c.responder else "",
            "Tawag Paglaum Code": c.id,
            "Date": c.date.strftime('%Y-%m-%d'),
            "Shift": c.shift,
            "Time Called": c.time_called.strftime('%H:%M') if c.time_called else "",
            "Length of Call": str(c.length_of_call),
            "Time Ended": c.time_ended.strftime('%H:%M') if c.time_ended else "",
            "Name": c.caller.name,
            "Gender": c.caller.get_gender_display(),
            "Status": c.caller.get_status_display(),
            "Age": c.caller.age,
            "Location": c.caller.location,
            "Source of Info": str(c.caller.source_of_info) if c.caller.source_of_info else "",
            "Reason For Calling": c.reasons_for_calling.label if c.reasons_for_calling else "",
            "Intervention": c.interventions,
            "Risk Assessment": c.risk_level,
            "Suicide/ Self Harming Method": c.suicide_methods or "",
            "Other Comments": c.comments or "",
        })
    df_soi = pd.DataFrame(soi_data)

    # Tally data
    def make_summary(df, column, title):
        return df[column].value_counts().reset_index().rename(columns={'index': title, column: 'Count'})

    tally_shift = make_summary(df_soi, "Shift", "Shift")
    tally_gender = make_summary(df_soi, "Gender", "Gender")
    tally_age = make_summary(df_soi, "Age", "Age")
    tally_risk = make_summary(df_soi, "Risk Assessment", "Risk")

    # EXCEL EXPORT
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        # Sheet 2: SOI
        df_soi.to_excel(writer, sheet_name='SOI', index=False)
        workbook = writer.book

        # Sheet 1: Detailed Report (vertical layout)
        sheet = workbook.create_sheet("Detailed Report", 0)
        writer.sheets["Detailed Report"] = sheet

        # Header
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=2)
        sheet.cell(row=1, column=1, value=config.site_name).font = Font(bold=True, size=14)
        if config.logo and os.path.isfile(config.logo.path):
            logo = XLImage(config.logo.path)
            logo.width = 90
            logo.height = 90
            sheet.add_image(logo, "C1")

        row = 3
        for idx, c in enumerate(calls, 1):
            case_fields = [
                ("Case No.", f"TPCEB1-{str(c.id).zfill(3)}"),
                ("Responder No.", c.responder.first_name if c.responder else ""),
                ("Date", c.date.strftime('%Y-%m-%d')),
                ("Time (Duration)", str(c.length_of_call)),
                ("Name", c.caller.name),
                ("Status", c.caller.get_status_display()),
                ("Age", c.caller.age),
                ("Location", c.caller.location),
                ("Source of Info", str(c.caller.source_of_info) if c.caller.source_of_info else ""),
                ("Reason for Calling", c.reasons_for_calling.label if c.reasons_for_calling else ""),
                ("Detailed Report Call", c.ai_summary or "")
            ]
            for label, value in case_fields:
                sheet.cell(row=row, column=1, value=f"{label}:").font = Font(bold=True)
                sheet.cell(row=row, column=2, value=value)
                row += 1
            row += 1

        # Sheet 3: Tally
        sheet = workbook.create_sheet("Tally")
        writer.sheets["Tally"] = sheet
        row = 1
        for name, df in {"Shift": tally_shift, "Gender": tally_gender, "Age": tally_age, "Risk": tally_risk}.items():
            sheet.cell(row=row, column=1, value=name).font = Font(bold=True)
            row += 1
            for col_idx, col in enumerate(df.columns, 1):
                sheet.cell(row=row, column=col_idx, value=col).font = Font(bold=True)
            for tup in df.itertuples(index=False):
                row += 1
                for col_idx, val in enumerate(tup, 1):
                    sheet.cell(row=row, column=col_idx, value=val)

            chart = PieChart() if name == "Gender" else BarChart()
            data = Reference(sheet, min_col=2, min_row=row - len(df) + 1, max_row=row)
            cats = Reference(sheet, min_col=1, min_row=row - len(df) + 1, max_row=row)
            chart.add_data(data, titles_from_data=False)
            chart.set_categories(cats)
            chart.title = f"{name} Distribution"
            if name != "Gender":
                chart.dLbls = DataLabelList()
                chart.dLbls.showVal = True
            if config.primary_color:
                chart.series[0].graphicalProperties.solidFill = config.primary_color.strip("#")
            row += 2
            sheet.add_chart(chart, f"E{row}")
            row += 10

        # Freeze panes & auto-width
        for sname in ["SOI", "Tally"]:
            ws = writer.sheets[sname]
            ws.freeze_panes = "A2"
            for col in ws.columns:
                max_len = max((len(str(cell.value)) if cell.value else 0) for cell in col)
                ws.column_dimensions[col[0].column_letter].width = max_len + 2

        # Sheet visibility fix
        for ws in workbook.worksheets:
            ws.sheet_state = "visible"
        workbook.active = workbook.sheetnames.index("SOI")

    buffer.seek(0)
    filename = f"SOI_Report_{calendar.month_name[int(month)] if month else 'All'}_{year}.xlsx"
    response = HttpResponse(buffer, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response