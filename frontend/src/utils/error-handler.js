import { ElMessage } from "element-plus";
import router from "../router";

// 错误类型枚举
export const ErrorType = {
  NETWORK: "NETWORK",
  AUTH: "AUTH",
  VALIDATION: "VALIDATION",
  SERVER: "SERVER",
  UNKNOWN: "UNKNOWN",
};

// 错误处理配置
const errorConfig = {
  [ErrorType.NETWORK]: {
    title: "网络错误",
    message: "请检查网络连接后重试",
    type: "error",
  },
  [ErrorType.AUTH]: {
    title: "认证错误",
    message: "请重新登录",
    type: "warning",
  },
  [ErrorType.VALIDATION]: {
    title: "验证错误",
    message: "请检查输入内容",
    type: "warning",
  },
  [ErrorType.SERVER]: {
    title: "服务器错误",
    message: "服务器处理请求时发生错误",
    type: "error",
  },
  [ErrorType.UNKNOWN]: {
    title: "未知错误",
    message: "发生未知错误，请稍后重试",
    type: "error",
  },
};

// 获取错误类型
const getErrorType = (error) => {
  if (!error.response) {
    return ErrorType.NETWORK;
  }

  const status = error.response.status;

  if (status === 401 || status === 403) {
    return ErrorType.AUTH;
  }

  if (status === 422) {
    return ErrorType.VALIDATION;
  }

  if (status >= 500) {
    return ErrorType.SERVER;
  }

  return ErrorType.UNKNOWN;
};

// 处理认证错误
const handleAuthError = () => {
  localStorage.removeItem("user");
  router.push({
    name: "Login",
    query: { redirect: router.currentRoute.value.fullPath },
  });
};

// 处理验证错误
const handleValidationError = (error) => {
  const errors = error.response.data.errors;
  if (errors) {
    Object.values(errors).forEach((messages) => {
      messages.forEach((message) => {
        ElMessage.warning(message);
      });
    });
  }
};

// 全局错误处理函数
export const handleError = (error) => {
  console.error("Error:", error);

  const errorType = getErrorType(error);
  const config = errorConfig[errorType];

  // 特殊错误处理
  if (errorType === ErrorType.AUTH) {
    handleAuthError();
  } else if (errorType === ErrorType.VALIDATION) {
    handleValidationError(error);
  }

  // 显示错误消息
  ElMessage({
    message: error.response?.data?.message || config.message,
    type: config.type,
    duration: 5000,
  });

  return error;
};

// 注册全局错误处理器
export const registerErrorHandler = (app) => {
  app.config.errorHandler = (err, instance, info) => {
    console.error("Vue Error:", err);
    console.error("Error Info:", info);

    ElMessage.error("组件渲染错误，请刷新页面重试");
  };

  window.onerror = (message, source, lineno, colno, error) => {
    // 忽略 ResizeObserver 相关的警告
    if (
      message &&
      typeof message === "string" &&
      message.includes("ResizeObserver")
    ) {
      return true;
    }

    // 忽略 ECharts 相关的错误
    if (
      message &&
      typeof message === "string" &&
      (message.includes(
        "Cannot read properties of undefined (reading 'type')"
      ) ||
        message.includes("ECharts") ||
        message.includes("echarts") ||
        message.includes("type") ||
        (source && source.includes("echarts")))
    ) {
      console.warn("ECharts error suppressed:", message);
      return true;
    }

    console.error("Global Error:", {
      message,
      source,
      lineno,
      colno,
      error,
    });

    ElMessage.error("发生未知错误，请刷新页面重试");
  };

  window.onunhandledrejection = (event) => {
    console.error("Unhandled Promise Rejection:", event.reason);

    ElMessage.error("操作失败，请重试");
  };
};
