# trading/urls.py
from django.urls import path
from .views import (
    RegisterView, LoginView, StockListView,
    FavoriteListCreateView, FavoriteDeleteView,
    PlaceOrderView, PositionsView, NewsView, SectorsView, IndicesView, KlineView, ActivateVipView, AIQueryView
)
from rest_framework.authtoken import views as drf_views

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("stocks/", StockListView.as_view(), name="stocks"),
    path("favorites/", FavoriteListCreateView.as_view(), name="favorites"),
    path("favorites/<int:pk>/", FavoriteDeleteView.as_view(), name="fav-del"),
    path("order/", PlaceOrderView.as_view(), name="order"),
    path("positions/", PositionsView.as_view(), name="positions"),
    path("news/", NewsView.as_view(), name="news"),
    path("sectors/", SectorsView.as_view(), name="sectors"),
    path("indices/", IndicesView.as_view(), name="indices"),
    path("kline/", KlineView.as_view(), name="kline"),
    path("ai/activate/", ActivateVipView.as_view(), name="ai-activate"),
    path("ai/query/", AIQueryView.as_view(), name="ai-query"),
]
