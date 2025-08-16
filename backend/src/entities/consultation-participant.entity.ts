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
import { Consultation } from './consultation.entity';

export enum ParticipantRole {
  DOCTOR = 'doctor',
  PATIENT = 'patient',
  OBSERVER = 'observer',
  ASSISTANT = 'assistant',
}

@Entity('consultation_participants')
@Index(['consultation', 'user'], { unique: true })
export class ConsultationParticipant {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({
    type: 'enum',
    enum: ParticipantRole,
  })
  role: ParticipantRole;

  @Column({ name: 'joined_at', type: 'timestamp', nullable: true })
  joinedAt: Date;

  @Column({ name: 'left_at', type: 'timestamp', nullable: true })
  leftAt: Date | null;

  @Column({ name: 'connection_issues', default: 0 })
  connectionIssues: number;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => Consultation, (consultation) => consultation.participants, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'consultation_id' })
  consultation: Consultation;

  @ManyToOne(() => User, (user) => user.consultationParticipants, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'user_id' })
  user: User;

  // Helper methods
  isCurrentlyJoined(): boolean {
    return !!this.joinedAt && !this.leftAt;
  }

  getSessionDuration(): number | null {
    if (!this.joinedAt) return null;
    
    const endTime = this.leftAt || new Date();
    return Math.floor((endTime.getTime() - this.joinedAt.getTime()) / 1000 / 60); // Duration in minutes
  }

  incrementConnectionIssues(): void {
    this.connectionIssues += 1;
  }

  markAsJoined(): void {
    this.joinedAt = new Date();
    this.leftAt = null;
  }

  markAsLeft(): void {
    this.leftAt = new Date();
  }
}