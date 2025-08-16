export { User, UserRole, Gender } from './user.entity';
export { Profile, BloodGroup } from './profile.entity';
export { Booking, AppointmentType, AppointmentStatus } from './booking.entity';
export { Consultation, ConsultationStatus, ConnectionQuality, VideoProvider } from './consultation.entity';
export { VitalRecord, VitalStatus } from './vital-record.entity';
export { VitalCategory } from './vital-category.entity';
export { Prescription } from './prescription.entity';
export { ProgressNote, NoteType } from './progress-note.entity';
export { Education } from './education.entity';
export { Experience } from './experience.entity';
export { Review } from './review.entity';
export { Specialty } from './specialty.entity';
export { SoapNote } from './soap-note.entity';
export { EHRRecord } from './ehr-record.entity';
export { MobileClinicRequest, MobileClinicNotification, MobileClinicStatus } from './mobile-clinic.entity';
export { AuditLog, AuditAction } from './audit-log.entity';

// Telemedicine entities
export { ConsultationParticipant, ParticipantRole } from './consultation-participant.entity';
export { ConsultationMessage, MessageType } from './consultation-message.entity';
export { ConsultationRecording } from './consultation-recording.entity';
export { WaitingRoom } from './waiting-room.entity';
export { TechnicalIssue, IssueType, IssueSeverity } from './technical-issue.entity';
export { VideoProviderConfig, VideoProvider as VideoProviderEnum } from './video-provider-config.entity';