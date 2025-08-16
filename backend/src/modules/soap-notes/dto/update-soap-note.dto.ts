import { PartialType } from '@nestjs/mapped-types';
import { CreateSoapNoteDto } from './create-soap-note.dto';
import { IsOptional, IsString, IsBoolean } from 'class-validator';

export class UpdateSoapNoteDto extends PartialType(CreateSoapNoteDto) {
  @IsOptional()
  @IsString({ message: 'Subjective must be a string' })
  subjective?: string;

  @IsOptional()
  @IsString({ message: 'Objective must be a string' })
  objective?: string;

  @IsOptional()
  @IsString({ message: 'Assessment must be a string' })
  assessment?: string;

  @IsOptional()
  @IsString({ message: 'Plan must be a string' })
  plan?: string;

  @IsOptional()
  @IsBoolean({ message: 'isDraft must be a boolean' })
  isDraft?: boolean;
}