import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';
import { User } from './user.entity';
import { Booking } from './booking.entity';

@Entity('soap_notes')
@Index(['patient', 'appointment'])
@Index(['created_by', 'created_at'])
export class SoapNote {
  @PrimaryGeneratedColumn()
  id: number;

  // SOAP Components
  @Column({ type: 'text' })
  subjective: string;

  @Column({ type: 'text' })
  objective: string;

  @Column({ type: 'text' })
  assessment: string;

  @Column({ type: 'text' })
  plan: string;

  @Column({ name: 'is_draft', default: false })
  isDraft: boolean;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.soapNotesAsPatient)
  @JoinColumn({ name: 'patient_id' })
  patient: User;

  @ManyToOne(() => Booking, (booking) => booking.soapNotes)
  @JoinColumn({ name: 'appointment_id' })
  appointment: Booking;

  @ManyToOne(() => User, (user) => user.soapNotesCreated)
  @JoinColumn({ name: 'created_by_id' })
  createdBy: User;

  // Helper methods
  isComplete(): boolean {
    return !!(this.subjective && this.objective && this.assessment && this.plan);
  }

  getCreatedByName(): string {
    return this.createdBy ? this.createdBy.getFullName() : 'Unknown';
  }

  getPatientName(): string {
    return this.patient ? this.patient.getFullName() : 'Unknown';
  }
}