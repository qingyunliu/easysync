<template>
  <div class="nas-to-nas-options">
    <el-form :model="form" label-width="120px">
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="rsync参数">
            <el-input
              v-model="form.rsync_args"
              placeholder="--exclude=*.tmp --include=*.jpg"
              @input="updateModelValue"
            />
            <div class="form-tip">自定义rsync参数，多个参数用空格分隔</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="同步模式">
            <el-select v-model="form.sync_mode" style="width: 100%" @change="updateModelValue">
              <el-option label="增量同步" value="incremental" />
              <el-option label="完全同步" value="full" />
              <el-option label="镜像同步" value="mirror" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="保留权限">
            <el-switch
              v-model="form.preserve_permissions"
              @change="updateModelValue"
            />
            <div class="form-tip">是否保留文件权限和所有者信息</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="保留时间戳">
            <el-switch
              v-model="form.preserve_timestamps"
              @change="updateModelValue"
            />
            <div class="form-tip">是否保留文件的修改时间</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="硬链接优化">
            <el-switch
              v-model="form.hard_links"
              @change="updateModelValue"
            />
            <div class="form-tip">使用硬链接优化存储空间</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="稀疏文件">
            <el-switch
              v-model="form.sparse_files"
              @change="updateModelValue"
            />
            <div class="form-tip">优化稀疏文件的传输</div>
          </el-form-item>
        </el-col>
      </el-row>
      
      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="部分传输">
            <el-switch
              v-model="form.partial"
              @change="updateModelValue"
            />
            <div class="form-tip">支持断点续传</div>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="进度显示">
            <el-switch
              v-model="form.progress"
              @change="updateModelValue"
            />
            <div class="form-tip">显示详细的传输进度</div>
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