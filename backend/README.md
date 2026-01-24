# Dental Smiles Backend

This is the backend API for the Dental Smiles clinic management system, built with Django and Django REST Framework.

## Prerequisites

- Docker
- Docker Compose

## Setup & Running

### 1. Start the Server
Build and start the containers (Django, PostgreSQL, Redis, Celery):

```bash
nano ~/.docker/config.json

# Create migration files based on model changes
docker compose exec web python manage.py makemigrations

# Apply migrations to the database
docker compose exec web python manage.py migrate

# 3. Create Admin User
## To access the Django admin panel at http://localhost:8000/admin/:

docker compose exec web python manage.py createsuperuser

#   
docker compose exec web python manage.py collectstatic --noinput