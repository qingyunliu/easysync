<template>
  <div class="login-container">
    <div class="login-background">
      <div class="login-content">
        <div class="login-header">
          <div class="login-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>{{ $t('auth.dataSyncPlatform') }}</p>
          </div>
        </div>
        <el-card class="login-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>{{ $t('auth.welcomeBack') }}</h2>
              <ThemeToggle class="theme-toggle-inline" />
            </div>
          </template>
          <el-form :model="loginForm" :rules="rules" ref="loginFormRef" label-width="0" @submit.prevent="handleLogin">
            <el-form-item prop="username">
              <el-input 
                v-model="loginForm.username" 
                :placeholder="$t('auth.username')"
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
                :placeholder="$t('auth.password')" 
                show-password
                class="custom-input"
              >
                <template #prefix>
                  <el-icon><Lock /></el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="captcha">
              <el-row :gutter="8">
                <el-col :span="12">
                  <el-input v-model="loginForm.captcha" maxlength="4" :placeholder="$t('auth.captcha')" />
                </el-col>
                <el-col :span="12">
                  <img
                    :src="captchaImg"
                    @click="refreshCaptcha"
                    style="height: 40px; cursor: pointer; border-radius: 4px; border:1px solid var(--border-color); background:var(--bg-color);"
                    :title="$t('auth.clickToRefresh')"
                  />
                </el-col>
              </el-row>
            </el-form-item>
            <el-form-item>
              <el-button 
                type="primary" 
                native-type="submit"
                :loading="loading" 
                class="login-button"
              >
                {{ $t('auth.login') }}
              </el-button>
            </el-form-item>
            <div class="register-link">
              <span>{{ $t('auth.noAccount') }}</span>
              <router-link to="/register">{{ $t('auth.registerNow') }}</router-link>
              <span class="forgot-link-sep">|</span>
              <router-link to="/forgot_password" class="forgot-link">{{ $t('auth.forgotPasswordLink') }}</router-link>
            </div>
          </el-form>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle.vue'

const router = useRouter()
const userStore = useUserStore()
const loginFormRef = ref(null)
const loading = ref(false)

const captchaId = ref('')
const captchaImg = ref('')

function refreshCaptcha() {
  axios.get('/api/auth/captcha', { responseType: 'blob', withCredentials: true }).then(res => {
    captchaId.value = res.headers['captcha-id']
    captchaImg.value = URL.createObjectURL(res.data)
  })
}

onMounted(() => {
  refreshCaptcha()
})

const loginForm = reactive({
  username: '',
  password: '',
  captcha: ''
})

const { t } = useI18n()

const rules = {
  username: [
    { required: true, message: t('auth.usernameInvalid'), trigger: 'blur' },
    { min: 3, max: 50, message: t('auth.usernameTooShort'), trigger: 'blur' }
  ],
  password: [
    { required: true, message: t('auth.passwordInvalid'), trigger: 'blur' },
    { min: 6, max: 50, message: t('auth.passwordTooShort'), trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: t('auth.captchaInvalid'), trigger: 'blur' },
    { len: 4, message: t('auth.captchaInvalid'), trigger: 'blur' }
  ]
}

const handleLogin = async () => {
  if (!loginFormRef.value) return
  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      loading.value = true
      try {
        const response = await axios.post('/api/auth', {
          username: loginForm.username,
          password: loginForm.password,
          captcha: loginForm.captcha,
          captcha_id: captchaId.value
        }, { withCredentials: true })
        if (response.data.status === 'success') {
          // 只保存token
          localStorage.setItem('access_token', response.data.data.access_token)
          localStorage.setItem('refresh_token', response.data.data.refresh_token)
          // 设置axios默认请求头
          axios.defaults.headers.common['Authorization'] = `Bearer ${response.data.data.access_token}`
          ElMessage.success({
            message: t('auth.loginSuccess'),
            duration: 3000
          })
          setTimeout(() => {
            router.push({ name: 'Dashboard' })
          }, 3000)
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.msg || error.response?.data?.message || t('auth.loginFailed'))
        refreshCaptcha()
        loginForm.captcha = ''
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
  background: var(--login-bg-gradient);
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
  width: 280px;
}

.login-logo p {
  font-size: 18px;
  opacity: 0.9;
}

.login-card {
  width: 100%;
  max-width: 400px;
  border-radius: 10px;
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  animation: fadeInUp 1s ease;
  border: 1px solid var(--border-color);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
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

.forgot-link {
  color: #409EFF;
  margin-left: 8px;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}
.forgot-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}
.forgot-link-sep {
  margin: 0 6px;
  color: #bbb;
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

.el-form-item .el-row {
  width: 100%;
}

.theme-toggle-bar {
  position: absolute;
  top: 32px;
  right: 48px;
  z-index: 10;
}
.theme-toggle-inline {
  margin-left: 12px;
}
</style> 