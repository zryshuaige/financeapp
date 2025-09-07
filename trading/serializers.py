# trading/serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Stock, Favorite, Order, Position, CashAccount, AIMessage, AIConversation


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ("username", "email", "password")
    def create(self, validated_data):
        user = User(username=validated_data["username"], email=validated_data.get("email",""))
        user.set_password(validated_data["password"])
        user.save()
        # create cash account
        CashAccount.objects.create(user=user, balance=100000.0)
        return user

class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = ("id", "symbol", "name", "price")

class FavoriteSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    stock_id = serializers.PrimaryKeyRelatedField(queryset=Stock.objects.all(), write_only=True, source="stock")
    class Meta:
        model = Favorite
        fields = ("id", "stock", "stock_id", "created_at")

class OrderSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    stock_id = serializers.PrimaryKeyRelatedField(queryset=Stock.objects.all(), write_only=True, source="stock")
    class Meta:
        model = Order
        fields = ("id", "stock", "stock_id", "side", "quantity", "price", "created_at")

class PositionSerializer(serializers.ModelSerializer):
    stock = StockSerializer(read_only=True)
    class Meta:
        model = Position
        fields = ("id", "stock", "quantity", "avg_price")

class CashAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashAccount
        fields = ("balance", "is_vip")



class AIMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIMessage
        fields = ("id","sender","content","created_at")

class AIConversationSerializer(serializers.ModelSerializer):
    messages = AIMessageSerializer(many=True, read_only=True)
    class Meta:
        model = AIConversation
        fields = ("id","title","created_at","messages")
