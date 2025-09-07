<template>
  <div>
    <h2>今日板块走势图</h2>
    <div style="display:flex;gap:12px;flex-wrap:wrap">
      <KlinePanel />
<!--      <div v-for="s in sectors" :key="s.name" style="width:320px;height:220px;border:1px solid #ddd;padding:8px">-->
<!--        <div>{{ s.name }}</div>-->
<!--        <div :id="'chart-'+s.name" style="width:100%;height:170px;"></div>-->
<!--      </div>-->
    </div>

    <div style="display:flex;gap:12px;align-items:center;margin-bottom:12px">
    <div v-for="idx in indices" :key="idx.raw_line" style="padding:8px;border:1px solid #ddd">
      <div><strong>{{ idx.name || 'Unknown' }}</strong></div>
      <div v-if="idx.current !== null">
        <span>{{ idx.current }}</span>
        <span :style="{color: idx.change>0 ? 'red' : (idx.change<0 ? 'green' : 'black')}">
          {{ idx.change !== null ? (idx.change>0 ? '+' : '') + idx.change : '' }}
          ({{ idx.change_pct !== null ? (idx.change_pct>0?'+':'') + idx.change_pct + '%' : '' }})
        </span>
      </div>
      <div v-else>
        <small>实时数据不可用</small>
      </div>
    </div>
  </div>

    <h2 style="margin-top:16px">重大新闻</h2>
    <ul>
      <img src="http://127.0.0.1:8000/media/news.jpg" alt="Logo" height="80pt"/>
      <li v-for="n in news" :key="n.id">{{ n.ts }} - <strong>{{ n.title }}</strong> ：{{ n.summary }}</li>
    </ul>

    <h2 style="margin-top:16px">市场股票（示例）</h2>
    <table border="1" cellpadding="6">
      <thead><tr><th>代码</th><th>名称</th><th>现价</th><th>操作</th></tr></thead>
      <tbody>
        <tr v-for="s in stocks" :key="s.id">
          <td>{{ s.symbol }}</td>
          <td>{{ s.name }}</td>
          <td>{{ s.price }}</td>
          <td>
            <button @click="toAddFavorite(s)">加入自选</button>
            <button @click="openOrder(s)">下单</button>
          </td>
        </tr>
      </tbody>
    </table>

    <!-- 简单下单弹窗 -->
    <div v-if="orderStock" style="position:fixed;right:20px;top:80px;background:white;border:1px solid #ccc;padding:12px">
      <h3>下单: {{ orderStock.name }} ({{ orderStock.symbol }})</h3>
      <div>
        <label>方向</label>
        <select v-model="orderSide"><option value="BUY">买入</option><option value="SELL">卖出</option></select>
      </div>
      <div><label>数量</label><input v-model.number="orderQty" type="number" /></div>
      <div><label>价格</label><input v-model.number="orderPrice" type="number" /></div>
      <div style="margin-top:8px">
        <button @click="placeOrder">提交</button>
        <button @click="orderStock=null">关闭</button>
      </div>
      <div v-if="orderMsg" style="color:green;margin-top:8px">{{ orderMsg }}</div>
    </div>

  </div>
</template>

<script>
import api from "../utils/api";
import * as echarts from 'echarts';
import KlinePanel from "./KlinePanel.vue";

export default {
  components: { KlinePanel },
  data(){ return {
    sectors: [],
    labels: [],
    news: [],
    stocks: [],
    indices: [],   // 新增
    orderStock: null,
    orderSide: "BUY",
    orderQty: 100,
    orderPrice: 0,
    orderLot: 100,
    orderMsg: ""
  }},
  mounted(){
  this.fetchAll();
  this.fetchIndices();
  // 每 5 秒刷新一次指数（可调整）
    this._indicesTimer = setInterval(()=> this.fetchIndices(), 5000);
  },
  beforeUnmount(){
    if(this._indicesTimer) clearInterval(this._indicesTimer);
  },
  methods:{
    async fetchIndices(){
    try {
      const r = await api.get("/indices/");
      // 直接使用 r.data.indices（数组），前端展示 name/current/change/change_pct
      this.indices = r.data.indices;
    } catch(err){
      console.warn("fetch indices failed", err);
      }
    },
    async fetchAll(){
      const sec = await api.get("/sectors/"); this.labels = sec.data.labels; this.sectors = sec.data.sectors;
      const n = await api.get("/news/"); this.news = n.data;
      const st = await api.get("/stocks/"); this.stocks = st.data;
      // render charts
      this.$nextTick(()=>{
        this.sectors.forEach(s=>{
          const el = document.getElementById("chart-"+s.name);
          if(!el) return;
          const chart = echarts.init(el);
          chart.setOption({
            xAxis:{type:'category', data:this.labels},
            yAxis:{type:'value'},
            series:[{data:s.values, type:'line', smooth:true}],
            tooltip:{}
          });
        });
      });
    },
    async toAddFavorite(stock){
      const token = localStorage.getItem("token");
      if(!token){ alert("请先登录"); this.$router.push('/login'); return; }
      try{
        const res = await api.post("/favorites/", {stock_id: stock.id});
        alert("已加入自选");
      }catch(e){
        alert("可能已加入或发生错误");
      }
    },
    openOrder(stock){
    this.orderStock = stock;
    this.orderPrice = stock.price;
    // 计算手数：688 开头为 200 股，否则 100 股
    if((stock.symbol||"").startsWith("688")) this.orderLot = 200;
    else this.orderLot = 100;
    this.orderQty = this.orderLot; // 默认一手
  },

  async placeOrder(){
    // 前端校验
    if(this.orderQty <= 0 || this.orderPrice <= 0){
      alert('请输入合法的数量和价格');
      return;
    }
    if(this.orderQty % this.orderLot !== 0){
      alert(`交易数量必须为 ${this.orderLot} 的整数倍`);
      return;
    }
    try{
      const res = await api.post("/order/", {
        stock_id:this.orderStock.id,
        side:this.orderSide,
        quantity:this.orderQty,
        price:this.orderPrice
      });
      this.orderMsg = "下单成功";
      setTimeout(()=>{ this.orderStock=null; this.orderMsg=""; this.$router.push('/positions') }, 800);
    }catch(e){
      alert(e.response?.data?.detail || "下单失败");
    }
  }
  }
}
</script>
