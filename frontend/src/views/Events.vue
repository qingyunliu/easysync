<template>
  <div class="events-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>事件管理</h1>
        <p class="page-description">查看和管理系统事件，监控告警触发情况</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="refreshEvents" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="exportEvents">
          <el-icon><Download /></el-icon>
          导出数据
        </el-button>
        <el-button @click="cleanupEvents">
          <el-icon><Delete /></el-icon>
          清理旧事件
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon><DataAnalysis /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ statistics.total_events || 0 }}</div>
              <div class="stats-label">总事件数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon><Warning /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ statistics.failed_events || 0 }}</div>
              <div class="stats-label">失败事件</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon><Bell /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ alertStatistics.total_alerts || 0 }}</div>
              <div class="stats-label">告警数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="stats-card">
          <div class="stats-content">
            <div class="stats-icon">
              <el-icon><TrendCharts /></el-icon>
            </div>
            <div class="stats-info">
              <div class="stats-value">{{ statistics.today_events || 0 }}</div>
              <div class="stats-label">今日事件</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 筛选和搜索 -->
    <el-card class="filter-card">
      <div class="filter-content">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-select 
              v-model="filters.event_type" 
              placeholder="选择事件类型" 
              clearable
              @change="handleFilterChange"
            >
              <el-option label="全部类型" value="" />
              <el-option label="存储事件" value="storage" />
              <el-option label="客户端事件" value="client" />
              <el-option label="代理事件" value="agent" />
              <el-option label="系统事件" value="system" />
            </el-select>
          </el-col>
          
          <el-col :span="6">
            <el-select 
              v-model="filters.event_action" 
              placeholder="选择事件动作" 
              clearable
              @change="handleFilterChange"
            >
              <el-option label="全部动作" value="" />
              <el-option label="创建" value="create" />
              <el-option label="更新" value="update" />
              <el-option label="删除" value="delete" />
              <el-option label="连接" value="connect" />
              <el-option label="断开" value="disconnect" />
            </el-select>
          </el-col>
          
          <el-col :span="6">
            <el-select 
              v-model="filters.event_result" 
              placeholder="选择事件结果" 
              clearable
              @change="handleFilterChange"
            >
              <el-option label="全部结果" value="" />
              <el-option label="成功" value="success" />
              <el-option label="失败" value="failed" />
              <el-option label="超时" value="timeout" />
              <el-option label="错误" value="error" />
              <el-option label="警告" value="warning" />
            </el-select>
          </el-col>
          
          <el-col :span="6">
            <el-date-picker
              v-model="filters.time_range"
              type="datetimerange"
              range-separator="至"
              start-placeholder="开始时间"
              end-placeholder="结束时间"
              format="YYYY-MM-DD HH:mm:ss"
              value-format="YYYY-MM-DD HH:mm:ss"
              @change="handleFilterChange"
            />
          </el-col>
        </el-row>
        
        <div class="filter-actions">
          <el-button @click="resetFilters">重置筛选</el-button>
          <el-button type="primary" @click="loadEvents">应用筛选</el-button>
        </div>
      </div>
    </el-card>

    <!-- 事件列表 -->
    <el-card class="events-card">
      <div class="card-header">
        <div class="card-title">
          <el-icon class="title-icon"><List /></el-icon>
          <span>事件列表</span>
        </div>
        <div class="card-stats">
          <span class="stats-text">共 {{ pagination.total }} 条记录</span>
        </div>
      </div>

      <div class="table-container">
        <el-table 
          :data="events" 
          class="events-table"
          :header-cell-style="{ background: 'var(--table-header-bg)', color: 'var(--text-color)' }"
          stripe
          v-loading="loading"
        >
          <el-table-column prop="id" label="事件ID" width="280" align="center">
            <template #default="scope">
              <el-tooltip :content="scope.row.id" placement="top">
                <span class="event-id">{{ scope.row.id.substring(0, 8) }}...</span>
              </el-tooltip>
            </template>
          </el-table-column>
          
          <el-table-column prop="event_type" label="事件类型" width="120" align="center">
            <template #default="scope">
              <el-tag 
                :type="getEventTypeColor(scope.row.event_type)"
                effect="light"
                size="small"
              >
                {{ getEventTypeLabel(scope.row.event_type) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="event_action" label="事件动作" width="120" align="center">
            <template #default="scope">
              <el-tag 
                :type="getEventActionColor(scope.row.event_action)"
                effect="light"
                size="small"
              >
                {{ getEventActionLabel(scope.row.event_action) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="event_result" label="事件结果" width="100" align="center">
            <template #default="scope">
              <el-tag 
                :type="getEventResultColor(scope.row.event_result)"
                effect="light"
                size="small"
              >
                {{ getEventResultLabel(scope.row.event_result) }}
              </el-tag>
            </template>
          </el-table-column>
          
          <el-table-column prop="message" label="事件消息" min-width="200">
            <template #default="scope">
              <div class="event-message">
                <el-tooltip :content="scope.row.message" placement="top">
                  <span>{{ scope.row.message }}</span>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="时间" width="180" align="center">
            <template #default="scope">
              <div class="time-info">
                <el-icon class="time-icon"><Clock /></el-icon>
                <span>{{ formatTime(scope.row.timestamp) }}</span>
              </div>
            </template>
          </el-table-column>
          
          <el-table-column label="操作" width="120" align="center">
            <template #default="scope">
              <el-button 
                type="primary" 
                size="small" 
                @click="viewEventDetail(scope.row)"
              >
                详情
              </el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.current_page"
          v-model:page-size="pagination.per_page"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
        />
      </div>
    </el-card>

    <!-- 事件详情对话框 -->
    <el-dialog
      v-model="eventDetailVisible"
      title="事件详情"
      width="800px"
      :before-close="handleCloseEventDetail"
    >
      <div v-if="selectedEvent" class="event-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="事件ID">{{ selectedEvent.id }}</el-descriptions-item>
          <el-descriptions-item label="事件类型">
            <el-tag :type="getEventTypeColor(selectedEvent.event_type)">
              {{ getEventTypeLabel(selectedEvent.event_type) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="事件动作">
            <el-tag :type="getEventActionColor(selectedEvent.event_action)">
              {{ getEventActionLabel(selectedEvent.event_action) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="事件结果">
            <el-tag :type="getEventResultColor(selectedEvent.event_result)">
              {{ getEventResultLabel(selectedEvent.event_result) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="用户ID">{{ selectedEvent.user_id }}</el-descriptions-item>
          <el-descriptions-item label="客户端ID">{{ selectedEvent.client_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="节点ID">{{ selectedEvent.node_id || '-' }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ formatTime(selectedEvent.created_at) }}</el-descriptions-item>
          <el-descriptions-item label="事件时间" :span="2">{{ formatTime(selectedEvent.timestamp) }}</el-descriptions-item>
          <el-descriptions-item label="事件消息" :span="2">{{ selectedEvent.message }}</el-descriptions-item>
        </el-descriptions>
        
        <div class="event-details-section">
          <h4>详细信息</h4>
          <el-card class="details-card">
            <pre>{{ JSON.stringify(selectedEvent.details, null, 2) }}</pre>
          </el-card>
        </div>
      </div>
    </el-dialog>

    <!-- 清理事件对话框 -->
    <el-dialog
      v-model="cleanupDialogVisible"
      title="清理旧事件"
      width="500px"
    >
      <div class="cleanup-form">
        <el-form :model="cleanupForm" label-width="120px">
          <el-form-item label="保留天数">
            <el-input-number 
              v-model="cleanupForm.days" 
              :min="1" 
              :max="365"
              placeholder="请输入保留天数"
            />
            <div class="form-tip">将删除指定天数之前的事件记录</div>
          </el-form-item>
        </el-form>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="cleanupDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmCleanup" :loading="cleanupLoading">
            确认清理
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Refresh, 
  Download, 
  Delete, 
  DataAnalysis, 
  Warning, 
  Bell, 
  TrendCharts,
  List,
  Clock
} from '@element-plus/icons-vue'
import axios from 'axios'

export default {
  name: 'Events',
  components: {
    Refresh,
    Download,
    Delete,
    DataAnalysis,
    Warning,
    Bell,
    TrendCharts,
    List,
    Clock
  },
  setup() {
    // 响应式数据
    const loading = ref(false)
    const events = ref([])
    const statistics = ref({})
    const alertStatistics = ref({})
    const eventDetailVisible = ref(false)
    const selectedEvent = ref(null)
    const cleanupDialogVisible = ref(false)
    const cleanupLoading = ref(false)
    
    const filters = reactive({
      event_type: '',
      event_action: '',
      event_result: '',
      time_range: []
    })
    
    const pagination = reactive({
      current_page: 1,
      per_page: 20,
      total: 0
    })
    
    const cleanupForm = reactive({
      days: 30
    })

    // 获取事件列表
    const loadEvents = async () => {
      loading.value = true
      try {
        const params = {
          page: pagination.current_page,
          per_page: pagination.per_page,
          ...filters
        }
        
        if (filters.time_range && filters.time_range.length === 2) {
          params.start_time = filters.time_range[0]
          params.end_time = filters.time_range[1]
        }
        
        const response = await axios.get('/api/events/', { params })
        if (response.data.status === 'success') {
          events.value = response.data.data.events
          pagination.total = response.data.data.total
          pagination.current_page = response.data.data.current_page
          pagination.per_page = response.data.data.per_page
        }
      } catch (error) {
        ElMessage.error('获取事件列表失败')
        console.error('Error loading events:', error)
      } finally {
        loading.value = false
      }
    }

    // 获取事件统计
    const loadStatistics = async () => {
      try {
        const response = await axios.get('/api/events/statistics')
        if (response.data.status === 'success') {
          statistics.value = response.data.data
        }
      } catch (error) {
        console.error('Error loading statistics:', error)
      }
    }

    // 获取告警统计
    const loadAlertStatistics = async () => {
      try {
        const response = await axios.get('/api/events/alert-statistics')
        if (response.data.status === 'success') {
          alertStatistics.value = response.data.data
        }
      } catch (error) {
        console.error('Error loading alert statistics:', error)
      }
    }

    // 刷新事件
    const refreshEvents = () => {
      loadEvents()
      loadStatistics()
      loadAlertStatistics()
    }

    // 筛选变化处理
    const handleFilterChange = () => {
      pagination.current_page = 1
      loadEvents()
    }

    // 重置筛选
    const resetFilters = () => {
      Object.keys(filters).forEach(key => {
        if (Array.isArray(filters[key])) {
          filters[key] = []
        } else {
          filters[key] = ''
        }
      })
      pagination.current_page = 1
      loadEvents()
    }

    // 分页处理
    const handleSizeChange = (size) => {
      pagination.per_page = size
      pagination.current_page = 1
      loadEvents()
    }

    const handleCurrentChange = (page) => {
      pagination.current_page = page
      loadEvents()
    }

    // 查看事件详情
    const viewEventDetail = (event) => {
      selectedEvent.value = event
      eventDetailVisible.value = true
    }

    // 关闭事件详情
    const handleCloseEventDetail = () => {
      eventDetailVisible.value = false
      selectedEvent.value = null
    }

    // 导出事件
    const exportEvents = async () => {
      try {
        const params = { ...filters }
        if (filters.time_range && filters.time_range.length === 2) {
          params.start_time = filters.time_range[0]
          params.end_time = filters.time_range[1]
        }
        
        const response = await axios.get('/api/events/export', { 
          params,
          responseType: 'blob'
        })
        
        const url = window.URL.createObjectURL(new Blob([response.data]))
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', `events_${new Date().toISOString().slice(0, 10)}.csv`)
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)
        
        ElMessage.success('事件数据导出成功')
      } catch (error) {
        ElMessage.error('导出失败')
        console.error('Error exporting events:', error)
      }
    }

    // 清理事件
    const cleanupEvents = () => {
      cleanupDialogVisible.value = true
    }

    // 确认清理
    const confirmCleanup = async () => {
      cleanupLoading.value = true
      try {
        const response = await axios.post('/api/events/cleanup', cleanupForm)
        if (response.data.status === 'success') {
          ElMessage.success(`成功清理 ${response.data.data.deleted_count} 条旧事件记录`)
          cleanupDialogVisible.value = false
          loadEvents()
          loadStatistics()
        }
      } catch (error) {
        ElMessage.error('清理失败')
        console.error('Error cleaning up events:', error)
      } finally {
        cleanupLoading.value = false
      }
    }

    // 工具函数
    const formatTime = (timeStr) => {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString('zh-CN')
    }

    const getEventTypeColor = (type) => {
      const colors = {
        storage: 'primary',
        client: 'success',
        agent: 'warning',
        system: 'info'
      }
      return colors[type] || 'info'
    }

    const getEventTypeLabel = (type) => {
      const labels = {
        storage: '存储',
        client: '客户端',
        agent: '代理',
        system: '系统'
      }
      return labels[type] || type
    }

    const getEventActionColor = (action) => {
      const colors = {
        create: 'success',
        update: 'primary',
        delete: 'danger',
        connect: 'success',
        disconnect: 'warning',
        test_connection: 'info'
      }
      return colors[action] || 'info'
    }

    const getEventActionLabel = (action) => {
      const labels = {
        create: '创建',
        update: '更新',
        delete: '删除',
        connect: '连接',
        disconnect: '断开',
        test_connection: '测试连接',
        list_buckets: '获取存储桶',
        list_objects: '获取对象',
        list_files: '获取文件',
        download: '下载',
        mount_check: '检查挂载'
      }
      return labels[action] || action
    }

    const getEventResultColor = (result) => {
      const colors = {
        success: 'success',
        failed: 'danger',
        timeout: 'warning',
        error: 'danger',
        warning: 'warning'
      }
      return colors[result] || 'info'
    }

    const getEventResultLabel = (result) => {
      const labels = {
        success: '成功',
        failed: '失败',
        timeout: '超时',
        error: '错误',
        warning: '警告'
      }
      return labels[result] || result
    }

    // 初始化
    onMounted(() => {
      loadEvents()
      loadStatistics()
      loadAlertStatistics()
    })

    return {
      loading,
      events,
      statistics,
      alertStatistics,
      filters,
      pagination,
      eventDetailVisible,
      selectedEvent,
      cleanupDialogVisible,
      cleanupLoading,
      cleanupForm,
      loadEvents,
      loadStatistics,
      loadAlertStatistics,
      refreshEvents,
      handleFilterChange,
      resetFilters,
      handleSizeChange,
      handleCurrentChange,
      viewEventDetail,
      handleCloseEventDetail,
      exportEvents,
      cleanupEvents,
      confirmCleanup,
      formatTime,
      getEventTypeColor,
      getEventTypeLabel,
      getEventActionColor,
      getEventActionLabel,
      getEventResultColor,
      getEventResultLabel
    }
  }
}
</script>

<style scoped>
.events-page {
  padding: 20px;
  background: var(--bg-color);
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  color: var(--text-color);
  font-size: 24px;
  font-weight: 600;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.stats-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
  border-radius: 8px;
}

.stats-content {
  display: flex;
  align-items: center;
  padding: 16px;
}

.stats-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 16px;
  background: var(--primary-color);
  color: white;
  font-size: 24px;
}

.stats-info {
  flex: 1;
}

.stats-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 4px;
}

.stats-label {
  font-size: 14px;
  color: var(--text-secondary);
}

.filter-card {
  margin-bottom: 20px;
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}

.filter-content {
  padding: 20px;
}

.filter-actions {
  margin-top: 16px;
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.events-card {
  background: var(--card-bg);
  border: 1px solid var(--border-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--border-color);
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.title-icon {
  margin-right: 8px;
  color: var(--primary-color);
}

.card-stats {
  color: var(--text-secondary);
  font-size: 14px;
}

.table-container {
  padding: 0 20px 20px;
}

.events-table {
  width: 100%;
}

.event-id {
  font-family: monospace;
  color: var(--text-secondary);
}

.event-message {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.time-info {
  display: flex;
  align-items: center;
  gap: 4px;
  color: var(--text-secondary);
  font-size: 12px;
}

.time-icon {
  font-size: 14px;
}

.pagination-container {
  display: flex;
  justify-content: center;
  padding: 20px;
  border-top: 1px solid var(--border-color);
}

.event-detail {
  max-height: 600px;
  overflow-y: auto;
}

.event-details-section {
  margin-top: 20px;
}

.event-details-section h4 {
  margin: 0 0 12px 0;
  color: var(--text-color);
  font-size: 16px;
  font-weight: 600;
}

.details-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
}

.details-card pre {
  margin: 0;
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 4px;
  font-size: 12px;
  color: var(--text-color);
  white-space: pre-wrap;
  word-break: break-all;
}

.cleanup-form {
  padding: 20px 0;
}

.form-tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    gap: 16px;
  }
  
  .header-right {
    width: 100%;
    justify-content: flex-start;
  }
  
  .filter-content .el-row {
    margin: 0;
  }
  
  .filter-content .el-col {
    margin-bottom: 12px;
  }
}
</style> 