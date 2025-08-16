import {
  Controller,
  Get,
  Post,
  Body,
  Patch,
  Param,
  Delete,
  UseGuards,
  Request,
  Query,
  ParseIntPipe,
  ValidationPipe,
  HttpCode,
  HttpStatus,
} from '@nestjs/common';
import { SoapNotesService } from './soap-notes.service';
import { CreateSoapNoteDto } from './dto/create-soap-note.dto';
import { UpdateSoapNoteDto } from './dto/update-soap-note.dto';
import { JwtAuthGuard } from '../auth/guards/jwt-auth.guard';
import { RolesGuard } from '../auth/guards/roles.guard';
import { Roles } from '../auth/decorators/roles.decorator';
import { UserRole } from '../../entities';

@Controller('core/api/soap-notes')
@UseGuards(JwtAuthGuard)
export class SoapNotesController {
  constructor(private readonly soapNotesService: SoapNotesService) {}

  @Post()
  @UseGuards(RolesGuard)
  @Roles(UserRole.DOCTOR)
  @HttpCode(HttpStatus.CREATED)
  async create(
    @Body(ValidationPipe) createSoapNoteDto: CreateSoapNoteDto,
    @Request() req,
  ) {
    return await this.soapNotesService.create(createSoapNoteDto, req.user, req);
  }

  @Get()
  async findAll(
    @Request() req,
    @Query('page', new ParseIntPipe({ optional: true })) page?: number,
    @Query('limit', new ParseIntPipe({ optional: true })) limit?: number,
  ) {
    return await this.soapNotesService.findAll(req.user, page || 1, limit || 10);
  }

  @Get('patient/:patientId')
  async findByPatient(
    @Param('patientId', ParseIntPipe) patientId: number,
    @Request() req,
  ) {
    return await this.soapNotesService.findByPatient(patientId, req.user);
  }

  @Get('appointment/:appointmentId')
  async findByAppointment(
    @Param('appointmentId', ParseIntPipe) appointmentId: number,
    @Request() req,
  ) {
    return await this.soapNotesService.findByAppointment(appointmentId, req.user);
  }

  @Get(':id')
  async findOne(
    @Param('id', ParseIntPipe) id: number,
    @Request() req,
  ) {
    return await this.soapNotesService.findOne(id, req.user);
  }

  @Patch(':id')
  async update(
    @Param('id', ParseIntPipe) id: number,
    @Body(ValidationPipe) updateSoapNoteDto: UpdateSoapNoteDto,
    @Request() req,
  ) {
    return await this.soapNotesService.update(id, updateSoapNoteDto, req.user, req);
  }

  @Delete(':id')
  @HttpCode(HttpStatus.NO_CONTENT)
  async remove(
    @Param('id', ParseIntPipe) id: number,
    @Request() req,
  ) {
    await this.soapNotesService.remove(id, req.user, req);
  }
}