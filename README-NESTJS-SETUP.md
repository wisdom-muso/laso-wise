# Laso Medical - NestJS + React Setup

This project has been migrated from Django to NestJS backend while keeping the existing React frontend.

## Architecture Overview

- **Frontend**: React with TypeScript, Vite, Tailwind CSS (port 3000)
- **Backend**: NestJS with TypeORM, JWT authentication (port 3001)
- **Database**: MySQL 8.0 (port 3306)

## Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- At least 4GB RAM available for containers

### 1. Start All Services
```bash
# Clone the repository and navigate to project root
cd /path/to/laso-medical

# Start all services with the new NestJS backend
docker-compose -f docker-compose.new.yml up -d

# View logs (optional)
docker-compose -f docker-compose.new.yml logs -f
```

### 2. Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:3001
- **Database**: localhost:3306 (username: laso_user, password: laso_password)

### 3. Stop Services
```bash
docker-compose -f docker-compose.new.yml down
```

## Development Setup

### Backend Development (NestJS)

1. **Install Dependencies**
```bash
cd backend
npm install
```

2. **Environment Configuration**
```bash
# Copy and configure environment variables
cp .env.example .env
# Edit .env with your database credentials
```

3. **Start MySQL Database**
```bash
docker run --name laso-mysql -e MYSQL_ROOT_PASSWORD=root -e MYSQL_DATABASE=laso_medical -p 3306:3306 -d mysql:8.0
```

4. **Run Backend**
```bash
# Development mode with hot reload
npm run start:dev

# Production mode
npm run build
npm run start:prod
```

### Frontend Development (React)

1. **Install Dependencies**
```bash
cd frontend
npm install
```

2. **Environment Configuration**
```bash
# Create environment file
echo "VITE_API_BASE=http://localhost:3001" > .env
```

3. **Run Frontend**
```bash
# Development mode with hot reload
npm run dev

# Build for production
npm run build
npm run preview
```

## API Endpoints

### Authentication
- `POST /accounts/api/login` - User login
- `POST /accounts/api/register` - User registration  
- `POST /accounts/api/logout` - User logout
- `GET /accounts/api/me` - Get current user profile
- `PUT /accounts/api/me/update` - Update user profile
- `GET /accounts/api/validate-token?token=<token>` - Validate JWT token

### Core Features
The following Django features have been replicated in NestJS:

- **User Management**: Custom user model with roles (patient/doctor/admin)
- **Profile Management**: User profiles with medical information
- **Authentication**: JWT token-based auth compatible with frontend
- **Database Models**: All Django models converted to TypeORM entities

### Entities Created
- `User` - Custom user with roles and authentication
- `Profile` - User profile information
- `Booking` - Appointment scheduling
- `Consultation` - Telemedicine consultations
- `VitalRecord` - Patient vital signs
- `VitalCategory` - Vital sign categories
- `Prescription` - Medical prescriptions
- `ProgressNote` - Clinical progress notes
- `Education` - Doctor education history
- `Experience` - Doctor work experience
- `Review` - Doctor reviews and ratings
- `Specialty` - Medical specializations

## Database Schema

The NestJS backend uses TypeORM with MySQL and automatically creates tables based on entities. The schema closely matches the original Django models.

### Key Features:
- **Automatic Migrations**: TypeORM synchronization in development
- **Relationship Mapping**: Foreign keys and associations preserved
- **Data Validation**: Class validators for input validation
- **Type Safety**: Full TypeScript support

## Authentication Flow

1. **Login**: User provides email/password
2. **JWT Generation**: Server creates JWT token with user payload
3. **Token Storage**: Frontend stores token in localStorage
4. **API Requests**: Token sent as `Authorization: Token <jwt>` header
5. **Validation**: Server validates token on protected routes

## Migration from Django

### What's Migrated:
✅ All Django models → TypeORM entities  
✅ Authentication system → JWT with same API endpoints  
✅ User management → Complete user/profile system  
✅ Database schema → MySQL with TypeORM  
✅ API endpoints → NestJS controllers with same paths  
✅ Docker setup → Multi-container orchestration  

### Still Needed:
🔄 Booking/appointment management module  
🔄 Vitals tracking module  
🔄 Telemedicine features  
🔄 Doctor management endpoints  
🔄 Data migration from Django database  

## Environment Variables

### Backend (.env)
```env
NODE_ENV=development
PORT=3001
DB_HOST=localhost
DB_PORT=3306
DB_USERNAME=laso_user
DB_PASSWORD=laso_password
DB_DATABASE=laso_medical
JWT_SECRET=your-super-secret-jwt-key
JWT_EXPIRES_IN=7d
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env)
```env
VITE_API_BASE=http://localhost:3001
NODE_ENV=development
```

## Troubleshooting

### Common Issues:

1. **Port Conflicts**
   - Frontend: Change port in package.json or use `npm run dev -- --port 3001`
   - Backend: Update PORT in .env file

2. **Database Connection**
   - Ensure MySQL is running and accessible
   - Check database credentials in backend/.env
   - Verify database exists and user has permissions

3. **CORS Issues**
   - Backend CORS is configured for localhost:3000
   - Update CORS origins in main.ts if using different URLs

4. **Authentication Issues**
   - Clear localStorage and retry login
   - Check JWT secret consistency between services
   - Verify token format in API requests

## Docker Compose Services

- **mysql**: MySQL 8.0 database with health checks
- **nestjs-backend**: NestJS API server with TypeORM
- **react-frontend**: React SPA served by Nginx

### Health Checks:
All services include health checks to ensure proper startup order and monitoring.

## Next Steps

1. **Complete Module Migration**: Implement remaining Django app functionality
2. **Data Migration**: Create scripts to migrate existing Django data
3. **Testing**: Add comprehensive test coverage
4. **Deployment**: Configure for production environment
5. **Monitoring**: Add logging and monitoring solutions

## Support

For issues with the NestJS migration, check:
- Backend logs: `docker-compose logs nestjs-backend`  
- Frontend logs: `docker-compose logs react-frontend`
- Database logs: `docker-compose logs mysql`