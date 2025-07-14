from django.urls import path
from .views import (
    RestaurantListView, RestaurantDetailView, RestaurantMenuView,
    OrderCreateView, RestaurantOrderListView, OrderDetailView, OrderStatusUpdateView, RegisterView
)
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework.permissions import AllowAny

schema_view = get_schema_view(
    openapi.Info(
        title="Food Ordering API",
        default_version='v1',
        description="Food Ordering API documentation",
        terms_of_service="https://www.example.com/terms/",
        contact=openapi.Contact(email="szoke.tamas03@gmail.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[AllowAny],
)


urlpatterns = [
    path('restaurants/', RestaurantListView.as_view(), name='restaurant-list'),
    path('restaurants/<int:pk>/', RestaurantDetailView.as_view(), name='restaurant-detail'),
    path('restaurants/<int:pk>/menu/', RestaurantMenuView.as_view(), name='restaurant-menu'),
    path('orders/', OrderCreateView.as_view(), name='order-create'),
    path('orders/list/', RestaurantOrderListView.as_view(), name='restaurant-orders'),
    path('orders/<int:pk>/', OrderDetailView.as_view(), name='order-detail'),
    path('orders/<int:pk>/status/', OrderStatusUpdateView.as_view(), name='order-status-update'),
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/register/', RegisterView.as_view(), name='register'),
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('openapi/', schema_view.without_ui(cache_timeout=0), name='schema-openapi'),
]