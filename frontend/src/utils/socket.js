import { io } from "socket.io-client";
import { ElMessage } from "element-plus";
import { wsConfig } from "@/config";

class SocketManager {
  constructor() {
    this.socket = null;
    this.connected = false;
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
    this.handlers = new Map();
    this.subscriptions = new Set();
  }

  connect(clientId) {
    if (this.socket && this.connected) {
      return;
    }

    console.log("Connecting to WebSocket server with client ID:", clientId);
    console.log("WebSocket URL:", wsConfig.url);
    console.log("WebSocket Path:", wsConfig.path);

    this.socket = io(wsConfig.url, {
      path: wsConfig.path,
      transports: ["websocket", "polling"], // 允许降级到轮询
      reconnection: true,
      reconnectionAttempts: this.maxReconnectAttempts,
      reconnectionDelay: this.reconnectDelay,
      timeout: 10000,
      query: {
        client_id: clientId,
      },
      extraHeaders: {
        Authorization: `Bearer ${clientId}`,
      },
    });

    this.socket.on("connect", () => {
      console.log("WebSocket connected");
      this.connected = true;
      this.reconnectAttempts = 0;

      // 重新订阅之前的房间
      this.subscriptions.forEach((clientId) => {
        this.subscribe(clientId);
      });
    });

    this.socket.on("disconnect", () => {
      console.log("WebSocket disconnected");
      this.connected = false;
      try {
        const msg =
          window?.__app_i18n__?.global?.t?.("socket.disconnected") ||
          "与服务器断开连接";
        ElMessage.warning(msg);
      } catch (_) {
        ElMessage.warning("与服务器断开连接");
      }
    });

    this.socket.on("connect_error", (error) => {
      console.error("WebSocket connection error:", error);
      this.reconnectAttempts++;
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        try {
          const msg =
            window?.__app_i18n__?.global?.t?.("socket.connectFailedRetry") ||
            "连接服务器失败，请刷新页面重试";
          ElMessage.error(msg);
        } catch (_) {
          ElMessage.error("连接服务器失败，请刷新页面重试");
        }
      }
    });

    this.socket.on("error", (error) => {
      console.error("WebSocket error:", error);
      try {
        const prefix =
          window?.__app_i18n__?.global?.t?.("socket.websocketError") ||
          "WebSocket错误：";
        ElMessage.error(prefix + error.message);
      } catch (_) {
        ElMessage.error("WebSocket错误：" + error.message);
      }
    });

    this.socket.on("subscribed", (data) => {
      console.log("Subscribed to room:", data.room);
    });

    this.socket.on("unsubscribed", (data) => {
      console.log("Unsubscribed from room:", data.room);
    });
  }

  disconnect() {
    if (this.socket) {
      // 取消所有订阅
      this.subscriptions.forEach((clientId) => {
        this.unsubscribe(clientId);
      });
      this.subscriptions.clear();

      this.socket.disconnect();
      this.socket = null;
      this.connected = false;
    }
  }

  subscribe(clientId) {
    if (!this.connected) {
      console.warn("WebSocket not connected, cannot subscribe");
      return;
    }

    this.socket.emit("subscribe", { client_id: clientId });
    this.subscriptions.add(clientId);
  }

  unsubscribe(clientId) {
    if (!this.connected) {
      return;
    }

    this.socket.emit("unsubscribe", { client_id: clientId });
    this.subscriptions.delete(clientId);
  }

  on(event, handler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set());
    }
    this.handlers.get(event).add(handler);
    if (this.socket) {
      this.socket.on(event, handler);
    }
  }

  off(event, handler) {
    if (this.handlers.has(event)) {
      this.handlers.get(event).delete(handler);
    }
    if (this.socket) {
      this.socket.off(event, handler);
    }
  }

  emit(event, data) {
    if (this.socket && this.connected) {
      this.socket.emit(event, data);
    } else {
      console.warn("WebSocket not connected, cannot emit event:", event);
    }
  }

  isConnected() {
    return this.connected && this.socket !== null;
  }
}

export const socketManager = new SocketManager();
