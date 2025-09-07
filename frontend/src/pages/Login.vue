<template>
  <div style="max-width:420px">
    <h2>登录</h2>
    <div><label>用户名</label><input v-model="username"/></div>
    <div><label>密码</label><input v-model="password" type="password"/></div>
    <div style="margin-top:8px">
      <button @click="login">登录</button>
      <button @click="$router.push('/register')">去注册</button>
    </div>
    <div v-if="err" style="color:red">{{ err }}</div>
  </div>
</template>

<script>
import api from "../utils/api";
export default {
  data(){ return { username:'', password:'', err:'' } },
  methods:{
    async login(){
      try{
        const r = await api.post("/login/", {username:this.username, password:this.password});
        localStorage.setItem("token", r.data.token);
        localStorage.setItem("user", JSON.stringify(r.data.user));
        this.$emit("login-success", r.data.user);
        this.$router.push('/');
      }catch(e){
        this.err = e.response?.data?.detail || "登录失败";
      }
    }
  }
}
</script>
