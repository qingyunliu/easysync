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
    
    <!-- 统计面板 -->
    <el-row :gutter="20" style="margin-bottom: 20px;">
      <el-col :span="4">
        <el-card class="stat-card">
          <div class="stat-content stat-flex">
            <div class="stat-icon total">
              <el-icon><Document /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.total || 0 }}</div>
              <div class="stat-label">总任务数</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card running">
          <div class="stat-content stat-flex">
            <div class="stat-icon running">
              <el-icon><Loading /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.running || 0 }}</div>
              <div class="stat-label">运行中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card pending">
          <div class="stat-content stat-flex">
            <div class="stat-icon pending">
              <el-icon><Clock /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.pending || 0 }}</div>
              <div class="stat-label">等待中</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card completed">
          <div class="stat-content stat-flex">
            <div class="stat-icon completed">
              <el-icon><CircleCheck /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.completed || 0 }}</div>
              <div class="stat-label">已完成</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card failed">
          <div class="stat-content stat-flex">
            <div class="stat-icon failed">
              <el-icon><CircleClose /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ taskStats.failed || 0 }}</div>
              <div class="stat-label">已失败</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="4">
        <el-card class="stat-card online-node">
          <div class="stat-content stat-flex">
            <div class="stat-icon online">
              <el-icon><Connection /></el-icon>
            </div>
            <div>
              <div class="stat-number">{{ OnlineNodeStats || 0 }}</div>
              <div class="stat-label">在线节点</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

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
            :icon="autoRefresh ? VideoPause : Refresh"
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
              <el-link type="primary" @click="handleViewDetail(row)">
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
              <el-icon style="vertical-align: middle; margin-right: 4px;">
                <component :is="getStatusIcon(row.status)" />
              </el-icon>
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

        <el-table-column label="操作" width="300" fixed="right">
          <template #default="{ row }">
            <el-button-group size="small">
              <!-- 启动/停止按钮 -->
            <el-button
                v-if="['pending', 'failed'].includes(row.status)"
                type="success"
                @click="handleStartTask(row)"
                :icon="VideoPlay"
                :loading="loadingTasks.has(row.id)"
              >
                启动
            </el-button>
              
              <!-- 暂停/恢复按钮 -->
            <el-button
                v-if="row.status === 'running'"
                type="warning"
                @click="handlePauseTask(row)"
                :icon="VideoPause"
                :loading="loadingTasks.has(row.id)"
              >
                暂停
            </el-button>
              
            <el-button
                v-if="row.status === 'paused'"
                type="success"
                @click="handleResumeTask(row)"
                :icon="VideoPlay"
                :loading="loadingTasks.has(row.id)"
              >
                恢复
            </el-button>
              
              <!-- 取消按钮 -->
            <el-button
                v-if="['running', 'assigned', 'paused'].includes(row.status)"
              type="danger"
                @click="handleCancelTask(row)"
                :icon="Close"
                :loading="loadingTasks.has(row.id)"
              >
                取消
              </el-button>
              
              <!-- 重试按钮 -->
              <el-button
                v-if="row.status === 'failed'"
                type="warning"
                @click="handleRetryTask(row)"
                :icon="RefreshRight"
                :loading="loadingTasks.has(row.id)"
              >
                重试
            </el-button>
          </el-button-group>
            
            <!-- 更多操作下拉菜单 -->
            <el-dropdown @command="(command) => handleDropdownCommand(command, row)" style="margin-left: 8px;">
              <el-button type="primary" :icon="More" size="small">
                更多
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="logs">
                    <el-icon><Document /></el-icon>查看日志
                  </el-dropdown-item>
                  <el-dropdown-item command="detail">
                    <el-icon><InfoFilled /></el-icon>详情
                  </el-dropdown-item>
                  <el-dropdown-item command="test-connection" v-if="canTestConnection(row)">
                    <el-icon><Connection /></el-icon>测试连接
                  </el-dropdown-item>
                  <el-dropdown-item command="test-mount" v-if="canTestMount(row)">
                    <el-icon><Connection /></el-icon>测试挂载
                  </el-dropdown-item>
                  <el-dropdown-item command="duplicate">
                    <el-icon><CopyDocument /></el-icon>复制任务
                  </el-dropdown-item>
                  <el-dropdown-item 
                    command="delete" 
                    :disabled="['running', 'assigned'].includes(row.status)"
                    style="color: #f56c6c;"
                  >
                    <el-icon><Delete /></el-icon>删除
                  </el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
        </template>
      </el-table-column>
    </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="totalTasks"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="handleSizeChange"
          @current-change="handleCurrentChange"
          style="margin-top: 20px; text-align: right;"
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
    <el-drawer
      v-model="detailDialogVisible"
      title="任务详情"
      direction="rtl"
      :size="isFullscreen ? '80vw' : '45vw'"
      :with-header="false"
      custom-class="task-detail-drawer"
      :close-on-click-modal="false"
    >
      <div class="drawer-header">
        <span>任务详情</span>
        <div>
          <el-button :icon="FullScreen" @click="isFullscreen = !isFullscreen" circle />
          <el-button :icon="Close" @click="detailDialogVisible = false" circle />
        </div>
      </div>
      <div class="task-detail-content">
        <el-card shadow="never" header="基础信息" class="mb-16">
          <el-descriptions :column="3" border>
            <el-descriptions-item label="任务名称">{{ selectedTask.name }}</el-descriptions-item>
            <el-descriptions-item label="类型">
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
              <el-progress :percentage="selectedTask.progress || 0" :status="getProgressStatus(selectedTask.status)" :stroke-width="6" />
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
            <el-descriptions-item label="开始时间">{{ selectedTask.started_at ? formatDateTime(selectedTask.started_at) : '未开始' }}</el-descriptions-item>
            <el-descriptions-item label="完成时间">{{ selectedTask.completed_at ? formatDateTime(selectedTask.completed_at) : '未完成' }}</el-descriptions-item>
          </el-descriptions>
        </el-card>
        <el-card shadow="never" header="源端信息" class="mb-16">
          <template v-if="selectedTask.source_type === 'storage' && selectedTask.source_storage_config">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="名称">{{ selectedTask.source_storage_config.name }}</el-descriptions-item>
              <el-descriptions-item label="类型">{{ getStorageTypeText(selectedTask.source_storage_config.type) }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(selectedTask.source_storage_config.status)">
                  {{ getStatusText(selectedTask.source_storage_config.status) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="配置">
                <pre v-if="selectedTask.source_storage_config.config">{{ JSON.stringify(selectedTask.source_storage_config.config, null, 2) }}</pre>
                <span v-else>无</span>
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <template v-else-if="selectedTask.source_type === 'client' && selectedTask.source_client_config">
            <el-descriptions :column="1" border>
              <el-descriptions-item label="名称">{{ selectedTask.source_client_config.name }}</el-descriptions-item>
              <el-descriptions-item label="主机名">{{ selectedTask.source_client_config.hostname }}</el-descriptions-item>
              <el-descriptions-item label="IP">{{ selectedTask.source_client_config.ip_address }}</el-descriptions-item>
              <el-descriptions-item label="端口">{{ selectedTask.source_client_config.port }}</el-descriptions-item>
              <el-descriptions-item label="用户名">{{ selectedTask.source_client_config.username }}</el-descriptions-item>
              <el-descriptions-item label="认证方式">{{ selectedTask.source_client_config.auth_type }}</el-descriptions-item>
              <el-descriptions-item label="状态">
                <el-tag :type="getStatusType(selectedTask.source_client_config.status)">
                  {{ getStatusText(selectedTask.source_client_config.status) }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
          </template>
          <template v-else>
            <div>无</div>
          </template>
        </el-card>
        <el-card shadow="never" header="目标存储" class="mb-16">
          <el-descriptions v-if="selectedTask.target_storage_config" :column="1" border>
            <el-descriptions-item label="名称">{{ selectedTask.target_storage_config.name }}</el-descriptions-item>
            <el-descriptions-item label="类型">{{ getStorageTypeText(selectedTask.target_storage_config.type) }}</el-descriptions-item>
            <el-descriptions-item label="状态">
              <el-tag :type="getStatusType(selectedTask.target_storage_config.status)">
                {{ getStatusText(selectedTask.target_storage_config.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="配置">
              <pre v-if="selectedTask.target_storage_config.config">{{ JSON.stringify(selectedTask.target_storage_config.config, null, 2) }}</pre>
              <span v-else>无</span>
            </el-descriptions-item>
          </el-descriptions>
          <div v-else>无</div>
        </el-card>
        <el-card shadow="never" header="同步选项">
          <el-descriptions v-if="selectedTask.options" :column="3" border>
            <el-descriptions-item label="删除目标多余文件">
              <el-tag :type="selectedTask.options.delete ? 'success' : 'info'">{{ selectedTask.options.delete ? '是' : '否' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="启用压缩传输">
              <el-tag :type="selectedTask.options.compress ? 'success' : 'info'">{{ selectedTask.options.compress ? '是' : '否' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="校验文件完整性">
              <el-tag :type="selectedTask.options.checksum ? 'success' : 'info'">{{ selectedTask.options.checksum ? '是' : '否' }}</el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="带宽限制(MB/s)">{{ selectedTask.options.bandwidth_limit || 0 }}</el-descriptions-item>
            <el-descriptions-item label="并发连接数">{{ selectedTask.options.max_connections || 1 }}</el-descriptions-item>
          </el-descriptions>
          <div v-else>无</div>
        </el-card>
      </div>
    </el-drawer>
    
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
  RefreshRight, More, InfoFilled, Close, FullScreen,
  Edit, Document, Connection, CopyDocument, Delete,
  CircleCheck, Clock, Loading, Warning, CircleClose
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
const loadingTasks = ref(new Set()) // 用于跟踪正在执行操作的任务

// 统计数据
const taskStats = ref({})
const OnlineNodeStats = ref(0)

// 搜索和筛选
const searchQuery = ref('')
const statusFilter = ref('')
const typeFilter = ref('')

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 自动刷新
const autoRefresh = ref(true)
const refreshInterval = ref(null)
const refreshCountdown = ref(30)
const totalTasks = ref(0)

// 对话框状态
const taskDialogVisible = ref(false)
const detailDialogVisible = ref(false)
const logsDialogVisible = ref(false)
const dialogType = ref('create')
const isFullscreen = ref(false)

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
// 获取统计数据
const fetchStatistics = async () => {
  try {
    const response = await axios.get('/api/tasks/statistics')
    taskStats.value = response.data.data
    
    // 获取在线节点数
    const nodesResponse = await axios.get('/api/nodes')
    OnlineNodeStats.value = nodesResponse.data.data.filter(node => node.status === 'online').length
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 自动刷新功能
const startAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
  }
  
  refreshCountdown.value = 30
  refreshInterval.value = setInterval(() => {
    refreshCountdown.value--
    
    if (refreshCountdown.value <= 0) {
      fetchTasks()
      refreshCountdown.value = 30
    }
  }, 1000)
}

const stopAutoRefresh = () => {
  if (refreshInterval.value) {
    clearInterval(refreshInterval.value)
    refreshInterval.value = null
  }
}

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
    fetchStatistics()
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

const handleViewLogs = (task) => {
  currentTaskId.value = task.id
  logsDialogVisible.value = true
  fetchTaskLogs()
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

// 新增任务管理方法
const handleStartTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return
  
  loadingTasks.value.add(task.id)
  try {
      await axios.post(`/api/tasks/${task.id}/start`)
    ElMessage.success('任务启动成功')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '启动失败')
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

const handlePauseTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return
  
  loadingTasks.value.add(task.id)
  try {
    await axios.post(`/api/tasks/${task.id}/pause`)
    ElMessage.success('任务暂停请求已发送')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '暂停失败')
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

const handleResumeTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return
  
  loadingTasks.value.add(task.id)
  try {
    await axios.post(`/api/tasks/${task.id}/resume`)
    ElMessage.success('任务恢复请求已发送')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '恢复失败')
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

const handleCancelTask = async (task) => {
  if (loadingTasks.value.has(task.id)) return
  
  try {
    await ElMessageBox.confirm('确定要取消此任务吗？', '提示', {
      type: 'warning'
    })
    
    loadingTasks.value.add(task.id)
    await axios.post(`/api/tasks/${task.id}/cancel`)
    ElMessage.success('任务取消请求已发送')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '取消失败')
    }
  } finally {
    loadingTasks.value.delete(task.id)
  }
}

const handleDeleteTask = async (task) => {
  try {
    await ElMessageBox.confirm('确定要删除此任务吗？此操作不可恢复。', '危险操作', {
      type: 'error',
      confirmButtonText: '确定删除',
      cancelButtonText: '取消'
    })
    
    const force = ['running', 'assigned'].includes(task.status)
    await axios.delete(`/api/tasks/${task.id}${force ? '?force=true' : ''}`)
    ElMessage.success('删除任务成功')
    fetchTasks()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.message || '删除失败')
    }
  }
}

const handleTestConnection = async (task) => {
  try {
    // 从任务中提取存储配置
    const storageConfig = getStorageConfigFromTask(task)
    console.log(task)
    if (!storageConfig) {
      ElMessage.error('无法获取存储配置信息')
      return
    }
    
    const response = await axios.post('/api/tasks/test-connection', {
      storage_config: storageConfig
    })
    
    ElMessage.success('连接测试任务已创建并启动')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '创建连接测试失败')
  }
}

const handleTestMount = async (task) => {
  try {
    // 从任务中提取存储配置和挂载点
    const storageConfig = getStorageConfigFromTask(task)
    const mountPoint = task.target_path || '/tmp/test_mount'
    
    if (!storageConfig) {
      ElMessage.error('无法获取存储配置信息')
      return
    }
    
    const response = await axios.post('/api/tasks/test-mount', {
      mount_point: mountPoint,
      storage_config: storageConfig
    })
    
    ElMessage.success('挂载测试任务已创建并启动')
    fetchTasks()
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '创建挂载测试失败')
  }
}

const handleDuplicateTask = (task) => {
  // 复制任务逻辑
  const duplicatedTask = {
    ...task,
    id: undefined,
    name: `${task.name} - 副本`,
    status: 'pending',
    created_at: undefined,
    updated_at: undefined,
    started_at: undefined,
    completed_at: undefined
  }
  
  // 设置表单数据并打开创建对话框
  taskForm.value = duplicatedTask
  dialogType.value = 'create'
  taskDialogVisible.value = true
}

// 辅助方法
const canTestConnection = (task) => {
  if (task.status != 'cancelled' && task.status != 'cancel_requested' && task.status != 'failed') {
    return task.source_type === 'storage' && task.source_storage_id
  }
  return false
}

const canTestMount = (task) => {
  if (task.status != 'cancelled' && task.status != 'cancel_requested' && task.status != 'failed') {
    return task.source_type === 'storage' && task.source_storage_id && !isS3Storage(task.source_storage)
  }
  return false
}

const getStorageConfigFromTask = (task) => {
  // 根据任务类型获取存储配置
  if (task.source_type === 'storage') {
    return {
      id: task.source_storage_id,
      name: task.source_storage_name,
      type: task.source_storage_type,
      config: task.source_storage_config
    }
  }

  if (task.source_storage) {
    return {
      id: task.source_storage.id,
      name: task.source_storage.name,
      type: task.source_storage.type,
      config: task.source_storage.config
    }
  }
  return null
}

const handleDropdownCommand = (command, task) => {
  switch (command) {
    case 'logs':
      handleViewLogs(task)
      break
    case 'detail':
      handleViewDetail(task)
      break
    case 'test-connection':
      handleTestConnection(task)
      break
    case 'test-mount':
      handleTestMount(task)
      break
    case 'duplicate':
      handleDuplicateTask(task)
      break
    case 'delete':
      handleDeleteTask(task)
      break
    default:
      console.warn('Unknown command:', command)
  }
}

const handleViewDetail = async (task) => {
  try {
    const response = await axios.get(`/api/tasks/${task.id}`)
    if (response.data.status === 'success') {
      selectedTask.value = response.data.data
    } else {
      ElMessage.error(response.data.message || '获取任务详情失败')
      return
    }
    detailDialogVisible.value = true
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '获取任务详情失败')
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

// 工具函数
const getStatusType = (status) => {
  const types = {
    active: 'success',
    pending: 'info',
    assigned: 'warning',
    running: 'success',
    completed: 'success',
    failed: 'danger',
    cancelled: 'info',
    cancel_requested: 'info'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    active: '活跃',
    pending: '等待中',
    assigned: '已分配',
    running: '运行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消',
    cancel_requested: '取消中'
  }
  return texts[status] || status
}

// 新增：获取状态对应的图标
const getStatusIcon = (status) => {
  const icons = {
    active: CircleCheck,
    pending: Clock,
    assigned: Loading,
    running: Loading,
    completed: CircleCheck,
    failed: CircleClose,
    cancelled: Warning,
    cancel_requested: Warning
  }
  return icons[status] || Clock
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
  fetchStatistics()
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

/* 统计卡片样式 */
.stat-card {
  border: none;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
}

.stat-card.running {
  background: linear-gradient(135deg, #67c23a, #85ce61);
  color: white;
}

.stat-card.pending {
  background: linear-gradient(135deg, #e6a23c, #f0a020);
  color: white;
}

.stat-card.completed {
  background: linear-gradient(135deg, #409eff, #66b1ff);
  color: white;
}

.stat-card.failed {
  background: linear-gradient(135deg, #f56c6c, #f89898);
  color: white;
}

.stat-content {
  text-align: center;
  padding: 10px 0;
}

.stat-number {
  font-size: 36px;
  font-weight: bold;
  line-height: 1;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.refresh-timer {
  color: #909399;
  font-size: 12px;
  margin-left: 8px;
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

.task-detail-drawer :deep(.el-drawer__header) {
  padding: 15px 20px;
  background: #f5f5f5;
  border-bottom: 1px solid #ebeef5;
}

.task-detail-drawer :deep(.el-drawer__body) {
  padding: 0;
  overflow-y: auto;
  max-height: calc(100vh - 200px); /* Adjust for header and footer */
}

.task-detail-drawer :deep(.el-drawer__footer) {
  padding: 15px 20px;
  background: #f5f5f5;
  border-top: 1px solid #ebeef5;
}

.task-detail-content {
  max-height: 80vh;
  overflow-y: auto;
  padding: 20px 10px 10px 10px;
}

.config-section {
  margin-top: 20px;
  min-height: 320px;
}

.config-row {
  min-height: 320px;
}

.config-section .el-card {
  margin-bottom: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.ellipsis {
  display: inline-block;
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}
.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 18px 24px 10px 24px;
  font-size: 20px;
  font-weight: 500;
  border-bottom: 1px solid #ebeef5;
  background: #f5f5f5;
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
.mb-16 {
  margin-bottom: 16px;
}
.stat-flex {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.stat-icon {
  width: 55px;
  height: 55px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 22px;
  margin-right: 14px;
  background: #f5f7fa;
}
.stat-icon.total {
  color: #409EFF;
  background: #e8f3ff;
}
.stat-icon.running {
  color: #67C23A;
  background: #f0f9eb;
}
.stat-icon.pending {
  color: #E6A23C;
  background: #fdf6ec;
}
.stat-icon.completed {
  color: #409EFF;
  background: #e8f3ff;
}
.stat-icon.failed {
  color: #F56C6C;
  background: #fef0f0;
}
.stat-icon.online {
  color: #909399;
  background: #f4f4f5;
}
</style> 