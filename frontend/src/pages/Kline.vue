<template>
  <div style="display:flex;gap:12px;flex-wrap:wrap">
    <div v-for="s in symbols" :key="s.code" style="width:320px;border:1px solid #eee;padding:8px">
      <div style="font-weight:bold">{{ s.name }} ({{ s.code }})</div>
      <div :id="'kchart-'+s.code" style="width:100%;height:200px"></div>
    </div>
  </div>
</template>

<script>
import api from "../utils/api";
import * as echarts from "echarts";

export default {
  props: {
    // symbols: [{code:'sh000001', name:'上证指数'}, ...]
    symbols: { type: Array, default: () => [
      {code:'sh000001', name:'上证指数'},
      {code:'sz399001', name:'深证成指'},
      {code:'sz399006', name:'创业板指'}
    ] }
  },
  data(){ return { charts: {} } },
  mounted(){
    this.symbols.forEach(s=>{
      this.charts[s.code] = echarts.init(document.getElementById("kchart-"+s.code));
    });
    this.loadAll();
    this._timer = setInterval(this.loadAll, 15000); // 每15s刷新，可改成 5000
  },
  beforeUnmount(){
    if(this._timer) clearInterval(this._timer);
    Object.values(this.charts).forEach(c=>c.dispose && c.dispose());
  },
  methods:{
    async loadAll() {
      for (const s of this.symbols) {
        try {
          const r = await api.get(`/kline/?symbol=${encodeURIComponent(s.code)}&limit=60`);
          const ts = r.data.timestamps;
          const klines = r.data.klines; // [ [open, close, low, high], ... ]
          const option = {
            xAxis: {type: 'category', data: ts, boundaryGap: true, axisLabel: {show: false}},
            yAxis: {scale: true, axisLabel: {show: false}},
            series: [{
              type: 'candlestick',
              data: klines,
              itemStyle: {
                color: '#ec0000', color0: '#00da3c', borderColor: '#8A0000', borderColor0: '#008F28'
              }
            }],
            tooltip: {trigger: 'axis'},
          };
          this.charts[s.code].setOption(option);
        } catch (e) {
          console.error("load kline failed for", s.code, e);
        }
      }
    }
  }
}
</script>
