# FROM python:3.11-slim

# ENV PYTHONDONTWRITEBYTECODE=1
# ENV PYTHONUNBUFFERED=1

# WORKDIR /app

# RUN apt-get update && apt-get install -y \
#     gcc \
#     libpq-dev \
#     libgobject-2.0-0 \
#     libpango-1.0-0 \
#     libpangoft2-1.0-0 \
#     libcairo2 \
#     libffi-dev \
#     && rm -rf /var/lib/apt/lists/*

# COPY requirements.txt .
# RUN pip install --upgrade pip && pip install -r requirements.txt

# COPY . .

# CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]


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

# Install os dependencies for our mini vm
RUN apt-get update && apt-get install -y \
    # for postgres
    libpq-dev \
    # for WeasyPrint (PDF generation)
    libcairo2 \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libgobject-2.0-0 \
    # other
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Create the code directory
RUN mkdir -p /app

# Set the working directory
WORKDIR /app

# Copy the requirements file
COPY requirements.txt /tmp/requirements.txt

# Copy the project code into the container
COPY . /app

# Install the Python project requirements
RUN pip install -r /tmp/requirements.txt

# Collect static files (database not needed for this)
RUN python manage.py collectstatic --noinput

# Create a bash script to run the Django project
# This script will execute at runtime when the database is available
RUN printf "#!/bin/bash\n" > ./startup.sh && \
    printf "RUN_PORT=\"\${PORT:-8000}\"\n\n" >> ./startup.sh && \
    printf "python manage.py migrate --no-input\n" >> ./startup.sh && \
    printf "gunicorn config.wsgi:application --bind \"[::]:\$RUN_PORT\"\n" >> ./startup.sh

# Make the bash script executable
RUN chmod +x startup.sh

# Clean up apt cache to reduce image size
RUN apt-get remove --purge -y \
    && apt-get autoremove -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Run the Django project via the startup script
# when the container starts
CMD ./startup.sh
