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

export enum AuditAction {
  CREATE = 'create',
  UPDATE = 'update',
  DELETE = 'delete',
  VIEW = 'view',
}

@Entity('audit_logs')
@Index(['user', 'timestamp'])
@Index(['model_name', 'timestamp'])
@Index(['action', 'timestamp'])
export class AuditLog {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({
    type: 'enum',
    enum: AuditAction,
  })
  action: AuditAction;

  @Column({ name: 'model_name', length: 100 })
  modelName: string;

  @Column({ name: 'object_id' })
  objectId: number;

  @Column({ name: 'object_repr', length: 200 })
  objectRepr: string;

  @Column({ type: 'jsonb', default: {} })
  changes: Record<string, any>;

  @Column({ name: 'ip_address', type: 'inet', nullable: true })
  ipAddress: string | null;

  @Column({ name: 'user_agent', type: 'text', nullable: true })
  userAgent: string | null;

  @CreateDateColumn({ name: 'timestamp' })
  timestamp: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.auditLogs, { nullable: true })
  @JoinColumn({ name: 'user_id' })
  user: User | null;

  // Helper methods
  static createLog(
    user: User | null,
    action: AuditAction,
    modelName: string,
    objectId: number,
    objectRepr: string,
    changes: Record<string, any> = {},
    ipAddress?: string,
    userAgent?: string,
  ): AuditLog {
    const auditLog = new AuditLog();
    auditLog.user = user;
    auditLog.action = action;
    auditLog.modelName = modelName;
    auditLog.objectId = objectId;
    auditLog.objectRepr = objectRepr;
    auditLog.changes = changes;
    auditLog.ipAddress = ipAddress || null;
    auditLog.userAgent = userAgent || null;
    return auditLog;
  }

  getActionDisplay(): string {
    const actionDisplayMap = {
      [AuditAction.CREATE]: 'Created',
      [AuditAction.UPDATE]: 'Updated',
      [AuditAction.DELETE]: 'Deleted',
      [AuditAction.VIEW]: 'Viewed',
    };
    return actionDisplayMap[this.action] || 'Unknown';
  }

  getUserDisplayName(): string {
    return this.user ? this.user.getFullName() : 'System';
  }

  getChangesSummary(): string {
    if (!this.changes || Object.keys(this.changes).length === 0) {
      return 'No changes recorded';
    }

    const changeCount = Object.keys(this.changes).length;
    const changedFields = Object.keys(this.changes).slice(0, 3).join(', ');
    
    if (changeCount <= 3) {
      return `Changed: ${changedFields}`;
    } else {
      return `Changed: ${changedFields} and ${changeCount - 3} more fields`;
    }
  }

  getTimeSinceAction(): string {
    const now = new Date();
    const diffInMs = now.getTime() - this.timestamp.getTime();
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