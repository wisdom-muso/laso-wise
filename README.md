# Django + React Medical System

A containerized medical system with Django backend and React frontend.

## Quick Start

```bash
# Start the system
./run.sh start

# Create Django superuser (first time only)
./run.sh migrate
./run.sh superuser
```

## Access URLs

- **React Frontend:** http://localhost:3000
- **Django Backend:** http://localhost:8005
- **Django Admin:** http://localhost:8005/admin

## Commands

| Command | Description |
|---------|-------------|
| `./run.sh start` | Start all services |
| `./run.sh stop` | Stop all services |
| `./run.sh logs` | View logs |
| `./run.sh migrate` | Run database migrations |
| `./run.sh superuser` | Create Django admin user |
| `./run.sh shell django` | Django shell |
| `./run.sh shell frontend` | Frontend shell |
| `./run.sh help` | Show all commands |

## Requirements

- Docker with `docker compose` command
- 4GB+ RAM recommended

## Architecture

- **Django**: Backend API (Port 8005)
- **React**: Frontend UI (Port 3000)
- **Database**: SQLite (development)

That's it! The system is ready to use.