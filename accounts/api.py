from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.db import transaction

from accounts.models import User, Profile


class LoginAPI(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response(
                {'message': 'Email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Try to find user by email
        try:
            user = User.objects.get(email=email)
            username = user.username
        except User.DoesNotExist:
            return Response(
                {'message': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Authenticate with username and password
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role,
                }
            })
        else:
            return Response(
                {'message': 'Invalid credentials'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )


class RegisterAPI(APIView):
    def post(self, request):
        data = request.data
        
        # Required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'message': f'{field} is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if user already exists
        if User.objects.filter(username=data['username']).exists():
            return Response(
                {'message': 'Username already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(email=data['email']).exists():
            return Response(
                {'message': 'Email already exists'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate role
        if data['role'] not in ['patient', 'doctor']:
            return Response(
                {'message': 'Role must be either patient or doctor'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Create user
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password=data['password'],
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                    role=data['role']
                )
                
                # Create profile
                profile = Profile.objects.create(
                    user=user,
                    phone=data.get('phone', ''),
                    gender=data.get('gender', ''),
                    city=data.get('city', ''),
                )
                
                # If doctor, add specialization
                if data['role'] == 'doctor' and data.get('specialization'):
                    profile.specialization = data['specialization']
                    profile.save()
                
                # Create token
                token, created = Token.objects.get_or_create(user=user)
                
                return Response({
                    'token': token.key,
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'first_name': user.first_name,
                        'last_name': user.last_name,
                        'role': user.role,
                    }
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            return Response(
                {'message': f'Registration failed: {str(e)}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )


class LogoutAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            # Delete the token
            request.user.auth_token.delete()
            logout(request)
            return Response({'message': 'Successfully logged out'})
        except:
            return Response({'message': 'Logout successful'})


class MeAPI(APIView):
  permission_classes = [IsAuthenticated]

  def get(self, request):
    u: User = request.user
    p: Profile = u.profile
    return Response({
      'id': u.id,
      'username': u.username,
      'email': u.email,
      'first_name': u.first_name,
      'last_name': u.last_name,
      'role': u.role,
      'profile': {
        'avatar': p.image,
        'phone': p.phone,
        'dob': p.dob,
        'about': p.about,
        'specialization': p.specialization,
        'gender': p.gender,
        'address': p.address,
        'city': p.city,
        'state': p.state,
        'postal_code': p.postal_code,
        'country': p.country,
        'price_per_consultation': p.price_per_consultation,
        'is_available': p.is_available,
        'allergies': p.allergies,
        'medical_conditions': p.medical_conditions,
      }
    })


class MeUpdateAPI(APIView):
  permission_classes = [IsAuthenticated]

  def post(self, request):
    u: User = request.user
    p: Profile = u.profile
    data = request.data

    # Basic fields
    for f in ['first_name', 'last_name', 'email']:
      if f in data:
        setattr(u, f, data.get(f))

    # Profile fields
    for f in ['phone','dob','about','specialization','gender','address','city','state','postal_code','country','price_per_consultation','is_available','allergies','medical_conditions']:
      if f in data:
        setattr(p, f, data.get(f))

    if request.FILES.get('avatar'):
      p.avatar = request.FILES['avatar']

    u.save()
    p.save()
    return Response({'ok': True})


class MeDeleteAPI(APIView):
  permission_classes = [IsAuthenticated]

  def post(self, request):
    # Soft-delete pattern can be implemented. For now, deactivate account.
    u: User = request.user
    u.is_active = False
    u.save()
    return Response({'ok': True}, status=status.HTTP_200_OK)







