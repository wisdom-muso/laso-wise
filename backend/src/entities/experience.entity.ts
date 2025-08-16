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

@Entity('experiences')
export class Experience {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ length: 300 })
  institution: string;

  @Column({ name: 'from_year', nullable: true })
  fromYear: number;

  @Column({ name: 'to_year', nullable: true })
  toYear: number;

  @Column({ name: 'working_here', default: false })
  workingHere: boolean;

  @Column({ length: 200, nullable: true })
  designation: string;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @ManyToOne(() => User, (user) => user.experiences)
  @JoinColumn({ name: 'user_id' })
  user: User;
}