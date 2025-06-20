from django.db import migrations


def load_initial_data(apps, schema_editor):
    SourceOfInfo = apps.get_model('calls', 'SourceOfInfo')
    ReasonForCalling = apps.get_model('calls', 'ReasonForCalling')
    Intervention = apps.get_model('calls', 'Intervention')
    SuicideMethod = apps.get_model('calls', 'SuicideMethod')

    # SourceOfInfo options
    sources = [
        'Colleague',
        'Family/Friends/Relationships',
        'Government Offices',
        'Media',
        'Medical Professionals',
        'N/A and Refused',
        "NGO's and other Organizations",
        'Online',
        'Other Hotlines',
        'Private Offices/Hospitals',
        'Referral',
        'Repeat Caller',
        'School Personnels',
        'Seminars/IEC Materials',
    ]
    for label in sources:
        SourceOfInfo.objects.get_or_create(label=label)

    # ReasonForCalling options
    reasons = [
        'Abortion', 'Academic Problem', 'Acute Stress Disorder', 'ADHD', 'Alcohol Dependence',
        'Anger Management Issue', 'Anxiety', 'Bipolar and OCD', 'Bullying', 'Calling for Another Person',
        'Current Social Issue', 'Cyberbullying', 'Depression', 'Domestic Abuse', 'Drug Addiction',
        'Emotional Crisis', 'Family Problem', 'Feelings of Sadness and Loneliness', 'Financial Problem',
        'Gambling Problem', 'Global Developmental Delay', 'Grief', 'Indentity Confusion', 'Inquiry',
        'Interpersonal Conflict', 'Intimacy Problems', 'Legal Advice', 'Marital Problem',
        'Medication Concern', 'Mental Health', 'Needed Referral', 'Other', 'Panic Attack',
        'Physical Abuse', 'Postpartum Depression', 'Psychiatric Emergency', 'Psychosomatic Pain',
        'PTSD', 'Rape', 'Relationship Problem', 'Schizophrenia', 'School',
        'Self-harming and Suicidal Attempt/Crisis', 'Sexual Harassment and Sexual Abuse',
        'Suicidal Crisis', 'Suicidal Ideation', 'Symptoms of Insomnia', 'Trauma', 'Work Problem'
    ]
    for label in reasons:
        ReasonForCalling.objects.get_or_create(label=label)

    # Intervention options
    interventions = [
        'Breathing Technique', 'Empathetic Listening', 'Empty Chair Technique', 'PsychEducation',
        'Referred to a Mental Health Professional', 'Referred to the Authority',
        'Referred to the nearest Emergency Unit', 'Safety Planning'
    ]
    for label in interventions:
        Intervention.objects.get_or_create(label=label)

    # SuicideMethod options
    suicide_methods = [
        'Hanging',
        'Overdose',
        'Jumping from Height',
        'Self-inflicted Stabbing or Cutting',
        'Drowning',
        'Gunshot',
        'Burning',
        'Ingestion of Poison or Toxic Substance',
        'Other'
    ]

    for label in suicide_methods:
        SuicideMethod.objects.get_or_create(label=label)


class Migration(migrations.Migration):

    dependencies = [
        ('calls', '0003_sourceofinfo_alter_caller_source_of_info'),  # Replace with your actual last migration filename
    ]

    operations = [
        migrations.RunPython(load_initial_data),
    ]
