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

@Entity('reviews')
@Index(['doctor', 'patient'], { unique: true })
export class Review {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ type: 'tinyint', unsigned: true })
  rating: number; // 1-5 rating

  @Column({ type: 'text' })
  comment: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.doctorReviews)
  @JoinColumn({ name: 'doctor_id' })
  doctor: User;

  @ManyToOne(() => User, (user) => user.patientReviews)
  @JoinColumn({ name: 'patient_id' })
  patient: User;
}