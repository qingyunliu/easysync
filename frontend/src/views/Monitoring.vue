<template>
  <div class="monitoring-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>系统监控</h1>
        <p class="page-description">实时监控系统状态、性能指标和资源使用情况</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="refreshMonitoring" :loading="loading">
          <el-icon><Refresh /></el-icon>
          刷新数据
        </el-button>
        <el-button @click="openSettings">
          <el-icon><Setting /></el-icon>
          监控设置
        </el-button>
      </div>
    </div>

    <!-- 系统状态概览 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="6">
        <el-card class="status-card cpu">
          <div class="status-content">
            <div class="status-icon">
              <el-icon><Cpu /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.cpu_usage }}%</div>
              <div class="status-label">CPU 使用率</div>
              <div class="status-trend" :class="getCpuTrendClass()">
                <el-icon><ArrowUp v-if="systemStatus.cpu_usage > 70" /><ArrowDown v-else /></el-icon>
                {{ getCpuStatus() }}
              </div>
            </div>
          </div>
          <div class="status-progress">
            <el-progress 
              :percentage="systemStatus.cpu_usage" 
              :color="getProgressColor(systemStatus.cpu_usage)"
              :show-text="false"
            />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="status-card memory">
          <div class="status-content">
            <div class="status-icon">
              <el-icon><Monitor /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.memory_usage }}%</div>
              <div class="status-label">内存使用率</div>
              <div class="status-trend" :class="getMemoryTrendClass()">
                <el-icon><ArrowUp v-if="systemStatus.memory_usage > 80" /><ArrowDown v-else /></el-icon>
                {{ getMemoryStatus() }}
              </div>
            </div>
          </div>
          <div class="status-progress">
            <el-progress 
              :percentage="systemStatus.memory_usage" 
              :color="getProgressColor(systemStatus.memory_usage)"
              :show-text="false"
            />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="status-card disk">
          <div class="status-content">
            <div class="status-icon">
              <el-icon><FolderOpened /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.disk_usage }}%</div>
              <div class="status-label">磁盘使用率</div>
              <div class="status-trend" :class="getDiskTrendClass()">
                <el-icon><ArrowUp v-if="systemStatus.disk_usage > 85" /><ArrowDown v-else /></el-icon>
                {{ getDiskStatus() }}
              </div>
            </div>
          </div>
          <div class="status-progress">
            <el-progress 
              :percentage="systemStatus.disk_usage" 
              :color="getProgressColor(systemStatus.disk_usage)"
              :show-text="false"
            />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="6">
        <el-card class="status-card network">
          <div class="status-content">
            <div class="status-icon">
              <el-icon><Connection /></el-icon>
            </div>
            <div class="status-info">
              <div class="status-value">{{ systemStatus.active_connections }}</div>
              <div class="status-label">活跃连接数</div>
              <div class="status-trend success">
                <el-icon><Check /></el-icon>
                正常
              </div>
            </div>
          </div>
          <div class="network-info">
            <div class="network-item">
              <span>入流量: {{ formatBytes(systemStatus.network_in) }}/s</span>
            </div>
            <div class="network-item">
              <span>出流量: {{ formatBytes(systemStatus.network_out) }}/s</span>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 服务状态 -->
    <el-card class="services-card" style="margin-bottom: 20px;">
      <template #header>
        <div class="card-header">
          <span>服务状态</span>
          <el-tag :type="getOverallServiceStatus().type" size="small">
            {{ getOverallServiceStatus().text }}
          </el-tag>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="8" v-for="(status, service) in systemStatus.services_status" :key="service">
          <div class="service-item">
            <div class="service-icon" :class="status">
              <el-icon>
                <CircleCheckFilled v-if="status === 'healthy'" />
                <CircleCloseFilled v-else />
              </el-icon>
            </div>
            <div class="service-info">
              <div class="service-name">{{ getServiceName(service) }}</div>
              <div class="service-status" :class="status">{{ getServiceStatusText(status) }}</div>
            </div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 监控图表 -->
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>CPU & 内存趋势</span>
              <el-select v-model="timeRange" size="small" style="width: 120px" @change="handleTimeRangeChange">
                <el-option label="1小时" value="1h" />
                <el-option label="6小时" value="6h" />
                <el-option label="24小时" value="24h" />
                <el-option label="7天" value="7d" />
              </el-select>
            </div>
          </template>
          
          <div class="chart-container" ref="cpuMemoryChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="chart-card">
          <template #header>
            <div class="card-header">
              <span>网络流量</span>
              <el-tag size="small" type="info">实时</el-tag>
            </div>
          </template>
          
          <div class="chart-container" ref="networkChart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 告警统计 -->
    <el-card class="alerts-card" style="margin-top: 20px;">
      <template #header>
        <div class="card-header">
          <span>告警统计</span>
          <el-button type="text" @click="$router.push('/monitoring/alerts')">
            查看详情
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
      </template>
      
      <el-row :gutter="20">
        <el-col :span="6">
          <div class="alert-stat-item">
            <div class="alert-stat-number total">{{ alertStats.total_alerts }}</div>
            <div class="alert-stat-label">总告警数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="alert-stat-item">
            <div class="alert-stat-number firing">{{ alertStats.firing_alerts }}</div>
            <div class="alert-stat-label">活跃告警</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="alert-stat-item">
            <div class="alert-stat-number resolved">{{ alertStats.resolved_alerts }}</div>
            <div class="alert-stat-label">已解决</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="alert-stat-item">
            <div class="alert-stat-number critical">{{ getCriticalAlerts() }}</div>
            <div class="alert-stat-label">严重告警</div>
          </div>
        </el-col>
      </el-row>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import {
  Refresh,
  Setting,
  Cpu,
  Monitor,
  FolderOpened,
  Connection,
  Check,
  ArrowUp,
  ArrowDown,
  CircleCheckFilled,
  CircleCloseFilled,
  ArrowRight
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

// 响应式数据
const loading = ref(false)
const timeRange = ref('1h')

const systemStatus = reactive({
  cpu_usage: 0,
  memory_usage: 0,
  disk_usage: 0,
  network_in: 0,
  network_out: 0,
  active_connections: 0,
  services_status: {},
  last_updated: null
})

const alertStats = reactive({
  total_alerts: 0,
  firing_alerts: 0,
  resolved_alerts: 0,
  severity_stats: {}
})

// 图表引用
const cpuMemoryChart = ref(null)
const networkChart = ref(null)
let cpuMemoryChartInstance = null
let networkChartInstance = null

// 数据更新定时器
let updateTimer = null

// 生命周期
onMounted(() => {
  fetchSystemStatus()
  fetchAlertStats()
  initCharts()
  startAutoUpdate()
})

onUnmounted(() => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
  if (cpuMemoryChartInstance) {
    cpuMemoryChartInstance.dispose()
  }
  if (networkChartInstance) {
    networkChartInstance.dispose()
  }
})

// 方法
const fetchSystemStatus = async () => {
  try {
    const response = await axios.get('/api/alerts/system/status')
    Object.assign(systemStatus, response.data)
  } catch (error) {
    console.error('获取系统状态失败:', error)
    ElMessage.error('获取系统状态失败')
  }
}

const fetchAlertStats = async () => {
  try {
    const response = await axios.get('/api/alerts/statistics', {
      params: { range: '24h' }
    })
    Object.assign(alertStats, response.data)
  } catch (error) {
    console.error('获取告警统计失败:', error)
  }
}

const refreshMonitoring = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchSystemStatus(),
      fetchAlertStats()
    ])
    updateCharts()
    ElMessage.success('数据刷新完成')
  } catch (error) {
    ElMessage.error('数据刷新失败')
  } finally {
    loading.value = false
  }
}

const startAutoUpdate = () => {
  updateTimer = setInterval(() => {
    fetchSystemStatus()
    updateCharts()
  }, 30000) // 30秒更新一次
}

const openSettings = () => {
  ElMessage.info('监控设置功能开发中...')
}

const handleTimeRangeChange = () => {
  updateCharts()
}

// 状态判断方法
const getCpuTrendClass = () => {
  return systemStatus.cpu_usage > 80 ? 'danger' : 
         systemStatus.cpu_usage > 60 ? 'warning' : 'success'
}

const getCpuStatus = () => {
  return systemStatus.cpu_usage > 80 ? '过高' : 
         systemStatus.cpu_usage > 60 ? '偏高' : '正常'
}

const getMemoryTrendClass = () => {
  return systemStatus.memory_usage > 85 ? 'danger' : 
         systemStatus.memory_usage > 70 ? 'warning' : 'success'
}

const getMemoryStatus = () => {
  return systemStatus.memory_usage > 85 ? '过高' : 
         systemStatus.memory_usage > 70 ? '偏高' : '正常'
}

const getDiskTrendClass = () => {
  return systemStatus.disk_usage > 90 ? 'danger' : 
         systemStatus.disk_usage > 75 ? 'warning' : 'success'
}

const getDiskStatus = () => {
  return systemStatus.disk_usage > 90 ? '空间不足' : 
         systemStatus.disk_usage > 75 ? '空间紧张' : '正常'
}

const getProgressColor = (value) => {
  if (value > 80) return '#f56c6c'
  if (value > 60) return '#e6a23c'
  return '#67c23a'
}

const getOverallServiceStatus = () => {
  const services = Object.values(systemStatus.services_status)
  const healthyCount = services.filter(status => status === 'healthy').length
  
  if (healthyCount === services.length) {
    return { type: 'success', text: '所有服务正常' }
  } else if (healthyCount > 0) {
    return { type: 'warning', text: '部分服务异常' }
  } else {
    return { type: 'danger', text: '服务异常' }
  }
}

const getServiceName = (service) => {
  const serviceNames = {
    database: '数据库',
    redis: 'Redis',
    queue: '消息队列'
  }
  return serviceNames[service] || service
}

const getServiceStatusText = (status) => {
  return status === 'healthy' ? '正常' : '异常'
}

const getCriticalAlerts = () => {
  return alertStats.severity_stats?.critical || 0
}

const formatBytes = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 图表相关方法
const initCharts = async () => {
  await nextTick()
  initCpuMemoryChart()
  initNetworkChart()
}

const initCpuMemoryChart = () => {
  if (!cpuMemoryChart.value) return
  
  cpuMemoryChartInstance = echarts.init(cpuMemoryChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['CPU', '内存']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: []
    },
    yAxis: {
      type: 'value',
      max: 100,
      axisLabel: {
        formatter: '{value}%'
      }
    },
    series: [
      {
        name: 'CPU',
        type: 'line',
        smooth: true,
        data: []
      },
      {
        name: '内存',
        type: 'line',
        smooth: true,
        data: []
      }
    ]
  }
  
  cpuMemoryChartInstance.setOption(option)
}

const initNetworkChart = () => {
  if (!networkChart.value) return
  
  networkChartInstance = echarts.init(networkChart.value)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      formatter: function (params) {
        let result = params[0].name + '<br/>'
        params.forEach(param => {
          result += param.seriesName + ': ' + formatBytes(param.value) + '/s<br/>'
        })
        return result
      }
    },
    legend: {
      data: ['入流量', '出流量']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: []
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: function (value) {
          return formatBytes(value) + '/s'
        }
      }
    },
    series: [
      {
        name: '入流量',
        type: 'line',
        smooth: true,
        data: []
      },
      {
        name: '出流量',
        type: 'line',
        smooth: true,
        data: []
      }
    ]
  }
  
  networkChartInstance.setOption(option)
}

const updateCharts = () => {
  // 生成模拟数据用于演示
  const now = new Date()
  const timeLabels = []
  const cpuData = []
  const memoryData = []
  const networkInData = []
  const networkOutData = []
  
  for (let i = 23; i >= 0; i--) {
    const time = new Date(now.getTime() - i * 60000) // 每分钟一个点
    timeLabels.push(time.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }))
    
    // 模拟数据，实际应该从API获取
    cpuData.push(Math.random() * 30 + 40)
    memoryData.push(Math.random() * 20 + 60)
    networkInData.push(Math.random() * 1024 * 1024 + 512 * 1024)
    networkOutData.push(Math.random() * 1024 * 1024 + 256 * 1024)
  }
  
  // 更新CPU/内存图表
  if (cpuMemoryChartInstance) {
    cpuMemoryChartInstance.setOption({
      xAxis: { data: timeLabels },
      series: [
        { data: cpuData },
        { data: memoryData }
      ]
    })
  }
  
  // 更新网络图表
  if (networkChartInstance) {
    networkChartInstance.setOption({
      xAxis: { data: timeLabels },
      series: [
        { data: networkInData },
        { data: networkOutData }
      ]
    })
  }
}
</script>

<style scoped>
.monitoring-page {
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
  margin: 0 0 5px 0;
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

/* 状态卡片 */
.status-card {
  border-radius: 12px;
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  overflow: hidden;
}

.status-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.12);
}

.status-content {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 12px;
}

.status-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  color: white;
}

.status-card.cpu .status-icon { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.status-card.memory .status-icon { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.status-card.disk .status-icon { background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); }
.status-card.network .status-icon { background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); }

.status-info {
  flex: 1;
}

.status-value {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-color);
  line-height: 1;
  margin-bottom: 4px;
}

.status-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.status-trend {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.status-trend.success { color: #67c23a; }
.status-trend.warning { color: #e6a23c; }
.status-trend.danger { color: #f56c6c; }

.status-progress {
  margin-top: 8px;
}

.network-info {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.network-item {
  font-size: 12px;
  color: var(--text-secondary);
}

/* 服务状态 */
.services-card {
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
}

.service-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-radius: 8px;
  background: var(--bg-color-page);
  border: 1px solid var(--border-color);
}

.service-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
}

.service-icon.healthy {
  background: #f0f9ff;
  color: #67c23a;
}

.service-icon:not(.healthy) {
  background: #fef2f2;
  color: #f56c6c;
}

.service-name {
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 2px;
}

.service-status {
  font-size: 12px;
  color: var(--text-secondary);
}

.service-status.healthy {
  color: #67c23a;
}

/* 图表卡片 */
.chart-card {
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.chart-container {
  width: 100%;
}

/* 告警统计 */
.alerts-card {
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.alert-stat-item {
  text-align: center;
  padding: 20px;
  border-radius: 8px;
  background: var(--bg-color-page);
}

.alert-stat-number {
  font-size: 28px;
  font-weight: 700;
  line-height: 1;
  margin-bottom: 8px;
}

.alert-stat-number.total { color: #409eff; }
.alert-stat-number.firing { color: #f56c6c; }
.alert-stat-number.resolved { color: #67c23a; }
.alert-stat-number.critical { color: #e6a23c; }

.alert-stat-label {
  font-size: 14px;
  color: var(--text-secondary);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .monitoring-page {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .status-content {
    gap: 12px;
  }
  
  .status-icon {
    width: 40px;
    height: 40px;
    font-size: 18px;
  }
  
  .status-value {
    font-size: 20px;
  }
}
</style>