# trading/models.py
from django.db import models
from django.contrib.auth.models import User

class Stock(models.Model):
    symbol = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    price = models.FloatField(default=0.0)  # current price (mock or updated)

    def __str__(self):
        return f"{self.symbol} - {self.name}"

class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favorites")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name="favorited_by")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "stock")

class Order(models.Model):
    SIDE_CHOICES = (("BUY", "Buy"), ("SELL", "Sell"))
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="orders")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    side = models.CharField(max_length=4, choices=SIDE_CHOICES)
    quantity = models.IntegerField()
    price = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

class Position(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="positions")
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    avg_price = models.FloatField()

    class Meta:
        unique_together = ("user", "stock")

class CashAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="cash_account")
    balance = models.FloatField(default=100000.0)
    is_vip = models.BooleanField(default=False)   # 新增字段



from django.db import models
from django.contrib.auth.models import User

class MediaResource(models.Model):
    """
    用于管理图片/视频资源（可在 admin 中上传或通过 API 上传）
    """
    UPLOAD_TYPE = (("image","image"),("video","video"))
    title = models.CharField(max_length=150)
    file = models.FileField(upload_to="resources/%Y/%m/%d/")
    file_type = models.CharField(max_length=10, choices=UPLOAD_TYPE, default="image")
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class AIConversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_conversations")
    title = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

class AIMessage(models.Model):
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=20)  # "user" or "bot"
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
