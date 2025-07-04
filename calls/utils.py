from .models import SiteConfig
import os
from groq import Groq
from django.conf import settings
from calendar import monthrange
from datetime import date, timedelta
from .models import ShiftType, Holiday


def get_primary_color():
    config = SiteConfig.objects.first()
    return config.primary_color if config else "#0d6efd"  # default Bootstrap blue


# 🔍 Initialize Groq client once
api_key = settings.GROQ_API_KEY


def generate_summary_with_groq(caller=None, session=None, transcript=None):
    try:
        client = Groq(api_key=settings.GROQ_API_KEY)

        if transcript:
            prompt = (
                "You are a professional mental health helpline assistant. Summarize the following call transcript "
                "into a clear, professional paragraph. Focus on the main concerns, emotional tone, urgency, and any "
                "discussed risks without adding information or assumptions.\n\n"
                f"{transcript.strip()}\n\n"
                "Avoid prefacing with 'Here is the summary'. Write it as a single paragraph."
            )
        else:
            if not caller or not session:
                raise ValueError("Caller and session are required for form-based summarization.")

            # 🔁 Shared base
            base_instruction = (
                "You are a professional mental health helpline responder tasked with writing a concise and factual call summary. "
                "Do NOT list field names (like Name:, Age:, etc.). Write in a single paragraph using complete sentences. "
                "Do NOT include bullet points. Use only the information explicitly stated below. Do not invent, guess, or assume anything.\n\n"
            )

            if session.is_calling_for_others:
                prompt = (
                    base_instruction +
                    "The caller is reporting on behalf of another individual. Focus the paragraph on the person being called for.\n\n"
                    f"Other Person's Name: {session.other_person_name or 'N/A'}\n"
                    f"Gender: {session.get_other_person_gender_display() or 'N/A'}\n"
                    f"Status: {session.get_other_person_status_display() or 'N/A'}\n"
                    f"Age: {session.other_person_age or 'N/A'}\n"
                    f"Location: {session.other_person_location or 'N/A'}\n"
                    f"Reason(s) for Calling: {', '.join([r.label for r in session.reasons_for_calling]) or 'None'}\n"
                    f"Intervention(s) Provided: {', '.join([i.label for i in session.interventions]) or 'None'}\n"
                    f"Suicide Method(s) Discussed: {', '.join([s.label for s in session.suicide_methods]) or 'None'}\n"
                    f"Risk Level: {session.get_risk_level_display() or 'N/A'}\n"
                    f"Additional Notes: {session.comments or 'None'}"
                )
            else:
                prompt = (
                    base_instruction +
                    f"Caller Name: {caller.name or 'N/A'}\n"
                    f"Gender: {caller.get_gender_display() or 'N/A'}\n"
                    f"Status: {caller.get_status_display() or 'N/A'}\n"
                    f"Age: {caller.age or 'N/A'}\n"
                    f"Location: {caller.location or 'N/A'}\n"
                    f"Source of Information: {caller.source_of_info or 'N/A'}\n"
                    f"Reason(s) for Calling: {', '.join([r.label for r in session.reasons_for_calling]) or 'None'}\n"
                    f"Intervention(s) Provided: {', '.join([i.label for i in session.interventions]) or 'None'}\n"
                    f"Suicide Method(s) Discussed: {', '.join([s.label for s in session.suicide_methods]) or 'None'}\n"
                    f"Risk Level: {session.get_risk_level_display() or 'N/A'}\n"
                    f"Additional Notes: {session.comments or 'None'}"
                )

            # 🧾 Show in logs
            print("\n🔎 Prompt sent to Groq:\n" + "=" * 40 + f"\n{prompt}\n" + "=" * 40)

        # 🧠 Generate
        response = client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=1,
            max_tokens=1024,
            top_p=1,
            stream=False,
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        print(f"[AI Summary Error] {type(e).__name__}: {e}")
        return "⚠️ Could not generate AI summary at this time."


def generate_calendar_matrix(year, month):
    first_day = date(year, month, 1)
    days_in_month = monthrange(year, month)[1]
    shifts = list(ShiftType.objects.order_by('start_time'))

    calendar_days = []
    for day in range(1, days_in_month + 1):
        current_date = date(year, month, day)
        holiday = Holiday.objects.filter(date=current_date).first()
        calendar_days.append({
            'date': current_date,
            'holiday': holiday,
            'shifts': shifts,
        })

    return calendar_days