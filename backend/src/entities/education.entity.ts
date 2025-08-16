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

@Entity('educations')
export class Education {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 300 })
  college: string;

  @Column({ length: 100 })
  degree: string;

  @Column({ name: 'year_of_completion', nullable: true })
  yearOfCompletion: number;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.educations)
  @JoinColumn({ name: 'user_id' })
  user: User;
}