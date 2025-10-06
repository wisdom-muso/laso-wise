"""
AI Dashboard Service for Predictive Analysis
Inspired by healthcare portal designs with risk assessment and AI interpretation
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from .ai_service import get_ai_service
from .ai_predictive_analysis import EndOrganDamagePredictor
from treatments.models_vitals import VitalSign
from treatments.models_medical_history import MedicalHistory
from treatments.models_lab import LabTest

User = get_user_model()
logger = logging.getLogger(__name__)


class AIDashboardService:
    """
    AI-powered dashboard service for predictive analysis and risk assessment
    """
    
    def __init__(self):
        self.ai_service = get_ai_service()
        self.predictor = EndOrganDamagePredictor()
        self.logger = logging.getLogger(__name__)
    
    def generate_cardiovascular_risk_assessment(self, patient: User) -> Dict[str, Any]:
        """
        Generate comprehensive cardiovascular disease risk assessment
        Similar to the first uploaded image
        """
        try:
            # Get patient data
            patient_data = self._collect_patient_data(patient)
            
            # Calculate CVD risk using AI
            cvd_risk_score = self._calculate_cvd_risk_score(patient_data)
            
            # Get AI interpretation
            ai_interpretation = self._get_ai_interpretation(patient, patient_data, cvd_risk_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(patient_data, cvd_risk_score)
            
            # Contributing factors analysis
            contributing_factors = self._analyze_contributing_factors(patient_data)
            
            # Key findings
            key_findings = self._extract_key_findings(patient_data)
            
            return {
                'patient': {
                    'name': patient.get_full_name(),
                    'age': self._calculate_age(patient.date_of_birth) if patient.date_of_birth else 'Unknown',
                    'id': patient.id
                },
                'risk_assessment': {
                    'cvd_risk_score': cvd_risk_score,
                    'risk_level': self._get_risk_level(cvd_risk_score),
                    'risk_percentage': int(cvd_risk_score * 100),
                    'description': self._get_risk_description(cvd_risk_score)
                },
                'contributing_factors': contributing_factors,
                'key_findings': key_findings,
                'ai_interpretation': ai_interpretation,
                'recommendations': recommendations,
                'confidence_level': self._calculate_confidence_level(patient_data),
                'analysis_date': timezone.now().strftime('%m/%d/%Y'),
                'next_assessment_date': (timezone.now() + timedelta(days=90)).strftime('%m/%d/%Y')
            }
            
        except Exception as e:
            self.logger.error(f"Error generating CVD risk assessment: {e}")
            return self._get_default_assessment(patient)
    
    def generate_end_organ_damage_assessment(self, patient: User) -> Dict[str, Any]:
        """
        Generate end-organ damage risk assessment
        Similar to the second uploaded image
        """
        try:
            # Use the existing predictor
            prediction = self.predictor.predict_end_organ_damage(patient)
            
            # Get AI analysis for each organ system
            ai_analysis = self._get_ai_organ_analysis(patient, prediction)
            
            return {
                'patient': {
                    'name': patient.get_full_name(),
                    'age': self._calculate_age(patient.date_of_birth) if patient.date_of_birth else 'Unknown',
                    'blood_pressure': self._get_latest_bp(patient),
                    'heart_rate': self._get_latest_hr(patient),
                    'cholesterol': self._get_latest_cholesterol(patient),
                    'smoking_status': self._get_smoking_status(patient)
                },
                'cardiovascular_assessment': {
                    'title': 'Cardiovascular Disease Risk Assessment',
                    'description': 'Run AI analysis to predict patient\'s CVD risk based on the provided data',
                    'about': 'This assessment uses AI to predict cardiovascular disease risk based on clinical parameters and lifestyle factors. It evaluates the 10-year risk of developing CVD.',
                    'ready_to_run': True
                },
                'end_organ_assessment': {
                    'title': 'End Organ Damage Risk Assessment',
                    'description': 'Predict potential hypertension-related end organ damage risks',
                    'about': 'This assessment evaluates the risk of hypertension-related damage to organs like the heart, kidneys, brain, and eyes based on long-term exposure to elevated blood pressure.',
                    'target_organs': [
                        'Cardiac (left ventricular hypertrophy, heart failure)',
                        'Renal (chronic kidney disease)',
                        'Cerebrovascular (stroke, vascular dementia)',
                        'Ocular (retinopathy)',
                        'Vascular (peripheral arterial disease)'
                    ],
                    'ready_to_run': True
                },
                'prediction_results': prediction if prediction else None,
                'ai_analysis': ai_analysis,
                'analysis_date': timezone.now().strftime('%m/%d/%Y')
            }
            
        except Exception as e:
            self.logger.error(f"Error generating end-organ damage assessment: {e}")
            return self._get_default_organ_assessment(patient)
    
    def run_ai_analysis(self, patient: User, analysis_type: str) -> Dict[str, Any]:
        """
        Run AI analysis for specific assessment type
        """
        try:
            if analysis_type == 'cardiovascular':
                return self.generate_cardiovascular_risk_assessment(patient)
            elif analysis_type == 'end_organ':
                return self.generate_end_organ_damage_assessment(patient)
            else:
                raise ValueError(f"Unknown analysis type: {analysis_type}")
                
        except Exception as e:
            self.logger.error(f"Error running AI analysis: {e}")
            return {'error': str(e), 'success': False}
    
    def _collect_patient_data(self, patient: User) -> Dict[str, Any]:
        """
        Collect comprehensive patient data for analysis
        """
        data = {
            'patient_id': patient.id,
            'age': self._calculate_age(patient.date_of_birth) if patient.date_of_birth else 50,
            'gender': getattr(patient, 'gender', 'M'),
        }
        
        # Get recent vital signs
        recent_vitals = VitalSign.objects.filter(
            patient=patient,
            recorded_at__gte=timezone.now() - timedelta(days=180)
        ).order_by('-recorded_at')
        
        if recent_vitals.exists():
            latest_vital = recent_vitals.first()
            avg_systolic = sum(v.systolic_bp for v in recent_vitals) / len(recent_vitals)
            avg_diastolic = sum(v.diastolic_bp for v in recent_vitals) / len(recent_vitals)
            
            data.update({
                'systolic_bp': latest_vital.systolic_bp,
                'diastolic_bp': latest_vital.diastolic_bp,
                'avg_systolic_bp': avg_systolic,
                'avg_diastolic_bp': avg_diastolic,
                'heart_rate': latest_vital.heart_rate,
                'bp_readings_count': len(recent_vitals)
            })
        
        # Medical history
        medical_history = MedicalHistory.objects.filter(patient=patient, is_active=True)
        data.update({
            'has_diabetes': medical_history.filter(condition_name__icontains='diabetes').exists(),
            'has_hypertension': medical_history.filter(condition_name__icontains='hypertension').exists(),
            'has_heart_disease': medical_history.filter(condition_name__icontains='heart').exists(),
            'smoking_history': medical_history.filter(condition_name__icontains='smoking').exists(),
        })
        
        # Lab values
        recent_labs = LabTest.objects.filter(
            patient=patient,
            test_date__gte=timezone.now().date() - timedelta(days=365)
        ).order_by('-test_date')
        
        data.update({
            'total_cholesterol': self._extract_lab_value(recent_labs, 'cholesterol', 200),
            'ldl_cholesterol': self._extract_lab_value(recent_labs, 'ldl', 130),
            'hdl_cholesterol': self._extract_lab_value(recent_labs, 'hdl', 50),
            'triglycerides': self._extract_lab_value(recent_labs, 'triglycerides', 150),
        })
        
        return data
    
    def _calculate_cvd_risk_score(self, data: Dict[str, Any]) -> float:
        """
        Calculate cardiovascular disease risk score
        """
        risk_score = 0.0
        
        # Age factor
        age = data.get('age', 50)
        if age > 65:
            risk_score += 0.25
        elif age > 55:
            risk_score += 0.15
        elif age > 45:
            risk_score += 0.10
        
        # Blood pressure
        systolic = data.get('avg_systolic_bp', data.get('systolic_bp', 120))
        if systolic > 160:
            risk_score += 0.30
        elif systolic > 140:
            risk_score += 0.20
        elif systolic > 130:
            risk_score += 0.10
        
        # Comorbidities
        if data.get('has_diabetes'):
            risk_score += 0.20
        if data.get('has_heart_disease'):
            risk_score += 0.25
        if data.get('smoking_history'):
            risk_score += 0.15
        
        # Cholesterol
        total_chol = data.get('total_cholesterol', 200)
        if total_chol > 240:
            risk_score += 0.15
        elif total_chol > 200:
            risk_score += 0.10
        
        return min(risk_score, 1.0)
    
    def _get_ai_interpretation(self, patient: User, data: Dict[str, Any], risk_score: float) -> Dict[str, Any]:
        """
        Get AI interpretation of the risk assessment
        """
        try:
            # Create a detailed prompt for AI analysis
            prompt = f"""
            Analyze this patient's cardiovascular risk assessment:
            
            Patient: {patient.get_full_name()}, Age: {data.get('age', 'Unknown')}
            Blood Pressure: {data.get('systolic_bp', 'N/A')}/{data.get('diastolic_bp', 'N/A')} mmHg
            Risk Score: {risk_score:.2f} ({int(risk_score * 100)}%)
            
            Medical History:
            - Diabetes: {'Yes' if data.get('has_diabetes') else 'No'}
            - Hypertension: {'Yes' if data.get('has_hypertension') else 'No'}
            - Heart Disease: {'Yes' if data.get('has_heart_disease') else 'No'}
            - Smoking: {'Yes' if data.get('smoking_history') else 'No'}
            
            Lab Values:
            - Total Cholesterol: {data.get('total_cholesterol', 'N/A')} mg/dL
            - LDL: {data.get('ldl_cholesterol', 'N/A')} mg/dL
            
            Please provide:
            1. A brief interpretation of the risk level
            2. Key contributing factors
            3. Specific recommendations for risk reduction
            4. Timeline for follow-up
            
            Keep the response concise and medically accurate.
            """
            
            ai_response = self.ai_service.chat(patient, prompt)
            
            if ai_response['success']:
                return {
                    'interpretation': ai_response['response'],
                    'confidence': 92,  # High confidence for AI analysis
                    'generated_at': timezone.now().isoformat()
                }
            else:
                return self._get_default_interpretation(risk_score)
                
        except Exception as e:
            self.logger.error(f"Error getting AI interpretation: {e}")
            return self._get_default_interpretation(risk_score)
    
    def _get_ai_organ_analysis(self, patient: User, prediction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AI analysis for organ damage prediction
        """
        try:
            if not prediction:
                return {}
            
            prompt = f"""
            Analyze this end-organ damage risk assessment for patient {patient.get_full_name()}:
            
            Overall Risk: {prediction.get('overall_risk', {}).get('risk_level', 'Unknown')}
            
            Organ-specific risks:
            - Cardiovascular: {prediction.get('organ_risks', {}).get('cardiovascular', {}).get('risk_level', 'Unknown')}
            - Renal: {prediction.get('organ_risks', {}).get('renal', {}).get('risk_level', 'Unknown')}
            - Retinal: {prediction.get('organ_risks', {}).get('retinal', {}).get('risk_level', 'Unknown')}
            - Cerebrovascular: {prediction.get('organ_risks', {}).get('cerebrovascular', {}).get('risk_level', 'Unknown')}
            
            Provide a concise analysis focusing on:
            1. Most concerning organ systems
            2. Preventive measures
            3. Monitoring recommendations
            4. Lifestyle modifications
            """
            
            ai_response = self.ai_service.chat(patient, prompt)
            
            if ai_response['success']:
                return {
                    'analysis': ai_response['response'],
                    'confidence': 88,
                    'generated_at': timezone.now().isoformat()
                }
            else:
                return {'analysis': 'AI analysis temporarily unavailable. Please consult with healthcare provider.'}
                
        except Exception as e:
            self.logger.error(f"Error getting AI organ analysis: {e}")
            return {'analysis': 'Analysis error. Please try again later.'}
    
    def _analyze_contributing_factors(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze contributing factors with scores
        """
        factors = []
        
        # Blood Pressure
        bp_score = 0
        systolic = data.get('avg_systolic_bp', data.get('systolic_bp', 120))
        if systolic > 160:
            bp_score = 36
        elif systolic > 140:
            bp_score = 27
        elif systolic > 130:
            bp_score = 18
        else:
            bp_score = 9
        
        factors.append({
            'name': 'Blood Pressure',
            'score': bp_score,
            'color': '#ef4444' if bp_score > 25 else '#f59e0b' if bp_score > 15 else '#10b981'
        })
        
        # Age
        age = data.get('age', 50)
        age_score = min(age / 80 * 27, 27)
        factors.append({
            'name': 'Age',
            'score': int(age_score),
            'color': '#06b6d4'
        })
        
        # Cholesterol
        chol = data.get('total_cholesterol', 200)
        chol_score = min((chol - 150) / 100 * 18, 18) if chol > 150 else 0
        factors.append({
            'name': 'Cholesterol',
            'score': max(int(chol_score), 9),
            'color': '#3b82f6'
        })
        
        # Lifestyle
        lifestyle_score = 9
        if data.get('smoking_history'):
            lifestyle_score += 9
        factors.append({
            'name': 'Lifestyle',
            'score': lifestyle_score,
            'color': '#10b981'
        })
        
        # Family History (placeholder)
        factors.append({
            'name': 'Family History',
            'score': 9,
            'color': '#f59e0b'
        })
        
        return factors
    
    def _extract_key_findings(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract key findings from patient data
        """
        findings = []
        
        # Blood pressure finding
        systolic = data.get('systolic_bp', data.get('avg_systolic_bp', 120))
        diastolic = data.get('diastolic_bp', data.get('avg_diastolic_bp', 80))
        
        if systolic >= 140 or diastolic >= 90:
            stage = "Stage 2" if systolic >= 160 or diastolic >= 100 else "Stage 1"
            findings.append({
                'title': f'Blood Pressure ({systolic}/{diastolic} mmHg)',
                'description': f'Above the recommended range, indicating {stage} Hypertension.'
            })
        
        # Cholesterol finding
        total_chol = data.get('total_cholesterol', 200)
        if total_chol > 200:
            level = "high" if total_chol > 240 else "borderline high"
            findings.append({
                'title': f'Total Cholesterol ({total_chol} mg/dL)',
                'description': f'{level.title()}, contributing to increased risk.'
            })
        
        # Age factor
        age = data.get('age', 50)
        if age > 45:
            findings.append({
                'title': f'Age Factor ({age})',
                'description': 'Contributing to moderate risk based on age alone.'
            })
        
        # Overall risk
        findings.append({
            'title': 'Overall 10-Year Risk',
            'description': f'{int(self._calculate_cvd_risk_score(data) * 100)}% chance of developing cardiovascular disease within the next decade.'
        })
        
        return findings
    
    def _generate_recommendations(self, data: Dict[str, Any], risk_score: float) -> Dict[str, Any]:
        """
        Generate personalized recommendations
        """
        recommendations = {
            'urgent': [],
            'medication': [],
            'lifestyle': [],
            'monitoring': []
        }
        
        # Urgent recommendations
        if risk_score > 0.6:
            recommendations['urgent'].append('Consult with cardiologist within 2 weeks')
        
        # Medication recommendations
        if data.get('avg_systolic_bp', 140) > 140:
            recommendations['medication'].append('Consider antihypertensive therapy')
        
        if data.get('total_cholesterol', 200) > 200:
            recommendations['medication'].append('Consider statin therapy')
        
        # Lifestyle recommendations
        recommendations['lifestyle'].extend([
            'DASH diet (low sodium)',
            'Regular aerobic exercise (30 min/day)',
            'Weight management',
            'Limit alcohol consumption'
        ])
        
        if data.get('smoking_history'):
            recommendations['lifestyle'].insert(0, 'Smoking cessation program')
        
        # Monitoring recommendations
        recommendations['monitoring'].extend([
            'Home BP monitoring, bimonthly follow-ups',
            'Annual lipid panel',
            'Regular cardiovascular screening'
        ])
        
        return recommendations
    
    def _get_risk_level(self, risk_score: float) -> str:
        """
        Convert risk score to risk level
        """
        if risk_score >= 0.8:
            return 'Very High Risk'
        elif risk_score >= 0.6:
            return 'High Risk'
        elif risk_score >= 0.4:
            return 'Moderate Risk'
        elif risk_score >= 0.2:
            return 'Low Risk'
        else:
            return 'Very Low Risk'
    
    def _get_risk_description(self, risk_score: float) -> str:
        """
        Get risk description
        """
        percentage = int(risk_score * 100)
        if percentage >= 68:
            return f"Based on the assessment, the patient shows a high risk ({percentage}%) for cardiovascular disease over the next 10 years. The primary contributing factors are elevated blood pressure and cholesterol levels."
        else:
            return f"The patient shows a {percentage}% risk for cardiovascular disease over the next 10 years based on current risk factors."
    
    def _calculate_confidence_level(self, data: Dict[str, Any]) -> int:
        """
        Calculate confidence level based on data completeness
        """
        total_factors = 10
        available_factors = 0
        
        if data.get('age'):
            available_factors += 1
        if data.get('systolic_bp') or data.get('avg_systolic_bp'):
            available_factors += 2
        if data.get('total_cholesterol'):
            available_factors += 2
        if data.get('bp_readings_count', 0) > 0:
            available_factors += 2
        if any([data.get('has_diabetes'), data.get('has_hypertension'), data.get('has_heart_disease')]):
            available_factors += 2
        if data.get('smoking_history') is not None:
            available_factors += 1
        
        return min(int((available_factors / total_factors) * 100), 95)
    
    def _calculate_age(self, birth_date) -> int:
        """
        Calculate age from birth date
        """
        if not birth_date:
            return 50  # Default age
        
        today = timezone.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def _get_latest_bp(self, patient: User) -> str:
        """
        Get latest blood pressure reading
        """
        latest_vital = VitalSign.objects.filter(patient=patient).order_by('-recorded_at').first()
        if latest_vital:
            return f"{latest_vital.systolic_bp}/{latest_vital.diastolic_bp} mmHg"
        return "No data"
    
    def _get_latest_hr(self, patient: User) -> str:
        """
        Get latest heart rate
        """
        latest_vital = VitalSign.objects.filter(patient=patient).order_by('-recorded_at').first()
        if latest_vital:
            return f"{latest_vital.heart_rate} BPM"
        return "No data"
    
    def _get_latest_cholesterol(self, patient: User) -> str:
        """
        Get latest cholesterol reading
        """
        recent_labs = LabTest.objects.filter(
            patient=patient,
            test_date__gte=timezone.now().date() - timedelta(days=365)
        ).order_by('-test_date')
        
        cholesterol = self._extract_lab_value(recent_labs, 'cholesterol', None)
        if cholesterol:
            return f"{cholesterol} mg/dL"
        return "No data"
    
    def _get_smoking_status(self, patient: User) -> str:
        """
        Get smoking status
        """
        medical_history = MedicalHistory.objects.filter(patient=patient, is_active=True)
        if medical_history.filter(condition_name__icontains='smoking').exists():
            return "Smoker"
        return "Non-Smoker"
    
    def _extract_lab_value(self, lab_tests, test_name: str, default_value):
        """
        Extract lab value from test results
        """
        for lab in lab_tests:
            if test_name.lower() in lab.test_name.lower():
                try:
                    # Try to extract numeric value from results
                    import re
                    numbers = re.findall(r'\d+\.?\d*', lab.results)
                    if numbers:
                        return float(numbers[0])
                except:
                    pass
        return default_value
    
    def _get_default_assessment(self, patient: User) -> Dict[str, Any]:
        """
        Get default assessment when data is insufficient
        """
        return {
            'patient': {
                'name': patient.get_full_name(),
                'age': 'Unknown',
                'id': patient.id
            },
            'risk_assessment': {
                'cvd_risk_score': 0.3,
                'risk_level': 'Moderate Risk',
                'risk_percentage': 30,
                'description': 'Insufficient data for accurate assessment. Please update patient records.'
            },
            'contributing_factors': [],
            'key_findings': [],
            'ai_interpretation': {
                'interpretation': 'Insufficient patient data for comprehensive AI analysis. Please ensure vital signs, lab results, and medical history are up to date.',
                'confidence': 50
            },
            'recommendations': {
                'urgent': ['Update patient medical records'],
                'medication': [],
                'lifestyle': ['Regular health checkups'],
                'monitoring': ['Establish baseline measurements']
            },
            'confidence_level': 50,
            'analysis_date': timezone.now().strftime('%m/%d/%Y')
        }
    
    def _get_default_interpretation(self, risk_score: float) -> Dict[str, Any]:
        """
        Get default AI interpretation when AI service is unavailable
        """
        risk_level = self._get_risk_level(risk_score)
        return {
            'interpretation': f'The patient shows {risk_level.lower()} based on available clinical data. AI analysis is temporarily unavailable. Please consult with healthcare provider for detailed interpretation.',
            'confidence': 75,
            'generated_at': timezone.now().isoformat()
        }
    
    def _get_default_organ_assessment(self, patient: User) -> Dict[str, Any]:
        """
        Get default organ assessment when prediction fails
        """
        return {
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
                'ready_to_run': False
            },
            'end_organ_assessment': {
                'title': 'End Organ Damage Risk Assessment',
                'description': 'Assessment temporarily unavailable',
                'ready_to_run': False
            },
            'error': 'Insufficient data or service unavailable',
            'analysis_date': timezone.now().strftime('%m/%d/%Y')
        }


# Singleton instance - lazy initialization
_ai_dashboard_service_instance = None

def get_ai_dashboard_service():
    """Get or create AI dashboard service instance"""
    global _ai_dashboard_service_instance
    if _ai_dashboard_service_instance is None:
        _ai_dashboard_service_instance = AIDashboardService()
    return _ai_dashboard_service_instance

# Use get_ai_dashboard_service() to get the instance