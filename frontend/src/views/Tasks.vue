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
            :icon="autoRefresh ? Pause : Refresh"
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
        stripe
        style="width: 100%"
      >
        <el-table-column type="selection" width="55" />
        
        <el-table-column prop="name" label="任务名称" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="task-name">
              <el-link type="primary" @click="showTaskDetail(row)">
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

        <el-table-column label="操作" width="250" fixed="right">
          <template #default="{ row }">
            <el-button-group size="small">
              <el-button
                :type="row.status === 'running' ? 'danger' : 'success'"
                @click="handleTaskAction(row)"
                :disabled="['completed', 'cancelled'].includes(row.status)"
                :icon="row.status === 'running' ? VideoPlay : VideoPause"
              >
                {{ row.status === 'running' ? '停止' : '启动' }}
              </el-button>
              
              <el-button
                type="warning"
                @click="handleRetryTask(row)"
                :disabled="row.status !== 'failed'"
                :icon="RefreshRight"
              >
                重试
              </el-button>
              
              <el-dropdown @command="(command) => handleDropdownCommand(command, row)">
                <el-button type="primary" :icon="More">
                  更多
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit" :disabled="row.status === 'running'">
                      编辑
                    </el-dropdown-item>
                    <el-dropdown-item command="logs">
                      查看日志
                    </el-dropdown-item>
                    <el-dropdown-item command="detail">
                      详情
                    </el-dropdown-item>
                    <el-dropdown-item command="delete" :disabled="row.status === 'running'">
                      <span style="color: #f56c6c">删除</span>
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :total="totalTasks"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </div>

    <!-- 创建/编辑任务对话框 -->
    <el-dialog
      :title="dialogType === 'create' ? '创建任务' : '编辑任务'"
      v-model="taskDialogVisible"
      width="700px"
      :before-close="handleDialogClose"
    >
      <el-form
        ref="taskFormRef"
        :model="taskForm"
        :rules="taskRules"
        label-width="120px"
        size="default"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="任务名称" prop="name">
              <el-input v-model="taskForm.name" placeholder="请输入任务名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="任务类型" prop="type">
              <el-select v-model="taskForm.type" placeholder="选择任务类型" style="width: 100%">
                <el-option label="文件同步" value="sync" />
                <el-option label="文件复制" value="copy" />
                <el-option label="挂载检测" value="mount-check" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="优先级" prop="priority">
              <el-select v-model="taskForm.priority" placeholder="选择优先级" style="width: 100%">
                <el-option label="低" :value="1" />
                <el-option label="普通" :value="2" />
                <el-option label="高" :value="3" />
                <el-option label="紧急" :value="4" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="执行节点" prop="node_id">
              <el-select v-model="taskForm.node_id" placeholder="选择执行节点（可选）" style="width: 100%" clearable>
                <el-option
                  v-for="node in nodes"
                  :key="node.id"
                  :label="node.name"
                  :value="node.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="任务描述" prop="description">
          <el-input v-model="taskForm.description" type="textarea" :rows="2" placeholder="请输入任务描述" />
        </el-form-item>

        <!-- 源端配置 -->
        <el-form-item label="源端类型" prop="source_type">
          <el-radio-group v-model="taskForm.source_type" @change="handleSourceTypeChange">
            <el-radio-button label="client">客户端(Client)</el-radio-button>
            <el-radio-button label="storage">存储系统</el-radio-button>
          </el-radio-group>
        </el-form-item>

        <!-- 源端为客户端时的配置 -->
        <el-form-item v-if="taskForm.source_type === 'client'" label="源端客户端" prop="source_client_id">
          <el-select v-model="taskForm.source_client_id" placeholder="选择源端客户端" style="width: 100%">
            <el-option
              v-for="client in clients"
              :key="client.id"
              :label="`${client.name} (${client.ip_address})`"
              :value="client.id"
            >
              <div>
                <span>{{ client.name }}</span>
                <span style="color: #8492a6; font-size: 12px; margin-left: 10px">{{ client.ip_address }}</span>
                <el-tag v-if="client.status === 'online'" type="success" size="small" style="margin-left: 10px">在线</el-tag>
                <el-tag v-else type="danger" size="small" style="margin-left: 10px">离线</el-tag>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 源端为存储时的配置 -->
        <el-form-item v-if="taskForm.source_type === 'storage'" label="源端存储" prop="source_storage_id">
          <el-select v-model="taskForm.source_storage_id" placeholder="选择源端存储" style="width: 100%">
            <el-option
              v-for="storage in storages"
              :key="storage.id"
              :label="`${storage.name} (${storage.type})`"
              :value="storage.id"
            >
              <div>
                <span>{{ storage.name }}</span>
                <el-tag :type="getStorageTypeColor(storage.type)" size="small" style="margin-left: 10px">
                  {{ getStorageTypeText(storage.type) }}
                </el-tag>
                <span style="color: #8492a6; font-size: 12px; margin-left: 10px">{{ storage.config?.host || storage.config?.bucket || '本地' }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 源端路径配置 -->
        <el-form-item :label="getSourcePathLabel()" prop="source_path">
          <el-input 
            v-model="taskForm.source_path" 
            :placeholder="getSourcePathPlaceholder()"
          />
          <div v-if="isS3Storage(getSourceStorage())" style="margin-top: 5px; font-size: 12px; color: #909399">
            <el-icon><InfoFilled /></el-icon>
            S3对象存储路径格式：bucket/path/to/object（无需挂载点）
          </div>
        </el-form-item>

        <!-- 目标端配置 -->
        <el-form-item label="目标端存储" prop="target_storage_id">
          <el-select v-model="taskForm.target_storage_id" placeholder="选择目标端存储" style="width: 100%">
            <el-option
              v-for="storage in storages"
              :key="storage.id"
              :label="`${storage.name} (${storage.type})`"
              :value="storage.id"
            >
              <div>
                <span>{{ storage.name }}</span>
                <el-tag :type="getStorageTypeColor(storage.type)" size="small" style="margin-left: 10px">
                  {{ getStorageTypeText(storage.type) }}
                </el-tag>
                <span style="color: #8492a6; font-size: 12px; margin-left: 10px">{{ storage.config?.host || storage.config?.bucket || '本地' }}</span>
              </div>
            </el-option>
          </el-select>
        </el-form-item>

        <!-- 目标端路径配置 -->
        <el-form-item label="目标端存储路径" prop="target_path">
          <el-input 
            v-model="taskForm.target_path" 
            :placeholder="getTargetPathPlaceholder()"
          />
          <div v-if="isS3Storage(getTargetStorage())" style="margin-top: 5px; font-size: 12px; color: #909399">
            <el-icon><InfoFilled /></el-icon>
            S3对象存储路径格式：bucket/path/to/object（无需挂载点）
          </div>
        </el-form-item>

        <!-- 节点分配 (仅当源端为存储时显示) -->
        <el-form-item v-if="taskForm.source_type === 'storage'" label="执行节点" prop="node_id">
          <el-select v-model="taskForm.node_id" placeholder="选择执行节点" style="width: 100%">
            <el-option label="自动分配" value="" />
            <el-option
              v-for="node in onlineNodes"
              :key="node.id"
              :label="`${node.name} (${node.ipaddress})`"
              :value="node.id"
            >
              <div>
                <span>{{ node.name }}</span>
                <span style="color: #8492a6; font-size: 12px; margin-left: 10px">{{ node.ipaddress }}</span>
                <el-tag type="success" size="small" style="margin-left: 10px">在线</el-tag>
                <span style="color: #8492a6; font-size: 12px; margin-left: 10px">负载: {{ node.current_tasks || 0 }}</span>
              </div>
            </el-option>
          </el-select>
          <div style="margin-top: 5px; font-size: 12px; color: #909399">
            <el-icon><InfoFilled /></el-icon>
            {{ taskForm.source_type === 'storage' ? '节点将负责挂载源存储和目标存储，并执行同步任务' : '如不选择将自动分配负载最低的节点' }}
          </div>
        </el-form-item>

        <el-form-item label="同步选项">
          <el-card class="config-card">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-checkbox v-model="taskForm.options.delete">删除目标多余文件</el-checkbox>
              </el-col>
              <el-col :span="8">
                <el-checkbox v-model="taskForm.options.compress">启用压缩传输</el-checkbox>
              </el-col>
              <el-col :span="8">
                <el-checkbox v-model="taskForm.options.checksum">校验文件完整性</el-checkbox>
              </el-col>
            </el-row>
            <el-row :gutter="20" style="margin-top: 10px">
              <el-col :span="12">
                <el-form-item label="带宽限制(MB/s)" style="margin-bottom: 0">
                  <el-input-number
                    v-model="taskForm.options.bandwidth_limit"
                    :min="0"
                    :max="1000"
                    placeholder="0表示无限制"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="并发连接数" style="margin-bottom: 0">
                  <el-input-number
                    v-model="taskForm.options.max_connections"
                    :min="1"
                    :max="10"
                    placeholder="默认为1"
                    style="width: 100%"
                  />
                </el-form-item>
              </el-col>
            </el-row>
          </el-card>
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="taskDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmitTask" :loading="submitting">
            {{ dialogType === 'create' ? '创建' : '更新' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 任务详情对话框 -->
    <el-dialog
      title="任务详情"
      v-model="detailDialogVisible"
      width="900px"
    >
      <div v-if="selectedTask" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ selectedTask.name }}</el-descriptions-item>
          <el-descriptions-item label="任务类型">
            <el-tag :type="getTaskTypeColor(selectedTask.type)">
              {{ getTaskTypeText(selectedTask.type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedTask.status)">
              {{ getStatusText(selectedTask.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="进度">
            <el-progress
              :percentage="selectedTask.progress || 0"
              :status="getProgressStatus(selectedTask.status)"
              :stroke-width="6"
            />
          </el-descriptions-item>
          <el-descriptions-item label="优先级">
            <el-tag :type="getPriorityType(selectedTask.priority)">
              {{ getPriorityText(selectedTask.priority) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="执行节点">
            {{ selectedTask.node_id ? getNodeName(selectedTask.node_id) : '未分配' }}
          </el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatDateTime(selectedTask.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">
            {{ selectedTask.started_at ? formatDateTime(selectedTask.started_at) : '未开始' }}
          </el-descriptions-item>
          <el-descriptions-item label="完成时间">
            {{ selectedTask.completed_at ? formatDateTime(selectedTask.completed_at) : '未完成' }}
          </el-descriptions-item>
          <el-descriptions-item label="错误信息" v-if="selectedTask.error">
            <el-text type="danger">{{ selectedTask.error }}</el-text>
          </el-descriptions-item>
        </el-descriptions>
        
        <div class="task-config" style="margin-top: 20px">
          <h4>配置信息</h4>
          <el-tabs>
            <el-tab-pane label="源配置" name="source">
              <pre>{{ JSON.stringify(selectedTask.source, null, 2) }}</pre>
            </el-tab-pane>
            <el-tab-pane label="目标配置" name="target">
              <pre>{{ JSON.stringify(selectedTask.target, null, 2) }}</pre>
            </el-tab-pane>
            <el-tab-pane label="同步选项" name="options">
              <pre>{{ JSON.stringify(selectedTask.options, null, 2) }}</pre>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </el-dialog>

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
  RefreshRight, More, InfoFilled
} from '@element-plus/icons-vue'
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

// 搜索和筛选
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const totalTasks = ref(0)

// 对话框状态
const taskDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const logsDialogVisible = ref(false)
const dialogType = ref('create')

// 自动刷新
const autoRefresh = ref(false)
const refreshInterval = ref(null)

// 日志
const taskLogs = ref([])
const logsLoading = ref(false)
const logLevel = ref('all')
const currentTaskId = ref(null)

// 表单引用
const taskFormRef = ref(null)

// 任务表单
const taskForm = ref({
  name: '',
  description: '',
  type: 'sync',
  priority: 2,
  source_type: 'client', // client 或 storage
  source_client_id: '', // 源端客户端ID
  source_storage_id: '', // 源端存储ID
  source_path: '', // 源端路径
  target_storage_id: '', // 目标存储ID
  target_path: '', // 目标路径
  node_id: '', // 执行节点ID (仅当源端为存储时)
  options: {
    delete: false,
    compress: false,
    checksum: true,
    bandwidth_limit: 0,
    max_connections: 1
  }
})

// 表单验证规则
const taskRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 2, max: 50, message: '长度在 2 到 50 个字符', trigger: 'blur' }
  ],
  type: [
    { required: true, message: '请选择任务类型', trigger: 'change' }
  ],
  priority: [
    { required: true, message: '请选择优先级', trigger: 'change' }
  ],
  source_type: [
    { required: true, message: '请选择源端类型', trigger: 'change' }
  ],
  source_client_id: [
    { required: true, message: '请选择源端客户端', trigger: 'change' }
  ],
  source_storage_id: [
    { required: true, message: '请选择源端存储', trigger: 'change' }
  ],
  source_path: [
    { required: true, message: '请输入源端路径', trigger: 'blur' }
  ],
  target_storage_id: [
    { required: true, message: '请选择目标存储', trigger: 'change' }
  ],
  target_path: [
    { required: true, message: '请输入目标路径', trigger: 'blur' }
  ]
}

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
  dialogType.value = 'create'
  resetTaskForm()
  taskDialogVisible.value = true
}

const showEditDialog = (task) => {
  dialogType.value = 'edit'
  taskForm.value = {
    ...task,
    source_type: task.source_client_id ? 'client' : 'storage',
    source_client_id: task.source_client_id || '',
    source_storage_id: task.source_storage_id || '',
    source_path: task.source_path || '',
    target_storage_id: task.target_storage_id || '',
    target_path: task.target_path || '',
    options: task.options || {
      delete: false,
      compress: false,
      checksum: true,
      bandwidth_limit: 0,
      max_connections: 1
    }
  }
  taskDialogVisible.value = true
}

const showTaskDetail = (task) => {
  selectedTask.value = task
  detailDialogVisible.value = true
}

const showLogsDialog = (task) => {
  currentTaskId.value = task.id
  logsDialogVisible.value = true
  fetchTaskLogs()
}

const handleDropdownCommand = (command, task) => {
  switch (command) {
    case 'edit':
      showEditDialog(task)
      break
    case 'logs':
      showLogsDialog(task)
      break
    case 'detail':
      showTaskDetail(task)
      break
    case 'delete':
      handleDeleteTask(task)
      break
  }
}

const handleDialogClose = () => {
  taskDialogVisible.value = false
  resetTaskForm()
}

const handleSourceTypeChange = (sourceType) => {
  // 清空相关字段
  taskForm.value.source_client_id = ''
  taskForm.value.source_storage_id = ''
  taskForm.value.node_id = ''
  
  // 根据源端类型调整验证规则
  if (sourceType === 'client') {
    // 客户端模式不需要选择节点
    taskForm.value.node_id = ''
  }
}

const resetTaskForm = () => {
  taskForm.value = {
    name: '',
    description: '',
    type: 'sync',
    priority: 2,
    source_type: 'client',
    source_client_id: '',
    source_storage_id: '',
    source_path: '',
    target_storage_id: '',
    target_path: '',
    node_id: '',
    options: {
      delete: false,
      compress: false,
      checksum: true,
      bandwidth_limit: 0,
      max_connections: 1
    }
  }
}

const handleSubmitTask = async () => {
  if (!taskFormRef.value) return
  
  try {
    await taskFormRef.value.validate()
    submitting.value = true
    
    const formData = { ...taskForm.value }
    
    // 根据源端类型清理不需要的字段
    if (formData.source_type === 'client') {
      delete formData.source_storage_id
    } else if (formData.source_type === 'storage') {
      delete formData.source_client_id
    }
    
    // 清理空字符串，避免外键约束错误
    Object.keys(formData).forEach(key => {
      if (formData[key] === '') {
        if (key.endsWith('_id')) {
          delete formData[key] // 删除空的ID字段
        }
      }
    })
    
    if (dialogType.value === 'create') {
      await axios.post('/api/tasks', formData)
      ElMessage.success('创建任务成功')
    } else {
      await axios.put(`/api/tasks/${formData.id}`, formData)
      ElMessage.success('更新任务成功')
    }
    
    taskDialogVisible.value = false
    fetchTasks()
  } catch (error) {
    if (error.response?.data?.message) {
      ElMessage.error(error.response.data.message)
    } else {
      ElMessage.error('操作失败')
    }
  } finally {
    submitting.value = false
  }
}

const handleTaskAction = async (task) => {
  try {
    if (task.status === 'running') {
      await axios.put(`/api/tasks/${task.id}/cancel`)
      ElMessage.success('取消任务成功')
    } else {
      await axios.post(`/api/tasks/${task.id}/start`)
      ElMessage.success('启动任务成功')
    }
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
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

const handleDeleteTask = async (task) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？', '提示', {
      type: 'warning'
    })
    
    await axios.delete(`/api/tasks/${task.id}`)
    ElMessage.success('删除任务成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
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

const startAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
  refreshInterval.value = setInterval(fetchTasks, 5000)
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

// 工具函数
const getStatusType = (status) => {
  const types = {
    pending: 'info',
    assigned: 'warning',
    running: 'success',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    assigned: '已分配',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
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

const getSourceStorage = () => {
  if (taskForm.value.source_type === 'storage' && taskForm.value.source_storage_id) {
    return storages.value.find(s => s.id === taskForm.value.source_storage_id)
  }
  return null
}

const getTargetStorage = () => {
  if (taskForm.value.target_storage_id) {
    return storages.value.find(s => s.id === taskForm.value.target_storage_id)
  }
  return null
}

const getSourcePathLabel = () => {
  if (taskForm.value.source_type === 'client') {
    return '源端路径'
  }
  const storage = getSourceStorage()
  if (isS3Storage(storage)) {
    return '源端对象路径'
  }
  return '源端存储路径'
}

const getSourcePathPlaceholder = () => {
  if (taskForm.value.source_type === 'client') {
    return '请输入客户端本地路径，如: /home/user/data'
  }
  const storage = getSourceStorage()
  if (isS3Storage(storage)) {
    return '请输入对象路径，如: mybucket/data/source'
  }
  return '请输入存储路径，如: /data/source'
}

const getTargetPathPlaceholder = () => {
  const storage = getTargetStorage()
  if (isS3Storage(storage)) {
    return '请输入对象路径，如: backup-bucket/data/target'
  }
  return '请输入目标存储路径，如: /backup/data'
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
  background-color: #f5f5f5;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-left h1 {
  margin: 0 0 5px 0;
  color: #303133;
  font-size: 24px;
}

.page-description {
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px 20px;
  background: white;
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
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.pagination-container {
  padding: 20px;
  text-align: right;
  border-top: 1px solid #ebeef5;
}

.task-name {
  display: flex;
  flex-direction: column;
}

.task-description {
  color: #909399;
  font-size: 12px;
  margin-top: 2px;
}

.progress-text {
  margin-left: 8px;
  font-size: 12px;
  color: #606266;
}

.text-muted {
  color: #909399;
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
  color: #303133;
}

.task-config pre {
  background: #f5f5f5;
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
  border-bottom: 1px solid #ebeef5;
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
</style>