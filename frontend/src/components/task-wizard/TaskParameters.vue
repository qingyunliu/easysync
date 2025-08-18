<template>
  <div class="task-parameters">
    <!-- 页面标题 -->
    <div class="parameters-header">
      <h3>{{ $t('taskParameters.configureTaskParameters') }}</h3>
      <p class="parameters-description">{{ $t('taskParameters.configureTaskParametersDesc') }}</p>
    </div>

    <!-- 基础信息 -->
    <el-collapse v-model="activeNames" accordion>
      <el-collapse-item name="basic" :title="$t('taskParameters.basicInfo')">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:information" class="title-icon" />
            <span>{{ $t('taskParameters.basicInfo') }}</span>
          </div>
        </template>

        <div class="collapse-content">
          <el-form :model="form" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.taskName')" required>
                  <el-input v-model="form.taskName" :placeholder="$t('taskParameters.enterTaskName')"
                    @input="updateModelValue" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.priority')">
                  <el-select v-model="form.priority" style="width: 100%" @change="updateModelValue">
                    <el-option :label="$t('taskParameters.priorities.low')" :value="1">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon low" />
                        <span>{{ $t('taskParameters.priorities.low') }}</span>
                      </div>
                    </el-option>
                    <el-option :label="$t('taskParameters.priorities.normal')" :value="2">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon normal" />
                        <span>{{ $t('taskParameters.priorities.normal') }}</span>
                      </div>
                    </el-option>
                    <el-option :label="$t('taskParameters.priorities.high')" :value="3">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon high" />
                        <span>{{ $t('taskParameters.priorities.high') }}</span>
                      </div>
                    </el-option>
                    <el-option :label="$t('taskParameters.priorities.urgent')" :value="4">
                      <div class="priority-option">
                        <Icon icon="mdi:flag" class="priority-icon urgent" />
                        <span>{{ $t('taskParameters.priorities.urgent') }}</span>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item :label="$t('taskParameters.taskDescription')">
              <el-input v-model="form.description" type="textarea" :rows="3"
                :placeholder="$t('taskParameters.enterTaskDescription')" @input="updateModelValue" />
            </el-form-item>
          </el-form>
        </div>
      </el-collapse-item>

      <!-- 同步选项 -->
      <el-collapse-item name="sync" :title="$t('taskParameters.syncOptions')">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:sync" class="title-icon" />
            <span>{{ $t('taskParameters.syncOptions') }}</span>
          </div>
        </template>

        <div class="collapse-content">
          <el-form :model="form.syncOptions" label-width="120px">
            <div class="options-grid">
              <div class="option-item">
                <el-checkbox v-model="form.syncOptions.delete" @change="updateModelValue">
                  <div class="option-content">
                    <Icon icon="mdi:delete" class="option-icon" />
                    <div class="option-text">
                      <div class="option-title">{{ $t('taskParameters.deleteExtraFiles') }}</div>
                      <div class="option-desc">{{ $t('taskParameters.deleteExtraFilesDesc') }}</div>
                    </div>
                  </div>
                </el-checkbox>
              </div>

              <div class="option-item">
                <el-checkbox v-model="form.syncOptions.compress" @change="updateModelValue">
                  <div class="option-content">
                    <Icon icon="mdi:compress" class="option-icon" />
                    <div class="option-text">
                      <div class="option-title">{{ $t('taskParameters.enableCompression') }}</div>
                      <div class="option-desc">{{ $t('taskParameters.enableCompressionDesc') }}</div>
                    </div>
                  </div>
                </el-checkbox>
              </div>

              <div class="option-item">
                <el-checkbox v-model="form.syncOptions.checksum" @change="updateModelValue">
                  <div class="option-content">
                    <Icon icon="mdi:check-circle" class="option-icon" />
                    <div class="option-text">
                      <div class="option-title">{{ $t('taskParameters.checksumVerification') }}</div>
                      <div class="option-desc">{{ $t('taskParameters.checksumVerificationDesc') }}</div>
                    </div>
                  </div>
                </el-checkbox>
              </div>
            </div>

            <el-divider />

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.bandwidthLimit')">
                  <el-input-number v-model="form.syncOptions.bandwidth_limit" :min="0" :max="1000"
                    :placeholder="$t('taskParameters.bandwidthLimitPlaceholder')" style="width: 100%"
                    @change="updateModelValue">
                    <template #suffix>MB/s</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.maxConnections')">
                  <el-input-number v-model="form.syncOptions.max_connections" :min="1" :max="10"
                    :placeholder="$t('taskParameters.maxConnectionsPlaceholder')" style="width: 100%"
                    @change="updateModelValue" />
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-collapse-item>

      <!-- 传输策略 -->
      <el-collapse-item name="retry" :title="$t('taskParameters.transferStrategy')">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:connection" class="title-icon" />
            <span>{{ $t('taskParameters.transferStrategy') }}</span>
          </div>
        </template>

        <div class="collapse-content">
          <el-form :model="form.retryOptions" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.retryCount')">
                  <el-input-number v-model="form.retryOptions.max_retries" :min="0" :max="10"
                    :placeholder="$t('taskParameters.retryCountPlaceholder')" style="width: 100%"
                    @change="updateModelValue" />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.retryInterval')">
                  <el-input-number v-model="form.retryOptions.retry_interval" :min="5" :max="300"
                    :placeholder="$t('taskParameters.retryIntervalPlaceholder')" style="width: 100%"
                    @change="updateModelValue">
                    <template #suffix>{{ $t('common.seconds') }}</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-collapse-item>

      <!-- 高级参数 -->
      <el-collapse-item name="advanced" :title="$t('taskParameters.advancedParameters')">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:cog" class="title-icon" />
            <span>{{ $t('taskParameters.advancedParameters') }}</span>
          </div>
        </template>

        <div class="collapse-content">
          <el-form :model="form.advancedOptions" label-width="120px">
            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.bufferSize')">
                  <el-input-number v-model="form.advancedOptions.buffer_size" :min="1" :max="100"
                    :placeholder="$t('taskParameters.bufferSizePlaceholder')" style="width: 100%"
                    @change="updateModelValue">
                    <template #suffix>MB</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.timeout')">
                  <el-input-number v-model="form.advancedOptions.timeout" :min="30" :max="3600"
                    :placeholder="$t('taskParameters.timeoutPlaceholder')" style="width: 100%"
                    @change="updateModelValue">
                    <template #suffix>{{ $t('common.seconds') }}</template>
                  </el-input-number>
                </el-form-item>
              </el-col>
            </el-row>

            <el-row :gutter="20">
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.excludePatterns')">
                  <el-input v-model="form.advancedOptions.exclude_patterns"
                    :placeholder="$t('taskParameters.excludePatternsPlaceholder')" @input="updateModelValue" />
                  <div class="form-tip">{{ $t('taskParameters.patternsTip') }}</div>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item :label="$t('taskParameters.includePatterns')">
                  <el-input v-model="form.advancedOptions.include_patterns"
                    :placeholder="$t('taskParameters.includePatternsPlaceholder')" @input="updateModelValue" />
                  <div class="form-tip">{{ $t('taskParameters.patternsTip') }}</div>
                </el-form-item>
              </el-col>
            </el-row>
          </el-form>
        </div>
      </el-collapse-item>

      <!-- 场景特定参数 -->
      <el-collapse-item v-if="showScenarioOptions" name="scenario" :title="scenarioTitle">
        <template #title>
          <div class="collapse-title">
            <Icon icon="mdi:settings" class="title-icon" />
            <span>{{ scenarioTitle }}</span>
          </div>
        </template>

        <div class="collapse-content">
          <component :is="scenarioComponent" v-model="form.scenarioOptions" :source-storage="sourceStorage"
            :target-storage="targetStorage" @change="updateModelValue" />
        </div>
      </el-collapse-item>
    </el-collapse>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { Icon } from '@iconify/vue'
import NasToNasOptions from './scenarios/NasToNasOptions.vue'
import NasToObsOptions from './scenarios/NasToObsOptions.vue'
import ObsToNasOptions from './scenarios/ObsToNasOptions.vue'
import ObsToObsOptions from './scenarios/ObsToObsOptions.vue'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      taskName: '',
      description: '',
      priority: 2,
      syncOptions: {
        delete: false,
        compress: false,
        checksum: true,
        bandwidth_limit: 0,
        max_connections: 1
      },
      retryOptions: {
        max_retries: 3,
        retry_interval: 30
      },
      advancedOptions: {
        buffer_size: 10,
        timeout: 300,
        exclude_patterns: '',
        include_patterns: ''
      },
      scenarioOptions: {}
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
const activeNames = ref(['basic'])
const form = ref({
  taskName: props.modelValue.taskName || '',
  description: props.modelValue.description || '',
  priority: props.modelValue.priority || 2,
  syncOptions: {
    delete: props.modelValue.syncOptions?.delete || false,
    compress: props.modelValue.syncOptions?.compress || false,
    checksum: props.modelValue.syncOptions?.checksum || true,
    bandwidth_limit: props.modelValue.syncOptions?.bandwidth_limit || 0,
    max_connections: props.modelValue.syncOptions?.max_connections || 1
  },
  retryOptions: {
    max_retries: props.modelValue.retryOptions?.max_retries || 3,
    retry_interval: props.modelValue.retryOptions?.retry_interval || 30
  },
  advancedOptions: {
    buffer_size: props.modelValue.advancedOptions?.buffer_size || 10,
    timeout: props.modelValue.advancedOptions?.timeout || 300,
    exclude_patterns: props.modelValue.advancedOptions?.exclude_patterns || '',
    include_patterns: props.modelValue.advancedOptions?.include_patterns || ''
  },
  scenarioOptions: props.modelValue.scenarioOptions || {}
})

// 计算属性
const showScenarioOptions = computed(() => {
  const result = props.sourceStorage.storageType && props.targetStorage.storageType
  return result
})

const scenarioTitle = computed(() => {
  if (!showScenarioOptions.value) return ''

  const sourceType = props.sourceStorage.storageType === 's3' ? 'OBS' : 'NAS'
  const targetType = props.targetStorage.storageType === 's3' ? 'OBS' : 'NAS'
  return `${sourceType}到${targetType}参数`
})

const scenarioComponent = computed(() => {
  if (!showScenarioOptions.value) return null

  const sourceType = props.sourceStorage.storageType === 's3' ? 'obs' : 'nas'
  const targetType = props.targetStorage.storageType === 's3' ? 'obs' : 'nas'

  if (sourceType === 'nas' && targetType === 'nas') {
    return NasToNasOptions
  } else if (sourceType === 'nas' && targetType === 'obs') {
    return NasToObsOptions
  } else if (sourceType === 'obs' && targetType === 'nas') {
    return ObsToNasOptions
  } else if (sourceType === 'obs' && targetType === 'obs') {
    return ObsToObsOptions
  }
  return null
})

// 方法
const updateModelValue = () => {
  const value = {
    taskName: form.value.taskName,
    description: form.value.description,
    priority: form.value.priority,
    syncOptions: { ...form.value.syncOptions },
    retryOptions: { ...form.value.retryOptions },
    advancedOptions: { ...form.value.advancedOptions },
    scenarioOptions: { ...form.value.scenarioOptions }
  }
  emit('update:modelValue', value)
  emit('change', value)
}

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue) {
    form.value = {
      taskName: newValue.taskName || '',
      description: newValue.description || '',
      priority: newValue.priority || 2,
      syncOptions: {
        delete: newValue.syncOptions?.delete || false,
        compress: newValue.syncOptions?.compress || false,
        checksum: newValue.syncOptions?.checksum || true,
        bandwidth_limit: newValue.syncOptions?.bandwidth_limit || 0,
        max_connections: newValue.syncOptions?.max_connections || 1
      },
      retryOptions: {
        max_retries: newValue.retryOptions?.max_retries || 3,
        retry_interval: newValue.retryOptions?.retry_interval || 30
      },
      advancedOptions: {
        buffer_size: newValue.advancedOptions?.buffer_size || 10,
        timeout: newValue.advancedOptions?.timeout || 300,
        exclude_patterns: newValue.advancedOptions?.exclude_patterns || '',
        include_patterns: newValue.advancedOptions?.include_patterns || ''
      },
      scenarioOptions: newValue.scenarioOptions || {}
    }
  }
}, { immediate: true })
</script>

<style scoped>
.task-parameters {
  padding: 20px;
}

.parameters-header {
  margin-bottom: 30px;
}

.parameters-header h3 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 20px;
  font-weight: 600;
}

.parameters-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.collapse-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.title-icon {
  font-size: 18px;
  color: var(--el-color-primary);
}

.collapse-content {
  padding: 20px 0;
}

.options-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.option-item {
  border: 1px solid var(--el-border-color-light);
  border-radius: 8px;
  padding: 16px;
  background: var(--el-bg-color-page);
  transition: all 0.2s;
}

.option-item:hover {
  border-color: var(--el-color-primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.option-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.option-icon {
  font-size: 20px;
  color: var(--el-color-primary);
  margin-top: 2px;
}

.option-text {
  flex: 1;
}

.option-title {
  font-weight: 500;
  color: var(--el-text-color-primary);
  margin-bottom: 4px;
}

.option-desc {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  line-height: 1.4;
}

.priority-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.priority-icon {
  font-size: 16px;
}

.priority-icon.low {
  color: #67c23a;
}

.priority-icon.normal {
  color: #409eff;
}

.priority-icon.high {
  color: #e6a23c;
}

.priority-icon.urgent {
  color: #f56c6c;
}

.form-tip {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

:deep(.el-collapse) {
  border: none;
  background: transparent;
}

:deep(.el-collapse-item__header) {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  margin-bottom: 8px;
  padding: 16px 20px;
  font-size: 16px;
  font-weight: 500;
  transition: all 0.2s;
}

:deep(.el-collapse-item__header:hover) {
  background: var(--el-color-primary-light-9);
  border-color: var(--el-color-primary);
}

:deep(.el-collapse-item__header.is-active) {
  background: var(--el-color-primary-light-8);
  border-color: var(--el-color-primary);
}

:deep(.el-collapse-item__content) {
  background: var(--el-bg-color);
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  margin-bottom: 8px;
  padding: 20px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
  transition: box-shadow 0.2s;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.el-checkbox__label) {
  font-weight: 500;
}

:deep(.el-divider) {
  margin: 24px 0;
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-input-number .el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
}

:deep(.el-input-number .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-input-number .el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}
</style>