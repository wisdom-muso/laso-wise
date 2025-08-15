from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

from accounts.models import User, Profile


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







