<template>
  <div class="verify-container">
    <div class="verify-background">
      <div class="verify-content">
        <div class="verify-header">
          <div class="verify-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>{{ $t('common.platformName') }}</p>
          </div>
        </div>
        <el-card class="verify-card" shadow="hover">
          <div v-if="status === 'pending'" class="verify-status">
            <el-icon class="verify-icon">
              <Loading />
            </el-icon>
            <h2>{{ $t('auth.verifyingEmail') }}</h2>
            <p>{{ $t('common.pleaseWait') }}</p>
          </div>
          <div v-else-if="status === 'success'" class="verify-status">
            <el-icon class="verify-icon" color="#67C23A">
              <CircleCheck />
            </el-icon>
            <h2>{{ $t('auth.emailVerifySuccess') }}</h2>
            <p>{{ $t('auth.emailActivatedSuccess') }}</p>
            <el-button type="primary" @click="goLogin" class="verify-btn">{{ $t('auth.goLogin') }}</el-button>
          </div>
          <div v-else class="verify-status">
            <el-icon class="verify-icon" color="#F56C6C">
              <CircleClose />
            </el-icon>
            <h2>{{ $t('auth.emailVerifyFailed') }}</h2>
            <p>{{ $t('auth.verifyLinkInvalid') }}</p>
            <el-button type="primary" @click="goRegister" class="verify-btn">{{ $t('auth.reregister') }}</el-button>
          </div>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import axios from '@/utils/axios.mjs'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const status = ref('pending')

const goLogin = () => router.push('/login')
const goRegister = () => router.push('/register')

onMounted(async () => {
  const token = route.query.token
  if (!token) {
    status.value = 'fail'
    return
  }
  try {
    const res = await axios.get(`/api/users/verify_email?token=${token}`)
    if (res.data.status === 'success') {
      status.value = 'success'
    } else {
      status.value = 'fail'
    }
  } catch (e) {
    status.value = 'fail'
  }
})
</script>

<style scoped>
.verify-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.verify-background {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.verify-background::before {
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

.verify-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.verify-header {
  width: 100%;
  text-align: center;
  margin-bottom: 40px;
  color: white;
  animation: fadeInDown 1s ease;
}

.verify-logo {
  width: 80%;
  margin: 0 auto;
}

.verify-logo img {
  width: 280px;
}

.verify-logo p {
  font-size: 18px;
  opacity: 0.9;
}

.verify-card {
  width: 100%;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(10px);
  animation: fadeInUp 1s ease;
  text-align: center;
  padding: 40px 20px 32px 20px;
}

.verify-status h2 {
  margin: 16px 0 8px 0;
  color: #409EFF;
}

.verify-status p {
  color: #333;
  font-size: 16px;
  margin-bottom: 0;
}

.verify-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.verify-btn {
  margin-top: 24px;
  width: 100%;
  height: 44px;
  font-size: 16px;
  border-radius: 8px;
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