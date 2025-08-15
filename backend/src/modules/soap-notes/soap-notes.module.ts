import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { SoapNotesService } from './soap-notes.service';
import { SoapNotesController } from './soap-notes.controller';
import { SoapNote, User, Booking, AuditLog } from '../../entities';

@Module({
  imports: [TypeOrmModule.forFeature([SoapNote, User, Booking, AuditLog])],
  controllers: [SoapNotesController],
  providers: [SoapNotesService],
  exports: [SoapNotesService],
})
export class SoapNotesModule {}