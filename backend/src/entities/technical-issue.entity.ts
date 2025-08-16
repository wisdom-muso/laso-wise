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

export enum IssueType {
  AUDIO = 'audio',
  VIDEO = 'video',
  CONNECTION = 'connection',
  SCREEN_SHARE = 'screen_share',
  RECORDING = 'recording',
  OTHER = 'other',
}

export enum IssueSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

@Entity('technical_issues')
@Index(['consultation', 'issue_type'])
@Index(['reporter', 'created_at'])
@Index(['severity', 'resolved'])
export class TechnicalIssue {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({
    name: 'issue_type',
    type: 'enum',
    enum: IssueType,
  })
  issueType: IssueType;

  @Column({ type: 'text' })
  description: string;

  @Column({
    type: 'enum',
    enum: IssueSeverity,
    default: IssueSeverity.MEDIUM,
  })
  severity: IssueSeverity;

  @Column({ default: false })
  resolved: boolean;

  @Column({ name: 'resolution_notes', type: 'text', nullable: true })
  resolutionNotes: string;

  @Column({ name: 'resolved_at', type: 'timestamp', nullable: true })
  resolvedAt: Date;

  @Column({ name: 'auto_resolved', default: false })
  autoResolved: boolean;

  @Column({ name: 'device_info', type: 'jsonb', default: {} })
  deviceInfo: Record<string, any>;

  @Column({ name: 'browser_info', type: 'jsonb', default: {} })
  browserInfo: Record<string, any>;

  @Column({ name: 'network_info', type: 'jsonb', default: {} })
  networkInfo: Record<string, any>;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => Consultation, (consultation) => consultation.technicalIssues, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'consultation_id' })
  consultation: Consultation;

  @ManyToOne(() => User, (user) => user.reportedTechnicalIssues, { onDelete: 'CASCADE' })
  @JoinColumn({ name: 'reporter_id' })
  reporter: User;

  @ManyToOne(() => User, (user) => user.resolvedTechnicalIssues, { nullable: true })
  @JoinColumn({ name: 'resolved_by_id' })
  resolvedBy: User;

  // Helper methods
  getIssueTypeDisplay(): string {
    const typeDisplayMap = {
      [IssueType.AUDIO]: 'Audio Problem',
      [IssueType.VIDEO]: 'Video Problem',
      [IssueType.CONNECTION]: 'Connection Issue',
      [IssueType.SCREEN_SHARE]: 'Screen Share Problem',
      [IssueType.RECORDING]: 'Recording Issue',
      [IssueType.OTHER]: 'Other',
    };
    return typeDisplayMap[this.issueType] || 'Unknown';
  }

  getSeverityDisplay(): string {
    const severityDisplayMap = {
      [IssueSeverity.LOW]: 'Low',
      [IssueSeverity.MEDIUM]: 'Medium',
      [IssueSeverity.HIGH]: 'High',
      [IssueSeverity.CRITICAL]: 'Critical',
    };
    return severityDisplayMap[this.severity] || 'Unknown';
  }

  getSeverityColor(): string {
    const severityColorMap = {
      [IssueSeverity.LOW]: '#22c55e',      // Green
      [IssueSeverity.MEDIUM]: '#f59e0b',   // Yellow
      [IssueSeverity.HIGH]: '#ef4444',     // Red
      [IssueSeverity.CRITICAL]: '#7c2d12', // Dark red
    };
    return severityColorMap[this.severity] || '#6b7280';
  }

  getResolutionTime(): number | null {
    if (!this.resolved || !this.resolvedAt) return null;
    
    return Math.floor((this.resolvedAt.getTime() - this.createdAt.getTime()) / 1000 / 60); // Minutes
  }

  getFormattedResolutionTime(): string {
    const resolutionTime = this.getResolutionTime();
    if (!resolutionTime) return 'Not resolved';
    
    if (resolutionTime < 60) {
      return `${resolutionTime} minutes`;
    } else {
      const hours = Math.floor(resolutionTime / 60);
      const minutes = resolutionTime % 60;
      return `${hours}h ${minutes}m`;
    }
  }

  markAsResolved(resolvedBy: User, resolutionNotes?: string): void {
    this.resolved = true;
    this.resolvedAt = new Date();
    this.resolvedBy = resolvedBy;
    if (resolutionNotes) {
      this.resolutionNotes = resolutionNotes;
    }
    this.autoResolved = false;
  }

  markAsAutoResolved(): void {
    this.resolved = true;
    this.resolvedAt = new Date();
    this.autoResolved = true;
    this.resolutionNotes = 'Automatically resolved - issue no longer detected';
  }

  updateDeviceInfo(deviceInfo: Record<string, any>): void {
    this.deviceInfo = { ...this.deviceInfo, ...deviceInfo };
  }

  updateBrowserInfo(browserInfo: Record<string, any>): void {
    this.browserInfo = { ...this.browserInfo, ...browserInfo };
  }

  updateNetworkInfo(networkInfo: Record<string, any>): void {
    this.networkInfo = { ...this.networkInfo, ...networkInfo };
  }

  isCritical(): boolean {
    return this.severity === IssueSeverity.CRITICAL;
  }

  isHighPriority(): boolean {
    return this.severity === IssueSeverity.HIGH || this.severity === IssueSeverity.CRITICAL;
  }

  needsImmedateAttention(): boolean {
    return this.isHighPriority() && !this.resolved;
  }

  getIssueIcon(): string {
    const iconMap = {
      [IssueType.AUDIO]: '🔊',
      [IssueType.VIDEO]: '📹',
      [IssueType.CONNECTION]: '🌐',
      [IssueType.SCREEN_SHARE]: '🖥️',
      [IssueType.RECORDING]: '⏺️',
      [IssueType.OTHER]: '⚠️',
    };
    return iconMap[this.issueType] || '❓';
  }
}