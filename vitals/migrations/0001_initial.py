from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [
        migrations.CreateModel(
            name='VitalCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('description', models.TextField(blank=True, verbose_name='Description')),
                ('unit', models.CharField(max_length=50, verbose_name='Unit of Measurement')),
                ('icon', models.CharField(default='fas fa-heartbeat', max_length=50, verbose_name='Icon Class')),
                ('color', models.CharField(default='#3498db', max_length=20, verbose_name='Color Code')),
                ('min_normal', models.FloatField(blank=True, null=True, verbose_name='Minimum Normal Value')),
                ('max_normal', models.FloatField(blank=True, null=True, verbose_name='Maximum Normal Value')),
                ('min_critical', models.FloatField(blank=True, null=True, verbose_name='Minimum Critical Value')),
                ('max_critical', models.FloatField(blank=True, null=True, verbose_name='Maximum Critical Value')),
                ('display_order', models.PositiveSmallIntegerField(default=0, verbose_name='Display Order')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
            ],
            options={
                'verbose_name': 'Vital Category',
                'verbose_name_plural': 'Vital Categories',
                'ordering': ['display_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='VitalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.FloatField(verbose_name='Value')),
                ('secondary_value', models.FloatField(blank=True, null=True, verbose_name='Secondary Value')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('is_professional_reading', models.BooleanField(default=False, verbose_name='Professional Reading')),
                ('recorded_at', models.DateTimeField(auto_now_add=True, verbose_name='Recorded At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='records', to='vitals.vitalcategory')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vital_records', to='auth.user')),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_vitals', to='auth.user')),
            ],
            options={
                'verbose_name': 'Vital Record',
                'verbose_name_plural': 'Vital Records',
                'ordering': ['-recorded_at'],
            },
        ),
        migrations.CreateModel(
            name='VitalNotification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message', models.TextField(verbose_name='Message')),
                ('severity', models.CharField(choices=[('info', 'Information'), ('warning', 'Warning'), ('danger', 'Danger')], default='info', max_length=20, verbose_name='Severity')),
                ('is_read', models.BooleanField(default=False, verbose_name='Read')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='Read At')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vital_notifications', to='auth.user')),
                ('vital_record', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='vitals.vitalrecord')),
            ],
            options={
                'verbose_name': 'Vital Notification',
                'verbose_name_plural': 'Vital Notifications',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='VitalGoal',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('target_value', models.FloatField(verbose_name='Target Value')),
                ('target_date', models.DateField(blank=True, null=True, verbose_name='Target Date')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('is_achieved', models.BooleanField(default=False, verbose_name='Achieved')),
                ('achieved_date', models.DateField(blank=True, null=True, verbose_name='Date Achieved')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goals', to='vitals.vitalcategory')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='vital_goals', to='auth.user')),
                ('set_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='set_vital_goals', to='auth.user')),
            ],
            options={
                'verbose_name': 'Vital Goal',
                'verbose_name_plural': 'Vital Goals',
                'ordering': ['-created_at'],
            },
        ),
    ]