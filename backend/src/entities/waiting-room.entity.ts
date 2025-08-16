import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToOne,
  JoinColumn,
} from 'typeorm';
import { Consultation } from './consultation.entity';

@Entity('waiting_rooms')
export class WaitingRoom {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'patient_joined_at', type: 'timestamp', nullable: true })
  patientJoinedAt: Date;

  @Column({ name: 'doctor_notified_at', type: 'timestamp', nullable: true })
  doctorNotifiedAt: Date;

  @Column({ name: 'estimated_wait_minutes', default: 0 })
  estimatedWaitMinutes: number;

  @Column({ name: 'queue_position', default: 1 })
  queuePosition: number;

  @Column({ name: 'is_active', default: true })
  isActive: boolean;

  @Column({ name: 'patient_notes', type: 'text', nullable: true })
  patientNotes: string;

  @Column({ name: 'last_activity', type: 'timestamp', nullable: true })
  lastActivity: Date;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => Consultation, (consultation) => consultation.waitingRoom, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'consultation_id' })
  consultation: Consultation;

  // Helper methods
  isPatientWaiting(): boolean {
    return !!this.patientJoinedAt && !this.isDoctorNotified() && this.isActive;
  }

  isDoctorNotified(): boolean {
    return !!this.doctorNotifiedAt;
  }

  getActualWaitTime(): number {
    if (!this.patientJoinedAt) return 0;
    
    const endTime = this.doctorNotifiedAt || new Date();
    return Math.floor((endTime.getTime() - this.patientJoinedAt.getTime()) / 1000 / 60); // Minutes
  }

  getEstimatedWaitMessage(): string {
    if (this.estimatedWaitMinutes <= 0) {
      return 'You will be seen shortly';
    } else if (this.estimatedWaitMinutes < 60) {
      return `Estimated wait time: ${this.estimatedWaitMinutes} minutes`;
    } else {
      const hours = Math.floor(this.estimatedWaitMinutes / 60);
      const minutes = this.estimatedWaitMinutes % 60;
      return `Estimated wait time: ${hours}h ${minutes}m`;
    }
  }

  getQueueMessage(): string {
    if (this.queuePosition <= 1) {
      return 'You are next in line';
    } else {
      return `You are #${this.queuePosition} in the queue`;
    }
  }

  markPatientJoined(): void {
    this.patientJoinedAt = new Date();
    this.updateLastActivity();
  }

  markDoctorNotified(): void {
    this.doctorNotifiedAt = new Date();
    this.updateLastActivity();
  }

  updateEstimatedWait(minutes: number): void {
    this.estimatedWaitMinutes = Math.max(0, minutes);
    this.updateLastActivity();
  }

  updateQueuePosition(position: number): void {
    this.queuePosition = Math.max(1, position);
    this.updateLastActivity();
  }

  deactivate(): void {
    this.isActive = false;
    this.updateLastActivity();
  }

  addPatientNotes(notes: string): void {
    this.patientNotes = notes;
    this.updateLastActivity();
  }

  private updateLastActivity(): void {
    this.lastActivity = new Date();
  }

  isStale(thresholdMinutes: number = 60): boolean {
    if (!this.lastActivity) return false;
    
    const now = new Date();
    const diffMinutes = (now.getTime() - this.lastActivity.getTime()) / 1000 / 60;
    return diffMinutes > thresholdMinutes;
  }
}