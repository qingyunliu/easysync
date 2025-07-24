import { defineStore } from "pinia";
import axios from "axios";

export const useUserStore = defineStore("user", {
  state: () => ({
    user: null,
    loading: false,
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
    },
    clearUser() {
      this.user = null;
    },
    async fetchUser() {
      this.loading = true;
      this.error = null;
      try {
        const res = await axios.get("/api/auth/me");
        this.user = res.data.data;
        return this.user;
      } catch (error) {
        this.user = null;
        this.error = error.response?.data?.message || "获取用户信息失败";
        throw error;
      } finally {
        this.loading = false;
      }
    },

    async login(username, password) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post("/api/login", { username, password });
        if (response.data.status === "success") {
          this.user = response.data.user;
          localStorage.setItem("user", JSON.stringify(this.user));
          return true;
        }
        return false;
      } catch (error) {
        this.error = error.response?.data?.message || "登录失败";
        return false;
      } finally {
        this.loading = false;
      }
    },

    async register(userData) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post("/api/users", userData);
        if (response.data.status === "success") {
          return true;
        }
        return false;
      } catch (error) {
        this.error = error.response?.data?.message || "注册失败";
        return false;
      } finally {
        this.loading = false;
      }
    },

    async updateProfile(profileData) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.put(
          `/api/users/${this.user.id}`,
          profileData
        );
        if (response.data.status === "success") {
          this.user = { ...this.user, ...profileData };
          localStorage.setItem("user", JSON.stringify(this.user));
          return true;
        }
        return false;
      } catch (error) {
        this.error = error.response?.data?.message || "更新失败";
        return false;
      } finally {
        this.loading = false;
      }
    },

    async updateAvatar(formData) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post(
          `/api/users/${this.user.id}/avatar`,
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );
        if (response.data.status === "success") {
          this.user = { ...this.user, avatar: response.data.avatar_url };
          localStorage.setItem("user", JSON.stringify(this.user));
          return true;
        }
        return false;
      } catch (error) {
        this.error = error.response?.data?.message || "头像更新失败";
        return false;
      } finally {
        this.loading = false;
      }
    },

    async changePassword(passwordData) {
      this.loading = true;
      this.error = null;
      try {
        const response = await axios.post(
          `/api/users/${this.user.id}/change-password`,
          passwordData
        );
        if (response.data.status === "success") {
          return true;
        }
        return false;
      } catch (error) {
        this.error = error.response?.data?.message || "修改密码失败";
        return false;
      } finally {
        this.loading = false;
      }
    },

    logout() {
      this.user = null;
    },
  },
});
