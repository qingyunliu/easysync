<template>
  <div class="tasks-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>{{ $t('tasks.title') }}</h1>
        <p class="page-description">{{ $t('tasks.description') }}</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="showCreateDialog">
          <el-icon>
            <Plus />
          </el-icon>
          {{ $t('tasks.createTask') }}
        </el-button>
      </div>
    </div>

    <!-- 统计面板 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content stat-flex">
            <div class="stat-icon total">
              <el-icon>
                <Document />
              </el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.total || 0 }}</div>
              <div class="stat-label">{{ $t('tasks.stats.totalTasks') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card running">
          <div class="stat-content stat-flex">
            <div class="stat-icon running">
              <el-icon>
                <Loading />
              </el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.running || 0 }}</div>
              <div class="stat-label">{{ $t('tasks.stats.running') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card pending">
          <div class="stat-content stat-flex">
            <div class="stat-icon pending">
              <el-icon>
                <Clock />
              </el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.pending || 0 }}</div>
              <div class="stat-label">{{ $t('tasks.stats.pending') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card completed">
          <div class="stat-content stat-flex">
            <div class="stat-icon completed">
              <el-icon>
                <CircleCheck />
              </el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.completed || 0 }}</div>
              <div class="stat-label">{{ $t('tasks.stats.completed') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card failed">
          <div class="stat-content stat-flex">
            <div class="stat-icon failed">
              <el-icon>
                <CircleClose />
              </el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.failed || 0 }}</div>
              <div class="stat-label">{{ $t('tasks.stats.failed') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card online-node">
          <div class="stat-content stat-flex">
            <div class="stat-icon online">
              <el-icon>
                <Connection />
              </el-icon>
            </div>
            <div>
              <div class="stat-number">{{ OnlineNodeStats || 0 }}</div>
              <div class="stat-label">{{ $t('tasks.stats.onlineNodes') }}</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input v-model="searchQuery" :placeholder="$t('tasks.searchPlaceholder')" style="width: 300px" clearable
          @input="handleSearch">
          <template #prefix>
            <el-icon>
              <Search />
            </el-icon>
          </template>
        </el-input>

        <el-select v-model="statusFilter" :placeholder="$t('tasks.statusFilter')"
          style="width: 150px; margin-left: 10px" clearable @change="handleFilter">
          <el-option :label="$t('tasks.all')" value="" />
          <el-option :label="$t('tasks.statuses.pending')" value="pending" />
          <el-option :label="$t('tasks.statuses.assigned')" value="assigned" />
          <el-option :label="$t('tasks.statuses.running')" value="running" />
          <el-option :label="$t('tasks.statuses.completed')" value="completed" />
          <el-option :label="$t('tasks.statuses.failed')" value="failed" />
          <el-option :label="$t('tasks.statuses.cancelled')" value="cancelled" />
        </el-select>

        <el-select v-model="typeFilter" :placeholder="$t('tasks.typeFilter')" style="width: 150px; margin-left: 10px"
          clearable @change="handleFilter">
          <el-option :label="$t('tasks.all')" value="" />
          <el-option :label="$t('tasks.types.sync')" value="sync" />
          <el-option :label="$t('tasks.types.copy')" value="copy" />
          <el-option :label="$t('tasks.types.mountCheck')" value="mount-check" />
        </el-select>
      </div>

      <div class="toolbar-right">
        <el-button-group>
          <el-button :type="autoRefresh ? 'primary' : 'default'" @click="toggleAutoRefresh"
            :icon="autoRefresh ? VideoPause : Refresh">
            {{ autoRefresh ? $t('tasks.pauseRefresh') : $t('tasks.enableRefresh') }}
          </el-button>
          <el-button @click="fetchTasks" :icon="Refresh">
            {{ $t('tasks.refresh') }}
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedTasks.length > 0" class="batch-toolbar">
      <div class="batch-info">
        {{ $t('tasks.selectedTasks', { count: selectedTasks.length }) }}
      </div>
      <div class="batch-actions">
        <el-button size="small" @click="batchCancel">{{ $t('tasks.batchCancel') }}</el-button>
        <el-button size="small" @click="batchRetry">{{ $t('tasks.batchRetry') }}</el-button>
        <el-button size="small" type="danger" @click="batchDelete">{{ $t('tasks.batchDelete') }}</el-button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="table-container">
      <el-table :data="filteredTasks" v-loading="loading" @selection-change="handleSelectionChange"
        :default-sort="{ prop: 'created_at', order: 'descending' }" style="width: 100%">
        <el-table-column type="selection" width="55" />

        <el-table-column prop="name" :label="$t('tasks.taskName')" min-width="320" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="task-name">
              <el-link type="primary" @click="handleViewDetail(row)">
                {{ row.name }}
              </el-link>
              <div class="task-description">{{ row.description || $t('tasks.noDescription') }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="description" :label="$t('tasks.taskDescription')" min-width="380" />

        <el-table-column prop="type" :label="$t('tasks.type')" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.type)" size="small">
              {{ getTaskTypeText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" :label="$t('tasks.status')" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              <el-icon style="vertical-align: middle; margin-right: 4px;">
                <component :is="getStatusIcon(row.status)" />
              </el-icon>
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="progress" :label="$t('tasks.progress')" width="180">
          <template #default="{ row }">
            <el-tooltip :content="getProgressTooltip(row)" placement="top" :disabled="!getProgressTooltip(row)">
              <div class="progress-container">
                <el-progress :percentage="row.progress || 0" :status="getProgressStatus(row.status)" :stroke-width="6"
                  :show-text="false" />
                <span class="progress-text">{{ row.progress || 0 }}%</span>
              </div>
            </el-tooltip>
          </template>
        </el-table-column>

        <el-table-column prop="node_id" :label="$t('tasks.executionNode')" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.node_id" type="info" size="small">
              {{ getNodeName(row.node_id) }}
            </el-tag>
            <span v-else class="text-muted">{{ $t('tasks.unassigned') }}</span>
          </template>
        </el-table-column>

        <el-table-column prop="priority" :label="$t('tasks.priority')" width="80">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" :label="$t('tasks.createTime')" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column :label="$t('tasks.actions')" width="300" fixed="right">
          <template #default="{ row }">
            <el-button-group size="small">
              <!-- 启动/停止按钮 -->
              <el-button v-if="['pending', 'failed'].includes(row.status)" type="success" @click="handleStartTask(row)"
                :icon="VideoPlay" :loading="loadingTasks.has(row.id)">
                {{ $t('tasks.actions.start') }}
              </el-button>

              <!-- 暂停/恢复按钮 -->
              <el-button v-if="row.status === 'running'" type="warning" @click="handlePauseTask(row)" :icon="VideoPause"
                :loading="loadingTasks.has(row.id)">
                {{ $t('tasks.actions.pause') }}
              </el-button>

              <el-button v-if="row.status === 'paused'" type="success" @click="handleResumeTask(row)" :icon="VideoPlay"
                :loading="loadingTasks.has(row.id)">
                {{ $t('tasks.actions.resume') }}
              </el-button>

              <!-- 取消按钮 -->
              <el-button v-if="['running', 'assigned', 'paused'].includes(row.status)" type="danger"
                @click="handleCancelTask(row)" :icon="Close" :loading="loadingTasks.has(row.id)">
                {{ $t('tasks.actions.cancel') }}
              </el-button>

              <!-- 重试按钮 -->
              <el-button v-if="row.status === 'failed'" type="warning" @click="handleRetryTask(row)"
                :icon="RefreshRight" :loading="loadingTasks.has(row.id)">
                {{ $t('tasks.actions.retry') }}
              </el-button>
            </el-button-group>

            <!-- 更多操作下拉菜单 -->
            <el-dropdown @command="(command) => handleDropdownCommand(command, row)" style="margin-left: 8px;">
              <el-button type="primary" :icon="More" size="small">
                {{ $t('tasks.actions.more') }}
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logs">
                    <el-icon>
                      <Document />
                    </el-icon>{{ $t('tasks.actions.viewLogs') }}
                  </el-dropdown-item>
                  <el-dropdown-item command="detail">
                    <el-icon>
                      <InfoFilled />
                    </el-icon>{{ $t('tasks.actions.detail') }}
                  </el-dropdown-item>
                  <el-dropdown-item command="duplicate">
                    <el-icon>
                      <CopyDocument />
                    </el-icon>{{ $t('tasks.actions.duplicate') }}
                  </el-dropdown-item>
                  <el-dropdown-item command="delete" :disabled="['running', 'assigned'].includes(row.status)"
                    style="color: #f56c6c;">
                    <el-icon>
                      <Delete />
                    </el-icon>{{ $t('tasks.actions.delete') }}
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :page-sizes="[10, 20, 50, 100]"
          :total="totalTasks" layout="total, sizes, prev, pager, next, jumper" @size-change="handleSizeChange"
          @current-change="handleCurrentChange" style="margin-top: 20px; text-align: right;" />
      </div>
    </div>

    <!-- 任务创建向导对话框 -->
    <el-dialog :title="copyFromTask ? $t('tasks.copyTask') : $t('tasks.createTask')" v-model="taskWizardVisible"
      width="60vw" :before-close="handleWizardClose" :close-on-click-modal="false" :close-on-press-escape="false">
      <TaskWizard v-model:visible="taskWizardVisible" :copy-from-task="copyFromTask" @created="handleTaskCreated" />
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-drawer v-model="detailDialogVisible" :title="$t('tasks.taskDetail')" direction="rtl"
      :size="isFullscreen ? '80vw' : '45vw'" :with-header="false" custom-class="task-detail-drawer"
      :close-on-click-modal="false">
      <div class="drawer-header">
        <span>{{ $t('tasks.taskDetailTitle') }}</span>
        <div>
          <el-button :icon="FullScreen" @click="isFullscreen = !isFullscreen" circle />
          <el-button :icon="Close" @click="detailDialogVisible = false" circle />
        </div>
      </div>
      <div class="task-detail-content">
        <TaskDetail :task="selectedTask" :nodes="nodes" />
      </div>
    </el-drawer>

    <!-- 任务日志对话框 -->
    <el-dialog
      :title="`${$t('tasks.taskLogs')}${logsAutoRefresh ? ` (${$t('tasks.autoRefresh')}: ${logsRefreshCountdown}s)` : ''}`"
      v-model="logsDialogVisible" width="1000px" :before-close="handleLogsDialogClose">
      <div class="logs-container">
        <div class="logs-toolbar">
          <div class="logs-toolbar-left">
            <el-button-group>
              <el-button :type="logLevel === 'all' ? 'primary' : 'default'" @click="logLevel = 'all'">
                {{ $t('tasks.logLevels.all') }}
              </el-button>
              <el-button :type="logLevel === 'error' ? 'danger' : 'default'" @click="logLevel = 'error'">
                {{ $t('tasks.logLevels.error') }}
              </el-button>
              <el-button :type="logLevel === 'progress' ? 'success' : 'default'" @click="logLevel = 'progress'">
                {{ $t('tasks.logLevels.progress') }}
              </el-button>
            </el-button-group>

            <!-- 刷新配置 -->
            <div class="refresh-config">
              <el-select v-model="logsRefreshInterval" :placeholder="$t('tasks.refreshInterval')" size="small"
                style="width: 120px; margin-left: 10px;" @change="handleLogsRefreshIntervalChange">
                <el-option :label="$t('tasks.closeRefresh')" :value="0" />
                <el-option :label="`3${$t('tasks.seconds')}`" :value="3000" />
                <el-option :label="`5${$t('tasks.seconds')}`" :value="5000" />
                <el-option :label="`30${$t('tasks.seconds')}`" :value="30000" />
                <el-option :label="`1${$t('tasks.minutes')}`" :value="60000" />
                <el-option :label="`5${$t('tasks.minutes')}`" :value="300000" />
              </el-select>

              <el-button :type="logsAutoRefresh ? 'success' : 'default'" :icon="logsAutoRefresh ? Loading : Refresh"
                size="small" style="margin-left: 5px;" @click="toggleLogsAutoRefresh" :loading="logsAutoRefresh">
                {{ logsAutoRefresh ? `${logsRefreshCountdown}s` : $t('tasks.manualRefresh') }}
              </el-button>
            </div>
          </div>

          <div class="logs-toolbar-right">
            <el-button @click="fetchTaskLogs" :icon="Refresh">{{ $t('tasks.refresh') }}</el-button>
            <el-button @click="cleanupLogs('duplicate')" :icon="Delete" style="margin-left: 10px;">
              {{ $t('tasks.refreshDuplicateLogs') }}
            </el-button>
            <el-button @click="cleanupLogs('old')" :icon="Warning" style="margin-left: 10px;">
              {{ $t('tasks.refreshOldLogs') }}
            </el-button>
          </div>
        </div>

        <el-table :data="filteredLogs" v-loading="logsLoading" height="400" style="width: 100%"
          :default-sort="{ prop: 'created_at', order: 'descending' }" :row-key="(row) => row.id">
          <el-table-column prop="created_at" :label="$t('common.time')" width="180" sortable>
            <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column prop="status" :label="$t('tasks.status')" width="100">
            <template #default="{ row }">
              <el-tag :type="getLogStatusType(row.status, row.message)" size="small">
                {{ row.message && row.message.includes('同步进度') ? $t('tasks.logLevels.progress') : row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="message" :label="$t('common.message')" show-overflow-tooltip>
            <template #default="{ row }">
              <span :class="getLogMessageClass(row.status, row.message)">{{ row.message }}</span>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页 -->
        <div class="logs-pagination" v-if="logsPagination.total > logsPagination.per_page">
          <el-pagination v-model:current-page="logsPagination.page" v-model:page-size="logsPagination.per_page"
            :page-sizes="[20, 50, 100, 200]" :total="logsPagination.total"
            layout="total, sizes, prev, pager, next, jumper" @size-change="handleLogsSizeChange"
            @current-change="handleLogsCurrentChange" />
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useI18n } from 'vue-i18n'
import {
  Plus, Search, Refresh, VideoPlay, VideoPause,
  RefreshRight, More, InfoFilled, Close, FullScreen,
  Edit, Document, Connection, CopyDocument, Delete,
  CircleCheck, Clock, Loading, Warning, CircleClose
} from '@element-plus/icons-vue'
import TaskWizard from '@/components/task-wizard/TaskWizard.vue'
import TaskDetail from '@/components/TaskDetail.vue'
import axios from 'axios'

const { t } = useI18n()

// 响应式数据
const loading = ref(false)
const submitting = ref(false)
const tasks = ref([])
const nodes = ref([])
const clients = ref([])
const storages = ref([])
const selectedTasks = ref([])
const selectedTask = ref(null)
const loadingTasks = ref(new Set()) // 用于跟踪正在执行操作的任务

// 统计数据
const taskStats = ref({})
const OnlineNodeStats = ref(0)

// 搜索和筛选
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 自动刷新
const autoRefresh = ref(true)
const refreshInterval = ref(null)
const refreshCountdown = ref(30)
const totalTasks = ref(0)

// 对话框状态
const taskWizardVisible = ref(false)
const detailDialogVisible = ref(false)
const logsDialogVisible = ref(false)
const isFullscreen = ref(false)
const copyFromTask = ref(null) // 新增：要复制的任务

// 日志
const taskLogs = ref([])
const logsLoading = ref(false)
const logLevel = ref('all')
const currentTaskId = ref(null)
const logsPagination = ref({
  page: 1,
  per_page: 20,
  total: 0
})

// 日志自动刷新配置
const logsRefreshInterval = ref(parseInt(localStorage.getItem('logsRefreshInterval') || '0')) // 从本地存储读取
const logsAutoRefresh = ref(false)
const logsRefreshCountdown = ref(0)
const logsRefreshTimer = ref(null)



// 计算属性
const filteredTasks = computed(() => {
  let filtered = tasks.value

  // 搜索筛选
  if (searchQuery.value) {
    filtered = filtered.filter(task =>
      task.name.toLowerCase().includes(searchQuery.value.toLowerCase())
    )
  }

  // 状态筛选
  if (statusFilter.value) {
    filtered = filtered.filter(task => task.status === statusFilter.value)
  }

  // 类型筛选
  if (typeFilter.value) {
    filtered = filtered.filter(task => task.type === typeFilter.value)
  }

  return filtered
})

const filteredLogs = computed(() => {
  if (logLevel.value === 'all') {
    return taskLogs.value
  } else if (logLevel.value === 'progress') {
    return taskLogs.value.filter(log => log.message && log.message.includes('同步进度'))
  } else if (logLevel.value === 'error') {
    return taskLogs.value.filter(log => log.status === 'error')
  }
  return taskLogs.value.filter(log => log.status === logLevel.value)
})

// 在线节点
const onlineNodes = computed(() => {
  return nodes.value.filter(node => node.status === 'online')
})

// API 方法
// 获取统计数据
const fetchStatistics = async () => {
  try {
    const response = await axios.get('/api/tasks/statistics')
    taskStats.value = response.data.data

    // 获取在线节点数
    const nodesResponse = await axios.get('/api/nodes')
    OnlineNodeStats.value = nodesResponse.data.data.filter(node => node.status === 'online').length
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 自动刷新功能
const startAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }

  refreshCountdown.value = 30
  refreshInterval.value = setInterval(() => {
    refreshCountdown.value--

    if (refreshCountdown.value <= 0) {
      fetchTasks()
      refreshCountdown.value = 30
    }
  }, 1000)
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/tasks', {
      params: {
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    if (response.data.status === 'success') {
      tasks.value = response.data.data || []
      totalTasks.value = response.data.total || 0
    }
    fetchStatistics()
  } catch (error) {
    ElMessage.error(t('tasks.messages.operationFailed'))
  } finally {
    loading.value = false
  }
}

const fetchNodes = async () => {
  try {
    const response = await axios.get('/api/nodes')
    if (response.data.status === 'success') {
      nodes.value = response.data.data || []
    }
  } catch (error) {
    ElMessage.error(t('tasks.messages.operationFailed'))
  }
}

const fetchClients = async () => {
  try {
    const response = await axios.get('/api/clients')
    if (response.data.status === 'success') {
      clients.value = response.data.data || []
    }
  } catch (error) {
    ElMessage.error('获取客户端列表失败')
  }
}

const fetchStorages = async () => {
  try {
    const response = await axios.get('/api/storages')
    if (response.data.status === 'success') {
      storages.value = response.data.data || []
    }
  } catch (error) {
    ElMessage.error('获取存储列表失败')
  }
}

const fetchTaskLogs = async () => {
  if (!currentTaskId.value || logsLoading.value) return

  logsLoading.value = true
  try {
    const response = await axios.get(`/api/tasks/${currentTaskId.value}/logs`, {
      params: {
        page: logsPagination.value.page,
        per_page: logsPagination.value.per_page
      }
    })
    if (response.data.status === 'success') {
      const allLogs = response.data.data || []

      // 优化日志显示：对于进度日志，只保留最新的一条
      const progressLogs = allLogs.filter(log => log.message && log.message.includes('同步进度'))
      const otherLogs = allLogs.filter(log => !log.message || !log.message.includes('同步进度'))

      // 如果有进度日志，只取最新的一条
      const latestProgressLog = progressLogs.length > 0
        ? progressLogs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at))[0]
        : null

      // 合并日志，进度日志放在最前面
      taskLogs.value = latestProgressLog
        ? [latestProgressLog, ...otherLogs]
        : otherLogs

      logsPagination.value.total = response.data.total || 0
      logsPagination.value.page = response.data.page || 1
      logsPagination.value.per_page = response.data.per_page || 20
    }
  } catch (error) {
    ElMessage.error('获取任务日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 清理日志功能
const cleanupLogs = async (type = 'duplicate') => {
  try {
    const response = await axios.post(`/api/tasks/${currentTaskId.value}/logs/cleanup`, {
      type: type,
      days: 7
    })

    if (response.data.status === 'success') {
      ElMessage.success(response.data.message)
      // 重新获取日志
      if (currentTaskId.value) {
        fetchTaskLogs()
      }
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '清理日志失败')
  }
}

// 日志分页处理
const handleLogsSizeChange = (size) => {
  logsPagination.value.per_page = size
  logsPagination.value.page = 1
  fetchTaskLogs()
}

const handleLogsCurrentChange = (page) => {
  logsPagination.value.page = page
  fetchTaskLogs()
}

// 日志自动刷新相关方法
const handleLogsRefreshIntervalChange = (interval) => {
  // 保存到本地存储
  localStorage.setItem('logsRefreshInterval', interval.toString())

  stopLogsAutoRefresh()
  if (interval > 0) {
    startLogsAutoRefresh(interval)
  }
}

const startLogsAutoRefresh = (interval = null) => {
  const refreshInterval = interval || logsRefreshInterval.value
  if (refreshInterval <= 0) return

  stopLogsAutoRefresh()

  logsAutoRefresh.value = true
  logsRefreshInterval.value = refreshInterval
  logsRefreshCountdown.value = Math.floor(refreshInterval / 1000)

  logsRefreshTimer.value = setInterval(() => {
    logsRefreshCountdown.value--

    if (logsRefreshCountdown.value <= 0) {
      // 执行刷新
      fetchTaskLogs()
      logsRefreshCountdown.value = Math.floor(refreshInterval / 1000)
    }
  }, 1000)
}

const stopLogsAutoRefresh = () => {
  if (logsRefreshTimer.value) {
    clearInterval(logsRefreshTimer.value)
    logsRefreshTimer.value = null
  }
  logsAutoRefresh.value = false
  logsRefreshCountdown.value = 0
}

const toggleLogsAutoRefresh = () => {
  if (logsAutoRefresh.value) {
    stopLogsAutoRefresh()
  } else if (logsRefreshInterval.value > 0) {
    startLogsAutoRefresh()
  } else {
    // 如果没有设置间隔，默认使用5秒
    startLogsAutoRefresh(5000)
  }
}

// 事件处理
const handleSearch = () => {
  currentPage.value = 1
}

const handleFilter = () => {
  currentPage.value = 1
}

const handleSelectionChange = (selection) => {
  selectedTasks.value = selection
}

const handleSizeChange = (size) => {
  pageSize.value = size
  fetchTasks()
}

const handleCurrentChange = (page) => {
  currentPage.value = page
  fetchTasks()
}

const showCreateDialog = () => {
  copyFromTask.value = null // 清空复制任务
  taskWizardVisible.value = true
}

const handleViewLogs = (task) => {
  currentTaskId.value = task.id
  logsDialogVisible.value = true
  fetchTaskLogs()

  // 如果之前设置了自动刷新，则启动
  if (logsRefreshInterval.value > 0) {
    startLogsAutoRefresh()
  }
}

const handleWizardClose = () => {
  taskWizardVisible.value = false
  copyFromTask.value = null
}

const handleLogsDialogClose = () => {
  logsDialogVisible.value = false
  stopLogsAutoRefresh()
  currentTaskId.value = null
}

const handleTaskCreated = (task) => {
  ElMessage.success(copyFromTask.value ? '任务复制成功' : '任务创建成功')
  copyFromTask.value = null
  fetchTasks()
}



// 新增任务管理方法
const handleStartTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return

  loadingTasks.value.add(task.id)
  try {
    await axios.post(`/api/tasks/${task.id}/start`)
    ElMessage.success('任务启动成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '启动失败')
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

const handlePauseTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return

  loadingTasks.value.add(task.id)
  try {
    await axios.post(`/api/tasks/${task.id}/pause`)
    ElMessage.success('任务暂停请求已发送')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '暂停失败')
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

const handleResumeTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return

  loadingTasks.value.add(task.id)
  try {
    await axios.post(`/api/tasks/${task.id}/resume`)
    ElMessage.success('任务恢复请求已发送')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '恢复失败')
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

const handleCancelTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return

  try {
    await ElMessageBox.confirm('确定要取消此任务吗？', '提示', {
      type: 'warning'
    })

    loadingTasks.value.add(task.id)
    const response = await axios.post(`/api/tasks/${task.id}/cancel`)

    if (response.data.status === 'success') {
      // 根据任务状态显示不同的消息
      if (task.status === 'running' || task.status === 'assigned') {
        ElMessage.success('任务取消请求已发送，正在等待Agent处理...')
        // 对于运行中的任务，启动轮询检查取消状态
        startCancelStatusPolling(task.id)
      } else {
        ElMessage.success('任务已取消')
      }
    }

    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '取消失败')
    }
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

// 取消状态轮询
const cancelPollingTimers = ref(new Map())

const startCancelStatusPolling = (taskId) => {
  // 清除之前的轮询
  if (cancelPollingTimers.value.has(taskId)) {
    clearInterval(cancelPollingTimers.value.get(taskId))
  }

  // 启动新的轮询
  const timer = setInterval(async () => {
    try {
      const response = await axios.get(`/api/tasks/${taskId}`)
      if (response.data.status === 'success') {
        const task = response.data.data
        if (task.status === 'cancelled') {
          ElMessage.success('任务已成功取消')
          clearInterval(timer)
          cancelPollingTimers.value.delete(taskId)
          fetchTasks()
        } else if (task.status === 'cancel_requested') {
          // 继续轮询
        } else if (task.status === 'running') {
          // 如果状态又变回running，说明取消失败
          ElMessage.warning('任务取消失败，状态已恢复为运行中')
          clearInterval(timer)
          cancelPollingTimers.value.delete(taskId)
          fetchTasks()
        }
      }
    } catch (error) {
      console.error('轮询任务状态失败:', error)
    }
  }, 2000) // 每2秒检查一次

  cancelPollingTimers.value.set(taskId, timer)

  // 30秒后自动停止轮询
  setTimeout(() => {
    if (cancelPollingTimers.value.has(taskId)) {
      clearInterval(cancelPollingTimers.value.get(taskId))
      cancelPollingTimers.value.delete(taskId)
      ElMessage.warning('任务取消状态检查超时，请手动刷新查看最新状态')
    }
  }, 30000)
}

const handleDeleteTask = async (task) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？此操作不可恢复。', '危险操作', {
      type: 'error',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })

    const force = ['running', 'assigned'].includes(task.status)
    await axios.delete(`/api/tasks/${task.id}${force ? '?force=true' : ''}`)
    ElMessage.success('删除任务成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const handleDuplicateTask = async (task) => {
  try {
    // 获取任务的完整详情
    const response = await axios.get(`/api/tasks/${task.id}`)
    if (response.data.status === 'success') {
      const taskDetail = response.data.data
      // 验证任务数据是否完整
      if (!taskDetail.source_storage_id || !taskDetail.target_storage_id) {
        ElMessage.warning('该任务配置不完整，无法复制')
        return
      }

      // 先显示对话框
      taskWizardVisible.value = true
      // 等待对话框挂载完成
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 300))
      // 再设置复制任务数据
      copyFromTask.value = taskDetail
    } else {
      ElMessage.error(response.data.message || '获取任务详情失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '获取任务详情失败')
  }
}

const getProgressTooltip = (task) => {
  // 只有运行中的任务才显示详细信息
  if (task.status !== 'running' && task.status !== 'assigned') {
    return null
  }

  const details = []

  // 添加进度信息
  if (task.progress !== undefined && task.progress !== null) {
    details.push(`同步进度: ${task.progress.toFixed(1)}%`)
  }

  // 添加传输大小信息
  if (task.details && task.details.transferred_size && task.details.total_size) {
    const transferred = formatBytes(task.details.transferred_size)
    const total = formatBytes(task.details.total_size)
    details.push(`(${transferred}/${total})`)
  }

  // 添加传输速率
  if (task.details && task.details.transfer_speed) {
    const transfer_speed = task.details.transfer_speed
    details.push(`速率: ${transfer_speed}`)
  }

  // 添加剩余时间信息
  if (task.details && task.details.eta) {
    const eta = task.details.eta
    details.push(`剩余时间: ${eta}`)
  }

  return details.length > 0 ? details.join(' ') : null
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getStorageConfigFromTask = (task) => {
  // 根据任务类型获取存储配置
  if (task.source_type === 'storage') {
    return {
      id: task.source_storage_id,
      name: task.source_storage_name,
      type: task.source_storage_type,
      config: task.source_storage_config
    }
  }

  if (task.source_storage) {
    return {
      id: task.source_storage.id,
      name: task.source_storage.name,
      type: task.source_storage.type,
      config: task.source_storage.config
    }
  }
  return null
}

const handleDropdownCommand = (command, task) => {
  switch (command) {
    case 'logs':
      handleViewLogs(task)
      break
    case 'detail':
      handleViewDetail(task)
      break
    case 'duplicate':
      handleDuplicateTask(task)
      break
    case 'delete':
      handleDeleteTask(task)
      break
    default:
      console.warn('Unknown command:', command)
  }
}

const handleViewDetail = async (task) => {
  try {
    const response = await axios.get(`/api/tasks/${task.id}`)
    if (response.data.status === 'success') {
      selectedTask.value = response.data.data
    } else {
      ElMessage.error(response.data.message || '获取任务详情失败')
      return
    }
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '获取任务详情失败')
  }
}

const handleRetryTask = async (task) => {
  try {
    await axios.post(`/api/tasks/${task.id}/retry`)
    ElMessage.success('重试任务成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '重试失败')
  }
}

// 批量操作
const batchCancel = async () => {
  if (selectedTasks.value.length === 0) return

  try {
    await ElMessageBox.confirm(`确定要取消选中的 ${selectedTasks.value.length} 个任务吗？`, '提示', {
      type: 'warning'
    })

    const taskIds = selectedTasks.value.map(task => task.id)
    await axios.put('/api/tasks/batch/cancel', { task_ids: taskIds })
    ElMessage.success('批量取消成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '批量取消失败')
    }
  }
}

const batchRetry = async () => {
  if (selectedTasks.value.length === 0) return

  try {
    await ElMessageBox.confirm(`确定要重试选中的 ${selectedTasks.value.length} 个任务吗？`, '提示', {
      type: 'warning'
    })

    const taskIds = selectedTasks.value.map(task => task.id)
    await axios.put('/api/tasks/batch/retry', { task_ids: taskIds })
    ElMessage.success('批量重试成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '批量重试失败')
    }
  }
}

const batchDelete = async () => {
  if (selectedTasks.value.length === 0) return

  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${selectedTasks.value.length} 个任务吗？`, '提示', {
      type: 'warning'
    })

    const taskIds = selectedTasks.value.map(task => task.id)
    await axios.delete('/api/tasks/batch/delete', { data: { task_ids: taskIds } })
    ElMessage.success('批量删除成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '批量删除失败')
    }
  }
}

// 自动刷新
const toggleAutoRefresh = () => {
  autoRefresh.value = !autoRefresh.value
  if (autoRefresh.value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

// 工具函数
const getStatusType = (status) => {
  const types = {
    active: 'success',
    pending: 'info',
    assigned: 'warning',
    running: 'success',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
    cancel_requested: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    active: t('tasks.statuses.running'),
    pending: t('tasks.statuses.pending'),
    assigned: t('tasks.statuses.assigned'),
    running: t('tasks.statuses.running'),
    completed: t('tasks.statuses.completed'),
    failed: t('tasks.statuses.failed'),
    cancelled: t('tasks.statuses.cancelled'),
    cancel_requested: t('tasks.statuses.cancelled')
  }
  return texts[status] || status
}

// 新增：获取状态对应的图标
const getStatusIcon = (status) => {
  const icons = {
    active: CircleCheck,
    pending: Clock,
    assigned: Loading,
    running: Loading,
    completed: CircleCheck,
    failed: CircleClose,
    cancelled: Warning,
    cancel_requested: Warning
  }
  return icons[status] || Clock
}

const getTaskTypeColor = (type) => {
  const colors = {
    sync: 'primary',
    copy: 'success',
    'mount-check': 'warning'
  }
  return colors[type] || 'info'
}

const getTaskTypeText = (type) => {
  const texts = {
    sync: t('tasks.types.sync'),
    copy: t('tasks.types.copy'),
    'mount-check': t('tasks.types.mountCheck')
  }
  return texts[type] || type
}

const getPriorityType = (priority) => {
  const types = {
    1: 'info',
    2: 'success',
    3: 'warning',
    4: 'danger'
  }
  return types[priority] || 'info'
}

const getPriorityText = (priority) => {
  const texts = {
    1: t('tasks.priorities.low'),
    2: t('tasks.priorities.normal'),
    3: t('tasks.priorities.high'),
    4: t('tasks.priorities.urgent')
  }
  return texts[priority] || t('tasks.priorities.normal')
}

const getProgressStatus = (status) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  return ''
}

const getNodeName = (nodeId) => {
  const node = nodes.value.find(n => n.id === nodeId)
  return node ? node.name : `节点${nodeId}`
}

const getLogStatusType = (status, message) => {
  // 如果是同步进度消息，显示为进度类型
  if (message && message.includes('同步进度')) {
    return 'success'
  }

  const types = {
    error: 'danger',
    progress: 'success',
    created: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return types[status] || 'info'
}

const getLogMessageClass = (status, message) => {
  return {
    'log-error': status === 'error',
    'log-success': (status === 'progress' || status === 'completed') || (message && message.includes('同步进度')),
    'log-warning': status === 'running'
  }
}

const getStorageTypeColor = (type) => {
  const colors = {
    local: 'info',
    nfs: 'success',
    smb: 'warning',
    ftp: 'danger',
    s3: 'primary',
    obs: 'primary',
    nas: 'success'
  }
  return colors[type] || 'info'
}

const getStorageTypeText = (type) => {
  const texts = {
    local: '本地',
    nfs: 'NFS',
    smb: 'SMB',
    ftp: 'FTP',
    s3: 'S3',
    obs: 'OBS',
    nas: 'NAS'
  }
  return texts[type] || type
}

// 新增工具函数
const isS3Storage = (storage) => {
  if (!storage) return false
  return ['s3', 'obs'].includes(storage.type)
}



const formatDateTime = (datetime) => {
  if (!datetime) return '-'
  return new Date(datetime).toLocaleString()
}

// 生命周期
onMounted(() => {
  fetchTasks()
  fetchNodes()
  fetchClients()
  fetchStorages()
  fetchStatistics()
  if (autoRefresh.value) {
    startAutoRefresh()
  }
})

onUnmounted(() => {
  stopAutoRefresh()
  stopLogsAutoRefresh()

  // 清理取消状态轮询定时器
  cancelPollingTimers.value.forEach((timer) => {
    clearInterval(timer)
  })
  cancelPollingTimers.value.clear()
})
</script>

<style scoped>
.tasks-page {
  padding: 20px;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  margin: 0 0 5px 0;
  color: var(--text-color);
  font-size: 24px;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

/* 统计卡片样式 */
.stat-card {
  border: 1px solid var(--border-color);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.stat-card.running {
  background: var(--card-bg);
  color: var(--text-color);
}

.stat-card.pending {
  background: var(--card-bg);
  color: var(--text-color);
}

.stat-card.completed {
  background: var(--card-bg);
  color: var(--text-color);
}

.stat-card.failed {
  background: var(--card-bg);
  color: var(--text-color);
}

.stat-content {
  text-align: center;
  padding: 10px 0;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.refresh-timer {
  color: var(--text-secondary);
  font-size: 12px;
  margin-left: 8px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.batch-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px 20px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 8px;
}

.batch-info {
  color: #1890ff;
  font-weight: 500;
}

.table-container {
  padding: 20px;
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: var(--card-shadow);
}

.pagination-container {
  text-align: right;
  border-top: 1px solid var(--border-color);
}

.task-name {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.task-description {
  color: var(--text-secondary);
  font-size: 12px;
  margin-top: 2px;
}

.progress-text {
  margin-left: 8px;
  font-size: 12px;
  color: var(--text-secondary);
}

.text-muted {
  color: var(--text-secondary);
  font-size: 13px;
}

.config-card {
  margin-bottom: 0;
}

.config-card :deep(.el-card__body) {
  padding: 15px;
}

.dialog-footer {
  text-align: right;
}

.task-detail {
  max-height: 60vh;
  overflow-y: auto;
}

.task-config h4 {
  margin-bottom: 10px;
  color: var(--text-color);
}

.task-config pre {
  background: var(--bg-secondary);
  padding: 10px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}

.logs-container {
  height: 500px;
  display: flex;
  flex-direction: column;
}

.logs-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.logs-toolbar-left {
  display: flex;
  align-items: center;
}

.logs-toolbar-right {
  display: flex;
  align-items: center;
}

.refresh-config {
  display: flex;
  align-items: center;
  margin-left: 15px;
}

.logs-pagination {
  margin-top: 15px;
  text-align: right;
  padding: 10px 0;
  border-top: 1px solid var(--border-color);
}

.log-error {
  color: #f56c6c;
}

.log-success {
  color: #67c23a;
}

.log-warning {
  color: #e6a23c;
}

.task-detail-drawer :deep(.el-drawer__header) {
  padding: 15px 20px;
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-color);
}

.task-detail-drawer :deep(.el-drawer__body) {
  padding: 0;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
  /* Adjust for header and footer */
}

.task-detail-drawer :deep(.el-drawer__footer) {
  padding: 15px 20px;
  background: var(--bg-secondary);
  border-top: 1px solid var(--border-color);
}

.task-detail-content {
  max-height: 80vh;
  overflow-y: auto;
  padding: 20px 10px 10px 10px;
}

.config-section {
  margin-top: 20px;
  min-height: 320px;
}

.config-row {
  min-height: 320px;
}

.config-section .el-card {
  margin-bottom: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.ellipsis {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px 10px 24px;
  font-size: 20px;
  font-weight: 500;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: flex-start;
  }

  .header-right {
    margin-top: 15px;
  }

  .toolbar {
    flex-direction: column;
    align-items: flex-start;
  }

  .toolbar-right {
    margin-top: 15px;
  }
}

.mb-16 {
  margin-bottom: 16px;
}

.stat-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-icon {
  width: 55px;
  height: 55px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 22px;
  margin-right: 14px;
  background: var(--bg-color);
}

.stat-icon.total {
  color: #409EFF;
  background: #e8f3ff;
}

.stat-icon.running {
  color: #67C23A;
  background: #f0f9eb;
}

.stat-icon.pending {
  color: #E6A23C;
  background: #fdf6ec;
}

.stat-icon.completed {
  color: #409EFF;
  background: #e8f3ff;
}

.stat-icon.failed {
  color: #F56C6C;
  background: #fef0f0;
}

.stat-icon.online {
  color: var(--text-secondary);
  background: #f0f9eb;
}

.progress-container {
  cursor: pointer;
  padding: 2px 0;
}

.progress-container:hover {
  background-color: var(--el-fill-color-light);
  border-radius: 4px;
  padding: 2px 4px;
  margin: 0 -4px;
}
</style>