<template>
  <div class="nas-to-nas-options">
    <el-form :model="form" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.rsyncArgs')">
            <el-input v-model="form.rsync_args" :placeholder="$t('nasToNasOptions.rsyncArgsPlaceholder')"
              @input="updateModelValue" />
            <div class="form-tip">{{ $t('nasToNasOptions.rsyncArgsTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.syncMode')">
            <el-select v-model="form.sync_mode" style="width: 100%" @change="updateModelValue">
              <el-option :label="$t('nasToNasOptions.incrementalSync')" value="incremental" />
              <el-option :label="$t('nasToNasOptions.fullSync')" value="full" />
              <el-option :label="$t('nasToNasOptions.mirrorSync')" value="mirror" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.preservePermissions')">
            <el-switch v-model="form.preserve_permissions" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToNasOptions.preservePermissionsTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.preserveTimestamps')">
            <el-switch v-model="form.preserve_timestamps" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToNasOptions.preserveTimestampsTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.hardLinks')">
            <el-switch v-model="form.hard_links" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToNasOptions.hardLinksTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.sparseFiles')">
            <el-switch v-model="form.sparse_files" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToNasOptions.sparseFilesTip') }}</div>
          </el-form-item>
        </el-col>
      </el-row>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.partialTransfer')">
            <el-switch v-model="form.partial" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToNasOptions.partialTransferTip') }}</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item :label="$t('nasToNasOptions.progressDisplay')">
            <el-switch v-model="form.progress" @change="updateModelValue" />
            <div class="form-tip">{{ $t('nasToNasOptions.progressDisplayTip') }}</div>
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
      rsync_args: '',
      sync_mode: 'incremental',
      preserve_permissions: true,
      preserve_timestamps: true,
      hard_links: false,
      sparse_files: false,
      partial: true,
      progress: true
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
  rsync_args: props.modelValue.rsync_args || '',
  sync_mode: props.modelValue.sync_mode || 'incremental',
  preserve_permissions: props.modelValue.preserve_permissions !== false,
  preserve_timestamps: props.modelValue.preserve_timestamps !== false,
  hard_links: props.modelValue.hard_links || false,
  sparse_files: props.modelValue.sparse_files || false,
  partial: props.modelValue.partial !== false,
  progress: props.modelValue.progress !== false
})

// 方法
const updateModelValue = () => {
  const value = {
    rsync_args: form.value.rsync_args,
    sync_mode: form.value.sync_mode,
    preserve_permissions: form.value.preserve_permissions,
    preserve_timestamps: form.value.preserve_timestamps,
    hard_links: form.value.hard_links,
    sparse_files: form.value.sparse_files,
    partial: form.value.partial,
    progress: form.value.progress
  }
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  form.value = {
    rsync_args: newValue.rsync_args || '',
    sync_mode: newValue.sync_mode || 'incremental',
    preserve_permissions: newValue.preserve_permissions !== false,
    preserve_timestamps: newValue.preserve_timestamps !== false,
    hard_links: newValue.hard_links || false,
    sparse_files: newValue.sparse_files || false,
    partial: newValue.partial !== false,
    progress: newValue.progress !== false
  }
}, { deep: true })
</script>

<style scoped>
.nas-to-nas-options {
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