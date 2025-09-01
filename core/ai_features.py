"""
AI-Powered Features for Laso Healthcare
"""
import re
from datetime import datetime, timedelta
from django.db.models import Q, Count
from django.utils import timezone
from collections import Counter
import json

from treatments.models import Treatment, Prescription
from treatments.models_lab import LabTest
from treatments.models_medical_history import MedicalHistory
from treatments.models_medications import Medication, MedicationInteraction
from appointments.models import Appointment
from django.contrib.auth import get_user_model

User = get_user_model()


class SymptomAnalyzer:
    """
    Symptom analysis and recommendations
    """
    
    # Symptom-disease matching database (simple example)
    SYMPTOM_DISEASE_MAP = {
        'fever': ['flu', 'infection', 'covid-19', 'bronchitis'],
        'cough': ['flu', 'bronchitis', 'asthma', 'covid-19'],
        'shortness of breath': ['asthma', 'covid-19', 'heart disease', 'lung disease'],
        'chest pain': ['heart disease', 'lung disease', 'muscle pain'],
        'headache': ['migraine', 'sinusitis', 'tension', 'hypertension'],
        'abdominal pain': ['gastritis', 'ulcer', 'appendicitis', 'gallstone'],
        'nausea': ['gastritis', 'pregnancy', 'migraine', 'food poisoning'],
        'vomiting': ['gastritis', 'food poisoning', 'migraine', 'appendicitis'],
        'diarrhea': ['gastroenteritis', 'food poisoning', 'ibs', 'infection'],
        'fatigue': ['anemia', 'depression', 'thyroid disease', 'diabetes'],
        'weight loss': ['diabetes', 'hyperthyroidism', 'cancer', 'depression'],
        'weight gain': ['hypothyroidism', 'diabetes', 'hormonal disorder'],
        'joint pain': ['arthritis', 'rheumatism', 'gout', 'fibromyalgia'],
        'skin rash': ['allergy', 'eczema', 'dermatitis', 'fungal infection'],
        'insomnia': ['anxiety', 'depression', 'stress', 'sleep apnea']
    }
    
    def analyze_symptoms(self, symptoms_text):
        """
        Analyzes symptom text to suggest possible diseases
        """
        if not symptoms_text:
            return []
        
        symptoms_text = symptoms_text.lower()
        found_symptoms = []
        possible_diseases = []
        
        # Find symptoms
        for symptom, diseases in self.SYMPTOM_DISEASE_MAP.items():
            if symptom in symptoms_text:
                found_symptoms.append(symptom)
                possible_diseases.extend(diseases)
        
        # Count the most common diseases
        disease_counts = Counter(possible_diseases)
        top_diseases = disease_counts.most_common(5)
        
        return {
            'found_symptoms': found_symptoms,
            'possible_diseases': [{'disease': disease, 'confidence': count} for disease, count in top_diseases],
            'recommendations': self.get_general_recommendations(found_symptoms)
        }
    
    def get_general_recommendations(self, symptoms):
        """
        General recommendations based on symptoms
        """
        recommendations = []
        
        if 'fever' in symptoms:
            recommendations.append('Drink plenty of fluids and rest')
            recommendations.append('Consult a doctor if fever is above 38.5°C')
        
        if 'cough' in symptoms:
            recommendations.append('Humidify the air')
            recommendations.append('A doctor check-up is necessary if the cough lasts longer than 2 weeks')
        
        if 'shortness of breath' in symptoms:
            recommendations.append('Seek immediate medical attention - it could be an emergency')
        
        if 'chest pain' in symptoms:
            recommendations.append('Go to the emergency room')
        
        if not recommendations:
            recommendations.append('A doctor check-up is recommended if symptoms persist')
        
        return recommendations


class DrugInteractionChecker:
    """
    Medication interaction check
    """
    
    def check_prescription_interactions(self, prescription_list):
        """
        Check for interactions between prescribed drugs
        """
        interactions = []
        
        # Check for interactions for each pair of drugs
        for i, med1 in enumerate(prescription_list):
            for med2 in prescription_list[i+1:]:
                interaction = self.check_drug_pair(med1, med2)
                if interaction:
                    interactions.append(interaction)
        
        return interactions
    
    def check_drug_pair(self, medication1, medication2):
        """
        Check for interaction between two drugs
        """
        try:
            # Search for interaction in the database
            interaction = MedicationInteraction.objects.filter(
                Q(medication1__name__icontains=medication1) & Q(medication2__name__icontains=medication2) |
                Q(medication1__name__icontains=medication2) & Q(medication2__name__icontains=medication1)
            ).first()
            
            if interaction:
                return {
                    'medication1': medication1,
                    'medication2': medication2,
                    'severity': interaction.severity,
                    'description': interaction.description,
                    'recommendations': interaction.recommendations
                }
        except Exception:
            pass
        
        return None
    
    def check_patient_drug_history(self, patient, new_medication):
        """
        Interaction between patient's current medications and new medication
        """
        # Get the patient's active medications
        current_medications = MedicalHistory.objects.filter(
            patient=patient,
            condition_type='medication',
            is_active=True
        ).values_list('condition_name', flat=True)
        
        interactions = []
        for current_med in current_medications:
            interaction = self.check_drug_pair(current_med, new_medication)
            if interaction:
                interactions.append(interaction)
        
        return interactions


class TreatmentRecommendationEngine:
    """
    Treatment recommendation engine
    """
    
    def get_similar_cases(self, patient_symptoms, patient_age=None, patient_gender=None, limit=5):
        """
        Finding similar cases
        """
        # Symptom analysis
        analyzer = SymptomAnalyzer()
        analysis = analyzer.analyze_symptoms(patient_symptoms)
        
        if not analysis['possible_diseases']:
            return []
        
        # Find similar treatments based on the most likely disease
        top_disease = analysis['possible_diseases'][0]['disease']
        
        similar_treatments = Treatment.objects.filter(
            diagnosis__icontains=top_disease
        ).select_related('appointment__patient').prefetch_related('prescriptions')[:limit]
        
        recommendations = []
        for treatment in similar_treatments:
            recommendations.append({
                'diagnosis': treatment.diagnosis,
                'patient_age': self.calculate_age(treatment.appointment.patient.date_of_birth) if hasattr(treatment.appointment.patient, 'date_of_birth') else None,
                'prescriptions': [
                    {
                        'name': p.name,
                        'dosage': p.dosage,
                        'instructions': p.instructions
                    } for p in treatment.prescriptions.all()
                ],
                'notes': treatment.notes,
                'success_rate': self.calculate_treatment_success_rate(treatment)
            })
        
        return recommendations
    
    def calculate_age(self, birth_date):
        """Calculate age"""
        if not birth_date:
            return None
        today = timezone.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def calculate_treatment_success_rate(self, treatment):
        """Calculate treatment success rate (placeholder)"""
        # This can be improved with real data
        return 85  # Default 85% success rate
    
    def recommend_lab_tests(self, symptoms, patient_history=None):
        """
        Recommend lab tests based on symptoms
        """
        test_recommendations = []
        
        symptoms_lower = symptoms.lower()
        
        # Symptom-test matching
        if any(word in symptoms_lower for word in ['fever', 'infection', 'fatigue']):
            test_recommendations.extend([
                'Complete Blood Count (CBC)',
                'C-Reactive Protein (CRP)',
                'Sedimentation Rate (ESR)'
            ])
        
        if any(word in symptoms_lower for word in ['chest pain', 'shortness of breath']):
            test_recommendations.extend([
                'ECG',
                'Chest X-Ray',
                'Troponin T/I'
            ])
        
        if any(word in symptoms_lower for word in ['abdominal pain', 'nausea', 'vomiting']):
            test_recommendations.extend([
                'Liver Function Tests',
                'Pancreatic Enzymes',
                'Abdominal Ultrasound'
            ])
        
        if any(word in symptoms_lower for word in ['fatigue', 'weight', 'sweating']):
            test_recommendations.extend([
                'Thyroid Function Tests',
                'HbA1c (Sugar)',
                'Vitamin B12, D'
            ])
        
        return list(set(test_recommendations))  # Remove duplicates


class PatientRiskAssessment:
    """
    Patient risk assessment
    """
    
    def assess_patient_risk(self, patient):
        """
        Patient's overall risk assessment
        """
        risk_factors = []
        risk_score = 0
        
        # Age risk factor
        age = self.calculate_age(getattr(patient, 'date_of_birth', None))
        if age:
            if age > 65:
                risk_factors.append('Age over 65')
                risk_score += 3
            elif age > 50:
                risk_factors.append('Age between 50-65')
                risk_score += 2
        
        # Chronic disease risk factors
        chronic_conditions = MedicalHistory.objects.filter(
            patient=patient,
            condition_type='chronic',
            is_active=True
        )
        
        high_risk_conditions = ['diabetes', 'hypertension', 'heart disease', 'copd', 'asthma']
        for condition in chronic_conditions:
            condition_name = condition.condition_name.lower()
            if any(hrc in condition_name for hrc in high_risk_conditions):
                risk_factors.append(f'Chronic disease: {condition.condition_name}')
                risk_score += 2
        
        # Allergy risk factors
        allergies = MedicalHistory.objects.filter(
            patient=patient,
            condition_type='allergy',
            is_active=True
        ).count()
        
        if allergies > 0:
            risk_factors.append(f'{allergies} active allergies')
            risk_score += 1
        
        # Determining the risk level
        if risk_score >= 6:
            risk_level = 'High'
            color = 'danger'
        elif risk_score >= 3:
            risk_level = 'Medium'
            color = 'warning'
        else:
            risk_level = 'Low'
            color = 'success'
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'risk_color': color,
            'risk_factors': risk_factors,
            'recommendations': self.get_risk_recommendations(risk_level, risk_factors)
        }
    
    def calculate_age(self, birth_date):
        """Calculate age"""
        if not birth_date:
            return None
        today = timezone.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def get_risk_recommendations(self, risk_level, risk_factors):
        """
        Recommendations based on risk level
        """
        recommendations = []
        
        if risk_level == 'High':
            recommendations.extend([
                'Regular doctor check-ups (every 3 months)',
                'Prepare an emergency plan',
                'Pay attention to medication compliance',
                'Make lifestyle changes'
            ])
        elif risk_level == 'Medium':
            recommendations.extend([
                'Regular check-ups (every 6 months)',
                'Healthy nutrition program',
                'Exercise regularly'
            ])
        else:
            recommendations.extend([
                'Annual check-ups are sufficient',
                'Maintain a healthy lifestyle',
                'Focus on preventive care'
            ])
        
        return recommendations


class AIHealthInsights:
    """
    AI-powered health insights
    """
    
    def __init__(self):
        self.symptom_analyzer = SymptomAnalyzer()
        self.drug_checker = DrugInteractionChecker()
        self.treatment_engine = TreatmentRecommendationEngine()
        self.risk_assessor = PatientRiskAssessment()
    
    def generate_patient_insights(self, patient):
        """
        Comprehensive AI analysis for patient
        """
        insights = {
            'patient': patient,
            'risk_assessment': self.risk_assessor.assess_patient_risk(patient),
            'recent_treatments': self.analyze_recent_treatments(patient),
            'medication_reminders': self.get_medication_reminders(patient),
            'upcoming_care_suggestions': self.suggest_upcoming_care(patient)
        }
        
        return insights
    
    def analyze_recent_treatments(self, patient):
        """
        Analyze recent treatments
        """
        recent_treatments = Treatment.objects.filter(
            appointment__patient=patient
        ).order_by('-created_at')[:5]
        
        analysis = {
            'total_treatments': recent_treatments.count(),
            'common_diagnoses': [],
            'treatment_patterns': [],
            'suggestions': []
        }
        
        if recent_treatments:
            # Most common diagnoses
            diagnoses = [t.diagnosis for t in recent_treatments]
            diagnosis_counts = Counter(diagnoses)
            analysis['common_diagnoses'] = diagnosis_counts.most_common(3)
            
            # Treatment patterns
            if len(recent_treatments) >= 3:
                analysis['treatment_patterns'].append('Shows regular follow-up')
            
            # Suggestions
            if diagnosis_counts.most_common(1)[0][1] > 1:
                analysis['suggestions'].append('Consider preventive treatment for recurrent complaint')
        
        return analysis
    
    def get_medication_reminders(self, patient):
        """
        Medication reminders
        """
        active_medications = MedicalHistory.objects.filter(
            patient=patient,
            condition_type='medication',
            is_active=True
        )
        
        reminders = []
        for med in active_medications:
            reminders.append({
                'medication': med.condition_name,
                'start_date': med.diagnosed_date,
                'notes': med.notes,
                'duration_days': (timezone.now().date() - med.diagnosed_date).days if med.diagnosed_date else 0
            })
        
        return reminders
    
    def suggest_upcoming_care(self, patient):
        """
        Future care recommendations
        """
        suggestions = []
        
        # Last appointment date
        last_appointment = Appointment.objects.filter(
            patient=patient,
            status='completed'
        ).order_by('-date').first()
        
        if last_appointment:
            days_since_last = (timezone.now().date() - last_appointment.date).days
            
            if days_since_last > 365:
                suggestions.append({
                    'type': 'General Check-up',
                    'urgency': 'High',
                    'description': 'Time for annual general check-up'
                })
            elif days_since_last > 180:
                suggestions.append({
                    'type': 'Follow-up Appointment',
                    'urgency': 'Medium',
                    'description': 'Six-month follow-up check'
                })
        
        # Chronic disease follow-up
        chronic_conditions = MedicalHistory.objects.filter(
            patient=patient,
            condition_type='chronic',
            is_active=True
        )
        
        for condition in chronic_conditions:
            suggestions.append({
                'type': 'Chronic Disease Follow-up',
                'urgency': 'Medium',
                'description': f'Check-up for {condition.condition_name}'
            })
        
        return suggestions
