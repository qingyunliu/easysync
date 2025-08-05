<template>
  <div class="obs-to-nas-options">
    <el-form :model="form" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="rclone参数">
            <el-input
              v-model="form.rclone_args"
              placeholder="--exclude=*.tmp --include=*.jpg"
              @input="updateModelValue"
            />
            <div class="form-tip">自定义rclone参数，多个参数用空格分隔</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="下载模式">
            <el-select v-model="form.download_mode" style="width: 100%" @change="updateModelValue">
              <el-option label="标准下载" value="standard" />
              <el-option label="流式下载" value="streaming" />
              <el-option label="分块下载" value="chunked" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="分块大小(MB)">
            <el-input-number
              v-model="form.chunk_size"
              :min="1"
              :max="1000"
              placeholder="分块大小"
              style="width: 100%"
              @change="updateModelValue"
            />
            <div class="form-tip">大文件分块下载的块大小</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="并发下载数">
            <el-input-number
              v-model="form.download_concurrency"
              :min="1"
              :max="20"
              placeholder="并发数"
              style="width: 100%"
              @change="updateModelValue"
            />
            <div class="form-tip">同时下载的文件数量</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="断点续传">
            <el-switch
              v-model="form.resume_download"
              @change="updateModelValue"
            />
            <div class="form-tip">支持断点续传功能</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="校验和验证">
            <el-switch
              v-model="form.checksum_verification"
              @change="updateModelValue"
            />
            <div class="form-tip">下载后验证文件完整性</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="保留元数据">
            <el-switch
              v-model="form.preserve_metadata"
              @change="updateModelValue"
            />
            <div class="form-tip">保留文件的元数据信息</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="进度报告">
            <el-switch
              v-model="form.progress_reporting"
              @change="updateModelValue"
            />
            <div class="form-tip">实时报告下载进度</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="重试策略">
            <el-select v-model="form.retry_strategy" style="width: 100%" @change="updateModelValue">
              <el-option label="指数退避" value="exponential" />
              <el-option label="固定间隔" value="fixed" />
              <el-option label="立即重试" value="immediate" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="临时目录">
            <el-input
              v-model="form.temp_directory"
              placeholder="/tmp/downloads"
              @input="updateModelValue"
            />
            <div class="form-tip">下载文件的临时存储目录</div>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      rclone_args: '',
      download_mode: 'standard',
      chunk_size: 64,
      download_concurrency: 4,
      resume_download: true,
      checksum_verification: true,
      preserve_metadata: true,
      progress_reporting: true,
      retry_strategy: 'exponential',
      temp_directory: '/tmp/downloads'
    })
  },
  sourceStorage: {
    type: Object,
    default: () => ({})
  },
  targetStorage: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 响应式数据
const form = ref({
  rclone_args: props.modelValue.rclone_args || '',
  download_mode: props.modelValue.download_mode || 'standard',
  chunk_size: props.modelValue.chunk_size || 64,
  download_concurrency: props.modelValue.download_concurrency || 4,
  resume_download: props.modelValue.resume_download !== false,
  checksum_verification: props.modelValue.checksum_verification !== false,
  preserve_metadata: props.modelValue.preserve_metadata !== false,
  progress_reporting: props.modelValue.progress_reporting !== false,
  retry_strategy: props.modelValue.retry_strategy || 'exponential',
  temp_directory: props.modelValue.temp_directory || '/tmp/downloads'
})

// 方法
const updateModelValue = () => {
  const value = {
    rclone_args: form.value.rclone_args,
    download_mode: form.value.download_mode,
    chunk_size: form.value.chunk_size,
    download_concurrency: form.value.download_concurrency,
    resume_download: form.value.resume_download,
    checksum_verification: form.value.checksum_verification,
    preserve_metadata: form.value.preserve_metadata,
    progress_reporting: form.value.progress_reporting,
    retry_strategy: form.value.retry_strategy,
    temp_directory: form.value.temp_directory
  }
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  form.value = {
    rclone_args: newValue.rclone_args || '',
    download_mode: newValue.download_mode || 'standard',
    chunk_size: newValue.chunk_size || 64,
    download_concurrency: newValue.download_concurrency || 4,
    resume_download: newValue.resume_download !== false,
    checksum_verification: newValue.checksum_verification !== false,
    preserve_metadata: newValue.preserve_metadata !== false,
    progress_reporting: newValue.progress_reporting !== false,
    retry_strategy: newValue.retry_strategy || 'exponential',
    temp_directory: newValue.temp_directory || '/tmp/downloads'
  }
}, { deep: true })
</script>

<style scoped>
.obs-to-nas-options {
  padding: 10px 0;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}
</style> 