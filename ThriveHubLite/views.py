from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from django.http import HttpResponse
from calls.models import CallSession, Caller
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from django.db.models.functions import ExtractYear
import calendar
import csv

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
