from django.db import migrations

def add_default_categories(apps, schema_editor):
    VitalCategory = apps.get_model('vitals', 'VitalCategory')
    
    # Define default categories
    default_categories = [
        {
            'name': 'Blood Pressure',
            'description': 'Systolic and diastolic blood pressure measurement',
            'unit': 'mmHg',
            'icon': 'fas fa-heartbeat',
            'color': '#e74c3c',
            'min_normal': 90,
            'max_normal': 120,
            'min_critical': 70,
            'max_critical': 180,
            'display_order': 1,
        },
        {
            'name': 'Heart Rate',
            'description': 'Pulse rate measurement',
            'unit': 'bpm',
            'icon': 'fas fa-heart',
            'color': '#e74c3c',
            'min_normal': 60,
            'max_normal': 100,
            'min_critical': 40,
            'max_critical': 130,
            'display_order': 2,
        },
        {
            'name': 'Blood Glucose',
            'description': 'Blood sugar level measurement',
            'unit': 'mg/dL',
            'icon': 'fas fa-tint',
            'color': '#3498db',
            'min_normal': 70,
            'max_normal': 140,
            'min_critical': 50,
            'max_critical': 300,
            'display_order': 3,
        },
        {
            'name': 'Body Temperature',
            'description': 'Body temperature measurement',
            'unit': '°C',
            'icon': 'fas fa-thermometer-half',
            'color': '#f39c12',
            'min_normal': 36.1,
            'max_normal': 37.2,
            'min_critical': 35.0,
            'max_critical': 39.0,
            'display_order': 4,
        },
        {
            'name': 'Oxygen Saturation',
            'description': 'Blood oxygen level measurement',
            'unit': '%',
            'icon': 'fas fa-lungs',
            'color': '#2ecc71',
            'min_normal': 95,
            'max_normal': 100,
            'min_critical': 90,
            'max_critical': None,
            'display_order': 5,
        },
        {
            'name': 'Weight',
            'description': 'Body weight measurement',
            'unit': 'kg',
            'icon': 'fas fa-weight',
            'color': '#9b59b6',
            'min_normal': None,
            'max_normal': None,
            'min_critical': None,
            'max_critical': None,
            'display_order': 6,
        },
        {
            'name': 'Respiratory Rate',
            'description': 'Breathing rate measurement',
            'unit': 'breaths/min',
            'icon': 'fas fa-wind',
            'color': '#1abc9c',
            'min_normal': 12,
            'max_normal': 20,
            'min_critical': 8,
            'max_critical': 30,
            'display_order': 7,
        },
        {
            'name': 'Cholesterol',
            'description': 'Total cholesterol level',
            'unit': 'mg/dL',
            'icon': 'fas fa-vial',
            'color': '#f1c40f',
            'min_normal': None,
            'max_normal': 200,
            'min_critical': None,
            'max_critical': 240,
            'display_order': 8,
        },
    ]
    
    # Create categories
    for category_data in default_categories:
        VitalCategory.objects.create(**category_data)


def remove_default_categories(apps, schema_editor):
    VitalCategory = apps.get_model('vitals', 'VitalCategory')
    VitalCategory.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('vitals', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_default_categories, remove_default_categories),
    ]