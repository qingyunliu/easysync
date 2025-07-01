<template>
  <div class="clients-container">
    <div class="header">
      <h2>服务器管理</h2>
      <el-button type="primary" @click="showAddDialog">添加服务器</el-button>
    </div>

    <el-table :data="clients" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="名称">
        <template #default="{ row }">
          <el-link 
            type="primary" 
            @click="handleNameClick(row)"
            :class="{ 'details-link': row.status !== 'online' }"
          >
            {{ row.name }}
          </el-link>
        </template>
      </el-table-column>
      <el-table-column prop="hostname" label="主机名" />
      <el-table-column prop="ip_address" label="IP地址" />
      <el-table-column prop="status" label="状态">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="agent_status" label="Agent状态">
        <template #default="{ row }">
          <el-tag :type="getAgentStatusType(row.agent_status)">
            {{ getAgentStatusText(row.agent_status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="os_type" label="操作系统" />
      <el-table-column prop="last_seen" label="最后在线时间">
        <template #default="{ row }">
          {{ formatDate(row.last_seen) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="300">
        <template #default="{ row }">
          <el-button-group>
            <el-button type="primary" size="small" @click="showEditDialog(row)">
              <el-icon><Edit /></el-icon>编辑
            </el-button>
            <el-button type="danger" size="small" @click="handleDelete(row)">
              <el-icon><Delete /></el-icon>删除
            </el-button>
            <el-dropdown trigger="click">
              <el-button type="primary" size="small">
                更多<el-icon class="el-icon--right"><arrow-down /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item @click="testConnection(row)">
                    <el-button type="text" :loading="row.testing">
                      <el-icon><Connection /></el-icon>测试连接
                    </el-button>
                  </el-dropdown-item>
                  <el-dropdown-item @click="installAgent(row)">
                    <el-button 
                      type="text" 
                      :disabled="row.status !== 'online' || row.agent_status === 'installed' || row.agent_status === 'running'"
                    >
                      <el-icon><Download /></el-icon>安装Agent
                    </el-button>
                  </el-dropdown-item>
                  <el-dropdown-item @click="uninstallAgent(row)">
                    <el-button 
                      type="text" 
                      :disabled="row.agent_status == 'not_installed' || row.agent_status == 'installing'"
                    >
                      <el-icon><Remove /></el-icon>卸载Agent
                    </el-button>
                  </el-dropdown-item>
                  <el-dropdown-item @click="getClientInfo(row)">
                    <el-button type="text" :loading="row.fetching">
                      <el-icon><InfoFilled /></el-icon>获取信息
                    </el-button>
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      :title="dialogType === 'add' ? '添加服务器' : '编辑服务器'"
      v-model="dialogVisible"
      width="500px"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
      >
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入服务器名称" />
        </el-form-item>
        <el-form-item label="主机名" prop="hostname">
          <el-input v-model="form.hostname" placeholder="请输入服务器名称" />
        </el-form-item>
        <el-form-item label="IP地址" prop="ip_address">
          <el-input v-model="form.ip_address" placeholder="请输入服务器地址" />
        </el-form-item>
        <el-form-item label="SSH端口" prop="port">
          <el-input-number v-model="form.port" :min="1" :max="65535" />
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="认证方式" prop="auth_type">
          <el-radio-group v-model="form.auth_type">
            <el-radio :value="'password'">密码认证</el-radio>
            <el-radio :value="'key'">密钥认证</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item
          v-if="form.auth_type === 'password'"
          label="密码"
          prop="password"
        >
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
          />
        </el-form-item>
        <el-form-item
          v-if="form.auth_type === 'key'"
          label="SSH密钥"
          prop="ssh_key"
        >
          <el-input
            v-model="form.ssh_key"
            type="textarea"
            :rows="4"
            placeholder="请输入SSH密钥"
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="2"
            placeholder="请输入备注信息"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 安装Agent对话框 -->
    <el-dialog
      title="安装Agent"
      v-model="installDialogVisible"
      width="500px"
    >
      <el-form :model="installForm" label-width="120px">
        <el-form-item label="安装路径">
          <el-input v-model="installForm.install_path" placeholder="/opt/easysync" />
        </el-form-item>
        <el-form-item label="配置参数">
          <el-input
            v-model="installForm.config"
            type="textarea"
            :rows="4"
            placeholder="请输入JSON格式的配置参数"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="installDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmInstall">开始安装</el-button>
        </span>
      </template>
    </el-dialog>

    <!-- 主机详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="主机详情"
      direction="rtl"
      size="60%"
      :before-close="handleDrawerClose"
    >
      <el-tabs v-model="activeTab" class="fixed-tabs">
        <!-- 基本信息标签页 -->
        <el-tab-pane label="基本信息" name="basic">
          <div class="detail-content scrollable-content">
            <!-- 基本信息卡片 -->
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span>基本信息</span>
                </div>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="主机名称">
                  <el-tag type="info">{{ currentClient.name }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="主机名">
                  <el-tag type="info">{{ currentClient.hostname }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="IP地址">
                  <el-tag type="success">{{ currentClient.ip_address }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="操作系统">
                  <el-tag type="warning">{{ clientDetail.os_type }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- CPU信息卡片 -->
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span>CPU信息</span>
                </div>
              </template>
              <div class="cpu-info">
                <div v-for="(cpu, index) in clientDetail.cpu_info" :key="index" class="cpu-item">
                  <el-tag type="primary">{{ cpu.model }}</el-tag>
                  <span class="cpu-cores">{{ cpu.cores }}核</span>
                </div>
              </div>
            </el-card>

            <!-- 内存信息卡片 -->
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span>内存信息</span>
                </div>
              </template>
              <div class="memory-info">
                <el-progress 
                  :percentage="(clientDetail.memory_info.used / clientDetail.memory_info.total * 100).toFixed(1)"
                  :status="getUsageStatus((clientDetail.memory_info.used / clientDetail.memory_info.total * 100))"
                />
                <div class="memory-details">
                  <span>总内存: {{ formatSize(clientDetail.memory_info.total) }}</span>
                  <span>已使用: {{ formatSize(clientDetail.memory_info.used) }}</span>
                  <span>可用: {{ formatSize(clientDetail.memory_info.total - clientDetail.memory_info.used) }}</span>
                </div>
              </div>
            </el-card>

            <!-- 磁盘信息卡片 -->
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span>磁盘信息</span>
                </div>
              </template>
              <div class="disk-info">
                <div v-for="(disk, index) in clientDetail.disk_info" :key="index" class="disk-item">
                  <div class="disk-header">
                    <el-tag type="info">{{ disk.device }}</el-tag>
                    <span class="disk-mount">{{ disk.mount }}</span>
                  </div>
                  <el-progress 
                    :percentage="disk.usage"
                    :status="getUsageStatus(disk.usage)"
                  />
                  <div class="disk-details">
                    <span>总容量: {{ formatSize(disk.total) }}</span>
                    <span>已使用: {{ formatSize(disk.used) }}</span>
                    <span>可用: {{ formatSize(disk.total - disk.used) }}</span>
                  </div>
                </div>
              </div>
            </el-card>

            <!-- 网卡信息卡片 -->
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span>网卡信息</span>
                </div>
              </template>
              <div class="network-info">
                <div v-for="(nic, index) in clientDetail.network_info" :key="index" class="nic-item">
                  <el-tag type="success">{{ nic.name }}</el-tag>
                  <span class="nic-ip">{{ nic.ip }}</span>
                  <span class="nic-ip6">{{ nic.ip6 }}</span>
                  <span class="nic-mac">{{ nic.mac }}</span>
                  <span class="nic-mtu">{{ nic.mtu }}</span>
                  <span class="nic-status">{{ nic.status }}</span>
                </div>
              </div>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 监控数据标签页 -->
        <el-tab-pane label="监控数据" name="monitor">
          <div class="monitor-content scrollable-content">
            <!-- 监控控制面板 -->
            <div class="monitor-control-panel">
              <div class="panel-section time-range-selector">
                <span class="section-label">时间范围</span>
                <el-select 
                  v-model="timeRange" 
                  placeholder="选择时间范围" 
                  @change="handleTimeRangeChange"
                  size="default"
                  class="time-select"
                >
                  <el-option label="近10分钟" value="10m" />
                  <el-option label="近15分钟" value="15m" />
                  <el-option label="近1小时" value="1h" />
                  <el-option label="近2小时" value="2h" />
                  <el-option label="自定义" value="custom" />
                </el-select>
                <el-date-picker
                  v-if="timeRange === 'custom'"
                  v-model="customTimeRange"
                  type="datetimerange"
                  range-separator="至"
                  start-placeholder="开始时间"
                  end-placeholder="结束时间"
                  size="default"
                  class="date-picker"
                  :default-time="[
                    new Date(2000, 1, 1, 0, 0, 0),
                    new Date(2000, 1, 1, 23, 59, 59),
                  ]"
                  @change="handleCustomTimeRangeChange"
                />
              </div>
              <div class="panel-section refresh-controls">
                <span class="section-label">刷新设置</span>
                <div class="refresh-group">
                  <el-button 
                    type="primary" 
                    :loading="refreshing" 
                    @click="handleManualRefresh"
                    size="default"
                    class="refresh-button"
                  >
                    <el-icon><Refresh /></el-icon>
                    <span>刷新</span>
                  </el-button>
                  <div class="auto-refresh-control">
                    <el-switch
                      v-model="autoRefresh"
                      active-text="自动刷新"
                      inactive-text=""
                      class="refresh-switch"
                      @change="handleAutoRefreshChange"
                    />
                    <el-select
                      v-if="autoRefresh"
                      v-model="refreshInterval"
                      placeholder="刷新间隔"
                      @change="handleRefreshIntervalChange"
                      size="default"
                      class="interval-select"
                    >
                      <el-option label="3秒" value="3" />
                      <el-option label="5秒" value="5" />
                      <el-option label="10秒" value="10" />
                      <el-option label="30秒" value="30" />
                      <el-option label="1分钟" value="60" />
                      <el-option label="5分钟" value="300" />
                    </el-select>
                  </div>
                </div>
              </div>
            </div>

            <!-- CPU使用率图表 -->
            <div class="chart-container">
              <div class="chart-header">
                <h3>CPU使用率</h3>
              </div>
              <div class="chart" ref="cpuChart"></div>
            </div>

            <!-- 内存使用率图表 -->
            <div class="chart-container">
              <div class="chart-header">
                <h3>内存使用率</h3>
              </div>
              <div class="chart" ref="memoryChart"></div>
            </div>

            <!-- 磁盘使用率 -->
            <div class="chart-container">
              <div class="chart-header">
                <h3>磁盘使用率</h3>
              </div>
              <el-table :data="clientDetail.disk_info" style="width: 100%">
                <el-table-column prop="device" label="设备" />
                <el-table-column prop="mount" label="挂载点" />
                <el-table-column prop="total" label="总容量">
                  <template #default="{ row }">
                    {{ formatSize(row.total) }}
                  </template>
                </el-table-column>
                <el-table-column prop="used" label="已使用">
                  <template #default="{ row }">
                    {{ formatSize(row.used) }}
                  </template>
                </el-table-column>
                <el-table-column prop="usage" label="使用率">
                  <template #default="{ row }">
                    <el-progress :percentage="row.usage" :status="getUsageStatus(row.usage)" />
                  </template>
                </el-table-column>
              </el-table>
            </div>

            <!-- 网络流量 -->
            <div class="chart-container">
              <div class="chart-header">
                <h3>网络流量</h3>
              </div>
              <div class="chart" ref="networkChart"></div>
            </div>

            <!-- 进程列表 -->
            <div class="chart-container">
              <div class="chart-header">
                <h3>进程列表</h3>
                <el-button type="primary" size="small" @click="refreshProcessList">刷新</el-button>
              </div>
              <el-table :data="clientDetail.process_list" style="width: 100%" :max-height="300">
                <el-table-column prop="pid" label="PID" width="80" />
                <el-table-column prop="user" label="用户" width="100" />
                <el-table-column prop="cpu_percent" label="CPU%" width="100" />
                <el-table-column prop="memory_percent" label="内存%" width="100" />
                <el-table-column prop="command" label="命令" show-overflow-tooltip />
              </el-table>
            </div>
          </div>
        </el-tab-pane>

        <!-- 系统日志标签页 -->
        <el-tab-pane label="系统日志" name="logs">
          <div class="logs-content scrollable-content">
            <!-- 日志控制面板 -->
            <div class="logs-control-panel">
              <div class="panel-section search-controls">
                <el-input
                  v-model="logSearchQuery"
                  placeholder="搜索日志"
                  clearable
                  @clear="handleLogSearch"
                  @input="handleLogSearch"
                  class="search-input"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <el-select
                  v-model="logLevelFilter"
                  placeholder="日志级别"
                  clearable
                  @change="handleLogSearch"
                  class="level-select"
                >
                  <el-option label="全部" value="" />
                  <el-option label="DEBUG" value="DEBUG" />
                  <el-option label="INFO" value="INFO" />
                  <el-option label="WARNING" value="WARNING" />
                  <el-option label="ERROR" value="ERROR" />
                  <el-option label="CRITICAL" value="CRITICAL" />
                </el-select>
                <el-button
                  type="primary"
                  :loading="refreshingLogs"
                  @click="handleManualLogRefresh"
                  class="refresh-button"
                >
                  <el-icon><Refresh /></el-icon>
                  <span>刷新</span>
                </el-button>
                <el-switch
                  v-model="autoRefreshLogs"
                  active-text="自动刷新"
                  inactive-text=""
                  class="refresh-switch"
                  @change="handleAutoLogRefreshChange"
                />
                <el-select
                  v-if="autoRefreshLogs"
                  v-model="logRefreshInterval"
                  placeholder="刷新间隔"
                  @change="handleLogRefreshIntervalChange"
                  class="interval-select"
                >
                  <el-option label="3秒" value="3" />
                  <el-option label="5秒" value="5" />
                  <el-option label="10秒" value="10" />
                  <el-option label="30秒" value="30" />
                </el-select>
              </div>
            </div>

            <!-- 日志列表 -->
            <div class="logs-list">
              <el-table
                :data="filteredLogs"
                style="width: 100%"
                height="calc(100vh - 300px)"
                v-loading="loadingLogs"
              >
                <el-table-column prop="timestamp" label="时间" width="180">
                  <template #default="{ row }">
                    {{ row.timestamp }}
                  </template>
                </el-table-column>
                <el-table-column prop="level" label="级别" width="100">
                  <template #default="{ row }">
                    <el-tag :type="getLogLevelType(row.level)">
                      {{ row.level }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="module" label="模块" width="150" />
                <el-table-column prop="message" label="消息" show-overflow-tooltip />
              </el-table>
            </div>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowDown,
  Edit,
  Delete,
  Connection,
  Download,
  Remove,
  InfoFilled,
  ArrowRight,
  Refresh,
  Search
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { socketManager } from '@/utils/socket'
import { computed } from 'vue'

const clients = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const installDialogVisible = ref(false)
const dialogType = ref('add')
const authType = ref('password')
const form = ref({
  name: '',
  hostname: '',
  ip_address: '',
  port: 22,
  username: '',
  auth_type: 'password',
  password: '',
  ssh_key: '',
  description: ''
})

const installForm = ref({
  install_path: '/opt/easysync',
  config: '{}'
})

const rules = {
  name: [
    { required: true, message: '请输入名称', trigger: 'blur' }
  ],
  hostname: [
    { required: false, message: '请输入服务器主机名', trigger: 'blur' }
  ],
  ip_address: [
    { required: true, message: '请输入服务器地址', trigger: 'blur' }
  ],
  port: [
    { required: true, message: '请输入SSH端口', trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: '端口号必须在1-65535之间', trigger: 'blur' }
  ],
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' }
  ],
  auth_type: [
    { required: true, message: '请选择认证方式', trigger: 'change' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { validator: (rule, value, callback) => {
      if (form.value.auth_type === 'password' && !value) {
        callback(new Error('密码不能为空'))
      } else {
        callback()
      }
    }, trigger: 'blur' }
  ],
  ssh_key: [
    { required: true, message: '请输入SSH密钥', trigger: 'blur' },
    { validator: (rule, value, callback) => {
      if (form.value.auth_type === 'key' && !value) {
        callback(new Error('SSH密钥不能为空'))
      } else {
        callback()
      }
    }, trigger: 'blur' }
  ]
}

const formRef = ref(null)

// 抽屉相关
const drawerVisible = ref(false)
const activeTab = ref('basic')
const currentClient = ref({})
const clientDetail = ref({
  cpu_info: [],
  memory_info: {},
  disk_info: [],
  network_info: [],
  process_list: [],
  os_type: ''
})

// 图表相关
const cpuChart = ref(null)
const memoryChart = ref(null)
const networkChart = ref(null)
const cpuTimeRange = ref('1h')
const memoryTimeRange = ref('1h')
const networkTimeRange = ref('1h')

const cpuChartInstance = ref(null)
const memoryChartInstance = ref(null)
const networkChartInstance = ref(null)

// WebSocket相关
const socket = ref(null)
const isConnected = ref(false)

// 监控相关的数据
const timeRange = ref('1h')
const customTimeRange = ref([])
const autoRefresh = ref(false)
const refreshInterval = ref('10')
const refreshing = ref(false)
const refreshTimer = ref(null)

const monitorData = ref({
  cpu: [],
  memory: [],
  network: {
    recv: [],
    sent: []
  }
})

// 日志相关数据
const logSearchQuery = ref('')
const logLevelFilter = ref('')
const autoRefreshLogs = ref(false)
const logRefreshInterval = ref('5')
const refreshingLogs = ref(false)
const loadingLogs = ref(false)
const logTimer = ref(null)
const logs = ref([])

// 添加全局错误处理器
const originalErrorHandler = window.onerror
window.onerror = function(message, source, lineno, colno, error) {
  // 忽略 ResizeObserver 相关的警告
  if (message && typeof message === 'string' && message.includes('ResizeObserver')) {
    return true
  }
  // 其他错误继续使用原来的错误处理器
  if (originalErrorHandler) {
    return originalErrorHandler.apply(this, arguments)
  }
  return false
}

const setupWebSocket = () => {
  // 连接到 WebSocket 服务器
  socketManager.connect(currentClient.value?.id);

  // 监听监控数据更新
  socketManager.on('monitor_update', (data) => {
    console.log('Received monitor update:', data);
    if (data.client_id === currentClient.value?.id) {
      // 确保数据格式正确
      if (data.data) {
        // 添加时间戳
        data.data.timestamp = data.timestamp;
        updateChartData(data.data);
      } else {
        console.warn('Monitor data format incorrect:', data);
      }
    }
  });

  // 监听客户端状态更新
  socketManager.on('client_status', (data) => {
    console.log('Received client status update:', data);
    updateClientStatus(data);
  });
};

const updateChartData = (data) => {
  try {
    console.log('Updating chart data:', data);
    if (!data || !data.timestamp) {
      console.warn('Invalid chart data received');
      return;
    }

    // 使用数据记录的时间戳
    const timestamp = new Date(data.timestamp).getTime();

    // 更新CPU数据
    if (cpuChartInstance.value && data.cpu) {
      const cpuUsage = parseFloat(data.cpu.percent || 0);
      if (!monitorData.value.cpu) {
        monitorData.value.cpu = [];
      }
      monitorData.value.cpu.push([timestamp, cpuUsage]);
      if (monitorData.value.cpu.length > 100) {
        monitorData.value.cpu.shift();
      }
      if (cpuChartInstance.value) {
        cpuChartInstance.value.setOption({
          series: [{
            data: monitorData.value.cpu
          }]
        });
      }
    }

    // 更新内存数据
    if (memoryChartInstance.value && data.memory) {
      const memoryUsage = parseFloat(data.memory.percent || 0);
      if (!monitorData.value.memory) {
        monitorData.value.memory = [];
      }
      monitorData.value.memory.push([timestamp, memoryUsage]);
      if (monitorData.value.memory.length > 100) {
        monitorData.value.memory.shift();
      }
      if (memoryChartInstance.value) {
        memoryChartInstance.value.setOption({
          series: [{
            data: monitorData.value.memory
          }]
        });
      }
    }

    // 更新网络数据
    if (networkChartInstance.value && data.network) {
      const recv = parseFloat(data.network.bytes_recv || 0);
      const sent = parseFloat(data.network.bytes_sent || 0);
      
      if (!monitorData.value.network) {
        monitorData.value.network = {
          recv: [],
          sent: []
        };
      }
      
      monitorData.value.network.recv.push([timestamp, recv]);
      monitorData.value.network.sent.push([timestamp, sent]);
      
      if (monitorData.value.network.recv.length > 100) {
        monitorData.value.network.recv.shift();
        monitorData.value.network.sent.shift();
      }
      
      if (networkChartInstance.value) {
        networkChartInstance.value.setOption({
          series: [
            { data: monitorData.value.network.recv },
            { data: monitorData.value.network.sent }
          ]
        });
      }
    }
  } catch (error) {
    console.error('更新图表数据失败:', error);
  }
};

const updateClientStatus = (data) => {
  const client = clients.value.find(c => c.id === data.client_id);
  if (client) {
    client.status = data.status;
    client.last_seen = data.timestamp;
  }
};

// 获取监控数据
const fetchMonitorData = async (clientId, type, timeRange) => {
  try {
    const hours = parseInt(timeRange);
    const end = new Date();
    const start = new Date(end.getTime() - hours * 3600 * 1000);
    
    const response = await axios.get(`/api/monitor/${clientId}/history`, {
      params: {
        type,
        start: start.toISOString(),
        end: end.toISOString()
      }
    });
    
    if (response.data.status === 'success') {
      return response.data.data || [];
    }
    return [];
  } catch (error) {
    console.error(`获取${type}监控数据失败:`, error);
    return [];
  }
};

// 获取服务器列表
const fetchClients = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/clients')
    // 确保返回的数据是数组
    const data = response.data.data
    clients.value = Array.isArray(data) ? data : []
    // 如果数据为空，显示提示信息
    if (clients.value.length === 0) {
      ElMessage.info('暂无服务器数据')
    }
  } catch (error) {
    // 错误处理已经在拦截器中完成
    clients.value = []  // 发生错误时设置为空数组
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '从未在线'
  return new Date(date).toLocaleString()
}

// 获取状态类型
const getStatusType = (status) => {
  switch (status) {
    case 'online':
      return 'success'
    case 'offline':
      return 'warning'
    case 'error':
      return 'danger'
    default:
      return 'info'
  }
}

// 获取使用率状态
const getUsageStatus = (usage) => {
  if (usage >= 90) return 'exception'
  if (usage >= 70) return 'warning'
  return 'success'
}

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case 'online':
      return '在线'
    case 'offline':
      return '离线'
    case 'error':
      return '错误'
    default:
      return '未知'
  }
}

// 获取Agent状态类型
const getAgentStatusType = (status) => {
  switch (status) {
    case 'running':
      return 'success'
    case 'installing':
      return 'warning'
    case 'not_installed':
      return 'info'
    case 'uninstall_error':
      return 'danger'
    case 'install_error':
      return 'danger'
    case 'online':
      return 'success'
    case 'offline':
      return 'warning'
    default:
      return 'info'
  }
}

// 获取Agent状态文本
const getAgentStatusText = (status) => {
  switch (status) {
    case 'running':
      return '运行中'
    case 'installing':
      return '安装中'
    case 'not_installed':
      return '未安装'
    case 'uninstall_error':
      return '卸载失败'
    case 'install_error':
      return '安装失败'
    case 'online':
      return '在线'
    case 'offline':
      return '离线'
    default:
      return '未知'
  }
}

// 格式化文件大小
const formatSize = (bytes) => {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(2)} ${units[unitIndex]}`
}

// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = 'add'
  form.value = {
    name: '',
    hostname: '',
    ip_address: '',
    port: 22,
    username: '',
    auth_type: 'password',
    password: '',
    ssh_key: '',
    description: ''
  }
  dialogVisible.value = true
}

// 显示编辑对话框
const showEditDialog = (row) => {
  dialogType.value = 'edit'
  form.value = { ...row }
  dialogVisible.value = true
}

// 提交表单
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    if (dialogType.value === 'add') {
      await axios.post('/api/clients', form.value)
      ElMessage.success('添加成功')
    } else {
      await axios.put(`/api/clients/${form.value.id}`, form.value)
      ElMessage.success('更新成功')
    }
    dialogVisible.value = false
    fetchClients()
  } catch (error) {
    if (error.response) {
      // 错误处理已经在拦截器中完成
    } else if (error.message) {
      // 表单验证错误
      ElMessage.error(error.message)
    }
  }
}

// 安装Agent
const installAgent = (row) => {
  currentClient.value = row
  installForm.value = {
    install_path: '/opt/easysync',
    config: JSON.stringify({
    })
  }
  installDialogVisible.value = true
}

// 确认安装
const confirmInstall = async () => {
  try {
    if (!currentClient.value) {
      ElMessage.error('未选择客户端')
      return
    }
    await axios.post(`/api/clients/${currentClient.value.id}/install`, installForm.value)
    ElMessage.success('开始安装Agent')
    installDialogVisible.value = false
    fetchClients()
  } catch (error) {
    // 错误处理已经在拦截器中完成
  }
}

// 卸载Agent
const uninstallAgent = async (row) => {
  try {
    await ElMessageBox.confirm('确定要卸载Agent吗？', '提示', {
      type: 'warning'
    })
    await axios.post(`/api/clients/${row.id}/uninstall`)
    ElMessage.success('开始卸载Agent')
    fetchClients()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误处理已经在拦截器中完成
    }
  }
}

// 删除服务器
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该服务器吗？', '提示', {
      type: 'warning'
    })
    await axios.delete(`/api/clients/${row.id}`)
    ElMessage.success('删除成功')
    fetchClients()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误处理已经在拦截器中完成
    }
  }
}

// 测试连接
const testConnection = async (row) => {
  try {
    row.testing = true
    const response = await axios.post(`/api/clients/${row.id}/test-connection`)
    if (response.data.status === 'success') {
      ElMessage.success('连接测试成功')
      // 更新本地状态
      row.status = 'online'
      fetchClients()  // 刷新列表以更新状态
    }
  } catch (error) {
    // 错误处理已经在拦截器中完成
  } finally {
    row.testing = false
  }
}

// 获取客户端信息
const getClientInfo = async (row) => {
  try {
    row.fetching = true
    await axios.post(`/api/clients/${row.id}/status`)
    ElMessage.success('获取信息成功')
    fetchClients()  // 刷新列表以更新信息
  } catch (error) {
    ElMessage.error('获取信息失败')
  } finally {
    row.fetching = false
  }
}

// 显示主机详情
const showClientDetail = async (client) => {
  try {
    currentClient.value = client;
    drawerVisible.value = true;
    
    // 先获取客户端详情
    await fetchClientDetail(client.id);

    // 初始化图表
    await nextTick();
    await initCharts();
    
    // 设置 WebSocket 连接
    setupWebSocket();
    
    // 订阅客户端数据
    if (socketManager.isConnected()) {
      console.log('Subscribing to client data:', client.id);
      socketManager.subscribe(client.id);
    } else {
      console.warn('WebSocket not connected, cannot subscribe');
    }
  } catch (error) {
    console.error('Error showing client detail:', error);
    ElMessage.error('加载客户端详情失败');
  }
};

// 获取主机详情
const fetchClientDetail = async (clientId) => {
  try {
    const response = await axios.get(`/api/clients/${clientId}/detail`)
    clientDetail.value = response.data.data
    clientDetail.value.os_type = response.data.data.os_type
  } catch (error) {
    ElMessage.error('获取主机详情失败')
  }
}

// 初始化图表
const initCharts = async () => {
  if (!currentClient.value?.id) {
    console.warn('当前没有选中的客户端')
    return
  }

  try {
    // 销毁旧的实例
    disposeCharts()
    
    await nextTick()
    
    // 初始化CPU图表
    if (cpuChart.value) {
      cpuChartInstance.value = echarts.init(cpuChart.value, null, {
        renderer: 'canvas',
        useDirtyRect: true
      })
      const cpuOption = {
        title: {
          text: 'CPU使用率',
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis',
          showContent: true,
          alwaysShowContent: false,
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          formatter: (params) => {
            if (!params || !params.length) return '';
            const time = new Date(params[0].value[0]).toLocaleString();
            const usage = params[0].value[1].toFixed(2);
            return `
              <div style="font-weight: bold">${time}</div>
              <div style="margin-top: 5px">
                <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${params[0].color};"></span>
                CPU使用率: ${usage}%
              </div>
            `;
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '60px',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: { show: true },
          axisTick: { show: true },
          axisLabel: {
            formatter: (value) => {
              return new Date(value).toLocaleTimeString()
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed'
            }
          },
        },
        yAxis: {
          type: 'value',
          name: '使用率(%)',
          min: 0,
          max: 100,
          axisLabel: {
            formatter: '{value}%'
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        series: [{
          name: 'CPU使用率',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          showSymbol: true,
          symbolSize: 5,
          sampling: 'average',
          itemStyle: {
            color: '#409EFF'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64,158,255,0.3)' },
              { offset: 1, color: 'rgba(64,158,255,0.1)' }
            ])
          },
          emphasis: {
            focus: 'series',
            itemStyle: {
              color: '#409EFF',
              borderWidth: 2,
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowOffsetY: 0,
              shadowColor: 'rgba(0,0,0,0.3)'
            }
          },
          data: monitorData.value.cpu || []
        }]
      }
      cpuChartInstance.value.setOption(cpuOption)
    }

    // 初始化内存图表
    if (memoryChart.value) {
      memoryChartInstance.value = echarts.init(memoryChart.value, null, {
        renderer: 'canvas',
        useDirtyRect: true
      })
      const memoryOption = {
        title: {
          text: '内存使用率',
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis',
          showContent: true,
          alwaysShowContent: false,
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          formatter: (params) => {
            if (!params || !params.length) return '';
            const time = new Date(params[0].value[0]).toLocaleString();
            const usage = params[0].value[1].toFixed(2);
            return `
              <div style="font-weight: bold">${time}</div>
              <div style="margin-top: 5px">
                <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${params[0].color};"></span>
                内存使用率: ${usage}%
              </div>
            `;
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '60px',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: { show: true },
          axisTick: { show: true },
          axisLabel: {
            formatter: (value) => {
              return new Date(value).toLocaleTimeString()
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '使用率(%)',
          min: 0,
          max: 100,
          axisLabel: {
            formatter: '{value}%'
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        series: [{
          name: '内存使用率',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          showSymbol: true,
          symbolSize: 5,
          sampling: 'average',
          itemStyle: {
            color: '#67C23A'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(103,194,58,0.3)' },
              { offset: 1, color: 'rgba(103,194,58,0.1)' }
            ])
          },
          emphasis: {
            focus: 'series',
            itemStyle: {
              color: '#67C23A',
              borderWidth: 2,
              shadowBlur: 10,
              shadowOffsetX: 0,
              shadowOffsetY: 0,
              shadowColor: 'rgba(0,0,0,0.3)'
            }
          },
          data: monitorData.value.memory || []
        }]
      }
      memoryChartInstance.value.setOption(memoryOption)
    }

    // 初始化网络图表
    if (networkChart.value) {
      networkChartInstance.value = echarts.init(networkChart.value, null, {
        renderer: 'canvas',
        useDirtyRect: true
      })
      const networkOption = {
        title: {
          text: '网络流量',
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 14
          }
        },
        tooltip: {
          trigger: 'axis',
          showContent: true,
          alwaysShowContent: false,
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          formatter: (params) => {
            if (!params || !params.length) return '';
            const time = new Date(params[0].value[0]).toLocaleString();
            const usage = params[0].value[1].toFixed(2);
            return `
              <div style="font-weight: bold">${time}</div>
              <div style="margin-top: 5px">
                <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${params[0].color};"></span>
                接收: ${formatSize(params[0].value[1])}/s
              </div>
              <div style="margin-top: 5px">
                <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${params[1].color};"></span>
                发送: ${formatSize(params[1].value[1])}/s
              </div>
            `;
          }
        },
        legend: {
          data: ['接收', '发送'],
          top: 40
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '90px',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: { show: true },
          axisTick: { show: true },
          axisLabel: {
            formatter: (value) => {
              return new Date(value).toLocaleTimeString()
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        yAxis: {
          type: 'value',
          name: '流量/s',
          axisLabel: {
            formatter: (value) => formatSize(value) + '/s'
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed'
            }
          }
        },
        series: [
          {
            name: '接收',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            showSymbol: true,
            symbolSize: 5,
            sampling: 'average',
            itemStyle: {
              color: '#409EFF'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(64,158,255,0.3)' },
                { offset: 1, color: 'rgba(64,158,255,0.1)' }
              ])
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                color: '#409EFF',
                borderWidth: 2,
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowOffsetY: 0,
                shadowColor: 'rgba(0,0,0,0.3)'
              }
            },
            data: monitorData.value.network.recv || []
          },
          {
            name: '发送',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            showSymbol: true,
            symbolSize: 5,
            sampling: 'average',
            itemStyle: {
              color: '#67C23A'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(103,194,58,0.3)' },
                { offset: 1, color: 'rgba(103,194,58,0.1)' }
              ])
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                color: '#67C23A',
                borderWidth: 2,
                shadowBlur: 10,
                shadowOffsetX: 0,
                shadowOffsetY: 0,
                shadowColor: 'rgba(0,0,0,0.3)'
              }
            },
            data: monitorData.value.network.sent || []
          }
        ]
      }
      networkChartInstance.value.setOption(networkOption)
    }

    // 加载历史数据
    await loadHistoryData()
    
  } catch (error) {
    console.error('初始化图表失败:', error)
    ElMessage.error('初始化图表失败，请稍后重试')
  }
}

// 加载历史数据
const loadHistoryData = async () => {
  try {
    const clientId = currentClient.value.id
    const now = new Date()
    let start = new Date()

    // 根据选择的时间范围计算开始时间
    if (timeRange.value === 'custom' && customTimeRange.value?.length === 2) {
      start = customTimeRange.value[0]
      now.setTime(customTimeRange.value[1])
    } else {
      const value = timeRange.value
      const unit = value.slice(-1)
      const amount = parseInt(value.slice(0, -1))
      
      if (unit === 'm') {
        start.setMinutes(start.getMinutes() - amount)
      } else if (unit === 'h') {
        start.setHours(start.getHours() - amount)
      }
    }
    
    const response = await axios.get(`/api/monitor/${clientId}/history`, {
      params: {
        start: start.toISOString(),
        end: now.toISOString()
      }
    })

    if (response.data.status === 'success' && response.data.data) {
      const historyData = response.data.data.sort((a, b) => 
        new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
      )

      // 清空现有数据
      monitorData.value = {
        cpu: [],
        memory: [],
        network: {
          recv: [],
          sent: []
        }
      }

      // 处理历史数据
      historyData.forEach(item => {
        // 使用数据记录的时间戳
        const timestamp = new Date(item.timestamp).getTime()
        
        // CPU数据
        const cpuUsage = parseFloat(item.data.cpu?.percent || 0)
        monitorData.value.cpu.push([timestamp, cpuUsage])
        
        // 内存数据
        const memoryUsage = parseFloat(item.data.memory?.percent || 0)
        monitorData.value.memory.push([timestamp, memoryUsage])
        
        // 网络数据
        const recv = parseFloat(item.data.network?.bytes_recv || 0)
        const sent = parseFloat(item.data.network?.bytes_sent || 0)
        monitorData.value.network.recv.push([timestamp, recv])
        monitorData.value.network.sent.push([timestamp, sent])
      })

      // 更新图表数据
      updateCharts()
    }
  } catch (error) {
    console.error('加载历史数据失败:', error)
    ElMessage.error('加载历史数据失败，请稍后重试')
  }
}

// 更新图表数据
const updateCharts = () => {
  if (cpuChartInstance.value) {
    cpuChartInstance.value.setOption({
      series: [{
        data: monitorData.value.cpu || []
      }]
    })
  }

  if (memoryChartInstance.value) {
    memoryChartInstance.value.setOption({
      series: [{
        data: monitorData.value.memory || []
      }]
    })
  }

  if (networkChartInstance.value) {
    networkChartInstance.value.setOption({
      series: [
        { data: monitorData.value.network.recv || [] },
        { data: monitorData.value.network.sent || [] }
      ]
    })
  }
}

// 处理时间范围变化
const handleTimeRangeChange = () => {
  if (timeRange.value !== 'custom') {
    loadHistoryData()
  }
}

// 处理自定义时间范围变化
const handleCustomTimeRangeChange = () => {
  if (customTimeRange.value && customTimeRange.value.length === 2) {
    loadHistoryData()
  }
}

// 处理手动刷新
const handleManualRefresh = async () => {
  refreshing.value = true
  try {
    await loadHistoryData()
  } finally {
    refreshing.value = false
  }
}

// 处理自动刷新开关变化
const handleAutoRefreshChange = (value) => {
  if (value) {
    startAutoRefresh()
  } else {
    stopAutoRefresh()
  }
}

// 处理刷新间隔变化
const handleRefreshIntervalChange = () => {
  if (autoRefresh.value) {
    stopAutoRefresh()
    startAutoRefresh()
  }
}

// 开始自动刷新
const startAutoRefresh = () => {
  stopAutoRefresh() // 先停止现有的定时器
  const interval = parseInt(refreshInterval.value) * 1000
  refreshTimer.value = setInterval(async () => {
    await loadHistoryData()
  }, interval)
}

// 停止自动刷新
const stopAutoRefresh = () => {
  if (refreshTimer.value) {
    clearInterval(refreshTimer.value)
    refreshTimer.value = null
  }
}

// 监听标签页切换
watch(activeTab, (newVal) => {
  if (newVal === 'monitor' && drawerVisible.value) {
    nextTick(async () => {
      await initCharts()
      // 如果已经连接了WebSocket，重新加载数据
      if (isConnected.value) {
        loadHistoryData()
      }
    })
  }
})

// 监听时间范围变化
watch([cpuTimeRange, memoryTimeRange, networkTimeRange], () => {
  if (activeTab.value === 'monitor' && drawerVisible.value) {
    nextTick(() => {
      loadHistoryData()
    })
  }
})

// 处理窗口大小变化
const handleResize = () => {
  if (!drawerVisible.value) return
  
  nextTick(() => {
    try {
      if (cpuChartInstance.value) {
        cpuChartInstance.value.resize({
          animation: {
            duration: 300
          },
          silent: true
        })
      }
      if (memoryChartInstance.value) {
        memoryChartInstance.value.resize({
          animation: {
            duration: 300
          },
          silent: true
        })
      }
      if (networkChartInstance.value) {
        networkChartInstance.value.resize({
          animation: {
            duration: 300
          },
          silent: true
        })
      }
    } catch (error) {
      console.warn('图表调整大小失败:', error)
    }
  })
}

// 销毁图表实例
const disposeCharts = () => {
  try {
    if (cpuChartInstance.value) {
      cpuChartInstance.value.dispose()
      cpuChartInstance.value = null
    }
    if (memoryChartInstance.value) {
      memoryChartInstance.value.dispose()
      memoryChartInstance.value = null
    }
    if (networkChartInstance.value) {
      networkChartInstance.value.dispose()
      networkChartInstance.value = null
    }
  } catch (error) {
    console.warn('销毁图表实例失败:', error)
  }
}

// 监听抽屉显示状态
watch(drawerVisible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      if (activeTab.value === 'monitor') {
        initCharts()
      }
      // 使用防抖处理resize事件
      const debouncedResize = debounce(handleResize, 300)
      window.addEventListener('resize', debouncedResize)
    })
  } else {
    disposeCharts()
    window.removeEventListener('resize', handleResize)
  }
})

// 添加防抖函数
const debounce = (fn, delay) => {
  let timer = null
  return function (...args) {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => {
      fn.apply(this, args)
    }, delay)
  }
}

// 组件卸载时清理
onUnmounted(() => {
  stopAutoRefresh()
  if (currentClient.value?.id) {
    socketManager.unsubscribe(currentClient.value.id)
  }
  socketManager.disconnect()
  disposeCharts()
  window.removeEventListener('resize', handleResize)
  // 恢复原来的错误处理器
  window.onerror = originalErrorHandler
})

// 关闭抽屉时清理
const handleDrawerClose = () => {
  stopAutoRefresh()
  if (currentClient.value?.id) {
    socketManager.unsubscribe(currentClient.value.id)
  }
  socketManager.disconnect()
  disposeCharts()
  drawerVisible.value = false
  activeTab.value = 'basic'
}

// 处理主机名点击
const handleNameClick = async (client) => {
  try {
    await showClientDetail(client);
  } catch (error) {
    console.error('加载监控数据失败:', error);
    ElMessage.error('加载监控数据失败: ' + error.message);
  }
};

// 刷新进程列表
const refreshProcessList = async () => {
  try {
    const response = await axios.get(`/api/clients/${currentClient.value.id}/processes`)
    clientDetail.value.process_list = response.data.data
  } catch (error) {
    ElMessage.error('获取进程列表失败')
  }
}

// 获取日志级别类型
const getLogLevelType = (level) => {
  switch (level) {
    case 'DEBUG':
      return 'info'
    case 'INFO':
      return ''
    case 'WARNING':
      return 'warning'
    case 'ERROR':
    case 'CRITICAL':
      return 'danger'
    default:
      return 'info'
  }
}

// 过滤日志
const filteredLogs = computed(() => {
  if (!Array.isArray(logs.value)) {
    return []
  }
  return logs.value.filter(log => {
    const matchesSearch = !logSearchQuery.value || 
      log.message.toLowerCase().includes(logSearchQuery.value.toLowerCase())
    const matchesLevel = !logLevelFilter.value || 
      log.level === logLevelFilter.value
    return matchesSearch && matchesLevel
  })
})

// 处理日志搜索
const handleLogSearch = () => {
  // 搜索逻辑已经在 computed 中实现
}

// 处理手动刷新日志
const handleManualLogRefresh = async () => {
  refreshingLogs.value = true
  try {
    await fetchLogs()
  } finally {
    refreshingLogs.value = false
  }
}

// 处理自动刷新开关变化
const handleAutoLogRefreshChange = (value) => {
  if (value) {
    startAutoLogRefresh()
  } else {
    stopAutoLogRefresh()
  }
}

// 处理刷新间隔变化
const handleLogRefreshIntervalChange = () => {
  if (autoRefreshLogs.value) {
    stopAutoLogRefresh()
    startAutoLogRefresh()
  }
}

// 开始自动刷新日志
const startAutoLogRefresh = () => {
  stopAutoLogRefresh() // 先停止现有的定时器
  const interval = parseInt(logRefreshInterval.value) * 1000
  logTimer.value = setInterval(async () => {
    await fetchLogs()
  }, interval)
}

// 停止自动刷新日志
const stopAutoLogRefresh = () => {
  if (logTimer.value) {
    clearInterval(logTimer.value)
    logTimer.value = null
  }
}

// 获取日志数据
const fetchLogs = async () => {
  if (!currentClient.value?.id) return
  
  try {
    loadingLogs.value = true
    const response = await axios.get(`/api/clients/${currentClient.value.id}/logs`)
    if (response.data.status === 'success') {
      // 解析日志字符串为数组
      const logEntries = response.data.data.log_content.split('\n')
        .filter(line => line.trim()) // 过滤空行
        .map(line => {
          // 解析日志行，格式如：2025-04-24 11:34:42,700 - agent.client - INFO - 心跳服务已停止
          const match = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}) - ([\w.]+) - (\w+) - (.+)$/)
          if (match) {
            return {
              timestamp: match[1],
              module: match[2],
              level: match[3],
              message: match[4]
            }
          }
          return null
        })
        .filter(entry => entry !== null) // 过滤掉解析失败的行
      
      logs.value = logEntries
    }
  } catch (error) {
    console.error('获取日志失败:', error)
    ElMessage.error('获取日志失败')
  } finally {
    loadingLogs.value = false
  }
}

// 监听标签页切换
watch(activeTab, (newVal) => {
  if (newVal === 'logs' && drawerVisible.value) {
    nextTick(async () => {
      await fetchLogs()
      if (autoRefreshLogs.value) {
        startAutoLogRefresh()
      }
    })
  } else if (newVal !== 'logs') {
    stopAutoLogRefresh()
  }
})

onMounted(() => {
  fetchClients()
})
</script>

<style scoped>
.clients-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.detail-content {
  height: calc(100vh - 120px);
  overflow-y: auto;
  padding: 20px;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  margin-bottom: 20px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 16px;
  font-weight: bold;
  color: #303133;
  padding: 12px 20px;
  border-bottom: 1px solid #ebeef5;
}

.cpu-info {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px;
}

.cpu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  min-width: 200px;
}

.cpu-cores {
  color: #606266;
  font-size: 14px;
}

.memory-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 16px;
}

.memory-details {
  display: flex;
  justify-content: space-between;
  color: #606266;
  font-size: 14px;
}

.disk-info {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 16px;
}

.disk-item {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.disk-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.disk-mount {
  color: #606266;
  font-size: 14px;
}

.disk-details {
  display: flex;
  justify-content: space-between;
  color: #606266;
  font-size: 14px;
}

.network-info {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  padding: 16px;
}

.nic-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background-color: #f5f7fa;
  border-radius: 4px;
  min-width: 300px;
  flex-wrap: wrap;
}

.nic-ip, .nic-ip6, .nic-mac, .nic-mtu, .nic-status {
  color: #606266;
  font-size: 14px;
  margin-right: 8px;
}

:deep(.el-descriptions) {
  padding: 16px;
}

:deep(.el-descriptions__label) {
  width: 100px;
  color: #909399;
}

:deep(.el-descriptions__content) {
  color: #303133;
}

:deep(.el-progress) {
  margin: 0;
}

@media screen and (max-width: 768px) {
  .detail-content {
    padding: 10px;
  }

  .cpu-item, .nic-item {
    min-width: 100%;
  }

  .memory-details, .disk-details {
    flex-direction: column;
    gap: 8px;
  }
}

.monitor-content {
  padding: 20px;
}

.chart-container {
  margin-bottom: 24px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 20px;

  .chart-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    padding-bottom: 16px;
    border-bottom: 1px solid #ebeef5;

    h3 {
      margin: 0;
      font-size: 16px;
      font-weight: 500;
      color: #303133;
    }
  }

  .chart {
    height: 300px;
    width: 100%;
  }

  :deep(.el-table) {
    --el-table-border-color: #ebeef5;
    --el-table-header-bg-color: #f5f7fa;
    border-radius: 4px;
    margin-top: 8px;
  }

  :deep(.el-table th) {
    background-color: var(--el-table-header-bg-color);
    font-weight: 500;
  }

  :deep(.el-table--border) {
    border: 1px solid var(--el-table-border-color);
  }

  :deep(.el-progress) {
    margin: 0;
  }
}

.monitor-control-panel {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  gap: 24px;
  flex-wrap: wrap;
}

.panel-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-label {
  font-size: 14px;
  font-weight: 500;
  color: #606266;
  white-space: nowrap;
}

.time-range-selector {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-select {
  width: 140px;
}

.date-picker {
  width: 360px;
}

.refresh-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.refresh-button {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.auto-refresh-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.refresh-switch {
  margin-right: 8px;
}

.interval-select {
  width: 100px;
}

@media screen and (max-width: 768px) {
  .monitor-control-panel {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .panel-section {
    width: 100%;
    flex-wrap: wrap;
  }

  .time-range-selector {
    flex-wrap: wrap;
  }

  .date-picker {
    width: 100%;
  }

  .refresh-controls {
    width: 100%;
    flex-wrap: wrap;
  }
}

.fixed-tabs {
  position: sticky;
  top: 0;
  z-index: 100;
  background-color: #fff;
  padding: 0 20px;
  margin: 0 -20px;
  border-bottom: 1px solid #ebeef5;
}

.scrollable-content {
  height: calc(100vh - 180px);
  overflow-y: auto;
  padding: 20px;
}

.logs-content {
  padding: 20px;
}

.logs-control-panel {
  margin-bottom: 20px;
  padding: 16px;
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.search-controls {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.search-input {
  width: 200px;
}

.level-select {
  width: 120px;
}

.logs-list {
  background-color: #ffffff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 16px;
}

@media screen and (max-width: 768px) {
  .search-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input,
  .level-select {
    width: 100%;
  }
}
</style> 