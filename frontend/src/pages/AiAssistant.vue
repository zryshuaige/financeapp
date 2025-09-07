<template>
  <div style="max-width:760px">
    <h2>AI 助手（DeepSeek）</h2>
   <img src="http://127.0.0.1:8000/media/deepseek.jpg" alt="Logo" height="80pt"/>
    <div v-if="!user">
      请先 <router-link to="/login">登录</router-link>
    </div>

    <div v-else>
      <div>
        VIP 状态：
        <strong v-if="isVip" style="color:green">已开通</strong>
        <strong v-else style="color:red">未开通</strong>
        <button v-if="!isVip" @click="activateVip">点击开通（模拟）</button>
      </div>

      <div style="margin-top:12px">
        <div v-for="m in messages" :key="m.created_at" style="margin-bottom:8px">
          <div v-if="m.sender==='user'"><b>我：</b> {{ m.content }}</div>
          <div v-else><b>助手：</b> {{ m.content }}</div>
        </div>
      </div>

      <div style="margin-top:12px">
        <textarea v-model="input" rows="3" style="width:100%"></textarea>
        <div style="display:flex;gap:8px;margin-top:8px">
          <button @click="send" :disabled="sending || !isVip">发送</button>
          <button v-if="!isVip" @click="activateVip">未开通？点此开通</button>
          <div v-if="sending">发送中...</div>
        </div>
        <div v-if="err" style="color:red">{{ err }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import api from "../utils/api";
export default {
  data(){ return {
    user: JSON.parse(localStorage.getItem("user")||"null"),
    isVip: false,
    messages: [],
    input: "",
    sending: false,
    err: ""
  }},
  async mounted(){
    if(this.user) await this.loadVip();
  },
  methods:{
    async loadVip(){
      try{
        // 请求 positions 或 cashaccount 来获得 is_vip 字段
        const r = await api.get("/positions/"); // positions 返回 cash 信息
        this.isVip = r.data.cash?.is_vip || false;
      }catch(e){
        console.warn("load vip failed", e);
      }
    },
    async activateVip(){
  try{
    const token = localStorage.getItem("token");
    if(!token){
      alert("请先登录再开通 VIP");
      this.$router.push('/login');
      return;
    }
    const r = await api.post("/ai/activate/");
    // response 包含 is_vip 与 cash
    this.isVip = !!r.data.is_vip;
    alert("已模拟开通 VIP");
  }catch(err){
    console.error("activateVip error:", err);
    // 优先显示后端返回的详细信息
    const msg = err.response?.data?.detail || err.response?.data || err.message || "开通失败";
    alert("开通失败: " + (typeof msg === "string" ? msg : JSON.stringify(msg)));
  }
},

async send(){
  this.err = "";
  if(!this.input.trim()){
    this.err = "请输入问题";
    return;
  }
  if(!this.isVip){
    this.err = "仅 VIP 可用，请先开通";
    return;
  }

  const token = localStorage.getItem("token");
  if(!token){
    this.err = "未检测到登录信息，请先登录";
    this.$router.push('/login');
    return;
  }

  this.sending = true;
  const payload = { text: this.input.trim() };

  try{
    // 保险起见，这里把 Authorization 写到单次请求 header（若你全局 interceptor 已生效，这一步可省）
    const r = await api.post("/ai/query/", payload, {
      headers: { Authorization: `Token ${token}` },
      timeout: 20000
    });

    // 如果后端返回 conversation.messages，直接使用
    if(r.data?.conversation?.messages){
      this.messages = r.data.conversation.messages;
    } else if (r.data?.answer){
      // 否则用 answer 字段拼接一条记录（保持历史）
      // 将用户问题和 AI 回答加入到 messages（后端也会持久化）
      this.messages.push({ sender: "user", content: this.input });
      this.messages.push({ sender: "bot", content: r.data.answer });
    } else {
      // 兜底处理
      console.warn("AI 返回未包含 conversation/messages 或 answer：", r.data);
      this.messages.push({ sender: "bot", content: JSON.stringify(r.data) });
    }

    // 清空输入框
    this.input = "";

  }catch(e){
    // 打印完整错误到 console 便于调试
    console.error("AI query error:", e);

    // 优先取后端返回的 detail 或 message
    const resp = e.response;
    if(resp){
      // HTTP 状态判断（示例）
      if(resp.status === 401){
        this.err = "未授权（请重新登录）";
        localStorage.removeItem("token");
        this.$router.push('/login');
      } else if (resp.status === 403){
        this.err = resp.data?.detail || "无权限访问（可能不是 VIP）";
      } else if (resp.status === 502 || resp.status === 503){
        // 502 可能是后端到 DeepSeek 的连接问题
        this.err = resp.data?.detail || `网关/上游服务错误（${resp.status}）`;
      } else {
        // 其他错误：显示后端 detail 或整个返回体
        this.err = resp.data?.detail || JSON.stringify(resp.data) || `请求失败: ${resp.status}`;
      }
    } else {
      // 没有 response（网络/超时等）
      this.err = e.message || "请求失败（网络或超时）";
    }
  } finally {
    this.sending = false;
  }
}

  }
}
</script>
