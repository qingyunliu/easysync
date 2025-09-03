import { defineStore } from "pinia";
import axios from "axios";

export const useUserStore = defineStore("user", {
  state: () => ({
    user: null, // 用户信息
    loaded: false, // 是否已加载
    error: null,
  }),
  getters: {
    isAuthenticated: (state) => !!state.user,
    isAdmin: (state) => state.user?.is_admin === true,
    username: (state) => state.user?.username,
    email: (state) => state.user?.email,
    avatar: (state) => state.user?.avatar,
  },
  actions: {
    setUser(user) {
      this.user = user;
      this.loaded = true;
    },
    clearUser() {
      this.user = null;
      this.loaded = true;
    },
    async fetchUser() {
      this.loaded = false;
      this.error = null;
      try {
        const res = await axios.get("/api/users/me");
        this.user = res.data.data;
      } catch (error) {
        this.user = null;
        // Use a generic error message that can be handled by the UI
        this.error = error.response?.data?.message || "FETCH_USER_FAILED";
      } finally {
        this.loaded = true;
      }
    },
    logout() {
      this.user = null;
      this.loaded = false;
    },
  },
});
