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

@Entity('consultation_recordings')
export class ConsultationRecording {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'recording_id' })
  recordingId: string;

  @Column({ name: 'recording_url' })
  recordingUrl: string;

  @Column({ name: 'download_url', nullable: true })
  downloadUrl: string;

  @Column({ name: 'file_size_mb', type: 'float', nullable: true })
  fileSizeMb: number;

  @Column({ name: 'duration_seconds', nullable: true })
  durationSeconds: number;

  @Column({ name: 'expires_at', type: 'timestamp', nullable: true })
  expiresAt: Date;

  @Column({ name: 'is_processed', default: false })
  isProcessed: boolean;

  @Column({ name: 'is_available', default: true })
  isAvailable: boolean;

  @Column({ name: 'processing_status', nullable: true })
  processingStatus: string;

  @Column({ name: 'transcript', type: 'text', nullable: true })
  transcript: string;

  @Column({ name: 'thumbnail_url', nullable: true })
  thumbnailUrl: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => Consultation, (consultation) => consultation.recording, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'consultation_id' })
  consultation: Consultation;

  // Helper methods
  isExpired(): boolean {
    if (!this.expiresAt) return false;
    return new Date() > this.expiresAt;
  }

  isAccessible(): boolean {
    return this.isAvailable && this.isProcessed && !this.isExpired();
  }

  getDurationFormatted(): string {
    if (!this.durationSeconds) return 'Unknown';
    
    const hours = Math.floor(this.durationSeconds / 3600);
    const minutes = Math.floor((this.durationSeconds % 3600) / 60);
    const seconds = this.durationSeconds % 60;
    
    if (hours > 0) {
      return `${hours}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
    } else {
      return `${minutes}:${seconds.toString().padStart(2, '0')}`;
    }
  }

  getFileSizeFormatted(): string {
    if (!this.fileSizeMb) return 'Unknown';
    
    if (this.fileSizeMb >= 1024) {
      return `${(this.fileSizeMb / 1024).toFixed(1)} GB`;
    } else {
      return `${this.fileSizeMb.toFixed(1)} MB`;
    }
  }

  setExpiry(days: number): void {
    const expiryDate = new Date();
    expiryDate.setDate(expiryDate.getDate() + days);
    this.expiresAt = expiryDate;
  }

  markAsProcessed(): void {
    this.isProcessed = true;
    this.processingStatus = 'completed';
  }

  markAsUnavailable(): void {
    this.isAvailable = false;
  }

  updateProcessingStatus(status: string): void {
    this.processingStatus = status;
  }
}