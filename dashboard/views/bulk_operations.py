from django.shortcuts import render, redirect
from django.views.generic import View
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import HttpResponse
import csv
import io
import pandas as pd
from datetime import datetime

from accounts.decorators import AdminRequiredMixin
from accounts.models import User, Profile
from core.models import Speciality


class BulkDoctorImportView(AdminRequiredMixin, View):
    """
    View for importing doctors in bulk via CSV
    """
    template_name = 'dashboard/bulk_operations/doctor_import.html'
    
    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        csv_file = request.FILES.get('csv_file')
        
        if not csv_file:
            messages.error(request, _('Please upload a CSV file'))
            return redirect('bulk-doctor-import')
        
        if not csv_file.name.endswith('.csv'):
            messages.error(request, _('File must be a CSV'))
            return redirect('bulk-doctor-import')
        
        # Process the CSV file
        try:
            # Read the CSV file
            csv_data = csv_file.read().decode('utf-8')
            io_string = io.StringIO(csv_data)
            reader = csv.DictReader(io_string)
            
            # Track import results
            total_rows = 0
            successful_imports = 0
            failed_imports = 0
            error_messages = []
            
            # Process each row
            for row in reader:
                total_rows += 1
                
                try:
                    # Extract required fields
                    email = row.get('email', '').strip()
                    first_name = row.get('first_name', '').strip()
                    last_name = row.get('last_name', '').strip()
                    speciality_name = row.get('speciality', '').strip()
                    
                    # Validate required fields
                    if not email or not first_name or not last_name or not speciality_name:
                        error_messages.append(f"Row {total_rows}: Missing required fields")
                        failed_imports += 1
                        continue
                    
                    # Check if user already exists
                    if User.objects.filter(email=email).exists():
                        error_messages.append(f"Row {total_rows}: User with email {email} already exists")
                        failed_imports += 1
                        continue
                    
                    # Get or create speciality
                    speciality, created = Speciality.objects.get_or_create(
                        name=speciality_name,
                        defaults={'description': f'Auto-created speciality for {speciality_name}'}
                    )
                    
                    # Create the user
                    user = User.objects.create_user(
                        email=email,
                        password='TemporaryPassword123',  # Temporary password
                        first_name=first_name,
                        last_name=last_name,
                        role='doctor'
                    )
                    
                    # Create or update profile
                    profile, created = Profile.objects.get_or_create(
                        user=user,
                        defaults={
                            'specialization': speciality,
                            'address': row.get('address', ''),
                            'city': row.get('city', ''),
                            'state': row.get('state', ''),
                            'country': row.get('country', ''),
                            'zip_code': row.get('zip_code', ''),
                            'phone_number': row.get('phone_number', ''),
                            'bio': row.get('bio', ''),
                            'price_per_consultation': float(row.get('price', 0)) if row.get('price') else 0,
                        }
                    )
                    
                    # If not created, update the profile
                    if not created:
                        profile.specialization = speciality
                        profile.address = row.get('address', '')
                        profile.city = row.get('city', '')
                        profile.state = row.get('state', '')
                        profile.country = row.get('country', '')
                        profile.zip_code = row.get('zip_code', '')
                        profile.phone_number = row.get('phone_number', '')
                        profile.bio = row.get('bio', '')
                        profile.price_per_consultation = float(row.get('price', 0)) if row.get('price') else 0
                        profile.save()
                    
                    successful_imports += 1
                
                except Exception as e:
                    error_messages.append(f"Row {total_rows}: {str(e)}")
                    failed_imports += 1
            
            # Display import results
            if successful_imports > 0:
                messages.success(request, _(f'Successfully imported {successful_imports} doctors'))
            
            if failed_imports > 0:
                messages.warning(request, _(f'Failed to import {failed_imports} doctors'))
                for error in error_messages[:10]:  # Show first 10 errors
                    messages.error(request, error)
                
                if len(error_messages) > 10:
                    messages.error(request, _('... and more errors. Check the logs for details.'))
            
            return redirect('admin-doctors')
        
        except Exception as e:
            messages.error(request, _(f'Error processing CSV file: {str(e)}'))
            return redirect('bulk-doctor-import')


class BulkDoctorExportView(AdminRequiredMixin, View):
    """
    View for exporting doctors in bulk to CSV
    """
    def get(self, request, *args, **kwargs):
        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="doctors_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'email', 'first_name', 'last_name', 'speciality', 
            'address', 'city', 'state', 'country', 'zip_code', 
            'phone_number', 'bio', 'price'
        ])
        
        # Get all doctors
        doctors = User.objects.filter(role='doctor').select_related('profile', 'profile__specialization')
        
        # Write data rows
        for doctor in doctors:
            writer.writerow([
                doctor.email,
                doctor.first_name,
                doctor.last_name,
                doctor.profile.specialization.name if doctor.profile.specialization else '',
                doctor.profile.address,
                doctor.profile.city,
                doctor.profile.state,
                doctor.profile.country,
                doctor.profile.zip_code,
                doctor.profile.phone_number,
                doctor.profile.bio,
                doctor.profile.price_per_consultation
            ])
        
        return response


class BulkDoctorUpdateView(AdminRequiredMixin, View):
    """
    View for updating doctors in bulk
    """
    template_name = 'dashboard/bulk_operations/doctor_update.html'
    
    def get(self, request, *args, **kwargs):
        # Get all specialities for the form
        specialities = Speciality.objects.all().order_by('name')
        
        return render(request, self.template_name, {
            'specialities': specialities
        })
    
    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        speciality_id = request.POST.get('speciality')
        price = request.POST.get('price')
        is_active = request.POST.get('is_active')
        
        # Validate inputs
        if not action:
            messages.error(request, _('Please select an action'))
            return redirect('bulk-doctor-update')
        
        # Get doctors to update
        doctors = User.objects.filter(role='doctor')
        
        # Apply filters if provided
        filter_speciality = request.POST.get('filter_speciality')
        if filter_speciality:
            doctors = doctors.filter(profile__specialization_id=filter_speciality)
        
        filter_active = request.POST.get('filter_active')
        if filter_active:
            doctors = doctors.filter(is_active=(filter_active == 'active'))
        
        # Count doctors to update
        doctor_count = doctors.count()
        
        if doctor_count == 0:
            messages.warning(request, _('No doctors match the selected filters'))
            return redirect('bulk-doctor-update')
        
        # Perform the selected action
        if action == 'update_speciality' and speciality_id:
            speciality = Speciality.objects.get(id=speciality_id)
            for doctor in doctors:
                doctor.profile.specialization = speciality
                doctor.profile.save()
            
            messages.success(request, _(f'Updated speciality for {doctor_count} doctors'))
        
        elif action == 'update_price' and price:
            try:
                price_value = float(price)
                for doctor in doctors:
                    doctor.profile.price_per_consultation = price_value
                    doctor.profile.save()
                
                messages.success(request, _(f'Updated price for {doctor_count} doctors'))
            except ValueError:
                messages.error(request, _('Invalid price value'))
        
        elif action == 'update_status' and is_active:
            status_value = (is_active == 'active')
            doctors.update(is_active=status_value)
            
            status_text = 'activated' if status_value else 'deactivated'
            messages.success(request, _(f'{doctor_count} doctors {status_text}'))
        
        else:
            messages.error(request, _('Invalid action or missing required parameters'))
        
        return redirect('admin-doctors')


class BulkDoctorTemplateView(AdminRequiredMixin, View):
    """
    View for downloading a CSV template for doctor import
    """
    def get(self, request, *args, **kwargs):
        # Create the HttpResponse object with CSV header
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="doctor_import_template.csv"'
        
        # Create CSV writer
        writer = csv.writer(response)
        
        # Write header row
        writer.writerow([
            'email', 'first_name', 'last_name', 'speciality', 
            'address', 'city', 'state', 'country', 'zip_code', 
            'phone_number', 'bio', 'price'
        ])
        
        # Write example row
        writer.writerow([
            'doctor@example.com', 'John', 'Doe', 'Cardiology',
            '123 Main St', 'New York', 'NY', 'USA', '10001',
            '+1234567890', 'Experienced cardiologist with 10 years of practice', '100'
        ])
        
        return response