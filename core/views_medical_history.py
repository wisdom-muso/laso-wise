from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.auth import get_user_model

from treatments.models_medical_history import MedicalHistory
from .forms import MedicalHistoryForm

User = get_user_model()

class MedicalHistoryListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """
    View for listing patient medical history.
    """
    model = MedicalHistory
    template_name = 'core/medical_history_list.html'
    context_object_name = 'medical_histories'
    
    def test_func(self):
        # Only doctors, receptionists, and admins can view
        # Patients can only view their own history
        user = self.request.user
        patient_id = self.kwargs.get('patient_id')
        
        if user.is_patient():
            return str(user.id) == str(patient_id)
        return user.is_doctor() or user.is_receptionist() or user.is_admin_user()
    
    def get_queryset(self):
        patient_id = self.kwargs.get('patient_id')
        return MedicalHistory.objects.filter(patient_id=patient_id).order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_id = self.kwargs.get('patient_id')
        context['patient'] = get_object_or_404(User, id=patient_id)
        return context

class MedicalHistoryCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """
    View for creating patient medical history.
    """
    model = MedicalHistory
    form_class = MedicalHistoryForm
    template_name = 'core/medical_history_form.html'
    
    def test_func(self):
        # Sadece doktorlar ve adminler ekleyebilir
        return self.request.user.is_doctor() or self.request.user.is_admin_user()
    
    def get_initial(self):
        initial = super().get_initial()
        patient_id = self.kwargs.get('patient_id')
        if patient_id:
            initial['patient'] = patient_id
        return initial
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient_id = self.kwargs.get('patient_id')
        context['patient'] = get_object_or_404(User, id=patient_id)
        return context
    
    def get_success_url(self):
        return reverse_lazy('medical-history-list', kwargs={'patient_id': self.kwargs.get('patient_id')})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Medical history record created successfully.'))
        return response

class MedicalHistoryUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating patient medical history.
    """
    model = MedicalHistory
    form_class = MedicalHistoryForm
    template_name = 'core/medical_history_form.html'
    
    def test_func(self):
        # Only doctors and admins can update
        return self.request.user.is_doctor() or self.request.user.is_admin_user()
    
    def get_success_url(self):
        return reverse_lazy('medical-history-list', kwargs={'patient_id': self.object.patient.id})
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, _('Medical history record updated successfully.'))
        return response

class MedicalHistoryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting patient medical history.
    """
    model = MedicalHistory
    template_name = 'core/medical_history_confirm_delete.html'
    
    def test_func(self):
        # Sadece doktorlar ve adminler silebilir
        return self.request.user.is_doctor() or self.request.user.is_admin_user()
    
    def get_success_url(self):
        return reverse_lazy('medical-history-list', kwargs={'patient_id': self.object.patient.id})
    
    def delete(self, request, *args, **kwargs):
        response = super().delete(request, *args, **kwargs)
        messages.success(self.request, _('Medical history record deleted successfully.'))
        return response
