import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  ManyToOne,
  JoinColumn,
  Index,
} from 'typeorm';
import { User } from './user.entity';
import { Consultation } from './consultation.entity';

export enum MessageType {
  TEXT = 'text',
  SYSTEM = 'system',
  FILE = 'file',
  PRESCRIPTION = 'prescription',
}

@Entity('consultation_messages')
@Index(['consultation', 'timestamp'])
@Index(['sender', 'timestamp'])
export class ConsultationMessage {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'text' })
  message: string;

  @Column({
    name: 'message_type',
    type: 'enum',
    enum: MessageType,
    default: MessageType.TEXT,
  })
  messageType: MessageType;

  @Column({ name: 'is_private', default: false })
  isPrivate: boolean;

  @Column({ name: 'file_url', nullable: true })
  fileUrl: string;

  @Column({ name: 'file_name', nullable: true })
  fileName: string;

  @Column({ name: 'file_size', nullable: true })
  fileSize: number;

  @CreateDateColumn({ name: 'timestamp' })
  timestamp: Date;

  // Relationships
  @ManyToOne(() => Consultation, (consultation) => consultation.messages, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'consultation_id' })
  consultation: Consultation;

  @ManyToOne(() => User, (user) => user.consultationMessages, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'sender_id' })
  sender: User;

  // Helper methods
  isFromDoctor(): boolean {
    return this.sender && this.sender.isDoctor();
  }

  isFromPatient(): boolean {
    return this.sender && this.sender.isPatient();
  }

  isSystemMessage(): boolean {
    return this.messageType === MessageType.SYSTEM;
  }

  isFileMessage(): boolean {
    return this.messageType === MessageType.FILE;
  }

  isPrescriptionMessage(): boolean {
    return this.messageType === MessageType.PRESCRIPTION;
  }

  canBeViewedBy(user: User): boolean {
    // Private messages can only be viewed by medical staff
    if (this.isPrivate) {
      return user.isDoctor() || user.isAdmin();
    }
    
    // All participants can view non-private messages
    return true;
  }

  getFormattedTimestamp(): string {
    return this.timestamp.toLocaleString();
  }

  getMessagePreview(maxLength: number = 50): string {
    if (this.messageType === MessageType.FILE) {
      return `📎 ${this.fileName || 'File'}`;
    }
    
    if (this.messageType === MessageType.PRESCRIPTION) {
      return `💊 Prescription shared`;
    }
    
    if (this.messageType === MessageType.SYSTEM) {
      return `🔔 ${this.message}`;
    }
    
    if (this.message.length <= maxLength) {
      return this.message;
    }
    
    return this.message.substring(0, maxLength) + '...';
  }
}