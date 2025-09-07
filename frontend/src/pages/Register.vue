<template>
  <div style="max-width:420px">
    <h2>注册</h2>
    <div><label>用户名</label><input v-model="username"/></div>
    <div><label>邮箱</label><input v-model="email"/></div>
    <div><label>密码</label><input v-model="password" type="password"/></div>
    <div style="margin-top:8px">
      <button @click="register">注册并登录</button>
    </div>
    <div v-if="err" style="color:red">{{ err }}</div>
  </div>
</template>

<script>
import api from "../utils/api";
export default {
  data(){ return { username:'', email:'', password:'', err:'' } },
  methods:{
    async register(){
      try{
        const r = await api.post("/register/", {username:this.username, email:this.email, password:this.password});
        localStorage.setItem("token", r.data.token);
        localStorage.setItem("user", JSON.stringify(r.data.user));
        this.$emit("login-success", r.data.user);
        this.$router.push('/');
      }catch(e){
        this.err = JSON.stringify(e.response?.data) || "注册失败";
      }
    }
  }
}
</script>
