import axios from "axios";
import { ElMessage } from "element-plus";
import { apiConfig } from "@/config";

// 创建axios实例
const service = axios.create({
  baseURL: apiConfig.baseURL,
  timeout: 5000,
});
