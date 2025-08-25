from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check existing users and create basic test users if needed'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Checking existing users...'))
        
        # Check all users
        users = User.objects.all()
        self.stdout.write(f'📊 Total users in database: {users.count()}')
        
        for user in users:
            self.stdout.write(f'  👤 {user.username} ({user.email}) - Type: {user.user_type} - Staff: {user.is_staff} - Superuser: {user.is_superuser}')
        
        # Create basic test users if none exist
        if users.count() == 0:
            self.stdout.write(self.style.WARNING('⚠️  No users found! Creating basic test users...'))
            
            # Create admin user
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@laso-healthcare.com',
                password='admin123',
                first_name='Admin',
                last_name='User',
                user_type='admin'
            )
            self.stdout.write(f'✅ Created admin user: admin/admin123')
            
            # Create doctor user
            doctor = User.objects.create_user(
                username='doctor',
                email='doctor@laso-healthcare.com',
                password='doctor123',
                first_name='Dr. Jane',
                last_name='Smith',
                user_type='doctor',
                specialization='General Medicine'
            )
            self.stdout.write(f'✅ Created doctor user: doctor/doctor123')
            
            # Create patient user
            patient = User.objects.create_user(
                username='patient',
                email='patient@laso-healthcare.com',
                password='patient123',
                first_name='John',
                last_name='Doe',
                user_type='patient'
            )
            self.stdout.write(f'✅ Created patient user: patient/patient123')
            
            self.stdout.write(self.style.SUCCESS('🎉 Basic test users created successfully!'))
        
        self.stdout.write(self.style.SUCCESS('✅ User check completed!'))