from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .models import Restaurant, MenuItem, Order, OrderItem
from .serializers import RestaurantSerializer, MenuItemSerializer, OrderSerializer, RegisterSerializer
from .permissions import IsRestaurantUser


class RestaurantListView(generics.ListAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    @swagger_auto_schema(
        operation_summary="List all restaurants",
        operation_description="Retrieve all available restaurants. Requires JWT authentication.",
        responses={200: RestaurantSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RestaurantDetailView(generics.RetrieveAPIView):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantSerializer

    @swagger_auto_schema(
        operation_summary="Get restaurant details",
        operation_description="Get detailed information for a specific restaurant by ID.",
        responses={200: RestaurantSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class RestaurantMenuView(generics.ListAPIView):
    serializer_class = MenuItemSerializer

    @swagger_auto_schema(
        operation_summary="List restaurant menu",
        operation_description="Get the menu items for a specific restaurant (by ID).",
        responses={200: MenuItemSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        restaurant_id = self.kwargs['pk']
        return MenuItem.objects.filter(restaurant_id=restaurant_id)


class OrderCreateView(APIView):
    @swagger_auto_schema(
        operation_summary="Create a new order",
        operation_description="Place a new order for the authenticated customer (self only).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["customerId", "restaurantId", "items"],
            properties={
                "customerId": openapi.Schema(type=openapi.TYPE_INTEGER, description="Customer/User ID (your own ID!)"),
                "restaurantId": openapi.Schema(type=openapi.TYPE_INTEGER, description="Target restaurant ID"),
                "items": openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            "itemId": openapi.Schema(type=openapi.TYPE_INTEGER, description="MenuItem ID"),
                            "quantity": openapi.Schema(type=openapi.TYPE_INTEGER, description="Quantity"),
                            "special_instructions": openapi.Schema(type=openapi.TYPE_STRING, description="Special instructions", default="")
                        }
                    ),
                    description="List of items to order"
                ),
            }
        ),
        responses={
            201: OrderSerializer,
            400: "Invalid input / MenuItem is not available",
            403: "You can only place an order as yourself"
        }
    )
    def post(self, request):
        customer_id = request.data.get('customerId')
        restaurant_id = request.data.get('restaurantId')
        items = request.data.get('items', [])

        if not (customer_id and restaurant_id and items):
            return Response({"error": "Missing data."}, status=status.HTTP_400_BAD_REQUEST)
        if int(customer_id) != request.user.id:
            return Response({"error": "You can only place an order as yourself!"}, status=status.HTTP_403_FORBIDDEN)

        try:
            restaurant = Restaurant.objects.get(id=restaurant_id)
        except Restaurant.DoesNotExist:
            return Response({"error": "No restaurant found."}, status=status.HTTP_400_BAD_REQUEST)

        order = Order.objects.create(
            customer_id=customer_id,
            restaurant=restaurant,
            status='received'
        )

        for item in items:
            try:
                menu_item = MenuItem.objects.get(id=item.get('itemId'), restaurant=restaurant)
            except MenuItem.DoesNotExist:
                order.delete()
                return Response({"error": f"MenuItem {item.get('itemId')} is not available for this restaurant."}, status=status.HTTP_400_BAD_REQUEST)
            OrderItem.objects.create(
                order=order,
                menu_item=menu_item,
                quantity=item.get('quantity', 1),
                special_instructions=item.get('special_instructions', "")
            )
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class RestaurantOrderListView(generics.ListAPIView):
    serializer_class = OrderSerializer

    @swagger_auto_schema(
        operation_summary="List orders for your restaurant",
        operation_description=(
            "If you are a restaurant user, list orders for your restaurant (optionally filter by restaurantId).\n"
            "If you are a customer, lists your own orders."
        ),
        manual_parameters=[
            openapi.Parameter('restaurantId', openapi.IN_QUERY, description="(Optional) Filter orders by restaurant ID", type=openapi.TYPE_INTEGER)
        ],
        responses={200: OrderSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        user = self.request.user
        restaurant_id = self.request.query_params.get('restaurantId')
        qs = Order.objects.all()
        if user.is_restaurant:
            if restaurant_id:
                qs = qs.filter(restaurant_id=restaurant_id, restaurant__user=user)
            else:
                qs = qs.filter(restaurant__user=user)
        elif user.is_customer:
            qs = qs.filter(customer=user)
        return qs


class OrderDetailView(generics.RetrieveAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    @swagger_auto_schema(
        operation_summary="Get order details",
        operation_description="Get order details (must be your order as customer, or for your restaurant as restaurant user).",
        responses={200: OrderSerializer, 403: "Forbidden"}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if user.is_customer and obj.customer != user:
            raise PermissionDenied("You can only view your own orders.")
        if user.is_restaurant and obj.restaurant.user != user:
            raise PermissionDenied("You can only view orders for your own restaurant.")
        return obj


class OrderStatusUpdateView(generics.UpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsRestaurantUser]

    @swagger_auto_schema(
        operation_summary="Update order status",
        operation_description="Change the status of an order. Only the owning restaurant user is allowed.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["status"],
            properties={
                "status": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="New status [received, preparing, ready, delivered]"
                )
            }
        ),
        responses={
            200: OrderSerializer,
            400: "Invalid status",
            403: "Only the owner restaurant user may update status"
        }
    )

    def partial_update(self, request, *args, **kwargs):
        order = self.get_object()
        user = request.user
        if order.restaurant.user != user:
            return Response({"error": "You can only modify your own orders!"}, status=status.HTTP_403_FORBIDDEN)
        new_status = request.data.get('status')
        if new_status not in ['received', 'preparing', 'ready', 'delivered']:
            return Response({"error": "Invalid status."}, status=status.HTTP_400_BAD_REQUEST)
        order.status = new_status
        order.save()
        return Response(OrderSerializer(order).data)

class RegisterView(APIView):
    permission_classes = []
    authentication_classes = []

    @swagger_auto_schema(
        operation_summary="Register a new user",
        operation_description="Register a new customer or restaurant user.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'email', 'password', 'is_customer', 'is_restaurant'],
            properties={
                "username": openapi.Schema(type=openapi.TYPE_STRING, description="Unique username"),
                "email": openapi.Schema(type=openapi.TYPE_STRING, description="Valid email address"),
                "password": openapi.Schema(type=openapi.TYPE_STRING, description="Password (min 6 characters)"),
                "is_customer": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Register as customer"),
                "is_restaurant": openapi.Schema(type=openapi.TYPE_BOOLEAN, description="Register as restaurant user")
            }
        ),
        responses={
            201: openapi.Response(
                description="Registration successful",
                examples={"application/json": {
                    "id": 5,
                    "username": "alice",
                    "email": "alice@example.com",
                    "is_customer": True,
                    "is_restaurant": False
                }}
            ),
            400: "Bad request (validation error)"
        }
    )

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_customer": user.is_customer,
                "is_restaurant": user.is_restaurant,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)