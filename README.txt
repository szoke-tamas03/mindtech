

																			Food Ordering REST API

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Features

JWT Authentication (SimpleJWT): Secure, stateless login for all clients
Role management: Separate logic & endpoints for Customers and Restaurant users
CRUD operations for restaurants, menus, and orders
Fine-grained permissions per endpoint (only owners can view/update sensitive data)
Comprehensive unit tests: >95% coverage
Swagger (OpenAPI) docs at /api/docs/ and /api/redoc/
Production-ready: quick dev start with SQLite, easily switchable to PostgreSQL

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Technology stack

Python 3.x
Django (4.x+)
Django REST Framework
SimpleJWT / djangorestframework-simplejwt
drf-yasg (Swagger documentation)
SQLite (default) or PostgreSQL (prod-ready option)

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Setup Instructions
																			
git clone https://github.com/yourusername/food-ordering-api.git
cd food-ordering-api
python -m venv venv
source venv/bin/activate  # or Windows: venv\Scripts\activate
pip install -r requirements.txt

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Database configuration
																			
By default, uses SQLite (db.sqlite3 will be created locally):
No extra setup needed.

For PostgreSQL or other SQL engines:
Edit .env or set environment variables, then in food_ordering/settings.py you may use:


    
import os

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("DB_NAME", BASE_DIR / "db.sqlite3"),
        "USER": os.environ.get("DB_USER", ""),
        "PASSWORD": os.environ.get("DB_PASSWORD", ""),
        "HOST": os.environ.get("DB_HOST", ""),
        "PORT": os.environ.get("DB_PORT", ""),
    }
}

For PostgreSQL add to your environment:

DB_ENGINE=django.db.backends.postgresql
DB_NAME=foodorder
DB_USER=youruser
DB_PASSWORD=yourpass
DB_HOST=localhost
DB_PORT=5432

And install Postgres driver:

pip install psycopg2-binary

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Migrate and seed database
																			
python manage.py migrate
--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Create superuser (for Django admin)
python manage.py createsuperuser
																			
--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Run the server
																			
python manage.py runserver

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			REST API Overview
																		
All endpoints (except registration & login) require JWT access token in the header:

Authorization: Bearer <access token>

Swagger UI: /api/docs/
ReDoc: /api/redoc/

See detailed endpoint documentation in the API docs.

Most important endpoints:
Authentication
POST /api/auth/register/ – Register new customer/restaurant user
POST /api/auth/login/ – Obtain JWT access/refresh token
POST /api/auth/refresh/ – Renew JWT access token using refresh
Restaurants
GET /api/restaurants/
GET /api/restaurants/<id>/
GET /api/restaurants/<id>/menu/
Orders
POST /api/orders/ – Customer places order (on their own behalf)
GET /api/orders/list/?restaurantId=<id> – Restaurant owners list their orders
GET /api/orders/<id>/
PATCH /api/orders/<id>/status/ – Restaurant owners update order status
See /api/docs/ for detailed schemas and sample responses.

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Testing
																			
Run the complete test suite:
    
python manage.py test core

Coverage:
   
coverage run manage.py test core
coverage report

Full coverage: >95%		
																	
--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Production tips
																			
This project is developed with SQLite by default, but you can switch to PostgreSQL or any RDBMS supported by Django.

Configure your database via environment variables
Install production-grade WSGI server for deployment (gunicorn, uWSGI, etc.)
Static/media files via WhiteNoise or alternative, as needed

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Questions?
																			
Contact: szoke.tamas03@gmail.com

--------------------------------------------------------------------------------------------------------------------------------------------------------------

																			Quick Start Demo
																			
python manage.py migrate
python manage.py runserver
# Register user → Login → Use API docs at /api/docs/

--------------------------------------------------------------------------------------------------------------------------------------------------------------																			