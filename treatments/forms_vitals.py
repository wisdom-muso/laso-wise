"""
Forms for Vital Signs Management
"""
from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from .models_vitals import VitalSign, VitalSignAlert

User = get_user_model()


class VitalSignForm(forms.ModelForm):
    """Form for creating and updating vital sign records"""
    
    class Meta:
        model = VitalSign
        fields = [
            'patient', 'systolic_bp', 'diastolic_bp', 'heart_rate',
            'temperature', 'respiratory_rate', 'oxygen_saturation',
            'weight', 'height', 'cholesterol_total', 'cholesterol_ldl',
            'cholesterol_hdl', 'blood_glucose', 'notes', 'measurement_context'
        ]
        
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2',
                'data-placeholder': _('Select patient...')
            }),
            'systolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 120'),
                'min': '50',
                'max': '300'
            }),
            'diastolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 80'),
                'min': '30',
                'max': '200'
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 72'),
                'min': '30',
                'max': '250'
            }),
            'temperature': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 36.5'),
                'step': '0.1',
                'min': '30.0',
                'max': '45.0'
            }),
            'respiratory_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 16'),
                'min': '8',
                'max': '60'
            }),
            'oxygen_saturation': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 98'),
                'min': '70',
                'max': '100'
            }),
            'weight': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 70.5'),
                'step': '0.1',
                'min': '20.0',
                'max': '500.0'
            }),
            'height': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 175'),
                'min': '100',
                'max': '250'
            }),
            'cholesterol_total': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 185'),
                'min': '100',
                'max': '500'
            }),
            'cholesterol_ldl': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 110'),
                'min': '50',
                'max': '300'
            }),
            'cholesterol_hdl': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 45'),
                'min': '20',
                'max': '150'
            }),
            'blood_glucose': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 95'),
                'min': '50',
                'max': '500'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Clinical notes or observations...')
            }),
            'measurement_context': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., "Morning reading", "Post-exercise"')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit patient choices based on user permissions
        if self.user:
            if self.user.is_doctor():
                # Doctors can select from their patients
                self.fields['patient'].queryset = User.objects.filter(
                    user_type='patient',
                    patient_appointments__doctor=self.user
                ).distinct()
            elif self.user.is_admin_user():
                # Admins can select any patient
                self.fields['patient'].queryset = User.objects.filter(user_type='patient')
            else:
                # Others cannot select patients
                self.fields['patient'].queryset = User.objects.none()
        
        # Add help text and validation messages
        self.fields['systolic_bp'].help_text = _('Normal: 90-120 mmHg')
        self.fields['diastolic_bp'].help_text = _('Normal: 60-80 mmHg')
        self.fields['heart_rate'].help_text = _('Normal: 60-100 bpm')
        self.fields['temperature'].help_text = _('Normal: 36.1-37.2°C')
        self.fields['oxygen_saturation'].help_text = _('Normal: 95-100%')
        self.fields['cholesterol_total'].help_text = _('Normal: <200 mg/dL')
        self.fields['blood_glucose'].help_text = _('Normal fasting: 70-100 mg/dL')
    
    def clean(self):
        cleaned_data = super().clean()
        systolic = cleaned_data.get('systolic_bp')
        diastolic = cleaned_data.get('diastolic_bp')
        
        # Validate blood pressure relationship
        if systolic and diastolic and systolic <= diastolic:
            raise forms.ValidationError(
                _('Systolic blood pressure must be higher than diastolic blood pressure.')
            )
        
        # Validate cholesterol values
        total_chol = cleaned_data.get('cholesterol_total')
        ldl_chol = cleaned_data.get('cholesterol_ldl')
        hdl_chol = cleaned_data.get('cholesterol_hdl')
        
        if total_chol and ldl_chol and hdl_chol:
            if ldl_chol + hdl_chol > total_chol:
                raise forms.ValidationError(
                    _('LDL + HDL cholesterol cannot exceed total cholesterol.')
                )
        
        return cleaned_data


class VitalSignFilterForm(forms.Form):
    """Form for filtering vital sign records"""
    
    patient = forms.ModelChoiceField(
        queryset=User.objects.filter(user_type='patient'),
        required=False,
        empty_label=_('All Patients'),
        widget=forms.Select(attrs={
            'class': 'form-select',
            'data-control': 'select2'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('From Date')
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label=_('To Date')
    )
    
    risk_level = forms.ChoiceField(
        choices=[('', _('All Risk Levels'))] + VitalSign.RISK_LEVEL_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        }),
        label=_('Risk Level')
    )
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit patient choices based on user permissions
        if user:
            if user.is_doctor():
                self.fields['patient'].queryset = User.objects.filter(
                    user_type='patient',
                    patient_appointments__doctor=user
                ).distinct()
            elif user.is_admin_user():
                self.fields['patient'].queryset = User.objects.filter(user_type='patient')
            else:
                # Patients don't need patient filter
                del self.fields['patient']


class QuickVitalSignForm(forms.ModelForm):
    """Simplified form for quick vital sign entry"""
    
    class Meta:
        model = VitalSign
        fields = ['patient', 'systolic_bp', 'diastolic_bp', 'heart_rate', 'notes']
        
        widgets = {
            'patient': forms.Select(attrs={
                'class': 'form-select',
                'data-control': 'select2'
            }),
            'systolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '120',
                'required': True
            }),
            'diastolic_bp': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '80',
                'required': True
            }),
            'heart_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '72',
                'required': True
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Quick notes...')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Limit patient choices
        if self.user and self.user.is_doctor():
            self.fields['patient'].queryset = User.objects.filter(
                user_type='patient',
                patient_appointments__doctor=self.user
            ).distinct()
        elif self.user and self.user.is_admin_user():
            self.fields['patient'].queryset = User.objects.filter(user_type='patient')


class VitalSignAlertForm(forms.ModelForm):
    """Form for managing vital sign alerts"""
    
    class Meta:
        model = VitalSignAlert
        fields = ['status', 'acknowledged_by']
        
        widgets = {
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'acknowledged_by': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Limit acknowledged_by to doctors and admins
        self.fields['acknowledged_by'].queryset = User.objects.filter(
            user_type__in=['doctor', 'admin']
        )


class BulkVitalSignForm(forms.Form):
    """Form for bulk operations on vital signs"""
    
    ACTION_CHOICES = [
        ('delete', _('Delete Selected')),
        ('export', _('Export Selected')),
        ('mark_reviewed', _('Mark as Reviewed')),
    ]
    
    action = forms.ChoiceField(
        choices=ACTION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    selected_vitals = forms.CharField(
        widget=forms.HiddenInput()
    )
    
    def clean_selected_vitals(self):
        data = self.cleaned_data['selected_vitals']
        try:
            vital_ids = [int(id) for id in data.split(',') if id.strip()]
            return vital_ids
        except ValueError:
            raise forms.ValidationError(_('Invalid vital sign IDs'))


class VitalSignSearchForm(forms.Form):
    """Advanced search form for vital signs"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by patient name, notes, or context...'),
            'autocomplete': 'off'
        })
    )
    
    bp_range_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Min systolic BP')
        }),
        label=_('Min Systolic BP')
    )
    
    bp_range_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Max systolic BP')
        }),
        label=_('Max Systolic BP')
    )
    
    hr_range_min = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Min heart rate')
        }),
        label=_('Min Heart Rate')
    )
    
    hr_range_max = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Max heart rate')
        }),
        label=_('Max Heart Rate')
    )
    
    has_alerts = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        }),
        label=_('Has Active Alerts')
    )