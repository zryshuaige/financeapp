# trading/admin.py
from django.contrib import admin
from .models import Stock, Favorite, Order, Position, CashAccount

admin.site.register(Stock)
admin.site.register(Favorite)
admin.site.register(Order)
admin.site.register(Position)
admin.site.register(CashAccount)
