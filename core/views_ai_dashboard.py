"""
AI Dashboard Views for Predictive Analysis
"""

import json
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.urls import reverse

from .ai_dashboard_service import get_ai_dashboard_service
from .models_ai_config import AIConfiguration

User = get_user_model()
logger = logging.getLogger(__name__)


class AIRiskAssessmentView(LoginRequiredMixin, TemplateView):
    """
    AI Risk Assessment input view (similar to second uploaded image)
    """
    template_name = 'core/ai_risk_assessment_input.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only doctors and admins can access AI risk assessment
        if not (request.user.is_doctor() or request.user.is_admin_user()):
            messages.error(request, "Only doctors and administrators can access AI risk assessment.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get patient
        patient_id = kwargs.get('patient_id')
        patient = get_object_or_404(User, id=patient_id, user_type='patient')
        
        # Get assessment data
        try:
            assessment_data = get_ai_dashboard_service().generate_end_organ_damage_assessment(patient)
            context['assessment_data'] = assessment_data
            context['patient'] = patient
            
        except Exception as e:
            logger.error(f"Error loading AI assessment data: {e}")
            context['assessment_data'] = {
                'patient': {
                    'name': patient.get_full_name(),
                    'age': 'Unknown',
                    'blood_pressure': 'No data',
                    'heart_rate': 'No data',
                    'cholesterol': 'No data',
                    'smoking_status': 'Unknown'
                },
                'cardiovascular_assessment': {
                    'title': 'Cardiovascular Disease Risk Assessment',
                    'description': 'AI analysis temporarily unavailable',
                    'about': 'Please check system configuration and try again.',
                    'ready_to_run': False
                },
                'end_organ_assessment': {
                    'title': 'End Organ Damage Risk Assessment',
                    'description': 'Assessment temporarily unavailable',
                    'about': 'Please check system configuration and try again.',
                    'ready_to_run': False
                }
            }
            context['patient'] = patient
            messages.warning(self.request, "AI assessment data could not be loaded. Some features may be limited.")
        
        return context


class AIRiskAssessmentResultsView(LoginRequiredMixin, TemplateView):
    """
    AI Risk Assessment results view (similar to first uploaded image)
    """
    template_name = 'core/ai_risk_assessment.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Only doctors and admins can access AI risk assessment
        if not (request.user.is_doctor() or request.user.is_admin_user()):
            messages.error(request, "Only doctors and administrators can access AI risk assessment.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get patient
        patient_id = kwargs.get('patient_id')
        patient = get_object_or_404(User, id=patient_id, user_type='patient')
        
        # Get analysis type from query params
        analysis_type = self.request.GET.get('type', 'cardiovascular')
        
        # Generate assessment
        try:
            if analysis_type == 'cardiovascular':
                assessment = get_ai_dashboard_service().generate_cardiovascular_risk_assessment(patient)
            else:
                # For end organ damage, we'll show the cardiovascular assessment as the main result
                # but include organ damage data
                assessment = get_ai_dashboard_service().generate_cardiovascular_risk_assessment(patient)
                organ_assessment = get_ai_dashboard_service().generate_end_organ_damage_assessment(patient)
                assessment['organ_assessment'] = organ_assessment.get('prediction_results')
            
            context['assessment'] = assessment
            context['patient'] = patient
            context['analysis_type'] = analysis_type
            
        except Exception as e:
            logger.error(f"Error generating AI assessment: {e}")
            # Provide fallback assessment
            context['assessment'] = {
                'patient': {
                    'name': patient.get_full_name(),
                    'age': 'Unknown',
                    'id': patient.id
                },
                'risk_assessment': {
                    'cvd_risk_score': 0.3,
                    'risk_level': 'Moderate Risk',
                    'risk_percentage': 30,
                    'description': 'AI analysis temporarily unavailable. Please try again later.'
                },
                'contributing_factors': [
                    {'name': 'Blood Pressure', 'score': 18, 'color': '#f59e0b'},
                    {'name': 'Age', 'score': 15, 'color': '#06b6d4'},
                    {'name': 'Cholesterol', 'score': 12, 'color': '#3b82f6'},
                    {'name': 'Lifestyle', 'score': 9, 'color': '#10b981'},
                    {'name': 'Family History', 'score': 9, 'color': '#f59e0b'}
                ],
                'key_findings': [
                    {
                        'title': 'System Status',
                        'description': 'AI analysis service is temporarily unavailable. Please check system configuration.'
                    }
                ],
                'ai_interpretation': {
                    'interpretation': 'AI analysis could not be completed at this time. Please ensure all patient data is up to date and try again. If the problem persists, contact system administrator.',
                    'confidence': 50
                },
                'recommendations': {
                    'urgent': ['Check system configuration'],
                    'medication': [],
                    'lifestyle': ['Regular health monitoring'],
                    'monitoring': ['System status monitoring']
                },
                'confidence_level': 50,
                'analysis_date': '06/10/2025'
            }
            context['patient'] = patient
            context['analysis_type'] = analysis_type
            messages.error(self.request, "AI analysis could not be completed. Please try again later.")
        
        return context


@login_required
@csrf_exempt
def run_ai_analysis(request, patient_id):
    """
    AJAX endpoint to run AI analysis
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'}, status=405)
    
    # Check permissions
    if not (request.user.is_doctor() or request.user.is_admin_user()):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
    
    try:
        # Get patient
        patient = get_object_or_404(User, id=patient_id, user_type='patient')
        
        # Parse request data
        data = json.loads(request.body)
        analysis_type = data.get('analysis_type', 'cardiovascular')
        
        # Run AI analysis
        result = get_ai_dashboard_service().run_ai_analysis(patient, analysis_type)
        
        if 'error' in result:
            return JsonResponse({'success': False, 'error': result['error']})
        
        return JsonResponse({
            'success': True,
            'analysis_type': analysis_type,
            'redirect_url': reverse('ai-risk-assessment-results', kwargs={'patient_id': patient_id}) + f'?type={analysis_type}'
        })
        
    except Exception as e:
        logger.error(f"Error running AI analysis: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def ai_dashboard_api(request, patient_id):
    """
    API endpoint for AI dashboard data
    """
    if not (request.user.is_doctor() or request.user.is_admin_user()):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        patient = get_object_or_404(User, id=patient_id, user_type='patient')
        
        # Get assessment data
        cardiovascular_data = get_ai_dashboard_service().generate_cardiovascular_risk_assessment(patient)
        organ_damage_data = get_ai_dashboard_service().generate_end_organ_damage_assessment(patient)
        
        return JsonResponse({
            'success': True,
            'cardiovascular_assessment': cardiovascular_data,
            'organ_damage_assessment': organ_damage_data,
            'patient': {
                'id': patient.id,
                'name': patient.get_full_name(),
                'age': cardiovascular_data.get('patient', {}).get('age', 'Unknown')
            }
        })
        
    except Exception as e:
        logger.error(f"Error fetching AI dashboard data: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def generate_risk_report(request, patient_id):
    """
    Generate comprehensive risk assessment report
    """
    if not (request.user.is_doctor() or request.user.is_admin_user()):
        messages.error(request, "Unauthorized access.")
        return redirect('dashboard')
    
    try:
        patient = get_object_or_404(User, id=patient_id, user_type='patient')
        
        # Generate comprehensive assessment
        cardiovascular_assessment = get_ai_dashboard_service().generate_cardiovascular_risk_assessment(patient)
        organ_assessment = get_ai_dashboard_service().generate_end_organ_damage_assessment(patient)
        
        context = {
            'patient': patient,
            'cardiovascular_assessment': cardiovascular_assessment,
            'organ_assessment': organ_assessment,
            'generated_by': request.user,
            'report_type': 'comprehensive'
        }
        
        return render(request, 'core/ai_risk_report.html', context)
        
    except Exception as e:
        logger.error(f"Error generating risk report: {e}")
        messages.error(request, "Could not generate risk report. Please try again.")
        return redirect('patient-detail', patient_id=patient_id)


class DoctorAIDashboardView(LoginRequiredMixin, TemplateView):
    """
    Doctor AI Dashboard with predictive analysis features
    """
    template_name = 'core/doctor_ai_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_doctor():
            messages.error(request, "Only doctors can access this dashboard.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get doctor's patients with recent activity
        doctor_patients = User.objects.filter(
            user_type='patient',
            patient_appointments__doctor=self.request.user
        ).distinct()[:10]
        
        # Get AI analysis summary for each patient
        patient_summaries = []
        for patient in doctor_patients:
            try:
                summary = get_ai_dashboard_service().generate_cardiovascular_risk_assessment(patient)
                patient_summaries.append({
                    'patient': patient,
                    'risk_level': summary.get('risk_assessment', {}).get('risk_level', 'Unknown'),
                    'risk_percentage': summary.get('risk_assessment', {}).get('risk_percentage', 0),
                    'last_analysis': summary.get('analysis_date', 'Never')
                })
            except:
                patient_summaries.append({
                    'patient': patient,
                    'risk_level': 'Data Incomplete',
                    'risk_percentage': 0,
                    'last_analysis': 'Never'
                })
        
        context['patient_summaries'] = patient_summaries
        context['doctor'] = self.request.user
        
        # AI system status
        try:
            ai_config = AIConfiguration.get_default_config()
            context['ai_status'] = {
                'available': bool(ai_config),
                'provider': ai_config.provider if ai_config else 'None',
                'model': ai_config.model_name if ai_config else 'None'
            }
        except:
            context['ai_status'] = {
                'available': False,
                'provider': 'None',
                'model': 'None'
            }
        
        return context


class SuperAdminAIDashboardView(LoginRequiredMixin, TemplateView):
    """
    Super Admin AI Dashboard with system-wide analytics
    """
    template_name = 'core/superadmin_ai_dashboard.html'
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_admin_user():
            messages.error(request, "Only administrators can access this dashboard.")
            return redirect('dashboard')
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # System-wide AI analytics
        total_patients = User.objects.filter(user_type='patient').count()
        high_risk_patients = 0
        moderate_risk_patients = 0
        low_risk_patients = 0
        
        # Sample data for demonstration (in production, this would come from stored assessments)
        context['ai_analytics'] = {
            'total_patients': total_patients,
            'assessments_completed': total_patients * 0.7,  # 70% completion rate
            'high_risk_patients': int(total_patients * 0.15),  # 15% high risk
            'moderate_risk_patients': int(total_patients * 0.35),  # 35% moderate risk
            'low_risk_patients': int(total_patients * 0.5),  # 50% low risk
            'ai_accuracy': 92.5,  # AI model accuracy
            'system_uptime': 99.8  # System uptime percentage
        }
        
        # AI system configuration
        try:
            ai_config = AIConfiguration.get_default_config()
            context['ai_config'] = {
                'provider': ai_config.provider if ai_config else 'Not configured',
                'model': ai_config.model_name if ai_config else 'Not configured',
                'api_url': ai_config.api_url if ai_config else 'Not configured',
                'max_tokens': ai_config.max_tokens if ai_config else 'Not configured',
                'temperature': ai_config.temperature if ai_config else 'Not configured'
            }
        except:
            context['ai_config'] = {
                'provider': 'Not configured',
                'model': 'Not configured',
                'api_url': 'Not configured',
                'max_tokens': 'Not configured',
                'temperature': 'Not configured'
            }
        
        # Recent AI activities (sample data)
        context['recent_activities'] = [
            {
                'type': 'assessment',
                'description': 'CVD risk assessment completed',
                'patient': 'John Doe',
                'doctor': 'Dr. Sarah Johnson',
                'timestamp': '2 minutes ago',
                'risk_level': 'High'
            },
            {
                'type': 'assessment',
                'description': 'End organ damage assessment',
                'patient': 'Jane Smith',
                'doctor': 'Dr. Michael Chen',
                'timestamp': '15 minutes ago',
                'risk_level': 'Moderate'
            },
            {
                'type': 'system',
                'description': 'AI model updated',
                'patient': 'System',
                'doctor': 'Admin',
                'timestamp': '1 hour ago',
                'risk_level': 'Info'
            }
        ]
        
        return context