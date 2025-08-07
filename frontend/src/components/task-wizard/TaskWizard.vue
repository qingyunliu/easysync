<template>
  <div class="task-wizard">
    <!-- 复制任务提示 -->
    <div v-if="copyFromTask" class="copy-notice">
      <el-alert
        title="正在复制任务配置"
        :description="`正在复制任务 '${copyFromTask.name}' 的配置信息。源端和目标端已自动设置，您可以查看和修改配置后创建新任务。`"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <!-- 步骤指示器 -->
    <el-steps :active="currentStep" finish-status="success" class="wizard-steps">
      <el-step title="选择源端" description="选择源端存储和文件">
        <template #icon>
          <el-icon><FolderOpened /></el-icon>
        </template>
      </el-step>
      <el-step title="选择目标端" description="选择目标端存储和路径">
        <template #icon>
          <el-icon><FolderAdd /></el-icon>
        </template>
      </el-step>
      <el-step title="任务参数" description="配置同步参数">
        <template #icon>
          <el-icon><Setting /></el-icon>
        </template>
      </el-step>
      <el-step title="确认配置" description="确认并创建任务">
        <template #icon>
          <el-icon><Check /></el-icon>
        </template>
      </el-step>
    </el-steps>

    <!-- 步骤内容 -->
    <div class="wizard-content">
      <!-- 步骤1: 选择源端 -->
      <div v-show="currentStep === 0" class="step-content">
        <div class="step-header">
          <h3>选择源端存储和文件</h3>
          <p class="step-description">请选择要同步的源端存储，并勾选需要同步的目录或文件</p>
        </div>
        
        <SourceSelector 
          ref="sourceSelectorRef"
          v-model="wizardData.source"
          @change="handleSourceChange"
        />
      </div>

      <!-- 步骤2: 选择目标端 -->
      <div v-show="currentStep === 1" class="step-content">
        <div class="step-header">
          <h3>选择目标端存储和路径</h3>
          <p class="step-description">请选择目标端存储，并指定同步的目标路径</p>
        </div>
        
        <TargetSelector 
          ref="targetSelectorRef"
          v-model="wizardData.target"
          :source-storage="wizardData.source"
          @change="handleTargetChange"
        />
      </div>

      <!-- 步骤3: 任务参数 -->
      <div v-show="currentStep === 2" class="step-content">
        <div class="step-header">
          <h3>配置任务参数</h3>
          <p class="step-description">根据源端和目标端类型配置相应的同步参数</p>
        </div>
        
        <TaskParameters 
          v-model="wizardData.parameters"
          :source-storage="wizardData.source"
          :target-storage="wizardData.target"
          @change="handleParametersChange"
        />
      </div>

      <!-- 步骤4: 确认配置 -->
      <div v-show="currentStep === 3" class="step-content">
        <div class="step-header">
          <h3>确认任务配置</h3>
          <p class="step-description">请确认以下配置信息，确认无误后点击创建任务</p>
        </div>
        
        <TaskConfirmation 
          :wizard-data="wizardData"
          @confirm="handleConfirm"
        />
      </div>
    </div>

    <!-- 步骤导航 -->
    <div class="wizard-footer">
      <div class="footer-actions">
        <el-button 
          v-if="currentStep > 0" 
          @click="prevStep"
          :disabled="loading"
        >
          <el-icon><ArrowLeft /></el-icon>
          上一步
        </el-button>
        
        <el-button 
          v-if="currentStep < 3" 
          type="primary" 
          @click="nextStep"
          :disabled="!canProceed || loading"
        >
          下一步
          <el-icon><ArrowRight /></el-icon>
        </el-button>
        
        <el-button 
          v-if="currentStep === 3" 
          type="success" 
          @click="createTask"
          :loading="loading"
          :disabled="!canCreate"
        >
          <el-icon><Check /></el-icon>
          创建任务
        </el-button>
      </div>
      
      <div class="footer-info">
        <el-button @click="resetWizard" :disabled="loading">
          重置向导
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened, FolderAdd, Setting, Check,
  ArrowLeft, ArrowRight
} from '@element-plus/icons-vue'
import SourceSelector from './SourceSelector.vue'
import TargetSelector from './TargetSelector.vue'
import TaskParameters from './TaskParameters.vue'
import TaskConfirmation from './TaskConfirmation.vue'
import axios from 'axios'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  // 新增：要复制的任务数据
  copyFromTask: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'created'])

// 响应式数据
const currentStep = ref(0)
const loading = ref(false)
const sourceSelectorRef = ref(null)
const targetSelectorRef = ref(null)
const extractedSourceConfig = ref(null)
const extractedTargetConfig = ref(null)

// 步骤状态缓存
const stepCache = ref({
  step0: null, // 源端选择器状态
  step1: null, // 目标端选择器状态
  step2: null, // 任务参数状态
  step3: null  // 确认配置状态
})

// 向导数据
const wizardData = ref({
  source: {
    storageId: '',
    storageName: '',
    storageType: '',
    selectedPaths: []
  },
  target: {
    storageId: '',
    storageName: '',
    storageType: '',
    targetPath: ''
  },
  parameters: {
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
  }
})

// 新增：从任务中提取配置的方法
const extractConfigFromTask = (task) => {
  if (!task) return

  try {
    // 提取源端配置
    if (task.source_type === 'storage' && task.source_storage_id) {
      // 处理源端路径 - 检查多个可能的字段
      let selectedPaths = []
      
      // 检查source_path字段
      if (task.source_path) {
        if (typeof task.source_path === 'string') {
          selectedPaths = task.source_path.split(',').map(path => ({ 
            path: path.trim(),
            name: path.trim().split('/').pop() || path.trim()
          }))
        } else if (Array.isArray(task.source_path)) {
          selectedPaths = task.source_path.map(path => ({
            path: typeof path === 'string' ? path : path.path,
            name: typeof path === 'string' ? path.split('/').pop() : path.name || path.path.split('/').pop()
          }))
        }
      }
      
      // 检查source_paths字段（如果存在）
      if (!selectedPaths.length && task.source_paths) {
        if (Array.isArray(task.source_paths)) {
          selectedPaths = task.source_paths.map(path => ({
            path: typeof path === 'string' ? path : path.path,
            name: typeof path === 'string' ? path.split('/').pop() : path.name || path.path.split('/').pop()
          }))
        }
      }
      
      // 检查source_storage_paths字段（如果存在）
      if (!selectedPaths.length && task.source_storage_paths) {
        if (Array.isArray(task.source_storage_paths)) {
          selectedPaths = task.source_storage_paths.map(path => ({
            path: typeof path === 'string' ? path : path.path,
            name: typeof path === 'string' ? path.split('/').pop() : path.name || path.path.split('/').pop()
          }))
        }
      }
      
      // 在复制任务时，不直接设置wizardData，避免触发props变化监听器
      const sourceConfig = {
        storageId: task.source_storage_id,
        storageName: task.source_storage_name || task.source_storage_config?.name || '',
        storageType: task.source_storage_type || task.source_storage_config?.type || '',
        selectedPaths: selectedPaths
      }
      
      // 保存配置，但不立即设置到wizardData
      extractedSourceConfig.value = sourceConfig
      
      // 在复制任务时，也设置wizardData以便子组件能正确接收
      wizardData.value.source = sourceConfig
      
    } else {
      console.warn('任务源端配置不完整，无法复制')
      ElMessage.warning('任务源端配置不完整，请手动配置源端')
    }

    // 提取目标端配置
    if (task.target_storage_id) {
      const targetConfig = {
        storageId: task.target_storage_id,
        storageName: task.target_storage_name || task.target_storage_config?.name || '',
        storageType: task.target_storage_type || task.target_storage_config?.type || '',
        targetPath: task.target_path || ''
      }
      
      // 保存配置，但不立即设置到wizardData
      extractedTargetConfig.value = targetConfig
      
      // 在复制任务时，也设置wizardData以便子组件能正确接收
      wizardData.value.target = targetConfig
      
    } else {
      console.warn('任务目标端配置不完整，无法复制')
      ElMessage.warning('任务目标端配置不完整，请手动配置目标端')
    }

    // 提取任务参数
    wizardData.value.parameters = {
      taskName: `${task.name} - 副本`,
      description: task.description ? `${task.description} (复制自任务: ${task.name})` : `复制自任务: ${task.name}`,
      priority: task.priority || 2,
      syncOptions: {
        delete: task.options?.delete || false,
        compress: task.options?.compress || false,
        checksum: task.options?.checksum !== false, // 默认为true
        bandwidth_limit: task.options?.bandwidth_limit || 0,
        max_connections: task.options?.max_connections || 1
      },
      retryOptions: {
        max_retries: task.options?.retry_options?.max_retries || 3,
        retry_interval: task.options?.retry_options?.retry_interval || 30
      },
      advancedOptions: {
        buffer_size: task.options?.buffer_size || 10,
        timeout: task.options?.timeout || 300,
        exclude_patterns: task.options?.exclude_patterns || '',
        include_patterns: task.options?.include_patterns || ''
      },
      scenarioOptions: task.options?.scenario_options || task.options?.scenarioOptions || task.scenario_options || task.scenarioOptions || {}
    }

    // 延迟执行，确保子组件已经挂载
    nextTick(async () => {
      // 等待子组件加载完成
      await new Promise(resolve => setTimeout(resolve, 300))
      
      // 如果有源端配置，初始化源端选择器
      if (extractedSourceConfig.value?.storageId && sourceSelectorRef.value) {
        try {
          await sourceSelectorRef.value.setInitialState(extractedSourceConfig.value)
        } catch (error) {
          console.error('初始化源端选择器失败:', error)
        }
      } else {
        console.warn('源端选择器未找到或配置不完整', {
          storageId: extractedSourceConfig.value?.storageId,
          sourceSelectorRef: sourceSelectorRef.value
        })
      }
      
      // 等待源端初始化完成
      await new Promise(resolve => setTimeout(resolve, 500))
      
      // 如果有目标端配置，预先初始化目标端选择器（但不显示）
      if (extractedTargetConfig.value?.storageId) {
      }
    })
  } catch (error) {
    console.error('提取任务配置时出错:', error)
    ElMessage.error('提取任务配置时出错，请手动配置任务')
  }
}

// 计算属性
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return wizardData.value.source.storageId && 
             wizardData.value.source.selectedPaths.length > 0
    case 1:
      return wizardData.value.target.storageId && 
             wizardData.value.target.targetPath
    case 2:
      return wizardData.value.parameters.taskName.trim()
    default:
      return true
  }
})

const canCreate = computed(() => {
  return wizardData.value.source.storageId &&
         wizardData.value.source.selectedPaths.length > 0 &&
         wizardData.value.target.storageId &&
         wizardData.value.target.targetPath &&
         wizardData.value.parameters.taskName.trim()
})

// 方法
const nextStep = async () => {
  if (currentStep.value < 3) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const handleSourceChange = (source) => {
  if (props.copyFromTask) {
    wizardData.value.source = {
      ...source,
      selectedPaths: source.selectedPaths.length > 0 ? source.selectedPaths : wizardData.value.source.selectedPaths
    }
  } else {
    wizardData.value.source = source
  }
}

const handleTargetChange = (target) => {
  if (props.copyFromTask) {
    const currentTarget = wizardData.value.target
    if (currentTarget.storageId !== target.storageId || 
        currentTarget.targetPath !== target.targetPath ||
        currentTarget.storageName !== target.storageName ||
        currentTarget.storageType !== target.storageType) {
      wizardData.value.target = {
        ...target,
        targetPath: target.targetPath || wizardData.value.target.targetPath
      }
    }
  } else {
    wizardData.value.target = target
  }
}

const handleParametersChange = (parameters) => {
  wizardData.value.parameters = parameters
}

const handleConfirm = () => {
}

const createTask = async () => {
  if (!canCreate.value) {
    ElMessage.warning('请完善所有必要的配置信息')
    return
  }

  try {
    loading.value = true

    // 构建任务数据
    const taskData = buildTaskData()
    
    // 调用API创建任务
    const response = await axios.post('/api/tasks', taskData)
    
    if (response.data.status === 'success') {
      ElMessage.success('任务创建成功')
      emit('created', response.data.data)
      resetWizard()
      emit('update:visible', false)
    } else {
      ElMessage.error(response.data.message || '创建任务失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '创建任务失败')
  } finally {
    loading.value = false
  }
}

const buildTaskData = () => {
  const { source, target, parameters } = wizardData.value
  // 构建任务数据
  const taskData = {
    name: parameters.taskName,
    description: parameters.description,
    type: 'sync',
    priority: parameters.priority,
    source_type: 'storage',
    source_storage_id: source.storageId,
    source_path: source.selectedPaths.map(p => p.path).join(','),
    target_storage_id: target.storageId,
    target_path: target.targetPath,
    options: {
      ...parameters.syncOptions,
      retry_options: parameters.retryOptions,
      advanced_options: parameters.advancedOptions,
      scenario_options: parameters.scenarioOptions
    }
  }

  return taskData
}

const resetWizard = () => {
  currentStep.value = 0
  wizardData.value = {
    source: {
      storageId: '',
      storageName: '',
      storageType: '',
      selectedPaths: []
    },
    target: {
      storageId: '',
      storageName: '',
      storageType: '',
      targetPath: ''
    },
    parameters: {
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
    }
  }
  
  // 清理步骤缓存
  stepCache.value = {
    step0: null,
    step1: null,
    step2: null,
    step3: null
  }
}

// 监听对话框显示状态
watch(() => props.visible, (visible) => {
  if (visible) {
    // 只有在不是复制任务时才重置
    if (!props.copyFromTask) {
      resetWizard()
      // 清理复制的任务配置
      extractedSourceConfig.value = null
      extractedTargetConfig.value = null
      
      // 延迟清理子组件状态
      nextTick(() => {
        if (sourceSelectorRef.value) {
          sourceSelectorRef.value.setInitialState(null)
        }
        if (targetSelectorRef.value) {
          targetSelectorRef.value.setInitialState(null)
        }
      })
    } else {
      // 复制任务时只重置步骤，不重置数据
      currentStep.value = 0
    }
    
    // 如果有要复制的任务，则提取配置
    if (props.copyFromTask) {
      // 延迟执行，确保组件完全挂载
      nextTick(() => {
        extractConfigFromTask(props.copyFromTask)
      })
    }
  } else {
    // 对话框关闭时，总是清理复制的任务配置
    extractedSourceConfig.value = null
    extractedTargetConfig.value = null
  }
})
</script>

<style scoped>
.task-wizard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.copy-notice {
  margin-bottom: 20px;
}

.wizard-steps {
  margin-bottom: 40px;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.wizard-content {
  min-height: 500px;
  margin-bottom: 30px;
}

.step-content {
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.step-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid var(--el-border-color-light);
}

.step-header h3 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 20px;
  font-weight: 600;
}

.step-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.wizard-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  background: var(--el-bg-color);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.footer-actions {
  display: flex;
  gap: 12px;
}

.footer-info {
  display: flex;
  gap: 12px;
}

:deep(.el-step__title) {
  font-size: 16px;
  font-weight: 500;
}

:deep(.el-step__description) {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

:deep(.el-step__icon) {
  font-size: 18px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .task-wizard {
    padding: 10px;
  }
  
  .wizard-footer {
    flex-direction: column;
    gap: 16px;
  }
  
  .footer-actions {
    width: 100%;
    justify-content: center;
  }
  
  .footer-info {
    width: 100%;
    justify-content: center;
  }
}
</style> 