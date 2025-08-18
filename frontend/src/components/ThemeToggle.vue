<template>
  <div class="theme-toggle" @click="toggleTheme">
    <el-tooltip :content="tooltipText" placement="bottom">
      <div class="toggle-button">
        <el-icon class="theme-icon">
          <component :is="currentTheme === 'light' ? Sunny : Moon" />
        </el-icon>
      </div>
    </el-tooltip>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { Sunny, Moon } from '@element-plus/icons-vue'

// 当前主题状态
const currentTheme = ref('light')

// 计算属性
const tooltipText = computed(() => {
  return currentTheme.value === 'light' ? '切换到深色模式' : '切换到浅色模式'
})

// 切换主题
const toggleTheme = () => {
  const newTheme = currentTheme.value === 'light' ? 'dark' : 'light'
  setTheme(newTheme)
}

// 设置主题
const setTheme = (theme) => {
  currentTheme.value = theme
  document.documentElement.setAttribute('data-theme', theme)
  localStorage.setItem('theme', theme)

  // 添加切换动画
  document.documentElement.classList.add('theme-transition')
  setTimeout(() => {
    document.documentElement.classList.remove('theme-transition')
  }, 300)
}

// 初始化主题
const initTheme = () => {
  const savedTheme = localStorage.getItem('theme') || 'light'
  setTheme(savedTheme)
}

// 组件挂载时初始化主题
onMounted(() => {
  initTheme()
})
</script>

<style scoped>
.theme-toggle {
  display: flex;
  align-items: center;
  margin-right: 16px;
}

.toggle-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.toggle-button:hover {
  background: var(--bg-tertiary);
  transform: scale(1.05);
}

.theme-icon {
  font-size: 16px;
  color: var(--text-color);
  transition: all 0.3s ease;
}

.toggle-button:hover .theme-icon {
  transform: rotate(180deg);
  color: #409eff;
}
</style>