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
import { Consultation } from './consultation.entity';
import { Prescription } from './prescription.entity';
import { ProgressNote } from './progress-note.entity';

export enum AppointmentType {
  IN_PERSON = 'in_person',
  VIRTUAL = 'virtual',
}

export enum AppointmentStatus {
  PENDING = 'pending',
  CONFIRMED = 'confirmed',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show',
}

export enum VideoProvider {
  JITSI = 'jitsi',
  ZOOM = 'zoom',
  GOOGLE_MEET = 'google_meet',
}

@Entity('bookings')
@Index(['doctor', 'appointmentDate', 'appointmentTime'], { unique: true })
export class Booking {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'appointment_date', type: 'date' })
  appointmentDate: Date;

  @Column({ name: 'appointment_time', type: 'time' })
  appointmentTime: string;

  @Column({
    name: 'appointment_type',
    type: 'enum',
    enum: AppointmentType,
    default: AppointmentType.IN_PERSON,
  })
  appointmentType: AppointmentType;

  @Column({
    type: 'enum',
    enum: AppointmentStatus,
    default: AppointmentStatus.PENDING,
  })
  status: AppointmentStatus;

  @Column({ name: 'consultation_notes', type: 'text', nullable: true })
  consultationNotes: string;

  @Column({
    name: 'preferred_video_provider',
    type: 'enum',
    enum: VideoProvider,
    nullable: true,
  })
  preferredVideoProvider: VideoProvider;

  @CreateDateColumn({ name: 'booking_date' })
  bookingDate: Date;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.appointments)
  @JoinColumn({ name: 'doctor_id' })
  doctor: User;

  @ManyToOne(() => User, (user) => user.patientAppointments)
  @JoinColumn({ name: 'patient_id' })
  patient: User;

  @OneToOne(() => Consultation, (consultation) => consultation.booking)
  consultation: Consultation;

  @OneToOne(() => Prescription, (prescription) => prescription.booking)
  prescription: Prescription;

  @OneToMany(() => ProgressNote, (progressNote) => progressNote.booking)
  progressNotes: ProgressNote[];

  // Virtual properties
  isVirtual(): boolean {
    return this.appointmentType === AppointmentType.VIRTUAL;
  }

  hasConsultation(): boolean {
    return !!this.consultation;
  }

  getAppointmentDateTime(): Date {
    const [hours, minutes] = this.appointmentTime.split(':').map(Number);
    const appointmentDateTime = new Date(this.appointmentDate);
    appointmentDateTime.setHours(hours, minutes, 0, 0);
    return appointmentDateTime;
  }

  canBeStarted(): boolean {
    const now = new Date();
    const appointmentDateTime = this.getAppointmentDateTime();
    const fifteenMinutesBefore = new Date(appointmentDateTime.getTime() - 15 * 60 * 1000);
    const oneHourAfter = new Date(appointmentDateTime.getTime() + 60 * 60 * 1000);
    
    return (
      this.status === AppointmentStatus.CONFIRMED &&
      now >= fifteenMinutesBefore &&
      now <= oneHourAfter
    );
  }
}