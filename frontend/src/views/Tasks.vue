<template>
  <div class="tasks-container">
    <div class="header">
      <h2>同步任务</h2>
      <el-button type="primary" @click="showCreateDialog">
        创建任务
      </el-button>
    </div>
    
    <el-table :data="tasks" v-loading="loading">
      <el-table-column prop="name" label="任务名称" />
      <el-table-column prop="source_path" label="源路径" />
      <el-table-column prop="target_path" label="目标路径" />
      <el-table-column prop="schedule" label="定时计划" />
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button-group>
            <el-button
              size="small"
              :type="row.status === 'running' ? 'danger' : 'success'"
              @click="handleTaskAction(row)"
            >
              {{ row.status === 'running' ? '停止' : '启动' }}
            </el-button>
            <el-button
              size="small"
              type="primary"
              @click="showEditDialog(row)"
            >
              编辑
            </el-button>
            <el-button
              size="small"
              type="info"
              @click="showLogsDialog(row)"
            >
              日志
            </el-button>
            <el-button
              size="small"
              type="danger"
              @click="handleDeleteTask(row)"
            >
              删除
            </el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 创建/编辑任务对话框 -->
    <el-dialog
      :title="dialogType === 'create' ? '创建任务' : '编辑任务'"
      v-model="taskDialogVisible"
      width="600px"
    >
      <el-form
        ref="taskForm"
        :model="taskForm"
        :rules="taskRules"
        label-width="100px"
      >
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="taskForm.name" />
        </el-form-item>
        <el-form-item label="源存储" prop="source_storage_id">
          <el-select v-model="taskForm.source_storage_id" placeholder="选择源存储">
            <el-option
              v-for="storage in storages"
              :key="storage.id"
              :label="storage.name"
              :value="storage.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="目标存储" prop="target_storage_id">
          <el-select v-model="taskForm.target_storage_id" placeholder="选择目标存储">
            <el-option
              v-for="storage in storages"
              :key="storage.id"
              :label="storage.name"
              :value="storage.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="源路径" prop="source_path">
          <el-input v-model="taskForm.source_path" />
        </el-form-item>
        <el-form-item label="目标路径" prop="target_path">
          <el-input v-model="taskForm.target_path" />
        </el-form-item>
        <el-form-item label="定时计划" prop="schedule">
          <el-input v-model="taskForm.schedule" placeholder="Cron表达式，例如: */5 * * * *">
            <template #append>
              <el-tooltip content="Cron表达式格式：分 时 日 月 星期">
                <el-icon><QuestionFilled /></el-icon>
              </el-tooltip>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="优先级" prop="priority">
          <el-input-number v-model="taskForm.priority" :min="0" :max="10" />
        </el-form-item>
        <el-form-item label="同步选项" prop="options">
          <el-input
            v-model="taskForm.options"
            type="textarea"
            :rows="4"
            placeholder="JSON格式的同步选项"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitTask">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 任务日志对话框 -->
    <el-dialog
      title="任务日志"
      v-model="logsDialogVisible"
      width="800px"
    >
      <el-table :data="taskLogs" v-loading="logsLoading">
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180">
          <template #default="{ row }">
            {{ row.end_time ? formatDateTime(row.end_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="files_processed" label="处理文件数" />
        <el-table-column prop="bytes_processed" label="处理字节数">
          <template #default="{ row }">
            {{ formatBytes(row.bytes_processed) }}
          </template>
        </el-table-column>
        <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { QuestionFilled } from '@element-plus/icons-vue'

// 状态
const loading = ref(false)
const tasks = ref([])
const storages = ref([])
const taskDialogVisible = ref(false)
const dialogType = ref('create')
const taskForm = ref({
  name: '',
  source_storage_id: '',
  target_storage_id: '',
  source_path: '',
  target_path: '',
  schedule: '',
  priority: 0,
  options: '{}'
})
const taskRules = {
  name: [
    { required: true, message: '请输入任务名称', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  source_storage_id: [
    { required: true, message: '请选择源存储', trigger: 'change' }
  ],
  target_storage_id: [
    { required: true, message: '请选择目标存储', trigger: 'change' }
  ],
  source_path: [
    { required: true, message: '请输入源路径', trigger: 'blur' }
  ],
  target_path: [
    { required: true, message: '请输入目标路径', trigger: 'blur' }
  ]
}

// 日志相关
const logsDialogVisible = ref(false)
const logsLoading = ref(false)
const taskLogs = ref([])
const currentTaskId = ref(null)

// 获取任务列表
const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/tasks')
    if (response.data.status === 'success') { 
      tasks.value = response.data.tasks
    }
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  } finally {
    loading.value = false
  }
}

// 获取存储列表
const fetchStorages = async () => {
  try {
    const response = await axios.get('/api/storages')
    storages.value = response.data
  } catch (error) {
    ElMessage.error('获取存储列表失败')
  }
}

// 显示创建对话框
const showCreateDialog = () => {
  dialogType.value = 'create'
  taskForm.value = {
    name: '',
    source_storage_id: '',
    target_storage_id: '',
    source_path: '',
    target_path: '',
    schedule: '',
    priority: 0,
    options: '{}'
  }
  taskDialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (task) => {
  dialogType.value = 'edit'
  taskForm.value = {
    ...task,
    options: typeof task.options === 'string' ? task.options : JSON.stringify(task.options)
  }
  taskDialogVisible.value = true
}

// 提交任务表单
const handleSubmitTask = async () => {
  try {
    const formData = {
      ...taskForm.value,
      options: JSON.parse(taskForm.value.options)
    }
    
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
    ElMessage.error(error.response && error.response.data && error.response.data.error || '操作失败')
  }
}

// 处理任务操作（启动/停止）
const handleTaskAction = async (task) => {
  try {
    if (task.status === 'running') {
      await axios.post(`/api/tasks/${task.id}/stop`)
      ElMessage.success('停止任务成功')
    } else {
      await axios.post(`/api/tasks/${task.id}/start`)
      ElMessage.success('启动任务成功')
    }
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response && error.response.data && error.response.data.error || '操作失败')
  }
}

// 删除任务
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
      ElMessage.error(error.response && error.response.data && error.response.data.error || '删除失败')
    }
  }
}

// 显示任务日志
const showLogsDialog = async (task) => {
  currentTaskId.value = task.id
  logsDialogVisible.value = true
  logsLoading.value = true
  
  try {
    const response = await axios.get(`/api/tasks/${task.id}/logs`)
    taskLogs.value = response.data
  } catch (error) {
    ElMessage.error('获取任务日志失败')
  } finally {
    logsLoading.value = false
  }
}

// 工具函数
const getStatusType = (status) => {
  const types = {
    running: 'success',
    stopped: 'info',
    error: 'danger'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    running: '运行中',
    stopped: '已停止',
    error: '错误'
  }
  return texts[status] || status
}

const formatDateTime = (datetime) => {
  return new Date(datetime).toLocaleString()
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 生命周期钩子
onMounted(() => {
  fetchTasks()
  fetchStorages()
})
</script>

<style scoped>
.tasks-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header h2 {
  margin: 0;
}
</style> 