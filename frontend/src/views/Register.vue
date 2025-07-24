<template>
  <div class="register-container">
    <div class="register-background">
      <div class="register-content">
        <div class="register-header">
          <div class="register-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>数据同步管理平台</p>
          </div>
        </div>
        <el-card class="register-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>创建账号</h2>
              <ThemeToggle class="theme-toggle-inline" />
            </div>
          </template>
          <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-width="0" @submit.prevent="handleRegister">
            <el-form-item prop="username">
              <el-input 
                v-model="registerForm.username" 
                placeholder="用户名"
                class="custom-input"
              >
                <template #prefix>
                  <el-icon><User /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="email">
              <el-input 
                v-model="registerForm.email" 
                placeholder="邮箱"
                class="custom-input"
              >
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input 
                v-model="registerForm.password" 
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
            <el-form-item prop="confirmPassword">
              <el-input 
                v-model="registerForm.confirmPassword" 
                type="password" 
                placeholder="确认密码" 
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
                native-type="submit"
                :loading="loading" 
                class="register-button"
              >
                注册
              </el-button>
            </el-form-item>
            <div class="login-link">
              <span>已有账号？</span>
              <router-link to="/login">立即登录</router-link>
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
import { User, Message, Lock } from '@element-plus/icons-vue'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const registerFormRef = ref(null)
const loading = ref(false)

const registerForm = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

const validatePass = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请输入密码'))
  } else {
    if (registerForm.confirmPassword !== '') {
      registerFormRef.value?.validateField('confirmPassword')
    }
    callback()
  }
}

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error('请再次输入密码'))
  } else if (value !== registerForm.password) {
    callback(new Error('两次输入密码不一致'))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度应在3-20个字符之间', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱地址', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱地址', trigger: 'blur' }
  ],
  password: [
    { required: true, validator: validatePass, trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应在6-20个字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, validator: validatePass2, trigger: 'blur' }
  ]
}

const handleRegister = async () => {
  if (!registerFormRef.value) return
  
  await registerFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await axios.post('/api/users', {
          username: registerForm.username,
          email: registerForm.email,
          password: registerForm.password
        })
        
        if (response.data.status === 'success') {
          ElMessage.success({
            message: '注册成功，已发送激活邮件',
            duration: 1500
          })
          setTimeout(() => {
            router.push({ name: 'RegisterMailSent', query: { email: registerForm.email } })
          }, 1500)
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.msg || error.response?.data?.message || '注册失败，请稍后再试')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.register-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: var(--login-bg-gradient);
  overflow: hidden;
}

.register-background {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.register-background::before {
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

.register-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1200px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.register-header {
  width: 100%;
  text-align: center;
  margin-bottom: 40px;
  color: white;
  animation: fadeInDown 1s ease;
}

.register-logo {
  width: 35%;
  margin: 0 auto;
}

.register-logo img {
   width: 280px;
}

.register-header p {
  font-size: 18px;
  opacity: 0.9;
}

.register-card {
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

.register-button {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  transition: all 0.3s ease;
}

.register-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.login-link {
  text-align: center;
  margin-top: 20px;
  color: #666;
}

.login-link a {
  color: #409EFF;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.login-link a:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.theme-toggle-bar {
  position: absolute;
  top: 32px;
  right: 48px;
  z-index: 10;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.theme-toggle-inline {
  margin-left: 12px;
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