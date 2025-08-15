import { Injectable, UnauthorizedException } from '@nestjs/common';
import { PassportStrategy } from '@nestjs/passport';
import { ExtractJwt, Strategy } from 'passport-jwt';
import { ConfigService } from '@nestjs/config';
import { AuthService } from '../auth.service';

// Custom token extractor that handles both "Bearer" and "Token" prefixes
const fromAuthHeaderAsTokenOrBearer = () => {
  return (request: any) => {
    let token = null;
    if (request && request.headers && request.headers.authorization) {
      const auth = request.headers.authorization;
      if (auth.startsWith('Token ')) {
        token = auth.substring(6); // Remove "Token " prefix
      } else if (auth.startsWith('Bearer ')) {
        token = auth.substring(7); // Remove "Bearer " prefix
      }
    }
    return token;
  };
};

@Injectable()
export class JwtStrategy extends PassportStrategy(Strategy) {
  constructor(
    private configService: ConfigService,
    private authService: AuthService,
  ) {
    super({
      jwtFromRequest: fromAuthHeaderAsTokenOrBearer(),
      ignoreExpiration: false,
      secretOrKey: configService.get<string>('JWT_SECRET') || 'default-secret-key',
    });
  }

  async validate(payload: any) {
    const user = await this.authService.findUserById(payload.sub);
    if (!user || !user.isActive) {
      throw new UnauthorizedException('User not found or inactive');
    }
    return { 
      userId: user.id, 
      username: user.username, 
      role: user.role,
      email: user.email 
    };
  }
}