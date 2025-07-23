<template>
  <div class="reset-container">
    <div class="reset-background">
      <div class="reset-content">
        <div class="reset-header">
          <div class="reset-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>数据同步管理平台</p>
          </div>
        </div>
        <el-card class="reset-card" shadow="hover">
          <h2>重置密码</h2>
          <el-form :model="form" :rules="rules" ref="formRef" label-width="0">
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="新密码" show-password />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="form.confirmPassword" type="password" placeholder="确认新密码" show-password />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" @click="handleSubmit" :loading="loading" class="reset-btn">重置密码</el-button>
            </el-form-item>
            <div class="login-link">
              <router-link to="/login">返回登录</router-link>
            </div>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const formRef = ref(null)
const loading = ref(false)
const form = ref({ password: '', confirmPassword: '' })
const rules = {
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度应在6-20个字符之间', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== form.value.password) {
          callback(new Error('两次输入的密码不一致'))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const token = route.query.token
        if (!token) {
          ElMessage.error('重置链接无效')
          return
        }
        const res = await axios.post('/api/auth/reset_password', {
          token,
          password: form.value.password
        })
        if (res.data.status === 'success') {
          ElMessage.success('密码重置成功，请登录')
          setTimeout(() => router.push('/login'), 1500)
        } else {
          ElMessage.error(res.data.msg || '重置失败')
        }
      } catch (e) {
        ElMessage.error(e.response?.data?.msg || '重置失败')
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.reset-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}
.reset-background {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
.reset-background::before {
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
.reset-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.reset-header {
  width: 100%;
  text-align: center;
  margin-bottom: 40px;
  color: var(--text-color);
  animation: fadeInDown 1s ease;
}
.reset-logo {
  width: 80%;
  margin: 0 auto;
}
.reset-logo img {
  width: 280px;
}
.reset-logo p {
  font-size: 18px;
  opacity: 0.9;
}
.reset-card {
  width: 100%;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(10px);
  animation: fadeInUp 1s ease;
  text-align: center;
  padding: 40px 20px 32px 20px;
}
.reset-card h2 {
  margin: 16px 0 12px 0;
  color: #409EFF;
}
.reset-btn {
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
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