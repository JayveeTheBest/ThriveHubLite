from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .forms import CallerForm, CallSessionForm
from django.utils import timezone
from .models import CallSession, Caller, ReasonForCalling, Intervention, SuicideMethod, SourceOfInfo
from .utils import generate_summary_with_groq
from datetime import time, datetime, timedelta


def determine_shift(time_called):
    if time(6, 0) <= time_called < time(14, 0):
        return '6-2'
    elif time(14, 0) <= time_called < time(22, 0):
        return '2-10'
    elif time(22, 0) <= time_called or time_called < time(6, 0):
        return '10-6'
    elif time(8, 0) <= time_called < time(16, 0):
        return '8-4'
    return None


@login_required
def log_call(request):
    last_session = CallSession.objects.order_by('-id').first()
    next_id = (last_session.id + 1) if last_session else 1
    year_suffix = timezone.now().year % 100
    call_id = f"TPCB-{year_suffix:02d}{next_id:04d}"

    if request.method == 'POST':
        print("📩 POST received in log_call view")
        caller_form = CallerForm(request.POST)
        callsession_form = CallSessionForm(request.POST)

        if caller_form.is_valid() and callsession_form.is_valid():
            caller = caller_form.save()
            call = callsession_form.save(commit=False)
            call.caller = caller
            call.responder = request.user
            call.date = timezone.localtime(timezone.now()).date()

            if call.time_called:
                call.shift = determine_shift(call.time_called)

            if call.time_called and call.time_ended:
                from datetime import datetime, timedelta
                t1 = datetime.combine(call.date, call.time_called)
                t2 = datetime.combine(call.date, call.time_ended)
                call.length_of_call = t2 - t1 if t2 >= t1 else timedelta(0)

            call.ai_summary = callsession_form.cleaned_data.get('ai_summary', '')
            call.save()
            callsession_form.save_m2m()

            messages.success(request, "Call log successfully saved.")
            return redirect('call_logs')
        else:
            print("❌ Caller Form Errors:", caller_form.errors.as_text())
            print("❌ CallSession Form Errors:", callsession_form.errors.as_text())

    else:
        caller_form = CallerForm()
        callsession_form = CallSessionForm()

    return render(request, 'calls/log_call.html', {
        'call_id': call_id,
        'caller_form': caller_form,
        'callsession_form': callsession_form
    })


@login_required
def generate_summary(request):
    if request.method == 'POST' and request.headers.get('x-requested-with') == 'XMLHttpRequest':
        try:
            data = request.POST
            print("📥 Raw POST Data:", data)

            # ⏱ Call details
            caller_name = data.get('name', '').strip()
            gender = data.get('gender', '')
            status = data.get('status', '')
            age = data.get('age', '')
            location = data.get('location', '').strip()
            source_id = data.get('source_of_info')

            # 🧠 Risk Assessment & Comments
            risk_level = data.get('risk_level', '')
            comments = data.get('comments', '').strip()

            # 🔄 Multi-choice (single in UI, but stored as FK)
            reason_id = data.get('reasons_for_calling')
            intervention_id = data.get('interventions')
            suicide_id = data.get('suicide_methods')

            is_calling_for_others = data.get('is_calling_for_others') == 'on'

            # 👤 Other person
            other_person_name = data.get('other_person_name', '').strip()
            other_person_gender = data.get('other_person_gender', '')
            other_person_status = data.get('other_person_status', '')
            other_person_age = data.get('other_person_age', '')
            other_person_location = data.get('other_person_location', '').strip()

            # 🎯 Resolve FK fields to model labels
            reason_objs = ReasonForCalling.objects.filter(id=reason_id) if reason_id else []
            intervention_objs = Intervention.objects.filter(id=intervention_id) if intervention_id else []
            suicide_objs = SuicideMethod.objects.filter(id=suicide_id) if suicide_id else []

            source_obj = SourceOfInfo.objects.filter(id=source_id).first()
            source_label = source_obj.label if source_obj else 'N/A'

            # 🧩 Dummy caller
            class DummyCaller:
                def __init__(self, name, gender, status, age, location, source_of_info):
                    self.name = name
                    self._gender = gender
                    self._status = status
                    self.age = age
                    self.location = location
                    self.source_of_info = source_of_info

                def get_gender_display(self):
                    return self._gender

                def get_status_display(self):
                    return self._status

            # 🧩 Dummy session
            class DummySession:
                def __init__(self, risk_level, comments, reasons, interventions, suicides,
                             is_calling_for_others, other_person_name, other_person_gender,
                             other_person_status, other_person_age, other_person_location):
                    self._risk_level = risk_level
                    self.comments = comments
                    self._reasons = reasons
                    self._interventions = interventions
                    self._suicides = suicides
                    self.is_calling_for_others = is_calling_for_others

                    self.other_person_name = other_person_name
                    self._other_person_gender = other_person_gender
                    self._other_person_status = other_person_status
                    self.other_person_age = other_person_age
                    self.other_person_location = other_person_location

                def get_risk_level_display(self):
                    return self._risk_level

                def get_other_person_gender_display(self):
                    return self._other_person_gender

                def get_other_person_status_display(self):
                    return self._other_person_status

                @property
                def reasons_for_calling(self):
                    return self._reasons

                @property
                def interventions(self):
                    return self._interventions

                @property
                def suicide_methods(self):
                    return self._suicides

            # 🧱 Build objects
            dummy_caller = DummyCaller(
                name=caller_name,
                gender=gender,
                status=status,
                age=age,
                location=location,
                source_of_info=source_label
            )

            dummy_session = DummySession(
                risk_level=risk_level,
                comments=comments,
                reasons=reason_objs,
                interventions=intervention_objs,
                suicides=suicide_objs,
                is_calling_for_others=is_calling_for_others,
                other_person_name=other_person_name,
                other_person_gender=other_person_gender,
                other_person_status=other_person_status,
                other_person_age=other_person_age,
                other_person_location=other_person_location
            )

            print("🧠 Generating AI Summary...")
            summary = generate_summary_with_groq(caller=dummy_caller, session=dummy_session)
            print("✅ Summary Generated")
            print("📤 Final Summary Output:\n", summary)

            return JsonResponse({'summary': summary})

        except Exception as e:
            print("❌ Error during summary generation:", e)
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def call_logs(request):
    logs = CallSession.objects.select_related('caller', 'responder').order_by('-date', '-time_called')
    return render(request, 'calls/call_logs.html', {'logs': logs})
