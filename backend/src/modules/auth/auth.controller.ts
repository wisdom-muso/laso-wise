import { 
  Controller, 
  Post, 
  Get, 
  Put, 
  Body, 
  UseGuards, 
  Request, 
  HttpCode, 
  HttpStatus,
  ValidationPipe,
  Query 
} from '@nestjs/common';
import { AuthService } from './auth.service';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';
import { JwtAuthGuard } from './guards/jwt-auth.guard';

@Controller('accounts')
export class AuthController {
  constructor(private authService: AuthService) {}

  @Post('api/login')
  @HttpCode(HttpStatus.OK)
  async login(@Body(ValidationPipe) loginDto: LoginDto) {
    return await this.authService.login(loginDto);
  }

  @Post('api/register')
  @HttpCode(HttpStatus.CREATED)
  async register(@Body(ValidationPipe) registerDto: RegisterDto) {
    return await this.authService.register(registerDto);
  }

  @Post('api/logout')
  @UseGuards(JwtAuthGuard)
  @HttpCode(HttpStatus.OK)
  async logout() {
    // For JWT tokens, logout is typically handled client-side by removing the token
    // This endpoint exists for API compatibility
    return { message: 'Logged out successfully' };
  }

  @Get('api/me')
  @UseGuards(JwtAuthGuard)
  async getProfile(@Request() req) {
    return await this.authService.getUserProfile(req.user.userId);
  }

  @Put('api/me/update')
  @UseGuards(JwtAuthGuard)
  async updateProfile(@Request() req, @Body() updateData: any) {
    return await this.authService.updateProfile(req.user.userId, updateData);
  }

  @Get('api/validate-token')
  async validateToken(@Query('token') token: string) {
    if (!token) {
      return { valid: false };
    }
    
    const isValid = await this.authService.validateToken(token);
    return { valid: isValid };
  }
}