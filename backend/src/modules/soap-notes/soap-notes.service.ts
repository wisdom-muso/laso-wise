import { Injectable, NotFoundException, BadRequestException, ForbiddenException } from '@nestjs/common';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import { SoapNote, User, Booking, UserRole, AuditLog, AuditAction } from '../../entities';
import { CreateSoapNoteDto } from './dto/create-soap-note.dto';
import { UpdateSoapNoteDto } from './dto/update-soap-note.dto';

@Injectable()
export class SoapNotesService {
  constructor(
    @InjectRepository(SoapNote)
    private soapNotesRepository: Repository<SoapNote>,
    @InjectRepository(User)
    private usersRepository: Repository<User>,
    @InjectRepository(Booking)
    private bookingsRepository: Repository<Booking>,
    @InjectRepository(AuditLog)
    private auditLogRepository: Repository<AuditLog>,
  ) {}

  async create(createSoapNoteDto: CreateSoapNoteDto, createdBy: User, req?: any): Promise<SoapNote> {
    // Verify that the user is a doctor
    if (createdBy.role !== UserRole.DOCTOR) {
      throw new ForbiddenException('Only doctors can create SOAP notes');
    }

    // Verify that the appointment exists and belongs to the patient
    const appointment = await this.bookingsRepository.findOne({
      where: { id: createSoapNoteDto.appointmentId },
      relations: ['patient', 'doctor'],
    });

    if (!appointment) {
      throw new NotFoundException('Appointment not found');
    }

    // Verify that the doctor creating the SOAP note is the assigned doctor for the appointment
    if (appointment.doctor.id !== createdBy.id) {
      throw new ForbiddenException('You can only create SOAP notes for your own appointments');
    }

    // Verify that the patient ID matches the appointment's patient
    if (appointment.patient.id !== createSoapNoteDto.patientId) {
      throw new BadRequestException('Patient ID does not match the appointment patient');
    }

    // Check if a SOAP note already exists for this appointment by this doctor
    const existingSoapNote = await this.soapNotesRepository.findOne({
      where: {
        appointment: { id: createSoapNoteDto.appointmentId },
        createdBy: { id: createdBy.id },
      },
    });

    if (existingSoapNote) {
      throw new BadRequestException('A SOAP note already exists for this appointment');
    }

    // Create the SOAP note
    const soapNote = this.soapNotesRepository.create({
      subjective: createSoapNoteDto.subjective,
      objective: createSoapNoteDto.objective,
      assessment: createSoapNoteDto.assessment,
      plan: createSoapNoteDto.plan,
      isDraft: createSoapNoteDto.isDraft || false,
      patient: appointment.patient,
      appointment: appointment,
      createdBy: createdBy,
    });

    const savedSoapNote = await this.soapNotesRepository.save(soapNote);

    // Create audit log
    await this.createAuditLog(
      createdBy,
      AuditAction.CREATE,
      'SoapNote',
      savedSoapNote.id,
      `SOAP Note for ${appointment.patient.getFullName()}`,
      createSoapNoteDto,
      req,
    );

    return this.findOne(savedSoapNote.id);
  }

  async findAll(user: User, page: number = 1, limit: number = 10): Promise<{ data: SoapNote[], total: number, page: number, limit: number }> {
    const skip = (page - 1) * limit;
    let whereCondition: any = {};

    // Apply role-based filtering
    if (user.role === UserRole.PATIENT) {
      whereCondition.patient = { id: user.id };
    } else if (user.role === UserRole.DOCTOR) {
      whereCondition.createdBy = { id: user.id };
    }
    // Admins can see all SOAP notes (no additional filtering)

    const [data, total] = await this.soapNotesRepository.findAndCount({
      where: whereCondition,
      relations: ['patient', 'appointment', 'createdBy'],
      order: { createdAt: 'DESC' },
      skip,
      take: limit,
    });

    return { data, total, page, limit };
  }

  async findOne(id: number, user?: User): Promise<SoapNote> {
    const soapNote = await this.soapNotesRepository.findOne({
      where: { id },
      relations: ['patient', 'appointment', 'createdBy'],
    });

    if (!soapNote) {
      throw new NotFoundException('SOAP note not found');
    }

    // Check permissions
    if (user && !this.canUserAccessSoapNote(user, soapNote)) {
      throw new ForbiddenException('You do not have permission to access this SOAP note');
    }

    return soapNote;
  }

  async findByPatient(patientId: number, user: User): Promise<SoapNote[]> {
    // Check if user can access patient data
    if (!user.canAccessPatientData(patientId)) {
      throw new ForbiddenException('You do not have permission to access this patient\'s SOAP notes');
    }

    return this.soapNotesRepository.find({
      where: { patient: { id: patientId } },
      relations: ['patient', 'appointment', 'createdBy'],
      order: { createdAt: 'DESC' },
    });
  }

  async findByAppointment(appointmentId: number, user: User): Promise<SoapNote[]> {
    const appointment = await this.bookingsRepository.findOne({
      where: { id: appointmentId },
      relations: ['patient', 'doctor'],
    });

    if (!appointment) {
      throw new NotFoundException('Appointment not found');
    }

    // Check permissions - user must be the patient, doctor, or admin
    if (user.role === UserRole.PATIENT && appointment.patient.id !== user.id) {
      throw new ForbiddenException('You can only access SOAP notes for your own appointments');
    }
    if (user.role === UserRole.DOCTOR && appointment.doctor.id !== user.id) {
      throw new ForbiddenException('You can only access SOAP notes for your own appointments');
    }

    return this.soapNotesRepository.find({
      where: { appointment: { id: appointmentId } },
      relations: ['patient', 'appointment', 'createdBy'],
      order: { createdAt: 'DESC' },
    });
  }

  async update(id: number, updateSoapNoteDto: UpdateSoapNoteDto, user: User, req?: any): Promise<SoapNote> {
    const soapNote = await this.findOne(id);

    // Only the creator (doctor) can update SOAP notes
    if (soapNote.createdBy.id !== user.id && user.role !== UserRole.ADMIN) {
      throw new ForbiddenException('You can only update SOAP notes that you created');
    }

    // Track changes for audit log
    const originalData = {
      subjective: soapNote.subjective,
      objective: soapNote.objective,
      assessment: soapNote.assessment,
      plan: soapNote.plan,
      isDraft: soapNote.isDraft,
    };

    // Update the SOAP note
    Object.assign(soapNote, updateSoapNoteDto);
    const updatedSoapNote = await this.soapNotesRepository.save(soapNote);

    // Create audit log with changes
    const changes = this.getChanges(originalData, updateSoapNoteDto);
    await this.createAuditLog(
      user,
      AuditAction.UPDATE,
      'SoapNote',
      soapNote.id,
      `SOAP Note for ${soapNote.patient.getFullName()}`,
      changes,
      req,
    );

    return this.findOne(updatedSoapNote.id);
  }

  async remove(id: number, user: User, req?: any): Promise<void> {
    const soapNote = await this.findOne(id);

    // Only the creator (doctor) or admin can delete SOAP notes
    if (soapNote.createdBy.id !== user.id && user.role !== UserRole.ADMIN) {
      throw new ForbiddenException('You can only delete SOAP notes that you created');
    }

    // Create audit log before deletion
    await this.createAuditLog(
      user,
      AuditAction.DELETE,
      'SoapNote',
      soapNote.id,
      `SOAP Note for ${soapNote.patient.getFullName()}`,
      { deleted: true },
      req,
    );

    await this.soapNotesRepository.remove(soapNote);
  }

  private canUserAccessSoapNote(user: User, soapNote: SoapNote): boolean {
    // Admin can access all
    if (user.role === UserRole.ADMIN) {
      return true;
    }

    // Patient can access their own SOAP notes
    if (user.role === UserRole.PATIENT && soapNote.patient.id === user.id) {
      return true;
    }

    // Doctor can access SOAP notes they created
    if (user.role === UserRole.DOCTOR && soapNote.createdBy.id === user.id) {
      return true;
    }

    return false;
  }

  private async createAuditLog(
    user: User,
    action: AuditAction,
    modelName: string,
    objectId: number,
    objectRepr: string,
    changes: any,
    req?: any,
  ): Promise<void> {
    const auditLog = AuditLog.createLog(
      user,
      action,
      modelName,
      objectId,
      objectRepr,
      changes,
      req?.ip,
      req?.get('User-Agent'),
    );

    await this.auditLogRepository.save(auditLog);
  }

  private getChanges(original: any, updated: any): Record<string, any> {
    const changes: Record<string, any> = {};

    Object.keys(updated).forEach(key => {
      if (updated[key] !== undefined && original[key] !== updated[key]) {
        changes[key] = {
          from: original[key],
          to: updated[key],
        };
      }
    });

    return changes;
  }
}