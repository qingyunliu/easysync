<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <div class="card-header">
          <h2>EasySync 登录</h2>
        </div>
      </template>

      <el-form
        ref="loginForm"
        :model="formData"
        :rules="formRules"
        label-width="80px"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="请输入用户名"
            clearable
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item label="验证码" prop="captcha">
          <div class="captcha-container">
            <el-input
              v-model="formData.captcha"
              placeholder="请输入验证码"
              style="width: 200px"
              @keyup.enter="handleLogin"
            />
            <img
              :src="captchaImg"
              alt="验证码"
              class="captcha-img"
              @click="refreshCaptcha"
            />
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="handleLogin">
            {{ loading ? '登录中...' : '登录' }}
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from '@/utils/axios.mjs'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const loginForm = ref(null)
const loading = ref(false)
const userStore = useUserStore()  // 添加userStore

// 验证码相关
const captchaId = ref('')
const captchaImg = ref('')

// 表单数据
const formData = reactive({
  username: '',
  password: '',
  captcha: ''
})

// 表单验证规则
const formRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' }
  ],
  captcha: [
    { required: true, message: '请输入验证码', trigger: 'blur' }
  ]
}

// 刷新验证码
function refreshCaptcha() {
  console.log('刷新验证码，请求路径: /auth/captcha')
  axios.get('/auth/captcha', { responseType: 'blob', withCredentials: true })
    .then(res => {
      console.log('验证码响应状态:', res.status)
      console.log('验证码响应头:', res.headers)
      captchaId.value = res.headers['captcha-id']
      captchaImg.value = URL.createObjectURL(res.data)
      console.log('验证码ID:', captchaId.value)
      console.log('验证码图片已更新')
    })
    .catch(err => {
      console.error('刷新验证码失败:', err)
      alert('刷新验证码失败，请检查网络连接')
    })
}

// 登录处理
function handleLogin() {
  if (!loginForm.value) return

  loginForm.value.validate((valid) => {
    if (!valid) {
      return false
    }

    loading.value = true

    const loginData = {
      username: formData.username,
      password: formData.password,
      captcha: formData.captcha,
      captcha_id: captchaId.value
    }

    console.log('登录数据:', loginData)

    axios.post('/auth/login', loginData, { withCredentials: true })
      .then(res => {
        console.log('登录成功:', res.data)
        
        // 保存 token 和用户信息
        if (res.data.data && res.data.data.access_token) {
          localStorage.setItem('access_token', res.data.data.access_token)
          localStorage.setItem('refresh_token', res.data.data.refresh_token)
          localStorage.setItem('user', JSON.stringify(res.data.data.user))
          
          // 更新 userStore
          userStore.setUser(res.data.data.user)
        }
        
        // 直接跳转到首页，不弹出提示
        router.push('/dashboard')
      })
      .catch(err => {
        console.error('登录失败:', err)
        const errorMsg = err.response?.data?.msg || err.response?.data?.message || '未知错误'

        // 根据错误类型显示不同的提示
        let displayMsg = errorMsg
        if (errorMsg.includes('验证码')) {
          displayMsg = '验证码输入错误，请重新输入'
        }

        alert('登录失败：' + displayMsg)
        // 用户确认错误提示后清空验证码，避免手动逐字删除
        formData.captcha = ''
        refreshCaptcha()
      })
      .finally(() => {
        loading.value = false
      })
  })
}

// 组件挂载时加载验证码
onMounted(() => {
  refreshCaptcha()
})
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
}

.card-header {
  text-align: center;
}

.card-header h2 {
  margin: 0;
  color: #333;
}

.captcha-container {
  display: flex;
  align-items: center;
  gap: 10px;
}

.captcha-img {
  cursor: pointer;
  height: 40px;
  border: 1px solid #ddd;
  border-radius: 4px;
  transition: opacity 0.2s;
}

.captcha-img:hover {
  opacity: 0.8;
}

.el-button {
  width: 100%;
}
</style>