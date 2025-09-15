# 🐘 PostgreSQL Setup for LASO Healthcare VPS

## The Problem
Your `.env` file is configured for PostgreSQL with Docker (`@db:5432`), but you're running directly on a VPS without Docker. The hostname `db` can't be resolved, causing the connection error.

## Solution Steps

### 1. Install and Setup PostgreSQL on VPS

Run the PostgreSQL setup script:
```bash
cd /root/laso-wise
./setup-postgresql-vps.sh
```

This script will:
- ✅ Install PostgreSQL on Ubuntu
- ✅ Create the `laso_healthcare` database
- ✅ Create the `laso_user` with password `laso2403`
- ✅ Update your `.env` file to use `localhost` instead of `db`
- ✅ Test the database connection

### 2. Your Updated .env Configuration

After running the script, your `.env` will be updated to:
```bash
# Before (Docker configuration)
DATABASE_URL=postgresql://laso_user:laso2403@db:5432/laso_healthcare

# After (VPS configuration)  
DATABASE_URL=postgresql://laso_user:laso2403@localhost:5432/laso_healthcare
```

### 3. Run Migrations

After PostgreSQL is set up:
```bash
./run-migrations.sh
```

### 4. Manual Setup (if script fails)

If the automated script doesn't work, here's the manual process:

#### Install PostgreSQL:
```bash
sudo apt update
sudo apt install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Create Database and User:
```bash
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE laso_healthcare;
CREATE USER laso_user WITH PASSWORD 'laso2403';
GRANT ALL PRIVILEGES ON DATABASE laso_healthcare TO laso_user;
ALTER USER laso_user CREATEDB;
\q
```

#### Update .env file:
```bash
nano .env
```

Change this line:
```bash
DATABASE_URL=postgresql://laso_user:laso2403@db:5432/laso_healthcare
```

To:
```bash
DATABASE_URL=postgresql://laso_user:laso2403@localhost:5432/laso_healthcare
```

#### Test Connection:
```bash
PGPASSWORD=laso2403 psql -h localhost -U laso_user -d laso_healthcare -c "SELECT version();"
```

### 5. Install Python PostgreSQL Dependencies

Make sure you have the required Python packages:
```bash
cd /root/laso-wise
source venv/bin/activate
pip install psycopg2-binary
```

### 6. Run Migrations and Create Admin

```bash
python manage.py migrate
python manage.py createsuperuser
```

## Troubleshooting

### Connection Refused Error
If you get "connection refused":
```bash
sudo systemctl status postgresql
sudo systemctl restart postgresql
```

### Authentication Failed
Check PostgreSQL authentication:
```bash
sudo nano /etc/postgresql/*/main/pg_hba.conf
```

Ensure this line exists:
```
local   all             all                                     md5
```

Then restart:
```bash
sudo systemctl restart postgresql
```

### Port Issues
Check if PostgreSQL is listening:
```bash
sudo netstat -tlnp | grep 5432
```

## Final Verification

After setup, verify everything works:
```bash
cd /root/laso-wise
source venv/bin/activate
python manage.py check --database default
python manage.py showmigrations
```

Your admin login should now work! 🎉