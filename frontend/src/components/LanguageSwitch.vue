<template>
  <el-dropdown @command="handleLanguageChange" trigger="click">
    <div class="language-switch">
      <span class="language-icon">🌐</span>
      <span class="language-text">{{ currentLanguageText }}</span>
      <el-icon class="el-icon--right"><arrow-down /></el-icon>
    </div>
    <template #dropdown>
      <el-dropdown-menu>
        <el-dropdown-item command="zh-CN">
          <span class="flag">🇨🇳</span>
          中文
        </el-dropdown-item>
        <el-dropdown-item command="en-US">
          <span class="flag">🇺🇸</span>
          English
        </el-dropdown-item>
      </el-dropdown-menu>
    </template>
  </el-dropdown>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { ArrowDown } from '@element-plus/icons-vue'
import { setLocale } from '@/i18n'

const { locale } = useI18n()

const currentLanguageText = computed(() => {
  return locale.value === 'zh-CN' ? '中文' : 'English'
})

const handleLanguageChange = (lang) => {
  setLocale(lang)
}
</script>

<style scoped>
.language-switch {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 12px;
  border-radius: 4px;
  transition: background-color 0.3s;
}

.language-switch:hover {
  background-color: var(--el-fill-color-light);
}

.language-text {
  margin: 0 4px;
  font-size: 14px;
}

.language-icon {
  font-size: 16px;
  margin-right: 4px;
}

.flag {
  margin-right: 8px;
  font-size: 16px;
}
</style>
