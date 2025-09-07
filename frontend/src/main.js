import { createApp } from "vue";
import { createRouter, createWebHistory } from "vue-router";
import AiAssistant from "./pages/AiAssistant.vue";

import App from "./App.vue";
import Home from "./pages/Home.vue";
import Login from "./pages/Login.vue";
import Register from "./pages/Register.vue";
import Favorites from "./pages/Favorites.vue";
import Positions from "./pages/Positions.vue";

const routes = [
  { path: "/", component: Home },
  { path: "/login", component: Login },
  { path: "/register", component: Register },
  { path: "/favorites", component: Favorites },
  { path: "/positions", component: Positions },
  { path: "/ai", component: AiAssistant },
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

createApp(App).use(router).mount("#app");
