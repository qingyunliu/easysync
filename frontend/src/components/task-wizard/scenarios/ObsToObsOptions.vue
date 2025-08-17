<template>
  <div class="obs-to-obs-options">
    <el-form :model="form" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.rcloneArgs')">
            <el-input
              v-model="form.rclone_args"
              :placeholder="$t('obsToObsOptions.rcloneArgsPlaceholder')"
              @input="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.rcloneArgsTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.transferMode')">
            <el-select v-model="form.transfer_mode" style="width: 100%" @change="updateModelValue">
              <el-option :label="$t('obsToObsOptions.directTransfer')" value="direct" />
              <el-option :label="$t('obsToObsOptions.localTransfer')" value="local" />
              <el-option :label="$t('obsToObsOptions.streamingTransfer')" value="streaming" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.chunkSize')">
            <el-input-number
              v-model="form.chunk_size"
              :min="1"
              :max="1000"
              :placeholder="$t('obsToObsOptions.chunkSizePlaceholder')"
              style="width: 100%"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.chunkSizeTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.transferConcurrency')">
            <el-input-number
              v-model="form.transfer_concurrency"
              :min="1"
              :max="20"
              :placeholder="$t('obsToObsOptions.transferConcurrencyPlaceholder')"
              style="width: 100%"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.transferConcurrencyTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.encryptTransfer')">
            <el-switch
              v-model="form.encrypt_transfer"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.encryptTransferTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.serverSideEncryption')">
            <el-switch
              v-model="form.server_side_encryption"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.serverSideEncryptionTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.preserveMetadata')">
            <el-switch
              v-model="form.preserve_metadata"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.preserveMetadataTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.checksumVerification')">
            <el-switch
              v-model="form.checksum_verification"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.checksumVerificationTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.retryStrategy')">
            <el-select v-model="form.retry_strategy" style="width: 100%" @change="updateModelValue">
              <el-option :label="$t('obsToObsOptions.exponentialBackoff')" value="exponential" />
              <el-option :label="$t('obsToObsOptions.fixedInterval')" value="fixed" />
              <el-option :label="$t('obsToObsOptions.immediateRetry')" value="immediate" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.progressReporting')">
            <el-switch
              v-model="form.progress_reporting"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.progressReportingTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.tempDirectory')">
            <el-input
              v-model="form.temp_directory"
              :placeholder="$t('obsToObsOptions.tempDirectoryPlaceholder')"
              @input="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.tempDirectoryTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('obsToObsOptions.cleanupTemp')">
            <el-switch
              v-model="form.cleanup_temp"
              @change="updateModelValue"
            />
            <div class="form-tip">{{ $t('obsToObsOptions.cleanupTempTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

const { t } = useI18n()

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