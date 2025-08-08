from django import forms
from django.utils.translation import gettext_lazy as _
from .models import VitalRecord, VitalGoal, VitalCategory


class VitalRecordForm(forms.ModelForm):
    """
    Form for recording vital signs
    """
    class Meta:
        model = VitalRecord
        fields = ['category', 'value', 'secondary_value', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'secondary_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        self.recorded_by = kwargs.pop('recorded_by', None)
        super().__init__(*args, **kwargs)
        
        # Only show active vital categories
        self.fields['category'].queryset = VitalCategory.objects.filter(is_active=True)
        
        # Add help text for secondary value
        self.fields['secondary_value'].help_text = _("Required for blood pressure (diastolic value)")
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.patient:
            instance.patient = self.patient
        if self.recorded_by:
            instance.recorded_by = self.recorded_by
            # If recorded by a doctor or admin, mark as professional reading
            if self.recorded_by.role in ['doctor', 'admin']:
                instance.is_professional_reading = True
        
        if commit:
            instance.save()
        return instance


class VitalGoalForm(forms.ModelForm):
    """
    Form for setting vital sign goals
    """
    class Meta:
        model = VitalGoal
        fields = ['category', 'target_value', 'target_date', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'target_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'target_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        self.patient = kwargs.pop('patient', None)
        self.set_by = kwargs.pop('set_by', None)
        super().__init__(*args, **kwargs)
        
        # Only show active vital categories
        self.fields['category'].queryset = VitalCategory.objects.filter(is_active=True)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.patient:
            instance.patient = self.patient
        if self.set_by:
            instance.set_by = self.set_by
        
        if commit:
            instance.save()
        return instance


class DateRangeForm(forms.Form):
    """
    Form for filtering vital records by date range
    """
    start_date = forms.DateField(
        label=_("Start Date"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        label=_("End Date"),
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    category = forms.ModelChoiceField(
        label=_("Vital Sign"),
        queryset=VitalCategory.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )