import { IsString, IsNotEmpty, IsOptional, IsBoolean, IsNumber } from 'class-validator';

export class CreateSoapNoteDto {
  @IsNumber({}, { message: 'Patient ID must be a number' })
  @IsNotEmpty({ message: 'Patient ID is required' })
  patientId: number;

  @IsNumber({}, { message: 'Appointment ID must be a number' })
  @IsNotEmpty({ message: 'Appointment ID is required' })
  appointmentId: number;

  @IsString({ message: 'Subjective must be a string' })
  @IsNotEmpty({ message: 'Subjective information is required' })
  subjective: string;

  @IsString({ message: 'Objective must be a string' })
  @IsNotEmpty({ message: 'Objective information is required' })
  objective: string;

  @IsString({ message: 'Assessment must be a string' })
  @IsNotEmpty({ message: 'Assessment is required' })
  assessment: string;

  @IsString({ message: 'Plan must be a string' })
  @IsNotEmpty({ message: 'Plan is required' })
  plan: string;

  @IsOptional()
  @IsBoolean({ message: 'isDraft must be a boolean' })
  isDraft?: boolean;
}