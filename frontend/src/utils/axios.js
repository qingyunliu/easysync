import axios from 'axios'
import { apiConfig } from '@/config'

// 创建统一的axios实例
const service = axios.create({
  baseURL: apiConfig.baseURL,  // 'http://localhost:5000/api'
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  }
})

// 请求拦截器
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
service.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    // 处理常见错误
    if (error.response) {
      const status = error.response.status
      const message = error.response.data?.msg || error.response.data?.message || '请求失败'
      
      // 验证码错误
      if (status === 400 && message.includes('验证码')) {
        return Promise.reject(error)
      }
      
      // Token过期
      if (status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
      }
    }
    
    return Promise.reject(error)
  }
)

export default service