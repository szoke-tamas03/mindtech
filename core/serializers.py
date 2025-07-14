from rest_framework import serializers
from .models import User, Restaurant, MenuItem, Order, OrderItem

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'is_customer', 'is_restaurant')

class RestaurantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Restaurant
        fields = ('id', 'user', 'name', 'description')

class MenuItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ('id', 'restaurant', 'name', 'price', 'description')

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'menu_item', 'quantity', 'special_instructions')

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    class Meta:
        model = Order
        fields = ('id', 'customer', 'restaurant', 'status', 'created_at', 'items')
        
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    is_customer = serializers.BooleanField()
    is_restaurant = serializers.BooleanField()

    class Meta:
        model = User
        fields = ("username", "email", "password", "is_customer", "is_restaurant")

    def validate(self, data):
        if data["is_customer"] == data["is_restaurant"]:
            raise serializers.ValidationError("Csak az egyik lehet igaz: is_customer vagy is_restaurant.")
        return data

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user