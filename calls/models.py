from django.db import models
from django.contrib.auth.models import User


class ReasonForCalling(models.Model):
    label = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.label


class Intervention(models.Model):
    label = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.label


class SuicideMethod(models.Model):
    label = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.label


class RiskDetail(models.Model):
    label = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.label


class SourceOfInfo(models.Model):
    label = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.label


class Caller(models.Model):
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('lgbtq', 'LGBTQ++'),
        ('na', 'N/A'),
    ]

    STATUS_CHOICES = [
        ('single', 'Single'),
        ('single_living_in', 'Single (Living in)'),
        ('married', 'Married'),
        ('separated', 'Separated'),
        ('widowed', 'Widowed'),
        ('na', 'N/A'),
    ]

    name = models.CharField(max_length=100)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    age = models.PositiveIntegerField()
    location = models.CharField(max_length=255)
    source_of_info = models.ForeignKey(SourceOfInfo, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.name


class CallSession(models.Model):
    SHIFT_CHOICES = [
        ('6-2', '6am–2pm'),
        ('2-10', '2pm–10pm'),
        ('10-6', '10pm–6am'),
        ('8-4', '8am–4pm'),
    ]

    RISK_LEVEL_CHOICES = [
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
    ]

    OTHER_PERSON_GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('lgbtq', 'LGBTQ++'),
        ('na', 'N/A'),
    ]

    OTHER_PERSON_STATUS_CHOICES = [
        ('single', 'Single'),
        ('single_living_in', 'Single (Living in)'),
        ('married', 'Married'),
        ('separated', 'Separated'),
        ('widowed', 'Widowed'),
        ('na', 'N/A'),
    ]

    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    caller = models.ForeignKey(Caller, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.CharField(max_length=10, choices=SHIFT_CHOICES)
    time_called = models.TimeField()
    time_ended = models.TimeField()
    length_of_call = models.DurationField()

    # Core call details
    risk_level = models.CharField(max_length=10, choices=RISK_LEVEL_CHOICES)
    reasons_for_calling = models.ForeignKey(ReasonForCalling, on_delete=models.SET_NULL, null=True, blank=True)
    interventions = models.ForeignKey(Intervention, on_delete=models.SET_NULL, null=True, blank=True)
    suicide_methods = models.ForeignKey(SuicideMethod, on_delete=models.SET_NULL, null=True, blank=True)
    risk_details = models.ForeignKey(RiskDetail, on_delete=models.SET_NULL, null=True, blank=True)
    comments = models.TextField(blank=True, null=True)

    # If calling for another person
    is_calling_for_others = models.BooleanField(default=False)
    other_person_name = models.CharField(max_length=100, blank=True, null=True)
    other_person_gender = models.CharField(max_length=10, choices=OTHER_PERSON_GENDER_CHOICES)
    other_person_status = models.CharField(max_length=50, choices=OTHER_PERSON_STATUS_CHOICES)
    other_person_age = models.PositiveIntegerField(blank=True, null=True)
    other_person_location = models.CharField(max_length=255, blank=True, null=True)

    # AI-generated summary
    ai_summary = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Call on {self.date} with {self.caller.name}"


class SiteConfig(models.Model):
    site_name = models.CharField(max_length=100, default="ThriveHub Lite")
    tagline = models.CharField(max_length=255, blank=True)
    logo = models.ImageField(upload_to='logos/', null=True, blank=True)
    favicon = models.ImageField(upload_to='site/', null=True, blank=True)
    primary_color = models.CharField(max_length=7, default="#0d6efd", help_text="Hex code, e.g. #0d6efd")
    dark_mode_default = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Configuration"
        verbose_name_plural = "Site Configuration"

    def __str__(self):
        return "Site Settings"

    def save(self, *args, **kwargs):
        if not self.pk and SiteConfig.objects.exists():
            raise ValueError("There can only be one SiteConfig instance.")
        super().save(*args, **kwargs)


DESIGNATION_CHOICES = [
    ('Psychologist', 'Psychologist'),
    ('Psychiatrist', 'Psychiatrist'),
]

GENDER_CHOICES = [
    ('Male', 'Male'),
    ('Female', 'Female'),
]


class ReferralContact(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default="Female")
    designation = models.CharField(max_length=20, choices=DESIGNATION_CHOICES, default="Psychologist")
    location = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, null=True, blank=True)
    phone_2 = models.CharField(max_length=15, null=True, blank=True)
    phone_3 = models.CharField(max_length=15, null=True, blank=True)
    email = models.EmailField(max_length=255, null=True, blank=True)
    alt_email = models.EmailField(max_length=255, null=True, blank=True)
    date_updated = models.DateField(auto_now=True)

    def __str__(self):
        return self.name


class ShiftType(models.Model):
    name = models.CharField(max_length=50)        # e.g., "Morning"
    start_time = models.TimeField()               # e.g., 06:00
    end_time = models.TimeField()                 # e.g., 14:00
    color = models.CharField(max_length=7, default="#0d6efd")
    is_teleconsult = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class Holiday(models.Model):
    date = models.DateField(unique=True)
    label = models.CharField(max_length=100)       # e.g., "Independence Day"

    def __str__(self):
        return f"{self.label} ({self.date})"


class ShiftPreference(models.Model):
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.ForeignKey(ShiftType, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('responder', 'date', 'shift')

    def __str__(self):
        return f"{self.responder} prefers {self.shift} on {self.date}"


class TimeOffRequest(models.Model):
    responder = models.ForeignKey(User, on_delete=models.CASCADE)

    # Extend to support multi-day leave
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Keep shift optional: if null, it's a full-day or multi-day leave
    shift = models.ForeignKey(ShiftType, on_delete=models.CASCADE, null=True, blank=True)

    reason = models.TextField(blank=True)

    status_choices = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='pending')

    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_off_requests'
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        if self.start_date == self.end_date:
            return f"{self.responder} time-off on {self.start_date} ({self.shift or 'Full Day'})"
        return f"{self.responder} leave from {self.start_date} to {self.end_date}"


class ShiftAssignment(models.Model):
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    shift = models.ForeignKey(ShiftType, on_delete=models.CASCADE)
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='assigned_shifts')
    assigned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('responder', 'date', 'shift')

    def __str__(self):
        return f"{self.responder} → {self.shift} on {self.date}"


class MonthlyTeleconsult(models.Model):
    responder = models.ForeignKey(User, on_delete=models.CASCADE)
    month = models.DateField()
    year = models.PositiveIntegerField()

    class Meta:
        unique_together = ('responder', 'month')

    def __str__(self):
        return f"{self.responder} - {self.month.strftime('%B %Y')}"
