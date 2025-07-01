<template>
  <div class="login-container">
    <div class="login-background">
      <div class="login-content">
        <div class="login-header">
          <div class="login-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>数据同步管理平台</p>
          </div>
        </div>
        <el-card class="login-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>欢迎登录</h2>
            </div>
          </template>
          <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="0">
            <el-form-item prop="username">
              <el-input 
                v-model="loginForm.username" 
                placeholder="用户名"
                class="custom-input"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input 
                v-model="loginForm.password" 
                type="password" 
                placeholder="密码" 
                show-password
                class="custom-input"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                @click="handleLogin" 
                :loading="loading" 
                class="login-button"
              >
                登录
              </el-button>
            </el-form-item>
            <div class="register-link">
              <span>还没有账号？</span>
              <router-link to="/register">立即注册</router-link>
            </div>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import axios from 'axios'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)

const loginForm = reactive({
  username: '',
  password: ''
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在3-20个字符之间', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应在6-20个字符之间', trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await axios.post('/api/auth', loginForm)
        if (response.data.status === 'success') {
          // 保存用户信息和token
          userStore.user = response.data.data.user
          localStorage.setItem('user', JSON.stringify(response.data.data.user))
          localStorage.setItem('access_token', response.data.data.access_token)
          localStorage.setItem('refresh_token', response.data.data.refresh_token)
          
          // 设置axios默认请求头
          axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.data.access_token}`
          
          ElMessage.success({
            message: '登录成功，3秒后自动跳转到主页',
            duration: 3000
          })
          
          setTimeout(() => {
            router.push({ name: 'Dashboard' })
          }, 3000)
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.message || '登录失败，请检查用户名和密码')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.login-background {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.login-background::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url('@/assets/login-bg.jpg') center/cover;
  opacity: 0.1;
  z-index: 0;
}

.login-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1200px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.login-header {
  width: 100%;
  text-align: center;
  margin-bottom: 40px;
  color: white;
  animation: fadeInDown 1s ease;
}

.login-logo {
  width: 35%;
  margin: 0 auto;
}

.login-logo img {
  margin-bottom: -110px;
}

.login-logo p {
  font-size: 18px;
  opacity: 0.9;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  animation: fadeInUp 1s ease;
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #409EFF;
  font-size: 24px;
}

.custom-input {
  margin-bottom: 20px;
}

.custom-input :deep(.el-input__wrapper) {
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.custom-input :deep(.el-input__wrapper:hover) {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.login-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.login-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.register-link {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.register-link a {
  color: #409EFF;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.register-link a:hover {
  color: #66b1ff;
  text-decoration: underline;
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style> 