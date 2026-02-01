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

# Dockerfile dev version
```
ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH=/opt/venv/bin:$PATH

# Create and activate virtual environment
RUN python -m venv /opt/venv && pip install --upgrade pip

# Install OS dependencies with retry logic
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
    libpq-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    gcc \
    libffi-dev && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get clean

# Create the code directory
WORKDIR /app

# Copy requirements
COPY requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install -r /tmp/requirements.txt

# Copy project code
COPY . /app

# Don't collect static files in dev (optional)
# RUN python manage.py collectstatic --noinput

# Development server command
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```




# Dockerfile prod version
```
ARG PYTHON_VERSION=3.12-slim-bullseye
FROM python:${PYTHON_VERSION}

# Create a virtual environment
RUN python -m venv /opt/venv

# Set the virtual environment as the current location
ENV PATH=/opt/venv/bin:$PATH

# Upgrade pip
RUN pip install --upgrade pip

# Set Python-related environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install os dependencies
RUN apt-get update && apt-get install -y \
    # for postgres
    libpq-dev \
    # for WeasyPrint (PDF generation)
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    # other
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create the code directory
RUN mkdir -p /app

# Set the working directory
WORKDIR /app

# Copy the requirements file (Updated path for root context)
COPY backend/requirements.txt /tmp/requirements.txt

# Install the Python project requirements
RUN pip install -r /tmp/requirements.txt

# Copy the project code into the container (Updated path for root context)
COPY backend /app

# Collect static files
RUN python manage.py collectstatic --noinput

# Create startup script
RUN printf "#!/bin/bash\n" > ./startup.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./startup.sh && \
    printf "python manage.py migrate --no-input\n" >> ./startup.sh && \
    printf "gunicorn config.wsgi:application --bind \"[::]:\$RUN_PORT\"\n" >> ./startup.sh

# Make the script executable
RUN chmod +x startup.sh

# Clean up apt cache
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run the startup script
CMD ./startup.sh
```