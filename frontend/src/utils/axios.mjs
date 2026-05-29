import axios from 'axios'
import { apiConfig } from '@/config/index.js'

// 创建统一的axios实例
const service = axios.create({
  baseURL: '/api',  // 使用相对路径，通过Vite代理转发
  withCredentials: true
  // 不设置默认的Accept和Content-Type，让每个请求自己设置
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
      
      // Token过期
      if (status === 401) {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        // 不要在验证码页面跳转
        if (!window.location.pathname.includes('/login')) {
          window.location.href = '/login'
        }
      }
    }
    
    // 直接返回错误，不要在这里拦截
    return Promise.reject(error)
  }
)

export default service