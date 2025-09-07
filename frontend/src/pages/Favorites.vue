<template>
  <div>
    <h2>自选股</h2>
    <div v-if="!user">
      请先 <router-link to="/login">登录</router-link>
    </div>
    <div v-else>
      <table border="1" cellpadding="6">
        <thead><tr><th>代码</th><th>名称</th><th>价格</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="f in favorites" :key="f.id">
            <td>{{ f.stock.symbol }}</td>
            <td>{{ f.stock.name }}</td>
            <td>{{ f.stock.price }}</td>
            <td>
              <button @click="remove(f.id)">删除自选</button>
              <button @click="openOrder(f.stock)">下单</button>
            </td>
          </tr>
        </tbody>
      </table>
      <h3 style="margin-top:12px">市场其它股票（示例）</h3>
      <table border="1" cellpadding="6">
        <thead><tr><th>代码</th><th>名称</th><th>价格</th><th>操作</th></tr></thead>
        <tbody>
          <tr v-for="s in otherStocks" :key="s.id">
            <td>{{ s.symbol }}</td><td>{{ s.name }}</td><td>{{ s.price }}</td>
            <td><button @click="addFavorite(s)">加入自选</button></td>
          </tr>
        </tbody>
      </table>
    </div>

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
    </div>

  </div>
</template>

<script>
import api from "../utils/api";
export default {
  data(){ return { favorites:[], otherStocks:[], user:null, orderStock:null, orderQty:1, orderPrice:0, orderSide:'BUY' } },
  mounted(){ this.fetch(); this.user = JSON.parse(localStorage.getItem("user")||"null"); },
  methods:{
    async fetch(){
      const res = await api.get("/favorites/"); this.favorites = res.data;
      const st = await api.get("/stocks/"); this.otherStocks = st.data;
    },
    async addFavorite(stock){
      try{ await api.post("/favorites/", {stock_id:stock.id}); alert("已加入自选"); this.fetch(); }
      catch(e){ alert("失败"); }
    },
    async remove(id){
      try{ await api.delete(`/favorites/${id}/`); alert("已删除"); this.fetch(); }
      catch(e){ alert("失败"); }
    },
    openOrder(stock){ this.orderStock = stock; this.orderPrice = stock.price; },
    async placeOrder(){
      try{
        await api.post("/order/", {stock_id:this.orderStock.id, side:this.orderSide, quantity:this.orderQty, price:this.orderPrice});
        alert("下单成功"); this.orderStock=null; this.$router.push('/positions');
      }catch(e){
        alert(e.response?.data?.detail || "失败");
      }
    }
  }
}
</script>
