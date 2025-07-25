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
    if (!config.headers.Authorization) {
      const token = localStorage.getItem("access_token");
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptors
let isRefreshing = false;
let refreshSubscribers = [];

function onRefreshed(token) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb) {
  refreshSubscribers.push(cb);
}

axios.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response &&
      error.response.status === 401 &&
      error.response.data?.msg === "Token has expired" &&
      !originalRequest._retry
    ) {
      // access_token 过期，尝试用 refresh_token 刷新
      if (isRefreshing) {
        // 正在刷新，队列等待
        return new Promise((resolve, reject) => {
          addRefreshSubscriber((token) => {
            if (token) {
              originalRequest.headers["Authorization"] = "Bearer " + token;
              resolve(axios(originalRequest));
            } else {
              reject(error);
            }
          });
        });
      }
      isRefreshing = true;
      originalRequest._retry = true;
      const refresh_token = localStorage.getItem("refresh_token");
      if (refresh_token) {
        try {
          const res = await axios.post(
            "/api/auth/refresh",
            {},
            {
              headers: { Authorization: "Bearer " + refresh_token },
            }
          );
          const newToken = res.data.access_token;
          localStorage.setItem("access_token", newToken);
          axios.defaults.headers.common["Authorization"] = "Bearer " + newToken;
          onRefreshed(newToken);
          isRefreshing = false;
          originalRequest.headers["Authorization"] = "Bearer " + newToken;
          return axios(originalRequest);
        } catch (e) {
          isRefreshing = false;
          onRefreshed(null);
          // 刷新失败，清除token并跳转登录
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          sessionStorage.removeItem("welcome_shown");
          router.push("/login");
          return Promise.reject(e);
        }
      } else {
        // 没有refresh_token
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");
        sessionStorage.removeItem("welcome_shown");
        router.push("/login");
        return Promise.reject(error);
      }
    }
    // 其他错误处理
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
