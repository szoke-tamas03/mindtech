# Offical python image
# This Dockerfile sets up a Python environment for a Django application
FROM python:3.11

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Workspace setup
WORKDIR /app

# Dependencies installation
COPY requirements.txt /app/
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the code
COPY . /app/

# (Optional step) for static files if using Django
# RUN python manage.py collectstatic --noinput

# Default command (can be overridden)
CMD ["gunicorn", "food_ordering.wsgi:application", "--bind", "0.0.0.0:8000"]

# Developer server: CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]