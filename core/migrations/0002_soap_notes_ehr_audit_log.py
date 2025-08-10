# Generated manually for SOAP Notes, EHR, and Audit Log models

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('bookings', '0001_initial'),
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SoapNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subjective', models.TextField(help_text='Patient-reported symptoms, history, and concerns')),
                ('objective', models.TextField(help_text='Observations, test results, vital signs')),
                ('assessment', models.TextField(help_text="Doctor's diagnosis, impressions")),
                ('plan', models.TextField(help_text='Treatment plan, follow-up instructions')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_draft', models.BooleanField(default=False)),
                ('appointment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='soap_notes', to='bookings.booking')),
                ('created_by', models.ForeignKey(limit_choices_to={'role': 'doctor'}, on_delete=django.db.models.deletion.CASCADE, related_name='soap_notes_created', to='accounts.user')),
                ('patient', models.ForeignKey(limit_choices_to={'role': 'patient'}, on_delete=django.db.models.deletion.CASCADE, related_name='soap_notes', to='accounts.user')),
            ],
            options={
                'verbose_name': 'SOAP Note',
                'verbose_name_plural': 'SOAP Notes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='EHRRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('allergies', models.TextField(blank=True, help_text='Known allergies and reactions')),
                ('medications', models.TextField(blank=True, help_text='Current medications and dosages')),
                ('medical_history', models.TextField(blank=True, help_text='Past medical conditions and surgeries')),
                ('immunizations', models.TextField(blank=True, help_text='Immunization history')),
                ('lab_results', models.JSONField(blank=True, default=dict, help_text='Laboratory test results')),
                ('imaging_results', models.JSONField(blank=True, default=dict, help_text='Imaging study results')),
                ('vital_signs_history', models.JSONField(blank=True, default=list, help_text='Historical vital signs')),
                ('emergency_contacts', models.JSONField(blank=True, default=list, help_text='Emergency contact information')),
                ('insurance_info', models.JSONField(blank=True, default=dict, help_text='Insurance details')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('last_updated_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='ehr_records_updated', to='accounts.user')),
                ('patient', models.OneToOneField(limit_choices_to={'role': 'patient'}, on_delete=django.db.models.deletion.CASCADE, related_name='ehr_record', to='accounts.user')),
            ],
            options={
                'verbose_name': 'EHR Record',
                'verbose_name_plural': 'EHR Records',
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(choices=[('create', 'Create'), ('update', 'Update'), ('delete', 'Delete'), ('view', 'View')], max_length=10)),
                ('model_name', models.CharField(max_length=100)),
                ('object_id', models.IntegerField()),
                ('object_repr', models.CharField(max_length=200)),
                ('changes', models.JSONField(blank=True, default=dict)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('user_agent', models.TextField(blank=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to='accounts.user')),
            ],
            options={
                'verbose_name': 'Audit Log',
                'verbose_name_plural': 'Audit Logs',
                'ordering': ['-timestamp'],
            },
        ),
        migrations.AddConstraint(
            model_name='soapnote',
            constraint=models.UniqueConstraint(fields=('appointment', 'created_by'), name='unique_soap_note_per_appointment_doctor'),
        ),
    ]
