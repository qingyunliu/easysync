<template>
  <div class="profile-container">
    <div class="page-header">
      <h2>{{ $t('profile.pageTitle') }}</h2>
    </div>
    
    <div class="content-wrapper">
      <el-tabs v-model="activeTab" class="profile-tabs">
        <!-- 基本信息 -->
        <el-tab-pane :label="$t('profile.basicInfo')" name="basic">
          <el-form 
            :model="profileForm" 
            :rules="profileRules" 
            ref="profileFormRef" 
            label-width="100px"
            class="profile-form"
          >
            <el-form-item :label="$t('profile.avatar')">
              <div class="avatar-uploader">
                <el-avatar 
                  :size="120" 
                  :src="profileForm.avatar || defaultAvatar"
                  @error="handleAvatarError"
                >
                  {{ profileForm.username?.charAt(0)?.toUpperCase() }}
                </el-avatar>
                <el-upload
                  class="avatar-uploader"
                  :show-file-list="false"
                  :before-upload="beforeAvatarUpload"
                  :http-request="handleAvatarUpload"
                >
                  <el-button type="primary" size="small" class="upload-button">
                    {{ $t('profile.changeAvatar') }}
                  </el-button>
                </el-upload>
              </div>
            </el-form-item>
            
            <el-form-item :label="$t('profile.username')">
              <el-input v-model="profileForm.username" disabled></el-input>
            </el-form-item>
            
            <el-form-item :label="$t('profile.email')" prop="email">
              <el-input v-model="profileForm.email"></el-input>
            </el-form-item>

            <el-divider content-position="left">{{ $t('profile.accountInfo') }}</el-divider>

            <el-form-item :label="$t('profile.userId')">
              <el-input v-model="profileForm.id" disabled>
                <template #append>
                  <el-tooltip :content="$t('profile.copyId')" placement="top">
                    <el-button class="copy-id-btn" @click="copyUserId">
                      <el-icon><Document /></el-icon>
                    </el-button>
                  </el-tooltip>
                </template>
              </el-input>
            </el-form-item>

            <el-form-item :label="$t('profile.userRole')">
              <el-tag 
                :type="profileForm.role === 'admin' ? 'danger' : 'success'"
                effect="dark"
                class="role-tag"
              >
                {{ profileForm.role === 'admin' ? $t('profile.admin') : $t('profile.normalUser') }}
              </el-tag>
            </el-form-item>

            <el-form-item :label="$t('profile.createdTime')">
              <span class="info-text">{{ formatDate(profileForm.created_at) }}</span>
            </el-form-item>

            <el-form-item :label="$t('profile.lastLogin')">
              <span class="info-text">{{ formatDate(profileForm.last_login) }}</span>
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                @click="handleUpdateProfile" 
                :loading="userStore.loading"
              >
                {{ $t('profile.saveChanges') }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
        
        <!-- 修改密码 -->
        <el-tab-pane :label="$t('profile.changePassword')" name="password">
          <el-form 
            :model="passwordForm" 
            :rules="passwordRules" 
            ref="passwordFormRef" 
            label-width="100px"
            class="profile-form"
          >
            <el-form-item :label="$t('profile.currentPassword')" prop="currentPassword">
              <el-input 
                v-model="passwordForm.currentPassword" 
                type="password" 
                show-password
              ></el-input>
            </el-form-item>
            
            <el-form-item :label="$t('profile.newPassword')" prop="newPassword">
              <el-input 
                v-model="passwordForm.newPassword" 
                type="password" 
                show-password
              ></el-input>
            </el-form-item>
            
            <el-form-item :label="$t('profile.confirmPassword')" prop="confirmPassword">
              <el-input 
                v-model="passwordForm.confirmPassword" 
                type="password" 
                show-password
              ></el-input>
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                @click="handleChangePassword" 
                :loading="userStore.loading"
              >
                {{ $t('profile.changePassword') }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { useUserStore } from '../stores/user'
import defaultAvatar from '@/assets/avatar/default-avatar.jpeg'
import { Document } from '@element-plus/icons-vue'
import axios from 'axios'

const { t } = useI18n()
const userStore = useUserStore()
const activeTab = ref('basic')
const profileFormRef = ref(null)
const passwordFormRef = ref(null)

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:50001"

// 个人信息表单
const profileForm = reactive({
  id: '',
  username: '',
  email: '',
  role: '',
  created_at: '',
  last_login: '',
  avatar: defaultAvatar
})

// 密码表单
const passwordForm = reactive({
  currentPassword: '',
  newPassword: '',
  confirmPassword: ''
})

// 个人信息验证规则
const profileRules = {
  email: [
    { required: true, message: t('profile.validation.enterEmail'), trigger: 'blur' },
    { type: 'email', message: t('profile.validation.enterValidEmail'), trigger: 'blur' }
  ]
}

// 密码验证规则
const passwordRules = {
  currentPassword: [
    { required: true, message: t('profile.validation.enterCurrentPassword'), trigger: 'blur' },
    { min: 6, max: 20, message: t('profile.validation.passwordLength'), trigger: 'blur' }
  ],
  newPassword: [
    { required: true, message: t('profile.validation.enterNewPassword'), trigger: 'blur' },
    { min: 6, max: 20, message: t('profile.validation.passwordLength'), trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: t('profile.validation.confirmNewPassword'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (value !== passwordForm.newPassword) {
          callback(new Error(t('profile.validation.passwordsNotMatch')))
        } else {
          callback()
        }
      },
      trigger: 'blur'
    }
  ]
}

// 头像上传前的验证
const beforeAvatarUpload = (file) => {
  const isJPG = file.type === 'image/jpeg' || file.type === 'image/png'
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isJPG) {
    ElMessage.error(t('profile.messages.avatarFormatError'))
  }
  if (!isLt2M) {
    ElMessage.error(t('profile.messages.avatarSizeError'))
  }
  return isJPG && isLt2M
}

// 获取用户信息
const fetchUserProfile = async () => {
  try {
    const response = await axios.get("/api/users/me");
    
    const userData = response.data.data
    Object.assign(profileForm, {
      id: userData.id,
      username: userData.username,
      email: userData.email,
      role: userData.role,
      created_at: userData.created_at,
      last_login: userData.last_login,
      avatar: userData.avatar ? `${API_BASE_URL}${userData.avatar}` : defaultAvatar
    })
  } catch (error) {
    ElMessage.error(t('profile.messages.getUserInfoFailed'))
    console.error('获取用户信息失败:', error)
  }
}

// 在组件挂载时获取用户信息
onMounted(() => {
  fetchUserProfile()
})

// 更新个人信息
const handleUpdateProfile = async () => {
  if (!profileFormRef.value) return
  
  await profileFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const response = await axios.put(
          `/api/users/${profileForm.id}`,
          { email: profileForm.email },
          {
            headers: {
              'Authorization': `Bearer ${userStore.token}`
            }
          }
        )
        
        if (response.status === 200) {
          ElMessage.success(t('profile.messages.profileUpdateSuccess'))
          // 重新获取用户信息
          await fetchUserProfile()
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.message || t('profile.messages.updateFailed'))
      }
    }
  })
}

// 处理头像上传
const handleAvatarUpload = async (options) => {
  const formData = new FormData()
  formData.append('avatar', options.file)
  
  try {
    const response = await axios.post(
      `/api/users/${profileForm.id}/avatar`,
      formData,
      {
        headers: {
          'Authorization': `Bearer ${userStore.token}`,
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    
    if (response.status === 200) {
      profileForm.avatar = `${response.data.avatar_url}`
      ElMessage.success(t('profile.messages.avatarUpdateSuccess'))
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('profile.messages.avatarUpdateFailed'))
  }
}

// 处理头像加载错误
const handleAvatarError = () => {
  profileForm.avatar = defaultAvatar
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return t('profile.unknown')
  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    hour12: false
  })
}

// 复制用户ID
const copyUserId = () => {
  if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
    navigator.clipboard.writeText(profileForm.id)
      .then(() => ElMessage.success(t('profile.messages.userIdCopied')))
      .catch(() => ElMessage.error(t('profile.messages.copyFailed')))
  } else {
    // 兼容性降级：使用 document.execCommand
    const input = document.createElement('input')
    input.value = profileForm.id
    document.body.appendChild(input)
    input.select()
    try {
      document.execCommand('copy')
      ElMessage.success(t('profile.messages.userIdCopied'))
    } catch (e) {
      ElMessage.error(t('profile.messages.copyFailed'))
    }
    document.body.removeChild(input)
  }
}

// 修改密码
const handleChangePassword = async () => {
  if (!passwordFormRef.value) return
  
  await passwordFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        const response = await axios.put(
          `/api/users/${profileForm.id}/password`,
          {
            current_password: passwordForm.currentPassword,
            new_password: passwordForm.newPassword
          },
          {
            headers: {
              'Authorization': `Bearer ${userStore.token}`
            }
          }
        )
        
        if (response.status === 200) {
          ElMessage.success(t('profile.messages.passwordChangeSuccess'))
          passwordForm.currentPassword = ''
          passwordForm.newPassword = ''
          passwordForm.confirmPassword = ''
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.message || t('profile.messages.changeFailed'))
      }
    }
  })
}
</script>

<style scoped>
.profile-container {
  padding: 24px;
  height: 100%;
  background-color: var(--bg-color);
}

.page-header {
  margin-bottom: 24px;
}

.page-header h2 {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
}

.content-wrapper {
  background-color: var(--card-bg);
  border-radius: 4px;
  padding: 24px;
  min-height: calc(100vh - 220px);
}

.profile-tabs {
  max-width: 800px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  background: var(--card-bg) #16161a;
  border-radius: 12px;
  padding: 24px;
  box-shadow: var(--card-shadow);
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
}

.profile-form {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px 0;
}

.avatar-uploader {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.upload-button {
  margin-top: 8px;
}

.el-avatar {
  border: 2px solid #fff;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.el-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 16px 0 rgba(0, 0, 0, 0.15);
}

.role-tag {
  font-size: 14px;
  padding: 4px 12px;
}

.info-text {
  color: var(--text-secondary);
  font-size: 14px;
}

:deep(.el-divider__text) {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
}

:deep(.el-tabs__nav-wrap::after) {
  height: 1px;
  background-color: #e4e7ed;
}

:deep(.el-tabs__item) {
  font-size: 16px;
  height: 48px;
  line-height: 48px;
}

:deep(.el-tabs__item.is-active) {
  font-weight: 600;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset;
}

:deep(.el-button--primary) {
  padding: 12px 24px;
  font-weight: 500;
}

:deep(.el-input-group__append) {
  padding: 0;
  background-color: transparent;
  box-shadow: 0px 0px 3px 0px var(--border-color);
  border: 1px solid var(--border-color);
}

:deep(.el-input-group__append .el-button) {
  border: none;
  padding: 8px 12px;
  margin: 0;
}

:deep(.el-input-group__append .el-button:hover) {
  background-color: var(--bg-color);
}

</style> 