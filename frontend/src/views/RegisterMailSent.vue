<template>
  <div class="mail-sent-container">
    <div class="mail-sent-background">
      <div class="mail-sent-content">
        <div class="mail-sent-header">
          <div class="mail-sent-logo">
            <img src="/src/assets/logo/easysync-login-page.svg">
            <p>{{ $t('auth.dataSyncPlatform') }}</p>
          </div>
        </div>
        <el-card class="mail-sent-card" shadow="hover">
          <el-icon class="mail-sent-icon" color="#67C23A">
            <CircleCheck />
          </el-icon>
          <h2>{{ $t('auth.registerEmailSentTitle') }}</h2>
          <p>{{ $t('auth.registerEmailSentDesc') }} <b>{{ email }}</b>。<br>{{ $t('auth.registerEmailSentCheck') }}</p>
          <el-button type="primary" @click="goLogin" class="mail-sent-btn">{{ $t('auth.backToLogin') }}</el-button>
        </el-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRoute, useRouter } from 'vue-router'
import { CircleCheck } from '@element-plus/icons-vue'
const route = useRoute()
const router = useRouter()
const email = route.query.email
const goLogin = () => router.push('/login')
</script>

<style scoped>
.mail-sent-container {
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  overflow: hidden;
}

.mail-sent-background {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.mail-sent-background::before {
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

.mail-sent-content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: 20px;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.mail-sent-header {
  width: 100%;
  text-align: center;
  margin-bottom: 40px;
  color: white;
  animation: fadeInDown 1s ease;
}

.mail-sent-logo {
  width: 80%;
  margin: 0 auto;
}

.mail-sent-logo img {
  width: 280px;
}

.mail-sent-logo p {
  font-size: 18px;
  opacity: 0.9;
}

.mail-sent-card {
  width: 100%;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.97);
  backdrop-filter: blur(10px);
  animation: fadeInUp 1s ease;
  text-align: center;
  padding: 40px 20px 32px 20px;
}

.mail-sent-card h2 {
  margin: 16px 0 12px 0;
  color: #409EFF;
}

.mail-sent-card p {
  color: #333;
  font-size: 16px;
  margin-bottom: 0;
}

.mail-sent-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.mail-sent-btn {
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