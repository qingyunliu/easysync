<template>
  <div class="nodes-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="header-left">
          <h1 class="page-title">{{ $t('nodes.pageTitle') }}</h1>
          <p class="page-subtitle">{{ $t('nodes.pageSubtitle') }}</p>
        </div>
        <div class="header-actions">
          <el-button type="primary" @click="showAddDialog" class="action-btn">
            <el-icon>
              <Plus />
            </el-icon>
            {{ $t('nodes.addProxyNode') }}
          </el-button>
          <el-button type="info" @click="toggleArchitecture" class="guide-btn"
            :title="showArchitecture ? $t('nodes.hideProcessGuide') : $t('nodes.showProcessGuide')">
            <el-icon>
              <View v-if="showArchitecture" />
              <Hide v-else />
            </el-icon>
            {{ $t('nodes.processGuide') }}
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
              <div class="header-left">
                <h3>{{ $t('nodes.architectureTitle') }}</h3>
                <el-tag type="info">{{ $t('nodes.architectureSubtitle') }}</el-tag>
              </div>
            </div>
          </template>
          <div class="architecture-content">
            <div class="architecture-central-diagram">
              <div class="storage-side">
                <div class="storage-icon">
                  <el-icon>
                    <FolderOpened />
                  </el-icon>
                </div>
                <div class="storage-label">{{ $t('nodes.storageResourceA') }}<br />({{ $t('nodes.storageTypes') }})
                </div>
              </div>
              <div class="sync-arrows">
                <el-icon class="arrow-left">
                  <ArrowLeft />
                </el-icon>
                <el-icon class="arrow-right">
                  <ArrowRight />
                </el-icon>
              </div>
              <div class="proxy-center">
                <div class="proxy-icon">
                  <el-icon>
                    <Connection />
                  </el-icon>
                </div>
                <div class="proxy-label">{{ $t('nodes.syncProxyNode') }}<br />(SyncProxy)</div>
                <div class="proxy-desc">{{ $t('nodes.proxyDescription') }}<br />{{ $t('nodes.proxyFeatures') }}</div>
              </div>
              <div class="sync-arrows">
                <el-icon class="arrow-left">
                  <ArrowLeft />
                </el-icon>
                <el-icon class="arrow-right">
                  <ArrowRight />
                </el-icon>
              </div>
              <div class="storage-side">
                <div class="storage-icon">
                  <el-icon>
                    <FolderOpened />
                  </el-icon>
                </div>
                <div class="storage-label">{{ $t('nodes.storageResourceB') }}<br />({{ $t('nodes.storageTypes') }})
                </div>
              </div>
            </div>
            <div class="central-arch-notes">
              <el-alert type="info" show-icon :closable="false" style="margin-bottom: 18px;">
                <template #title>
                  <strong>{{ $t('nodes.description') }}：</strong> {{ $t('nodes.architectureDescription') }}
                </template>
              </el-alert>
            </div>
            <div class="usage-guide">
              <h4>{{ $t('nodes.usageGuide') }}</h4>
              <div class="guide-steps">
                <div class="guide-step">
                  <div class="step-number">1</div>
                  <div class="step-content">
                    <strong>{{ $t('nodes.step1Title') }}</strong>
                    <p>{{ $t('nodes.step1Description') }}</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">2</div>
                  <div class="step-content">
                    <strong>{{ $t('nodes.step2Title') }}</strong>
                    <p>{{ $t('nodes.step2Description') }}</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">3</div>
                  <div class="step-content">
                    <strong>{{ $t('nodes.step3Title') }}</strong>
                    <p>{{ $t('nodes.step3Description') }}</p>
                  </div>
                </div>
                <div class="guide-step">
                  <div class="step-number">4</div>
                  <div class="step-content">
                    <strong>{{ $t('nodes.step4Title') }}</strong>
                    <p>{{ $t('nodes.step4Description') }}</p>
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
            <div class="stat-value">{{ stats?.online || "0" }} </div>
            <div class="stat-label">{{ $t('nodes.onlineServers') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon offline">
            <el-icon>
              <CircleClose />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats?.offline || "0" }} </div>
            <div class="stat-label">{{ $t('nodes.offlineServers') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon running">
            <el-icon>
              <Connection />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats?.running || "0" }} </div>
            <div class="stat-label">{{ $t('nodes.runningAgents') }}</div>
          </div>
        </div>
        <div class="stat-card">
          <div class="stat-icon pending">
            <el-icon>
              <Clock />
            </el-icon>
          </div>
          <div class="stat-content">
            <div class="stat-value">{{ stats?.pending || "0" }} </div>
            <div class="stat-label">{{ $t('nodes.pendingAgents') }}</div>
          </div>
        </div>
      </div>
    </div>
    <div class="nodes-container">
      <el-card class="nodes-card" shadow="never">
        <template #header>
          <div class="card-header">
            <div class="header-left">
              <h3>{{ $t('nodes.nodeList') }}</h3>
              <el-tag type="info" size="small">{{ nodes.length }}{{ $t('nodes.nodesCount') }}</el-tag>
            </div>
            <div class="header-right">
              <div class="header">
                <div class="header-actions">
                  <el-select v-model="selectedGroup" :placeholder="$t('nodes.groupFilter')" clearable
                    style="width: 120px">
                    <el-option v-for="group in groupList" :key="group" :label="group" :value="group" />
                  </el-select>
                  <el-select v-model="selectedTag" :placeholder="$t('nodes.tagFilter')" clearable style="width: 120px">
                    <el-option v-for="tag in tagList" :key="tag" :label="tag" :value="tag" />
                  </el-select>
                  <el-select v-model="statusFilter" :placeholder="$t('nodes.statusFilter')" style="width: 120px"
                    @change="handleSearch" class="filter-select">
                    <el-option :label="$t('nodes.all')" value="all" />
                    <el-option :label="$t('nodes.online')" value="online" />
                    <el-option :label="$t('nodes.offline')" value="offline" />
                    <el-option :label="$t('nodes.agentInstalled')" value="agent_installed" />
                    <el-option :label="$t('nodes.agentNotInstalled')" value="agent_not_installed" />
                  </el-select>
                  <el-button type="danger" :disabled="!multipleSelection.length" @click="handleBatchDelete">{{
                    $t('nodes.batchDelete') }}</el-button>
                  <el-button type="primary" :disabled="!multipleSelection.length" @click="showBatchGroupDialog">{{
                    $t('nodes.batchGroup') }}</el-button>
                  <el-button type="primary" :disabled="!multipleSelection.length" @click="showBatchTagDialog">{{
                    $t('nodes.batchTag') }}</el-button>
                </div>
              </div>
              <el-input v-model="searchQuery" :placeholder="$t('nodes.searchNameIp')" class="search-input" clearable
                @input="handleSearch">
                <template #prefix>
                  <el-icon>
                    <Search />
                  </el-icon>
                </template>
              </el-input>
              <el-button @click="fetchNodes" class="refresh-btn">
                <el-icon>
                  <Refresh />
                </el-icon>
              </el-button>
            </div>
          </div>
        </template>
        <div class="table-container">
          <el-table :data="filteredNodes" v-loading="loading" @selection-change="handleSelectionChange"
            style="width: 100%" class="nodes-table">
            <el-table-column type="selection" width="55" />
            <el-table-column prop="name" :label="$t('nodes.name')" min-width="120">
              <template #default="{ row }">
                <div class="server-info server-name-link" @click="handleNameClick(row)">
                  <el-icon class="server-link-icon">
                    <Monitor />
                  </el-icon>
                  <span>{{ row.name }}</span>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="group" :label="$t('nodes.group')" width="100">
              <template #default="{ row }">
                <el-tag v-if="row.group">{{ row.group }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="tags" :label="$t('nodes.tags')" width="140">
              <template #default="{ row }">
                <el-tag v-for="tag in (row.tags ? row.tags.split(',') : [])" :key="tag" type="info"
                  style="margin-right: 2px;">{{ tag }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ipaddress" :label="$t('nodes.ipAddress')" min-width="120" />
            <el-table-column prop="username" :label="$t('nodes.username')" min-width="120" />
            <el-table-column prop="port" :label="$t('nodes.port')" min-width="80" />
            <el-table-column prop="status" :label="$t('nodes.status')" min-width="100">
              <template #default="{ row }">
                <el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="agent_status" :label="$t('nodes.agentStatus')" min-width="120">
              <template #default="{ row }">
                <el-tag :type="getAgentStatusType(row.agent_status)">{{ getAgentStatusText(row.agent_status) }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="last_heartbeat" :label="$t('nodes.lastHeartbeat')" min-width="160">
              <template #default="{ row }">
                {{ formatDate(row.last_heartbeat) }}
              </template>
            </el-table-column>
            <el-table-column prop="description" :label="$t('nodes.description')" min-width="120" />
            <el-table-column :label="$t('nodes.actions')" min-width="200" fixed="right">
              <template #default="{ row }">
                <div class="action-buttons">
                  <el-button type="primary" size="small" @click.stop="handleNameClick(row)" class="detail-btn">
                    <el-icon>
                      <View />
                    </el-icon>
                    {{ $t('nodes.details') }}
                  </el-button>
                  <el-dropdown trigger="click" @command="handleNodeCommand">
                    <el-button size="small">
                      {{ $t('nodes.more') }}<el-icon class="el-icon--right">
                        <ArrowDown />
                      </el-icon>
                    </el-button>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item :command="{ action: 'edit', row }">
                          <el-icon>
                            <Edit />
                          </el-icon>{{ $t('nodes.edit') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'test', row }">
                          <el-icon>
                            <Connection />
                          </el-icon>{{ $t('nodes.testConnection') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'install', row }" :disabled="row.status === 'offline'">
                          <el-icon>
                            <Download />
                          </el-icon>{{ $t('nodes.installAgent') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'uninstall', row }" :disabled="row.status === 'offline'">
                          <el-icon>
                            <Remove />
                          </el-icon>{{ $t('nodes.uninstallAgent') }}
                        </el-dropdown-item>
                        <el-dropdown-item :command="{ action: 'info', row }" :disabled="row.status === 'offline'">
                          <el-icon>
                            <InfoFilled />
                          </el-icon>{{ $t('nodes.getInfo') }}
                        </el-dropdown-item>
                        <el-dropdown-item divided :command="{ action: 'delete', row }">
                          <el-icon>
                            <Delete />
                          </el-icon>{{ $t('nodes.delete') }}
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
      <!-- 节点添加/编辑弹窗 -->
      <el-dialog :title="dialogType === 'add' ? $t('nodes.addNode') : $t('nodes.editNode')" v-model="dialogVisible"
        width="500px">
        <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
          <el-form-item :label="$t('nodes.name')" prop="name"><el-input v-model="form.name"
              :placeholder="$t('nodes.enterNodeName')" /></el-form-item>
          <el-form-item :label="$t('nodes.ipAddress')" prop="ipaddress"><el-input v-model="form.ipaddress"
              :placeholder="$t('nodes.enterIpAddress')" /></el-form-item>
          <el-form-item :label="$t('nodes.username')" prop="username"><el-input v-model="form.username"
              :placeholder="$t('nodes.enterUsername')" /></el-form-item>
          <el-form-item :label="$t('nodes.port')" prop="port"><el-input-number v-model="form.port" :min="1"
              :max="65535" /></el-form-item>
          <el-form-item :label="$t('nodes.authType')" prop="auth_type">
            <el-radio-group v-model="form.auth_type">
              <el-radio :value="'password'">{{ $t('nodes.passwordAuth') }}</el-radio>
              <el-radio :value="'key'">{{ $t('nodes.keyAuth') }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item v-if="form.auth_type === 'password'" :label="$t('nodes.password')" prop="password"><el-input
              v-model="form.password" type="password" :placeholder="$t('nodes.enterPassword')"
              show-password /></el-form-item>
          <el-form-item v-if="form.auth_type === 'key'" :label="$t('nodes.sshKey')" prop="ssh_key"><el-input
              v-model="form.ssh_key" type="textarea" :rows="4" :placeholder="$t('nodes.enterSshKey')" /></el-form-item>
          <el-form-item :label="$t('nodes.description')"><el-input v-model="form.description" type="textarea" :rows="2"
              :placeholder="$t('nodes.enterDescription')" /></el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="dialogVisible = false">{{ $t('nodes.cancel') }}</el-button>
            <el-button type="primary" @click="handleSubmit">{{ $t('nodes.confirm') }}</el-button>
          </span>
        </template>
      </el-dialog>
      <!-- 安装/卸载Agent弹窗 -->
      <el-dialog :title="$t('nodes.installUninstallAgent')" v-model="installDialogVisible" width="500px">
        <el-form :model="installForm" label-width="120px">
          <el-form-item :label="$t('nodes.installPath')"><el-input v-model="installForm.install_path"
              placeholder="/opt/easysync/proxy" /></el-form-item>
          <el-form-item :label="$t('nodes.serverIp')" required>
            <el-input v-model="installForm.server_ip" :placeholder="$t('nodes.serverIpPlaceholder')" />
          </el-form-item>
          <el-form-item :label="$t('nodes.serverPort')" required>
            <el-input-number v-model="installForm.server_port" :min="1" :max="65535" :placeholder="$t('nodes.serverPortPlaceholder')" style="width: 100%" />
          </el-form-item>
          <el-form-item :label="$t('nodes.configParams')"><el-input v-model="installForm.config" type="textarea"
              :rows="4" :placeholder="$t('nodes.enterJsonConfig')" /></el-form-item>
        </el-form>
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="installDialogVisible = false">{{ $t('nodes.cancel') }}</el-button>
            <el-button type="primary" @click="confirmInstall">{{ $t('nodes.startInstall') }}</el-button>
          </span>
        </template>
      </el-dialog>
      <!-- 节点详情抽屉 -->
      <el-drawer v-model="drawerVisible" :title="$t('nodes.nodeDetails')" direction="rtl" size="70%"
        :before-close="handleDrawerClose" class="client-drawer">
        <div class="drawer-content">
          <el-tabs v-model="activeTab" class="detail-tabs">
            <!-- 基本信息标签页 -->
            <el-tab-pane :label="$t('nodes.basicInfo')" name="basic">
              <div class="detail-content">
                <!-- 基本信息卡片 -->
                <el-card class="info-card">
                  <template #header>
                    <div class="card-header">
                      <span>{{ $t('nodes.basicInfo') }}</span>
                    </div>
                  </template>
                  <el-descriptions :column="2" border>
                    <el-descriptions-item :label="$t('nodes.nodeName')">
                      <el-tag type="info">{{ currentNode.name }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item :label="$t('nodes.group')">
                      <el-tag v-if="currentNode.group">{{ currentNode.group }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item :label="$t('nodes.tags')">
                      <el-tag v-for="tag in (currentNode.tags ? currentNode.tags.split(',') : [])" :key="tag"
                        type="info" style="margin-right: 2px;">{{ tag }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item :label="$t('nodes.ipAddress')">
                      <el-tag type="success">{{ currentNode.ipaddress }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item :label="$t('nodes.status')">
                      <el-tag :type="getStatusType(currentNode.status)">{{ getStatusText(currentNode.status) }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item :label="$t('nodes.agentStatus')">
                      <el-tag :type="getAgentStatusType(currentNode.agent_status)">{{
                        getAgentStatusText(currentNode.agent_status) }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item :label="$t('nodes.operatingSystem')">
                      <el-tag type="success">{{ nodeDetail.os_type }}</el-tag>
                    </el-descriptions-item>
                    <el-descriptions-item :label="$t('nodes.description')">{{ currentNode.description
                      }}</el-descriptions-item>
                  </el-descriptions>
                </el-card>
                <!-- CPU信息卡片 -->
                <el-card class="info-card">
                  <template #header>
                    <div class="card-header">
                      <span>{{ $t('nodes.cpuInfo') }}</span>
                    </div>
                  </template>
                  <div class="cpu-info">
                    <div v-for="(cpu, index) in nodeDetail.cpu_info" :key="index" class="cpu-item">
                      <el-tag type="primary">{{ cpu.model }}</el-tag>
                      <span class="cpu-cores">{{ cpu.cores }}{{ $t('nodes.cores') }}</span>
                    </div>
                  </div>
                </el-card>
                <!-- 内存信息卡片 -->
                <el-card class="info-card">
                  <template #header>
                    <div class="card-header">
                      <span>{{ $t('nodes.memoryInfo') }}</span>
                    </div>
                  </template>
                  <div class="memory-info">
                    <el-progress
                      :percentage="Number((nodeDetail.memory_info.used / nodeDetail.memory_info.total * 100).toFixed(1))"
                      :status="getUsageStatus((nodeDetail.memory_info.used / nodeDetail.memory_info.total * 100))" />
                    <div class="memory-details">
                      <span>{{ $t('nodes.totalMemory') }}: {{ formatSize(nodeDetail.memory_info.total) }}</span>
                      <span>{{ $t('nodes.usedMemory') }}: {{ formatSize(nodeDetail.memory_info.used) }}</span>
                      <span>{{ $t('nodes.availableMemory') }}: {{ formatSize(nodeDetail.memory_info.total -
                        nodeDetail.memory_info.used) }}</span>
                    </div>
                  </div>
                </el-card>
                <!-- 磁盘信息卡片 -->
                <el-card class="info-card">
                  <template #header>
                    <div class="card-header">
                      <span>{{ $t('nodes.diskInfo') }}</span>
                    </div>
                  </template>
                  <div class="disk-info">
                    <div v-for="(disk, index) in nodeDetail.disk_info" :key="index" class="disk-item">
                      <div class="disk-header">
                        <el-tag type="info">{{ disk.device }}</el-tag>
                        <span class="disk-mount">{{ disk.mount }}</span>
                      </div>
                      <el-progress :percentage="Number(disk.usage)" :status="getUsageStatus(disk.usage)" />
                      <div class="disk-details">
                        <span>{{ $t('nodes.totalCapacity') }}: {{ formatSize(disk.total) }}</span>
                        <span>{{ $t('nodes.usedCapacity') }}: {{ formatSize(disk.used) }}</span>
                        <span>{{ $t('nodes.availableCapacity') }}: {{ formatSize(disk.total - disk.used) }}</span>
                      </div>
                    </div>
                  </div>
                </el-card>
                <!-- 网卡信息卡片 -->
                <el-card class="info-card">
                  <template #header>
                    <div class="card-header">
                      <span>{{ $t('nodes.networkInfo') }}</span>
                    </div>
                  </template>
                  <div class="network-info">
                    <div v-for="(nic, index) in nodeDetail.network_info" :key="index" class="nic-item">
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
            <el-tab-pane :label="$t('nodes.monitorData')" name="monitor">
              <div class="monitor-content">
                <!-- 监控控制面板、图表等，参考Clients.vue -->
                <div class="monitor-control-panel">
                  <div class="panel-section time-range-selector">
                    <span class="section-label">{{ $t('nodes.timeRange') }}</span>
                    <el-select v-model="timeRange" :placeholder="$t('nodes.selectTimeRange')"
                      @change="handleTimeRangeChange" size="default" class="time-select">
                      <el-option :label="$t('nodes.last10Minutes')" value="10m" />
                      <el-option :label="$t('nodes.last15Minutes')" value="15m" />
                      <el-option :label="$t('nodes.last1Hour')" value="1h" />
                      <el-option :label="$t('nodes.last2Hours')" value="2h" />
                      <el-option :label="$t('nodes.custom')" value="custom" />
                    </el-select>
                    <el-date-picker v-if="timeRange === 'custom'" v-model="customTimeRange" type="datetimerange"
                      :range-separator="$t('nodes.to')" :start-placeholder="$t('nodes.startTime')"
                      :end-placeholder="$t('nodes.endTime')" size="default" class="date-picker" :default-time="[
                        new Date(2000, 1, 1, 0, 0, 0),
                        new Date(2000, 1, 1, 23, 59, 59),
                      ]" @change="handleCustomTimeRangeChange" />
                  </div>
                  <div class="panel-section refresh-controls">
                    <span class="section-label">{{ $t('nodes.refreshSettings') }}</span>
                    <div class="refresh-group">
                      <el-button type="primary" :loading="refreshing" @click="handleManualRefresh" size="default"
                        class="refresh-button">
                        <el-icon>
                          <Refresh />
                        </el-icon>
                        <span>{{ $t('nodes.refresh') }}</span>
                      </el-button>

                      <div class="auto-refresh-control">
                        <el-switch v-model="autoRefresh" :active-text="$t('nodes.autoRefresh')" inactive-text=""
                          class="refresh-switch" @change="handleAutoRefreshChange" />
                        <el-select v-if="autoRefresh" v-model="refreshInterval"
                          :placeholder="$t('nodes.refreshInterval')" @change="handleRefreshIntervalChange"
                          size="default" class="interval-select">
                          <el-option :label="$t('nodes.3Seconds')" value="3" />
                          <el-option :label="$t('nodes.5Seconds')" value="5" />
                          <el-option :label="$t('nodes.10Seconds')" value="10" />
                          <el-option :label="$t('nodes.30Seconds')" value="30" />
                          <el-option :label="$t('nodes.1Minute')" value="60" />
                          <el-option :label="$t('nodes.5Minutes')" value="300" />
                        </el-select>
                      </div>
                    </div>
                  </div>
                </div>
                <!-- CPU使用情况图表 -->
                <div class="chart-container">
                  <div class="chart-header">
                    <h3>{{ $t('nodes.cpuUsage') }}</h3>
                  </div>
                  <div class="chart" ref="cpuChart"></div>
                </div>
                <!-- 内存使用情况图表 -->
                <div class="chart-container">
                  <div class="chart-header">
                    <h3>{{ $t('nodes.memoryUsage') }}</h3>
                  </div>
                  <div class="chart" ref="memoryChart"></div>
                </div>
                <!-- 磁盘使用率图表 -->
                <div class="chart-container">
                  <div class="chart-header">
                    <h3>{{ $t('nodes.diskUsage') }}</h3>
                  </div>
                  <div class="chart" ref="diskChart"></div>
                </div>
                <!-- 网络流量监控图表 -->
                <div class="chart-container">
                  <div class="chart-header">
                    <h3>{{ $t('nodes.networkTrafficMonitor') }}</h3>
                  </div>
                  <div class="chart" ref="networkChart"></div>
                </div>
                <!-- 进程列表 -->
                <div class="chart-container">
                  <div class="chart-header">
                    <h3>{{ $t('nodes.processList') }}</h3>
                    <el-button type="primary" size="small" @click="refreshProcessList">{{ $t('nodes.refresh')
                      }}</el-button>
                  </div>
                  <el-table :data="nodeDetail.process_list" style="width: 100%" :max-height="300">
                    <el-table-column prop="pid" label="PID" width="80" />
                    <el-table-column prop="user" :label="$t('nodes.user')" width="100" />
                    <el-table-column prop="cpu_percent" label="CPU%" width="100" />
                    <el-table-column prop="memory_percent" :label="$t('nodes.memoryPercent')" width="100" />
                    <el-table-column prop="command" :label="$t('nodes.command')" show-overflow-tooltip />
                  </el-table>
                </div>
              </div>
            </el-tab-pane>

            <!-- 系统日志标签页 -->
            <el-tab-pane :label="$t('nodes.systemLogs')" name="logs">
              <div class="logs-content">
                <!-- 日志控制面板 -->
                <div class="logs-control-panel">
                  <div class="panel-section search-controls">
                    <el-input v-model="logSearchQuery" :placeholder="$t('nodes.searchLogs')" clearable
                      @clear="handleLogSearch" @input="handleLogSearch" class="search-input">
                      <template #prefix>
                        <el-icon>
                          <Search />
                        </el-icon>
                      </template>
                    </el-input>
                    <el-select v-model="logLevelFilter" :placeholder="$t('nodes.logLevel')" clearable
                      @change="handleLogSearch" class="level-select">
                      <el-option :label="$t('nodes.all')" value="" />
                      <el-option label="DEBUG" value="DEBUG" />
                      <el-option label="INFO" value="INFO" />
                      <el-option label="WARNING" value="WARNING" />
                      <el-option label="ERROR" value="ERROR" />
                      <el-option label="CRITICAL" value="CRITICAL" />
                    </el-select>
                    <el-button type="primary" :loading="refreshingLogs" @click="handleManualLogRefresh"
                      class="refresh-button">
                      <el-icon>
                        <Refresh />
                      </el-icon>
                      <span>{{ $t('nodes.refresh') }}</span>
                    </el-button>
                    <el-switch v-model="autoRefreshLogs" :active-text="$t('nodes.autoRefresh')" inactive-text=""
                      class="refresh-switch" @change="handleAutoLogRefreshChange" />
                    <el-select v-if="autoRefreshLogs" v-model="logRefreshInterval"
                      :placeholder="$t('nodes.refreshInterval')" @change="handleLogRefreshIntervalChange"
                      class="interval-select">
                      <el-option :label="$t('nodes.3Seconds')" value="3" />
                      <el-option :label="$t('nodes.5Seconds')" value="5" />
                      <el-option :label="$t('nodes.10Seconds')" value="10" />
                      <el-option :label="$t('nodes.30Seconds')" value="30" />
                    </el-select>
                  </div>
                </div>

                <!-- 日志列表 -->
                <div class="logs-list">
                  <el-table :data="filteredLogs" style="width: 100%" height="calc(100vh - 300px)"
                    v-loading="loadingLogs">
                    <el-table-column prop="timestamp" :label="$t('nodes.timestamp')" width="180">
                      <template #default="{ row }">
                        {{ row.timestamp }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="level" :label="$t('nodes.level')" width="100">
                      <template #default="{ row }">
                        <el-tag :type="getLogLevelType(row.level)">
                          {{ row.level }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="module" :label="$t('nodes.module')" width="180" />
                    <el-table-column prop="message" :label="$t('nodes.message')" show-overflow-tooltip />
                  </el-table>
                </div>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </el-drawer>
      <!-- 批量分组弹窗 -->
      <el-dialog :title="$t('nodes.batchGroup')" v-model="batchGroupDialogVisible" width="400px">
        <el-input v-model="batchGroupName" :placeholder="$t('nodes.enterNewGroupName')" />
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="batchGroupDialogVisible = false">{{ $t('nodes.cancel') }}</el-button>
            <el-button type="primary" @click="confirmBatchGroup">{{ $t('nodes.confirm') }}</el-button>
          </span>
        </template>
      </el-dialog>
      <!-- 批量打标签弹窗 -->
      <el-dialog :title="$t('nodes.batchTag')" v-model="batchTagDialogVisible" width="400px">
        <el-input v-model="batchTags" :placeholder="$t('nodes.enterNewTags')" />
        <template #footer>
          <span class="dialog-footer">
            <el-button @click="batchTagDialogVisible = false">{{ $t('nodes.cancel') }}</el-button>
            <el-button type="primary" @click="confirmBatchTag">{{ $t('nodes.confirm') }}</el-button>
          </span>
        </template>
      </el-dialog>
    </div>
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
  Monitor,
  Connection,
  CircleClose,
  Clock,
  Download,
  Remove,
  InfoFilled,
  Refresh,
  Search,
  View,
  Plus,
  ArrowRight,
  FolderOpened,
  Hide,
  ArrowLeft
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import axios from 'axios'

const { t } = useI18n()

// ECharts 错误过滤已在全局错误处理器中处理

const nodes = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const installDialogVisible = ref(false)
const dialogType = ref('add')
const form = ref({
  name: '',
  ipaddress: '',
  port: 22,
  username: '',
  auth_type: 'password',
  password: '',
  ssh_key: '',
  description: ''
})

// 统计数据
const stats = computed(() => {
  const online = nodes.value.filter(c => c.status === 'online').length
  const offline = nodes.value.filter(c => c.status === 'offline').length
  const running = nodes.value.filter(c => c.agent_status === 'running').length
  const pending = nodes.value.filter(c => c.agent_status === 'not_installed').length

  return { online, offline, running, pending }
})

const installForm = ref({
  install_path: '/opt/easysync/proxy',
  server_ip: '',
  server_port: 5001,
  config: '{}'
})

const rules = {
  name: [
    { required: true, message: t('nodes.validation.enterName'), trigger: 'blur' }
  ],
  ipaddress: [
    { required: true, message: t('nodes.validation.enterIpAddress'), trigger: 'blur' }
  ],
  username: [
    { required: true, message: t('nodes.validation.enterUsername'), trigger: 'blur' }
  ],
  port: [
    { required: true, message: t('nodes.validation.enterPort'), trigger: 'blur' },
    { type: 'number', min: 1, max: 65535, message: t('nodes.validation.portRange'), trigger: 'blur' }
  ],
  auth_type: [
    { required: true, message: t('nodes.validation.selectAuthType'), trigger: 'change' }
  ],
  password: [
    { required: true, message: t('nodes.validation.enterPassword'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (form.value.auth_type === 'password' && !value) {
          callback(new Error(t('nodes.validation.passwordRequired')))
        } else {
          callback()
        }
      }, trigger: 'blur'
    }
  ],
  ssh_key: [
    { required: true, message: t('nodes.validation.enterSshKey'), trigger: 'blur' },
    {
      validator: (rule, value, callback) => {
        if (form.value.auth_type === 'key' && !value) {
          callback(new Error(t('nodes.validation.sshKeyRequired')))
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
const currentNode = ref({})
const nodeDetail = ref({
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
const diskChart = ref(null)
const networkChart = ref(null)
const cpuTimeRange = ref('1h')
const memoryTimeRange = ref('1h')
const diskTimeRange = ref('1h')
const networkTimeRange = ref('1h')

const cpuChartInstance = ref(null)
const memoryChartInstance = ref(null)
const diskChartInstance = ref(null)
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
  load1: [],
  load5: [],
  load15: [],
  memory: [],
  memoryUsed: [],
  memoryAvailable: [],
  disk: [],
  diskUsed: [],
  diskFree: [],
  network: {
    recv: [],
    sent: [],
    dropped: []
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

const searchQuery = ref('')
const statusFilter = ref('all')
const multipleSelection = ref([])

// 分组/标签相关变量
const groupList = ref([])
const tagList = ref([])
const selectedGroup = ref('')
const selectedTag = ref('')

// 切换架构说明显示
const showArchitecture = ref(false)
const toggleArchitecture = () => {
  showArchitecture.value = !showArchitecture.value
}

const filteredNodes = computed(() => {
  let result = nodes.value
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(n => n.name.toLowerCase().includes(q) || n.ipaddress.toLowerCase().includes(q))
  }

  // 分组过滤
  if (selectedGroup.value) {
    result = result.filter(node => node.group === selectedGroup.value)
  }

  // 标签过滤
  if (selectedTag.value) {
    result = result.filter(node => {
      if (!node.tags) return false
      const tags = node.tags.split(',').map(tag => tag.trim())
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

const handleSearch = () => { }
const handleSelectionChange = (val) => { multipleSelection.value = val }
const batchGroupDialogVisible = ref(false)
const batchTagDialogVisible = ref(false)
const batchGroupName = ref('')
const batchTags = ref('')

// 批量分组对话框
const showBatchGroupDialog = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning(t('nodes.pleaseSelectNodesToGroup'))
    return
  }
  // 统计当前选中节点的分组分布
  const groupStats = {}
  multipleSelection.value.forEach(node => {
    const group = node.group || t('nodes.noGroup')
    groupStats[group] = (groupStats[group] || 0) + 1
  })
  const groupInfo = Object.entries(groupStats)
    .map(([group, count]) => `${group}: ${count}${t('nodes.nodesUnit')}`)
    .join('\n')
  try {
    const { value: groupName } = await ElMessageBox.prompt(
      `${t('nodes.currentSelected')} ${multipleSelection.value.length} ${t('nodes.nodesCount')}\n\n${t('nodes.groupDistribution')}：\n${groupInfo}\n\n${t('nodes.enterNewGroupNameTip')}`,
      t('nodes.batchGroup'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        inputValue: '',
        inputPlaceholder: t('nodes.inputGroupName')
      }
    )
    const nodeIds = multipleSelection.value.map(item => item.id)
    await axios.post('/api/nodes/batch_group', { node_ids: nodeIds, group: groupName || '' })
    ElMessage.success(t('nodes.batchGroupSuccess'))
    fetchNodes()
    fetchGroups()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('nodes.batchGroupFailed'))
    }
  }
}

// 批量打标签对话框
const showBatchTagDialog = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning(t('nodes.pleaseSelectNodesToTag'))
    return
  }
  // 统计当前选中节点的标签分布
  const tagStats = {}
  const allTags = new Set()
  multipleSelection.value.forEach(node => {
    if (node.tags) {
      const tags = node.tags.split(',').map(tag => tag.trim()).filter(tag => tag)
      tags.forEach(tag => {
        tagStats[tag] = (tagStats[tag] || 0) + 1
        allTags.add(tag)
      })
    }
  })
  const tagInfo = Object.entries(tagStats)
    .map(([tag, count]) => `${tag}: ${count}${t('nodes.nodesUnit')}`)
    .join('\n')
  const currentTags = Array.from(allTags).join(', ')
  try {
    const { value: tags } = await ElMessageBox.prompt(
      `${t('nodes.currentSelected')} ${multipleSelection.value.length} ${t('nodes.nodesCount')}\n\n${t('nodes.tagDistribution')}：\n${tagInfo}\n\n${t('nodes.enterNewTagsTip')}`,
      t('nodes.batchTag'),
      {
        confirmButtonText: t('common.confirm'),
        cancelButtonText: t('common.cancel'),
        inputValue: currentTags,
        inputPlaceholder: t('nodes.inputTags')
      }
    )
    const nodeIds = multipleSelection.value.map(item => item.id)
    await axios.post('/api/nodes/batch_tags', { node_ids: nodeIds, tags: tags || '' })
    ElMessage.success(t('nodes.batchTagSuccess'))
    fetchNodes()
    fetchTags()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('nodes.batchTagFailed'))
    }
  }
}

// 批量删除
const handleBatchDelete = async () => {
  if (!multipleSelection.value.length) {
    ElMessage.warning(t('nodes.pleaseSelectNodesToDelete'))
    return
  }

  try {
    await ElMessageBox.confirm(t('nodes.confirmBatchDelete', { count: multipleSelection.value.length }), t('nodes.batchDelete'), {
      type: 'warning'
    })

    const nodeIds = multipleSelection.value.map(item => item.id)
    await axios.post('/api/nodes/batch_delete', { node_ids: nodeIds })

    ElMessage.success(t('nodes.batchDeleteSuccess'))
    fetchNodes()
    multipleSelection.value = []
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('nodes.batchDeleteFailed'))
    }
  }
}

const fetchGroups = async () => {
  try {
    const response = await axios.get('/api/nodes/groups')
    if (response.data.status === 'success') {
      groupList.value = response.data.data || []
    }
  } catch (error) {
    // 静默处理错误
  }
}

const fetchTags = async () => {
  try {
    const response = await axios.get('/api/nodes/tags')
    if (response.data.status === 'success') {
      tagList.value = response.data.data || []
    }
  } catch (error) {
    // 静默处理错误
  }
}

// 获取节点列表
const fetchNodes = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/nodes')
    nodes.value = response.data.data
  } catch (error) {
    nodes.value = []
  } finally {
    loading.value = false
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return t('nodes.neverOnline')
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

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case 'online':
      return t('nodes.online')
    case 'offline':
      return t('nodes.offline')
    case 'error':
      return t('nodes.error')
    default:
      return t('nodes.unknown')
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
      return t('nodes.running')
    case 'installing':
      return t('nodes.installing')
    case 'not_installed':
      return t('nodes.notInstalled')
    case 'uninstall_error':
      return t('nodes.uninstallError')
    case 'install_error':
      return t('nodes.installError')
    case 'online':
      return t('nodes.online')
    case 'offline':
      return t('nodes.offline')
    default:
      return t('nodes.unknown')
  }
}

// 显示添加对话框
const showAddDialog = () => {
  dialogType.value = 'add'
  form.value = {
    name: '',
    ipaddress: '',
    username: '',
    port: 22,
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
      await axios.post('/api/nodes', form.value)
      ElMessage.success(t('nodes.addSuccess'))
    } else {
      await axios.put(`/api/nodes/${form.value.id}`, form.value)
      ElMessage.success(t('nodes.updateSuccess'))
    }
    dialogVisible.value = false
    fetchNodes()
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
  currentNode.value = row
  // 从当前窗口获取默认服务器地址和端口
  const defaultHost = window.location.hostname
  const defaultPort = window.location.port || '5001'
  
  installForm.value = {
    install_path: '/opt/easysync/proxy',
    server_ip: defaultHost,
    server_port: parseInt(defaultPort) || 5001,
    config: JSON.stringify({
    })
  }
  installDialogVisible.value = true
}

// 确认安装
const confirmInstall = async () => {
  try {
    if (!currentNode.value) {
      ElMessage.error(t('nodes.noNodeSelected'))
      return
    }
    // 验证必填字段
    if (!installForm.value.server_ip || !installForm.value.server_port) {
      ElMessage.error('请填写服务器IP和端口')
      return
    }
    await axios.post(`/api/nodes/${currentNode.value.id}/install`, installForm.value)
    ElMessage.success(t('nodes.startInstallAgent'))
    installDialogVisible.value = false
    fetchNodes()
  } catch (error) {
    // 错误处理已经在拦截器中完成
  }
}

// 卸载Agent
const uninstallAgent = async (row) => {
  try {
    await ElMessageBox.confirm(t('nodes.confirmUninstallAgent'), t('nodes.tip'), {
      type: 'warning'
    })
    await axios.post(`/api/nodes/${row.id}/uninstall`)
    ElMessage.success(t('nodes.startUninstallAgent'))
    fetchNodes()
  } catch (error) {
    if (error !== 'cancel') {
      // 错误处理已经在拦截器中完成
    }
  }
}

// 删除节点
const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(t('nodes.confirmDeleteNode'), t('nodes.tip'), {
      type: 'warning'
    })
    await axios.delete(`/api/nodes/${row.id}`)
    ElMessage.success(t('nodes.deleteSuccess'))
    fetchNodes()
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
    const response = await axios.post(`/api/nodes/${row.id}/test-connection`)
    if (response.data.status === 'success') {
      ElMessage.success(t('nodes.connectionTestSuccess'))
      // 更新本地状态
      row.status = 'online'
      fetchNodes()  // 刷新列表以更新状态
    }
  } catch (error) {
    // 错误处理已经在拦截器中完成
  } finally {
    row.testing = false
  }
}

// 获取节点信息
const getNodeInfo = async (row) => {
  try {
    row.fetching = true
    const response = await axios.post(`/api/nodes/${row.id}/status`)
    if (response.data.status === 'success') {
      ElMessage.success(t('nodes.getInfoSuccess'))
      fetchNodes()  // 刷新列表以更新信息
    }
  } catch (error) {
    ElMessage.error(t('nodes.getInfoFailed'))
  } finally {
    row.fetching = false
  }
}

// 显示节点详情
const handleNameClick = async (node) => {
  try {
    currentNode.value = node
    drawerVisible.value = true

    // 先获取节点详情
    await fetchNodeDetail(node.id)

    // 初始化图表
    await nextTick()
    await initCharts()
  } catch (error) {
    ElMessage.error(t('nodes.loadNodeDetailsFailed'))
  }
}

const handleNodeCommand = async (command) => {
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
      await getNodeInfo(row)
      break
    case 'delete':
      await handleDelete(row)
      break
  }
}

// 获取节点详情
const fetchNodeDetail = async (nodeId) => {
  try {
    const response = await axios.get(`/api/nodes/${nodeId}/detail`)
    nodeDetail.value = response.data.data
    nodeDetail.value.os_type = response.data.data.os_type
  } catch (error) {
    ElMessage.error(t('nodes.getNodeDetailsFailed'))
  }
}

// 添加安全初始化 ECharts 的函数
function safeInitChart(refDom, instanceRef, option) {
  if (!refDom.value) return
  // 如果宽高为0，延迟重试
  if (refDom.value.clientWidth === 0 || refDom.value.clientHeight === 0) {
    setTimeout(() => safeInitChart(refDom, instanceRef, option), 120)
    return
  }

  try {
    // 销毁现有实例
    if (instanceRef.value) {
      instanceRef.value.dispose()
    }

    // 创建新实例
    instanceRef.value = echarts.init(refDom.value, null, {
      renderer: 'canvas',
      useDirtyRect: true
    })

    // 验证数据格式并确保所有必要属性存在
    if (option.series) {
      option.series.forEach((series, index) => {
        // 确保基本属性存在
        if (!series.type) {
          series.type = 'line'
        }
        if (!series.name) {
          series.name = `Series ${index}`
        }
        if (!Array.isArray(series.data)) {
          series.data = []
        }

        // 确保其他必要属性存在
        if (!series.smooth) series.smooth = true
        if (!series.symbol) series.symbol = 'circle'
        if (!series.showSymbol) series.showSymbol = false
        if (!series.symbolSize) series.symbolSize = 6
        if (!series.sampling) series.sampling = 'average'

        // 确保样式属性存在
        if (!series.itemStyle) {
          series.itemStyle = {
            color: '#409EFF'
          }
        }

        // 确保 emphasis 属性存在
        if (!series.emphasis) {
          series.emphasis = {
            focus: 'series',
            itemStyle: {
              borderWidth: 3,
              shadowBlur: 10
            }
          }
        }
      })
    }

    // 设置配置
    instanceRef.value.setOption(option, true)

  } catch (error) {
    // 静默处理错误
  }
}

// 修改 initCharts 函数，重新设计图表配置
const initCharts = async () => {
  if (!currentNode.value?.id) {
    return
  }
  try {
    disposeCharts()
    await nextTick()

    // 确保数据存在，如果为空则添加默认数据
    const ensureData = (dataArray, defaultValue = 0) => {
      if (!Array.isArray(dataArray) || dataArray.length === 0) {
        const now = Date.now()
        return [[now - 60000, defaultValue], [now, defaultValue]]
      }
      return dataArray
    }

    // CPU 图表 - 包含使用率和负载
    if (cpuChart.value) {
      const cpuOption = {
        title: {
          text: t('nodes.cpuUsage'),
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold',
            color: '#303133'
          }
        },
        tooltip: {
          trigger: 'axis',
          show: true,
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e4e7ed',
          borderWidth: 1,
          textStyle: {
            color: '#303133'
          }
        },
        legend: {
          data: [t('nodes.cpuUsage'), t('nodes.load1Minute'), t('nodes.load5Minutes'), t('nodes.load15Minutes')],
          top: 40,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '100px',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisTick: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisLabel: {
            color: '#909399',
            formatter: (value) => {
              return new Date(value).toLocaleTimeString()
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed',
              color: '#f0f0f0'
            }
          }
        },
        yAxis: [
          {
            type: 'value',
            name: t('nodes.cpuUsage'),
            min: 0,
            max: 100,
            position: 'left',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399',
              formatter: '{value}%'
            },
            splitLine: {
              show: true,
              lineStyle: {
                type: 'dashed',
                color: '#f0f0f0'
              }
            }
          },
          {
            type: 'value',
            name: t('nodes.load1Minute'),
            position: 'right',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399'
            },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: t('nodes.cpuUsage'),
            type: 'line',
            yAxisIndex: 0,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 6,
            sampling: 'average',
            itemStyle: {
              color: '#409EFF'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(64,158,255,0.4)' },
                { offset: 1, color: 'rgba(64,158,255,0.1)' }
              ])
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                color: '#409EFF',
                borderWidth: 3,
                shadowBlur: 10,
                shadowColor: 'rgba(64,158,255,0.3)'
              }
            },
            data: ensureData(monitorData.value.cpu, 50)
          },
          {
            name: t('nodes.load1Minute'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#E6A23C'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.load1, 1.5)
          },
          {
            name: t('nodes.load5Minutes'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#F56C6C'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.load5, 1.2)
          },
          {
            name: t('nodes.load15Minutes'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#909399'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.load15, 1.0)
          }
        ]
      }
      safeInitChart(cpuChart, cpuChartInstance, cpuOption)
    }

    // 内存图表 - 包含使用率和详细信息
    if (memoryChart.value) {
      const memoryOption = {
        title: {
          text: t('nodes.memoryUsage'),
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold',
            color: '#303133'
          }
        },
        tooltip: {
          trigger: 'axis',
          show: true,
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e4e7ed',
          borderWidth: 1,
          textStyle: {
            color: '#303133'
          }
        },
        legend: {
          data: [t('nodes.memoryUsage'), t('nodes.usedMemory'), t('nodes.availableMemory')],
          top: 40,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '100px',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisTick: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisLabel: {
            color: '#909399',
            formatter: (value) => {
              return new Date(value).toLocaleTimeString()
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed',
              color: '#f0f0f0'
            }
          }
        },
        yAxis: [
          {
            type: 'value',
            name: t('nodes.memoryUsage'),
            min: 0,
            max: 100,
            position: 'left',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399',
              formatter: '{value}%'
            },
            splitLine: {
              show: true,
              lineStyle: {
                type: 'dashed',
                color: '#f0f0f0'
              }
            }
          },
          {
            type: 'value',
            name: t('nodes.usedMemory'),
            position: 'right',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399',
              formatter: (value) => formatSize(value)
            },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: t('nodes.memoryUsage'),
            type: 'line',
            yAxisIndex: 0,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 6,
            sampling: 'average',
            itemStyle: {
              color: '#67C23A'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(103,194,58,0.4)' },
                { offset: 1, color: 'rgba(103,194,58,0.1)' }
              ])
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                color: '#67C23A',
                borderWidth: 3,
                shadowBlur: 10,
                shadowColor: 'rgba(103,194,58,0.3)'
              }
            },
            data: ensureData(monitorData.value.memory, 60)
          },
          {
            name: t('nodes.usedMemory'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#F56C6C'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.memoryUsed, 8 * 1024 * 1024 * 1024) // 8GB
          },
          {
            name: t('nodes.availableMemory'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#909399'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.memoryAvailable, 4 * 1024 * 1024 * 1024) // 4GB
          }
        ]
      }
      safeInitChart(memoryChart, memoryChartInstance, memoryOption)
    }

    // 磁盘图表 - 新增磁盘使用情况
    if (diskChart.value) {
      const diskOption = {
        title: {
          text: t('nodes.diskUsage'),
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold',
            color: '#303133'
          }
        },
        tooltip: {
          trigger: 'axis',
          show: true,
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e4e7ed',
          borderWidth: 1,
          textStyle: {
            color: '#303133'
          }
        },
        legend: {
          data: [t('nodes.diskUsage'), t('nodes.usedCapacity'), t('nodes.availableCapacity')],
          top: 40,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '100px',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisTick: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisLabel: {
            color: '#909399',
            formatter: (value) => {
              return new Date(value).toLocaleTimeString()
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed',
              color: '#f0f0f0'
            }
          }
        },
        yAxis: [
          {
            type: 'value',
            name: t('nodes.diskUsage'),
            min: 0,
            max: 100,
            position: 'left',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399',
              formatter: '{value}%'
            },
            splitLine: {
              show: true,
              lineStyle: {
                type: 'dashed',
                color: '#f0f0f0'
              }
            }
          },
          {
            type: 'value',
            name: t('nodes.usedCapacity'),
            position: 'right',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399',
              formatter: (value) => formatSize(value)
            },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: t('nodes.diskUsage'),
            type: 'line',
            yAxisIndex: 0,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 6,
            sampling: 'average',
            itemStyle: {
              color: '#E6A23C'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(230,162,60,0.4)' },
                { offset: 1, color: 'rgba(230,162,60,0.1)' }
              ])
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                color: '#E6A23C',
                borderWidth: 3,
                shadowBlur: 10,
                shadowColor: 'rgba(230,162,60,0.3)'
              }
            },
            data: ensureData(monitorData.value.disk, 70)
          },
          {
            name: t('nodes.usedCapacity'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#F56C6C'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.diskUsed, 500 * 1024 * 1024 * 1024) // 500GB
          },
          {
            name: t('nodes.availableCapacity'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#909399'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.diskFree, 200 * 1024 * 1024 * 1024) // 200GB
          }
        ]
      }
      safeInitChart(diskChart, diskChartInstance, diskOption)
    }

    // 网络图表 - 优化网络流量展示
    if (networkChart.value) {
      const networkOption = {
        title: {
          text: t('nodes.networkTraffic'),
          left: 'center',
          top: 10,
          textStyle: {
            fontSize: 16,
            fontWeight: 'bold',
            color: '#303133'
          }
        },
        tooltip: {
          trigger: 'axis',
          show: true,
          axisPointer: {
            type: 'cross',
            label: {
              backgroundColor: '#6a7985'
            }
          },
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          borderColor: '#e4e7ed',
          borderWidth: 1,
          textStyle: {
            color: '#303133'
          }
        },
        legend: {
          data: [t('nodes.receivedTraffic'), t('nodes.sentTraffic'), t('nodes.droppedPackets')],
          top: 40,
          textStyle: {
            fontSize: 12
          }
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: '100px',
          containLabel: true
        },
        xAxis: {
          type: 'time',
          boundaryGap: false,
          axisLine: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisTick: {
            show: true,
            lineStyle: { color: '#e4e7ed' }
          },
          axisLabel: {
            color: '#909399',
            formatter: (value) => {
              return new Date(value).toLocaleTimeString()
            }
          },
          splitLine: {
            show: true,
            lineStyle: {
              type: 'dashed',
              color: '#f0f0f0'
            }
          }
        },
        yAxis: [
          {
            type: 'value',
            name: t('nodes.networkTraffic'),
            position: 'left',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399',
              formatter: (value) => formatSize(value)
            },
            splitLine: {
              show: true,
              lineStyle: {
                type: 'dashed',
                color: '#f0f0f0'
              }
            }
          },
          {
            type: 'value',
            name: t('nodes.droppedPackets'),
            position: 'right',
            axisLine: { show: false },
            axisTick: { show: false },
            axisLabel: {
              color: '#909399'
            },
            splitLine: { show: false }
          }
        ],
        series: [
          {
            name: t('nodes.receivedTraffic'),
            type: 'line',
            yAxisIndex: 0,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 6,
            sampling: 'average',
            itemStyle: {
              color: '#409EFF'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(64,158,255,0.4)' },
                { offset: 1, color: 'rgba(64,158,255,0.1)' }
              ])
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                color: '#409EFF',
                borderWidth: 3,
                shadowBlur: 10,
                shadowColor: 'rgba(64,158,255,0.3)'
              }
            },
            data: ensureData(monitorData.value.network.recv, 100 * 1024 * 1024) // 100MB
          },
          {
            name: t('nodes.sentTraffic'),
            type: 'line',
            yAxisIndex: 0,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 6,
            sampling: 'average',
            itemStyle: {
              color: '#67C23A'
            },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(103,194,58,0.4)' },
                { offset: 1, color: 'rgba(103,194,58,0.1)' }
              ])
            },
            emphasis: {
              focus: 'series',
              itemStyle: {
                color: '#67C23A',
                borderWidth: 3,
                shadowBlur: 10,
                shadowColor: 'rgba(103,194,58,0.3)'
              }
            },
            data: ensureData(monitorData.value.network.sent, 50 * 1024 * 1024) // 50MB
          },
          {
            name: t('nodes.droppedPackets'),
            type: 'line',
            yAxisIndex: 1,
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 4,
            sampling: 'average',
            itemStyle: {
              color: '#F56C6C'
            },
            lineStyle: {
              type: 'dashed'
            },
            data: ensureData(monitorData.value.network.dropped, 10) // 10 packets
          }
        ]
      }
      safeInitChart(networkChart, networkChartInstance, networkOption)
    }



  } catch (e) {
    // 静默处理错误
  }
}

// 修改 loadHistoryData 函数，支持新的数据结构
const loadHistoryData = async () => {
  try {
    const nodeId = currentNode.value.id
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

    const response = await axios.get(`/api/monitor/${nodeId}/history`, {
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
        load1: [],
        load5: [],
        load15: [],
        memory: [],
        memoryUsed: [],
        memoryAvailable: [],
        disk: [],
        diskUsed: [],
        diskFree: [],
        network: {
          recv: [],
          sent: [],
          dropped: []
        }
      }

      // 处理历史数据
      historyData.forEach(item => {
        try {
          // 使用数据记录的时间戳
          const timestamp = new Date(item.timestamp).getTime()

          // CPU数据
          const cpuUsage = parseFloat(item.data.cpu?.percent || 0)
          if (!isNaN(cpuUsage)) {
            monitorData.value.cpu.push([timestamp, cpuUsage])
          }

          // CPU负载数据
          const loadAvg = item.data.cpu?.load_avg || [0, 0, 0]
          const load1 = parseFloat(loadAvg[0] || 0)
          const load5 = parseFloat(loadAvg[1] || 0)
          const load15 = parseFloat(loadAvg[2] || 0)

          if (!isNaN(load1)) monitorData.value.load1.push([timestamp, load1])
          if (!isNaN(load5)) monitorData.value.load5.push([timestamp, load5])
          if (!isNaN(load15)) monitorData.value.load15.push([timestamp, load15])

          // 内存数据
          const memoryUsage = parseFloat(item.data.memory?.percent || 0)
          const memoryUsed = parseFloat(item.data.memory?.used || 0)
          const memoryAvailable = parseFloat(item.data.memory?.available || 0)

          if (!isNaN(memoryUsage)) monitorData.value.memory.push([timestamp, memoryUsage])
          if (!isNaN(memoryUsed)) monitorData.value.memoryUsed.push([timestamp, memoryUsed])
          if (!isNaN(memoryAvailable)) monitorData.value.memoryAvailable.push([timestamp, memoryAvailable])

          // 磁盘数据
          const diskUsage = parseFloat(item.data.disk?.percent || 0)
          const diskUsed = parseFloat(item.data.disk?.used || 0)
          const diskFree = parseFloat(item.data.disk?.free || 0)

          if (!isNaN(diskUsage)) monitorData.value.disk.push([timestamp, diskUsage])
          if (!isNaN(diskUsed)) monitorData.value.diskUsed.push([timestamp, diskUsed])
          if (!isNaN(diskFree)) monitorData.value.diskFree.push([timestamp, diskFree])

          // 网络数据
          const recv = parseFloat(item.data.network?.bytes_recv || 0)
          const sent = parseFloat(item.data.network?.bytes_sent || 0)
          const dropped = parseFloat(item.data.network?.packets_dropped || 0)

          if (!isNaN(recv)) monitorData.value.network.recv.push([timestamp, recv])
          if (!isNaN(sent)) monitorData.value.network.sent.push([timestamp, sent])
          if (!isNaN(dropped)) monitorData.value.network.dropped.push([timestamp, dropped])

        } catch (error) {
          // 静默处理错误
        }
      })




      // 更新图表数据
      updateCharts()
    }
  } catch (error) {
    ElMessage.error(t('nodes.loadHistoryDataFailed'))
  }
}

// 更新图表数据 - 使用更安全的方式更新数据
const updateCharts = () => {
  if (activeTab.value === 'monitor' && drawerVisible.value) {
    nextTick(() => {
      try {
        // 创建完整的系列配置，包含所有必要属性
        const createSeriesConfig = (name, data, color = '#409EFF', lineStyle = {}, hasArea = false) => {
          const config = {
            name,
            type: 'line',
            data: data || [],
            smooth: true,
            symbol: 'circle',
            showSymbol: false,
            symbolSize: 6,
            sampling: 'average',
            itemStyle: { color },
            lineStyle,
            emphasis: {
              focus: 'series',
              itemStyle: {
                borderWidth: 3,
                shadowBlur: 10
              }
            }
          }

          // 为第一个系列添加区域样式
          if (hasArea) {
            // 将十六进制颜色转换为rgba格式
            const hexToRgba = (hex, alpha) => {
              const r = parseInt(hex.slice(1, 3), 16)
              const g = parseInt(hex.slice(3, 5), 16)
              const b = parseInt(hex.slice(5, 7), 16)
              return `rgba(${r}, ${g}, ${b}, ${alpha})`
            }

            config.areaStyle = {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: hexToRgba(color, 0.4) },
                { offset: 1, color: hexToRgba(color, 0.1) }
              ])
            }
          }

          return config
        }

        // 只更新数据，不重新初始化整个图表
        if (cpuChartInstance.value) {
          cpuChartInstance.value.setOption({
            series: [
              createSeriesConfig(t('nodes.cpuUsage'), monitorData.value.cpu, '#409EFF', {}, true),
              createSeriesConfig(t('nodes.load1Minute'), monitorData.value.load1, '#E6A23C', { type: 'dashed' }),
              createSeriesConfig(t('nodes.load5Minutes'), monitorData.value.load5, '#F56C6C', { type: 'dashed' }),
              createSeriesConfig(t('nodes.load15Minutes'), monitorData.value.load15, '#909399', { type: 'dashed' })
            ]
          }, false)
        }

        if (memoryChartInstance.value) {
          memoryChartInstance.value.setOption({
            series: [
              createSeriesConfig(t('nodes.memoryUsage'), monitorData.value.memory, '#409EFF', {}, true),
              createSeriesConfig(t('nodes.usedMemory'), monitorData.value.memoryUsed, '#E6A23C', { type: 'dashed' }),
              createSeriesConfig(t('nodes.availableMemory'), monitorData.value.memoryAvailable, '#F56C6C', { type: 'dashed' })
            ]
          }, false)
        }

        if (diskChartInstance.value) {
          diskChartInstance.value.setOption({
            series: [
              createSeriesConfig(t('nodes.diskUsage'), monitorData.value.disk, '#409EFF', {}, true),
              createSeriesConfig('已用空间', monitorData.value.diskUsed, '#E6A23C', { type: 'dashed' }),
              createSeriesConfig('可用空间', monitorData.value.diskFree, '#F56C6C', { type: 'dashed' })
            ]
          }, false)
        }

        if (networkChartInstance.value) {
          networkChartInstance.value.setOption({
            series: [
              createSeriesConfig('接收流量', monitorData.value.network.recv, '#409EFF', {}, true),
              createSeriesConfig('发送流量', monitorData.value.network.sent, '#E6A23C', { type: 'dashed' }),
              createSeriesConfig('丢包数', monitorData.value.network.dropped, '#F56C6C', { type: 'dashed' })
            ]
          }, false)
        }
      } catch (error) {
        // 如果更新失败，回退到重新初始化
        setTimeout(() => {
          initCharts()
        }, 100)
      }
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
    nextTick(() => {
      setTimeout(() => {
        initCharts()
      }, 120)
    })
  }
})

// 监听时间范围变化
watch([cpuTimeRange, memoryTimeRange, diskTimeRange, networkTimeRange], () => {
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
      if (diskChartInstance.value) {
        diskChartInstance.value.resize({
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
      // 静默处理错误
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
    if (diskChartInstance.value) {
      diskChartInstance.value.dispose()
      diskChartInstance.value = null
    }
    if (networkChartInstance.value) {
      networkChartInstance.value.dispose()
      networkChartInstance.value = null
    }
  } catch (error) {
    // 静默处理错误
  }
}

// 监听抽屉显示状态
watch(drawerVisible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      setTimeout(() => {
        if (activeTab.value === 'monitor') {
          initCharts()
        }
      }, 120)
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
})

// 关闭抽屉时清理
const handleDrawerClose = () => {
  stopAutoRefresh()
  disposeCharts()
  drawerVisible.value = false
  activeTab.value = 'basic'
}

// 刷新进程列表
const refreshProcessList = async () => {
  try {
    const response = await axios.get(`/api/nodes/${currentNode.value.id}/processes`)
    if (response.data.status === 'success') {
      nodeDetail.value.process_list = response.data.data
    }
  } catch (error) {
    ElMessage.error(t('nodes.getProcessListFailed'))
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
  if (!currentNode.value?.id) return

  try {
    loadingLogs.value = true
    const response = await axios.get(`/api/nodes/${currentNode.value.id}/logs`, {
      params: {
        lines: 100,
        level: logLevelFilter.value || 'ALL'
      }
    })
    if (response.data.status === 'success') {
      const logEntries = response.data.data.log_content.split('\n')
        .filter(line => line.trim())
        .map(line => {
          let match = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[.,]\d{3})\s+(\d+)\s+([\w._]+)\s+(\w+)(?:\s+(\[[^\]]+\]))?\s*-\s*(?:[\w()]+\s*\[-\]\s*(?:-\s*)?)?(.+)$/)
          if (match) {
            let message = (match[6] || line).trim()
            if (message.startsWith(']')) {
              message = message.substring(1).trim()
            }
            return {
              timestamp: match[1].replace('.', ','),
              module: match[3],
              level: match[4],
              message: message
            }
          }
          
          match = line.match(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[.,]\d{3})\s*-\s*([\w._]+)\s*-\s*(\w+)\s*-\s*(.+)$/)
          if (match) {
            return {
              timestamp: match[1].replace('.', ','),
              module: match[2],
              level: match[3],
              message: match[4]
            }
          }
          
          return {
            timestamp: '',
            module: '',
            level: 'INFO',
            message: line
          }
        })

      logs.value = logEntries
    }
  } catch (error) {
    ElMessage.error(t('nodes.getLogsFailed'))
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

// 获取使用率状态
const getUsageStatus = (usage) => {
  if (usage >= 90) return 'exception'
  if (usage >= 70) return 'warning'
  return 'success'
}

onMounted(() => {
  fetchNodes()
  fetchTags()
  fetchGroups()
})
</script>

<style scoped>
.nodes-page {
  padding: 20px;
  min-height: 100vh;
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

.architecture-central-diagram {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 30px;
  padding: 20px;
  background: var(--card-bg);
  border-radius: 12px;
  border: 1px solid var(--border-color);
}

.storage-side {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  flex: 1;
  max-width: 280px;
}

.storage-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--card-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--text-color);
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.storage-icon.current-step {
  background: var(--card-bg);
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
}

.storage-label {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.sync-arrows {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #409EFF;
  margin: 0 20px;
  animation: pulse 2s infinite;
}

@keyframes pulse {

  0%,
  100% {
    transform: scale(1);
  }

  50% {
    transform: scale(1.1);
  }
}

.proxy-center {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  flex: 1;
  max-width: 280px;
}

.proxy-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--card-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: var(--text-color);
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.proxy-icon.current-step {
  background: var(--card-bg);
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.3);
}

.proxy-label {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.proxy-desc {
  margin: 0;
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.central-arch-notes {
  margin-bottom: 30px;
}

.usage-guide {
  margin-bottom: 30px;
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

.step-content strong {
  display: block;
  margin-bottom: 8px;
  color: var(--text-color);
  font-size: 14px;
  font-weight: 600;
}

.step-content p {
  margin: 0;
  color: var(--text-secondary);
  font-size: 13px;
  line-height: 1.5;
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

.nodes-container {
  padding: 0px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
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
  background-color: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  background: var(--bg-secondary);
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
  background-color: var(--bg-color);
  border-radius: 4px;
  min-width: 200px;
}

.cpu-cores {
  color: var(--text-secondary);
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
  color: var(--text-secondary);
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
  background-color: var(--bg-color);
  border-radius: 4px;
}

.disk-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.disk-mount {
  color: var(--text-secondary);
  font-size: 14px;
}

.disk-details {
  display: flex;
  justify-content: space-between;
  color: var(--text-secondary);
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
  background-color: var(--bg-secondary);
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
  color: var(--text-secondary);
  font-size: 14px;
  margin-right: 8px;
}

:deep(.el-descriptions) {
  padding: 16px;
}

:deep(.el-descriptions__label) {
  width: 100px;
  color: var(--text-secondary);
}

:deep(.el-descriptions__content) {
  color: var(--text-color);
}

:deep(.el-progress) {
  margin: 0;
}

@media screen and (max-width: 768px) {
  .detail-content {
    padding: 10px;
  }

  .cpu-item,
  .nic-item {
    min-width: 100%;
  }

  .memory-details,
  .disk-details {
    flex-direction: column;
    gap: 8px;
  }
}

.monitor-content {
  padding: 20px;
}

.chart-container {
  margin-bottom: 24px;
  background-color: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 20px;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border-color);
}

.monitor-control-panel {
  display: flex;
  align-items: center;
  margin-bottom: 24px;
  padding: 16px 20px;
  background-color: var(--card-bg);
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
  color: var(--text-secondary);
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
  border-bottom: 1px solid var(--border-color);
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
  background-color: var(--card-bg);
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
  background-color: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  padding: 16px;
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

.nodes-card {
  background: var(--card-bg);
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: 1px solid var(--border-color);
  margin-bottom: 24px;
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
  gap: 10px;
}

.nodes-table {
  width: 100%;
}

.nodes-table :deep(.el-table__header) {
  background: var(--bg-secondary);
}

.nodes-table :deep(.el-table__header th) {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
}

.nodes-table :deep(.el-table__row) {
  transition: all 0.3s ease;
}

.action-buttons {
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  width: 200px;
}

.refresh-btn {
  margin-left: 8px;
}

@media screen and (max-width: 1200px) {
  .nodes-card {
    padding: 10px;
  }
}

@media screen and (max-width: 768px) {
  .nodes-container {
    padding: 10px;
  }

  .card-header {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .search-input {
    width: 100%;
  }
}

.nodes-card {
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

.table-container {
  padding: 0;
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

.chart {
  width: 100%;
  height: 300px;
  min-height: 200px;
}
</style>