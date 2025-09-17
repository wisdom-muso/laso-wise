import random
from datetime import datetime, timedelta, time
import pytz
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from appointments.models import Appointment
from appointments.models_availability import DoctorAvailability, DoctorTimeOff
from treatments.models import Treatment, Prescription
from treatments.models_medical_history import MedicalHistory
from core.models_communication import CommunicationNotification
from treatments.models_medications import Medication
from treatments.models_lab import LabTest, TestResult
from treatments.models_imaging import MedicalImage, Report

User = get_user_model()

# Doctor specializations
SPECIALIZATIONS = [
    'Internal Medicine', 'Cardiology', 'Ophthalmology', 'Orthopedics', 'Neurology',
    'Dermatology', 'Urology', 'Otorhinolaryngology', 'General Surgery', 'Obstetrics and Gynecology',
    'Pediatrics', 'Psychiatry', 'Physical Therapy and Rehabilitation'
]

# Patient blood types
BLOOD_TYPES = ['A Rh+', 'A Rh-', 'B Rh+', 'B Rh-', 'AB Rh+', 'AB Rh-', '0 Rh+', '0 Rh-']

# Cities and districts (a few examples have been added)
CITIES_AND_DISTRICTS = [
    {'city': 'Istanbul', 'districts': ['Kadikoy', 'Besiktas', 'Sisli', 'Uskudar', 'Beyoglu']},
    {'city': 'Ankara', 'districts': ['Cankaya', 'Kecioren', 'Mamak', 'Yenimahalle', 'Etimesgut']},
    {'city': 'Izmir', 'districts': ['Konak', 'Karsiyaka', 'Bornova', 'Bayrakli', 'Buca']},
    {'city': 'Bursa', 'districts': ['Osmangazi', 'Nilufer', 'Yildirim', 'Gemlik', 'Inegol']},
    {'city': 'Antalya', 'districts': ['Muratpasa', 'Konyaalti', 'Kepez', 'Alanya', 'Manavgat']}
]

# Treatment diagnoses
DIAGNOSES = [
    'Flu', 'Common Cold', 'Migraine', 'Hypertension', 'Diabetes', 
    'Anemia', 'Herniated Disc', 'Cervical Hernia', 'Gastritis', 'Reflux',
    'Asthma', 'Bronchitis', 'Sinusitis', 'Ear Infection', 'Pharyngitis',
    'Eczema', 'Psoriasis', 'Allergy', 'Vertigo', 'Anxiety'
]

# Medications and instructions for use
MEDICATIONS = [
    {
        'name': 'Parol',
        'dosage': '500 mg',
        'instructions': '3 times a day, should not be taken on an empty stomach.'
    },
    {
        'name': 'Aspirin',
        'dosage': '100 mg',
        'instructions': 'Once a day, should be taken after meals.'
    },
    {
        'name': 'Nurofen',
        'dosage': '400 mg',
        'instructions': 'Twice a day, should be taken 12 hours apart.'
    },
    {
        'name': 'Augmentin',
        'dosage': '1000 mg',
        'instructions': 'Twice a day, 12 hours apart, should be taken before meals.'
    },
    {
        'name': 'Ventolin',
        'dosage': '100 mcg',
        'instructions': 'Twice a day, should be administered as 2 inhalations.'
    },
    {
        'name': 'Nexium',
        'dosage': '40 mg',
        'instructions': 'Once a day, should be taken in the morning on an empty stomach.'
    },
    {
        'name': 'Cipralex',
        'dosage': '10 mg',
        'instructions': 'Once a day, should be taken after dinner.'
    },
    {
        'name': 'Euthyrox',
        'dosage': '50 mcg',
        'instructions': 'Once a day, in the morning on an empty stomach, 30 minutes before breakfast.'
    },
    {
        'name': 'Concor',
        'dosage': '5 mg',
        'instructions': 'Once a day, should be taken after breakfast in the morning.'
    },
    {
        'name': 'Xyzal',
        'dosage': '5 mg',
        'instructions': 'Once a day, should be taken after dinner.'
    }
]

class Command(BaseCommand):
    help = 'Creates sample data for the Laso Healthcare system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--patients',
            type=int,
            default=20,
            help='Number of patients to create'
        )
        parser.add_argument(
            '--doctors',
            type=int,
            default=10,
            help='Number of doctors to create'
        )
        parser.add_argument(
            '--appointments',
            type=int,
            default=50,
            help='Number of appointments to create'
        )
        parser.add_argument(
            '--treatments',
            type=int,
            default=30,
            help='Number of treatments to create'
        )
        parser.add_argument(
            '--availabilities',
            type=int,
            default=20,
            help='Number of doctor availabilities to create'
        )
        parser.add_argument(
            '--timeoffs',
            type=int,
            default=15,
            help='Number of doctor timeoffs to create'
        )
        parser.add_argument(
            '--medicalhistories',
            type=int,
            default=25,
            help='Number of medical histories to create'
        )
        parser.add_argument(
            '--notifications',
            type=int,
            default=40,
            help='Number of notifications to create'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting Laso Healthcare sample data creation...'))
        
        # Create admin user
        self.create_admin_user()
        
        # Create receptionists
        self.create_receptionists()
        
        # Create doctors
        num_doctors = options['doctors']
        doctors = self.create_doctors(num_doctors)
        
        # Create patients
        num_patients = options['patients']
        patients = self.create_patients(num_patients)
        
        # Create doctor availabilities
        num_availabilities = options['availabilities']
        self.create_doctor_availabilities(num_availabilities, doctors)
        
        # Create doctor timeoffs
        num_timeoffs = options['timeoffs']
        self.create_doctor_timeoffs(num_timeoffs, doctors)
        
        # Create appointments
        num_appointments = options['appointments']
        appointments = self.create_appointments(num_appointments, doctors, patients)
        
        # Create treatments and prescriptions
        num_treatments = options['treatments']
        treatments = self.create_treatments_and_prescriptions(num_treatments, appointments)
        
        # Create medical histories
        num_medicalhistories = options['medicalhistories']
        self.create_medical_histories(num_medicalhistories, patients)
        
        # Create lab tests and results
        self.create_lab_tests_and_results(doctors, patients)
        
        # Create imaging and results
        self.create_imaging_and_results(doctors, patients)
        
        # Create notifications
        num_notifications = options['notifications']
        self.create_notifications(num_notifications)
        
        self.stdout.write(self.style.SUCCESS('Sample data created successfully!'))
        self.stdout.write(f'- {num_doctors} doctors')
        self.stdout.write(f'- {num_patients} patients')
        self.stdout.write(f'- {num_availabilities} doctor availabilities')
        self.stdout.write(f'- {num_timeoffs} doctor timeoffs')
        self.stdout.write(f'- {num_appointments} appointments')
        self.stdout.write(f'- {num_treatments} treatments and prescriptions')
        self.stdout.write(f'- {num_medicalhistories} medical history records')
        self.stdout.write(f'- {num_notifications} notifications')

    def create_admin_user(self):
        """Creates an admin user."""
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@laso.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'user_type': 'admin',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Admin user created'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))

    def create_receptionists(self):
        """Creates receptionist users."""
        receptionist_data = [
            {
                'username': 'ayse',
                'email': 'ayse@laso.com',
                'first_name': 'Ayse',
                'last_name': 'Yilmaz',
                'password': 'password123'
            },
            {
                'username': 'mehmet',
                'email': 'mehmet@laso.com',
                'first_name': 'Mehmet',
                'last_name': 'Demir',
                'password': 'password123'
            }
        ]
        
        created_count = 0
        for data in receptionist_data:
            user, created = User.objects.get_or_create(
                username=data['username'],
                defaults={
                    'email': data['email'],
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'user_type': 'receptionist',
                }
            )
            
            if created:
                user.set_password(data['password'])
                user.save()
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'{created_count} receptionist users created'))

    def create_doctors(self, num_doctors):
        """Creates the specified number of doctors."""
        created_count = 0
        for i in range(1, num_doctors + 1):
            first_name = self.get_random_first_name(gender='male' if i % 2 == 0 else 'female')
            last_name = self.get_random_last_name()
            specialization = random.choice(SPECIALIZATIONS)
            username = f"dr.{first_name.lower()}"
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@laso.com',
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_type': 'doctor',
                    'specialization': specialization,
                }
            )
            
            if created:
                user.set_password('doctor123')
                user.save()
                created_count += 1
        
        doctors = User.objects.filter(user_type='doctor')
        self.stdout.write(self.style.SUCCESS(f'{created_count} doctor users created'))
        return doctors

    def create_patients(self, num_patients):
        """Creates the specified number of patients."""
        created_count = 0
        for i in range(1, num_patients + 1):
            first_name = self.get_random_first_name(gender='male' if i % 2 == 0 else 'female')
            last_name = self.get_random_last_name()
            username = f"patient.{first_name.lower()}"
            
            # Create random address
            location = random.choice(CITIES_AND_DISTRICTS)
            district = random.choice(location['districts'])
            address = f"{random.randint(1, 100)}. Street, No: {random.randint(1, 100)}, {district} / {location['city']}"
            
            # Random date of birth (between 18-80 years old)
            age = random.randint(18, 80)
            birth_date = datetime.now().date() - timedelta(days=age*365)
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@gmail.com',
                    'first_name': first_name,
                    'last_name': last_name,
                    'user_type': 'patient',
                    'date_of_birth': birth_date,
                    'phone_number': f"05{random.randint(10, 99)}{random.randint(1000000, 9999999)}",
                    'address': address,
                    'blood_type': random.choice(BLOOD_TYPES),
                }
            )
            
            if created:
                user.set_password('patient123')
                user.save()
                created_count += 1
        
        patients = User.objects.filter(user_type='patient')
        self.stdout.write(self.style.SUCCESS(f'{created_count} patient users created'))
        return patients

    def create_appointments(self, num_appointments, doctors, patients):
        """Creates the specified number of appointments."""
        if not doctors.exists() or not patients.exists():
            self.stdout.write(self.style.ERROR('Doctor or patient not found! Appointments cannot be created.'))
            return []
        
        # Appointment times (09:00 - 17:00, 30-minute intervals)
        appointment_times = []
        start_time = time(9, 0)
        for i in range(16):  # 8 hours x 2 (30-minute slots)
            hour = 9 + i // 2
            minute = 0 if i % 2 == 0 else 30
            appointment_times.append(time(hour, minute))
        
        # Create appointments between the last 60 days and the next 30 days
        start_date = timezone.now().date() - timedelta(days=60)
        end_date = timezone.now().date() + timedelta(days=30)
        date_range = (end_date - start_date).days
        
        created_count = 0
        appointments = []
        
        for _ in range(num_appointments):
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            
            # Random date and time
            random_day = random.randint(0, date_range)
            appointment_date = start_date + timedelta(days=random_day)
            appointment_time = random.choice(appointment_times)
            
            # Appointment status
            if appointment_date < timezone.now().date():
                # Past appointments are either completed or canceled
                status = random.choice(['completed', 'cancelled', 'completed', 'completed'])  # More completed
            else:
                # Future appointments are planned
                status = 'planned'
            
            # Random description
            descriptions = [
                'General check-up',
                'Regular check-up',
                'Pain complaint',
                'Follow-up appointment',
                'Prescription writing',
                'Evaluation of test results',
                'Headache complaint',
                'Back pain',
                'Blood pressure check',
                'Stomach complaints'
            ]
            
            description = random.choice(descriptions)
            
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=appointment_date,
                time=appointment_time,
                description=description,
                status=status
            )
            
            appointments.append(appointment)
            created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'{created_count} appointments created'))
        return appointments

    def create_treatments_and_prescriptions(self, num_treatments, appointments):
        """Creates the specified number of treatments and prescriptions."""
        # Treatments can only be added to completed appointments
        completed_appointments = [appt for appt in appointments if appt.status == 'completed']
        
        if not completed_appointments:
            self.stdout.write(self.style.ERROR('No completed appointments found! Treatments cannot be created.'))
            return []
        
        # Create a random number of treatments (if there are not more completed appointments than num_treatments)
        treatment_count = min(len(completed_appointments), num_treatments)
        created_count = 0
        created_treatments = []
        
        for i in range(treatment_count):
            # Select a random completed appointment that does not yet have a treatment
            available_appointments = [appt for appt in completed_appointments if not hasattr(appt, 'treatment')]
            if not available_appointments:
                break
                
            appointment = random.choice(available_appointments)
            
            # Create treatment
            diagnosis = random.choice(DIAGNOSES)
            notes = random.choice([
                'Patient showed improvement within a week.',
                'Responded well to treatment.',
                'Regular medication use is important.',
                'Follow-up appointment scheduled for 2 weeks later.',
                'Patient was informed.',
                None,  # Sometimes there may be no notes
            ])
            
            treatment = Treatment.objects.create(
                appointment=appointment,
                diagnosis=diagnosis,
                notes=notes
            )
            
            created_count += 1
            created_treatments.append(treatment)
            
            # Add 1-3 random prescriptions
            num_prescriptions = random.randint(1, 3)
            medication_options = random.sample(MEDICATIONS, num_prescriptions)
            
            for medication in medication_options:
                # Create new medication object
                med_obj = Medication.objects.create(
                    name=medication['name'],
                    active_ingredient=f"Active ingredient {random.randint(1, 100)}",
                    description=f"{medication['name']} - {medication['dosage']} dose",
                    side_effects="Drowsiness, dizziness, nausea may occur."
                )
                
                # Create prescription
                Prescription.objects.create(
                    treatment=treatment,
                    medication=med_obj,
                    name=medication['name'],
                    dosage=medication['dosage'],
                    instructions=medication['instructions']
                )
        
        self.stdout.write(self.style.SUCCESS(f'{created_count} treatments and {created_count * 2} average prescriptions created'))
        return created_treatments

    def create_doctor_availabilities(self, num_availabilities, doctors):
        """Creates availability hours for doctors."""
        if not doctors.exists():
            self.stdout.write(self.style.ERROR('Doctor not found! Availabilities cannot be created.'))
            return
        
        # Day names (0: Monday, 6: Sunday)
        days = [0, 1, 2, 3, 4]  # Weekdays
        
        created_count = 0
        for doctor in doctors:
            if doctor.user_type != 'doctor':
                continue
                
            # Add 3-5 days of availability for each doctor
            available_days = random.sample(days, random.randint(3, 5))
            
            for day in available_days:
                # Working hour variations
                start_options = ['08:00', '09:00', '10:00']
                end_options = ['16:00', '17:00', '18:00']
                
                # Select random start and end times
                start_time = random.choice(start_options)
                end_time = random.choice(end_options)
                
                # Check start and end times for consistency
                start_hour = int(start_time.split(':')[0])
                end_hour = int(end_time.split(':')[0])
                
                if end_hour <= start_hour:
                    end_time = '18:00'  # Default end time
                
                try:
                    # Create availability
                    DoctorAvailability.objects.create(
                        doctor=doctor,
                        weekday=day,
                        start_time=start_time,
                        end_time=end_time
                    )
                    created_count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Error while creating availability: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'{created_count} doctor availabilities created'))

    def create_doctor_timeoffs(self, num_timeoffs, doctors):
        """Creates time off days for doctors."""
        if not doctors.exists():
            self.stdout.write(self.style.ERROR('Doctor not found! Time offs cannot be created.'))
            return
        
        # Reasons for leave
        reasons = ['Annual Leave', 'Sick Leave', 'Conference', 'Training', 'Personal Matters']
        
        created_count = 0
        today = timezone.now().date()
        
        for _ in range(num_timeoffs):
            try:
                # Select one of the users with doctor type
                doctor_users = [d for d in doctors if d.user_type == 'doctor']
                if not doctor_users:
                    break
                    
                doctor = random.choice(doctor_users)
                
                # Reason for leave
                reason = random.choice(reasons)
                
                # Random date range (past or future)
                if random.random() < 0.5:
                    # Past leave
                    start_date = today - timedelta(days=random.randint(60, 90))
                else:
                    # Future leave
                    start_date = today + timedelta(days=random.randint(10, 60))
                
                # Duration of leave (1-7 days)
                duration = random.randint(1, 7)
                end_date = start_date + timedelta(days=duration)
                
                # Create time off
                DoctorTimeOff.objects.create(
                    doctor=doctor,
                    start_date=start_date,
                    end_date=end_date,
                    reason=reason
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error while creating time off: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'{created_count} doctor time offs created'))

    def create_medical_histories(self, num_medicalhistories, patients):
        """Creates medical history records for patients."""
        if not patients.exists():
            self.stdout.write(self.style.ERROR('Patient not found! Medical history cannot be created.'))
            return
        
        # Medical conditions
        conditions = [
            'Hypertension', 'Diabetes', 'Asthma', 'Heart Disease', 'Migraine', 
            'Rheumatism', 'Thyroid Disease', 'Depression', 'Anxiety Disorder',
            'Cholesterol', 'Reflux', 'Ulcer', 'Chronic Bronchitis', 'Psoriasis',
            'Allergy', 'Arthritis', 'Osteoporosis', 'Epilepsy', 'Anemia'
        ]
        
        # Condition types
        condition_types = ['chronic', 'surgery', 'allergy', 'medication', 'other']
        
        created_count = 0
        today = timezone.now().date()
        
        for _ in range(num_medicalhistories):
            try:
                # Select one of the users with patient type
                patient_users = [p for p in patients if p.user_type == 'patient']
                if not patient_users:
                    break
                    
                patient = random.choice(patient_users)
                
                # Select a random condition
                condition = random.choice(conditions)
                condition_type = random.choice(condition_types)
                
                # Diagnosis date (1-15 years ago)
                years_ago = random.randint(1, 15)
                diagnosed_date = today - timedelta(days=years_ago * 365)
                
                # Notes
                notes_options = [
                    f'{condition} diagnosed. Regular follow-up required.',
                    f'Regular medication use recommended for {condition}.',
                    f'{condition} under control, check-up recommended every 6 months.',
                    f'Lifestyle changes recommended for {condition}, which is also in the family history.',
                    f'Patient informed about {condition}, regular check-ups planned.'
                ]
                
                # Create medical history
                MedicalHistory.objects.create(
                    patient=patient,
                    condition=condition,
                    condition_type=condition_type,
                    diagnosed_date=diagnosed_date,
                    notes=random.choice(notes_options)
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error while creating medical history: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'{created_count} medical history records created'))

    def create_lab_tests_and_results(self, doctors, patients):
        """Creates lab tests and results."""
        if not doctors.exists() or not patients.exists():
            self.stdout.write(self.style.ERROR('Doctor or patient not found! Lab tests cannot be created.'))
            return
        
        # Test types
        test_types = [
            'Complete Blood Count', 'Blood Sugar', 'Cholesterol Panel', 'Liver Function Test',
            'Kidney Function Test', 'Thyroid Panel', 'Urinalysis', 'HbA1c',
            'Vitamin D', 'Vitamin B12', 'Iron', 'Electrolyte Panel'
        ]
        
        created_tests_count = 0
        created_results_count = 0
        today = timezone.now().date()
        
        # Filter doctor and patient lists
        doctor_users = [d for d in doctors if d.user_type == 'doctor']
        patient_users = [p for p in patients if p.user_type == 'patient']
        
        if not doctor_users or not patient_users:
            self.stdout.write(self.style.ERROR('Doctor or patient not found! Lab tests cannot be created.'))
            return
        
        # Create 20-30 tests
        num_tests = random.randint(20, 30)
        
        for _ in range(num_tests):
            try:
                # Select random patient and doctor
                patient = random.choice(patient_users)
                doctor = random.choice(doctor_users)
                
                # Test type
                test_type = random.choice(test_types)
                
                # Test date (within the last 180 days)
                days_ago = random.randint(1, 180)
                test_date = today - timedelta(days=days_ago)
                
                # Test status
                if days_ago > 7:
                    status = 'completed'  # Tests older than 1 week are completed
                else:
                    status = random.choice(['pending', 'completed', 'completed'])  # New tests are mostly completed
                
                # Create lab test
                lab_test = LabTest.objects.create(
                    patient=patient,
                    doctor=doctor,
                    test_type=test_type,
                    test_date=test_date,
                    status=status
                )
                created_tests_count += 1
                
                # Create result for completed tests
                if status == 'completed':
                    # Result date (1-3 days after test date)
                    result_date = test_date + timedelta(days=random.randint(1, 3))
                    
                    # Results and comments
                    results_options = [
                        f'{test_type} results are within the normal range.',
                        f'Slight abnormalities were observed in the {test_type} results.',
                        f'{test_type} values are within the reference range.',
                        f'{test_type} results were examined in detail.'
                    ]
                    
                    interpretation_options = [
                        'Normal results, consistent with clinical findings.',
                        'Slight abnormalities present, not clinically significant.',
                        'Results evaluated, no change in treatment required.',
                        'Results are within the normal range, health status is good.'
                    ]
                    
                    recommendations_options = [
                        'No follow-up required.',
                        'Follow-up recommended after 6 months.',
                        'Continuation of current treatment is appropriate.',
                        'Lifestyle changes are recommended.',
                        'Annual routine check-ups are sufficient.'
                    ]
                    
                    # Create result
                    TestResult.objects.create(
                        lab_test=lab_test,
                        result_date=result_date,
                        results=random.choice(results_options),
                        interpretation=random.choice(interpretation_options),
                        recommendations=random.choice(recommendations_options)
                    )
                    created_results_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error while creating lab test/result: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'{created_tests_count} lab tests and {created_results_count} lab results created'))

    def create_imaging_and_results(self, doctors, patients):
        """Creates medical images and reports."""
        if not doctors.exists() or not patients.exists():
            self.stdout.write(self.style.ERROR('Doctor or patient not found! Medical images cannot be created.'))
            return
        
        # Imaging types
        image_types = ['xray', 'mri', 'ct', 'ultrasound', 'other']
        
        # Body parts
        body_parts = [
            'Chest', 'Abdomen', 'Head', 'Spine', 'Pelvis', 
            'Knee', 'Shoulder', 'Wrist', 'Ankle', 'Hip'
        ]
        
        created_images_count = 0
        created_reports_count = 0
        today = timezone.now().date()
        
        # Filter doctor and patient lists
        doctor_users = [d for d in doctors if d.user_type == 'doctor']
        patient_users = [p for p in patients if p.user_type == 'patient']
        
        if not doctor_users or not patient_users:
            self.stdout.write(self.style.ERROR('Doctor or patient not found! Medical images cannot be created.'))
            return
        
        # Create random treatments (to be used later)
        treatments = []
        for _ in range(20):
            # Create a random appointment
            patient = random.choice(patient_users)
            doctor = random.choice(doctor_users)
            
            # Appointment date
            appointment_date = today - timedelta(days=random.randint(10, 60))
            appointment_time = time(random.randint(9, 16), random.choice([0, 15, 30, 45]))
            
            # Create appointment
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                date=appointment_date,
                time=appointment_time,
                description="Appointment for imaging",
                status="completed"
            )
            
            # Create treatment
            treatment = Treatment.objects.create(
                appointment=appointment,
                diagnosis="Condition requiring imaging",
                notes="Treatment to be planned according to imaging result"
            )
            treatments.append(treatment)
        
        # Create 15-25 imaging
        num_imaging = random.randint(15, 25)
        
        for _ in range(num_imaging):
            try:
                # Select random treatment, patient and doctor
                treatment = random.choice(treatments)
                patient = treatment.patient
                doctor = treatment.doctor
                
                # Imaging type and body part
                image_type = random.choice(image_types)
                body_part = random.choice(body_parts)
                
                # Imaging date (within the last 60 days)
                days_ago = random.randint(1, 60)
                taken_date = today - timedelta(days=days_ago)
                
                # Description
                description_options = [
                    f'{image_type} imaging due to {body_part} pain',
                    f'Imaging due to swelling in the {body_part} area',
                    f'Post-traumatic check-up of the {body_part} area',
                    f'Suspicion of abnormality in the {body_part} area',
                    'Routine check-up',
                    'Follow-up imaging'
                ]
                
                # Create medical image
                image = MedicalImage.objects.create(
                    treatment=treatment,
                    patient=patient,
                    doctor=doctor,
                    image_type=image_type,
                    body_part=body_part,
                    taken_date=taken_date,
                    description=random.choice(description_options),
                    image_file="medical_images/sample.jpg"  # Sample file name
                )
                created_images_count += 1
                
                # Create report for random images (with 70% probability)
                if random.random() < 0.7:
                    # Report date (1-3 days after imaging date)
                    report_date = taken_date + timedelta(days=random.randint(1, 3))
                    
                    # Report contents
                    title_options = [
                        f'{body_part} {image_type} Evaluation',
                        f'{body_part} Imaging Report',
                        f'{image_type.upper()} Report - {body_part}',
                        f'Medical Evaluation - {body_part}'
                    ]
                    
                    content_options = [
                        f'No abnormality was detected in the {body_part} area. Normal anatomical structure and appearance are present.',
                        f'Minimal degenerative changes were observed in the {body_part} area. No clinically significant pathology was observed.',
                        f'{body_part} imaging is within normal limits, and no findings were found to explain the patient\'s complaints.',
                        f'Slight changes are present in the {body_part} area, and clinical correlation is recommended. Control imaging is not required.'
                    ]
                    
                    # Create report
                    Report.objects.create(
                        treatment=treatment,
                        patient=patient,
                        doctor=doctor,
                        report_type='diagnostic',
                        title=random.choice(title_options),
                        content=random.choice(content_options),
                        valid_from=report_date,
                        valid_until=report_date + timedelta(days=365)  # Valid for 1 year
                    )
                    created_reports_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error while creating medical image/report: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'{created_images_count} medical images and {created_reports_count} reports created'))

    def create_notifications(self, num_notifications):
        """Creates notifications for users."""
        all_users = User.objects.all()
        
        if not all_users.exists():
            self.stdout.write(self.style.ERROR('User not found! Notifications cannot be created.'))
            return
        
        # Notification types
        notification_types = [
            'appointment_reminder', 'prescription_refill', 'test_result',
            'message', 'system'
        ]
        
        created_count = 0
        today = timezone.now()
        
        for _ in range(num_notifications):
            try:
                # Select a random user
                user = random.choice(all_users)
                
                # Notification type
                notification_type = random.choice(notification_types)
                
                # Notification content
                content = ''
                if notification_type == 'appointment_reminder':
                    content = random.choice([
                        "Reminder about your upcoming appointment.",
                        "Don't forget your appointment tomorrow.",
                        "You have an appointment scheduled for next week.",
                        "Your appointment with Dr. is in 3 days."
                    ])
                elif notification_type == 'prescription_refill':
                    content = random.choice([
                        "It's time to renew your prescription.",
                        "Your medications are running low, please contact your doctor.",
                        "Your prescription is ready, you can pick it up from the pharmacy.",
                        "Renewal reminder for your medication treatment."
                    ])
                elif notification_type == 'test_result':
                    content = random.choice([
                        "Your test results are ready.",
                        "Your lab results have been uploaded to the system.",
                        "Your imaging results have been evaluated by your doctor.",
                        "Your new test results are available."
                    ])
                elif notification_type == 'message':
                    content = random.choice([
                        "You have a new message from your doctor.",
                        "You have a message from your healthcare team.",
                        "A new message about your treatment.",
                        "You have received a message about your appointment."
                    ])
                else:  # system
                    content = random.choice([
                        "There will be a short interruption due to system maintenance.",
                        "The application has been updated.",
                        "Update your account information.",
                        "New features have been added, discover them!"
                    ])
                
                # Creation date (within the last 30 days)
                days_ago = random.randint(0, 30)
                created_at = today - timedelta(days=days_ago)
                
                # Read status
                is_read = random.choice([True, False]) if days_ago > 2 else False
                
                # Create notification
                CommunicationNotification.objects.create(
                    user=user,
                    notification_type=notification_type,
                    content=content,
                    is_read=is_read,
                    created_at=created_at
                )
                created_count += 1
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error while creating notification: {e}'))
        
        self.stdout.write(self.style.SUCCESS(f'{created_count} notifications created'))

    def get_random_first_name(self, gender='male'):
        """Returns a random Turkish name."""
        male_names = ['Ahmet', 'Mehmet', 'Mustafa', 'Ali', 'Hasan', 'Huseyin', 'Ibrahim', 'Osman', 'Yusuf', 'Murat',
                     'Omer', 'Enes', 'Emre', 'Baran', 'Can', 'Deniz', 'Eren', 'Furkan', 'Gokhan', 'Kemal']
        female_names = ['Ayse', 'Fatma', 'Emine', 'Hatice', 'Zeynep', 'Elif', 'Meryem', 'Esra', 'Nur', 'Zehra',
                       'Melek', 'Ebru', 'Derya', 'Canan', 'Busra', 'Asli', 'Gul', 'Seda', 'Pinar', 'Ozge']
        
        if gender == 'male':
            return random.choice(male_names)
        else:
            return random.choice(female_names)

    def get_random_last_name(self):
        """Returns a random Turkish surname."""
        last_names = ['Yilmaz', 'Kaya', 'Demir', 'Celik', 'Sahin', 'Yildiz', 'Yildirim', 'Ozturk', 'Aydin', 'Ozdemir',
                     'Arslan', 'Dogan', 'Kilic', 'Aslan', 'Cetin', 'Kara', 'Koc', 'Kurt', 'Ozkan', 'Simsek']
        return random.choice(last_names)