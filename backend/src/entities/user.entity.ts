import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToOne,
  OneToMany,
  ManyToMany,
  JoinTable,
} from 'typeorm';
import { Exclude } from 'class-transformer';
import { Profile } from './profile.entity';
import { Booking } from './booking.entity';
import { VitalRecord } from './vital-record.entity';
import { Consultation } from './consultation.entity';
import { Education } from './education.entity';
import { Experience } from './experience.entity';
import { Review } from './review.entity';
import { Specialty } from './specialty.entity';

export enum UserRole {
  DOCTOR = 'doctor',
  PATIENT = 'patient',
  ADMIN = 'admin',
}

export enum Gender {
  MALE = 'male',
  FEMALE = 'female',
  OTHER = 'other',
}

@Entity('users')
export class User {
  @PrimaryGeneratedColumn()
  id: number;

  @Column({ unique: true, length: 30 })
  username: string;

  @Column({ unique: true })
  email: string;

  @Exclude()
  @Column()
  password: string;

  @Column({ name: 'first_name', length: 150, nullable: true })
  firstName: string;

  @Column({ name: 'last_name', length: 150, nullable: true })
  lastName: string;

  @Column({
    type: 'enum',
    enum: UserRole,
    default: UserRole.PATIENT,
  })
  role: UserRole;

  @Column({ name: 'registration_number', nullable: true })
  registrationNumber: number;

  @Column({ name: 'is_active', default: true })
  isActive: boolean;

  @Column({ name: 'is_staff', default: false })
  isStaff: boolean;

  @Column({ name: 'is_superuser', default: false })
  isSuperuser: boolean;

  @Column({ name: 'date_joined', type: 'timestamp', default: () => 'CURRENT_TIMESTAMP' })
  dateJoined: Date;

  @Column({ name: 'last_login', type: 'timestamp', nullable: true })
  lastLogin: Date;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => Profile, (profile) => profile.user, { cascade: true })
  profile: Profile;

  @OneToMany(() => Booking, (booking) => booking.doctor)
  appointments: Booking[];

  @OneToMany(() => Booking, (booking) => booking.patient)
  patientAppointments: Booking[];

  @OneToMany(() => VitalRecord, (vitalRecord) => vitalRecord.patient)
  vitalRecords: VitalRecord[];

  @OneToMany(() => VitalRecord, (vitalRecord) => vitalRecord.recordedBy)
  recordedVitals: VitalRecord[];

  @OneToMany(() => Consultation, (consultation) => consultation.doctor)
  consultationsAsDoctor: Consultation[];

  @OneToMany(() => Consultation, (consultation) => consultation.patient)
  consultationsAsPatient: Consultation[];

  @OneToMany(() => Education, (education) => education.user)
  educations: Education[];

  @OneToMany(() => Experience, (experience) => experience.user)
  experiences: Experience[];

  @OneToMany(() => Review, (review) => review.doctor)
  doctorReviews: Review[];

  @OneToMany(() => Review, (review) => review.patient)
  patientReviews: Review[];

  @ManyToMany(() => Specialty, (specialty) => specialty.doctors)
  @JoinTable({
    name: 'user_specialties',
    joinColumn: { name: 'user_id', referencedColumnName: 'id' },
    inverseJoinColumn: { name: 'specialty_id', referencedColumnName: 'id' },
  })
  specialties: Specialty[];

  // Virtual properties
  getFullName(): string {
    if (this.firstName && this.lastName) {
      return `${this.firstName} ${this.lastName}`.trim();
    }
    return this.username;
  }

  // Calculate average rating for doctors
  getAverageRating(): number {
    if (!this.doctorReviews || this.doctorReviews.length === 0) {
      return 0;
    }
    const sum = this.doctorReviews.reduce((acc, review) => acc + review.rating, 0);
    return sum / this.doctorReviews.length;
  }

  getRatingCount(): number {
    return this.doctorReviews ? this.doctorReviews.length : 0;
  }
}