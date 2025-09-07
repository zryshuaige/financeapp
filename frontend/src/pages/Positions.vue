<template>
  <div>
    <h2>持仓与账户</h2>

    <div v-if="!user">
      请先 <router-link to="/login">登录</router-link>
    </div>

    <div v-else>
      <div style="display:flex;gap:24px;align-items:center;margin-bottom:12px">
        <div><strong>账户余额：</strong>{{ cash.balance }} 元</div>
        <div><strong>持仓市值：</strong>{{ total_market_value }} 元</div>
        <div><strong>总未实现盈亏：</strong>
          <span :style="{ color: total_unrealized_pl>0 ? 'red' : (total_unrealized_pl<0 ? 'green' : 'black') }">
            {{ total_unrealized_pl }} 元
          </span>
        </div>
        <div style="margin-left:auto">
          <button @click="refresh">刷新</button>
        </div>
      </div>

      <table border="1" cellpadding="6" style="width:100%; border-collapse:collapse">
        <thead>
          <tr>
            <th>代码</th><th>名称</th><th>数量</th><th>均价</th><th>现价</th><th>市值</th><th>盈亏</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="d in details" :key="d.position_id">
            <td>{{ d.symbol }}</td>
            <td>{{ d.name }}</td>
            <td>{{ d.quantity }}</td>
            <td>{{ d.avg_price }}</td>
            <td>{{ d.market_price }}</td>
            <td>{{ d.market_value }}</td>
            <td :style="{ color: d.unrealized_pl>0 ? 'red' : (d.unrealized_pl<0 ? 'green' : 'black') }">
              {{ d.unrealized_pl }}
            </td>
            <td>
              <!-- 打开卖出（默认 SELL） -->
              <button @click="openOrderFromPosition(d, 'SELL')">卖出</button>
              <!-- 追加买入 -->
              <button @click="openOrderFromPosition(d, 'BUY')">买入</button>
            </td>
          </tr>
        </tbody>
      </table>

      <div style="margin-top:16px">
        <h3>提示</h3>
        <ul>
          <li>A股一般交易单位为每手 100 股；科创板 (代码以 688 开头) 为每手 200 股。</li>
          <li>下单数量必须为对应手数的整数倍，且后端会做严格校验。</li>
        </ul>
      </div>
    </div>

    <!-- 下单弹窗 -->
    <div v-if="orderVisible" style="position:fixed; right:20px; top:80px; width:340px; background:white; border:1px solid #ccc; padding:12px; z-index:999">
      <h3>下单 — {{ orderStock?.name }} ({{ orderStock?.symbol }})</h3>

      <div style="margin-bottom:8px">
        <label>方向：</label>
        <select v-model="orderSide">
          <option value="BUY">买入</option>
          <option value="SELL">卖出</option>
        </select>
      </div>

      <div style="margin-bottom:8px">
        <label>数量</label>
        <input type="number" v-model.number="orderQty" :min="orderLot" :step="orderLot" />
        <div style="font-size:12px;color:#666">手数：每手 {{ orderLot }} 股</div>
      </div>

      <div style="margin-bottom:8px">
        <label>价格</label>
        <input type="number" v-model.number="orderPrice" step="0.01" />
      </div>

      <div style="display:flex;gap:8px;justify-content:flex-end">
        <button @click="submitOrder">提交</button>
        <button @click="closeOrder">取消</button>
      </div>

      <div v-if="orderMsg" style="margin-top:8px;color:green">{{ orderMsg }}</div>
      <div v-if="orderErr" style="margin-top:8px;color:red">{{ orderErr }}</div>
    </div>
  </div>
</template>

<script>
import api from "../utils/api";

export default {
  data() {
    return {
      user: null,
      cash: { balance: 0 },
      total_market_value: 0,
      total_unrealized_pl: 0,
      details: [],

      // order modal
      orderVisible: false,
      orderStock: null,
      orderSide: "SELL",
      orderQty: 0,
      orderPrice: 0,
      orderLot: 100, // 手数（100 或 200）
      orderMsg: "",
      orderErr: ""
    };
  },
  mounted() {
    this.user = JSON.parse(localStorage.getItem("user") || "null");
    if (this.user) this.fetch();
  },
  methods: {
    async fetch() {
      try {
        const r = await api.get("/positions/");
        this.cash = r.data.cash || {balance: 0};
        this.total_market_value = r.data.total_market_value || 0;
        this.total_unrealized_pl = r.data.total_unrealized_pl || 0;
        this.details = r.data.details || [];
      } catch (err) {
        console.error("fetch positions failed", err);
      }
    },
    refresh() {
      this.fetch();
    },
    openOrderFromPosition(pos, side) {
      // pos 是后端返回的持仓条目
      this.orderStock = {id: null, symbol: pos.symbol, name: pos.name, price: pos.market_price};
      // we need to find stock id from stocks list if needed; but order API accepts stock_id - we need id.
      // Simplest: fetch all stocks and match symbol -> id; but to avoid extra request, we assume frontend has stocks list.
      // We'll try to find it in localStorage cached stocks
      const cached = JSON.parse(localStorage.getItem("stocks_cache") || "null");
      if (cached && Array.isArray(cached)) {
        const found = cached.find(s => s.symbol === pos.symbol);
        if (found) this.orderStock.id = found.id;
      }
      this.orderSide = side || "SELL";
      // 手数：688 开头为 200，否则 100
      if ((pos.symbol || "").startsWith("688")) this.orderLot = 200;
      else this.orderLot = 100;

      // 默认数量：若卖出则默认全仓（nearest lower multiple of orderLot）
      if (this.orderSide === "SELL") {
        const maxSell = Math.floor(pos.quantity / this.orderLot) * this.orderLot;
        this.orderQty = maxSell > 0 ? maxSell : this.orderLot;
      } else {
        // BUY 默认一手
        this.orderQty = this.orderLot;
      }

      // 默认价格取现价
      this.orderPrice = pos.market_price || 0;
      this.orderErr = "";
      this.orderMsg = "";
      this.orderVisible = true;
    },
    closeOrder() {
      this.orderVisible = false;
      this.orderStock = null;
      this.orderMsg = "";
      this.orderErr = "";
    },
// 在 methods 中替换 submitOrder
async submitOrder() {
  this.orderErr = "";
  this.orderMsg = "";

  // ensure stock id or symbol exists
  let payload = {
    side: this.orderSide,
    quantity: this.orderQty,
    price: this.orderPrice
  };

  // 优先使用 stock_id（如果有），否则传 symbol（后端已支持）
  if (this.orderStock && this.orderStock.id) payload.stock_id = this.orderStock.id;
  else if (this.orderStock && this.orderStock.symbol) payload.symbol = this.orderStock.symbol;
  else {
    this.orderErr = "无法确定股票标识 (stock_id 或 symbol)";
    return;
  }

  // basic front-end validation
  if (this.orderQty <= 0 || this.orderPrice <= 0) {
    this.orderErr = "请输入合法数量和价格";
    return;
  }
  if (this.orderQty % this.orderLot !== 0) {
    this.orderErr = `下单数量必须为 ${this.orderLot} 的整数倍`;
    return;
  }

  try {
    const res = await api.post("/order/", payload);
    this.orderMsg = "下单成功";
    await this.fetch(); // 刷新持仓和余额
    setTimeout(() => this.closeOrder(), 800);
  } catch (err) {
    // 更清晰的错误展示：优先显示 backend 返回的 detail
    console.error("order error raw:", err);
    const detail = err.response?.data?.detail || err.response?.data || err.message || "下单失败";
    this.orderErr = typeof detail === "string" ? detail : JSON.stringify(detail);
  }
}

  }
};
</script>
