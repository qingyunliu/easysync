<template>
  <div class="nas-to-obs-options">
    <el-form :model="form" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.rcloneArgs')">
            <el-input v-model="form.rclone_args" :placeholder="$t('nasToObsOptions.rcloneArgsPlaceholder')"
              @input="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.rcloneArgsTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.transferMode')">
            <el-select v-model="form.transfer_mode" style="width: 100%" @change="updateModelValue">
              <el-option :label="$t('nasToObsOptions.standardTransfer')" value="standard" />
              <el-option :label="$t('nasToObsOptions.streamingTransfer')" value="streaming" />
              <el-option :label="$t('nasToObsOptions.chunkedTransfer')" value="chunked" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.chunkSize')">
            <el-input-number v-model="form.chunk_size" :min="1" :max="1000"
              :placeholder="$t('nasToObsOptions.chunkSizePlaceholder')" style="width: 100%"
              @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.chunkSizeTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.uploadConcurrency')">
            <el-input-number v-model="form.upload_concurrency" :min="1" :max="20"
              :placeholder="$t('nasToObsOptions.uploadConcurrencyPlaceholder')" style="width: 100%"
              @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.uploadConcurrencyTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.encryptTransfer')">
            <el-switch v-model="form.encrypt_transfer" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.encryptTransferTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.serverSideEncryption')">
            <el-switch v-model="form.server_side_encryption" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.serverSideEncryptionTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.preserveMetadata')">
            <el-switch v-model="form.preserve_metadata" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.preserveMetadataTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.checksumVerification')">
            <el-switch v-model="form.checksum_verification" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.checksumVerificationTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.retryStrategy')">
            <el-select v-model="form.retry_strategy" style="width: 100%" @change="updateModelValue">
              <el-option :label="$t('nasToObsOptions.exponentialBackoff')" value="exponential" />
              <el-option :label="$t('nasToObsOptions.fixedInterval')" value="fixed" />
              <el-option :label="$t('nasToObsOptions.immediateRetry')" value="immediate" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToObsOptions.progressReporting')">
            <el-switch v-model="form.progress_reporting" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToObsOptions.progressReportingTip') }}</div>
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
      transfer_mode: 'standard',
      chunk_size: 64,
      upload_concurrency: 4,
      encrypt_transfer: true,
      server_side_encryption: false,
      preserve_metadata: true,
      checksum_verification: true,
      retry_strategy: 'exponential',
      progress_reporting: true
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
  transfer_mode: props.modelValue.transfer_mode || 'standard',
  chunk_size: props.modelValue.chunk_size || 64,
  upload_concurrency: props.modelValue.upload_concurrency || 4,
  encrypt_transfer: props.modelValue.encrypt_transfer !== false,
  server_side_encryption: props.modelValue.server_side_encryption || false,
  preserve_metadata: props.modelValue.preserve_metadata !== false,
  checksum_verification: props.modelValue.checksum_verification !== false,
  retry_strategy: props.modelValue.retry_strategy || 'exponential',
  progress_reporting: props.modelValue.progress_reporting !== false
})

// 方法
const updateModelValue = () => {
  const value = {
    rclone_args: form.value.rclone_args,
    transfer_mode: form.value.transfer_mode,
    chunk_size: form.value.chunk_size,
    upload_concurrency: form.value.upload_concurrency,
    encrypt_transfer: form.value.encrypt_transfer,
    server_side_encryption: form.value.server_side_encryption,
    preserve_metadata: form.value.preserve_metadata,
    checksum_verification: form.value.checksum_verification,
    retry_strategy: form.value.retry_strategy,
    progress_reporting: form.value.progress_reporting
  }
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  form.value = {
    rclone_args: newValue.rclone_args || '',
    transfer_mode: newValue.transfer_mode || 'standard',
    chunk_size: newValue.chunk_size || 64,
    upload_concurrency: newValue.upload_concurrency || 4,
    encrypt_transfer: newValue.encrypt_transfer !== false,
    server_side_encryption: newValue.server_side_encryption || false,
    preserve_metadata: newValue.preserve_metadata !== false,
    checksum_verification: newValue.checksum_verification !== false,
    retry_strategy: newValue.retry_strategy || 'exponential',
    progress_reporting: newValue.progress_reporting !== false
  }
}, { deep: true })
</script>

<style scoped>
.nas-to-obs-options {
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