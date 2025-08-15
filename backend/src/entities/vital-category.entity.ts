import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToMany,
} from 'typeorm';
import { VitalRecord } from './vital-record.entity';

@Entity('vital_categories')
export class VitalCategory {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 100 })
  name: string;

  @Column({ type: 'text', nullable: true })
  description: string;

  @Column({ length: 50 })
  unit: string;

  @Column({ length: 50, default: 'fas fa-heartbeat' })
  icon: string;

  @Column({ length: 20, default: '#3498db' })
  color: string;

  @Column({ name: 'min_normal', type: 'float', nullable: true })
  minNormal: number;

  @Column({ name: 'max_normal', type: 'float', nullable: true })
  maxNormal: number;

  @Column({ name: 'min_critical', type: 'float', nullable: true })
  minCritical: number;

  @Column({ name: 'max_critical', type: 'float', nullable: true })
  maxCritical: number;

  @Column({ name: 'display_order', default: 0 })
  displayOrder: number;

  @Column({ name: 'is_active', default: true })
  isActive: boolean;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @OneToMany(() => VitalRecord, (record) => record.category)
  records: VitalRecord[];
}