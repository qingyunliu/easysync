<template>
  <div v-if="error" class="error-boundary">
    <el-result
      icon="error"
      title="组件渲染错误"
      :sub-title="error.message"
    >
      <template #extra>
        <el-button type="primary" @click="handleReset">重试</el-button>
        <el-button @click="handleReport">报告问题</el-button>
      </template>
    </el-result>
  </div>
  <slot v-else></slot>
</template>

<script setup>
import { ref, onErrorCaptured } from 'vue'
import { ElMessage } from 'element-plus'

const error = ref(null)

onErrorCaptured((err, instance, info) => {
  error.value = err
  console.error('组件错误:', err)
  console.error('错误信息:', info)
  return false // 阻止错误继续传播
})

const handleReset = () => {
  error.value = null
}

const handleReport = () => {
  const errorInfo = {
    message: error.value.message,
    stack: error.value.stack,
    component: error.value.componentName,
    timestamp: new Date().toISOString()
  }
  
  // 这里可以添加错误上报逻辑
  console.error('错误详情:', errorInfo)
  ElMessage.success('错误已记录，我们会尽快处理')
}
</script>

<style scoped>
.error-boundary {
  padding: 20px;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}
</style> 