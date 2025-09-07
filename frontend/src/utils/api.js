import axios from "axios";
import { API_BASE } from "../config";

const instance = axios.create({
  baseURL: API_BASE,
  timeout: 5000
});

instance.interceptors.request.use(config=>{
  const token = localStorage.getItem("token");
  if(token) config.headers.Authorization = `Token ${token}`;
  return config;
});

export default instance;
