from django import forms
from .models import Caller, CallSession


class CallerForm(forms.ModelForm):
    class Meta:
        model = Caller
        fields = ['name', 'gender', 'status', 'age', 'location', 'source_of_info']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'age': forms.NumberInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_location'}),
            'source_of_info': forms.Select(attrs={'class': 'form-select'}),
        }


class CallSessionForm(forms.ModelForm):
    class Meta:
        model = CallSession
        exclude = ['caller', 'responder', 'length_of_call', 'created_at']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'shift': forms.Select(attrs={'class': 'form-select'}),
            'time_called': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'time_ended': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'reasons_for_calling': forms.Select(attrs={'class': 'form-select'}),
            'interventions': forms.Select(attrs={'class': 'form-select'}),
            'suicide_methods': forms.Select(attrs={'class': 'form-select'}),
            'risk_details': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': '2'}),
            'is_calling_for_others': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'other_person_name': forms.TextInput(attrs={'class': 'form-control'}),
            'other_person_gender': forms.Select(attrs={'class': 'form-select'}),
            'other_person_status': forms.Select(attrs={'class': 'form-select'}),
            'other_person_age': forms.NumberInput(attrs={'class': 'form-control'}),
            'other_person_location': forms.TextInput(attrs={'class': 'form-control', 'id': 'id_other_person_location'}),
            'ai_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': '5'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reasons_for_calling'].label_from_instance = lambda obj: obj.label
        self.fields['interventions'].label_from_instance = lambda obj: obj.label
        self.fields['suicide_methods'].label_from_instance = lambda obj: obj.label
        self.fields['other_person_name'].required = False
        self.fields['other_person_gender'].required = False
        self.fields['other_person_status'].required = False
        self.fields['other_person_age'].required = False
        self.fields['other_person_location'].required = False
        self.fields['date'].required = False
        self.fields['shift'].required = False

