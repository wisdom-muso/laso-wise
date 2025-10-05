"""
Advanced AI Predictive Analysis System for End-Organ Damage Prediction
Enterprise-grade AI features for healthcare risk assessment
"""
import numpy as np
import logging
from datetime import datetime, timedelta
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.conf import settings
from treatments.models_vitals import VitalSign
from treatments.models_medical_history import MedicalHistory
from treatments.models_lab import LabTest

User = get_user_model()
logger = logging.getLogger(__name__)


class EndOrganDamagePredictor:
    """
    AI-powered end-organ damage prediction system
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Risk factors weights (based on clinical evidence)
        self.risk_weights = {
            'age': 0.15,
            'hypertension_duration': 0.20,
            'bp_control': 0.25,
            'diabetes': 0.15,
            'smoking': 0.10,
            'cholesterol': 0.10,
            'kidney_function': 0.05
        }
        
        # Organ-specific risk thresholds
        self.organ_thresholds = {
            'cardiovascular': 0.6,
            'renal': 0.65,
            'retinal': 0.55,
            'cerebrovascular': 0.7
        }
    
    def predict_end_organ_damage(self, patient, prediction_years=5):
        """
        Predict end-organ damage risk for a patient
        
        Args:
            patient: User object (patient)
            prediction_years: Years ahead to predict (default: 5)
            
        Returns:
            dict: Comprehensive risk assessment
        """
        try:
            # Collect patient data
            patient_data = self.collect_patient_data(patient)
            
            # Calculate risk scores for each organ system
            cardiovascular_risk = self.calculate_cardiovascular_risk(patient_data)
            renal_risk = self.calculate_renal_risk(patient_data)
            retinal_risk = self.calculate_retinal_risk(patient_data)
            cerebrovascular_risk = self.calculate_cerebrovascular_risk(patient_data)
            
            # Overall risk assessment
            overall_risk = self.calculate_overall_risk({
                'cardiovascular': cardiovascular_risk,
                'renal': renal_risk,
                'retinal': retinal_risk,
                'cerebrovascular': cerebrovascular_risk
            })
            
            # Generate recommendations
            recommendations = self.generate_recommendations(patient_data, {
                'cardiovascular': cardiovascular_risk,
                'renal': renal_risk,
                'retinal': retinal_risk,
                'cerebrovascular': cerebrovascular_risk,
                'overall': overall_risk
            })
            
            # Risk timeline
            risk_timeline = self.generate_risk_timeline(patient_data, prediction_years)
            
            prediction = {
                'patient': patient,
                'prediction_date': timezone.now(),
                'prediction_years': prediction_years,
                'organ_risks': {
                    'cardiovascular': {
                        'risk_score': cardiovascular_risk,
                        'risk_level': self.get_risk_level(cardiovascular_risk, 'cardiovascular'),
                        'description': self.get_cardiovascular_description(cardiovascular_risk)
                    },
                    'renal': {
                        'risk_score': renal_risk,
                        'risk_level': self.get_risk_level(renal_risk, 'renal'),
                        'description': self.get_renal_description(renal_risk)
                    },
                    'retinal': {
                        'risk_score': retinal_risk,
                        'risk_level': self.get_risk_level(retinal_risk, 'retinal'),
                        'description': self.get_retinal_description(retinal_risk)
                    },
                    'cerebrovascular': {
                        'risk_score': cerebrovascular_risk,
                        'risk_level': self.get_risk_level(cerebrovascular_risk, 'cerebrovascular'),
                        'description': self.get_cerebrovascular_description(cerebrovascular_risk)
                    }
                },
                'overall_risk': {
                    'risk_score': overall_risk,
                    'risk_level': self.get_overall_risk_level(overall_risk),
                    'description': self.get_overall_description(overall_risk)
                },
                'risk_factors': patient_data,
                'recommendations': recommendations,
                'risk_timeline': risk_timeline,
                'confidence_score': self.calculate_confidence_score(patient_data)
            }
            
            # Log prediction
            self.logger.info(f"Generated end-organ damage prediction for patient {patient.id}")
            
            return prediction
            
        except Exception as e:
            self.logger.error(f"Error in end-organ damage prediction: {e}")
            return self.get_default_prediction(patient)
    
    def collect_patient_data(self, patient):
        """
        Collect comprehensive patient data for risk assessment
        """
        data = {
            'patient_id': patient.id,
            'age': self.calculate_age(patient.date_of_birth) if patient.date_of_birth else 50,
            'gender': getattr(patient, 'gender', 'M'),
        }
        
        # Get recent vital signs (last 6 months)
        recent_vitals = VitalSign.objects.filter(
            patient=patient,
            recorded_at__gte=timezone.now() - timedelta(days=180)
        ).order_by('-recorded_at')
        
        if recent_vitals.exists():
            # Blood pressure control
            avg_systolic = sum(v.systolic_bp for v in recent_vitals) / len(recent_vitals)
            avg_diastolic = sum(v.diastolic_bp for v in recent_vitals) / len(recent_vitals)
            
            data.update({
                'avg_systolic_bp': avg_systolic,
                'avg_diastolic_bp': avg_diastolic,
                'bp_variability': self.calculate_bp_variability(recent_vitals),
                'latest_bp': f"{recent_vitals[0].systolic_bp}/{recent_vitals[0].diastolic_bp}",
                'bp_readings_count': len(recent_vitals)
            })
        else:
            data.update({
                'avg_systolic_bp': 140,  # Default assumption
                'avg_diastolic_bp': 90,
                'bp_variability': 0,
                'latest_bp': 'No data',
                'bp_readings_count': 0
            })
        
        # Medical history
        medical_history = MedicalHistory.objects.filter(patient=patient, is_active=True)
        
        data.update({
            'has_diabetes': medical_history.filter(condition_name__icontains='diabetes').exists(),
            'has_hypertension': medical_history.filter(condition_name__icontains='hypertension').exists(),
            'has_heart_disease': medical_history.filter(condition_name__icontains='heart').exists(),
            'has_kidney_disease': medical_history.filter(condition_name__icontains='kidney').exists(),
            'smoking_history': medical_history.filter(condition_name__icontains='smoking').exists(),
        })
        
        # Hypertension duration
        hypertension_history = medical_history.filter(condition_name__icontains='hypertension').first()
        if hypertension_history and hypertension_history.diagnosed_date:
            duration = (timezone.now().date() - hypertension_history.diagnosed_date).days / 365.25
            data['hypertension_duration_years'] = duration
        else:
            data['hypertension_duration_years'] = 0
        
        # Lab values (if available)
        recent_labs = LabTest.objects.filter(
            patient=patient,
            test_date__gte=timezone.now().date() - timedelta(days=365)
        ).order_by('-test_date')
        
        # Extract lab values
        data.update({
            'creatinine': self.extract_lab_value(recent_labs, 'creatinine', 1.0),
            'egfr': self.extract_lab_value(recent_labs, 'egfr', 90),
            'total_cholesterol': self.extract_lab_value(recent_labs, 'cholesterol', 200),
            'ldl_cholesterol': self.extract_lab_value(recent_labs, 'ldl', 130),
            'hba1c': self.extract_lab_value(recent_labs, 'hba1c', 5.5),
        })
        
        return data
    
    def calculate_cardiovascular_risk(self, data):
        """
        Calculate cardiovascular end-organ damage risk
        """
        risk_score = 0.0
        
        # Age factor
        age = data.get('age', 50)
        if age > 65:
            risk_score += 0.3
        elif age > 55:
            risk_score += 0.2
        elif age > 45:
            risk_score += 0.1
        
        # Blood pressure control
        avg_systolic = data.get('avg_systolic_bp', 140)
        if avg_systolic > 160:
            risk_score += 0.4
        elif avg_systolic > 140:
            risk_score += 0.3
        elif avg_systolic > 130:
            risk_score += 0.2
        
        # Hypertension duration
        duration = data.get('hypertension_duration_years', 0)
        if duration > 10:
            risk_score += 0.3
        elif duration > 5:
            risk_score += 0.2
        elif duration > 2:
            risk_score += 0.1
        
        # Comorbidities
        if data.get('has_diabetes'):
            risk_score += 0.25
        if data.get('has_heart_disease'):
            risk_score += 0.3
        if data.get('smoking_history'):
            risk_score += 0.15
        
        # Cholesterol
        ldl = data.get('ldl_cholesterol', 130)
        if ldl > 160:
            risk_score += 0.2
        elif ldl > 130:
            risk_score += 0.1
        
        # BP variability
        bp_variability = data.get('bp_variability', 0)
        if bp_variability > 20:
            risk_score += 0.15
        elif bp_variability > 15:
            risk_score += 0.1
        
        return min(risk_score, 1.0)  # Cap at 1.0
    
    def calculate_renal_risk(self, data):
        """
        Calculate renal end-organ damage risk
        """
        risk_score = 0.0
        
        # Kidney function
        egfr = data.get('egfr', 90)
        if egfr < 30:
            risk_score += 0.5
        elif egfr < 60:
            risk_score += 0.3
        elif egfr < 90:
            risk_score += 0.1
        
        # Blood pressure control (kidneys are sensitive to BP)
        avg_systolic = data.get('avg_systolic_bp', 140)
        if avg_systolic > 150:
            risk_score += 0.3
        elif avg_systolic > 140:
            risk_score += 0.2
        
        # Diabetes (major risk factor for kidney disease)
        if data.get('has_diabetes'):
            risk_score += 0.35
            # HbA1c control
            hba1c = data.get('hba1c', 5.5)
            if hba1c > 8.0:
                risk_score += 0.2
            elif hba1c > 7.0:
                risk_score += 0.1
        
        # Existing kidney disease
        if data.get('has_kidney_disease'):
            risk_score += 0.4
        
        # Age
        age = data.get('age', 50)
        if age > 65:
            risk_score += 0.2
        elif age > 55:
            risk_score += 0.1
        
        # Hypertension duration
        duration = data.get('hypertension_duration_years', 0)
        if duration > 10:
            risk_score += 0.25
        elif duration > 5:
            risk_score += 0.15
        
        return min(risk_score, 1.0)
    
    def calculate_retinal_risk(self, data):
        """
        Calculate retinal end-organ damage risk
        """
        risk_score = 0.0
        
        # Blood pressure (retina is sensitive to BP changes)
        avg_systolic = data.get('avg_systolic_bp', 140)
        if avg_systolic > 160:
            risk_score += 0.35
        elif avg_systolic > 140:
            risk_score += 0.25
        elif avg_systolic > 130:
            risk_score += 0.15
        
        # Diabetes (major risk factor for retinopathy)
        if data.get('has_diabetes'):
            risk_score += 0.4
            hba1c = data.get('hba1c', 5.5)
            if hba1c > 8.0:
                risk_score += 0.25
            elif hba1c > 7.0:
                risk_score += 0.15
        
        # Hypertension duration
        duration = data.get('hypertension_duration_years', 0)
        if duration > 10:
            risk_score += 0.3
        elif duration > 5:
            risk_score += 0.2
        
        # Age
        age = data.get('age', 50)
        if age > 60:
            risk_score += 0.2
        elif age > 50:
            risk_score += 0.1
        
        # BP variability (important for retinal vessels)
        bp_variability = data.get('bp_variability', 0)
        if bp_variability > 20:
            risk_score += 0.2
        elif bp_variability > 15:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def calculate_cerebrovascular_risk(self, data):
        """
        Calculate cerebrovascular end-organ damage risk
        """
        risk_score = 0.0
        
        # Age (major factor for stroke risk)
        age = data.get('age', 50)
        if age > 75:
            risk_score += 0.4
        elif age > 65:
            risk_score += 0.3
        elif age > 55:
            risk_score += 0.2
        elif age > 45:
            risk_score += 0.1
        
        # Blood pressure
        avg_systolic = data.get('avg_systolic_bp', 140)
        if avg_systolic > 160:
            risk_score += 0.35
        elif avg_systolic > 140:
            risk_score += 0.25
        elif avg_systolic > 130:
            risk_score += 0.15
        
        # Comorbidities
        if data.get('has_diabetes'):
            risk_score += 0.2
        if data.get('has_heart_disease'):
            risk_score += 0.25
        if data.get('smoking_history'):
            risk_score += 0.2
        
        # Cholesterol
        total_cholesterol = data.get('total_cholesterol', 200)
        if total_cholesterol > 240:
            risk_score += 0.15
        elif total_cholesterol > 200:
            risk_score += 0.1
        
        # Hypertension duration
        duration = data.get('hypertension_duration_years', 0)
        if duration > 15:
            risk_score += 0.25
        elif duration > 10:
            risk_score += 0.15
        elif duration > 5:
            risk_score += 0.1
        
        return min(risk_score, 1.0)
    
    def calculate_overall_risk(self, organ_risks):
        """
        Calculate overall end-organ damage risk
        """
        # Weighted average of organ risks
        weights = {
            'cardiovascular': 0.3,
            'renal': 0.25,
            'retinal': 0.2,
            'cerebrovascular': 0.25
        }
        
        overall_risk = sum(
            organ_risks[organ] * weights[organ] 
            for organ in organ_risks
        )
        
        return min(overall_risk, 1.0)
    
    def get_risk_level(self, risk_score, organ):
        """
        Convert risk score to risk level
        """
        threshold = self.organ_thresholds.get(organ, 0.6)
        
        if risk_score >= threshold + 0.2:
            return 'Very High'
        elif risk_score >= threshold:
            return 'High'
        elif risk_score >= threshold - 0.2:
            return 'Moderate'
        elif risk_score >= threshold - 0.4:
            return 'Low'
        else:
            return 'Very Low'
    
    def get_overall_risk_level(self, risk_score):
        """
        Get overall risk level
        """
        if risk_score >= 0.8:
            return 'Very High'
        elif risk_score >= 0.6:
            return 'High'
        elif risk_score >= 0.4:
            return 'Moderate'
        elif risk_score >= 0.2:
            return 'Low'
        else:
            return 'Very Low'
    
    def generate_recommendations(self, patient_data, risk_scores):
        """
        Generate personalized recommendations based on risk assessment
        """
        recommendations = []
        
        # Overall risk-based recommendations
        overall_risk = risk_scores['overall']
        
        if overall_risk >= 0.7:
            recommendations.extend([
                "URGENT: Immediate medical evaluation required",
                "Consider referral to specialist (cardiologist, nephrologist)",
                "Intensive blood pressure management needed",
                "Monthly monitoring recommended"
            ])
        elif overall_risk >= 0.5:
            recommendations.extend([
                "Schedule appointment with healthcare provider within 2 weeks",
                "Optimize blood pressure control",
                "Consider additional medications",
                "Bi-weekly monitoring recommended"
            ])
        
        # Organ-specific recommendations
        if risk_scores['cardiovascular'] >= 0.6:
            recommendations.extend([
                "Cardiology consultation recommended",
                "Consider ECG and echocardiogram",
                "Optimize cholesterol management",
                "Cardiac stress test may be needed"
            ])
        
        if risk_scores['renal'] >= 0.6:
            recommendations.extend([
                "Nephrology consultation recommended",
                "Monitor kidney function (creatinine, eGFR)",
                "Consider ACE inhibitor or ARB",
                "Protein restriction may be needed"
            ])
        
        if risk_scores['retinal'] >= 0.5:
            recommendations.extend([
                "Ophthalmology examination recommended",
                "Annual dilated eye exam",
                "Optimize diabetes control if applicable",
                "Monitor for retinal changes"
            ])
        
        if risk_scores['cerebrovascular'] >= 0.6:
            recommendations.extend([
                "Neurology consultation may be needed",
                "Consider carotid ultrasound",
                "Optimize stroke prevention measures",
                "Consider antiplatelet therapy"
            ])
        
        # Lifestyle recommendations
        recommendations.extend([
            "Maintain healthy diet (DASH diet recommended)",
            "Regular physical activity (150 minutes/week)",
            "Weight management if overweight",
            "Stress management techniques",
            "Medication adherence is crucial",
            "Regular blood pressure monitoring"
        ])
        
        return recommendations
    
    def generate_risk_timeline(self, patient_data, years):
        """
        Generate risk progression timeline
        """
        timeline = []
        current_risk = self.calculate_overall_risk({
            'cardiovascular': self.calculate_cardiovascular_risk(patient_data),
            'renal': self.calculate_renal_risk(patient_data),
            'retinal': self.calculate_retinal_risk(patient_data),
            'cerebrovascular': self.calculate_cerebrovascular_risk(patient_data)
        })
        
        # Project risk over time (simplified model)
        for year in range(1, years + 1):
            # Risk increases with age and duration
            age_factor = 0.02 * year  # 2% increase per year due to aging
            duration_factor = 0.01 * year  # 1% increase per year due to disease duration
            
            projected_risk = min(current_risk + age_factor + duration_factor, 1.0)
            
            timeline.append({
                'year': year,
                'risk_score': projected_risk,
                'risk_level': self.get_overall_risk_level(projected_risk)
            })
        
        return timeline
    
    def calculate_confidence_score(self, patient_data):
        """
        Calculate confidence score for the prediction
        """
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        if patient_data.get('bp_readings_count', 0) > 10:
            confidence += 0.2
        elif patient_data.get('bp_readings_count', 0) > 5:
            confidence += 0.1
        
        # Recent lab data increases confidence
        if patient_data.get('creatinine') != 1.0:  # Has actual lab data
            confidence += 0.15
        
        # Medical history completeness
        if patient_data.get('hypertension_duration_years', 0) > 0:
            confidence += 0.1
        
        # Age data availability
        if patient_data.get('age') != 50:  # Not default value
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    # Helper methods
    def calculate_age(self, birth_date):
        """Calculate age from birth date"""
        if not birth_date:
            return 50  # Default age
        today = timezone.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def calculate_bp_variability(self, vitals):
        """Calculate blood pressure variability"""
        if len(vitals) < 2:
            return 0
        
        systolic_values = [v.systolic_bp for v in vitals]
        return np.std(systolic_values) if len(systolic_values) > 1 else 0
    
    def extract_lab_value(self, lab_tests, test_name, default_value):
        """Extract lab value from test results"""
        for lab in lab_tests:
            if test_name.lower() in lab.test_name.lower():
                try:
                    return float(lab.result_value)
                except (ValueError, AttributeError):
                    continue
        return default_value
    
    def get_default_prediction(self, patient):
        """Return default prediction when error occurs"""
        return {
            'patient': patient,
            'prediction_date': timezone.now(),
            'error': 'Unable to generate prediction due to insufficient data',
            'organ_risks': {
                'cardiovascular': {'risk_score': 0.3, 'risk_level': 'Moderate'},
                'renal': {'risk_score': 0.3, 'risk_level': 'Moderate'},
                'retinal': {'risk_score': 0.3, 'risk_level': 'Moderate'},
                'cerebrovascular': {'risk_score': 0.3, 'risk_level': 'Moderate'}
            },
            'overall_risk': {'risk_score': 0.3, 'risk_level': 'Moderate'},
            'recommendations': ['Regular medical follow-up recommended'],
            'confidence_score': 0.2
        }
    
    # Description methods
    def get_cardiovascular_description(self, risk_score):
        """Get cardiovascular risk description"""
        if risk_score >= 0.8:
            return "Very high risk of heart attack, heart failure, or other cardiovascular events"
        elif risk_score >= 0.6:
            return "High risk of cardiovascular complications"
        elif risk_score >= 0.4:
            return "Moderate risk of cardiovascular issues"
        else:
            return "Low risk of cardiovascular complications"
    
    def get_renal_description(self, risk_score):
        """Get renal risk description"""
        if risk_score >= 0.8:
            return "Very high risk of kidney failure or chronic kidney disease progression"
        elif risk_score >= 0.6:
            return "High risk of kidney damage"
        elif risk_score >= 0.4:
            return "Moderate risk of kidney complications"
        else:
            return "Low risk of kidney damage"
    
    def get_retinal_description(self, risk_score):
        """Get retinal risk description"""
        if risk_score >= 0.8:
            return "Very high risk of severe retinopathy or vision loss"
        elif risk_score >= 0.6:
            return "High risk of retinal damage"
        elif risk_score >= 0.4:
            return "Moderate risk of retinal complications"
        else:
            return "Low risk of retinal damage"
    
    def get_cerebrovascular_description(self, risk_score):
        """Get cerebrovascular risk description"""
        if risk_score >= 0.8:
            return "Very high risk of stroke or other cerebrovascular events"
        elif risk_score >= 0.6:
            return "High risk of stroke"
        elif risk_score >= 0.4:
            return "Moderate risk of cerebrovascular complications"
        else:
            return "Low risk of stroke or cerebrovascular events"
    
    def get_overall_description(self, risk_score):
        """Get overall risk description"""
        if risk_score >= 0.8:
            return "Very high overall risk of end-organ damage requiring immediate intervention"
        elif risk_score >= 0.6:
            return "High overall risk of end-organ damage"
        elif risk_score >= 0.4:
            return "Moderate overall risk of end-organ damage"
        else:
            return "Low overall risk of end-organ damage"


class PredictionHistory(models.Model):
    """
    Store AI prediction history for tracking and analysis
    """
    patient = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_predictions',
        limit_choices_to={'user_type': 'patient'}
    )
    
    prediction_data = models.JSONField()
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_predictions',
        limit_choices_to={'user_type__in': ['doctor', 'admin']}
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'AI Prediction History'
        verbose_name_plural = 'AI Prediction Histories'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Prediction for {self.patient} - {self.created_at.strftime('%Y-%m-%d')}"


def generate_end_organ_damage_prediction(patient, user=None):
    """
    Generate and save end-organ damage prediction
    """
    predictor = EndOrganDamagePredictor()
    prediction = predictor.predict_end_organ_damage(patient)
    
    # Save prediction history
    PredictionHistory.objects.create(
        patient=patient,
        prediction_data=prediction,
        created_by=user
    )
    
    return prediction


def get_patient_risk_trends(patient, months=12):
    """
    Get risk trends for a patient over time
    """
    end_date = timezone.now()
    start_date = end_date - timedelta(days=months * 30)
    
    predictions = PredictionHistory.objects.filter(
        patient=patient,
        created_at__range=[start_date, end_date]
    ).order_by('created_at')
    
    trends = []
    for prediction in predictions:
        data = prediction.prediction_data
        trends.append({
            'date': prediction.created_at,
            'overall_risk': data.get('overall_risk', {}).get('risk_score', 0),
            'cardiovascular_risk': data.get('organ_risks', {}).get('cardiovascular', {}).get('risk_score', 0),
            'renal_risk': data.get('organ_risks', {}).get('renal', {}).get('risk_score', 0),
            'retinal_risk': data.get('organ_risks', {}).get('retinal', {}).get('risk_score', 0),
            'cerebrovascular_risk': data.get('organ_risks', {}).get('cerebrovascular', {}).get('risk_score', 0)
        })
    
    return trends