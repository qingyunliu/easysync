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
        <!-- 控制台 -->
        <div class="menu-group-title" v-if="!isCollapsed">{{ $t('nav.dashboard') }}</div>
        <el-tooltip :content="$t('nav.dashboard')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/dashboard">
            <el-icon><Histogram /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.dashboard') }}</span>
          </el-menu-item>
        </el-tooltip>

        <!-- 资源管理 -->
        <div class="menu-group-title" v-if="!isCollapsed">{{ $t('nav.resourceManagement') }}</div>
        <el-tooltip :content="$t('nav.clients')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/clients">
            <el-icon><Monitor /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.clients') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.nodes')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/nodes">
            <el-icon><Connection /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.nodes') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.storage')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/storages">
            <el-icon><Files /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.storage') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.tasks')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/tasks">
            <el-icon><Clock /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.tasks') }}</span>
          </el-menu-item>
        </el-tooltip>

        <!-- 运维管理 -->
        <div class="menu-group-title" v-if="!isCollapsed">{{ $t('nav.operationsManagement') }}</div>
        <el-tooltip :content="$t('nav.auditLogs')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/audit-logs">
            <el-icon><Notebook /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.auditLogs') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.events')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/events">
            <el-icon><List /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.events') }}</span>
          </el-menu-item>
        </el-tooltip>

        <!-- 监控告警 -->
        <div class="menu-group-title" v-if="!isCollapsed">{{ $t('nav.monitoring') }}</div>
        <el-tooltip :content="$t('nav.systemMonitoring')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/monitoring">
            <el-icon><DataAnalysis /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.systemMonitoring') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.alertPolicies')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/alert-policies">
            <el-icon><Warning /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.alertPolicies') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.alertTemplates')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/alert-templates">
            <el-icon><Document /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.alertTemplates') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.notificationChannels')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/notification-channels">
            <el-icon><Message /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.notificationChannels') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.notificationTargets')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/notification-targets">
            <el-icon><User /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.notificationTargets') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.notifications')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/notifications">
            <el-icon><Bell /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.notifications') }}</span>
          </el-menu-item>
        </el-tooltip>

        <!-- 系统管理 -->
        <div class="menu-group-title" v-if="!isCollapsed">{{ $t('nav.systemManagement') }}</div>
        <el-tooltip :content="$t('nav.logs')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/logs">
            <el-icon><Document /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.logs') }}</span>
          </el-menu-item>
        </el-tooltip>
        <el-tooltip :content="$t('nav.settings')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/settings">
            <el-icon><Setting /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.settings') }}</span>
          </el-menu-item>
        </el-tooltip>

        <!-- 个人中心 -->
        <div class="menu-group-title" v-if="!isCollapsed">{{ $t('nav.personalCenter') }}</div>
        <el-tooltip :content="$t('nav.profile')" placement="right" :disabled="!isCollapsed">
          <el-menu-item index="/profile">
            <el-icon><User /></el-icon>
            <span v-if="!isCollapsed">{{ $t('nav.profile') }}</span>
          </el-menu-item>
        </el-tooltip>
      </el-menu>
    </div>
    
    <div class="main-content">
      <div class="header">
        <div class="header-right">
          <LanguageSwitch />
          <ThemeToggle />
          <el-dropdown @command="handleCommand" trigger="click">
            <div class="user-info">
              <el-avatar 
                :size="32" 
                :src="avatarUrl"
                :style="{ backgroundColor: userStore.user?.avatar ? 'transparent' : '#1890ff' }"
                @error="handleAvatarError"
              >
                {{ userStore.user?.username?.charAt(0)?.toUpperCase() }}
              </el-avatar>
              <span class="username">
                <template v-if="userStore.loaded">
                  {{ userStore.user?.username || $t('auth.notLoggedIn') }}
                </template>
                <template v-else>
                  {{ $t('common.loading') }}
                </template>
              </span>
              <el-icon class="arrow-down"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="profile">
                  <el-icon><User /></el-icon>
                  <span>{{ $t('nav.profile') }}</span>
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>
                  <span>{{ $t('auth.logout') }}</span>
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
import { useI18n } from 'vue-i18n'
import { ElNotification } from 'element-plus'
import ThemeToggle from '@/components/ThemeToggle.vue'
import LanguageSwitch from '@/components/LanguageSwitch.vue'
import { 
  Histogram, 
  DataAnalysis,
  Document, 
  Monitor,
  Connection,
  Setting, 
  ArrowDown,
  User,
  SwitchButton,
  Fold,
  Expand,
  Clock,
  Files,
  Bell,
  Warning,
  Notebook,
  Message,
  List,
} from '@element-plus/icons-vue'
import axios from 'axios'
import defaultAvatar from '@/assets/avatar/default-avatar.jpeg'
import { useUserStore } from '@/stores/user'
const userStore = useUserStore()

const isCollapsed = ref(localStorage.getItem('isCollapsedSideBar') === 'true')
const router = useRouter()

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

const { t } = useI18n()

function getGreeting() {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 11) {
    return { text: t('common.goodMorning'), emoji: '🌅' }
  } else if (hour >= 11 && hour < 13) {
    return { text: t('common.goodNoon'), emoji: '☀️' }
  } else if (hour >= 13 && hour < 18) {
    return { text: t('common.goodAfternoon'), emoji: '🌤️' }
  } else if (hour >= 18 && hour < 22) {
    return { text: t('common.goodEvening'), emoji: '🌙' }
  } else {
    return { text: t('common.goodNight'), emoji: '🌃' }
  }
}

onMounted(async () => {
  isCollapsed.value = localStorage.getItem('isCollapsedSideBar') === 'true'
  if (!userStore.loaded) {
    await userStore.fetchUser()
  }
  if (!userStore.user) {
    userStore.clearUser()
    router.push('/login')
    return
  }
  if (!sessionStorage.getItem('welcome_shown') && userStore.user && userStore.user.username) {
    const { text, emoji } = getGreeting()
    ElNotification({
      title: `${text} ${emoji}`,
      message: `${t('auth.welcomeBack')}，${userStore.user.username}！`,
      type: 'success',
      duration: 0,
      showClose: true,
      offset: 50,
      position: 'top-right'
    })
    sessionStorage.setItem('welcome_shown', '1')
  }
})

function toggleSidebar() {
  isCollapsed.value = !isCollapsed.value
  localStorage.setItem('isCollapsedSideBar', isCollapsed.value)
}

const username = computed(() => userStore.user?.username)
const avatarUrl = computed(() => {
  if (!userStore.user || !userStore.user.avatar) return defaultAvatar
  return `${API_BASE_URL}${userStore.user.avatar}`
})
const isAdmin = computed(() => userStore.user && userStore.user.is_admin === true)

const handleCommand = async (command) => {
  if (command === 'profile') {
    router.push('/profile')
  } else if (command === 'logout') {
    try {
      // 调用退出登录API记录审计日志
      await axios.post('/api/auth/logout')
    } catch (error) {
      console.warn('退出登录审计记录失败:', error)
    }
    
    // 清除本地存储
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')

    // 清除sessionStorage
    sessionStorage.removeItem('welcome_shown')

    // 清除axios默认请求头
    delete axios.defaults.headers.common['Authorization']
    // 跳转到登录页
    userStore.logout()
    router.push('/login')
  }
}

const handleAvatarError = () => {
  // 当头像加载失败时，使用默认头像
  if (userStore.user) userStore.user.avatar = defaultAvatar
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
  width: var(--sidebar-width);
  min-width: 60px;
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
  height: 45px;
  font-weight: 500;
  line-height: 48px;
  border-radius: 16px;
  color: var(--sidebar-text);
  font-size: 14px;
  transition: background 0.25s, color 0.25s, box-shadow 0.25s, border 0.25s;
  display: flex;
  align-items: center;
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
  color: var(--text-secondary);
  transition: color 0.25s, transform 0.25s;
  margin-right: 10px
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

.menu-group-title {
  font-size: 13px;
  color: #888;
  margin: 18px 0 6px 24px;
  letter-spacing: 1px;
  font-weight: 500;
  user-select: none;
}
</style> 