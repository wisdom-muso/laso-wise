import { IsString, IsOptional, IsObject, IsArray, IsNumber } from 'class-validator';

export class CreateEHRRecordDto {
  @IsNumber({}, { message: 'Patient ID must be a number' })
  patientId: number;

  @IsOptional()
  @IsString({ message: 'Allergies must be a string' })
  allergies?: string;

  @IsOptional()
  @IsString({ message: 'Medications must be a string' })
  medications?: string;

  @IsOptional()
  @IsString({ message: 'Medical history must be a string' })
  medicalHistory?: string;

  @IsOptional()
  @IsString({ message: 'Immunizations must be a string' })
  immunizations?: string;

  @IsOptional()
  @IsObject({ message: 'Lab results must be an object' })
  labResults?: Record<string, any>;

  @IsOptional()
  @IsObject({ message: 'Imaging results must be an object' })
  imagingResults?: Record<string, any>;

  @IsOptional()
  @IsArray({ message: 'Vital signs history must be an array' })
  vitalSignsHistory?: any[];

  @IsOptional()
  @IsArray({ message: 'Emergency contacts must be an array' })
  emergencyContacts?: any[];

  @IsOptional()
  @IsObject({ message: 'Insurance info must be an object' })
  insuranceInfo?: Record<string, any>;
}