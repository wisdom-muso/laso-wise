from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model

from .models_lab import LabTest, TestResult

User = get_user_model()

class LabTestForm(forms.ModelForm):
    """
    Laboratory test creation and editing form.
    """
    class Meta:
        model = LabTest
        fields = ['treatment', 'patient', 'doctor', 'test_name', 'test_details', 'status']
        widgets = {
            'treatment': forms.Select(attrs={'class': 'form-control'}),
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'test_name': forms.TextInput(attrs={'class': 'form-control'}),
            'test_details': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show only users of type doctor
        self.fields['doctor'].queryset = User.objects.filter(user_type='doctor')
        # Show only users of type patient
        self.fields['patient'].queryset = User.objects.filter(user_type='patient')

class TestResultForm(forms.ModelForm):
    """
    Test result creation and editing form.
    """
    class Meta:
        model = TestResult
        fields = ['lab_test', 'result_text', 'reference_values', 'is_normal', 'notes', 'technician', 'result_file']
        widgets = {
            'lab_test': forms.Select(attrs={'class': 'form-control'}),
            'result_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'reference_values': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_normal': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'technician': forms.TextInput(attrs={'class': 'form-control'}),
            'result_file': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Show incomplete tests
        self.fields['lab_test'].queryset = LabTest.objects.filter(status='in_progress')
