<template>
  <div class="register-container">
    <div class="register-background">
      <div class="register-content">
        <div class="register-header">
          <div class="register-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>{{ $t('auth.dataSyncPlatform') }}</p>
          </div>
        </div>
        <el-card class="register-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <h2>{{ $t('auth.createAccount') }}</h2>
              <div class="header-actions">
                <LanguageIcon />
                <ThemeToggle class="theme-toggle-inline" />
              </div>
            </div>
          </template>
          <el-form :model="registerForm" :rules="rules" ref="registerFormRef" label-width="0"
            @submit.prevent="handleRegister">
            <el-form-item prop="username">
              <el-input v-model="registerForm.username" :placeholder="$t('auth.username')" class="custom-input">
                <template #prefix>
                  <el-icon>
                    <User />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="email">
              <el-input v-model="registerForm.email" :placeholder="$t('auth.email')" class="custom-input">
                <template #prefix>
                  <el-icon>
                    <Message />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="registerForm.password" type="password" :placeholder="$t('auth.password')" show-password
                class="custom-input">
                <template #prefix>
                  <el-icon>
                    <Lock />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" :placeholder="$t('auth.confirmPassword')"
                show-password class="custom-input">
                <template #prefix>
                  <el-icon>
                    <Lock />
                  </el-icon>
                </template>
              </el-input>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" native-type="submit" :loading="loading" class="register-button">
                {{ $t('auth.register') }}
              </el-button>
            </el-form-item>
            <div class="login-link">
              <span>{{ $t('auth.haveAccount') }}</span>
              <router-link to="/login">{{ $t('auth.loginNow') }}</router-link>
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
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'
import axios from 'axios'
import ThemeToggle from '@/components/ThemeToggle.vue'
import LanguageIcon from '@/components/LanguageIcon.vue'

const router = useRouter()
const { t } = useI18n()
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
    callback(new Error(t('auth.passwordInvalid')))
  } else {
    if (registerForm.confirmPassword !== '') {
      registerFormRef.value?.validateField('confirmPassword')
    }
    callback()
  }
}

const validatePass2 = (rule, value, callback) => {
  if (value === '') {
    callback(new Error(t('auth.confirmPasswordInvalid')))
  } else if (value !== registerForm.password) {
    callback(new Error(t('auth.passwordMismatch')))
  } else {
    callback()
  }
}

const rules = {
  username: [
    { required: true, message: t('auth.usernameInvalid'), trigger: 'blur' },
    { min: 3, max: 20, message: t('auth.usernameTooShort'), trigger: 'blur' }
  ],
  email: [
    { required: true, message: t('auth.emailInvalid'), trigger: 'blur' },
    { type: 'email', message: t('auth.emailInvalid'), trigger: 'blur' }
  ],
  password: [
    { required: true, validator: validatePass, trigger: 'blur' },
    { min: 6, max: 20, message: t('auth.passwordTooShort'), trigger: 'blur' }
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
            message: t('auth.registerSuccess'),
            duration: 1500
          })
          setTimeout(() => {
            router.push({ name: 'RegisterMailSent', query: { email: registerForm.email } })
          }, 1500)
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.msg || error.response?.data?.message || t('auth.registerFailed'))
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
  max-width: 430px;
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

.header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
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