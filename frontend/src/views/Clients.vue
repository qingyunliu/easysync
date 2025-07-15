<template>
  <div class="clients-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">源端服务器管理</h1>
          <p class="page-subtitle">管理您的源端服务器，安装Agent后可将本地数据同步到目标存储</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="showAddDialog" class="action-btn">
            <el-icon><Plus /></el-icon>
            添加源端服务器
          </el-button>
          <el-button 
            type="info" 
            @click="toggleArchitecture"
            class="guide-btn"
            :title="showArchitecture ? '隐藏流程引导' : '显示流程引导'"
          >
            <el-icon>
              <View v-if="showArchitecture" />
              <Hide v-else />
            </el-icon>
            流程引导
          </el-button>
        </div>
      </div>
    </div>

    <!-- 架构说明卡片 -->
    <transition name="fade-arch">
      <div class="architecture-section" v-show="showArchitecture">
        <el-card class="architecture-card" shadow="never">
          <template #header>
            <div class="card-header">
              <h3>数据同步架构说明</h3>
              <el-tag type="info">EasySync 数据同步流程</el-tag>
            </div>
          </template>
          <div class="architecture-content">
            <div class="architecture-diagram">
              <div class="flow-step">
                <div class="step-icon">
                  <el-icon><Monitor /></el-icon>
                </div>
                <div class="step-content">
                  <h4>1. 源端服务器 (Clients)</h4>
                  <p>用户的数据源服务器，安装Agent后可获取本地分区、目录、文件信息</p>
                  <ul>
                    <li>支持Windows/Linux系统</li>
                    <li>通过SSH连接管理</li>
                    <li>Agent自动采集系统资源信息</li>
                  </ul>
                </div>
              </div>
              
              <div class="flow-arrow">
                <el-icon><ArrowRight /></el-icon>
              </div>
              
              <div class="flow-step">
                <div class="step-icon">
                  <el-icon><Connection /></el-icon>
                </div>
                <div class="step-content">
                  <h4>2. 同步代理 (Nodes)</h4>
                  <p>数据同步的中间节点，负责数据传输和转换</p>
                  <ul>
                    <li>接收源端数据</li>
                    <li>处理数据格式转换</li>
                    <li>转发到目标存储</li>
                  </ul>
                </div>
              </div>
              
              <div class="flow-arrow">
                <el-icon><ArrowRight /></el-icon>
              </div>
              
              <div class="flow-step">
                <div class="step-icon">
                  <el-icon><FolderOpened /></el-icon>
                </div>
                <div class="step-content">
                  <h4>3. 目标存储 (Storages)</h4>
                  <p>数据同步的目标位置，支持多种存储类型</p>
                  <ul>
                    <li>NAS网络存储</li>
                    <li>OBS对象存储</li>
                    <li>NFS文件系统</li>
                    <li>本地存储</li>
                  </ul>
                </div>
              </div>
            </div>
            
            <div class="usage-guide">
              <h4>使用指南</h4>
              <div class="guide-steps">
                <div class="guide-step">
                  <div class="step-number">1</div>
                  <div class="step-text">
                    <strong>添加源端服务器</strong>
                    <p>点击"添加源端服务器"按钮，填写服务器信息（IP、用户名、密码等）</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">2</div>
                  <div class="step-text">
                    <strong>测试连接</strong>
                    <p>确保能够通过SSH连接到源端服务器</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">3</div>
                  <div class="step-text">
                    <strong>安装Agent</strong>
                    <p>在源端服务器上安装EasySync Agent，用于数据采集和传输</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">4</div>
                  <div class="step-text">
                    <strong>配置同步任务</strong>
                    <p>在任务管理中创建同步任务，指定源端路径和目标存储</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </el-card>
      </div>
    </transition>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-icon online">
            <el-icon><Monitor /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.online }}</div>
            <div class="stat-label">在线服务器</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon offline">
            <el-icon><CircleClose /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.offline }}</div>
            <div class="stat-label">离线服务器</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon running">
            <el-icon><Connection /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.running }}</div>
            <div class="stat-label">运行中Agent</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon pending">
            <el-icon><Clock /></el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pending }}</div>
            <div class="stat-label">待安装Agent</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 服务器列表卡片 -->
      <el-card class="clients-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <h3>服务器列表</h3>
              <el-tag type="info" size="small">{{ clients?.length || 0 }}台服务器</el-tag>
            </div>
            <div class="header-right">
              <!-- 分组/标签筛选与批量操作 -->
              <div class="filter-batch-bar" style="display: flex; align-items: center; gap: 16px;">
                <el-button type="danger" :disabled="!(multipleSelection?.length)" @click="handleBatchDelete">批量删除</el-button>
                <el-button type="primary" :disabled="!(multipleSelection?.length)" @click="showBatchGroupDialog">批量分组</el-button>
                <el-button type="primary" :disabled="!(multipleSelection?.length)" @click="showBatchTagDialog">批量打标签</el-button>
                <el-select v-model="selectedGroup" placeholder="分组筛选" clearable style="width: 140px">
                  <el-option v-for="group in groupList" :key="group" :label="group" :value="group" />
                </el-select>
                <el-select v-model="selectedTag" placeholder="标签筛选" clearable style="width: 140px">
                  <el-option v-for="tag in tagList" :key="tag" :label="tag" :value="tag" />
                </el-select>
                <el-select v-model="statusFilter" placeholder="状态筛选" style="width: 120px" @change="handleSearch" class="filter-select">
                  <el-option label="全部" value="all" />
                  <el-option label="在线" value="online" />
                  <el-option label="离线" value="offline" />
                  <el-option label="已安装Agent" value="agent_installed" />
                  <el-option label="未安装Agent" value="agent_not_installed" />
                </el-select>
              </div>
              <el-input
                v-model="searchQuery"
                placeholder="搜索客户端..."
                class="search-input"
                clearable
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
              <el-button @click="fetchClients" class="refresh-btn">
                <el-icon><Refresh /></el-icon>
              </el-button>
            </div>
          </div>
        </template>

        <!-- 服务器表格 -->
        <div class="table-container">
          <el-table 
            :data="filteredClients" 
            style="width: 100%" 
            v-loading="loading"
            class="clients-table"
            @selection-change="handleSelectionChange"
          >
            <el-table-column type="selection" width="50" />
            <el-table-column prop="name" label="客户端名称" min-width="150">
              <template #default="{ row }">
                <div class="server-info server-name-link" @click="showClientDetail(row)">
                  <el-icon class="server-link-icon"><Monitor /></el-icon>
                  <span>{{ row.name }}</span>
                  <el-tag v-if="isNewServer(row)" type="success" class="new-tag">NEW</el-tag>
                </div>
        </template>
      </el-table-column>
            <el-table-column prop="group" label="分组" width="100">
        <template #default="{ row }">
                <el-tag v-if="row.group">{{ row.group }}</el-tag>
        </template>
      </el-table-column>
            <el-table-column prop="tags" label="标签" width="140">
        <template #default="{ row }">
                <el-tag v-for="tag in (row.tags ? row.tags.split(',') : [])" :key="tag" type="info" style="margin-right: 2px;">{{ tag }}</el-tag>
              </template>
            </el-table-column>
            
            <el-table-column prop="ip_address" label="IP地址" width="140" />
            
            <el-table-column prop="status" label="连接状态" width="120">
              <template #default="{ row }">
                <div class="status-indicator">
                  <div class="status-dot" :class="row.status"></div>
                  <span>{{ getStatusText(row.status) }}</span>
                </div>
              </template>
            </el-table-column>
            
            <el-table-column prop="agent_status" label="Agent状态" width="120">
              <template #default="{ row }">
                <el-tag :type="getAgentStatusType(row.agent_status)" size="small">
            {{ getAgentStatusText(row.agent_status) }}
          </el-tag>
        </template>
      </el-table-column>
            
            <el-table-column prop="os_type" label="操作系统" width="120" />
            
            <el-table-column prop="last_seen" label="上线时间" width="160">
        <template #default="{ row }">
                <div class="last-seen">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatDate(row.last_seen) }}</span>
                </div>
        </template>
      </el-table-column>
            
            <el-table-column label="操作" width="200" fixed="right">
        <template #default="{ row }">
                <div class="action-buttons">
                  <el-button 
                    type="primary" 
                    size="small" 
                    @click.stop="showClientDetail(row)"
                    class="detail-btn"
                  >
                    <el-icon><View /></el-icon>
                    详情
            </el-button>
                  <el-dropdown trigger="click" @command="handleCommand">
                    <el-button size="small">
                      更多<el-icon class="el-icon--right"><ArrowDown /></el-icon>
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'edit', row }">
                          <el-icon><Edit /></el-icon>编辑
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'test', row }">
                      <el-icon><Connection /></el-icon>测试连接
                  </el-dropdown-item>
                        <el-dropdown-item 
                          :command="{ action: 'install', row }"
                      :disabled="row.status !== 'online' || row.agent_status === 'installed' || row.agent_status === 'running'"
                    >
                      <el-icon><Download /></el-icon>安装Agent
                  </el-dropdown-item>
                        <el-dropdown-item 
                          :command="{ action: 'uninstall', row }"
                          :disabled="row.agent_status === 'not_installed' || row.agent_status === 'installing'"
                    >
                      <el-icon><Remove /></el-icon>卸载Agent
                  </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'info', row }">
                      <el-icon><InfoFilled /></el-icon>获取信息
                        </el-dropdown-item>
                        <el-dropdown-item divided :command="{ action: 'delete', row }">
                          <el-icon><Delete /></el-icon>删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
                </div>
        </template>
      </el-table-column>
    </el-table>
        </div>
      </el-card>
    </div>

    <!-- 添加/编辑对话框 -->
    <el-dialog
      :title="dialogType === 'add' ? '添加客户端' : '编辑客户端'"
      v-model="dialogVisible"
      width="600px"
      class="client-dialog"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-width="100px"
        class="client-form"
      >
        <el-row :gutter="20">
          <el-col :span="12">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入客户端名称" />
        </el-form-item>
          </el-col>
          <el-col :span="12">
        <el-form-item label="主机名" prop="hostname">
              <el-input v-model="form.hostname" placeholder="请输入主机名" />
        </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
        <el-form-item label="IP地址" prop="ip_address">
              <el-input v-model="form.ip_address" placeholder="请输入IP地址" />
        </el-form-item>
          </el-col>
          <el-col :span="12">
        <el-form-item label="SSH端口" prop="port">
              <el-input-number v-model="form.port" :min="1" :max="65535" style="width: 100%" />
        </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" />
        </el-form-item>
          </el-col>
          <el-col :span="12">
        <el-form-item label="认证方式" prop="auth_type">
          <el-radio-group v-model="form.auth_type">
            <el-radio :value="'password'">密码认证</el-radio>
            <el-radio :value="'key'">密钥认证</el-radio>
          </el-radio-group>
        </el-form-item>
          </el-col>
        </el-row>

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
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 安装Agent对话框 -->
    <el-dialog
      title="安装Agent"
      v-model="installDialogVisible"
      width="500px"
      class="install-dialog"
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
        <div class="dialog-footer">
          <el-button @click="installDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="confirmInstall">开始安装</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 主机详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="主机详情"
      direction="rtl"
      size="70%"
      :before-close="handleDrawerClose"
      class="client-drawer"
    >
      <div class="drawer-content">
        <el-tabs v-model="activeTab" class="detail-tabs">
        <!-- 基本信息标签页 -->
        <el-tab-pane label="基本信息" name="basic">
            <div class="detail-content">
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
            <div class="monitor-content">
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
            <div class="logs-content">
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
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, watch, onUnmounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ArrowDown,
  Edit,
  Delete,
  Connection,
  Download,
  Remove,
  Refresh,
  Search,
  Clock,
  Plus,
  Monitor,
  InfoFilled,
  CircleClose,
  View,
  ArrowRight,
  FolderOpened,
  Hide
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

// 基础数据
const clients = ref([])
const loading = ref(false)
const statusFilter = ref('all')
const searchQuery = ref('')
const handleSearch = () => {}

// 统计数据
const stats = computed(() => {
  const online = clients.value.filter(c => c.status === 'online').length
  const offline = clients.value.filter(c => c.status === 'offline').length
  const running = clients.value.filter(c => c.agent_status === 'running').length
  const pending = clients.value.filter(c => c.agent_status === 'not_installed').length
  
  return { online, offline, running, pending }
})

// 过滤后的客户端列表
const filteredClients = computed(() => {
  let result = clients.value
  
  // 搜索过滤
  if (searchQuery.value) {
    result = result.filter(client => 
      client.name.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      client.hostname.toLowerCase().includes(searchQuery.value.toLowerCase()) ||
      client.ip_address.includes(searchQuery.value)
    )
  }
  
  // 分组过滤
  if (selectedGroup.value) {
    result = result.filter(client => client.group === selectedGroup.value)
  }
  
  // 标签过滤
  if (selectedTag.value) {
    result = result.filter(client => {
      if (!client.tags) return false
      const tags = client.tags.split(',').map(tag => tag.trim())
      return tags.includes(selectedTag.value)
    })
  }

  if (statusFilter.value === 'online') {
    result = result.filter(n => n.status === 'online')
  } else if (statusFilter.value === 'offline') {
    result = result.filter(n => n.status === 'offline')
  } else if (statusFilter.value === 'agent_installed') {
    result = result.filter(n => n.agent_status === 'running')
  } else if (statusFilter.value === 'agent_not_installed') {
    result = result.filter(n => n.agent_status !== 'running')
  }
  
  return result
})

// 对话框相关
const dialogVisible = ref(false)
const installDialogVisible = ref(false)
const dialogType = ref('add')
const form = ref({
  name: '',
  hostname: '',
  ip_address: '',
  port: 22,
  username: '',
  auth_type: 'password',
  password: '',
  ssh_key: '',
  description: '',
  auto_generate_token: true,
  token_expires_in: 60,
  token_max_uses: 1
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

// 新上线服务器高亮（3分钟内显示 NEW 标签）
const now = ref(Date.now())
setInterval(() => { now.value = Date.now() }, 60000) // 每分钟刷新一次
const isNewServer = (server) => {
  if (!server.last_seen) return false
  const lastSeen = new Date(server.last_seen).getTime()
  return now.value - lastSeen < 3 * 60 * 1000 // 3分钟内
}

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

// 处理命令
const handleCommand = async (command) => {
  const { action, row } = command
  
  switch (action) {
    case 'edit':
      showEditDialog(row)
      break
    case 'test':
      await testConnection(row)
      break
    case 'install':
      installAgent(row)
      break
    case 'uninstall':
      await uninstallAgent(row)
      break
    case 'info':
      await getClientInfo(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
    }

// 获取监控数据
const fetchMonitorData = async (clientId) => {
  try {
    const res = await axios.get(`/api/monitor/${clientId}/history`)
    if (res.data.status === 'success' && res.data.data) {
      const data = res.data.data
      monitorData.value = {
        cpu: data.cpu || [],
        memory: data.memory || [],
        network: {
          recv: data.network?.recv || [],
          sent: data.network?.sent || []
        }
      }
      updateCharts && updateCharts()
    } else {
      // 若无数据也保证结构
      monitorData.value = {
        cpu: [],
        memory: [],
        network: { recv: [], sent: [] }
      }
      updateCharts && updateCharts()
    }
  } catch (e) {
    monitorData.value = {
      cpu: [],
      memory: [],
      network: { recv: [], sent: [] }
    }
    updateCharts && updateCharts()
    // 可选：ElMessage.error('获取监控数据失败')
  }
}

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
    
    const payload = {
      name: form.value.name,
      hostname: form.value.hostname,
      ip_address: form.value.ip_address,
      port: form.value.port,
      username: form.value.username,
      auth_type: form.value.auth_type,
      password: form.value.auth_type === 'password' ? form.value.password : undefined,
      ssh_key: form.value.auth_type === 'key' ? form.value.ssh_key : undefined,
      description: form.value.description,
    }
    
    if (dialogType.value === 'add') {
      const response = await axios.post('/api/clients', payload)
      if (response.data.status === 'success') {
      ElMessage.success('添加成功')
        dialogVisible.value = false
        
        ElMessage.success('服务器添加成功')
        
        fetchClients()
      }
    } else {
      const response = await axios.put(`/api/clients/${form.value.id}`, payload)
      if (response.data.status === 'success') {
      ElMessage.success('更新成功')
    dialogVisible.value = false
    fetchClients()
      }
    }
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
    const response = await axios.post(`/api/clients/${row.id}/status`)
    if (response.data.status === 'success') {
      ElMessage.success('获取信息成功')
      fetchClients()  // 刷新列表以更新信息
    }
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
    await fetchClientDetail(client.id);
    await nextTick();
    await initCharts();
    fetchMonitorData(client.id)
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
  disposeCharts()
  window.removeEventListener('resize', handleResize)
  // 恢复原来的错误处理器
  window.onerror = originalErrorHandler
})

// 关闭抽屉时清理
const handleDrawerClose = () => {
  disposeCharts()
  drawerVisible.value = false
  activeTab.value = 'basic'
}

// 刷新进程列表
const refreshProcessList = async () => {
  try {
    const response = await axios.get(`/api/clients/${currentClient.value.id}/processes`)
    if (response.data.status === 'success') {
      clientDetail.value.process_list = response.data.data
    }
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
    const response = await axios.get(`/api/clients/${currentClient.value.id}/logs`, {
      params: {
        lines: 100,
        level: logLevelFilter.value || 'ALL'
      }
    })
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

const multipleSelection = ref([])

// 分组/标签相关变量
const groupList = ref([])
const tagList = ref([])
const selectedGroup = ref('')
const selectedTag = ref('')

// 批量选择处理
const handleSelectionChange = (selection) => {
  multipleSelection.value = selection
}

// 批量删除
const handleBatchDelete = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning('请选择要删除的服务器')
      return
    }
  
  try {
    await ElMessageBox.confirm(`确定要删除选中的 ${multipleSelection.value.length} 台服务器吗？`, '批量删除', {
      type: 'warning'
    })
    
    const clientIds = multipleSelection.value.map(item => item.id)
    await axios.post('/api/clients/batch_delete', { client_ids: clientIds })
    
    ElMessage.success('批量删除成功')
    fetchClients()
    multipleSelection.value = []
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量删除失败')
    }
  }
}

// 批量分组对话框
const showBatchGroupDialog = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning('请选择要分组的服务器')
    return
  }
  
  // 分析当前选中服务器的分组情况
  const groupStats = {}
  multipleSelection.value.forEach(client => {
    const group = client.group || '未分组'
    groupStats[group] = (groupStats[group] || 0) + 1
  })
  
  const groupInfo = Object.entries(groupStats)
    .map(([group, count]) => `${group}: ${count}台`)
    .join('\n')
  
  try {
    const { value: groupName } = await ElMessageBox.prompt(
      `当前选中 ${multipleSelection.value.length} 台服务器\n\n分组分布：\n${groupInfo}\n\n请输入新的分组名称（留空则清空分组）：`, 
      '批量分组', 
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: '',
        inputPlaceholder: '请输入分组名称'
      }
    )
    
    const clientIds = multipleSelection.value.map(item => item.id)
    await axios.post('/api/clients/batch_group', { client_ids: clientIds, group: groupName || '' })
    
    ElMessage.success('批量分组成功')
    fetchClients()
    fetchGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量分组失败')
  }
}
}

// 批量打标签对话框
const showBatchTagDialog = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning('请选择要打标签的服务器')
    return
  }
  
  // 分析当前选中服务器的标签情况
  const tagStats = {}
  const allTags = new Set()
  
  multipleSelection.value.forEach(client => {
    if (client.tags) {
      const tags = client.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
      tags.forEach(tag => {
        tagStats[tag] = (tagStats[tag] || 0) + 1
        allTags.add(tag)
      })
    }
  })
  
  const tagInfo = Object.entries(tagStats)
    .map(([tag, count]) => `${tag}: ${count}台`)
    .join('\n')
  
  const currentTags = Array.from(allTags).join(', ')
  
  try {
    const { value: tags } = await ElMessageBox.prompt(
      `当前选中 ${multipleSelection.value.length} 台服务器\n\n现有标签分布：\n${tagInfo}\n\n请输入新标签（逗号分隔，留空则清空标签）：`, 
      '批量打标签', 
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: currentTags,
        inputPlaceholder: '请输入标签，多个标签用逗号分隔'
      }
    )
    
    const clientIds = multipleSelection.value.map(item => item.id)
    await axios.post('/api/clients/batch_tags', { client_ids: clientIds, tags: tags || '' })
    
    ElMessage.success('批量打标签成功')
    fetchClients()
    fetchTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('批量打标签失败')
    }
  }
}

// 获取所有分组
const fetchGroups = async () => {
  try {
    const response = await axios.get('/api/clients/groups')
    if (response.data.status === 'success') {
      groupList.value = response.data.data || []
    }
  } catch (error) {
    console.error('获取分组列表失败:', error)
  }
}

// 获取所有标签
const fetchTags = async () => {
  try {
    const response = await axios.get('/api/clients/tags')
    if (response.data.status === 'success') {
      tagList.value = response.data.data || []
    }
  } catch (error) {
    console.error('获取标签列表失败:', error)
  }
}

// 在组件挂载时获取分组和标签列表
onMounted(() => {
  fetchClients()
  fetchGroups()
  fetchTags()
})

// 切换架构图显示/隐藏
const showArchitecture = ref(false)
const toggleArchitecture = () => {
  showArchitecture.value = !showArchitecture.value
}
</script>

<style scoped>
.clients-page {
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  padding: 30px;
  margin-bottom: 24px;
  color: white;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-title {
  font-size: 28px;
  font-weight: 600;
  margin: 0;
  color: white;
}

.page-subtitle {
  font-size: 16px;
  opacity: 0.9;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 8px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.stats-section {
  margin-bottom: 24px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.stat-card {
  display: flex;
  justify-content: space-between;
  background: white;
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid #f0f0f0;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
}

.stat-icon.online {
  background: linear-gradient(135deg, #67C23A, #85ce61);
}

.stat-icon.offline {
  background: linear-gradient(135deg, #F56C6C, #f78989);
}

.stat-icon.running {
  background: linear-gradient(135deg, #409EFF, #66b1ff);
}

.stat-icon.pending {
  background: linear-gradient(135deg, #E6A23C, #ebb563);
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stat-value {
  font-size: 32px;
  font-weight: 700;
  color: #303133;
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  font-weight: 500;
}

.main-content {
  display: block;
}

.clients-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.header-left h3 {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  margin: 0;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.search-input {
  width: 240px;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
}

.table-container {
  padding: 0;
}

.clients-table {
  width: 100%;
}

.clients-table :deep(.el-table__header) {
  background: #fafafa;
}

.clients-table :deep(.el-table__header th) {
  background: #fafafa;
  color: #606266;
  font-weight: 600;
  border-bottom: 1px solid #ebeef5;
}

.clients-table :deep(.el-table__row) {
  transition: all 0.3s ease;
}

.server-info {
  display: flex;
  flex-direction: row;
  gap: 4px;
}

.server-name {
  font-size: 14px;
  font-weight: 600;
  color: #303133;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 500;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.online {
  background: #67C23A;
  box-shadow: 0 0 0 2px rgba(103, 194, 58, 0.2);
}

.status-dot.offline {
  background: #F56C6C;
  box-shadow: 0 0 0 2px rgba(245, 108, 108, 0.2);
}

.status-dot.error {
  background: #E6A23C;
  box-shadow: 0 0 0 2px rgba(230, 162, 60, 0.2);
}

.last-seen {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #909399;
}

.action-buttons {
  display: flex;
  gap: 8px;
  align-items: center;
}

.detail-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 12px;
}

/* 对话框样式 */
.client-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 8px 8px 0 0;
}

.client-dialog :deep(.el-dialog__title) {
  color: white;
  font-weight: 600;
}

.client-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white;
}

.client-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.client-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: #606266;
}

.client-form :deep(.el-input__wrapper) {
  border-radius: 6px;
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

.client-form :deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

.client-form :deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px #409eff inset;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid #f0f0f0;
  background: #fafafa;
}

/* 抽屉样式 */
.client-drawer :deep(.el-drawer__header) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 20px 24px;
  margin: 0;
}

.client-drawer :deep(.el-drawer__title) {
  color: white;
  font-weight: 600;
  font-size: 18px;
}

.client-drawer :deep(.el-drawer__headerbtn .el-drawer__close) {
  color: white;
}

.drawer-content {
  height: 100%;
  display: flex;
    flex-direction: column;
}

.detail-tabs {
  flex: 1;
  display: flex;
}

.detail-tabs :deep(.el-tabs__header) {
  background: #fafafa;
  margin: 0;
  padding: 0 24px;
  border-bottom: 1px solid #f0f0f0;
}

.detail-tabs :deep(.el-tabs__nav-wrap) {
  padding: 0;
}

.detail-tabs :deep(.el-tabs__item) {
  padding: 16px 24px;
  font-weight: 500;
  color: #606266;
  border-bottom: 2px solid transparent;
  transition: all 0.3s ease;
}

.detail-tabs :deep(.el-tabs__item.is-active) {
  color: #409eff;
  border-bottom-color: #409eff;
}

.detail-tabs :deep(.el-tabs__content) {
  flex: 1;
  padding: 0;
}

.detail-tabs :deep(.el-tab-pane) {
  height: 100%;
  padding: 24px;
  overflow-y: auto;
}

.detail-content, .monitor-content, .logs-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.info-card :deep(.el-card__header) {
  background: #fafafa;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.info-card :deep(.el-card__header span) {
  font-weight: 600;
  color: #303133;
  font-size: 16px;
}

.info-card :deep(.el-card__body) {
  padding: 20px;
}

.cpu-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
}

.cpu-item {
    display: flex;
    align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.cpu-cores {
  color: #6c757d;
  font-size: 14px;
      font-weight: 500;
}

.memory-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  }

.memory-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
  margin-top: 12px;
  }

.memory-details span {
  text-align: center;
  padding: 8px;
  background: #f8f9fa;
    border-radius: 4px;
  font-size: 14px;
  color: #6c757d;
}

.disk-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
  }

.disk-item {
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

.disk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.disk-mount {
  font-size: 14px;
  color: #6c757d;
  }

.disk-details {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 12px;
}

.disk-details span {
  text-align: center;
  padding: 6px;
  background: white;
  border-radius: 4px;
  font-size: 13px;
  color: #6c757d;
  }

.network-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 12px;
}

.nic-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
  flex-wrap: wrap;
}

.nic-ip, .nic-ip6, .nic-mac, .nic-mtu, .nic-status {
  font-size: 13px;
  color: #6c757d;
  padding: 2px 6px;
  background: white;
  border-radius: 3px;
}

/* 监控面板样式 */
.monitor-control-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 24px;
  flex-wrap: wrap;
}

.panel-section {
  display: flex;
  align-items: center;
  gap: 12px;
}

.section-label {
  font-weight: 600;
  color: #606266;
  white-space: nowrap;
}

.time-select {
  width: 140px;
}

.date-picker {
  width: 360px;
}

.refresh-group {
  display: flex;
  align-items: center;
  gap: 16px;
}

.refresh-button {
  display: flex;
  align-items: center;
  gap: 6px;
}

.auto-refresh-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.interval-select {
  width: 100px;
}

.chart-container {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  }

.chart-header h3 {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
  margin: 0;
  }

.chart {
  height: 300px;
    width: 100%;
  }

/* 日志面板样式 */
.logs-control-panel {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
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
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid #f0f0f0;
  overflow: hidden;
}

.logs-list :deep(.el-table) {
  font-size: 13px;
}

.logs-list :deep(.el-table__header th) {
  background: #fafafa;
  color: #606266;
  font-weight: 600;
  font-size: 13px;
}

/* 响应式设计 */
@media screen and (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media screen and (max-width: 768px) {
  .clients-page {
    padding: 12px;
  }
  
  .page-header {
    padding: 20px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .monitor-control-panel {
    flex-direction: column;
    align-items: stretch;
  }
  
  .panel-section {
    justify-content: space-between;
  }
  
  .search-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .search-input,
  .level-select {
    width: 100%;
  }
  
  .time-select,
  .date-picker {
    width: 100%;
}

  .memory-details,
  .disk-details {
    grid-template-columns: 1fr;
  }
  
  .cpu-info,
  .network-info {
    grid-template-columns: 1fr;
  }
}

/* 动画效果 */
.clients-card,
.info-card,
.chart-container,
.logs-control-panel,
.logs-list {
  animation: fadeInUp 0.6s ease-out;
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 滚动条样式 */
.detail-content::-webkit-scrollbar,
.monitor-content::-webkit-scrollbar,
.logs-content::-webkit-scrollbar {
  width: 6px;
}

.detail-content::-webkit-scrollbar-track,
.monitor-content::-webkit-scrollbar-track,
.logs-content::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.detail-content::-webkit-scrollbar-thumb,
.monitor-content::-webkit-scrollbar-thumb,
.logs-content::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.detail-content::-webkit-scrollbar-thumb:hover,
.monitor-content::-webkit-scrollbar-thumb:hover,
.logs-content::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

.server-name-link {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #409eff;
  font-weight: 600;
  font-size: 15px;
  border-radius: 4px;
  padding: 2px 6px;
  transition: background 0.2s, color 0.2s;
}
.server-name-link:hover {
  background: #e6f0fa;
  color: #1769aa;
  text-decoration: underline;
}
.server-link-icon {
  font-size: 16px;
  color: #409eff;
  transition: color 0.2s;
}
.server-name-link:hover .server-link-icon {
  color: #1769aa;
}

.new-tag {
  margin-left: 8px;
  font-size: 12px;
  font-weight: bold;
  background: #eaffea;
  color: #21ba45;
  border: 1px solid #b7e4c7;
  border-radius: 4px;
  padding: 0 6px;
  vertical-align: middle;
}

.architecture-section {
  margin-bottom: 24px;
}

.architecture-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid #f0f0f0;
}

.architecture-content {
  padding: 20px;
}

.architecture-diagram {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-radius: 12px;
  border: 1px solid #dee2e6;
}

.flow-step {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  flex: 1;
  max-width: 280px;
}

.step-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: white;
  font-size: 24px;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.step-content h4 {
  margin: 0 0 8px 0;
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.step-content p {
  margin: 0 0 12px 0;
  color: #606266;
  font-size: 14px;
  line-height: 1.5;
}

.step-content ul {
  display: inline-block;
  margin: 0;
  padding-left: 20px;
  text-align: left;
}

.step-content li {
  color: #606266;
  font-size: 13px;
  margin-bottom: 4px;
}

.flow-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #409eff;
  font-size: 24px;
  margin: 0 20px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.usage-guide {
  border-top: 1px solid #ebeef5;
  padding-top: 24px;
}

.usage-guide h4 {
  margin: 0 0 20px 0;
  color: #303133;
  font-size: 18px;
  font-weight: 600;
}

.guide-steps {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.guide-step {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
  transition: all 0.3s ease;
}

.guide-step:hover {
  background: #e9ecef;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.step-text strong {
  display: block;
  margin-bottom: 8px;
  color: #303133;
  font-size: 14px;
  font-weight: 600;
}

.step-text p {
  margin: 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

@media screen and (max-width: 768px) {
  .architecture-diagram {
    flex-direction: column;
    gap: 20px;
  }
  
  .flow-arrow {
    transform: rotate(90deg);
    margin: 10px 0;
  }
  
  .guide-steps {
    grid-template-columns: 1fr;
  }
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.toggle-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.guide-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.3s ease;
}

.guide-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 在style中添加动画 */
.fade-arch-enter-active, .fade-arch-leave-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}
.fade-arch-enter-from, .fade-arch-leave-to {
  opacity: 0;
}
.fade-arch-enter-to, .fade-arch-leave-from {
  opacity: 1;
}
</style> 