<template>
  <div class="language-toggle">
    <el-tooltip :content="tooltipText" placement="bottom">
      <div class="toggle-button" @click="toggleLanguage">
        <span class="language-text">{{ currentLanguage === 'zh-CN' ? '中' : 'EN' }}</span>
      </div>
    </el-tooltip>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { setLocale } from '@/i18n'

const { locale, t } = useI18n()

const currentLanguage = computed(() => locale.value)

const tooltipText = computed(() => {
  return currentLanguage.value === 'zh-CN' ? 'Switch to English' : '切换到中文'
})

const toggleLanguage = () => {
  const newLang = currentLanguage.value === 'zh-CN' ? 'en-US' : 'zh-CN'
  setLocale(newLang)
}
</script>

<style scoped>
.language-toggle {
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

.language-text {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-color);
  transition: all 0.3s ease;
  letter-spacing: 0.5px;
}

.toggle-button:hover .language-text {
  color: #409eff;
  transform: scale(1.1);
}
</style>