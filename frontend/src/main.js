import { createApp } from "vue";
import { createPinia } from "pinia";
import ElementPlus from "element-plus";
import { ElMessage } from "element-plus";
import "element-plus/dist/index.css";
import zhCn from "element-plus/dist/locale/zh-cn.mjs";
import App from "./App.vue";
import router from "./router";
import "./assets/theme.css";
import axios from "axios";
import { registerErrorHandler, handleError } from "./utils/error-handler";
import { apiConfig } from "@/config";

// Configure axios
axios.defaults.baseURL = apiConfig.baseURL;
axios.defaults.withCredentials = true;
axios.defaults.headers.common["Content-Type"] = "application/json";
axios.defaults.headers.common["Accept"] = "application/json";

// Add request interceptors
axios.interceptors.request.use(
  (config) => {
    // Add JWT token to request headers
    const token = localStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptors
axios.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    if (error.response) {
      switch (error.response.status) {
        case 401:
          // 未授权，跳转到登录页面
          if (error.response.data.msg == "Token has expired") {
            ElMessage.error("登录已过期，请重新登录");
            localStorage.removeItem("access_token");
            localStorage.removeItem("refresh_token");
            localStorage.removeItem("user");
            sessionStorage.removeItem("welcome_shown");
            router.push("/login");
          }
          break;
        case 403:
          // 禁止访问，跳转到403页面
          ElMessage.error("禁止访问");
          router.push("/403");
          break;
        case 404:
          // 未找到资源，跳转到404页面
          ElMessage.error("请求资源不存在");
          router.push("/404");
          break;
        case 500:
          // 服务器错误，跳转到500页面
          ElMessage.error("服务器错误");
          router.push("/500");
          break;
        default:
          // 其他错误，显示错误信息
          ElMessage.error(error.response.status.message || "请求失败");
      }
    } else {
      ElMessage.error("网络错误，请稍后再试");
    }
    return Promise.reject(handleError(error));
  }
);

// 自动设置默认主题
if (!document.documentElement.getAttribute("data-theme")) {
  document.documentElement.setAttribute("data-theme", "light");
}

const app = createApp(App);

// Register global error handler
registerErrorHandler(app);

app.use(createPinia());
app.use(router);
app.use(ElementPlus, {
  locale: zhCn,
});

app.mount("#app");
