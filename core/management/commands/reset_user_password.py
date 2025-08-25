from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Reset a user password for testing'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to reset password for')
        parser.add_argument('--password', type=str, default='test123', help='New password (default: test123)')

    def handle(self, *args, **options):
        username = options['username']
        password = options['password']
        
        try:
            user = User.objects.get(username=username)
            
            self.stdout.write(f'🔍 User found: {user.username} ({user.email})')
            self.stdout.write(f'   Current user type: {user.user_type}')
            self.stdout.write(f'   Current active status: {user.is_active}')
            self.stdout.write(f'   Has usable password: {user.has_usable_password()}')
            
            if user.password:
                self.stdout.write(f'   Current password hash: {user.password[:30]}...')
            else:
                self.stdout.write('   ❌ No password hash found!')
            
            # Set new password
            user.set_password(password)
            user.save()
            
            self.stdout.write(self.style.SUCCESS(f'✅ Password reset for {username}'))
            self.stdout.write(f'🔑 New credentials: {username}/{password}')
            self.stdout.write(f'   New password hash: {user.password[:30]}...')
            
            # Test the password
            if user.check_password(password):
                self.stdout.write(self.style.SUCCESS('✅ Password verification successful'))
            else:
                self.stdout.write(self.style.ERROR('❌ Password verification failed'))
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ User "{username}" not found'))
            self.stdout.write('Available users:')
            for u in User.objects.all()[:10]:
                self.stdout.write(f'  - {u.username} ({u.email})')
            if User.objects.count() > 10:
                self.stdout.write(f'  ... and {User.objects.count() - 10} more users')