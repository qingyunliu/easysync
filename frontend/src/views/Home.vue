<template>
  <div class="home-container">
    <div class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="logo">
        <img :src="logoSrc" :style="isCollapsed ? '' : 'margin-left:-10px;width:165px;'">
      </div>
      <div class="collapse-btn" @click="toggleSidebar">
        <el-icon>
          <component :is="isCollapsed ? Expand : Fold" />
        </el-icon>
      </div>
      <el-menu
        default-active="1"
        class="el-menu-vertical"
        background-color="transparent"
        text-color="#fff"
        active-text-color="#00f2fe"
        router
        :collapse="isCollapsed"
        :collapse-transition="true"
      >
        <el-tooltip content="首页" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <span v-if="!isCollapsed">首页</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="客户端管理" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/clients">
            <el-icon><Monitor /></el-icon>
            <span v-if="!isCollapsed">客户端管理</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="节点管理" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/nodes">
            <el-icon><Connection /></el-icon>
            <span v-if="!isCollapsed">节点管理</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="存储管理" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/storages">
            <el-icon><Folder /></el-icon>
            <span v-if="!isCollapsed">存储管理</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="任务管理" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/tasks">
            <el-icon><List /></el-icon>
            <span v-if="!isCollapsed">任务管理</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="日志管理" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/logs">
            <el-icon><Document /></el-icon>
            <span v-if="!isCollapsed">日志管理</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="通知设置" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/notifications">
            <el-icon><Bell /></el-icon>
            <span v-if="!isCollapsed">通知设置</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip content="系统设置" placement="right" :disabled="!isCollapsed" v-if="isAdmin">
          <el-menu-item index="/settings" v-if="isAdmin">
            <el-icon><Setting /></el-icon>
            <span v-if="!isCollapsed">系统设置</span>
          </el-menu-item>
        </el-tooltip>
      </el-menu>
    </div>
    
    <div class="main-content">
      <div class="header">
        <div class="header-right">
          <ThemeToggle />
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
import ThemeToggle from '@/components/ThemeToggle.vue'
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
  SwitchButton,
  Fold,
  Expand
} from '@element-plus/icons-vue'
import axios from 'axios'
import defaultAvatar from '@/assets/avatar/default-avatar.jpeg'

const isCollapsed = ref(localStorage.getItem('isCollapsedSideBar') === 'true')

const router = useRouter()
const user = ref(null)

// 主题判断
const theme = ref(document.documentElement.getAttribute('data-theme') || 'light')
const updateTheme = () => {
  theme.value = document.documentElement.getAttribute('data-theme') || 'light'
}
window.addEventListener('DOMContentLoaded', updateTheme)
window.addEventListener('storage', updateTheme)
const observer = new MutationObserver(updateTheme)
observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })

const logoSrc = computed(() => {
  if (isCollapsed.value) {
    if (theme.value === 'dark') {
      return '/src/assets/logo/easysync-small-white-page.svg'
    }
    return '/src/assets/logo/easysync-small-logo.svg'
  }
  if (theme.value === 'dark') {
    return '/src/assets/logo/easysync-login-page.svg'
  }
  return '/src/assets/logo/easysync-master-logo.svg'
})

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

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('isCollapsedSideBar', isCollapsed.value)
}

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
  color: var(--text-color);
  background: var(--bg-color);
}

.sidebar {
  width: 200px;
  background: var(--sidebar-bg);
  border-right: 1px solid var(--border-color);
  box-shadow: 2px 0 16px 0 rgba(24, 144, 255, 0.06);
  transition: width 0.3s cubic-bezier(.4,0,.2,1), background 0.3s;
  position: relative;
  backdrop-filter: blur(8px);
}
.sidebar.collapsed {
  width: 60px;
}
.logo {
  text-align: center;
  border-bottom: 1px solid var(--border-color);
  height: 60px;
  transition: height 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
}

.collapse-btn {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  margin-bottom: 2px;
}
.collapse-btn:hover {
  background: var(--bg-secondary);
}
.el-menu {
  background: transparent;
  border-right: none;
  padding: 18px 0;
}
.sidebar.collapsed .el-menu {
  padding: 8px 0;
}
.el-menu-item {
  height: 48px;
  font-weight: 500;
  line-height: 48px;
  margin: 8px 0;
  border-radius: 16px;
  color: var(--sidebar-text);
  font-size: 15px;
  transition: background 0.25s, color 0.25s, box-shadow 0.25s, border 0.25s;
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: none;
  border: 2px solid transparent;
  position: relative;
}
.el-menu-item span {
  transition: opacity 0.2s;
}
.sidebar.collapsed .el-menu-item span {
  opacity: 0;
  width: 0;
  display: inline-block;
}
.el-menu-item:hover {
  background: var(--bg-secondary);
  color: var(--sidebar-active);
  box-shadow: 0 2px 8px 0 rgba(64, 158, 255, 0.10);
  border: 1px solid var(--border-color);
}
.el-menu-item.is-active {
  background: var(--bg-secondary);
  color: var(--sidebar-active) !important;
  font-weight: 600;
  box-shadow: 0 2px 12px 0 rgba(64, 158, 255, 0.10);
  border: 1px solid var(--border-color);
}

.el-menu-item .el-icon {
  font-size: 22px;
  color: var(--sidebar-text);
  transition: color 0.25s, transform 0.25s;
}

.el-menu-item.is-active .el-icon,
.el-menu-item:hover .el-icon {
  color: var(--sidebar-active);
  transform: scale(1.18);
  text-shadow: 0 0 8px #b2e2ff;
}

.sidebar.collapsed .el-menu-item {
  justify-content: center;
  padding: 0;
}

.sidebar.collapsed .el-menu-item .el-icon {
  margin: 0;
}

.sidebar.collapsed .el-menu-item span {
  display: none;
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
  border-bottom: 1px solid var(--border-color);
  background: var(--header-bg);
  backdrop-filter: blur(10px);
}

.header-right {
  display: flex;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 8px;
  transition: all 0.3s ease;
  color: var(--text-color);
}

.user-info:hover {
  background: var(--bg-secondary);
}

.username {
  font-size: 14px;
  font-weight: 500;
}

.arrow-down {
  font-size: 12px;
  transition: transform 0.3s ease;
  color: var(--text-secondary);
}

.el-dropdown:hover .arrow-down {
  transform: rotate(180deg);
}

.content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background: var(--bg-color);
}

:deep(.el-dropdown-menu) {
  background: var(--card-bg);
  backdrop-filter: blur(10px);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 8px 0;
  box-shadow: var(--card-shadow-hover);
}

:deep(.el-dropdown-menu__item) {
  color: var(--text-color);
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
}

:deep(.el-dropdown-menu__item:hover) {
  background: var(--bg-secondary);
}

:deep(.el-dropdown-menu__item--divided) {
  border-top: 1px solid var(--border-lighter);
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