<template>
  <div class="task-wizard">
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
      <div v-if="currentStep === 0" class="step-content">
        <div class="step-header">
          <h3>选择源端存储和文件</h3>
          <p class="step-description">请选择要同步的源端存储，并勾选需要同步的目录或文件</p>
        </div>
        
        <SourceSelector 
          v-model="wizardData.source"
          @change="handleSourceChange"
        />
      </div>

      <!-- 步骤2: 选择目标端 -->
      <div v-if="currentStep === 1" class="step-content">
        <div class="step-header">
          <h3>选择目标端存储和路径</h3>
          <p class="step-description">请选择目标端存储，并指定同步的目标路径</p>
        </div>
        
        <TargetSelector 
          v-model="wizardData.target"
          :source-storage="wizardData.source"
          @change="handleTargetChange"
        />
      </div>

      <!-- 步骤3: 任务参数 -->
      <div v-if="currentStep === 2" class="step-content">
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
      <div v-if="currentStep === 3" class="step-content">
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
import { ref, computed, watch } from 'vue'
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
  }
})

const emit = defineEmits(['update:visible', 'created'])

// 响应式数据
const currentStep = ref(0)
const loading = ref(false)

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
const nextStep = () => {
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
  wizardData.value.source = source
}

const handleTargetChange = (target) => {
  wizardData.value.target = target
}

const handleParametersChange = (parameters) => {
  wizardData.value.parameters = parameters
}

const handleConfirm = () => {
  // 确认配置，可以在这里添加额外的验证
  console.log('配置已确认:', wizardData.value)
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
      retry_options: parameters.retryOptions
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
}

// 监听对话框显示状态
watch(() => props.visible, (visible) => {
  if (visible) {
    resetWizard()
  }
})
</script>

<style scoped>
.task-wizard {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
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