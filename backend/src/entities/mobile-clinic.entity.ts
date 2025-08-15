import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  ManyToOne,
  OneToMany,
  JoinColumn,
  Index,
} from 'typeorm';
import { User } from './user.entity';

export enum MobileClinicStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

@Entity('mobile_clinic_requests')
@Index(['patient', 'status'])
@Index(['requested_date', 'status'])
export class MobileClinicRequest {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ name: 'requested_date', type: 'date' })
  requestedDate: Date;

  @Column({ name: 'requested_time', type: 'time' })
  requestedTime: string;

  @Column({ type: 'text' })
  address: string;

  @Column({ type: 'text' })
  reason: string;

  @Column({ type: 'text', nullable: true })
  notes: string;

  @Column({
    type: 'enum',
    enum: MobileClinicStatus,
    default: MobileClinicStatus.PENDING,
  })
  status: MobileClinicStatus;

  @Column({ name: 'admin_notes', type: 'text', nullable: true })
  adminNotes: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.mobileClinicRequests)
  @JoinColumn({ name: 'patient_id' })
  patient: User;

  @OneToMany(() => MobileClinicNotification, (notification) => notification.request)
  notifications: MobileClinicNotification[];

  // Helper methods
  getRequestedDateTime(): Date {
    const [hours, minutes] = this.requestedTime.split(':').map(Number);
    const requestedDateTime = new Date(this.requestedDate);
    requestedDateTime.setHours(hours, minutes, 0, 0);
    return requestedDateTime;
  }

  canBeCancelled(): boolean {
    return this.status === MobileClinicStatus.PENDING || this.status === MobileClinicStatus.APPROVED;
  }

  canBeApproved(): boolean {
    return this.status === MobileClinicStatus.PENDING;
  }

  canBeCompleted(): boolean {
    return this.status === MobileClinicStatus.APPROVED;
  }

  getStatusColor(): string {
    const statusColors = {
      [MobileClinicStatus.PENDING]: '#f39c12',     // Orange
      [MobileClinicStatus.APPROVED]: '#2ecc71',    // Green
      [MobileClinicStatus.REJECTED]: '#e74c3c',    // Red
      [MobileClinicStatus.COMPLETED]: '#3498db',   // Blue
      [MobileClinicStatus.CANCELLED]: '#95a5a6',   // Gray
    };
    return statusColors[this.status] || '#95a5a6';
  }
}

@Entity('mobile_clinic_notifications')
@Index(['request', 'created_at'])
export class MobileClinicNotification {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'text' })
  message: string;

  @Column({ name: 'is_read', default: false })
  isRead: boolean;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  // Relationships
  @ManyToOne(() => MobileClinicRequest, (request) => request.notifications)
  @JoinColumn({ name: 'request_id' })
  request: MobileClinicRequest;

  // Helper methods
  markAsRead(): void {
    this.isRead = true;
  }

  getTimeAgo(): string {
    const now = new Date();
    const diffInMs = now.getTime() - this.createdAt.getTime();
    const diffInHours = Math.floor(diffInMs / (1000 * 60 * 60));
    const diffInDays = Math.floor(diffInHours / 24);

    if (diffInDays > 0) {
      return `${diffInDays} day${diffInDays > 1 ? 's' : ''} ago`;
    } else if (diffInHours > 0) {
      return `${diffInHours} hour${diffInHours > 1 ? 's' : ''} ago`;
    } else {
      const diffInMinutes = Math.floor(diffInMs / (1000 * 60));
      return `${diffInMinutes} minute${diffInMinutes > 1 ? 's' : ''} ago`;
    }
  }
}