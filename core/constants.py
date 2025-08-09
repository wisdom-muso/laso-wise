"""
Constants for the core application.
This file centralizes hardcoded values that were previously scattered throughout the codebase.
"""

# User roles
USER_ROLE_DOCTOR = 'doctor'
USER_ROLE_PATIENT = 'patient'
USER_ROLE_ADMIN = 'admin'
USER_ROLE_STAFF = 'staff'

USER_ROLES = (
    (USER_ROLE_DOCTOR, 'Doctor'),
    (USER_ROLE_PATIENT, 'Patient'),
    (USER_ROLE_ADMIN, 'Admin'),
    (USER_ROLE_STAFF, 'Staff'),
)

# Booking status
BOOKING_STATUS_PENDING = 'pending'
BOOKING_STATUS_CONFIRMED = 'confirmed'
BOOKING_STATUS_COMPLETED = 'completed'
BOOKING_STATUS_CANCELLED = 'cancelled'

BOOKING_STATUSES = (
    (BOOKING_STATUS_PENDING, 'Pending'),
    (BOOKING_STATUS_CONFIRMED, 'Confirmed'),
    (BOOKING_STATUS_COMPLETED, 'Completed'),
    (BOOKING_STATUS_CANCELLED, 'Cancelled'),
)

# Time periods for analytics
DAYS_RECENT = 30
DAYS_LAST_WEEK = 7
MONTHS_TREND = 6

# Pagination
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# File upload limits
MAX_UPLOAD_SIZE = 5 * 1024 * 1024  # 5MB

# Review ratings
MIN_RATING = 1
MAX_RATING = 5