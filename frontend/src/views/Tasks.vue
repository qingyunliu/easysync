<template>
  <div class="tasks-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>任务管理</h1>
        <p class="page-description">管理和监控同步任务的创建、执行和状态</p>
      </div>
      <div class="header-right">
      <el-button type="primary" @click="showCreateDialog">
          <el-icon><Plus /></el-icon>
        创建任务
      </el-button>
      </div>
    </div>
    
    <!-- 统计面板 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content stat-flex">
            <div class="stat-icon total">
              <el-icon><Document /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.total || 0 }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card running">
          <div class="stat-content stat-flex">
            <div class="stat-icon running">
              <el-icon><Loading /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.running || 0 }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card pending">
          <div class="stat-content stat-flex">
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.pending || 0 }}</div>
              <div class="stat-label">等待中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card completed">
          <div class="stat-content stat-flex">
            <div class="stat-icon completed">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.completed || 0 }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card failed">
          <div class="stat-content stat-flex">
            <div class="stat-icon failed">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.failed || 0 }}</div>
              <div class="stat-label">已失败</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card online-node">
          <div class="stat-content stat-flex">
            <div class="stat-icon online">
              <el-icon><Connection /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ OnlineNodeStats || 0 }}</div>
              <div class="stat-label">在线节点</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 操作栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="searchQuery"
          placeholder="搜索任务名称..."
          style="width: 300px"
          clearable
          @input="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        
        <el-select
          v-model="statusFilter"
          placeholder="状态筛选"
          style="width: 150px; margin-left: 10px"
          clearable
          @change="handleFilter"
        >
          <el-option label="全部" value="" />
          <el-option label="等待中" value="pending" />
          <el-option label="已分配" value="assigned" />
          <el-option label="运行中" value="running" />
          <el-option label="已完成" value="completed" />
          <el-option label="失败" value="failed" />
          <el-option label="已取消" value="cancelled" />
        </el-select>

        <el-select
          v-model="typeFilter"
          placeholder="类型筛选"
          style="width: 150px; margin-left: 10px"
          clearable
          @change="handleFilter"
        >
          <el-option label="全部" value="" />
          <el-option label="文件同步" value="sync" />
          <el-option label="文件复制" value="copy" />
          <el-option label="挂载检测" value="mount-check" />
        </el-select>
      </div>
      
      <div class="toolbar-right">
        <el-button-group>
          <el-button
            :type="autoRefresh ? 'primary' : 'default'"
            @click="toggleAutoRefresh"
            :icon="autoRefresh ? VideoPause : Refresh"
          >
            {{ autoRefresh ? '暂停刷新' : '开启刷新' }}
          </el-button>
          <el-button @click="fetchTasks" :icon="Refresh">
            刷新
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 批量操作栏 -->
    <div v-if="selectedTasks.length > 0" class="batch-toolbar">
      <div class="batch-info">
        已选择 {{ selectedTasks.length }} 个任务
      </div>
      <div class="batch-actions">
        <el-button size="small" @click="batchCancel">批量取消</el-button>
        <el-button size="small" @click="batchRetry">批量重试</el-button>
        <el-button size="small" type="danger" @click="batchDelete">批量删除</el-button>
      </div>
    </div>

    <!-- 任务列表 -->
    <div class="table-container">
      <el-table
        :data="filteredTasks"
        v-loading="loading"
        @selection-change="handleSelectionChange"
        :default-sort="{ prop: 'created_at', order: 'descending' }"
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="任务名称" min-width="150" show-overflow-tooltip>
        <template #default="{ row }">
            <div class="task-name">
              <el-link type="primary" @click="handleViewDetail(row)">
                {{ row.name }}
              </el-link>
              <div class="task-description">{{ row.description || '无描述' }}</div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTaskTypeColor(row.type)" size="small">
              {{ getTaskTypeText(row.type) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)" size="small">
              <el-icon style="vertical-align: middle; margin-right: 4px;">
                <component :is="getStatusIcon(row.status)" />
              </el-icon>
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>

        <el-table-column prop="progress" label="进度" width="120">
        <template #default="{ row }">
            <el-progress
              :percentage="row.progress || 0"
              :status="getProgressStatus(row.status)"
              :stroke-width="6"
              :show-text="false"
            />
            <span class="progress-text">{{ row.progress || 0 }}%</span>
          </template>
        </el-table-column>

        <el-table-column prop="node_id" label="执行节点" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.node_id" type="info" size="small">
              {{ getNodeName(row.node_id) }}
            </el-tag>
            <span v-else class="text-muted">未分配</span>
          </template>
        </el-table-column>

        <el-table-column prop="priority" label="优先级" width="80">
          <template #default="{ row }">
            <el-tag :type="getPriorityType(row.priority)" size="small">
              {{ getPriorityText(row.priority) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button-group size="small">
              <!-- 启动/停止按钮 -->
            <el-button
                v-if="['pending', 'failed'].includes(row.status)"
                type="success"
                @click="handleStartTask(row)"
                :icon="VideoPlay"
                :loading="loadingTasks.has(row.id)"
              >
                启动
            </el-button>
              
              <!-- 暂停/恢复按钮 -->
            <el-button
                v-if="row.status === 'running'"
                type="warning"
                @click="handlePauseTask(row)"
                :icon="VideoPause"
                :loading="loadingTasks.has(row.id)"
              >
                暂停
            </el-button>
              
            <el-button
                v-if="row.status === 'paused'"
                type="success"
                @click="handleResumeTask(row)"
                :icon="VideoPlay"
                :loading="loadingTasks.has(row.id)"
              >
                恢复
            </el-button>
              
              <!-- 取消按钮 -->
            <el-button
                v-if="['running', 'assigned', 'paused'].includes(row.status)"
              type="danger"
                @click="handleCancelTask(row)"
                :icon="Close"
                :loading="loadingTasks.has(row.id)"
              >
                取消
              </el-button>
              
              <!-- 重试按钮 -->
              <el-button
                v-if="row.status === 'failed'"
                type="warning"
                @click="handleRetryTask(row)"
                :icon="RefreshRight"
                :loading="loadingTasks.has(row.id)"
              >
                重试
            </el-button>
          </el-button-group>
            
            <!-- 更多操作下拉菜单 -->
            <el-dropdown @command="(command) => handleDropdownCommand(command, row)" style="margin-left: 8px;">
              <el-button type="primary" :icon="More" size="small">
                更多
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logs">
                    <el-icon><Document /></el-icon>查看日志
                  </el-dropdown-item>
                  <el-dropdown-item command="detail">
                    <el-icon><InfoFilled /></el-icon>详情
                  </el-dropdown-item>
                  <el-dropdown-item command="test-connection" v-if="canTestConnection(row)">
                    <el-icon><Connection /></el-icon>测试连接
                  </el-dropdown-item>
                  <el-dropdown-item command="test-mount" v-if="canTestMount(row)">
                    <el-icon><Connection /></el-icon>测试挂载
                  </el-dropdown-item>
                  <el-dropdown-item command="duplicate">
                    <el-icon><CopyDocument /></el-icon>复制任务
                  </el-dropdown-item>
                  <el-dropdown-item 
                    command="delete" 
                    :disabled="['running', 'assigned'].includes(row.status)"
                    style="color: #f56c6c;"
                  >
                    <el-icon><Delete /></el-icon>删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalTasks"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          style="margin-top: 20px; text-align: right;"
        />
      </div>
    </div>
    
    <!-- 任务创建向导对话框 -->
    <el-dialog
      title="创建任务"
      v-model="taskWizardVisible"
      width="90vw"
      :before-close="handleWizardClose"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
    >
      <TaskWizard 
        v-model:visible="taskWizardVisible"
        @created="handleTaskCreated"
      />
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-drawer
      v-model="detailDialogVisible"
      title="任务详情"
      direction="rtl"
      :size="isFullscreen ? '80vw' : '45vw'"
      :with-header="false"
      custom-class="task-detail-drawer"
      :close-on-click-modal="false"
    >
      <div class="drawer-header">
        <span>任务详情</span>
        <div>
          <el-button :icon="FullScreen" @click="isFullscreen = !isFullscreen" circle />
          <el-button :icon="Close" @click="detailDialogVisible = false" circle />
        </div>
      </div>
      <div class="task-detail-content">
        <TaskDetail 
          :task="selectedTask"
          :nodes="nodes"
        />
      </div>
    </el-drawer>
    
    <!-- 任务日志对话框 -->
    <el-dialog
      title="任务日志"
      v-model="logsDialogVisible"
      width="1000px"
    >
      <div class="logs-container">
        <div class="logs-toolbar">
          <el-button-group>
            <el-button
              :type="logLevel === 'all' ? 'primary' : 'default'"
              @click="logLevel = 'all'"
            >
              全部
            </el-button>
            <el-button
              :type="logLevel === 'error' ? 'danger' : 'default'"
              @click="logLevel = 'error'"
            >
              错误
            </el-button>
            <el-button
              :type="logLevel === 'progress' ? 'success' : 'default'"
              @click="logLevel = 'progress'"
            >
              进度
            </el-button>
          </el-button-group>
          <el-button @click="fetchTaskLogs" :icon="Refresh">刷新</el-button>
        </div>
        
        <el-table
          :data="filteredLogs"
          v-loading="logsLoading"
          height="400"
          style="width: 100%"
        >
          <el-table-column prop="created_at" label="时间" width="180">
          <template #default="{ row }">
              {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>
          <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
              <el-tag :type="getLogStatusType(row.status)" size="small">
                {{ row.status }}
            </el-tag>
          </template>
        </el-table-column>
          <el-table-column prop="message" label="消息" show-overflow-tooltip>
          <template #default="{ row }">
              <span :class="getLogMessageClass(row.status)">{{ row.message }}</span>
          </template>
        </el-table-column>
      </el-table>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus, Search, Refresh, VideoPlay, VideoPause,
  RefreshRight, More, InfoFilled, Close, FullScreen,
  Edit, Document, Connection, CopyDocument, Delete,
  CircleCheck, Clock, Loading, Warning, CircleClose
} from '@element-plus/icons-vue'
import TaskWizard from '@/components/task-wizard/TaskWizard.vue'
import TaskDetail from '@/components/TaskDetail.vue'
import axios from 'axios'

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

// 日志
const taskLogs = ref([])
const logsLoading = ref(false)
const logLevel = ref('all')
const currentTaskId = ref(null)



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
    ElMessage.error('获取任务列表失败')
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
    ElMessage.error('获取节点列表失败')
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
  if (!currentTaskId.value) return
  
  logsLoading.value = true
  try {
    const response = await axios.get(`/api/tasks/${currentTaskId.value}/logs`)
    if (response.data.status === 'success') {
      taskLogs.value = response.data.data || []
    }
  } catch (error) {
    ElMessage.error('获取任务日志失败')
  } finally {
    logsLoading.value = false
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
  console.log('打开任务创建向导')
  taskWizardVisible.value = true
}

const handleViewLogs = (task) => {
  currentTaskId.value = task.id
  logsDialogVisible.value = true
  fetchTaskLogs()
}

const handleWizardClose = () => {
  taskWizardVisible.value = false
}

const handleTaskCreated = (task) => {
  ElMessage.success('任务创建成功')
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
    await axios.post(`/api/tasks/${task.id}/cancel`)
    ElMessage.success('任务取消请求已发送')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '取消失败')
    }
  } finally {
    loadingTasks.value.delete(task.id)
  }
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

const handleTestConnection = async (task) => {
  try {
    // 从任务中提取存储配置
    const storageConfig = getStorageConfigFromTask(task)
    console.log(task)
    if (!storageConfig) {
      ElMessage.error('无法获取存储配置信息')
      return
    }
    
    // 检查是否有可用的测试节点
    const nodesResponse = await axios.get('/api/nodes')
    const availableNodes = (nodesResponse.data.data || []).filter(
      node => node.status === 'online' && node.agent_status === 'running'
    )
    
    if (availableNodes.length === 0) {
      ElMessage.error('没有可用的测试节点，请确保有节点在线且Agent已启动')
      return
    }
    
    // 使用第一个可用节点进行测试
    const testNode = availableNodes[0]
    
    // 如果有存储ID，使用存储测试接口
    if (storageConfig.id) {
      const response = await axios.post(`/api/storages/${storageConfig.id}/test-connection`, {
        node_id: testNode.id
      })
      ElMessage.success('连接测试任务已创建并启动')
    } else {
      // 否则使用临时测试接口
      const response = await axios.post('/api/storages/test-connection', {
        type: storageConfig.type,
        config: storageConfig.config,
        node_id: testNode.id
      })
      ElMessage.success('连接测试任务已创建并启动')
    }
    
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '创建连接测试失败')
  }
}

const handleTestMount = async (task) => {
  try {
    // 从任务中提取存储配置和挂载点
    const storageConfig = getStorageConfigFromTask(task)
    const mountPoint = task.target_path || '/tmp/test_mount'
    
    if (!storageConfig) {
      ElMessage.error('无法获取存储配置信息')
      return
    }
    
    const response = await axios.post('/api/tasks/test-mount', {
      mount_point: mountPoint,
      storage_config: storageConfig
    })
    
    ElMessage.success('挂载测试任务已创建并启动')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '创建挂载测试失败')
  }
}

const handleDuplicateTask = (task) => {
  // 复制任务逻辑 - 暂时禁用，等待新的向导支持
  ElMessage.info('复制任务功能将在新版本中支持')
}

// 辅助方法
const canTestConnection = (task) => {
  if (task.status != 'cancelled' && task.status != 'cancel_requested' && task.status != 'failed') {
    return task.source_type === 'storage' && task.source_storage_id
  }
  return false
}

const canTestMount = (task) => {
  if (task.status != 'cancelled' && task.status != 'cancel_requested' && task.status != 'failed') {
    return task.source_type === 'storage' && task.source_storage_id && !isS3Storage(task.source_storage)
  }
  return false
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
    case 'test-connection':
      handleTestConnection(task)
      break
    case 'test-mount':
      handleTestMount(task)
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
    active: '活跃',
    pending: '等待中',
    assigned: '已分配',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
    cancel_requested: '取消中'
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
    sync: '同步',
    copy: '复制',
    'mount-check': '挂载检测'
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
    1: '低',
    2: '普通',
    3: '高',
    4: '紧急'
  }
  return texts[priority] || '普通'
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

const getLogStatusType = (status) => {
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

const getLogMessageClass = (status) => {
  return {
    'log-error': status === 'error',
    'log-success': status === 'progress' || status === 'completed',
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
  max-height: calc(100vh - 200px); /* Adjust for header and footer */
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
  background: #f4f4f5;
}
</style> 