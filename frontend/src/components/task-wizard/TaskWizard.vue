<template>
  <div class="task-wizard">
    <!-- 科技感背景装饰 -->
    <div class="wizard-bg-decoration">
      <div class="grid-pattern"></div>
      <div class="floating-particles">
        <div class="particle" v-for="i in 20" :key="i"></div>
      </div>
    </div>

    <!-- 复制任务提示 -->
    <div v-if="copyFromTask" class="copy-notice">
      <div class="cyber-alert">
        <div class="alert-icon">
          <el-icon>
            <CopyDocument />
          </el-icon>
        </div>
        <div class="alert-content">
          <h4>{{ $t('taskWizard.copyTaskConfig') }}</h4>
          <p>{{ $t('taskWizard.copyingTaskConfig', { taskName: copyFromTask.name }) }}</p>
        </div>
        <div class="alert-decoration"></div>
      </div>
    </div>

    <!-- 科技感步骤指示器 -->
    <div class="cyber-steps">
      <div class="steps-container">
        <div v-for="(step, index) in steps" :key="index" class="step-item" :class="{
          'active': currentStep === index,
          'completed': currentStep > index,
          'upcoming': currentStep < index
        }" @click="canGoToStep(index) && goToStep(index)">
          <div class="step-circle">
            <div class="step-inner">
              <el-icon v-if="currentStep > index" class="step-check">
                <Check />
              </el-icon>
              <el-icon v-else :class="step.iconClass">
                <component :is="step.icon" />
              </el-icon>
            </div>
            <div class="step-glow"></div>
          </div>
          <div class="step-info">
            <span class="step-title">{{ step.title }}</span>
            <span class="step-desc">{{ step.description }}</span>
          </div>
          <div v-if="index < steps.length - 1" class="step-connector">
            <div class="connector-line" :class="{ 'active': currentStep > index }"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 步骤内容 -->
    <div class="wizard-content">
      <!-- 步骤1: 选择源端 -->
      <Transition name="step-slide" mode="out-in">
        <div v-show="currentStep === 0" class="step-content cyber-panel">
          <div class="panel-header">
            <div class="header-decoration">
              <div class="header-line"></div>
              <div class="header-dot"></div>
            </div>
            <div class="step-header">
              <h3>
                <el-icon class="header-icon">
                  <FolderOpened />
                </el-icon>
                {{ $t('taskWizard.selectSourceStorageAndFiles') }}
              </h3>
              <p class="step-description">{{ $t('taskWizard.selectSourceStorageAndFilesDesc') }}</p>
            </div>
            <div class="header-decoration reverse">
              <div class="header-dot"></div>
              <div class="header-line"></div>
            </div>
          </div>

          <div class="panel-content">
            <SourceSelector ref="sourceSelectorRef" v-model="wizardData.source" @change="handleSourceChange" />
          </div>
        </div>
      </Transition>

      <!-- 步骤2: 选择目标端 -->
      <Transition name="step-slide" mode="out-in">
        <div v-show="currentStep === 1" class="step-content cyber-panel">
          <div class="panel-header">
            <div class="header-decoration">
              <div class="header-line"></div>
              <div class="header-dot"></div>
            </div>
            <div class="step-header">
              <h3>
                <el-icon class="header-icon">
                  <FolderAdd />
                </el-icon>
                {{ $t('taskWizard.selectTargetStorageAndPath') }}
              </h3>
              <p class="step-description">{{ $t('taskWizard.selectTargetStorageAndPathDesc') }}</p>
            </div>
            <div class="header-decoration reverse">
              <div class="header-dot"></div>
              <div class="header-line"></div>
            </div>
          </div>

          <div class="panel-content">
            <TargetSelector ref="targetSelectorRef" v-model="wizardData.target" :source-storage="wizardData.source"
              @change="handleTargetChange" />
          </div>
        </div>
      </Transition>

      <!-- 步骤3: 任务参数 -->
      <Transition name="step-slide" mode="out-in">
        <div v-show="currentStep === 2" class="step-content cyber-panel">
          <div class="panel-header">
            <div class="header-decoration">
              <div class="header-line"></div>
              <div class="header-dot"></div>
            </div>
            <div class="step-header">
              <h3>
                <el-icon class="header-icon">
                  <Setting />
                </el-icon>
                {{ $t('taskWizard.configureTaskParameters') }}
              </h3>
              <p class="step-description">{{ $t('taskWizard.configureTaskParametersDesc') }}</p>
            </div>
            <div class="header-decoration reverse">
              <div class="header-dot"></div>
              <div class="header-line"></div>
            </div>
          </div>

          <div class="panel-content">
            <TaskParameters v-model="wizardData.parameters" :source-storage="wizardData.source"
              :target-storage="wizardData.target" @change="handleParametersChange" />
          </div>
        </div>
      </Transition>

      <!-- 步骤4: 确认配置 -->
      <Transition name="step-slide" mode="out-in">
        <div v-show="currentStep === 3" class="step-content cyber-panel">
          <div class="panel-header">
            <div class="header-decoration">
              <div class="header-line"></div>
              <div class="header-dot"></div>
            </div>
            <div class="step-header">
              <h3>
                <el-icon class="header-icon">
                  <Check />
                </el-icon>
                {{ $t('taskWizard.confirmTaskConfiguration') }}
              </h3>
              <p class="step-description">{{ $t('taskWizard.confirmTaskConfigurationDesc') }}</p>
            </div>
            <div class="header-decoration reverse">
              <div class="header-dot"></div>
              <div class="header-line"></div>
            </div>
          </div>

          <div class="panel-content">
            <TaskConfirmation :wizard-data="wizardData" @confirm="handleConfirm" />
          </div>
        </div>
      </Transition>
    </div>

    <!-- 科技感导航栏 -->
    <div class="cyber-footer">
      <div class="footer-bg"></div>

      <div class="footer-content">
        <!-- 左侧按钮组 -->
        <div class="footer-actions">
          <button v-if="currentStep > 0" class="cyber-btn secondary" @click="prevStep" :disabled="loading">
            <el-icon>
              <ArrowLeft />
            </el-icon>
            <span>{{ $t('taskWizard.previousStep') }}</span>
          </button>

          <button class="cyber-btn reset" @click="resetWizard" :disabled="loading">
            <el-icon>
              <RefreshLeft />
            </el-icon>
            <span>{{ $t('taskWizard.reset') }}</span>
          </button>
        </div>

        <!-- 中间进度指示 -->
        <div class="progress-indicator">
          <div class="progress-text">{{ $t('taskWizard.stepProgress', { current: currentStep + 1, total: steps.length })
          }}</div>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: `${((currentStep + 1) / steps.length) * 100}%` }"></div>
          </div>
          <div class="progress-dots">
            <div v-for="i in steps.length" :key="i" class="progress-dot" :class="{ active: i <= currentStep + 1 }">
            </div>
          </div>
        </div>

        <!-- 右侧主要按钮 -->
        <div class="footer-primary">
          <button v-if="currentStep < 3" class="cyber-btn primary" @click="nextStep" :disabled="!canProceed || loading">
            <span>{{ $t('taskWizard.nextStep') }}</span>
            <el-icon>
              <ArrowRight />
            </el-icon>
          </button>

          <button v-if="currentStep === 3" class="cyber-btn success" @click="createTask"
            :disabled="!canCreate || loading">
            <el-icon v-if="loading">
              <Loading />
            </el-icon>
            <el-icon v-else>
              <Check />
            </el-icon>
            <span>{{ copyFromTask ? $t('taskWizard.createCopy') : $t('taskWizard.createTask') }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, markRaw } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  FolderOpened, FolderAdd, Setting, Check,
  ArrowLeft, ArrowRight, RefreshLeft, Loading,
  CopyDocument, Close
} from '@element-plus/icons-vue'
import SourceSelector from './SourceSelector.vue'
import TargetSelector from './TargetSelector.vue'
import TaskParameters from './TaskParameters.vue'
import TaskConfirmation from './TaskConfirmation.vue'
import axios from '@/utils/axios.mjs'

const { t } = useI18n()

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

// 步骤配置
const steps = ref([
  {
    title: t('taskWizard.steps.selectSource'),
    description: t('taskWizard.steps.selectSourceDesc'),
    icon: markRaw(FolderOpened),
    iconClass: 'step-icon-source'
  },
  {
    title: t('taskWizard.steps.selectTarget'),
    description: t('taskWizard.steps.selectTargetDesc'),
    icon: markRaw(FolderAdd),
    iconClass: 'step-icon-target'
  },
  {
    title: t('taskWizard.steps.configureParameters'),
    description: t('taskWizard.steps.configureParametersDesc'),
    icon: markRaw(Setting),
    iconClass: 'step-icon-settings'
  },
  {
    title: t('taskWizard.steps.confirmConfig'),
    description: t('taskWizard.steps.confirmConfigDesc'),
    icon: markRaw(Check),
    iconClass: 'step-icon-confirm'
  }
])

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

// 初始化子组件的方法
const initializeChildComponents = async () => {
  // 延迟执行，确保子组件已经挂载
  await nextTick()

  // 多次尝试初始化，直到子组件可用
  let retryCount = 0
  const maxRetries = 10

  while (retryCount < maxRetries) {
    // 等待子组件加载完成
    await new Promise(resolve => setTimeout(resolve, 200))

    // 如果有源端配置，初始化源端选择器
    if (extractedSourceConfig.value?.storageId && sourceSelectorRef.value) {
      try {
        await sourceSelectorRef.value.setInitialState(extractedSourceConfig.value)
        break
      } catch (error) {
        if (import.meta.env.DEV) {
          console.error(t('taskWizard.messages.sourceInitFailed', { current: retryCount + 1, max: maxRetries }), error)
        }
      }
    } else {
      if (import.meta.env.DEV) {
        console.debug(t('taskWizard.messages.waitingForComponentMount', { current: retryCount + 1, max: maxRetries }), {
          storageId: extractedSourceConfig.value?.storageId,
          sourceSelectorRef: !!sourceSelectorRef.value
        })
      }
    }

    retryCount++
  }

  if (retryCount >= maxRetries) {
    console.warn('源端选择器初始化超时，可能需要手动配置')
    ElMessage.warning(t('taskWizard.warnings.sourceInitTimeout'))
  }
}

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
      ElMessage.warning(t('taskWizard.warnings.sourceConfigIncompleteManual'))
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
      ElMessage.warning(t('taskWizard.warnings.targetConfigIncompleteManual'))
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

    // 如果对话框已经可见，立即尝试初始化子组件
    if (props.visible) {
      initializeChildComponents()
    }
  } catch (error) {
    console.error('提取任务配置时出错:', error)
    ElMessage.error(t('taskWizard.errors.extractConfigFailed'))
  }
}

// 新增方法：步骤导航控制
const canGoToStep = (stepIndex) => {
  // 可以回到之前的步骤，或者当前步骤可以前进时可以到下一步
  return stepIndex <= currentStep.value || (stepIndex === currentStep.value + 1 && canProceed.value)
}

const goToStep = (stepIndex) => {
  if (canGoToStep(stepIndex)) {
    currentStep.value = stepIndex
  }
}

// 计算属性
const canProceed = computed(() => {
  switch (currentStep.value) {
    case 0:
      return wizardData.value.source.storageId &&
        wizardData.value.source.selectedPaths.length > 0
    case 1:
      // 目标端只需要选择了存储，路径可以为空（虚拟托管样式）
      return wizardData.value.target.storageId
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
    ElMessage.warning(t('taskWizard.messages.completeAllRequiredConfig'))
    return
  }

  try {
    loading.value = true

    // 构建任务数据
    const taskData = buildTaskData()

    // 调用API创建任务
    const response = await axios.post('/tasks', taskData)

    if (response.data.status === 'success') {
      ElMessage.success(t('taskWizard.messages.taskCreatedSuccess'))
      emit('created', response.data.data)
      resetWizard()
      emit('update:visible', false)
    } else {
      ElMessage.error(response.data.message || t('taskWizard.messages.createTaskFailed'))
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || t('taskWizard.messages.createTaskFailed'))
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
      // 复制任务时重置步骤和数据，确保状态清洁
      resetWizard()
      currentStep.value = 0
    }

    // 如果有要复制的任务，则提取配置
    if (props.copyFromTask) {
      // 延迟执行，确保组件完全挂载
      nextTick(() => {
        extractConfigFromTask(props.copyFromTask)
        // 初始化子组件
        initializeChildComponents()
      })
    }
  } else {
    // 对话框关闭时，总是清理复制的任务配置
    extractedSourceConfig.value = null
    extractedTargetConfig.value = null
  }
})

// 新增：监听copyFromTask的变化
watch(() => props.copyFromTask, (newTask, oldTask) => {
  if (newTask && newTask !== oldTask) {
    // 当copyFromTask发生变化时，无论对话框是否可见都处理配置
    nextTick(async () => {
      // 先提取配置
      extractConfigFromTask(newTask)
      // 如果对话框可见，再初始化子组件
      if (props.visible) {
        await new Promise(resolve => setTimeout(resolve, 100))
        initializeChildComponents()
      }
    })
  }
}, {
  immediate: false, // 不立即执行，避免重复调用
  deep: true
})
</script>

<style scoped>
/* 科技感主容器 */
.task-wizard {
  position: relative;
  padding: 20px;
  max-width: 1000px;
  margin: 0 auto;
  background: var(--bg-color);
  overflow: hidden;
}

/* 背景装饰 */
.wizard-bg-decoration {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  pointer-events: none;
  z-index: 0;
}

.grid-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    linear-gradient(rgba(64, 158, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  animation: gridMove 20s linear infinite;
}

.floating-particles {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.particle {
  position: absolute;
  width: 2px;
  height: 2px;
  background: rgba(64, 158, 255, 0.4);
  border-radius: 50%;
  animation: float 8s infinite linear;
}

.particle:nth-child(odd) {
  animation-delay: -2s;
  background: rgba(103, 194, 58, 0.3);
}

.particle:nth-child(3n) {
  animation-delay: -4s;
  background: rgba(245, 108, 108, 0.3);
}

@keyframes gridMove {
  0% {
    transform: translate(0, 0);
  }

  100% {
    transform: translate(50px, 50px);
  }
}

@keyframes float {
  0% {
    transform: translateY(100vh) rotate(0deg);
    opacity: 0;
  }

  10% {
    opacity: 1;
  }

  90% {
    opacity: 1;
  }

  100% {
    transform: translateY(-100px) rotate(360deg);
    opacity: 0;
  }
}

/* 生成随机粒子位置 */
.particle:nth-child(1) {
  left: 5%;
  animation-duration: 6s;
}

.particle:nth-child(2) {
  left: 15%;
  animation-duration: 8s;
}

.particle:nth-child(3) {
  left: 25%;
  animation-duration: 7s;
}

.particle:nth-child(4) {
  left: 35%;
  animation-duration: 9s;
}

.particle:nth-child(5) {
  left: 45%;
  animation-duration: 6s;
}

.particle:nth-child(6) {
  left: 55%;
  animation-duration: 8s;
}

.particle:nth-child(7) {
  left: 65%;
  animation-duration: 7s;
}

.particle:nth-child(8) {
  left: 75%;
  animation-duration: 9s;
}

.particle:nth-child(9) {
  left: 85%;
  animation-duration: 6s;
}

.particle:nth-child(10) {
  left: 95%;
  animation-duration: 8s;
}

/* 复制任务提示 */
.copy-notice {
  position: relative;
  margin-bottom: 30px;
  z-index: 1;
}

.cyber-alert {
  position: relative;
  display: flex;
  align-items: center;
  padding: 20px;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.1) 0%, rgba(64, 158, 255, 0.05) 100%);
  border: 1px solid rgba(64, 158, 255, 0.3);
  border-radius: 12px;
  backdrop-filter: blur(10px);
  overflow: hidden;
}

.cyber-alert::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(64, 158, 255, 0.1), transparent);
  animation: scanLine 3s infinite;
}

@keyframes scanLine {
  0% {
    left: -100%;
  }

  100% {
    left: 100%;
  }
}

.alert-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(64, 158, 255, 0.2);
  border-radius: 50%;
  margin-right: 16px;
  font-size: 18px;
  color: #409eff;
}

.alert-content h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.alert-content p {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
}

.alert-decoration {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(64, 158, 255, 0.3);
  border-radius: 4px;
  animation: pulse 2s infinite;
}

/* 科技感步骤指示器 */
.cyber-steps {
  position: relative;
  margin-bottom: 40px;
  z-index: 1;
}

.steps-container {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  background: var(--cyber-glass-bg);
  border: 1px solid var(--cyber-glass-border);
  border-radius: 16px;
  backdrop-filter: blur(10px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 var(--cyber-glass-border);
}

.step-item {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: all 0.3s ease;
  flex: 1;
}

.step-item.active .step-circle .step-inner {
  background: linear-gradient(135deg, var(--cyber-primary) 0%, var(--cyber-success) 100%);
  border-color: var(--cyber-primary);
  box-shadow: 0 0 20px var(--cyber-glow-primary);
  transform: scale(1.1);
}

.step-item.completed .step-circle .step-inner {
  background: linear-gradient(135deg, var(--cyber-success) 0%, var(--cyber-primary) 100%);
  border-color: var(--cyber-success);
  box-shadow: 0 0 15px var(--cyber-glow-success);
}

.step-item.upcoming .step-circle .step-inner {
  background: var(--bg-secondary);
  border-color: var(--border-color);
}

.step-circle {
  position: relative;
  margin-bottom: 12px;
}

.step-inner {
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid var(--border-color);
  border-radius: 50%;
  background: var(--bg-color);
  font-size: 24px;
  color: var(--text-color);
  transition: all 0.3s ease;
  z-index: 2;
  position: relative;
}

.step-glow {
  position: absolute;
  top: -4px;
  left: -4px;
  right: -4px;
  bottom: -4px;
  border-radius: 50%;
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.3), rgba(103, 194, 58, 0.3));
  opacity: 0;
  filter: blur(8px);
  transition: opacity 0.3s ease;
  z-index: 1;
}

.step-item.active .step-glow {
  opacity: 1;
  animation: glow 2s ease-in-out infinite alternate;
}

@keyframes glow {
  from {
    transform: scale(1);
  }

  to {
    transform: scale(1.1);
  }
}

.step-info {
  text-align: center;
  max-width: 120px;
}

.step-title {
  display: block;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 4px;
  transition: color 0.3s ease;
}

.step-desc {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  line-height: 1.3;
}

.step-item.active .step-title {
  color: #409eff;
}

.step-item.completed .step-title {
  color: #67c23a;
}

.step-connector {
  position: absolute;
  top: 30px;
  left: calc(50% + 40px);
  right: calc(-50% + 40px);
  height: 2px;
  display: flex;
  align-items: center;
  z-index: 1;
}

.connector-line {
  width: 100%;
  height: 2px;
  background: var(--border-color);
  position: relative;
  overflow: hidden;
  transition: all 0.3s ease;
}

.connector-line.active {
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.3);
}

.connector-line.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.4), transparent);
  animation: flow 2s infinite;
}

@keyframes flow {
  0% {
    left: -100%;
  }

  100% {
    left: 100%;
  }
}

/* 步骤内容面板 */
.wizard-content {
  position: relative;
  min-height: 600px;
  margin-bottom: 30px;
  z-index: 1;
}

.cyber-panel {
  background: var(--cyber-panel-bg);
  border: 1px solid var(--cyber-panel-border);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 var(--cyber-panel-border);
  overflow: hidden;
  position: relative;
}

.cyber-panel::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(64, 158, 255, 0.5), transparent);
}

.panel-header {
  display: flex;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
  background: linear-gradient(135deg, rgba(64, 158, 255, 0.05) 0%, rgba(103, 194, 58, 0.05) 100%);
}

.header-decoration {
  display: flex;
  align-items: center;
  margin-right: 20px;
}

.header-decoration.reverse {
  margin-right: 0;
  margin-left: 20px;
  flex-direction: row-reverse;
}

.header-line {
  width: 30px;
  height: 2px;
  background: linear-gradient(90deg, #409eff, #67c23a);
  border-radius: 1px;
}

.header-dot {
  width: 8px;
  height: 8px;
  background: #409eff;
  border-radius: 50%;
  margin: 0 8px;
  animation: pulse 2s infinite;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.6;
    transform: scale(1.2);
  }
}

.step-header {
  flex: 1;
  text-align: center;
}

.step-header h3 {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  background: linear-gradient(135deg, var(--text-color) 0%, #409eff 100%);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.header-icon {
  font-size: 28px;
  color: #409eff;
}

.step-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 16px;
  line-height: 1.5;
}

.panel-content {
  padding: 20px;
}

/* 科技感底部导航 */
.cyber-footer {
  position: relative;
  z-index: 1;
}

.footer-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid var(--border-color);
  border-radius: 16px;
  backdrop-filter: blur(20px);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.footer-content {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 30px;
  z-index: 2;
}

.footer-actions {
  display: flex;
  gap: 16px;
}

.footer-primary {
  display: flex;
  gap: 16px;
}

/* 科技感按钮 */
.cyber-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
  border: 1px solid var(--border-color);
  color: var(--text-color);
  backdrop-filter: blur(10px);
}

.cyber-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  transition: left 0.5s;
}

.cyber-btn:hover::before {
  left: 100%;
}

.cyber-btn.primary {
  background: linear-gradient(135deg, #409eff 0%, #67c23a 100%);
  border-color: #409eff;
  color: white;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.3);
}

.cyber-btn.primary:hover {
  box-shadow: 0 6px 20px rgba(64, 158, 255, 0.4);
  transform: translateY(-2px);
}

.cyber-btn.success {
  background: linear-gradient(135deg, #67c23a 0%, #409eff 100%);
  border-color: #67c23a;
  color: white;
  box-shadow: 0 4px 16px rgba(103, 194, 58, 0.3);
}

.cyber-btn.success:hover {
  box-shadow: 0 6px 20px rgba(103, 194, 58, 0.4);
  transform: translateY(-2px);
}

.cyber-btn.secondary {
  background: linear-gradient(135deg, rgba(96, 98, 102, 0.1) 0%, rgba(96, 98, 102, 0.05) 100%);
  border-color: var(--border-color);
  color: var(--text-secondary);
}

.cyber-btn.secondary:hover {
  border-color: #409eff;
  color: #409eff;
  box-shadow: 0 4px 16px rgba(64, 158, 255, 0.2);
}

.cyber-btn.reset {
  background: linear-gradient(135deg, rgba(245, 108, 108, 0.1) 0%, rgba(245, 108, 108, 0.05) 100%);
  border-color: rgba(245, 108, 108, 0.3);
  color: #f56c6c;
}

.cyber-btn.reset:hover {
  border-color: #f56c6c;
  box-shadow: 0 4px 16px rgba(245, 108, 108, 0.2);
}

.cyber-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* 进度指示器 */
.progress-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-secondary);
}

.progress-bar {
  width: 200px;
  height: 4px;
  background: var(--border-color);
  border-radius: 2px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #409eff 0%, #67c23a 100%);
  border-radius: 2px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-fill::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
  animation: progress-flow 2s infinite;
}

@keyframes progress-flow {
  0% {
    left: -100%;
  }

  100% {
    left: 100%;
  }
}

.progress-dots {
  display: flex;
  gap: 6px;
}

.progress-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--border-color);
  transition: all 0.3s ease;
}

.progress-dot.active {
  background: #409eff;
  box-shadow: 0 0 8px rgba(64, 158, 255, 0.5);
}

/* 步骤切换动画 */
.step-slide-enter-active,
.step-slide-leave-active {
  transition: all 0.3s ease;
}

.step-slide-enter-from {
  opacity: 0;
  transform: translateX(30px);
}

.step-slide-leave-to {
  opacity: 0;
  transform: translateX(-30px);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .task-wizard {
    padding: 20px;
  }

  .steps-container {
    padding: 20px;
  }

  .step-inner {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }

  .step-info {
    max-width: 100px;
  }
}

@media (max-width: 768px) {
  .task-wizard {
    padding: 15px;
  }

  .steps-container {
    flex-direction: column;
    gap: 20px;
    padding: 24px 20px;
  }

  .step-item {
    flex-direction: row;
    justify-content: flex-start;
    width: 100%;
  }

  .step-circle {
    margin-bottom: 0;
    margin-right: 16px;
  }

  .step-connector {
    display: none;
  }

  .footer-content {
    flex-direction: column;
    gap: 20px;
  }

  .footer-actions,
  .footer-primary {
    width: 100%;
    justify-content: center;
  }

  .cyber-btn {
    flex: 1;
    justify-content: center;
  }

  .progress-indicator {
    order: -1;
  }
}

/* 深色主题优化 */
[data-theme="dark"] .cyber-panel {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

[data-theme="dark"] .cyber-footer .footer-bg {
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.03) 0%, rgba(255, 255, 255, 0.01) 100%);
  box-shadow:
    0 8px 32px rgba(0, 0, 0, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}

[data-theme="dark"] .grid-pattern {
  background:
    linear-gradient(rgba(64, 158, 255, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(64, 158, 255, 0.02) 1px, transparent 1px);
}
</style>