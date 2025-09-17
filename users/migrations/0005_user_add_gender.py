# Generated manually for gender field
from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20250915_1259'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='gender',
            field=models.CharField(blank=True, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], max_length=1, null=True, verbose_name='Gender'),
        ),
    ]
