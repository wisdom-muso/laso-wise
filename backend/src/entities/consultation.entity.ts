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
} from 'typeorm';
import { User } from './user.entity';
import { Booking } from './booking.entity';

export enum ConsultationStatus {
  SCHEDULED = 'scheduled',
  WAITING = 'waiting',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show',
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
@Index(['scheduledStart'])
export class Consultation {
  @PrimaryGeneratedColumn('uuid')
  id: string;

  @Column({ name: 'meeting_id', nullable: true })
  meetingId: string;

  @Column({ name: 'meeting_url', nullable: true })
  meetingUrl: string;

  @Column({ name: 'meeting_password', nullable: true })
  meetingPassword: string;

  @Column({
    type: 'enum',
    enum: ConsultationStatus,
    default: ConsultationStatus.SCHEDULED,
  })
  status: ConsultationStatus;

  @Column({ name: 'scheduled_start', type: 'timestamp' })
  scheduledStart: Date;

  @Column({ name: 'actual_start', type: 'timestamp', nullable: true })
  actualStart: Date;

  @Column({ name: 'actual_end', type: 'timestamp', nullable: true })
  actualEnd: Date;

  @Column({ name: 'duration_minutes', nullable: true })
  durationMinutes: number;

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

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => Booking, (booking) => booking.consultation)
  @JoinColumn({ name: 'booking_id' })
  booking: Booking;

  @ManyToOne(() => User, (user) => user.consultationsAsDoctor)
  @JoinColumn({ name: 'doctor_id' })
  doctor: User;

  @ManyToOne(() => User, (user) => user.consultationsAsPatient)
  @JoinColumn({ name: 'patient_id' })
  patient: User;

  // Virtual properties
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
        this.durationMinutes = Math.floor(duration / (1000 * 60));
      }
      return true;
    }
    return false;
  }
}