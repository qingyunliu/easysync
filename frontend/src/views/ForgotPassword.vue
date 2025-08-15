<template>
  <div class="forgot-container">
    <div class="forgot-background">
      <div class="forgot-content">
        <div class="forgot-header">
          <div class="forgot-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>{{ $t('auth.dataSyncPlatform') }}</p>
          </div>
        </div>
        <el-card class="forgot-card" shadow="hover">
          <h2>{{ $t('auth.forgotPassword') }}</h2>
          <el-form :model="form" :rules="rules" ref="formRef" label-width="0" @submit.prevent="handleSubmit">
            <el-form-item prop="email">
              <el-input v-model="form.email" :placeholder="$t('auth.enterRegisteredEmail')">
                <template #prefix>
                  <el-icon><Message /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                native-type="submit"
                :loading="loading" 
                class="forgot-btn"
              >
                {{ $t('auth.sendResetEmail') }}
              </el-button>
            </el-form-item>
            <div class="login-link">
              <router-link to="/login">{{ $t('auth.backToLogin') }}</router-link>
            </div>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Message } from '@element-plus/icons-vue'
import axios from 'axios'

const router = useRouter()
const { t } = useI18n()
const formRef = ref(null)
const loading = ref(false)
const form = ref({ email: '' })
const rules = {
  email: [
    { required: true, message: t('auth.emailInvalid'), trigger: 'blur' },
    { type: 'email', message: t('auth.emailInvalid'), trigger: 'blur' }
  ]
}
const handleSubmit = async () => {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const res = await axios.post('/api/auth/forgot_password', { email: form.value.email })
        if (res.data.status === 'success') {
          router.push({ name: 'ResetMailSent', query: { email: form.value.email } })
        } else {
          ElMessage.error(res.data.msg || t('auth.sendFailed'))
        }
      } catch (e) {
        ElMessage.error(e.response?.data?.msg || t('auth.sendFailed'))
      } finally {
        loading.value = false
      }
    }
  })
}
</script>

<style scoped>
.forgot-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}
.forgot-background {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}
.forgot-background::before {
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
.forgot-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.forgot-header {
  width: 100%;
  text-align: center;
  margin-bottom: 40px;
  color: white;
  animation: fadeInDown 1s ease;
}
.forgot-logo {
  width: 80%;
  margin: 0 auto;
}
.forgot-logo img {
  width: 280px;
}
.forgot-logo p {
  font-size: 18px;
  opacity: 0.9;
}
.forgot-card {
  width: 100%;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(10px);
  animation: fadeInUp 1s ease;
  text-align: center;
  padding: 40px 20px 32px 20px;
}
.forgot-card h2 {
  margin: 16px 0 12px 0;
  color: #409EFF;
}
.forgot-btn {
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