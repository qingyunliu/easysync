import { ElMessage, ElMessageBox } from "element-plus";
import router from "@/router";

/**
 * 认证工具类 - 处理token相关的用户交互
 */
export class AuthHandler {
  /**
   * 清除所有认证信息
   */
  static clearAuthData() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    sessionStorage.removeItem("welcome_shown");

    // 清除用户信息（动态导入避免循环依赖）
    try {
      import("@/stores/user")
        .then(({ useUserStore }) => {
          const userStore = useUserStore();
          if (userStore) {
            userStore.clearUser();
          }
        })
        .catch((e) => {
          console.warn("无法清除用户store:", e);
        });
    } catch (e) {
      console.warn("无法导入用户store:", e);
    }
  }

  /**
   * 处理refresh token过期 - 显示确认对话框
   */
  static async handleRefreshTokenExpired() {
    try {
      await ElMessageBox.confirm(
        "您的登录已过期，为了保护您的账户安全，请重新登录。",
        "登录过期提醒",
        {
          confirmButtonText: "重新登录",
          cancelButtonText: "稍后再说",
          type: "warning",
          showClose: false,
          closeOnClickModal: false,
          closeOnPressEscape: false,
          beforeClose: (action, instance, done) => {
            if (action === "confirm") {
              this.clearAuthData();
              router.push("/login");
              done();
            } else {
              // 即使点击"稍后再说"，也要清除认证信息并跳转
              ElMessage({
                type: "info",
                message: "为了您的账户安全，仍需重新登录",
                duration: 2000,
              });
              setTimeout(() => {
                this.clearAuthData();
                router.push("/login");
                done();
              }, 2000);
            }
          },
        }
      );
    } catch (error) {
      // 如果用户取消或其他错误，仍然要清除认证信息
      this.clearAuthData();
      router.push("/login");
    }
  }

  /**
   * 处理refresh token无效 - 显示错误对话框
   */
  static async handleRefreshTokenInvalid(message) {
    try {
      await ElMessageBox.alert(
        message || "登录信息无效，请重新登录以继续使用系统。",
        "登录失效",
        {
          confirmButtonText: "立即登录",
          type: "error",
          showClose: false,
          closeOnClickModal: false,
          closeOnPressEscape: false,
          callback: () => {
            this.clearAuthData();
            router.push("/login");
          },
        }
      );
    } catch (error) {
      this.clearAuthData();
      router.push("/login");
    }
  }

  /**
   * 显示简单的token过期提示消息
   */
  static showTokenExpiredMessage() {
    ElMessage({
      type: "warning",
      message: "登录已过期，正在跳转到登录页面...",
      duration: 2000,
      showClose: true,
      onClose: () => {
        this.clearAuthData();
        router.push("/login");
      },
    });
  }

  /**
   * 处理其他认证错误
   */
  static handleAuthError(error) {
    console.error("认证错误:", error);
    ElMessage({
      type: "error",
      message: "认证失败，请重新登录",
      duration: 3000,
      showClose: true,
    });

    setTimeout(() => {
      this.clearAuthData();
      router.push("/login");
    }, 1000);
  }
}
