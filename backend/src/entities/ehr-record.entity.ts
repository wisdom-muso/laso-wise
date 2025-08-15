import {
  Entity,
  PrimaryGeneratedColumn,
  Column,
  CreateDateColumn,
  UpdateDateColumn,
  OneToOne,
  ManyToOne,
  JoinColumn,
} from 'typeorm';
import { User } from './user.entity';

@Entity('ehr_records')
export class EHRRecord {
  @PrimaryGeneratedColumn()
  id: number;

  // Medical Information
  @Column({ type: 'text', nullable: true })
  allergies: string;

  @Column({ type: 'text', nullable: true })
  medications: string;

  @Column({ name: 'medical_history', type: 'text', nullable: true })
  medicalHistory: string;

  @Column({ type: 'text', nullable: true })
  immunizations: string;

  // Structured Data (using JSON for PostgreSQL)
  @Column({ name: 'lab_results', type: 'jsonb', default: {} })
  labResults: Record<string, any>;

  @Column({ name: 'imaging_results', type: 'jsonb', default: {} })
  imagingResults: Record<string, any>;

  @Column({ name: 'vital_signs_history', type: 'jsonb', default: [] })
  vitalSignsHistory: any[];

  @Column({ name: 'emergency_contacts', type: 'jsonb', default: [] })
  emergencyContacts: any[];

  @Column({ name: 'insurance_info', type: 'jsonb', default: {} })
  insuranceInfo: Record<string, any>;

  @CreateDateColumn({ name: 'created_at' })
  createdAt: Date;

  @UpdateDateColumn({ name: 'updated_at' })
  updatedAt: Date;

  // Relationships
  @OneToOne(() => User, (user) => user.ehrRecord)
  @JoinColumn({ name: 'patient_id' })
  patient: User;

  @ManyToOne(() => User, (user) => user.ehrRecordsUpdated, { nullable: true })
  @JoinColumn({ name: 'last_updated_by_id' })
  lastUpdatedBy: User;

  // Helper methods
  addVitalSigns(vitalSignsData: any): void {
    if (!Array.isArray(this.vitalSignsHistory)) {
      this.vitalSignsHistory = [];
    }
    
    const dataWithTimestamp = {
      ...vitalSignsData,
      timestamp: new Date().toISOString(),
    };
    
    this.vitalSignsHistory.push(dataWithTimestamp);
  }

  addLabResult(testName: string, resultData: any): void {
    if (!this.labResults || typeof this.labResults !== 'object') {
      this.labResults = {};
    }
    
    if (!this.labResults[testName]) {
      this.labResults[testName] = [];
    }
    
    const dataWithTimestamp = {
      ...resultData,
      timestamp: new Date().toISOString(),
    };
    
    this.labResults[testName].push(dataWithTimestamp);
  }

  addImagingResult(studyType: string, resultData: any): void {
    if (!this.imagingResults || typeof this.imagingResults !== 'object') {
      this.imagingResults = {};
    }
    
    if (!this.imagingResults[studyType]) {
      this.imagingResults[studyType] = [];
    }
    
    const dataWithTimestamp = {
      ...resultData,
      timestamp: new Date().toISOString(),
    };
    
    this.imagingResults[studyType].push(dataWithTimestamp);
  }

  addEmergencyContact(contactData: any): void {
    if (!Array.isArray(this.emergencyContacts)) {
      this.emergencyContacts = [];
    }
    
    this.emergencyContacts.push(contactData);
  }

  updateInsuranceInfo(insuranceData: any): void {
    this.insuranceInfo = { ...this.insuranceInfo, ...insuranceData };
  }

  getRecentVitalSigns(limit: number = 10): any[] {
    if (!Array.isArray(this.vitalSignsHistory)) {
      return [];
    }
    
    return this.vitalSignsHistory
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, limit);
  }

  getLatestLabResults(): Record<string, any> {
    if (!this.labResults || typeof this.labResults !== 'object') {
      return {};
    }
    
    const latest: Record<string, any> = {};
    
    Object.keys(this.labResults).forEach(testName => {
      const results = this.labResults[testName];
      if (Array.isArray(results) && results.length > 0) {
        latest[testName] = results
          .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
      }
    });
    
    return latest;
  }
}