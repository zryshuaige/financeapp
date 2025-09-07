<template>
  <div>
    <nav style="background:#2b2f42;color:white;padding:10px;display:flex;gap:12px;">
<a href="/">
      <img src="http://127.0.0.1:8000/media/logo.jpg" alt="Logo" height="100pt"/>
    </a>
      <router-link to="/" style="color:white">首页</router-link>
      <router-link to="/favorites" style="color:white">自选股</router-link>
      <router-link to="/positions" style="color:white">持仓</router-link>
      <router-link to="/ai" style="color:white">AI 助手</router-link>
      <p style="font-size: 20px; text-align: left; margin-top: 50px;">
        {{ hitokoto }}
      </p>
      <div style="margin-left:auto">
        <span v-if="user">你好，{{ user.username }}</span>
        <button v-if="!user" @click="$router.push('/login')">登录</button>
        <button v-if="user" @click="logout">退出</button>
      </div>
    </nav>
    <div style="padding:12px">
      <router-view @login-success="onLogin"></router-view>
    </div>
  </div>
</template>

<script>
import { BACKEND_BASE } from './config'; // 路径按你实际位置调整
import { ref, onMounted } from "vue"
export default {
  data(){
    return { user: null,
    backend: BACKEND_BASE
    }
  },

  created(){
    const s = localStorage.getItem("user");
    if(s) this.user = JSON.parse(s);
  },
  methods:{
    onLogin(user){
      this.user = user;
      localStorage.setItem("user", JSON.stringify(user));
    },
    logout(){
      localStorage.removeItem("token");
      localStorage.removeItem("user");
      this.user = null;
      this.$router.push("/");
    },
  },
    setup() {
    const hitokoto = ref("加载中...")

    onMounted(async () => {
      try {
        const res = await fetch("https://v1.hitokoto.cn/?c=f&encode=text")
        const text = await res.text()
        hitokoto.value = text
      } catch (e) {
        hitokoto.value = "获取失败"
      }
    })

    return { hitokoto }
  }
}
</script>


