<template>
  <div class="logs-container">
    <div class="header">
      <h2>日志查看</h2>
      <div class="actions">
        <el-button type="primary" @click="handleExport">导出日志</el-button>
      </div>
    </div>
    
    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="任务">
          <el-select v-model="filterForm.task_id" placeholder="选择任务" clearable>
            <el-option
              v-for="task in tasks"
              :key="task.id"
              :label="task.name"
              :value="task.id"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="状态">
          <el-select v-model="filterForm.status" placeholder="选择状态" clearable>
            <el-option label="成功" value="completed" />
            <el-option label="失败" value="failed" />
            <el-option label="运行中" value="running" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="时间范围">
          <el-date-picker
            v-model="filterForm.date_range"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">搜索</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="logs-card">
      <el-table
        v-loading="loading"
        :data="logs"
        style="width: 100%"
        border
      >
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="task_name" label="任务名称" min-width="150" />
        <el-table-column prop="start_time" label="开始时间" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" label="结束时间" width="180">
          <template #default="scope">
            {{ scope.row.end_time ? formatDateTime(scope.row.end_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="files_processed" label="处理文件数" width="120" />
        <el-table-column prop="bytes_processed" label="处理数据量" width="120">
          <template #default="scope">
            {{ formatBytes(scope.row.bytes_processed) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="showLogDetail(scope.row)"
            >
              详情
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div class="pagination">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper"
          :total="total"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>
    
    <!-- 日志详情对话框 -->
    <el-dialog
      v-model="detailDialogVisible"
      title="日志详情"
      width="70%"
      destroy-on-close
    >
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务名称">{{ currentLog && currentLog.task_name }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentLog && currentLog.status)">
              {{ getStatusText(currentLog && currentLog.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ formatDateTime(currentLog && currentLog.start_time) }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ currentLog && currentLog.end_time ? formatDateTime(currentLog.end_time) : '-' }}</el-descriptions-item>
          <el-descriptions-item label="处理文件数">{{ currentLog && currentLog.files_processed }}</el-descriptions-item>
          <el-descriptions-item label="处理数据量">{{ formatBytes(currentLog && currentLog.bytes_processed) }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="log-detail-section">
          <h3>错误信息</h3>
          <el-input
            :value="currentLog && currentLog.error_message"
            type="textarea"
            :rows="3"
            readonly
          />
        </div>
        
        <div class="log-detail-section">
          <h3>处理文件列表</h3>
          <el-table :data="currentLog && currentLog.processed_files || []" border style="width: 100%">
            <el-table-column prop="path" label="文件路径" min-width="300" />
            <el-table-column prop="size" label="大小" width="120">
              <template #default="scope">
                {{ formatBytes(scope.row.size) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" label="状态" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                  {{ scope.row.status === 'success' ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'

// 状态和数据
const loading = ref(false)
const detailLoading = ref(false)
const logs = ref([])
const tasks = ref([])
const currentLog = ref(null)
const detailDialogVisible = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 筛选表单
const filterForm = reactive({
  task_id: '',
  status: '',
  date_range: []
})

// 获取任务列表
const fetchTasks = async () => {
  try {
    const response = await axios.get('/api/tasks')
    tasks.value = response.data
  } catch (error) {
    ElMessage.error('获取任务列表失败')
  }
}

// 获取日志列表
const fetchLogs = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      per_page: pageSize.value,
      task_id: filterForm.task_id || undefined,
      status: filterForm.status || undefined,
      start_date: filterForm.date_range && filterForm.date_range[0] || undefined,
      end_date: filterForm.date_range && filterForm.date_range[1] || undefined
    }
    
    const response = await axios.get('/api/tasks/logs', { params })
    logs.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('获取日志列表失败')
  } finally {
    loading.value = false
  }
}

// 获取日志详情
const fetchLogDetail = async (logId) => {
  detailLoading.value = true
  try {
    const response = await axios.get(`/api/tasks/logs/${logId}`)
    currentLog.value = response.data
  } catch (error) {
    ElMessage.error('获取日志详情失败')
  } finally {
    detailLoading.value = false
  }
}

// 显示日志详情
const showLogDetail = (log) => {
  currentLog.value = log
  detailDialogVisible.value = true
  fetchLogDetail(log.id)
}

// 导出日志
const handleExport = async () => {
  try {
    const params = {
      task_id: filterForm.task_id || undefined,
      status: filterForm.status || undefined,
      start_date: filterForm.date_range && filterForm.date_range[0] || undefined,
      end_date: filterForm.date_range && filterForm.date_range[1] || undefined
    }
    
    const response = await axios.get('/api/tasks/logs/export', {
      params,
      responseType: 'blob'
    })
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `logs_${new Date().toISOString().split('T')[0]}.csv`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    ElMessage.success('日志导出成功')
  } catch (error) {
    ElMessage.error('日志导出失败')
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
  fetchLogs()
}

// 重置筛选
const resetFilter = () => {
  filterForm.task_id = ''
  filterForm.status = ''
  filterForm.date_range = []
  handleSearch()
}

// 分页处理
const handleSizeChange = (val) => {
  pageSize.value = val
  fetchLogs()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  fetchLogs()
}

// 工具函数
const getStatusType = (status) => {
  switch (status) {
    case 'completed':
      return 'success'
    case 'failed':
      return 'danger'
    case 'running':
      return 'warning'
    default:
      return 'info'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'completed':
      return '成功'
    case 'failed':
      return '失败'
    case 'running':
      return '运行中'
    default:
      return '未知'
  }
}

const formatDateTime = (dateStr) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const formatBytes = (bytes) => {
  if (!bytes) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 生命周期钩子
onMounted(() => {
  fetchTasks()
  fetchLogs()
})
</script>

<style scoped>
.logs-container {
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

.filter-card {
  margin-bottom: 20px;
}

.filter-form {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.logs-card {
  margin-bottom: 20px;
}

.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.log-detail-section {
  margin-top: 20px;
}

.log-detail-section h3 {
  margin-bottom: 10px;
  font-size: 16px;
}
</style> 