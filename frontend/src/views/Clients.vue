<template>
  <div class="clients-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">{{ $t('clients.pageTitle') }}</h1>
          <p class="page-subtitle">{{ $t('clients.pageSubtitle') }}</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="showAddDialog" class="action-btn">
            <el-icon>
              <Plus />
            </el-icon>
            {{ $t('clients.addSourceServer') }}
          </el-button>
          <el-button type="info" @click="toggleArchitecture" class="guide-btn"
            :title="showArchitecture ? $t('clients.hideProcessGuide') : $t('clients.showProcessGuide')">
            <el-icon>
              <View v-if="showArchitecture" />
              <Hide v-else />
            </el-icon>
            {{ $t('clients.processGuide') }}
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
              <h3>{{ $t('clients.architectureTitle') }}</h3>
              <el-tag type="info">{{ $t('clients.architectureSubtitle') }}</el-tag>
            </div>
          </template>
          <div class="architecture-content">
            <div class="architecture-diagram">
              <div class="flow-step">
                <div class="step-icon">
                  <el-icon>
                    <Monitor />
                  </el-icon>
                </div>
                <div class="step-content">
                  <h4>{{ $t('clients.sourceServer') }}</h4>
                  <p>{{ $t('clients.sourceServerDesc') }}</p>
                  <ul>
                    <li>{{ $t('clients.supportSystems') }}</li>
                    <li>{{ $t('clients.sshConnection') }}</li>
                    <li>{{ $t('clients.agentAutoCollect') }}</li>
                  </ul>
                </div>
              </div>

              <div class="flow-arrow">
                <el-icon>
                  <ArrowRight />
                </el-icon>
              </div>

              <div class="flow-step">
                <div class="step-icon">
                  <el-icon>
                    <Connection />
                  </el-icon>
                </div>
                <div class="step-content">
                  <h4>{{ $t('clients.syncProxy') }}</h4>
                  <p>{{ $t('clients.syncProxyDesc') }}</p>
                  <ul>
                    <li>{{ $t('clients.receiveSourceData') }}</li>
                    <li>{{ $t('clients.processDataFormat') }}</li>
                    <li>{{ $t('clients.forwardToTarget') }}</li>
                  </ul>
                </div>
              </div>

              <div class="flow-arrow">
                <el-icon>
                  <ArrowRight />
                </el-icon>
              </div>

              <div class="flow-step">
                <div class="step-icon">
                  <el-icon>
                    <FolderOpened />
                  </el-icon>
                </div>
                <div class="step-content">
                  <h4>{{ $t('clients.targetStorage') }}</h4>
                  <p>{{ $t('clients.targetStorageDesc') }}</p>
                  <ul>
                    <li>{{ $t('clients.nasStorage') }}</li>
                    <li>{{ $t('clients.obsStorage') }}</li>
                    <li>{{ $t('clients.nfsStorage') }}</li>
                    <li>{{ $t('clients.localStorage') }}</li>
                  </ul>
                </div>
              </div>
            </div>

            <div class="usage-guide">
              <h4>{{ $t('clients.usageGuide') }}</h4>
              <div class="guide-steps">
                <div class="guide-step">
                  <div class="step-number">1</div>
                  <div class="step-text">
                    <strong>{{ $t('clients.addSourceServerStep') }}</strong>
                    <p>{{ $t('clients.addSourceServerStepDesc') }}</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">2</div>
                  <div class="step-text">
                    <strong>{{ $t('clients.testConnection') }}</strong>
                    <p>{{ $t('clients.testConnectionDesc') }}</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">3</div>
                  <div class="step-text">
                    <strong>{{ $t('clients.installAgentStep') }}</strong>
                    <p>{{ $t('clients.installAgentStepDesc') }}</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">4</div>
                  <div class="step-text">
                    <strong>{{ $t('clients.configureSyncStep') }}</strong>
                    <p>{{ $t('clients.configureSyncStepDesc') }}</p>
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
            <el-icon>
              <Monitor />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.online }}</div>
            <div class="stat-label">{{ $t('clients.onlineServers') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon offline">
            <el-icon>
              <CircleClose />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.offline }}</div>
            <div class="stat-label">{{ $t('clients.offlineServers') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon running">
            <el-icon>
              <Connection />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.running }}</div>
            <div class="stat-label">{{ $t('clients.runningAgents') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon pending">
            <el-icon>
              <Clock />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats.pending }}</div>
            <div class="stat-label">{{ $t('clients.pendingAgents') }}</div>
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
              <h3>{{ $t('clients.clientList') }}</h3>
              <el-tag type="info" size="small">{{ clients?.length || 0 }}{{ $t('clients.clientsCount') }}</el-tag>
            </div>
            <div class="header-right">
              <!-- 分组/标签筛选与批量操作 -->
              <div class="filter-batch-bar" style="display: flex; align-items: center; gap: 16px;">
                <el-select v-model="selectedGroup" :placeholder="$t('clients.groupFilter')" clearable
                  style="width: 140px">
                  <el-option v-for="group in groupList" :key="group" :label="group" :value="group" />
                </el-select>
                <el-select v-model="selectedTag" :placeholder="$t('clients.tagFilter')" clearable style="width: 140px">
                  <el-option v-for="tag in tagList" :key="tag" :label="tag" :value="tag" />
                </el-select>
                <el-select v-model="statusFilter" :placeholder="$t('clients.statusFilter')" style="width: 120px"
                  @change="handleSearch" class="filter-select">
                  <el-option :label="$t('clients.all')" value="all" />
                  <el-option :label="$t('clients.online')" value="online" />
                  <el-option :label="$t('clients.offline')" value="offline" />
                  <el-option :label="$t('clients.agentInstalled')" value="agent_installed" />
                  <el-option :label="$t('clients.agentNotInstalled')" value="agent_not_installed" />
                </el-select>
                <el-button type="danger" :disabled="!(multipleSelection?.length)" @click="handleBatchDelete">{{
                  $t('clients.batchDelete') }}</el-button>
                <el-button type="primary" :disabled="!(multipleSelection?.length)" @click="showBatchGroupDialog">{{
                  $t('clients.batchGroup') }}</el-button>
                <el-button type="primary" :disabled="!(multipleSelection?.length)" @click="showBatchTagDialog">{{
                  $t('clients.batchTag') }}</el-button>
              </div>
              <el-input v-model="searchQuery" :placeholder="$t('clients.searchNameIp')" class="search-input" clearable>
                <template #prefix>
                  <el-icon>
                    <Search />
                  </el-icon>
                </template>
              </el-input>
              <el-button @click="fetchClients" class="refresh-btn">
                <el-icon>
                  <Refresh />
                </el-icon>
              </el-button>
            </div>
          </div>
        </template>

        <!-- 服务器表格 -->
        <div class="table-container">
          <el-table :data="filteredClients" :empty-text="$t('common.noData')" style="width: 100%" v-loading="loading"
            class="clients-table" @selection-change="handleSelectionChange">
            <el-table-column type="selection" width="50" />
            <el-table-column prop="name" :label="$t('clients.name')" min-width="150">
              <template #default="{ row }">
                <div class="server-info server-name-link" @click="showClientDetail(row)">
                  <el-icon class="server-link-icon">
                    <Monitor />
                  </el-icon>
                  <span>{{ row.name }}</span>
                  <el-tag v-if="isNewServer(row)" type="success" class="new-tag">NEW</el-tag>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="group" :label="$t('clients.group')" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.group">{{ row.group }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="tags" :label="$t('clients.tags')" width="140">
              <template #default="{ row }">
                <el-tag v-for="tag in (row.tags ? row.tags.split(',') : [])" :key="tag" type="info"
                  style="margin-right: 2px;">{{ tag }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ip_address" :label="$t('clients.ipAddress')" width="140" />
            <el-table-column prop="status" :label="$t('clients.status')" width="120">
              <template #default="{ row }">
                <div class="status-indicator">
                  <div class="status-dot" :class="row.status"></div>
                  <span>{{ getStatusText(row.status) }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="agent_status" :label="$t('clients.agentStatus')" width="120">
              <template #default="{ row }">
                <el-tag :type="getAgentStatusType(row.agent_status)" size="small">
                  {{ getAgentStatusText(row.agent_status) }}
                </el-tag>
              </template>
            </el-table-column>

            <el-table-column prop="os_type" :label="$t('clients.operatingSystem')" width="120" />
            <el-table-column prop="last_seen" :label="$t('clients.lastHeartbeat')" width="160">
              <template #default="{ row }">
                <div class="last-seen">
                  <el-icon>
                    <Clock />
                  </el-icon>
                  <span>{{ formatDate(row.last_seen) }}</span>
                </div>
              </template>
            </el-table-column>

            <el-table-column :label="$t('clients.actions')" width="200" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click.stop="showClientDetail(row)" class="detail-btn">
                    <el-icon>
                      <View />
                    </el-icon>
                    {{ $t('clients.details') }}
                  </el-button>
                  <el-dropdown trigger="click" @command="handleCommand">
                    <el-button size="small">
                      {{ $t('clients.more') }}<el-icon class="el-icon--right">
                        <ArrowDown />
                      </el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'edit', row }">
                          <el-icon>
                            <Edit />
                          </el-icon>{{ $t('clients.edit') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'test', row }">
                          <el-icon>
                            <Connection />
                          </el-icon>{{ $t('clients.testConnection') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'install', row }"
                          :disabled="row.status !== 'online' || row.agent_status === 'installed' || row.agent_status === 'running'">
                          <el-icon>
                            <Download />
                          </el-icon>{{ $t('clients.installAgent') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'uninstall', row }"
                          :disabled="row.agent_status === 'not_installed' || row.agent_status === 'installing'">
                          <el-icon>
                            <Remove />
                          </el-icon>{{ $t('clients.uninstallAgent') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'info', row }">
                          <el-icon>
                            <InfoFilled />
                          </el-icon>{{ $t('clients.getInfo') }}
                        </el-dropdown-item>
                        <el-dropdown-item divided :command="{ action: 'delete', row }">
                          <el-icon>
                            <Delete />
                          </el-icon>{{ $t('clients.delete') }}
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
    <el-dialog :title="dialogType === 'add' ? $t('clients.addClient') : $t('clients.editClient')"
      v-model="dialogVisible" width="600px" class="client-dialog" :close-on-click-modal="false">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="100px" class="client-form">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('clients.name')" prop="name">
              <el-input v-model="form.name" :placeholder="$t('clients.enterClientName')" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('clients.hostname')" prop="hostname">
              <el-input v-model="form.hostname" :placeholder="$t('clients.enterHostname')" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('clients.ipAddress')" prop="ip_address">
              <el-input v-model="form.ip_address" :placeholder="$t('clients.enterIpAddress')" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('clients.port')" prop="port">
              <el-input-number v-model="form.port" :min="1" :max="65535" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item :label="$t('clients.username')" prop="username">
              <el-input v-model="form.username" :placeholder="$t('clients.enterUsername')" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item :label="$t('clients.authType')" prop="auth_type">
              <el-radio-group v-model="form.auth_type">
                <el-radio :value="'password'">{{ $t('clients.passwordAuth') }}</el-radio>
                <el-radio :value="'key'">{{ $t('clients.keyAuth') }}</el-radio>
              </el-radio-group>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item v-if="form.auth_type === 'password'" :label="$t('clients.password')" prop="password">
          <el-input v-model="form.password" type="password" :placeholder="$t('clients.enterPassword')" show-password />
        </el-form-item>

        <el-form-item v-if="form.auth_type === 'key'" :label="$t('clients.sshKey')" prop="ssh_key">
          <el-input v-model="form.ssh_key" type="textarea" :rows="4" :placeholder="$t('clients.enterSshKey')" />
        </el-form-item>

        <el-form-item :label="$t('clients.description')">
          <el-input v-model="form.description" type="textarea" :rows="2"
            :placeholder="$t('clients.enterDescription')" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">{{ $t('clients.cancel') }}</el-button>
          <el-button type="primary" @click="handleSubmit">{{ $t('clients.confirm') }}</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 安装Agent对话框 -->
    <el-dialog :title="$t('clients.installAgent')" v-model="installDialogVisible" width="500px" class="install-dialog" :close-on-click-modal="false">
      <el-form :model="installForm" label-width="120px">
        <el-form-item :label="$t('clients.installPath')">
          <el-input v-model="installForm.install_path" :placeholder="$t('clients.defaultInstallPath')" />
        </el-form-item>
        <el-form-item :label="$t('clients.configParams')">
          <el-input v-model="installForm.config" type="textarea" :rows="4"
            :placeholder="$t('clients.enterJsonConfig')" />
        </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="installDialogVisible = false">{{ $t('clients.cancel') }}</el-button>
          <el-button type="primary" @click="confirmInstall">{{ $t('clients.startInstall') }}</el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 主机详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="$t('clients.clientDetails')" direction="rtl" size="70%"
      :before-close="handleDrawerClose" class="client-drawer">
      <div class="drawer-content">
        <el-tabs v-model="activeTab" class="detail-tabs">
          <!-- 基本信息标签页 -->
          <el-tab-pane :label="$t('clients.basicInfo')" name="basic">
            <div class="detail-content">
              <!-- 基本信息卡片 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>{{ $t('clients.basicInfo') }}</span>
                  </div>
                </template>
                <el-descriptions :column="2" border>
                  <el-descriptions-item :label="$t('clients.name')">
                    <el-tag type="info">{{ currentClient.name }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('clients.hostname')">
                    <el-tag type="info">{{ currentClient.hostname }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('clients.ipAddress')">
                    <el-tag type="success">{{ currentClient.ip_address }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('clients.operatingSystem')">
                    <el-tag type="warning">{{ clientDetail.os_type }}</el-tag>
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>

              <!-- CPU信息卡片 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>{{ $t('clients.cpuInfo') }}</span>
                  </div>
                </template>
                <div class="cpu-info">
                  <div v-for="(cpu, index) in clientDetail.cpu_info" :key="index" class="cpu-item">
                    <el-tag type="primary">{{ cpu.model }}</el-tag>
                    <span class="cpu-cores">{{ cpu.cores }}{{ $t('clients.cores') }}</span>
                  </div>
                </div>
              </el-card>

              <!-- 内存信息卡片 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>{{ $t('clients.memoryInfo') }}</span>
                  </div>
                </template>
                <div class="memory-info">
                  <el-progress
                    :percentage="(clientDetail.memory_info.used / clientDetail.memory_info.total * 100).toFixed(1)"
                    :status="getUsageStatus((clientDetail.memory_info.used / clientDetail.memory_info.total * 100))" />
                  <div class="memory-details">
                    <span>{{ $t('clients.totalMemory') }}: {{ formatSize(clientDetail.memory_info.total) }}</span>
                    <span>{{ $t('clients.usedMemory') }}: {{ formatSize(clientDetail.memory_info.used) }}</span>
                    <span>{{ $t('clients.availableMemory') }}: {{ formatSize(clientDetail.memory_info.total -
                      clientDetail.memory_info.used) }}</span>
                  </div>
                </div>
              </el-card>

              <!-- 磁盘信息卡片 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>{{ $t('clients.diskInfo') }}</span>
                  </div>
                </template>
                <div class="disk-info">
                  <div v-for="(disk, index) in clientDetail.disk_info" :key="index" class="disk-item">
                    <div class="disk-header">
                      <el-tag type="info">{{ disk.device }}</el-tag>
                      <span class="disk-mount">{{ disk.mount }}</span>
                    </div>
                    <el-progress :percentage="disk.usage" :status="getUsageStatus(disk.usage)" />
                    <div class="disk-details">
                      <span>{{ $t('clients.totalCapacity') }}: {{ formatSize(disk.total) }}</span>
                      <span>{{ $t('clients.usedCapacity') }}: {{ formatSize(disk.used) }}</span>
                      <span>{{ $t('clients.availableCapacity') }}: {{ formatSize(disk.total - disk.used) }}</span>
                    </div>
                  </div>
                </div>
              </el-card>

              <!-- 网卡信息卡片 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>{{ $t('clients.networkInfo') }}</span>
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
          <el-tab-pane :label="$t('clients.monitorData')" name="monitor">
            <div class="monitor-content">
              <!-- 监控控制面板 -->
              <div class="monitor-control-panel">
                <div class="panel-section time-range-selector">
                  <span class="section-label">{{ $t('clients.timeRange') }}</span>
                  <el-select v-model="timeRange" :placeholder="$t('clients.selectTimeRange')"
                    @change="handleTimeRangeChange" size="default" class="time-select">
                    <el-option :label="$t('clients.last10Minutes')" value="10m" />
                    <el-option :label="$t('clients.last15Minutes')" value="15m" />
                    <el-option :label="$t('clients.last1Hour')" value="1h" />
                    <el-option :label="$t('clients.last2Hours')" value="2h" />
                    <el-option :label="$t('clients.custom')" value="custom" />
                  </el-select>
                  <el-date-picker v-if="timeRange === 'custom'" v-model="customTimeRange" type="datetimerange"
                    :range-separator="$t('clients.to')" :start-placeholder="$t('clients.startTime')"
                    :end-placeholder="$t('clients.endTime')" size="default" class="date-picker" :default-time="[
                      new Date(2000, 1, 1, 0, 0, 0),
                      new Date(2000, 1, 1, 23, 59, 59),
                    ]" @change="handleCustomTimeRangeChange" />
                </div>
                <div class="panel-section refresh-controls">
                  <span class="section-label">{{ $t('clients.refreshSettings') }}</span>
                  <div class="refresh-group">
                    <el-button type="primary" :loading="refreshing" @click="handleManualRefresh" size="default"
                      class="refresh-button">
                      <el-icon>
                        <Refresh />
                      </el-icon>
                      <span>{{ $t('clients.refresh') }}</span>
                    </el-button>
                    <div class="auto-refresh-control">
                      <el-switch v-model="autoRefresh" :active-text="$t('clients.autoRefresh')" inactive-text=""
                        class="refresh-switch" @change="handleAutoRefreshChange" />
                      <el-select v-if="autoRefresh" v-model="refreshInterval"
                        :placeholder="$t('clients.refreshInterval')" @change="handleRefreshIntervalChange"
                        size="default" class="interval-select">
                        <el-option :label="$t('clients.3Seconds')" value="3" />
                        <el-option :label="$t('clients.5Seconds')" value="5" />
                        <el-option :label="$t('clients.10Seconds')" value="10" />
                        <el-option :label="$t('clients.30Seconds')" value="30" />
                        <el-option :label="$t('clients.1Minute')" value="60" />
                        <el-option :label="$t('clients.5Minutes')" value="300" />
                      </el-select>
                    </div>
                  </div>
                </div>
              </div>

              <!-- CPU使用率图表 -->
              <div class="chart-container">
                <div class="chart-header">
                  <h3>{{ $t('clients.cpuUsage') }}</h3>
                </div>
                <div class="chart" ref="cpuChart"></div>
              </div>

              <!-- 内存使用率图表 -->
              <div class="chart-container">
                <div class="chart-header">
                  <h3>{{ $t('clients.memoryUsage') }}</h3>
                </div>
                <div class="chart" ref="memoryChart"></div>
              </div>

              <!-- 磁盘使用率 -->
              <div class="chart-container">
                <div class="chart-header">
                  <h3>{{ $t('clients.diskUsage') }}</h3>
                </div>
                <el-table :data="clientDetail.disk_info" :empty-text="$t('common.noData')" style="width: 100%">
                  <el-table-column prop="device" :label="$t('clients.device')" />
                  <el-table-column prop="mount" :label="$t('clients.mountPoint')" />
                  <el-table-column prop="total" :label="$t('clients.totalCapacity')">
                    <template #default="{ row }">
                      {{ formatSize(row.total) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="used" :label="$t('clients.usedCapacity')">
                    <template #default="{ row }">
                      {{ formatSize(row.used) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="usage" :label="$t('clients.usageRate')">
                    <template #default="{ row }">
                      <el-progress :percentage="row.usage" :status="getUsageStatus(row.usage)" />
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- 网络流量 -->
              <div class="chart-container">
                <div class="chart-header">
                  <h3>{{ $t('clients.networkTraffic') }}</h3>
                </div>
                <div class="chart" ref="networkChart"></div>
              </div>

              <!-- 进程列表 -->
              <div class="chart-container">
                <div class="chart-header">
                  <h3>{{ $t('clients.processList') }}</h3>
                  <el-button type="primary" size="small" @click="refreshProcessList">{{ $t('clients.refresh')
                    }}</el-button>
                </div>
                <el-table :data="clientDetail.process_list" :empty-text="$t('common.noData')" style="width: 100%"
                  :max-height="300">
                  <el-table-column prop="pid" :label="$t('clients.pid')" width="80" />
                  <el-table-column prop="user" :label="$t('clients.user')" width="100" />
                  <el-table-column prop="cpu_percent" :label="$t('clients.cpuPercent')" width="100" />
                  <el-table-column prop="memory_percent" :label="$t('clients.memoryPercent')" width="100" />
                  <el-table-column prop="command" :label="$t('clients.command')" show-overflow-tooltip />
                </el-table>
              </div>
            </div>
          </el-tab-pane>

          <!-- 系统日志标签页 -->
          <el-tab-pane :label="$t('clients.systemLogs')" name="logs">
            <div class="logs-content">
              <!-- 日志控制面板 -->
              <div class="logs-control-panel">
                <div class="panel-section search-controls">
                  <el-input v-model="logSearchQuery" :placeholder="$t('clients.searchLogs')" clearable
                    @clear="handleLogSearch" @input="handleLogSearch" class="search-input">
                    <template #prefix>
                      <el-icon>
                        <Search />
                      </el-icon>
                    </template>
                  </el-input>
                  <el-select v-model="logLevelFilter" :placeholder="$t('clients.logLevel')" clearable
                    @change="handleLogSearch" class="level-select">
                    <el-option :label="$t('clients.all')" value="" />
                    <el-option :label="$t('clients.debug')" value="DEBUG" />
                    <el-option :label="$t('clients.info')" value="INFO" />
                    <el-option :label="$t('clients.warning')" value="WARNING" />
                    <el-option :label="$t('clients.error')" value="ERROR" />
                    <el-option :label="$t('clients.critical')" value="CRITICAL" />
                  </el-select>
                  <el-button type="primary" :loading="refreshingLogs" @click="handleManualLogRefresh"
                    class="refresh-button">
                    <el-icon>
                      <Refresh />
                    </el-icon>
                    <span>{{ $t('clients.refresh') }}</span>
                  </el-button>
                  <el-switch v-model="autoRefreshLogs" :active-text="$t('clients.autoRefresh')" inactive-text=""
                    class="refresh-switch" @change="handleAutoLogRefreshChange" />
                  <el-select v-if="autoRefreshLogs" v-model="logRefreshInterval"
                    :placeholder="$t('clients.refreshInterval')" @change="handleLogRefreshIntervalChange"
                    class="interval-select">
                    <el-option :label="$t('clients.3Seconds')" value="3" />
                    <el-option :label="$t('clients.5Seconds')" value="5" />
                    <el-option :label="$t('clients.10Seconds')" value="10" />
                    <el-option :label="$t('clients.30Seconds')" value="30" />
                  </el-select>
                </div>
              </div>

              <!-- 日志列表 -->
              <div class="logs-list">
                <el-table :data="filteredLogs" :empty-text="$t('common.noData')" style="width: 100%"
                  height="calc(100vh - 300px)" v-loading="loadingLogs">
                  <el-table-column prop="timestamp" :label="$t('clients.timestamp')" width="180">
                    <template #default="{ row }">
                      {{ row.timestamp }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="level" :label="$t('clients.level')" width="100">
                    <template #default="{ row }">
                      <el-tag :type="getLogLevelType(row.level)">
                        {{ row.level }}
                      </el-tag>
                    </template>
                  </el-table-column>
                  <el-table-column prop="module" :label="$t('clients.module')" width="150" />
                  <el-table-column prop="message" :label="$t('clients.message')" show-overflow-tooltip />
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
import { useI18n } from 'vue-i18n'
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
import axios from '@/utils/axios.mjs'

const { t } = useI18n()

// 基础数据
const clients = ref([])
const loading = ref(false)
const statusFilter = ref('all')
const searchQuery = ref('')
const handleSearch = () => { }

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
    { required: true, message: t('clients.enterName'), trigger: 'blur' }
  ],
  hostname: [
    { required: false, message: t('clients.enterServerHostname'), trigger: 'blur' }
  ],
  ip_address: [
    { required: true, message: t('clients.enterServerAddress'), trigger: 'blur' }
  ],
  port: [
    { required: true, message: t('clients.enterSshPort'), trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: t('clients.portRangeError'), trigger: 'blur' }
  ],
  username: [
    { required: true, message: t('clients.enterUsername'), trigger: 'blur' }
  ],
  auth_type: [
    { required: true, message: t('clients.selectAuthType'), trigger: 'change' }
  ],
  password: [
    { required: true, message: t('clients.enterPassword'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (form.value.auth_type === 'password' && !value) {
          callback(new Error(t('clients.passwordRequired')))
        } else {
          callback()
        }
      }, trigger: 'blur'
    }
  ],
  ssh_key: [
    { required: true, message: t('clients.enterSshKey'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (form.value.auth_type === 'key' && !value) {
          callback(new Error(t('clients.sshKeyRequired')))
        } else {
          callback()
        }
      }, trigger: 'blur'
    }
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
window.onerror = function (message, source, lineno, colno, error) {
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
    const response = await axios.get('/clients')
    const data = response.data.data
    clients.value = Array.isArray(data) ? data : []
  } catch (error) {
    clients.value = []
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return t('clients.neverOnline')
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
      return t('clients.online')
    case 'offline':
      return t('clients.offline')
    case 'error':
      return t('clients.error')
    default:
      return t('clients.unknown')
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
      return t('clients.running')
    case 'installing':
      return t('clients.installing')
    case 'not_installed':
      return t('clients.notInstalled')
    case 'uninstall_error':
      return t('clients.uninstallError')
    case 'install_error':
      return t('clients.installError')
    case 'online':
      return t('clients.online')
    case 'offline':
      return t('clients.offline')
    default:
      return t('clients.unknown')
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
      const response = await axios.post('/clients', payload)
      if (response.data.status === 'success') {
        ElMessage.success(t('clients.addSuccess'))
        dialogVisible.value = false

        ElMessage.success(t('clients.addSuccess'))

        fetchClients()
      }
    } else {
      const response = await axios.put(`/clients/${form.value.id}`, payload)
      if (response.data.status === 'success') {
        ElMessage.success(t('clients.updateSuccess'))
        dialogVisible.value = false
        fetchClients()
      }
    }
  } catch (error) {
    if (error.response) {
      // 错误处理已经在拦截器中完成
    } else if (error.message) {
      // 表单验证错误
      ElMessage.error(t('clients.formValidationError'))
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
      ElMessage.error(t('clients.noClientSelected'))
      return
    }
    await axios.post(`/clients/${currentClient.value.id}/install`, installForm.value)
    ElMessage.success(t('clients.startInstallAgent'))
    installDialogVisible.value = false
    fetchClients()
  } catch (error) {
    // 错误处理已经在拦截器中完成
  }
}

// 卸载Agent
const uninstallAgent = async (row) => {
  try {
    await ElMessageBox.confirm(t('clients.confirmUninstallAgent'), t('clients.tip'), {
      type: 'warning'
    })
    await axios.post(`/clients/${row.id}/uninstall`)
    ElMessage.success(t('clients.startUninstallAgent'))
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
    await ElMessageBox.confirm(t('clients.confirmDeleteClient'), t('clients.tip'), {
      type: 'warning'
    })
    await axios.delete(`/clients/${row.id}`)
    ElMessage.success(t('clients.deleteSuccess'))
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
    const response = await axios.post(`/clients/${row.id}/test-connection`)
    if (response.data.status === 'success') {
      ElMessage.success(t('clients.connectionTestSuccess'))
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
    const response = await axios.post(`/clients/${row.id}/status`)
    if (response.data.status === 'success') {
      ElMessage.success(t('clients.getInfoSuccess'))
      fetchClients()  // 刷新列表以更新信息
    }
  } catch (error) {
    ElMessage.error(t('clients.getInfoFailed'))
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
    console.error(t('clients.errorShowingClientDetail'), error);
    ElMessage.error(t('clients.loadClientDetailFailed'));
  }
};

// 获取主机详情
const fetchClientDetail = async (clientId) => {
  try {
    const response = await axios.get(`/api/clients/${clientId}/detail`)
    clientDetail.value = response.data.data
    clientDetail.value.os_type = response.data.data.os_type
  } catch (error) {
    ElMessage.error(t('clients.getHostDetailFailed'))
  }
}

// 初始化图表
const initCharts = async () => {
  if (!currentClient.value?.id) {
    console.warn(t('clients.noClientSelected'))
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
          text: t('clients.cpuUsage'),
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
                ${t('clients.cpuUsage')}: ${usage}%
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
          name: t('clients.usagePercent'),
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
          name: t('clients.cpuUsage'),
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
          text: t('clients.memoryUsage'),
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
                ${t('clients.memoryUsage')}: ${usage}%
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
          name: t('clients.usagePercent'),
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
          text: t('clients.networkTraffic'),
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
                ${t('clients.received')}: ${formatSize(params[0].value[1])}/s
              </div>
              <div style="margin-top: 5px">
                <span style="display:inline-block;margin-right:5px;border-radius:50%;width:10px;height:10px;background-color:${params[1].color};"></span>
                ${t('clients.sent')}: ${formatSize(params[1].value[1])}/s
              </div>
            `;
          }
        },
        legend: {
          data: [t('clients.received'), t('clients.sent')],
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
          name: t('clients.trafficPerSecond'),
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
            name: t('clients.received'),
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
            name: t('clients.sent'),
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
    console.error(t('clients.initChartFailed'), error)
    ElMessage.error(t('clients.initChartFailed'))
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
    console.error(t('clients.loadHistoryDataFailed'), error)
    ElMessage.error(t('clients.loadHistoryDataFailed'))
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
      console.warn(t('clients.chartResizeFailed'), error)
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
    console.warn(t('clients.destroyChartFailed'), error)
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
    ElMessage.error(t('clients.getProcessListFailed'))
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
    console.error(t('clients.getLogsFailed'), error)
    ElMessage.error(t('clients.getLogsFailed'))
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
    ElMessage.warning(t('clients.selectServersToDelete'))
    return
  }

  try {
    await ElMessageBox.confirm(t('clients.confirmBatchDelete', { count: multipleSelection.value.length }), t('clients.batchDelete'), {
      type: 'warning'
    })

    const clientIds = multipleSelection.value.map(item => item.id)
    await axios.post('/clients/batch_delete', { client_ids: clientIds })

    ElMessage.success(t('clients.batchDeleteSuccess'))
    fetchClients()
    multipleSelection.value = []
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('clients.batchDeleteFailed'))
    }
  }
}

// 批量分组对话框
const showBatchGroupDialog = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning(t('clients.selectServersToGroup'))
    return
  }

  // 分析当前选中服务器的分组情况
  const groupStats = {}
  multipleSelection.value.forEach(client => {
    const group = client.group || t('clients.ungrouped')
    groupStats[group] = (groupStats[group] || 0) + 1
  })

  const groupInfo = Object.entries(groupStats)
    .map(([group, count]) => `${group}: ${count}${t('clients.servers')}`)
    .join('\n')

  try {
    const { value: groupName } = await ElMessageBox.prompt(
      t('clients.batchGroupPrompt', {
        count: multipleSelection.value.length,
        groupInfo: groupInfo
      }),
      t('clients.batchGroup'),
      {
        confirmButtonText: t('clients.confirm'),
        cancelButtonText: t('clients.cancel'),
        inputValue: '',
        inputPlaceholder: t('clients.enterGroupName')
      }
    )

    const clientIds = multipleSelection.value.map(item => item.id)
    await axios.post('/clients/batch_group', { client_ids: clientIds, group: groupName || '' })

    ElMessage.success(t('clients.batchGroupSuccess'))
    fetchClients()
    fetchGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('clients.batchGroupFailed'))
    }
  }
}

// 批量打标签对话框
const showBatchTagDialog = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning(t('clients.selectServersToTag'))
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
    .map(([tag, count]) => `${tag}: ${count}${t('clients.servers')}`)
    .join('\n')

  const currentTags = Array.from(allTags).join(', ')

  try {
    const { value: tags } = await ElMessageBox.prompt(
      t('clients.batchTagPrompt', {
        count: multipleSelection.value.length,
        tagInfo: tagInfo
      }),
      t('clients.batchTag'),
      {
        confirmButtonText: t('clients.confirm'),
        cancelButtonText: t('clients.cancel'),
        inputValue: currentTags,
        inputPlaceholder: t('clients.enterTagsCommaSeparated')
      }
    )

    const clientIds = multipleSelection.value.map(item => item.id)
    await axios.post('/clients/batch_tags', { client_ids: clientIds, tags: tags || '' })

    ElMessage.success(t('clients.batchTagSuccess'))
    fetchClients()
    fetchTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('clients.batchTagFailed'))
    }
  }
}

// 获取所有分组
const fetchGroups = async () => {
  try {
    const response = await axios.get('/clients/groups')
    if (response.data.status === 'success') {
      groupList.value = response.data.data || []
    }
  } catch (error) {
    console.error(t('clients.getGroupsFailed'), error)
  }
}

// 获取所有标签
const fetchTags = async () => {
  try {
    const response = await axios.get('/clients/tags')
    if (response.data.status === 'success') {
      tagList.value = response.data.data || []
    }
  } catch (error) {
    console.error(t('clients.getTagsFailed'), error)
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
  background: var(--card-bg);
  border-radius: 12px;
  padding: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
  border: 1px solid var(--border-color);
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
  color: var(--text-color);
  line-height: 1;
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  font-weight: 500;
}

.main-content {
  display: block;
}

.clients-card {
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: var(--bg-secondary);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.header-left h3 {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
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
  background: var(--bg-secondary);
}

.clients-table :deep(.el-table__header th) {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
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
  color: var(--text-color);
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
  color: var(--text-secondary);
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
  background: var(--card-bg);
  color: var(--text-color);
  border-radius: 8px 8px 0 0;
  border-bottom: 1px solid var(--border-color);
}

.client-dialog :deep(.el-dialog__title) {
  color: var(--text-color);
  font-weight: 600;
}

:deep(.el-dialog__title) {
  color: var(--text-color) !important;
}

.client-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: var(--text-color);
}

.client-dialog :deep(.el-dialog__body) {
  padding: 24px;
}

.client-form :deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-secondary);
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

.client-form :deep(.el-textarea__inner) {
  box-shadow: 0 0 0 1px var(--border-color) inset !important;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 24px;
  border-top: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

/* 抽屉样式 */
.client-drawer :deep(.el-drawer__header) {
  background: var(--card-bg);
  color: var(--text-color);
  padding: 20px 24px;
  margin: 0;
  border-bottom: 1px solid var(--border-color);
}

.client-drawer :deep(.el-drawer__title) {
  color: var(--text-color);
  font-weight: 600;
  font-size: 18px;
}

.client-drawer :deep(.el-drawer__headerbtn .el-drawer__close) {
  color: var(--text-color);
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
  background: var(--bg-secondary);
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
  color: var(--text-secondary);
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

.detail-content,
.monitor-content,
.logs-content {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.info-card {
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.info-card :deep(.el-card__header) {
  background: var(--bg-secondary);
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.info-card :deep(.el-card__header span) {
  font-weight: 600;
  color: var(--text-color);
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
  background: var(--bg-secondary);
  border-radius: 6px;
  border: 1px solid var(--border-color);
}

.cpu-cores {
  color: var(--text-secondary);
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
  background: var(--bg-secondary);
  border-radius: 4px;
  font-size: 14px;
  color: var(--text-secondary);
}

.disk-info {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.disk-item {
  padding: 16px;
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
}

.disk-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.disk-mount {
  font-size: 14px;
  color: var(--text-secondary);
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
  background: var(--card-bg);
  border-radius: 4px;
  font-size: 13px;
  color: var(--text-secondary);
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
  padding: 8px 12px;
  background: var(--bg-secondary);
  border-radius: 6px;
  min-width: 300px;
  border: 1px solid var(--border-color);
  flex-wrap: wrap;
}

.nic-ip,
.nic-ip6,
.nic-mac,
.nic-mtu,
.nic-status {
  font-size: 13px;
  color: var(--text-secondary);
  padding: 2px 6px;
  background: var(--card-bg);
  border-radius: 3px;
}

/* 监控面板样式 */
.monitor-control-panel {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
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
  color: var(--text-secondary);
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
  background: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
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
  color: var(--text-color);
  margin: 0;
}

.chart {
  height: 300px;
  width: 100%;
}

/* 日志面板样式 */
.logs-control-panel {
  background: var(--card-bg);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
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
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.logs-list :deep(.el-table) {
  font-size: 13px;
}

.logs-list :deep(.el-table__header th) {
  background: var(--bg-secondary);
  color: var(--text-secondary);
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
  background: var(--card-bg);
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
  border: 1px solid var(--border-color);
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
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
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
  background: var(--bg-secondary);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 16px;
  color: #409eff;
  font-size: 24px;
  box-shadow: var(--card-shadow);
  border: 2px solid var(--border-color);
}

.step-content h4 {
  margin: 0 0 8px 0;
  color: var(--text-color);
  font-size: 16px;
  font-weight: 600;
}

.step-content p {
  margin: 0 0 12px 0;
  color: var(--text-secondary);
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
  color: var(--text-secondary);
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

  0%,
  100% {
    opacity: 1;
  }

  50% {
    opacity: 0.6;
  }
}

.usage-guide {
  border-top: 1px solid var(--border-color);
  padding-top: 24px;
}

.usage-guide h4 {
  margin: 0 0 20px 0;
  color: var(--text-color);
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
  background: var(--bg-secondary);
  border-radius: 8px;
  border: 1px solid var(--border-color);
  transition: all 0.3s ease;
}

.guide-step:hover {
  background: var(--border-color);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.step-number {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--card-bg);
  color: var(--text-color);
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
  color: var(--text-color);
  font-size: 14px;
  font-weight: 600;
}

.step-text p {
  margin: 0;
  color: var(--text-secondary);
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
.fade-arch-enter-active,
.fade-arch-leave-active {
  transition: opacity 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-arch-enter-from,
.fade-arch-leave-to {
  opacity: 0;
}

.fade-arch-enter-to,
.fade-arch-leave-from {
  opacity: 1;
}
</style>