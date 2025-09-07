# trading/views.py
import traceback

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from .models import Stock, Favorite, Order, Position, CashAccount, AIMessage, AIConversation
from .serializers import (RegisterSerializer, UserSerializer, StockSerializer,
                          FavoriteSerializer, OrderSerializer, PositionSerializer,
                          CashAccountSerializer, AIConversationSerializer)
from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes

# Register
class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user": UserSerializer(user).data})

# Login -> return token
class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        user = authenticate(username=username, password=password)
        if user:
            token, _ = Token.objects.get_or_create(user=user)
            return Response({"token": token.key, "user": UserSerializer(user).data})
        return Response({"detail":"Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

# Stocks listing (mock price)
class StockListView(generics.ListAPIView):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [permissions.AllowAny]

# Favorites: list, add, delete
class FavoriteListCreateView(generics.ListCreateAPIView):
    serializer_class = FavoriteSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related("stock")
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FavoriteDeleteView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def delete(self, request, pk):
        fav = get_object_or_404(Favorite, pk=pk, user=request.user)
        fav.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

# Orders -> place buy/sell (updates Position and CashAccount)
class PlaceOrderView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request):
        user = request.user

        # 接受 stock_id 或 symbol（优先 stock_id）
        stock_id = request.data.get("stock_id", None)
        symbol = request.data.get("symbol", None)

        if stock_id is None and not symbol:
            return Response({"detail":"需要提供 stock_id 或 symbol"}, status=400)

        # 解析数量/价格
        try:
            qty = int(request.data.get("quantity", 0))
        except (TypeError, ValueError):
            return Response({"detail":"quantity must be integer"}, status=400)
        try:
            price = float(request.data.get("price", 0.0))
        except (TypeError, ValueError):
            return Response({"detail":"price must be numeric"}, status=400)

        if qty <= 0 or price <= 0:
            return Response({"detail":"qty and price must be > 0"}, status=400)

        # 获取 Stock（优先 id，否则按 symbol）
        try:
            if stock_id is not None:
                stock = get_object_or_404(Stock, pk=int(stock_id))
            else:
                stock = get_object_or_404(Stock, symbol=symbol)
        except Exception as e:
            return Response({"detail": f"找不到对应股票: {str(e)}"}, status=400)

        cash = CashAccount.objects.select_for_update().get(user=user)

        # 交易规则：lot
        sym = (stock.symbol or "").strip()
        lot = 200 if sym.startswith("688") else 100
        if qty % lot != 0:
            return Response({"detail": f"下单数量必须为 {lot} 的整数倍（每手 {lot} 股）"}, status=400)

        total = qty * price

        if request.data.get("side") not in ("BUY", "SELL"):
            return Response({"detail":"side must be BUY or SELL"}, status=400)
        side = request.data.get("side")

        # BUY
        if side == "BUY":
            if cash.balance < total:
                return Response({"detail":"Insufficient funds"}, status=400)
            cash.balance -= total
            cash.save()
            pos, created = Position.objects.select_for_update().get_or_create(
                user=user, stock=stock, defaults={"quantity": qty, "avg_price": price}
            )
            if not created:
                new_total_qty = pos.quantity + qty
                new_avg = ((pos.avg_price * pos.quantity) + (price * qty)) / new_total_qty
                pos.quantity = new_total_qty
                pos.avg_price = new_avg
                pos.save()
        else:  # SELL
            pos = Position.objects.select_for_update().filter(user=user, stock=stock).first()
            if not pos or pos.quantity < qty:
                return Response({"detail":"Insufficient holdings"}, status=400)
            pos.quantity -= qty
            cash.balance += total
            cash.save()
            if pos.quantity == 0:
                pos.delete()
            else:
                pos.save()

        order = Order.objects.create(user=user, stock=stock, side=side, quantity=qty, price=price)
        return Response({"order": OrderSerializer(order).data, "cash": CashAccountSerializer(cash).data})

# Positions and account summary
# trading/views.py （只替换 PositionsView 部分）
from rest_framework import permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import PositionSerializer, CashAccountSerializer
from .models import Position, CashAccount
from django.shortcuts import get_object_or_404

# trading/views.py — 替换 PositionsView 为下面内容
class PositionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        positions = Position.objects.filter(user=user).select_related("stock")
        cash = CashAccount.objects.get(user=user)

        details = []
        total_market_value = 0.0
        total_unrealized_pl = 0.0

        for p in positions:
            market_price = float(p.stock.price or 0.0)
            avg_price = float(p.avg_price or 0.0)
            qty = int(p.quantity or 0)

            market_value = round(market_price * qty, 2)
            unrealized_pl = round((market_price - avg_price) * qty, 2)

            details.append({
                "position_id": p.id,
                "stock_id": p.stock.id,           # <-- 新增 stock_id
                "symbol": p.stock.symbol,
                "name": p.stock.name,
                "quantity": qty,
                "avg_price": round(avg_price, 2),
                "market_price": round(market_price, 2),
                "market_value": market_value,
                "unrealized_pl": unrealized_pl
            })

            total_market_value += market_value
            total_unrealized_pl += unrealized_pl

        total_market_value = round(total_market_value, 2)
        total_unrealized_pl = round(total_unrealized_pl, 2)

        return Response({
            "cash": CashAccountSerializer(cash).data,
            "total_market_value": total_market_value,
            "total_unrealized_pl": total_unrealized_pl,
            "details": details
        })


# Simple "news" endpoint (mock). You can replace with a real news API by fetching external APIs.
class NewsView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        news = [
            {"id":1, "title":"市场早报：A股板块普涨", "summary":"今日A股多个板块表现良好，金融、地产、科技涨幅显著。", "ts":"2025-01-01"},
            {"id":2, "title":"政策解读：某行业利好", "summary":"政府发布新规推动行业转型升级。", "ts":"2025-01-02"},
        ]
        return Response(news)

# Sectors time series (mock). Return simple arrays suitable for charting.
class SectorsView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        # mock 3 sectors with 30-day prices
        import random, datetime
        days = 30
        labels = []
        for i in range(days):
            labels.append((datetime.date.today() - datetime.timedelta(days=days-i-1)).isoformat())
        sectors = [
            {"name":"金融", "values":[round(100 + i*0.5 + random.uniform(-1,1), 2) for i in range(days)]},
            {"name":"科技", "values":[round(120 + i*0.8 + random.uniform(-1.5,1.5),2) for i in range(days)]},
            {"name":"地产", "values":[round(90 + i*0.2 + random.uniform(-0.5,0.5),2) for i in range(days)]},
        ]
        return Response({"labels": labels, "sectors": sectors})


import requests

class IndicesView(APIView):
    permission_classes = [permissions.AllowAny]
    def get(self, request):
        """
        返回上证 (sh000001), 深证成指 (sz399001), 创业板指 (sz399006) 的实时数据（来自新浪 hq.sinajs.cn）
        注意：新浪接口返回的是 GBK/GB2312 编码的文本，需要按实际解析字段。
        """
        try:
            # 需要的指数代码列表（如果想要更多可在这里扩展）
            codes = ["sh000001", "sz399001", "sz399006"]
            url = "http://hq.sinajs.cn/list=" + ",".join(codes)
            r = requests.get(url, timeout=5)
            # 新浪返回的是 gbk 编码（简体中文），所以用 r.encoding 或指定 'gbk'
            r.encoding = 'gbk'
            text = r.text.strip()
            # text 里有多行，每行形如：
            # var hq_str_sh000001="上证指数,XXX,YYY,ZZZ,..."；
            # 我们解析每一行，取指标名称与当前点位与昨收来计算涨跌幅
            results = []
            for line in text.splitlines():
                if not line:
                    continue
                # 找等号后面的引号内容
                try:
                    raw = line.split("=",1)[1]
                    # raw 的形式: "上证指数,3094.668,-128.073,-3.97,436653,5458126";
                    content = raw.strip().strip(";").strip().strip('"')
                    parts = content.split(",")
                    # 常见字段： parts[0]=name, parts[1]=current? parts[2]=change? 格式不同的站点可能不同。
                    # 常见可用字段： name, current, unknown..., 前收/昨收可能在 parts[2] 或 elsewhere。
                    name = parts[0] if len(parts)>0 else ""
                    # 尝试解析当前价与昨收（尽量稳健）
                    # 常见 pattern： [name, current, change, change_pct, ...] 或 [name, open, prev_close, current, ...]
                    # 我们尝试多种位置来尽量找到 current 与 prev_close
                    current = None
                    prev_close = None
                    # 先尝试 parts[3] as current (some older examples)
                    if len(parts) > 3:
                        try:
                            current = float(parts[3])
                        except:
                            current = None
                    # 如果没拿到，再试 parts[1]
                    if current is None and len(parts) > 1:
                        try:
                            current = float(parts[1])
                        except:
                            current = None
                    # prev_close: try parts[2]
                    if len(parts) > 2:
                        try:
                            prev_close = float(parts[2])
                        except:
                            prev_close = None
                    # 如果能拿到 current 与 prev_close，则计算涨跌额与涨跌幅
                    change = None
                    change_pct = None
                    if current is not None and prev_close is not None and prev_close != 0:
                        change = round(current - prev_close, 2)
                        change_pct = round((current - prev_close) / prev_close * 100, 2)
                    results.append({
                        "raw_line": line,
                        "name": name,
                        "current": current,
                        "prev_close": prev_close,
                        "change": change,
                        "change_pct": change_pct
                    })
                except Exception as e:
                    # 出错时也返回原始行，便于调试
                    results.append({"raw_line": line, "error": str(e)})
            return Response({"indices": results})
        except Exception as e:
            return Response({"detail":"failed to fetch indices", "error": str(e)}, status=500)


# trading/views.py (新增)
from rest_framework.views import APIView
from rest_framework.response import Response
# trading/views.py - 新增 KlineView
from rest_framework.views import APIView
from rest_framework.response import Response
import random, datetime

class KlineView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """
        Query params:
          symbol: e.g. sh000001, sz399001, sz399006
          limit: number of points, default 60
        返回格式：
        {
          "timestamps": ["2025-09-01","2025-09-02", ...],
          "klines": [[open, close, low, high], ...]   // 与 ECharts candlestick 要求一致
        }
        """
        symbol = request.query_params.get("symbol", "sh000001")
        limit = int(request.query_params.get("limit", 60))

        today = datetime.date.today()
        timestamps = []
        klines = []

        # 用 symbol 决定基础价格（只是为了示例稳定性）
        if symbol.startswith("sh"):
            base = 3000.0
        elif symbol.startswith("sz"):
            if symbol == "sz399006":  # 创业板
                base = 3000.0
            else:
                base = 15000.0
        else:
            base = 1000.0 + sum(ord(c) for c in symbol) % 1000

        prev_close = base
        for i in range(limit):
            dt = today - datetime.timedelta(days=(limit - i - 1))
            timestamps.append(dt.isoformat())
            # 模拟 OHLC
            open_p = round(prev_close * (1 + random.uniform(-0.005, 0.005)), 2)
            close_p = round(open_p * (1 + random.uniform(-0.02, 0.02)), 2)
            high_p = round(max(open_p, close_p) * (1 + random.uniform(0, 0.01)), 2)
            low_p = round(min(open_p, close_p) * (1 - random.uniform(0, 0.01)), 2)
            klines.append([open_p, close_p, low_p, high_p])
            prev_close = close_p

        return Response({"timestamps": timestamps, "klines": klines})



from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
import os
import requests

# 简单的 VIP 检查装饰器/辅助
def user_is_vip(user):
    try:
        return bool(user.cash_account.is_vip)
    except:
        return False

class ActivateVipView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        # 保证有 CashAccount（兼容旧数据）
        ca, created = CashAccount.objects.get_or_create(user=user, defaults={"balance": 100000.0})
        # 模拟开通（如果要扣款或更复杂逻辑在这里实现）
        ca.is_vip = True
        ca.save()
        return Response({
            "detail": "activated",
            "is_vip": ca.is_vip,
            "cash": CashAccountSerializer(ca).data
        })

from openai import OpenAI
client = OpenAI(api_key="sk-2f4ef76fe18347f0b533d541e5bc9823", base_url="https://api.deepseek.com/v1")

os.environ["http_proxy"] = 'http://127.0.0.1:7890'
os.environ["https_proxy"] = 'http://127.0.0.1:7890'
class AIQueryView(APIView):
    """
    精简版：接收 { "text": "用户提问" }，
    调用 DeepSeek（openai-compatible SDK），
    将 Q/A 都存入数据库，并返回回答。
    """
    permission_classes = [permissions.IsAuthenticated]  # 需要登录

    def post(self, request):
        user = request.user
        text = (request.data.get("text") or "").strip()
        if not text:
            return Response({"detail": "text 不能为空"}, status=400)

        # 建一个新的会话（简单）
        conv = AIConversation.objects.create(user=user, title=text[:120])

        # 存 user 问
        AIMessage.objects.create(conversation=conv, sender="user", content=text)

        # 调用 DeepSeek（官方示例风格）
        try:
            resp = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "你是一个金融投资领域的专业机器人."},
                    {"role": "user", "content": text},
                ],
                stream=False
            )

            # 官方示例：resp.choices[0].message.content
            answer = ""
            try:
                choice0 = resp.choices[0]
                answer = getattr(choice0.message, "content", None) or getattr(choice0, "text", None) or str(choice0)
            except Exception:
                # 兜底：把整个 resp 转为字符串
                answer = str(resp)

        except Exception as e:
            # 最小化错误处理：把错误信息也保存并返回，便于调试
            answer = f"调用 DeepSeek 失败：{type(e).__name__} {str(e)}"

        # 存 bot 回答
        AIMessage.objects.create(conversation=conv, sender="bot", content=answer)

        # 返回会话与回答
        return Response({
            "answer": answer,
            "conversation": AIConversationSerializer(conv).data
        })
