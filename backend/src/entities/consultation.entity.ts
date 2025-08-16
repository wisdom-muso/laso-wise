import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  OneToOne,
  OneToMany,
  JoinColumn,
  Index,
  Generated,
} from 'typeorm';
import { User } from './user.entity';
import { Booking } from './booking.entity';
import { ConsultationParticipant } from './consultation-participant.entity';
import { ConsultationMessage } from './consultation-message.entity';
import { ConsultationRecording } from './consultation-recording.entity';
import { WaitingRoom } from './waiting-room.entity';
import { TechnicalIssue } from './technical-issue.entity';

export enum ConsultationStatus {
  SCHEDULED = 'scheduled',
  WAITING = 'waiting',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show',
}

export enum VideoProvider {
  JITSI = 'jitsi',
  ZOOM = 'zoom',
  GOOGLE_MEET = 'google_meet',
}

export enum ConnectionQuality {
  EXCELLENT = 'excellent',
  GOOD = 'good',
  FAIR = 'fair',
  POOR = 'poor',
}

@Entity('consultations')
@Index(['doctor', 'status'])
@Index(['patient', 'status'])
@Index(['scheduled_start'])
export class Consultation {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  // Video call configuration
  @Column({
    name: 'video_provider',
    type: 'enum',
    enum: VideoProvider,
    default: VideoProvider.JITSI,
  })
  videoProvider: VideoProvider;

  @Column({ name: 'meeting_id', nullable: true })
  meetingId: string;

  @Column({ name: 'meeting_url', nullable: true })
  meetingUrl: string;

  @Column({ name: 'meeting_password', nullable: true })
  meetingPassword: string;

  // Consultation details
  @Column({
    type: 'enum',
    enum: ConsultationStatus,
    default: ConsultationStatus.SCHEDULED,
  })
  status: ConsultationStatus;

  @Column({ name: 'scheduled_start', type: 'timestamp' })
  scheduledStart: Date;

  @Column({ name: 'actual_start', type: 'timestamp', nullable: true })
  actualStart: Date | null;

  @Column({ name: 'actual_end', type: 'timestamp', nullable: true })
  actualEnd: Date | null;

  @Column({ name: 'duration_minutes', nullable: true })
  durationMinutes: number | null;

  // Technical details
  @Column({ name: 'recording_enabled', default: false })
  recordingEnabled: boolean;

  @Column({ name: 'recording_url', nullable: true })
  recordingUrl: string;

  @Column({
    name: 'connection_quality',
    type: 'enum',
    enum: ConnectionQuality,
    nullable: true,
  })
  connectionQuality: ConnectionQuality;

  @Column({ type: 'text', nullable: true })
  notes: string;

  @Column({ name: 'consultation_fee', type: 'decimal', precision: 10, scale: 2, nullable: true })
  consultationFee: number;

  @Column({ name: 'payment_status', default: 'pending' })
  paymentStatus: string;

  @Column({ name: 'requires_follow_up', default: false })
  requiresFollowUp: boolean;

  @Column({ name: 'follow_up_date', type: 'date', nullable: true })
  followUpDate: Date | null;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => Booking, (booking) => booking.consultation, { nullable: true })
  @JoinColumn({ name: 'booking_id' })
  booking: Booking;

  @ManyToOne(() => User, (user) => user.consultationsAsDoctor)
  @JoinColumn({ name: 'doctor_id' })
  doctor: User;

  @ManyToOne(() => User, (user) => user.consultationsAsPatient)
  @JoinColumn({ name: 'patient_id' })
  patient: User;

  @OneToMany(() => ConsultationParticipant, (participant) => participant.consultation)
  participants: ConsultationParticipant[];

  @OneToMany(() => ConsultationMessage, (message) => message.consultation)
  messages: ConsultationMessage[];

  @OneToOne(() => ConsultationRecording, (recording) => recording.consultation)
  recording: ConsultationRecording;

  @OneToOne(() => WaitingRoom, (waitingRoom) => waitingRoom.consultation)
  waitingRoom: WaitingRoom;

  @OneToMany(() => TechnicalIssue, (issue) => issue.consultation)
  technicalIssues: TechnicalIssue[];

  // Virtual properties and methods
  isActive(): boolean {
    return this.status === ConsultationStatus.WAITING || this.status === ConsultationStatus.IN_PROGRESS;
  }

  canStart(): boolean {
    const now = new Date();
    const fifteenMinutesBefore = new Date(this.scheduledStart.getTime() - 15 * 60 * 1000);
    const oneHourAfter = new Date(this.scheduledStart.getTime() + 60 * 60 * 1000);
    
    return (
      this.status === ConsultationStatus.SCHEDULED &&
      now >= fifteenMinutesBefore &&
      now <= oneHourAfter
    );
  }

  startConsultation(): boolean {
    if (this.canStart()) {
      this.status = ConsultationStatus.IN_PROGRESS;
      this.actualStart = new Date();
      return true;
    }
    return false;
  }

  endConsultation(): boolean {
    if (this.status === ConsultationStatus.IN_PROGRESS) {
      this.actualEnd = new Date();
      this.status = ConsultationStatus.COMPLETED;
      
      if (this.actualStart) {
        const duration = this.actualEnd.getTime() - this.actualStart.getTime();
        this.durationMinutes = Math.floor(duration / 1000 / 60);
      }
      
      return true;
    }
    return false;
  }

  getStatusDisplay(): string {
    const statusDisplayMap = {
      [ConsultationStatus.SCHEDULED]: 'Scheduled',
      [ConsultationStatus.WAITING]: 'Waiting Room',
      [ConsultationStatus.IN_PROGRESS]: 'In Progress',
      [ConsultationStatus.COMPLETED]: 'Completed',
      [ConsultationStatus.CANCELLED]: 'Cancelled',
      [ConsultationStatus.NO_SHOW]: 'No Show',
    };
    return statusDisplayMap[this.status] || 'Unknown';
  }

  getStatusColor(): string {
    const statusColorMap = {
      [ConsultationStatus.SCHEDULED]: '#3b82f6',    // Blue
      [ConsultationStatus.WAITING]: '#f59e0b',      // Yellow
      [ConsultationStatus.IN_PROGRESS]: '#10b981',  // Green
      [ConsultationStatus.COMPLETED]: '#6b7280',    // Gray
      [ConsultationStatus.CANCELLED]: '#ef4444',    // Red
      [ConsultationStatus.NO_SHOW]: '#dc2626',      // Dark red
    };
    return statusColorMap[this.status] || '#6b7280';
  }

  getProviderDisplayName(): string {
    const providerNames = {
      [VideoProvider.JITSI]: 'Jitsi Meet',
      [VideoProvider.ZOOM]: 'Zoom',
      [VideoProvider.GOOGLE_MEET]: 'Google Meet',
    };
    return providerNames[this.videoProvider] || 'Unknown';
  }

  getDurationFormatted(): string {
    if (!this.durationMinutes) return 'N/A';
    
    const hours = Math.floor(this.durationMinutes / 60);
    const minutes = this.durationMinutes % 60;
    
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  }

  getConnectionQualityDisplay(): string {
    if (!this.connectionQuality) return 'Unknown';
    
    const qualityDisplayMap = {
      [ConnectionQuality.EXCELLENT]: 'Excellent',
      [ConnectionQuality.GOOD]: 'Good',
      [ConnectionQuality.FAIR]: 'Fair',
      [ConnectionQuality.POOR]: 'Poor',
    };
    return qualityDisplayMap[this.connectionQuality] || 'Unknown';
  }

  getConnectionQualityColor(): string {
    const qualityColorMap = {
      [ConnectionQuality.EXCELLENT]: '#10b981', // Green
      [ConnectionQuality.GOOD]: '#3b82f6',      // Blue
      [ConnectionQuality.FAIR]: '#f59e0b',      // Yellow
      [ConnectionQuality.POOR]: '#ef4444',      // Red
    };
    return qualityColorMap[this.connectionQuality] || '#6b7280';
  }

  hasRecording(): boolean {
    return !!this.recording && this.recording.isAccessible();
  }

  canJoinWaitingRoom(): boolean {
    const now = new Date();
    const thirtyMinutesBefore = new Date(this.scheduledStart.getTime() - 30 * 60 * 1000);
    const twoHoursAfter = new Date(this.scheduledStart.getTime() + 120 * 60 * 1000);
    
    return (
      this.status === ConsultationStatus.SCHEDULED &&
      now >= thirtyMinutesBefore &&
      now <= twoHoursAfter
    );
  }

  isOverdue(): boolean {
    if (this.status !== ConsultationStatus.SCHEDULED) return false;
    
    const now = new Date();
    const oneHourAfter = new Date(this.scheduledStart.getTime() + 60 * 60 * 1000);
    
    return now > oneHourAfter;
  }

  getTimeUntilStart(): number {
    const now = new Date();
    return Math.floor((this.scheduledStart.getTime() - now.getTime()) / 1000 / 60); // Minutes
  }

  getTimeUntilStartFormatted(): string {
    const minutes = this.getTimeUntilStart();
    
    if (minutes < 0) {
      return 'Overdue';
    } else if (minutes < 60) {
      return `${minutes}m`;
    } else {
      const hours = Math.floor(minutes / 60);
      const remainingMinutes = minutes % 60;
      return `${hours}h ${remainingMinutes}m`;
    }
  }

  markAsNoShow(): void {
    this.status = ConsultationStatus.NO_SHOW;
  }

  cancel(): void {
    this.status = ConsultationStatus.CANCELLED;
  }

  reschedule(newDate: Date): void {
    this.scheduledStart = newDate;
    this.status = ConsultationStatus.SCHEDULED;
    this.actualStart = null;
    this.actualEnd = null;
    this.durationMinutes = null;
  }

  updateConnectionQuality(quality: ConnectionQuality): void {
    this.connectionQuality = quality;
  }

  enableRecording(): void {
    this.recordingEnabled = true;
  }

  disableRecording(): void {
    this.recordingEnabled = false;
  }

  setFollowUpRequired(date?: Date): void {
    this.requiresFollowUp = true;
    if (date) {
      this.followUpDate = date;
    }
  }

  clearFollowUpRequired(): void {
    this.requiresFollowUp = false;
    this.followUpDate = null;
  }

  updateNotes(notes: string): void {
    this.notes = notes;
  }

  setConsultationFee(fee: number): void {
    this.consultationFee = fee;
  }

  updatePaymentStatus(status: string): void {
    this.paymentStatus = status;
  }
}