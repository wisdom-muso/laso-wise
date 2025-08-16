import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { User } from './user.entity';
import { Booking } from './booking.entity';

export enum NoteType {
  CONSULTATION = 'consultation',
  FOLLOW_UP = 'follow_up',
  TREATMENT = 'treatment',
  OBSERVATION = 'observation',
  DISCHARGE = 'discharge',
}

@Entity('progress_notes')
export class ProgressNote {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({
    name: 'note_type',
    type: 'enum',
    enum: NoteType,
    default: NoteType.CONSULTATION,
  })
  noteType: NoteType;

  @Column({ length: 200 })
  title: string;

  @Column({ type: 'text' })
  content: string;

  @Column({ name: 'is_private', default: false })
  isPrivate: boolean;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => Booking, (booking) => booking.progressNotes)
  @JoinColumn({ name: 'booking_id' })
  booking: Booking;

  @ManyToOne(() => User, (user) => user.id)
  @JoinColumn({ name: 'doctor_id' })
  doctor: User;

  @ManyToOne(() => User, (user) => user.id)
  @JoinColumn({ name: 'patient_id' })
  patient: User;
}