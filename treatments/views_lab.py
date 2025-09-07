from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone

from .models_lab import LabTest, TestResult
from .forms import LabTestForm, TestResultForm
from treatments.models import Treatment

User = settings.AUTH_USER_MODEL

class LabTestListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    Laboratory tests list view.
    """
    model = LabTest
    template_name = 'treatments/lab_test_list.html'
    context_object_name = 'lab_tests'
    
    def test_func(self):
        # Only doctors, lab technicians and admins can view all lab tests
        # Patients can only view their own tests
        user = self.request.user
        patient_id = self.kwargs.get('patient_id')
        
        if user.is_patient():
            # If no patient_id in URL, patient can access (will be filtered in get_queryset)
            if patient_id is None:
                return True
            return str(user.id) == str(patient_id)
        return user.is_doctor() or user.is_receptionist() or user.is_admin_user()
    
    def get_queryset(self):
        user = self.request.user
        patient_id = self.kwargs.get('patient_id')
        
        if patient_id:
            return LabTest.objects.filter(patient_id=patient_id).order_by('-requested_date')
        elif user.is_patient():
            # If patient accesses without patient_id, show their own tests
            return LabTest.objects.filter(patient=user).order_by('-requested_date')
        elif user.is_doctor():
            return LabTest.objects.filter(doctor=user).order_by('-requested_date')
        else:
            return LabTest.objects.all().order_by('-requested_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_id = self.kwargs.get('patient_id')
        if patient_id:
            context['patient'] = get_object_or_404(User, id=patient_id)
        return context

class LabTestDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """
    Laboratory test detail view.
    """
    model = LabTest
    template_name = 'treatments/lab_test_detail.html'
    context_object_name = 'lab_test'
    
    def test_func(self):
        lab_test = self.get_object()
        user = self.request.user
        
        if user.is_patient():
            return lab_test.patient == user
        return user.is_doctor() or user.is_receptionist() or user.is_admin_user()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lab_test = self.get_object()
        
        # If the test result exists and contains a numeric value, get the past results
        if lab_test.result and lab_test.patient:
            try:
                # Get past results for tests with the same name
                previous_tests = LabTest.objects.filter(
                    patient=lab_test.patient,
                    test_name=lab_test.test_name,
                    status='completed'
                ).exclude(id=lab_test.id).order_by('requested_date')
                
                # If there are results and they contain numeric values, prepare the chart data
                if previous_tests.exists() and all(test.result for test in previous_tests):
                    dates = [test.result.created_at.strftime('%d.%m.%Y') for test in previous_tests]
                    dates.append(lab_test.result.created_at.strftime('%d.%m.%Y'))
                    
                    # Try to parse the result values
                    import re
                    values = []
                    unit = ''
                    reference_min = 0
                    reference_max = 0
                    
                    # Find the reference range of the current test
                    if lab_test.result.reference_values:
                        ref_match = re.search(r'(\d+\.?\d*)\s*-\s*(\d+\.?\d*)', lab_test.result.reference_values)
                        if ref_match:
                            reference_min = float(ref_match.group(1))
                            reference_max = float(ref_match.group(2))
                    
                    # Find the unit information
                    if lab_test.result.result_text:
                        unit_match = re.search(r'(\d+\.?\d*)\s*([a-zA-Z/]+)', lab_test.result.result_text)
                        if unit_match:
                            unit = unit_match.group(2)
                    
                    # Parse past test results
                    for test in previous_tests:
                        if test.result and test.result.result_text:
                            value_match = re.search(r'(\d+\.?\d*)', test.result.result_text)
                            if value_match:
                                values.append(float(value_match.group(1)))
                    
                    # Parse the current test result
                    if lab_test.result.result_text:
                        value_match = re.search(r'(\d+\.?\d*)', lab_test.result.result_text)
                        if value_match:
                            values.append(float(value_match.group(1)))
                    
                    # If the values are successfully parsed, add the chart data
                    if len(values) == len(dates) and len(values) > 0:
                        context['lab_results_chart_data'] = {
                            'dates': dates,
                            'values': values,
                            'unit': unit,
                            'reference_range': {
                                'min': reference_min,
                                'max': reference_max
                            }
                        }
            except Exception as e:
                # Do not prepare chart data in case of error
                print(f"Error processing lab results chart data: {e}")
        
        return context

class LabTestCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Laboratory test creation view.
    """
    model = LabTest
    form_class = LabTestForm
    template_name = 'treatments/lab_test_form.html'
    
    def test_func(self):
        # Only doctors, admins and receptionists can add
        user = self.request.user
        return user.is_doctor() or user.is_admin_user() or user.is_receptionist()
    
    def get_initial(self):
        initial = super().get_initial()
        treatment_id = self.kwargs.get('treatment_id')
        doctor_id = self.request.user.id if self.request.user.is_doctor() else None
        
        if treatment_id:
            treatment = get_object_or_404(Treatment, id=treatment_id)
            initial['treatment'] = treatment
            initial['patient'] = treatment.appointment.patient.id
            initial['doctor'] = treatment.appointment.doctor.id
        elif doctor_id:
            initial['doctor'] = doctor_id
            
        patient_id = self.kwargs.get('patient_id')
        if patient_id:
            initial['patient'] = patient_id
            
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        treatment_id = self.kwargs.get('treatment_id')
        patient_id = self.kwargs.get('patient_id')
        
        if treatment_id:
            context['treatment'] = get_object_or_404(Treatment, id=treatment_id)
        if patient_id:
            context['patient'] = get_object_or_404(User, id=patient_id)
            
        context['title'] = _('Request New Lab Test')
        return context
    
    def get_success_url(self):
        if 'treatment_id' in self.kwargs:
            return reverse_lazy('treatment-detail', kwargs={'pk': self.kwargs['treatment_id']})
        elif 'patient_id' in self.kwargs:
            return reverse_lazy('lab-test-list', kwargs={'patient_id': self.kwargs['patient_id']})
        return reverse_lazy('lab-test-list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Lab test created successfully.'))
        return response

class LabTestUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Laboratory test update view.
    """
    model = LabTest
    form_class = LabTestForm
    template_name = 'treatments/lab_test_form.html'
    
    def test_func(self):
        lab_test = self.get_object()
        user = self.request.user
        # Only the requesting doctor or admins can update
        if user.is_doctor():
            return lab_test.doctor == user
        return user.is_admin_user()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update Lab Test')
        return context
    
    def get_success_url(self):
        return reverse_lazy('lab-test-detail', kwargs={'pk': self.object.id})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Lab test updated successfully.'))
        return response

class LabTestDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Laboratory test deletion view.
    """
    model = LabTest
    template_name = 'treatments/lab_test_confirm_delete.html'
    
    def test_func(self):
        lab_test = self.get_object()
        user = self.request.user
        # Only the requesting doctor or admins can delete
        if user.is_doctor():
            return lab_test.doctor == user
        return user.is_admin_user()
    
    def get_success_url(self):
        if hasattr(self.object, 'patient'):
            return reverse_lazy('lab-test-list', kwargs={'patient_id': self.object.patient.id})
        return reverse_lazy('lab-test-list')
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, _('Lab test deleted successfully.'))
        return response

class TestResultCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    Test result creation view.
    """
    model = TestResult
    form_class = TestResultForm
    template_name = 'treatments/test_result_form.html'
    
    def test_func(self):
        # Only doctors, lab technicians and admins can add
        user = self.request.user
        return user.is_doctor() or user.is_admin_user() or user.is_receptionist()
    
    def get_initial(self):
        initial = super().get_initial()
        lab_test_id = self.kwargs.get('lab_test_id')
        
        if lab_test_id:
            lab_test = get_object_or_404(LabTest, id=lab_test_id)
            initial['lab_test'] = lab_test
            
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        lab_test_id = self.kwargs.get('lab_test_id')
        
        if lab_test_id:
            context['lab_test'] = get_object_or_404(LabTest, id=lab_test_id)
            
        context['title'] = _('Add Test Result')
        return context
    
    def get_success_url(self):
        return reverse_lazy('lab-test-detail', kwargs={'pk': self.object.lab_test.id})
    
    def form_valid(self, form):
        form.instance.lab_test.status = 'completed'
        form.instance.lab_test.completed_date = timezone.now()
        form.instance.lab_test.save()
        
        response = super().form_valid(form)
        messages.success(self.request, _('Test result added successfully.'))
        return response

class TestResultUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Test result update view.
    """
    model = TestResult
    form_class = TestResultForm
    template_name = 'treatments/test_result_form.html'
    
    def test_func(self):
        # Only doctors, lab technicians and admins can update
        user = self.request.user
        return user.is_doctor() or user.is_admin_user() or user.is_receptionist()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Update Test Result')
        context['lab_test'] = self.object.lab_test
        return context
    
    def get_success_url(self):
        return reverse_lazy('lab-test-detail', kwargs={'pk': self.object.lab_test.id})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Test result updated successfully.'))
        return response
