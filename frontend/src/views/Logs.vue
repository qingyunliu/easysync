<template>
  <div class="logs-container">
    <div class="header">
      <h2>{{ $t('logs.title') }}</h2>
      <div class="actions">
        <el-button type="primary" @click="handleExport">{{ $t('logs.exportLogs') }}</el-button>
      </div>
    </div>

    <el-card class="filter-card">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item :label="$t('logs.task')">
          <el-select v-model="filterForm.task_id" :placeholder="$t('logs.selectTask')" clearable>
            <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('logs.status')">
          <el-select v-model="filterForm.status" :placeholder="$t('logs.selectStatus')" clearable>
            <el-option :label="$t('logs.success')" value="completed" />
            <el-option :label="$t('logs.failed')" value="failed" />
            <el-option :label="$t('logs.running')" value="running" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('logs.timeRange')">
          <el-date-picker v-model="filterForm.date_range" type="daterange" :range-separator="$t('common.to')"
            :start-placeholder="$t('logs.startDate')" :end-placeholder="$t('logs.endDate')" value-format="YYYY-MM-DD" />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">{{ $t('common.search') }}</el-button>
          <el-button @click="resetFilter">{{ $t('common.reset') }}</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card class="logs-card">
      <el-table v-loading="loading" :data="logs" :empty-text="$t('common.noData')" style="width: 100%">
        <el-table-column prop="id" :label="$t('logs.id')" width="80" />
        <el-table-column prop="task_name" :label="$t('logs.taskName')" min-width="150" />
        <el-table-column prop="start_time" :label="$t('logs.startTime')" width="180">
          <template #default="scope">
            {{ formatDateTime(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="end_time" :label="$t('logs.endTime')" width="180">
          <template #default="scope">
            {{ scope.row.end_time ? formatDateTime(scope.row.end_time) : '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="status" :label="$t('logs.status')" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="files_processed" :label="$t('logs.filesProcessed')" width="120" />
        <el-table-column prop="bytes_processed" :label="$t('logs.bytesProcessed')" width="120">
          <template #default="scope">
            {{ formatBytes(scope.row.bytes_processed) }}
          </template>
        </el-table-column>
        <el-table-column :label="$t('common.actions')" width="120" fixed="right">
          <template #default="scope">
            <el-button type="primary" size="small" @click="showLogDetail(scope.row)">
              {{ $t('logs.details') }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="pagination">
        <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize" :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next, jumper" :total="total" @size-change="handleSizeChange"
          @current-change="handleCurrentChange" />
      </div>
    </el-card>

    <!-- 日志详情对话框 -->
    <el-dialog v-model="detailDialogVisible" :title="$t('logs.logDetail')" width="70%" destroy-on-close>
      <div v-loading="detailLoading">
        <el-descriptions :column="2" border>
          <el-descriptions-item :label="$t('logs.taskName')">{{ currentLog && currentLog.task_name
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('logs.status')">
            <el-tag :type="getStatusType(currentLog && currentLog.status)">
              {{ getStatusText(currentLog && currentLog.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item :label="$t('logs.startTime')">{{ formatDateTime(currentLog && currentLog.start_time)
          }}</el-descriptions-item>
          <el-descriptions-item :label="$t('logs.endTime')">{{ currentLog && currentLog.end_time ?
            formatDateTime(currentLog.end_time)
            :
            '-' }}</el-descriptions-item>
          <el-descriptions-item :label="$t('logs.filesProcessed')">{{ currentLog && currentLog.files_processed
            }}</el-descriptions-item>
          <el-descriptions-item :label="$t('logs.bytesProcessed')">{{ formatBytes(currentLog &&
            currentLog.bytes_processed)
            }}</el-descriptions-item>
        </el-descriptions>

        <div class="log-detail-section">
          <h3>{{ $t('logs.errorMessage') }}</h3>
          <el-input :value="currentLog && currentLog.error_message" type="textarea" :rows="3" readonly />
        </div>

        <div class="log-detail-section">
          <h3>{{ $t('logs.processedFiles') }}</h3>
          <el-table :data="currentLog && currentLog.processed_files || []" border style="width: 100%">
            <el-table-column prop="path" :label="$t('logs.filePath')" min-width="300" />
            <el-table-column prop="size" :label="$t('logs.size')" width="120">
              <template #default="scope">
                {{ formatBytes(scope.row.size) }}
              </template>
            </el-table-column>
            <el-table-column prop="status" :label="$t('logs.fileStatus')" width="100">
              <template #default="scope">
                <el-tag :type="scope.row.status === 'success' ? 'success' : 'danger'">
                  {{ scope.row.status === 'success' ? $t('logs.success') : $t('logs.failed') }}
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
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t } = useI18n()

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
    ElMessage.error(t('logs.getTasksFailed'))
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
    ElMessage.error(t('logs.getLogsFailed'))
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
    ElMessage.error(t('logs.getLogDetailFailed'))
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

    ElMessage.success(t('logs.exportSuccess'))
  } catch (error) {
    ElMessage.error(t('logs.exportFailed'))
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
      return t('logs.success')
    case 'failed':
      return t('logs.failed')
    case 'running':
      return t('logs.running')
    default:
      return t('common.unknown')
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

:deep(.el-table__header) {
  width: 100% !important;
}

:deep(.el-table__header th) {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
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