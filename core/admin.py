from django.contrib import admin
from .models import User, Restaurant, MenuItem, Order, OrderItem

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_customer', 'is_restaurant', 'is_staff', 'is_superuser')
    list_filter = ('is_customer', 'is_restaurant', 'is_staff', 'is_superuser', )
    search_fields = ('username', 'email')

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'description')
    search_fields = ('name',)
    autocomplete_fields = ['user']

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'restaurant', 'price', 'description')
    list_filter = ('restaurant',)
    search_fields = ('name', 'restaurant__name')

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'restaurant', 'status', 'created_at')
    list_filter = ('status', 'restaurant')
    search_fields = ('customer__username', 'restaurant__name')
    autocomplete_fields = ['customer', 'restaurant']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'special_instructions')
    search_fields = ('order__id', 'menu_item__name')
    autocomplete_fields = ['order', 'menu_item']
    
# Admin felhasználó: Username: AdminMindtechUser, Password: admin