import { Injectable, UnauthorizedException, ConflictException, BadRequestException } from '@nestjs/common';
import { JwtService } from '@nestjs/jwt';
import { InjectRepository } from '@nestjs/typeorm';
import { Repository } from 'typeorm';
import * as bcrypt from 'bcryptjs';

import { User, Profile, UserRole } from '../../entities';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';

@Injectable()
export class AuthService {
  constructor(
    @InjectRepository(User)
    private usersRepository: Repository<User>,
    @InjectRepository(Profile)
    private profilesRepository: Repository<Profile>,
    private jwtService: JwtService,
  ) {}

  async validateUser(email: string, password: string): Promise<User | null> {
    const user = await this.usersRepository.findOne({
      where: { email },
      relations: ['profile'],
    });

    if (user && await bcrypt.compare(password, user.password)) {
      return user;
    }
    return null;
  }

  async login(loginDto: LoginDto) {
    const { email, password } = loginDto;
    
    if (!email || !password) {
      throw new BadRequestException('Email and password are required');
    }

    // Try to find user by email
    const user = await this.usersRepository.findOne({
      where: { email },
      relations: ['profile'],
    });

    if (!user) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Verify password
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      throw new UnauthorizedException('Invalid credentials');
    }

    // Update last login
    user.lastLogin = new Date();
    await this.usersRepository.save(user);

    // Generate JWT token
    const payload = { username: user.username, sub: user.id, role: user.role };
    const token = this.jwtService.sign(payload);

    return {
      token,
      user: {
        id: user.id,
        username: user.username,
        email: user.email,
        first_name: user.firstName,
        last_name: user.lastName,
        role: user.role,
        profile: user.profile ? {
          phone: user.profile.phone,
          avatar: user.profile.getAvatarUrl(),
          age: user.profile.getAge(),
          gender: user.profile.gender,
          city: user.profile.city,
          specialization: user.profile.specialization,
          price_per_consultation: user.profile.pricePerConsultation,
        } : null,
      },
    };
  }

  async register(registerDto: RegisterDto) {
    const { username, email, password, firstName, lastName, role } = registerDto;

    // Check if user already exists
    const existingUser = await this.usersRepository.findOne({
      where: [{ email }, { username }],
    });

    if (existingUser) {
      if (existingUser.email === email) {
        throw new ConflictException('A user with that email already exists.');
      }
      if (existingUser.username === username) {
        throw new ConflictException('A user with that username already exists.');
      }
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, 10);

    // Create user
    const user = this.usersRepository.create({
      username,
      email,
      password: hashedPassword,
      firstName,
      lastName,
      role: role || UserRole.PATIENT,
      isActive: true,
    });

    const savedUser = await this.usersRepository.save(user);

    // Create profile
    const profile = this.profilesRepository.create({
      user: savedUser,
    });
    await this.profilesRepository.save(profile);

    // Generate JWT token
    const payload = { username: user.username, sub: user.id, role: user.role };
    const token = this.jwtService.sign(payload);

    return {
      token,
      user: {
        id: savedUser.id,
        username: savedUser.username,
        email: savedUser.email,
        first_name: savedUser.firstName,
        last_name: savedUser.lastName,
        role: savedUser.role,
      },
    };
  }

  async findUserById(id: number): Promise<User | null> {
    return await this.usersRepository.findOne({
      where: { id },
      relations: ['profile'],
    });
  }

  async getUserProfile(userId: number) {
    const user = await this.usersRepository.findOne({
      where: { id: userId },
      relations: ['profile'],
    });

    if (!user) {
      throw new UnauthorizedException('User not found');
    }

    return {
      id: user.id,
      username: user.username,
      email: user.email,
      first_name: user.firstName,
      last_name: user.lastName,
      role: user.role,
      profile: user.profile ? {
        phone: user.profile.phone,
        avatar: user.profile.getAvatarUrl(),
        age: user.profile.getAge(),
        gender: user.profile.gender,
        city: user.profile.city,
        state: user.profile.state,
        country: user.profile.country,
        specialization: user.profile.specialization,
        price_per_consultation: user.profile.pricePerConsultation,
        is_available: user.profile.isAvailable,
        blood_group: user.profile.bloodGroup,
        allergies: user.profile.allergies,
        medical_conditions: user.profile.medicalConditions,
      } : null,
    };
  }

  async updateProfile(userId: number, updateData: any) {
    const user = await this.usersRepository.findOne({
      where: { id: userId },
      relations: ['profile'],
    });

    if (!user) {
      throw new UnauthorizedException('User not found');
    }

    // Update user fields
    if (updateData.firstName !== undefined) user.firstName = updateData.firstName;
    if (updateData.lastName !== undefined) user.lastName = updateData.lastName;
    if (updateData.email !== undefined) user.email = updateData.email;

    await this.usersRepository.save(user);

    // Update profile fields
    if (user.profile) {
      if (updateData.phone !== undefined) user.profile.phone = updateData.phone;
      if (updateData.dob !== undefined) user.profile.dob = updateData.dob;
      if (updateData.about !== undefined) user.profile.about = updateData.about;
      if (updateData.specialization !== undefined) user.profile.specialization = updateData.specialization;
      if (updateData.gender !== undefined) user.profile.gender = updateData.gender;
      if (updateData.address !== undefined) user.profile.address = updateData.address;
      if (updateData.city !== undefined) user.profile.city = updateData.city;
      if (updateData.state !== undefined) user.profile.state = updateData.state;
      if (updateData.postalCode !== undefined) user.profile.postalCode = updateData.postalCode;
      if (updateData.country !== undefined) user.profile.country = updateData.country;
      if (updateData.pricePerConsultation !== undefined) user.profile.pricePerConsultation = updateData.pricePerConsultation;
      if (updateData.bloodGroup !== undefined) user.profile.bloodGroup = updateData.bloodGroup;
      if (updateData.allergies !== undefined) user.profile.allergies = updateData.allergies;
      if (updateData.medicalConditions !== undefined) user.profile.medicalConditions = updateData.medicalConditions;

      await this.profilesRepository.save(user.profile);
    }

    return this.getUserProfile(userId);
  }

  async validateToken(token: string): Promise<boolean> {
    try {
      const decoded = this.jwtService.verify(token);
      const user = await this.findUserById(decoded.sub);
      return !!user && user.isActive;
    } catch (error) {
      return false;
    }
  }
}