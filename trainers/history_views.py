from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils.dateparse import parse_date
from django.core.paginator import Paginator
from django.http import HttpResponse
import csv
from .models import Attendance, Participant
from pravaah.accounts.decorators import trainer_required


@login_required
@trainer_required
def attendance_history(request, batch_id):
    """Show attendance sessions summary for a batch and optional session detail when ?session_date=YYYY-MM-DD provided.
    Supports pagination, date range filtering and CSV export for a session.
    """
    session_date_str = request.GET.get('session_date')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    page = int(request.GET.get('page', 1))

    # build base queryset
    qs = Attendance.objects.filter(batch_id=batch_id)
    if date_from:
        df = parse_date(date_from)
        if df:
            qs = qs.filter(session_date__gte=df)
    if date_to:
        dt = parse_date(date_to)
        if dt:
            qs = qs.filter(session_date__lte=dt)

    sessions = qs.values('session_date').annotate(
        present=Count('id', filter=Q(status='Present')),
        absent=Count('id', filter=Q(status='Absent')),
        late=Count('id', filter=Q(status='Late')),
        total=Count('id')
    ).order_by('-session_date')

    # paginate sessions list
    sessions_list = list(sessions)
    paginator = Paginator(sessions_list, 10)
    page_obj = paginator.get_page(page)

    # if export csv for a selected session_date or for a date range
    if request.GET.get('export') == 'csv':
        # export single session
        if session_date_str:
            sd = parse_date(session_date_str)
            if sd:
                rows = Attendance.objects.filter(batch_id=batch_id, session_date=sd).order_by('-marked_at')
                # prepare CSV
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="attendance_{batch_id}_{session_date_str}.csv"'
                writer = csv.writer(response)
                writer.writerow(['session_date','participant_id', 'participant_name', 'status', 'marked_at', 'marked_by'])
                pids = [r.participant_id for r in rows]
                participants_map = {}
                if pids:
                    qs_p = Participant.objects.filter(id__in=pids).values('id', 'name')
                    participants_map = {p['id']: p['name'] for p in qs_p}
                for r in rows:
                    writer.writerow([r.session_date, r.participant_id, participants_map.get(r.participant_id, ''), r.status, r.marked_at, r.marked_by])
                return response
        # export date range (full batch attendance)
        else:
            # require at least one date filter
            if not (date_from or date_to):
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = f'attachment; filename="attendance_{batch_id}_all.csv"'
                writer = csv.writer(response)
                writer.writerow(['session_date','participant_id', 'participant_name', 'status', 'marked_at', 'marked_by'])
                return response

            rows = Attendance.objects.filter(batch_id=batch_id)
            if date_from:
                df = parse_date(date_from)
                if df:
                    rows = rows.filter(session_date__gte=df)
            if date_to:
                dt = parse_date(date_to)
                if dt:
                    rows = rows.filter(session_date__lte=dt)
            rows = rows.order_by('session_date', 'participant_id')

            response = HttpResponse(content_type='text/csv')
            fname_from = date_from or 'start'
            fname_to = date_to or 'end'
            response['Content-Disposition'] = f'attachment; filename="attendance_{batch_id}_{fname_from}_{fname_to}.csv"'
            writer = csv.writer(response)
            writer.writerow(['session_date','participant_id', 'participant_name', 'status', 'marked_at', 'marked_by'])
            pids = list(rows.values_list('participant_id', flat=True))
            participants_map = {}
            if pids:
                qs_p = Participant.objects.filter(id__in=set(pids)).values('id', 'name')
                participants_map = {p['id']: p['name'] for p in qs_p}
            for r in rows:
                writer.writerow([r.session_date, r.participant_id, participants_map.get(r.participant_id, ''), r.status, r.marked_at, r.marked_by])
            return response

    session_rows = None
    participants_map = {}
    if session_date_str:
        sd = parse_date(session_date_str)
        if sd:
            session_rows = list(Attendance.objects.filter(batch_id=batch_id, session_date=sd).order_by('-marked_at'))
            pids = [r.participant_id for r in session_rows]
            if pids:
                qs = Participant.objects.filter(id__in=pids).values('id', 'name')
                participants_map = {p['id']: p['name'] for p in qs}

    return render(request, 'trainers/attendance_history.html', {
        'batch_id': batch_id,
        'sessions': page_obj,
        'session_rows': session_rows,
        'participants_map': participants_map,
        'selected_date': session_date_str,
        'page_obj': page_obj,
    })
