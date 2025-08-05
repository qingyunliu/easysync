<template>
  <div class="obs-to-obs-options">
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
          <el-form-item label="传输模式">
            <el-select v-model="form.transfer_mode" style="width: 100%" @change="updateModelValue">
              <el-option label="直接传输" value="direct" />
              <el-option label="本地中转" value="local" />
              <el-option label="流式传输" value="streaming" />
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
            <div class="form-tip">大文件分块传输的块大小</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="并发传输数">
            <el-input-number
              v-model="form.transfer_concurrency"
              :min="1"
              :max="20"
              placeholder="并发数"
              style="width: 100%"
              @change="updateModelValue"
            />
            <div class="form-tip">同时传输的文件数量</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="加密传输">
            <el-switch
              v-model="form.encrypt_transfer"
              @change="updateModelValue"
            />
            <div class="form-tip">使用TLS加密传输数据</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="服务器端加密">
            <el-switch
              v-model="form.server_side_encryption"
              @change="updateModelValue"
            />
            <div class="form-tip">在目标对象存储端加密数据</div>
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
          <el-form-item label="校验和验证">
            <el-switch
              v-model="form.checksum_verification"
              @change="updateModelValue"
            />
            <div class="form-tip">传输后验证文件完整性</div>
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
          <el-form-item label="进度报告">
            <el-switch
              v-model="form.progress_reporting"
              @change="updateModelValue"
            />
            <div class="form-tip">实时报告传输进度</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="临时目录">
            <el-input
              v-model="form.temp_directory"
              placeholder="/tmp/obs_transfer"
              @input="updateModelValue"
            />
            <div class="form-tip">本地中转时的临时存储目录</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="清理临时文件">
            <el-switch
              v-model="form.cleanup_temp"
              @change="updateModelValue"
            />
            <div class="form-tip">传输完成后清理临时文件</div>
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
      transfer_mode: 'direct',
      chunk_size: 64,
      transfer_concurrency: 4,
      encrypt_transfer: true,
      server_side_encryption: false,
      preserve_metadata: true,
      checksum_verification: true,
      retry_strategy: 'exponential',
      progress_reporting: true,
      temp_directory: '/tmp/obs_transfer',
      cleanup_temp: true
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
  transfer_mode: props.modelValue.transfer_mode || 'direct',
  chunk_size: props.modelValue.chunk_size || 64,
  transfer_concurrency: props.modelValue.transfer_concurrency || 4,
  encrypt_transfer: props.modelValue.encrypt_transfer !== false,
  server_side_encryption: props.modelValue.server_side_encryption || false,
  preserve_metadata: props.modelValue.preserve_metadata !== false,
  checksum_verification: props.modelValue.checksum_verification !== false,
  retry_strategy: props.modelValue.retry_strategy || 'exponential',
  progress_reporting: props.modelValue.progress_reporting !== false,
  temp_directory: props.modelValue.temp_directory || '/tmp/obs_transfer',
  cleanup_temp: props.modelValue.cleanup_temp !== false
})

// 方法
const updateModelValue = () => {
  const value = {
    rclone_args: form.value.rclone_args,
    transfer_mode: form.value.transfer_mode,
    chunk_size: form.value.chunk_size,
    transfer_concurrency: form.value.transfer_concurrency,
    encrypt_transfer: form.value.encrypt_transfer,
    server_side_encryption: form.value.server_side_encryption,
    preserve_metadata: form.value.preserve_metadata,
    checksum_verification: form.value.checksum_verification,
    retry_strategy: form.value.retry_strategy,
    progress_reporting: form.value.progress_reporting,
    temp_directory: form.value.temp_directory,
    cleanup_temp: form.value.cleanup_temp
  }
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  form.value = {
    rclone_args: newValue.rclone_args || '',
    transfer_mode: newValue.transfer_mode || 'direct',
    chunk_size: newValue.chunk_size || 64,
    transfer_concurrency: newValue.transfer_concurrency || 4,
    encrypt_transfer: newValue.encrypt_transfer !== false,
    server_side_encryption: newValue.server_side_encryption || false,
    preserve_metadata: newValue.preserve_metadata !== false,
    checksum_verification: newValue.checksum_verification !== false,
    retry_strategy: newValue.retry_strategy || 'exponential',
    progress_reporting: newValue.progress_reporting !== false,
    temp_directory: newValue.temp_directory || '/tmp/obs_transfer',
    cleanup_temp: newValue.cleanup_temp !== false
  }
}, { deep: true })
</script>

<style scoped>
.obs-to-obs-options {
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