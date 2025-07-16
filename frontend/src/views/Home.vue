<template>
  <div class="home-container">
    <div class="sidebar">
      <div class="logo">
        <img src="/src/assets/logo/easysync-master-logo.svg">
      </div>
      <el-menu
        default-active="1"
        class="el-menu-vertical"
        background-color="transparent"
        text-color="#fff"
        active-text-color="#00f2fe"
        router
      >
        <el-menu-item index="/dashboard">
          <el-icon><HomeFilled /></el-icon>
          <span>首页</span>
        </el-menu-item>
        <el-menu-item index="/clients">
          <el-icon><Monitor /></el-icon>
          <span>客户端管理</span>
        </el-menu-item>
        <el-menu-item index="/nodes">
          <el-icon><Connection /></el-icon>
          <span>节点管理</span>
        </el-menu-item>
        <el-menu-item index="/storages">
          <el-icon><Folder /></el-icon>
          <span>存储管理</span>
        </el-menu-item>
        <el-menu-item index="/tasks">
          <el-icon><List /></el-icon>
          <span>任务管理</span>
        </el-menu-item>
        <el-menu-item index="/logs">
          <el-icon><Document /></el-icon>
          <span>日志管理</span>
        </el-menu-item>
        <el-menu-item index="/notifications">
          <el-icon><Bell /></el-icon>
          <span>通知设置</span>
        </el-menu-item>
        <el-menu-item index="/settings" v-if="isAdmin">
          <el-icon><Setting /></el-icon>
          <span>系统设置</span>
        </el-menu-item>
      </el-menu>
    </div>
    
    <div class="main-content">
      <div class="header">
        <div class="header-right">
          <el-dropdown @command="handleCommand" trigger="click">
            <div class="user-info">
              <el-avatar 
                :size="32" 
                :src="avatarUrl"
                :style="{ backgroundColor: user?.avatar ? 'transparent' : '#1890ff' }"
                @error="handleAvatarError"
              >
                {{ username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="username">{{ username }}</span>
              <el-icon class="arrow-down"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span>个人信息</span>
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  <span>退出登录</span>
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
      
      <div class="content">
        <router-view></router-view>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { 
  HomeFilled, 
  Folder, 
  Document, 
  List, 
  Bell, 
  Monitor,
  Connection,
  Setting, 
  ArrowDown,
  User,
  SwitchButton
} from '@element-plus/icons-vue'
import axios from 'axios'
import defaultAvatar from '@/assets/avatar/default-avatar.jpeg'

const router = useRouter()
const user = ref(null)

// 获取后端基础URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

onMounted(() => {
  const userStr = localStorage.getItem('user')
  const token = localStorage.getItem('access_token')
  
  if (userStr && token) {
    user.value = JSON.parse(userStr)
    // 设置axios默认请求头
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    router.push('/login')
  }
})

const username = computed(() => {
  return user.value ? user.value.username : '用户'
})

const avatarUrl = computed(() => {
  if (!user.value || !user.value.avatar) return defaultAvatar
  return `${API_BASE_URL}${user.value.avatar}`
})

const isAdmin = computed(() => {
  return user.value && user.value.role === 'admin'
})

const handleCommand = (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    // 清除本地存储
    localStorage.removeItem('user')
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    // 清除axios默认请求头
    delete axios.defaults.headers.common['Authorization']
    // 跳转到登录页
    router.push('/login')
  }
}

const handleAvatarError = () => {
  // 当头像加载失败时，使用默认头像
  user.value.avatar = defaultAvatar
}
</script>

<style scoped>
.home-container {
  display: flex;
  height: 100vh;
  color: #2c3e50;
}

.sidebar {
  width: 240px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  border-right: 1px solid rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  box-shadow: 2px 0 8px rgba(0, 0, 0, 0.05);
}

.logo {
  padding: 10px;
  text-align: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  height: 60px;
}

.logo img {
  height: 50px;
  margin-left: 20px;
}

.el-menu {
  border-right: none;
  padding: 20px 0;
}

.el-menu-item {
  height: 50px;
  line-height: 50px;
  margin: 4px 0;
  border-radius: 8px;
  transition: all 0.3s ease;
  color: #2c3e50;
}

.el-menu-item:hover {
  background: rgba(24, 144, 255, 0.1) !important;
}

.el-menu-item.is-active {
  background: linear-gradient(135deg, rgba(24, 144, 255, 0.1) 0%, rgba(54, 207, 201, 0.1) 100%) !important;
  color: #1890ff !important;
}

.main-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  height: 60px;
  padding: 0 20px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  border-bottom: 1px solid rgba(0, 0, 0, 0.1);
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  color: #2c3e50;
}

.user-info:hover {
  background: rgba(24, 144, 255, 0.1);
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.arrow-down {
  font-size: 12px;
  transition: transform 0.3s ease;
  color: #2c3e50;
}

.el-dropdown:hover .arrow-down {
  transform: rotate(180deg);
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

:deep(.el-dropdown-menu) {
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(0, 0, 0, 0.1);
  border-radius: 8px;
  padding: 8px 0;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

:deep(.el-dropdown-menu__item) {
  color: #2c3e50;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
}

:deep(.el-dropdown-menu__item:hover) {
  background: rgba(24, 144, 255, 0.1);
}

:deep(.el-dropdown-menu__item--divided) {
  border-top: 1px solid rgba(0, 0, 0, 0.1);
}

:deep(.el-dropdown-menu__item .el-icon) {
  font-size: 16px;
}

/* 滚动条样式 */
::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 3px;
}

::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.el-avatar {
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.el-avatar:hover {
  transform: scale(1.05);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}
</style> 