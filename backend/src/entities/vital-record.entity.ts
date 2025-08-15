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
import { VitalCategory } from './vital-category.entity';

export enum VitalStatus {
  CRITICAL_LOW = 'critical-low',
  CRITICAL_HIGH = 'critical-high',
  ABNORMAL_LOW = 'abnormal-low',
  ABNORMAL_HIGH = 'abnormal-high',
  NORMAL = 'normal',
}

@Entity('vital_records')
export class VitalRecord {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'float' })
  value: number;

  @Column({ name: 'secondary_value', type: 'float', nullable: true })
  secondaryValue: number;

  @Column({ type: 'text', nullable: true })
  notes: string;

  @Column({ name: 'is_professional_reading', default: false })
  isProfessionalReading: boolean;

  @CreateDateColumn({ name: 'recorded_at' })
  recordedAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.vitalRecords)
  @JoinColumn({ name: 'patient_id' })
  patient: User;

  @ManyToOne(() => VitalCategory, (category) => category.records)
  @JoinColumn({ name: 'category_id' })
  category: VitalCategory;

  @ManyToOne(() => User, (user) => user.recordedVitals, { nullable: true })
  @JoinColumn({ name: 'recorded_by_id' })
  recordedBy: User;

  // Virtual properties
  getStatus(): VitalStatus {
    if (!this.category) return VitalStatus.NORMAL;

    if (this.category.minCritical !== null && this.value < this.category.minCritical) {
      return VitalStatus.CRITICAL_LOW;
    }
    if (this.category.maxCritical !== null && this.value > this.category.maxCritical) {
      return VitalStatus.CRITICAL_HIGH;
    }
    if (this.category.minNormal !== null && this.value < this.category.minNormal) {
      return VitalStatus.ABNORMAL_LOW;
    }
    if (this.category.maxNormal !== null && this.value > this.category.maxNormal) {
      return VitalStatus.ABNORMAL_HIGH;
    }
    return VitalStatus.NORMAL;
  }

  getStatusDisplay(): string {
    const statusMap = {
      [VitalStatus.CRITICAL_LOW]: 'Critical Low',
      [VitalStatus.CRITICAL_HIGH]: 'Critical High',
      [VitalStatus.ABNORMAL_LOW]: 'Below Normal',
      [VitalStatus.ABNORMAL_HIGH]: 'Above Normal',
      [VitalStatus.NORMAL]: 'Normal',
    };
    return statusMap[this.getStatus()] || 'Unknown';
  }

  getStatusColor(): string {
    const statusColors = {
      [VitalStatus.CRITICAL_LOW]: '#e74c3c',
      [VitalStatus.CRITICAL_HIGH]: '#e74c3c',
      [VitalStatus.ABNORMAL_LOW]: '#f39c12',
      [VitalStatus.ABNORMAL_HIGH]: '#f39c12',
      [VitalStatus.NORMAL]: '#2ecc71',
    };
    return statusColors[this.getStatus()] || '#95a5a6';
  }

  getDisplayValue(): string {
    if (this.secondaryValue !== null) {
      return `${this.value}/${this.secondaryValue}`;
    }
    return this.value.toString();
  }
}