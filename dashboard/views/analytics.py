from django.shortcuts import render
from django.views.generic import TemplateView
from django.db.models import Count, Sum, Avg, F, Q, Case, When, Value, IntegerField
from django.db.models.functions import TruncMonth, TruncDay, TruncWeek, TruncYear, ExtractHour
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder
from datetime import timedelta, datetime
import json
import random

from accounts.decorators import AdminRequiredMixin
from accounts.models import User, Profile
from bookings.models import Booking, Prescription
from core.models import Speciality, Review
from vitals.models import VitalRecord, VitalCategory


class HospitalAnalyticsView(AdminRequiredMixin, TemplateView):
    """
    Comprehensive hospital analytics dashboard
    """
    template_name = 'dashboard/analytics/hospital_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from query params or default to last 30 days
        end_date = timezone.now().date()
        start_date = self.request.GET.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
        
        end_date_param = self.request.GET.get('end_date')
        if end_date_param:
            try:
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # Get all data for the selected date range
        bookings = Booking.objects.filter(
            appointment_date__range=[start_date, end_date]
        ).select_related('doctor', 'patient', 'doctor__profile')
        
        prescriptions = Prescription.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).select_related('doctor', 'patient')
        
        reviews = Review.objects.filter(
            created_at__date__range=[start_date, end_date]
        ).select_related('doctor', 'patient')
        
        vital_records = VitalRecord.objects.filter(
            recorded_at__date__range=[start_date, end_date]
        ).select_related('patient', 'category')
        
        # 1. Patient Demographics
        patients = User.objects.filter(role='patient').select_related('profile')
        
        # Age distribution
        age_groups = {
            '0-17': 0,
            '18-24': 0,
            '25-34': 0,
            '35-44': 0,
            '45-54': 0,
            '55-64': 0,
            '65+': 0,
            'Unknown': 0
        }
        
        gender_distribution = {
            'Male': 0,
            'Female': 0,
            'Other': 0,
            'Unknown': 0
        }
        
        for patient in patients:
            if patient.profile.dob:
                today = timezone.now().date()
                age = today.year - patient.profile.dob.year - (
                    (today.month, today.day) < (patient.profile.dob.month, patient.profile.dob.day)
                )
                
                if age < 18:
                    age_groups['0-17'] += 1
                elif age < 25:
                    age_groups['18-24'] += 1
                elif age < 35:
                    age_groups['25-34'] += 1
                elif age < 45:
                    age_groups['35-44'] += 1
                elif age < 55:
                    age_groups['45-54'] += 1
                elif age < 65:
                    age_groups['55-64'] += 1
                else:
                    age_groups['65+'] += 1
            else:
                age_groups['Unknown'] += 1
            
            if patient.profile.gender:
                if patient.profile.gender.lower() == 'male':
                    gender_distribution['Male'] += 1
                elif patient.profile.gender.lower() == 'female':
                    gender_distribution['Female'] += 1
                else:
                    gender_distribution['Other'] += 1
            else:
                gender_distribution['Unknown'] += 1
        
        context['age_distribution'] = json.dumps({
            'labels': list(age_groups.keys()),
            'data': list(age_groups.values())
        })
        
        context['gender_distribution'] = json.dumps({
            'labels': list(gender_distribution.keys()),
            'data': list(gender_distribution.values())
        })
        
        # 2. Appointment Analytics
        # Appointment status distribution
        status_counts = bookings.values('status').annotate(count=Count('id')).order_by('status')
        status_data = {item['status']: item['count'] for item in status_counts}
        
        context['appointment_status'] = json.dumps({
            'labels': list(status_data.keys()),
            'data': list(status_data.values())
        })
        
        # Appointment trend by month
        monthly_appointments = list(
            bookings.annotate(month=TruncMonth('appointment_date'))
            .values('month')
            .annotate(count=Count('id'))
            .order_by('month')
        )
        
        # Format dates for JSON
        for item in monthly_appointments:
            item['month'] = item['month'].strftime('%Y-%m-%d')
        
        context['monthly_appointments'] = json.dumps(monthly_appointments)
        
        # Appointment distribution by day of week
        weekday_appointments = list(
            bookings.annotate(
                weekday=F('appointment_date__week_day')
            ).values('weekday').annotate(count=Count('id')).order_by('weekday')
        )
        
        # Convert Django's day of week (1=Sunday, 7=Saturday) to standard (0=Monday, 6=Sunday)
        weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        weekday_data = [0] * 7
        
        for item in weekday_appointments:
            # Convert Django's day of week to standard
            day_idx = (item['weekday'] % 7) - 1
            if day_idx == -1:
                day_idx = 6  # Sunday
            weekday_data[day_idx] = item['count']
        
        context['weekday_appointments'] = json.dumps({
            'labels': weekday_names,
            'data': weekday_data
        })
        
        # 3. Revenue Analytics
        # Total revenue
        total_revenue = bookings.filter(status='completed').aggregate(
            total=Sum('doctor__profile__price_per_consultation')
        )['total'] or 0
        
        context['total_revenue'] = total_revenue
        
        # Revenue by speciality
        revenue_by_speciality = list(
            bookings.filter(status='completed')
            .values('doctor__profile__specialization__name')
            .annotate(revenue=Sum('doctor__profile__price_per_consultation'))
            .order_by('-revenue')
        )
        
        context['revenue_by_speciality'] = json.dumps(revenue_by_speciality)
        
        # Monthly revenue trend
        monthly_revenue = list(
            bookings.filter(status='completed')
            .annotate(month=TruncMonth('appointment_date'))
            .values('month')
            .annotate(revenue=Sum('doctor__profile__price_per_consultation'))
            .order_by('month')
        )
        
        # Format dates and convert Decimal to float for JSON
        for item in monthly_revenue:
            item['month'] = item['month'].strftime('%Y-%m-%d')
            item['revenue'] = float(item['revenue']) if item['revenue'] else 0
        
        context['monthly_revenue'] = json.dumps(monthly_revenue)
        
        # 4. Doctor Performance
        # Top performing doctors
        top_doctors = list(
            bookings.filter(status='completed')
            .values('doctor__first_name', 'doctor__last_name', 'doctor__id')
            .annotate(
                appointments=Count('id'),
                revenue=Sum('doctor__profile__price_per_consultation'),
                avg_rating=Avg('doctor__reviews_received__rating')
            )
            .order_by('-appointments')[:10]
        )
        
        context['top_doctors'] = top_doctors
        
        # Doctor utilization rate
        doctor_count = User.objects.filter(role='doctor').count()
        active_doctors = bookings.values('doctor').distinct().count()
        
        if doctor_count > 0:
            utilization_rate = (active_doctors / doctor_count) * 100
        else:
            utilization_rate = 0
        
        context['doctor_utilization'] = round(utilization_rate, 2)
        
        # 5. Patient Health Metrics
        # Vital signs trends
        vital_categories = VitalCategory.objects.all()
        vital_trends = {}
        
        for category in vital_categories:
            records = vital_records.filter(category=category).order_by('recorded_at')
            if records.exists():
                data_points = list(
                    records.annotate(month=TruncMonth('recorded_at'))
                    .values('month')
                    .annotate(avg_value=Avg('value'))
                    .order_by('month')
                )
                
                # Format dates for JSON
                for point in data_points:
                    point['month'] = point['month'].strftime('%Y-%m-%d')
                
                vital_trends[category.name] = {
                    'data': data_points,
                    'unit': category.unit,
                    'color': category.color or '#007bff'
                }
        
        context['vital_trends'] = json.dumps(vital_trends)
        
        # Abnormal vitals count
        abnormal_vitals = vital_records.exclude(status='normal').count()
        total_vitals = vital_records.count()
        
        if total_vitals > 0:
            abnormal_rate = (abnormal_vitals / total_vitals) * 100
        else:
            abnormal_rate = 0
        
        context['abnormal_vitals_rate'] = round(abnormal_rate, 2)
        
        # 6. Prescription Analytics
        # Prescription count by doctor
        prescription_by_doctor = list(
            prescriptions.values('doctor__first_name', 'doctor__last_name')
            .annotate(count=Count('id'))
            .order_by('-count')[:10]
        )
        
        context['prescription_by_doctor'] = prescription_by_doctor
        
        # 7. Operational Metrics
        # Average wait time (simulated for demo)
        avg_wait_time = random.randint(15, 45)  # minutes
        context['avg_wait_time'] = avg_wait_time
        
        # No-show rate
        no_shows = bookings.filter(status='no_show').count()
        total_appointments = bookings.count()
        
        if total_appointments > 0:
            no_show_rate = (no_shows / total_appointments) * 100
        else:
            no_show_rate = 0
        
        context['no_show_rate'] = round(no_show_rate, 2)
        
        # 8. Patient Satisfaction
        # Average rating
        avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
        context['avg_rating'] = round(avg_rating, 2)
        
        # Rating distribution
        rating_distribution = list(
            reviews.values('rating')
            .annotate(count=Count('id'))
            .order_by('rating')
        )
        
        # Fill in missing ratings
        rating_data = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for item in rating_distribution:
            rating_data[item['rating']] = item['count']
        
        context['rating_distribution'] = json.dumps({
            'labels': list(rating_data.keys()),
            'data': list(rating_data.values())
        })
        
        return context


class DoctorAnalyticsView(AdminRequiredMixin, TemplateView):
    """
    Doctor performance analytics
    """
    template_name = 'dashboard/analytics/doctor_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from query params or default to last 30 days
        end_date = timezone.now().date()
        start_date = self.request.GET.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
        
        end_date_param = self.request.GET.get('end_date')
        if end_date_param:
            try:
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # Get doctor ID from URL parameter
        doctor_id = self.kwargs.get('doctor_id')
        
        if doctor_id:
            doctor = User.objects.filter(id=doctor_id, role='doctor').select_related('profile').first()
            
            if doctor:
                context['doctor'] = doctor
                
                # Get all bookings for this doctor
                bookings = Booking.objects.filter(
                    doctor=doctor,
                    appointment_date__range=[start_date, end_date]
                ).select_related('patient')
                
                # Get all reviews for this doctor
                reviews = Review.objects.filter(
                    doctor=doctor,
                    created_at__date__range=[start_date, end_date]
                ).select_related('patient')
                
                # Get all prescriptions by this doctor
                prescriptions = Prescription.objects.filter(
                    doctor=doctor,
                    created_at__date__range=[start_date, end_date]
                ).select_related('patient')
                
                # 1. Appointment Statistics
                # Appointment status distribution
                status_counts = bookings.values('status').annotate(count=Count('id')).order_by('status')
                status_data = {item['status']: item['count'] for item in status_counts}
                
                context['appointment_status'] = json.dumps({
                    'labels': list(status_data.keys()),
                    'data': list(status_data.values())
                })
                
                # Appointment trend by day
                daily_appointments = list(
                    bookings.annotate(day=TruncDay('appointment_date'))
                    .values('day')
                    .annotate(count=Count('id'))
                    .order_by('day')
                )
                
                # Format dates for JSON
                for item in daily_appointments:
                    item['day'] = item['day'].strftime('%Y-%m-%d')
                
                context['daily_appointments'] = json.dumps(daily_appointments)
                
                # 2. Revenue Statistics
                # Total revenue
                total_revenue = bookings.filter(status='completed').aggregate(
                    total=Sum('doctor__profile__price_per_consultation')
                )['total'] or 0
                
                context['total_revenue'] = total_revenue
                
                # Daily revenue
                daily_revenue = list(
                    bookings.filter(status='completed')
                    .annotate(day=TruncDay('appointment_date'))
                    .values('day')
                    .annotate(revenue=Sum('doctor__profile__price_per_consultation'))
                    .order_by('day')
                )
                
                # Format dates and convert Decimal to float for JSON
                for item in daily_revenue:
                    item['day'] = item['day'].strftime('%Y-%m-%d')
                    item['revenue'] = float(item['revenue']) if item['revenue'] else 0
                
                context['daily_revenue'] = json.dumps(daily_revenue)
                
                # 3. Patient Demographics
                # Unique patients
                unique_patients = bookings.values('patient').distinct().count()
                context['unique_patients'] = unique_patients
                
                # Returning patients (patients with more than one appointment)
                returning_patients = bookings.values('patient').annotate(
                    count=Count('id')
                ).filter(count__gt=1).count()
                
                context['returning_patients'] = returning_patients
                
                # 4. Performance Metrics
                # Average rating
                avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
                context['avg_rating'] = round(avg_rating, 2)
                
                # Rating distribution
                rating_distribution = list(
                    reviews.values('rating')
                    .annotate(count=Count('id'))
                    .order_by('rating')
                )
                
                # Fill in missing ratings
                rating_data = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for item in rating_distribution:
                    rating_data[item['rating']] = item['count']
                
                context['rating_distribution'] = json.dumps({
                    'labels': list(rating_data.keys()),
                    'data': list(rating_data.values())
                })
                
                # Completion rate
                completed = bookings.filter(status='completed').count()
                total = bookings.count()
                
                if total > 0:
                    completion_rate = (completed / total) * 100
                else:
                    completion_rate = 0
                
                context['completion_rate'] = round(completion_rate, 2)
                
                # 5. Prescription Analytics
                # Prescription count
                context['prescription_count'] = prescriptions.count()
                
                # Prescriptions per appointment
                if completed > 0:
                    prescriptions_per_appointment = prescriptions.count() / completed
                else:
                    prescriptions_per_appointment = 0
                
                context['prescriptions_per_appointment'] = round(prescriptions_per_appointment, 2)
                
                # 6. Time Efficiency
                # Average appointment duration (simulated for demo)
                avg_duration = random.randint(15, 45)  # minutes
                context['avg_appointment_duration'] = avg_duration
                
                # 7. Comparison with other doctors
                # Get average metrics for all doctors
                all_doctors_avg_rating = Review.objects.filter(
                    created_at__date__range=[start_date, end_date]
                ).aggregate(avg=Avg('rating'))['avg'] or 0
                
                all_doctors_completion_rate = Booking.objects.filter(
                    appointment_date__range=[start_date, end_date]
                ).aggregate(
                    completed=Count('id', filter=Q(status='completed')),
                    total=Count('id')
                )
                
                if all_doctors_completion_rate['total'] > 0:
                    all_doctors_completion_rate_value = (all_doctors_completion_rate['completed'] / all_doctors_completion_rate['total']) * 100
                else:
                    all_doctors_completion_rate_value = 0
                
                context['comparison'] = {
                    'rating': {
                        'doctor': round(avg_rating, 2),
                        'average': round(all_doctors_avg_rating, 2),
                        'difference': round(avg_rating - all_doctors_avg_rating, 2)
                    },
                    'completion_rate': {
                        'doctor': round(completion_rate, 2),
                        'average': round(all_doctors_completion_rate_value, 2),
                        'difference': round(completion_rate - all_doctors_completion_rate_value, 2)
                    }
                }
                
                # 8. Recent Activity
                context['recent_appointments'] = bookings.order_by('-appointment_date')[:10]
                context['recent_reviews'] = reviews.order_by('-created_at')[:10]
                context['recent_prescriptions'] = prescriptions.order_by('-created_at')[:10]
            
        # Get all doctors for the dropdown
        context['all_doctors'] = User.objects.filter(role='doctor').order_by('first_name', 'last_name')
        
        return context


class PatientAnalyticsView(AdminRequiredMixin, TemplateView):
    """
    Patient analytics dashboard
    """
    template_name = 'dashboard/analytics/patient_analytics.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get date range from query params or default to last 30 days
        end_date = timezone.now().date()
        start_date = self.request.GET.get('start_date')
        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
            except ValueError:
                start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=30)
        
        end_date_param = self.request.GET.get('end_date')
        if end_date_param:
            try:
                end_date = datetime.strptime(end_date_param, '%Y-%m-%d').date()
            except ValueError:
                pass
        
        context['start_date'] = start_date
        context['end_date'] = end_date
        
        # Get patient ID from URL parameter
        patient_id = self.kwargs.get('patient_id')
        
        if patient_id:
            patient = User.objects.filter(id=patient_id, role='patient').select_related('profile').first()
            
            if patient:
                context['patient'] = patient
                
                # Get all bookings for this patient
                bookings = Booking.objects.filter(
                    patient=patient,
                    appointment_date__range=[start_date, end_date]
                ).select_related('doctor')
                
                # Get all reviews by this patient
                reviews = Review.objects.filter(
                    patient=patient,
                    created_at__date__range=[start_date, end_date]
                ).select_related('doctor')
                
                # Get all prescriptions for this patient
                prescriptions = Prescription.objects.filter(
                    patient=patient,
                    created_at__date__range=[start_date, end_date]
                ).select_related('doctor')
                
                # Get all vital records for this patient
                vital_records = VitalRecord.objects.filter(
                    patient=patient,
                    recorded_at__date__range=[start_date, end_date]
                ).select_related('category')
                
                # 1. Appointment Statistics
                # Appointment status distribution
                status_counts = bookings.values('status').annotate(count=Count('id')).order_by('status')
                status_data = {item['status']: item['count'] for item in status_counts}
                
                context['appointment_status'] = json.dumps({
                    'labels': list(status_data.keys()),
                    'data': list(status_data.values())
                })
                
                # Appointment trend by month
                monthly_appointments = list(
                    bookings.annotate(month=TruncMonth('appointment_date'))
                    .values('month')
                    .annotate(count=Count('id'))
                    .order_by('month')
                )
                
                # Format dates for JSON
                for item in monthly_appointments:
                    item['month'] = item['month'].strftime('%Y-%m-%d')
                
                context['monthly_appointments'] = json.dumps(monthly_appointments)
                
                # 2. Health Metrics
                # Vital signs trends
                vital_categories = VitalCategory.objects.all()
                vital_trends = {}
                
                for category in vital_categories:
                    records = vital_records.filter(category=category).order_by('recorded_at')
                    if records.exists():
                        data_points = []
                        for record in records:
                            data_points.append({
                                'date': record.recorded_at.strftime('%Y-%m-%d'),
                                'value': float(record.value),
                                'status': record.status
                            })
                        
                        vital_trends[category.name] = {
                            'data': data_points,
                            'unit': category.unit,
                            'color': category.color or '#007bff'
                        }
                
                context['vital_trends'] = json.dumps(vital_trends)
                
                # Abnormal vitals count
                abnormal_vitals = vital_records.exclude(status='normal').count()
                total_vitals = vital_records.count()
                
                if total_vitals > 0:
                    abnormal_rate = (abnormal_vitals / total_vitals) * 100
                else:
                    abnormal_rate = 0
                
                context['abnormal_vitals_rate'] = round(abnormal_rate, 2)
                
                # 3. Doctor Visits
                # Doctors visited
                doctors_visited = bookings.values('doctor').distinct().count()
                context['doctors_visited'] = doctors_visited
                
                # Most visited doctor
                most_visited = bookings.values(
                    'doctor__first_name', 'doctor__last_name', 'doctor__id'
                ).annotate(
                    count=Count('id')
                ).order_by('-count').first()
                
                context['most_visited_doctor'] = most_visited
                
                # 4. Prescription Analytics
                # Prescription count
                context['prescription_count'] = prescriptions.count()
                
                # Prescriptions by doctor
                prescription_by_doctor = list(
                    prescriptions.values('doctor__first_name', 'doctor__last_name')
                    .annotate(count=Count('id'))
                    .order_by('-count')
                )
                
                context['prescription_by_doctor'] = prescription_by_doctor
                
                # 5. Engagement Metrics
                # No-show rate
                no_shows = bookings.filter(status='no_show').count()
                total_appointments = bookings.count()
                
                if total_appointments > 0:
                    no_show_rate = (no_shows / total_appointments) * 100
                else:
                    no_show_rate = 0
                
                context['no_show_rate'] = round(no_show_rate, 2)
                
                # Cancellation rate
                cancellations = bookings.filter(status='cancelled').count()
                
                if total_appointments > 0:
                    cancellation_rate = (cancellations / total_appointments) * 100
                else:
                    cancellation_rate = 0
                
                context['cancellation_rate'] = round(cancellation_rate, 2)
                
                # 6. Satisfaction Metrics
                # Average rating given
                avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0
                context['avg_rating'] = round(avg_rating, 2)
                
                # Rating distribution
                rating_distribution = list(
                    reviews.values('rating')
                    .annotate(count=Count('id'))
                    .order_by('rating')
                )
                
                # Fill in missing ratings
                rating_data = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
                for item in rating_distribution:
                    rating_data[item['rating']] = item['count']
                
                context['rating_distribution'] = json.dumps({
                    'labels': list(rating_data.keys()),
                    'data': list(rating_data.values())
                })
                
                # 7. Recent Activity
                context['recent_appointments'] = bookings.order_by('-appointment_date')[:10]
                context['recent_vitals'] = vital_records.order_by('-recorded_at')[:10]
                context['recent_prescriptions'] = prescriptions.order_by('-created_at')[:10]
            
        # Get all patients for the dropdown
        context['all_patients'] = User.objects.filter(role='patient').order_by('first_name', 'last_name')
        
        return context