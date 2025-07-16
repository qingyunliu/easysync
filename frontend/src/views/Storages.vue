<template>
  <div class="storages-container">
    <div class="header">
      <div class="header-left">
        <h2>存储管理</h2>
        <p class="page-description">管理和监控存储的创建、配置和使用</p>
      </div>
      <div class="header-right">
        <div class="header-actions">
          <el-input
            v-model="searchQuery"
            placeholder="搜索存储"
            clearable
            class="search-input"
          >
            <template #prefix>
              <Icon icon="mdi:magnify" />
            </template>
          </el-input>
          <el-dropdown @command="handleAddStorage" trigger="click">
            <el-button type="primary">
              <Icon icon="mdi:plus" />&nbsp;添加存储
              <Icon icon="mdi:chevron-down" class="el-icon--right" />
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="nas">添加 NAS 存储</el-dropdown-item>
                <el-dropdown-item command="s3">添加 OBS 存储</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </div>
    
    <!-- NAS存储部分 -->
    <el-collapse v-model="activeCollapse" class="storage-sections">
      <el-collapse-item name="nas">
        <template #title>
          <div class="section-header">
            <Icon icon="mdi:folder-network" />
            <span>NAS 设备</span>
            <el-tag type="warning" class="count-tag">{{ nasStorages.length }}</el-tag>
          </div>
        </template>
        
        <el-table
          :data="filteredNasStorages"
          style="width: 100%"
          v-loading="loading"
          border
          :fit="false"
        >
          <el-table-column prop="name" label="名称" min-width="180" :resizable="true">
            <template #default="{ row }">
              <div class="storage-name-cell">
                <Icon icon="mdi:folder-network" class="icon-nas" :width="20" />
                <el-link type="primary" @click="handleNameClick(row)">
                  {{ row.name }}
                </el-link>
              </div>
            </template>
      </el-table-column>
          <el-table-column prop="config.protocol" label="协议类型">
            <template #default="{ row }">
              <el-tag>{{ row.config.protocol === 'nfs' ? 'NFS' : 'CIFS' }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="config.server" label="服务器" min-width="160" :resizable="true" />
          <el-table-column prop="config.path" label="共享目录" min-width="180" :resizable="true" />
          <el-table-column prop="config.is_mounted" label="挂载状态" min-width="100" :resizable="true">
            <template #default="{ row }">
                  <el-tag :type="row.config.is_mounted ? 'success' : 'info'">
                    {{ row.config.is_mounted ? '已挂载' : '未挂载' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="创建时间" min-width="160" :resizable="true" />
          <el-table-column label="操作" min-width="280" fixed="right">
            <template #default="{ row }">
              <StorageActions :storage="row" @refresh="fetchStorages" />
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>

      <!-- OBS存储部分 -->
      <el-collapse-item name="s3">
        <template #title>
          <div class="section-header">
            <Icon icon="mdi:cloud" />
            <span>OBS 存储</span>
            <el-tag type="primary" class="count-tag">{{ s3Storages.length }}</el-tag>
          </div>
        </template>

        <el-table
          :data="filteredS3Storages"
          style="width: 100%"
          v-loading="loading"
          border
          :fit="false"
        >
          <el-table-column prop="name" label="名称" min-width="180" :resizable="true">
            <template #default="{ row }">
              <div class="storage-name-cell">
                <Icon icon="mdi:cloud" class="icon-s3" :width="20" />
                <el-link type="primary" @click="handleNameClick(row)">
                  {{ row.name }}
                </el-link>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="config.provider" label="提供商" min-width="120" :resizable="true">
            <template #default="{ row }">
              <el-tag :type="getProviderType(row.config.provider)">
                {{ getProviderText(row.config.provider) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="config.access_key" label="Access Key ID" min-width="200" :resizable="true" />
          <el-table-column prop="config.endpoint" label="Endpoint" min-width="200" :resizable="true" />
          <el-table-column prop="config.region" label="区域" min-width="120" :resizable="true" />
          <el-table-column prop="created_at" label="创建时间" min-width="160" :resizable="true" />
          <el-table-column label="操作" min-width="280" fixed="right">
            <template #default="{ row }">
              <StorageActions :storage="row" @refresh="fetchStorages" />
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <!-- 存储详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="存储详情"
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
                <el-descriptions-item label="存储名称">
                  <el-tag type="info">{{ currentStorage.name }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="存储类型">
                  <el-tag :type="getStorageTypeTag(currentStorage.type)">
                    {{ getStorageTypeText(currentStorage.type) }}
                  </el-tag>
                </el-descriptions-item>
                <template v-if="currentStorage.type === 'nas'">
                  <el-descriptions-item label="协议类型">
                    <el-tag :type="currentStorage.config.protocol === 'nfs' ? 'success' : 'warning'">
                      {{ currentStorage.config.protocol === 'nfs' ? 'NFS' : 'CIFS' }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="服务器">
                    {{ currentStorage.config.server }}
                  </el-descriptions-item>
                  <el-descriptions-item label="共享目录">
                    {{ currentStorage.config.path }}
                  </el-descriptions-item>
                  <el-descriptions-item label="协议版本">
                    NFSv{{ currentStorage.config.version }}
                  </el-descriptions-item>
                  <el-descriptions-item label="挂载参数">
                    {{ currentStorage.config.options || '无' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="读写权限">
                    {{ currentStorage.config.permission }}
                  </el-descriptions-item>
                  <el-descriptions-item label="用户名">
                    {{ currentStorage.config.username || '无' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="挂载状态">
                    <el-tag :type="currentStorage.config.is_mounted ? 'success' : 'info'">
                      {{ currentStorage.config.is_mounted ? '已挂载' : '未挂载' }}
                    </el-tag>
                  </el-descriptions-item>
                </template>
                <template v-else>
                  <el-descriptions-item label="提供商">
                    <el-tag :type="getProviderType(currentStorage.config?.provider)">
                      {{ getProviderText(currentStorage.config?.provider) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="Endpoint">
                    {{ currentStorage.config?.endpoint }}
                  </el-descriptions-item>
                  <el-descriptions-item label="区域">
                    {{ currentStorage.config?.region }}
                  </el-descriptions-item>
                </template>
                <el-descriptions-item label="创建时间">
                  {{ formatDate(currentStorage.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="最后更新">
                  {{ formatDate(currentStorage.updated_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 统计信息卡片 -->
            <template v-if="currentStorage.type === 'nas'">
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>存储使用情况</span>
                    <el-button 
                      type="primary" 
                      link 
                      @click="refreshNASStats"
                      :loading="refreshingStats"
                    >
                      <Icon icon="mdi:refresh" :class="{ 'rotating': refreshingStats }" />刷新
                    </el-button>
                  </div>
                </template>
                <div class="stats-grid" v-loading="refreshingStats">
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:harddisk" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatSize(nasStats.total_size) }}</div>
                      <div class="stat-label">总容量</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:database" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatSize(nasStats.used_size) }}</div>
                      <div class="stat-label">已用空间</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:file" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ nasStats.total_files || 0 }}</div>
                      <div class="stat-label">文件数量</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:folder" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ nasStats.total_objects || 0 }}</div>
                      <div class="stat-label">对象数量</div>
                    </div>
                  </div>
                </div>
              </el-card>
            </template>
            <template v-else>
              <!-- 原有的 OBS 统计信息卡片 -->
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>统计信息</span>
                    <el-button 
                      type="primary" 
                      link 
                      @click="refreshStats"
                      :loading="refreshingStats"
                      :disabled="refreshingStats"
                    >
                      <Icon icon="mdi:refresh" :class="{ 'rotating': refreshingStats }" />刷新
                    </el-button>
                  </div>
                </template>
                <div class="stats-grid" v-loading="refreshingStats" element-loading-text="正在获取统计信息...">
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:bucket" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ storageStats.bucket_count || 0 }}</div>
                      <div class="stat-label">存储桶数量</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:file" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ storageStats.object_count || 0 }}</div>
                      <div class="stat-label">对象数量</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:database" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatSize(storageStats.total_size || 0) }}</div>
                      <div class="stat-label">总存储量</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:clock-outline" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatDate(storageStats.last_modified) }}</div>
                      <div class="stat-label">最后更新</div>
                    </div>
                  </div>
                </div>
              </el-card>
            </template>

            <!-- 存储桶使用情况卡片 -->
            <el-card class="info-card" v-if="storageStats.bucket_stats && storageStats.bucket_stats.length > 0">
              <template #header>
                <div class="card-header">
                  <span>存储桶使用情况</span>
                </div>
              </template>
              <el-table :data="storageStats.bucket_stats" style="width: 100%">
                <el-table-column prop="name" label="存储桶名称" min-width="200">
                  <template #default="{ row }">
                    <div class="bucket-name">
                      <Icon icon="mdi:bucket" :width="20" />
                      <span>{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="object_count" label="对象数量" width="120" />
                <el-table-column prop="size" label="存储大小" width="120">
                  <template #default="{ row }">
                    {{ formatSize(row.size) }}
                  </template>
                </el-table-column>
                <el-table-column prop="last_modified" label="最后更新" width="180">
                  <template #default="{ row }">
                    {{ formatDate(row.last_modified) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 文件浏览标签页 -->
        <el-tab-pane v-if="currentStorage.type === 'nas'" label="文件浏览" name="files">
          <div class="files-content scrollable-content">
            <!-- 面包屑导航 -->
            <div class="breadcrumb">
              <el-breadcrumb separator="/">
                <el-breadcrumb-item
                  :class="{ 'is-disabled': !currentPath }"
                  @click="!currentPath && $event.preventDefault(); handleNASBreadcrumbClick('')"
                  style="cursor: pointer;"
                >
                  根目录
                </el-breadcrumb-item>
                <el-breadcrumb-item 
                  v-for="(path, index) in currentPath.split('/').filter(Boolean)" 
                  :key="index"
                  @click="handleNASBreadcrumbClick(
                    currentPath.split('/').filter(Boolean).slice(0, index + 1).join('/') + '/'
                  )"
                  style="cursor: pointer;"
                >
                  {{ path }}
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>

            <!-- 文件列表 -->
            <el-table
              :data="files"
              style="width: 100%"
              v-loading="loadingFiles"
              @row-click="handleFileClick"
            >
              <el-table-column label="名称" min-width="300">
                <template #default="{ row }">
                  <div class="file-name">
                    <Icon :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'" :width="20" />
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="size" label="大小" width="120">
                <template #default="{ row }">
                  {{ row.type === 'directory' ? '-' : formatSize(row.size) }}
                </template>
              </el-table-column>
              <el-table-column prop="modified_time" label="修改时间" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.modified_time) }}
                </template>
              </el-table-column>
              <el-table-column label="操作" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button 
                    v-if="row.type !== 'directory'"
                    type="primary" 
                    size="small"
                    @click.stop="handleFileDownload(row)"
                  >
                    <Icon icon="mdi:download" />
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination">
              <el-pagination
                v-model:current-page="currentPage"
                v-model:page-size="pageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="total"
                layout="total, sizes, prev, pager, next"
                @size-change="handleSizeChange"
                @current-change="handleCurrentChange"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 存储桶列表标签页 -->
        <el-tab-pane v-if="currentStorage.type === 's3'" label="存储桶" name="buckets">
          <div class="buckets-content scrollable-content">
            <el-table
              :data="buckets"
              style="width: 100%"
              v-loading="loadingBuckets"
              @row-click="handleBucketClick"
            >
              <el-table-column prop="name" label="存储桶名称" min-width="200">
                <template #default="{ row }">
                  <div class="bucket-name">
                    <Icon icon="mdi:bucket" :width="20" />
                    <span>{{ row.name }}</span>
                  </div>
                  </template>
              </el-table-column>
              <el-table-column prop="creationDate" label="创建时间" min-width="180">
                <template #default="{ row }">
                  {{ formatDate(row.creationDate) }}
                </template>
              </el-table-column>
              <el-table-column prop="region" label="区域" min-width="120" />
            </el-table>
            <div class="pagination">
              <el-pagination
                v-model:current-page="bucketPage"
                v-model:page-size="bucketPageSize"
                :page-sizes="[10, 20, 50, 100]"
                :total="bucketTotal"
                layout="total, sizes, prev, pager, next"
                @size-change="handleBucketPageSizeChange"
                @current-change="handleBucketPageChange"
              />
            </div>
          </div>
        </el-tab-pane>

        <!-- 对象列表标签页 -->
        <el-tab-pane v-if="currentStorage.type === 's3'" label="对象列表" name="objects">
          <div class="objects-content scrollable-content">
            <!-- 面包屑导航 -->
            <template v-if="currentBucket">
              <div class="breadcrumb">
                <el-breadcrumb separator="/">
                  <el-breadcrumb-item
                    :class="{ 'is-disabled': !currentPath }"
                    @click="!currentPath && $event.preventDefault(); handleS3BreadcrumbClick('')"
                    style="cursor: pointer;"
                  >
                    {{ currentBucket }}
                  </el-breadcrumb-item>
                  <el-breadcrumb-item 
                    v-for="(path, index) in currentPath.split('/').filter(Boolean)" 
                    :key="index"
                    @click="handleS3BreadcrumbClick(
                      currentPath.split('/').filter(Boolean).slice(0, index + 1).join('/') + '/'
                    )"
                    style="cursor: pointer;"
                  >
                    {{ path }}
                  </el-breadcrumb-item>
                </el-breadcrumb>
              </div>

              <!-- 对象列表 -->
              <el-table
                :data="objects"
                style="width: 100%"
                v-loading="loadingObjects"
                @row-click="handleObjectClick"
              >
                <el-table-column label="名称" min-width="300">
                  <template #default="{ row }">
                    <div class="object-name">
                      <Icon :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'" :width="20" />
                      <span>{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="size" label="大小" width="120">
                  <template #default="{ row }">
                    {{ row.type === 'directory' ? '-' : formatSize(row.size) }}
                  </template>
                </el-table-column>
                <el-table-column prop="lastModified" label="最后修改时间" width="180">
                  <template #default="{ row }">
                    {{ formatDate(row.lastModified) }}
                  </template>
                </el-table-column>
                <el-table-column label="操作" width="120" fixed="right">
                  <template #default="{ row }">
                      <el-button 
                      v-if="row.type !== 'directory'"
                        type="primary" 
                        size="small"
                      @click.stop="handleS3Download(row)"
                      >
                      <Icon icon="mdi:download" />
                      </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 分页 -->
              <div class="pagination">
                <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="total"
                  layout="total, sizes, prev, pager, next"
                  @size-change="handleSizeChange"
                  @current-change="handleCurrentChange"
                />
              </div>
            </template>
            <template v-else>
              <!-- 没有选择存储桶 -->
              <div style="padding: 40px; text-align: center; color: #888;">
                <Icon icon="mdi:folder-outline" :width="40" />
                <p>请先选择一个存储桶</p>
              </div>
            </template>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>

    <!-- 存储编辑对话框 -->
    <el-dialog
      :title="dialogType === 'add' ? '添加存储' : '编辑存储'"
      v-model="dialogVisible"
      width="600px"
      :before-close="handleDialogClose"
    >
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="120px" class="storage-form">
        <el-form-item label="存储名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入存储名称" />
        </el-form-item>

        <template v-if="form.type === 'nas'">
          <el-form-item label="协议类型" prop="config.protocol">
            <el-radio-group v-model="form.config.protocol">
              <el-radio label="cifs">CIFS</el-radio>
              <el-radio label="nfs">NFS</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item label="IP地址" prop="config.server">
            <el-input v-model="form.config.server" />
          </el-form-item>
          <el-form-item label="共享目录" prop="config.path">
            <el-input v-model="form.config.path" />
          </el-form-item>
          <el-form-item label="读写权限" prop="config.permission">
            <el-radio-group v-model="form.config.permission">
              <el-radio label="rw">读写</el-radio>
              <el-radio label="ro">只读</el-radio>
            </el-radio-group>
          </el-form-item>
          <!-- NFS专属 -->
          <template v-if="form.config.protocol === 'nfs'">
            <el-form-item label="协议版本" prop="config.version">
              <el-select v-model="form.config.version">
                <el-option label="NFSv3" value="3" />
                <el-option label="NFSv4.0" value="4.0" />
                <el-option label="NFSv4.1" value="4.1" />
              </el-select>
            </el-form-item>
          </template>
          <!-- CIFS专属 -->
          <template v-else>
            <el-form-item label="协议版本" prop="config.version">
              <el-select v-model="form.config.version">
                <el-option label="CIFSv2.0" value="2.0" />
                <el-option label="CIFSv3.0" value="3.0" />
              </el-select>
            </el-form-item>
            <el-form-item label="用户名" prop="config.username">
              <el-input v-model="form.config.username" />
            </el-form-item>
            <el-form-item label="密码" prop="config.password">
              <el-input v-model="form.config.password" type="password" />
            </el-form-item>
            <el-form-item label="工作组" prop="config.workgroup">
              <el-input v-model="form.config.workgroup" />
            </el-form-item>
          </template>

          <!-- 高级选项折叠面板 -->
          <div class="storage-advanced-section">
            <el-collapse v-model="advancedOptions">
              <el-collapse-item title="高级选项" name="advanced">
                <el-form-item label="端口" prop="config.port">
                  <el-input v-model="form.config.port" placeholder="默认端口：NFS(2049)、CIFS(445)" />
                </el-form-item>
                <el-form-item label="挂载参数" prop="config.options">
                  <el-input v-model="form.config.options" placeholder="例如：vers=x.0,xxx=xxx" />
                  <div class="storage-form-tip">
                    <el-icon><InfoFilled /></el-icon>
                    <span>NFS示例：vers=3,rsize=1048576,wsize=1048576,hard,timeo=600,retrans=2</span>
                  </div>
                  <div class="storage-form-tip">
                    <el-icon><InfoFilled /></el-icon>
                    <span>CIFS示例：vers=3.0,iocharset=utf8,file_mode=0777,dir_mode=0777</span>
                  </div>
                </el-form-item>
              </el-collapse-item>
            </el-collapse>
          </div>
        </template>

        <template v-else-if="form.type === 's3'">
          <el-form-item label="提供商" prop="config.provider">
            <el-select v-model="form.config.provider" placeholder="请选择提供商">
              <el-option label="AWS" value="aws" />
              <el-option label="Google Cloud" value="google" />
              <el-option label="腾讯云" value="tencent" />
              <el-option label="阿里云" value="aliyun" />
              <el-option label="华为云" value="huawei" />
              <el-option label="MinIO" value="minio" />
              <el-option label="其他" value="other" />
              <!-- 其他选项 -->
            </el-select>
          </el-form-item>
          <el-form-item label="Access Key ID" prop="config.access_key">
            <el-input v-model="form.config.access_key" placeholder="请输入Access Key" />
          </el-form-item>
          <el-form-item label="Secret Key ID" prop="config.secret_key">
            <el-input v-model="form.config.secret_key" type="password" placeholder="请输入 Secret Key"/>
          </el-form-item>
          <el-form-item label="Endpoint" prop="config.endpoint">
            <el-input v-model="form.config.endpoint" placeholder="请输入Endpoint" />
          </el-form-item>
          <el-form-item label="区域" prop="config.region">
            <el-input v-model="form.config.region" placeholder="请输入区域" />
          </el-form-item>
          <el-form-item label="存储桶" prop="config.bucket">
            <el-input v-model="form.config.bucket" placeholder="请输入存储桶名称">
            </el-input>
          </el-form-item>
          <el-form-item label="路径样式" prop="config.path_style">
            <el-switch v-model="form.config.path_style" />
          </el-form-item>
          <!-- 继续渲染 S3/OBS 相关项 -->
        </template>

        <el-form-item label="测试节点" prop="test_node_id">
          <el-select v-model="testNodeId" placeholder="请选择节点">
            <el-option v-for="node in availableNodes" :key="node.id" :label="node.name + '（' + node.ipaddress + '）'" :value="node.id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button @click="handleTestConnect">测试连接</el-button>
          <el-button type="primary" @click="handleSubmit">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon } from '@iconify/vue'
import StorageActions from '@/components/StorageActions.vue'
import axios from 'axios'

const storages = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogType = ref('add')
const drawerVisible = ref(false)
const activeTab = ref('basic')
const currentStorage = ref({})

// S3 存储相关状态
const storageStats = ref({
  bucket_count: 0,
  object_count: 0,
  total_size: 0,
  last_modified: null,
  bucket_stats: []
})

// NAS 存储相关的状态
const nasStats = ref({
  total_size: 0,
  used_size: 0,
  free_size: 0,
  total_files: 0,
  total_objects: 0,
  last_modified: null
})

// 文件列表相关
const files = ref([])
const loadingFiles = ref(false)
const searchQuery = ref('')
const selectedFiles = ref([])

const form = ref({
  name: '',
  type: 'nas',
  config: {
    // S3 配置
    provider: 'aws',
    access_key: '',
    secret_key: '',
    endpoint: '',
    region: '',
    path_style: false,
    bucket: '',

    // NAS 配置
    protocol: 'cifs', // 默认选中 CIFS
    server: '',
    path: '',
    permission: 'rw',
    version: '',
    port: '',
    options: '',
    workgroup: '',
    username: '',
    password: ''
  }
})

const folderForm = ref({
  name: ''
})

const renameForm = ref({
  name: ''
})

const folderRules = {
  name: [
    { required: true, message: '请输入文件夹名称', trigger: 'blur' }
  ]
}

const renameRules = {
  name: [
    { required: true, message: '请输入新名称', trigger: 'blur' }
  ]
}

const folderFormRef = ref(null)
const renameFormRef = ref(null)

// 添加存储类型相关的响应式变量
const activeCollapse = ref(['nas', 's3']) // 默认展开所有部分

const nasStorages = computed(() => 
  storages.value.filter(storage => storage.type === 'nas')
)

const s3Storages = computed(() => 
  storages.value.filter(storage => storage.type === 's3')
)

// 搜索过滤
const filteredNasStorages = computed(() => {
  if (!searchQuery.value) return nasStorages.value
  const query = searchQuery.value.toLowerCase()
  return nasStorages.value.filter(storage => 
    storage.name.toLowerCase().includes(query) ||
    storage.config.server.toLowerCase().includes(query) ||
    storage.config.path.toLowerCase().includes(query)
  )
})

const filteredS3Storages = computed(() => {
  if (!searchQuery.value) return s3Storages.value
  const query = searchQuery.value.toLowerCase()
  return s3Storages.value.filter(storage => 
    storage.name.toLowerCase().includes(query) ||
    storage.config.endpoint.toLowerCase().includes(query) ||
    storage.config.bucket.toLowerCase().includes(query)
  )
})

// 存储桶相关
const buckets = ref([])
const bucketPage = ref(1)
const bucketPageSize = ref(20)
const bucketTotal = ref(0)
const loadingBuckets = ref(false)
const currentBucket = ref('')
const currentPath = ref('')
const objects = ref([])
const loadingObjects = ref(false)
const currentPage = ref(1)
const pageSize = ref(20)
const total = ref(0)

// 添加刷新状态变量
const refreshingStats = ref(false)

// 添加高级选项的响应式变量
const advancedOptions = ref([])  // 默认不展开

const testNodeId = ref('')
const availableNodes = ref([])

// 获取存储列表
const fetchStorages = async () => {
  try {
    loading.value = true
    const response = await axios.get('/api/storages');
      storages.value = response.data.data
  } catch (error) {
    ElMessage.error('获取存储列表失败')
  } finally {
    loading.value = false
  }
}

// 获取存储类型标签
const getStorageTypeTag = (type) => {
  switch (type) {
    case 'nas':
      return 'warning'
    case 's3':
      return 'info'
    default:
      return 'info'
  }
}

// 获取存储类型文本
const getStorageTypeText = (type) => {
  switch (type) {
    case 'nas':
      return 'NAS存储'
    case 's3':
      return 'S3存储'
    default:
      return '未知类型'
  }
}

// 获取状态类型
const getStatusType = (status) => {
  switch (status) {
    case 'active':
      return 'success'
    case 'error':
      return 'danger'
    case 'disabled':
      return 'info'
    default:
      return 'info'
  }
}

// 获取状态文本
const getStatusText = (status) => {
  switch (status) {
    case 'active':
      return '正常'
    case 'error':
      return '错误'
    case 'disabled':
      return '已禁用'
    default:
      return '未知'
  }
}

// 格式化日期
const formatDate = (date) => {
  if (!date) return '-'
  return new Date(date).toLocaleString()
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

// 获取使用率状态
const getUsageStatus = (usage) => {
  if (usage >= 90) return 'exception'
  if (usage >= 70) return 'warning'
  return 'success'
}

// 显示编辑对话框
const showEditDialog = (row) => {
  dialogType.value = 'edit'
  form.value = {
    id: row.id,
    name: row.name,
    type: row.type,
    config: {
      // s3 配置
      provider: row.config?.provider || 'aws',
      access_key: row.config?.access_key || '',
      secret_key: row.config?.secret_key || '',
      endpoint: row.config?.endpoint || '',
      region: row.config?.region || '',
      bucket: row.config?.bucket || '',
      path_style: row.config?.path_style || false,
      protocol: row.type === 's3' ? (row.config?.protocol || 'https') : (row.config?.protocol || 'cifs'),
      // NAS 配置
      server: row.config?.server || '',
      path: row.config?.path || '',
      version: row.config?.version || '',
      options: row.config?.options || '',
      port: row.config?.port || '',
      permission: row.config?.permission || '',
      workgroup: row.config?.workgroup || '',
      username: row.config?.username || '',
      password: row.config?.password || '',
    }
  }
  // 打印编辑的表单数据，用于调试
  dialogVisible.value = true
}

// 获取存储信息
const getStorageInfo = async (row) => {
  try {
    row.fetching = true
    const response = await axios.get(`/api/storages/${row.id}/info`)
    storageStats.value = response.data.data
    ElMessage.success('获取信息成功')
  } catch (error) {
    ElMessage.error('获取信息失败')
  } finally {
    row.fetching = false
  }
}

// 显示存储详情
const handleNameClick = async (row) => {
  try {
    currentStorage.value = row
    drawerVisible.value = true
    activeTab.value = 'basic'
    bucketPage.value = 1
    bucketPageSize.value = 10

    if (row.type === "nas") {
      // 获取存储桶列表
      await fetchNASDetails()
      await fetchFiles()
    } else {
      await fetchBuckets()
    }
  } catch (error) {
    ElMessage.error('加载存储详情失败')
  }
}

// 处理文件点击
const handleFileClick = (row) => {
  if (row.type === 'directory') {
    currentPath.value = row.path
    currentPage.value = 1
    fetchFiles()
  }
}

// 获取 nas 存储信息
const fetchNASDetails = async () => {
  try {
    loading.value = true
    const response = await axios.get(`/api/storages/${currentStorage.value.id}/nas/stats`)
    nasStats.value = response.data.data
  } catch (error) {
    ElMessage.error('获取 NAS 存储信息失败')
  } finally {
    loading.value = false
  }
}

// 刷新 NAS 统计信息
const refreshNASStats = async () => {
  try {
    refreshingStats.value = true
    await fetchNASDetails()
    ElMessage.success('统计信息已更新')
  } catch (error) {
    ElMessage.error('更新统计信息失败')
  } finally {
    refreshingStats.value = false
  }
}

// 下载文件
const handleFileDownload = async (file) => {
  try {
    const response = await axios.get(`/api/storages/${currentStorage.value.id}/nas/download`, {
      params: { path: file.path },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', file.name)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 获取文件列表
const fetchFiles = async () => {
  try {
    loadingFiles.value = true
    const response = await axios.get(`/api/storages/${currentStorage.value.id}/nas/files`, {
      params: {
        path: currentPath.value,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    files.value = response.data.data.files
    total.value = response.data.data.total
  } catch (error) {
    ElMessage.error('获取文件列表失败')
  } finally {
    loadingFiles.value = false
  }
}

// 获取对象存储存储桶列表
const fetchBuckets = async () => {
  try {
    loadingBuckets.value = true
    const response = await axios.get(`/api/storages/${currentStorage.value.id}/buckets`, {
      params: {
        page: bucketPage.value,
        page_size: bucketPageSize.value
      }
    })
    if (response.data.data.buckets && Array.isArray(response.data.data.buckets)) {
      buckets.value = response.data.data.buckets
      bucketTotal.value = response.data.data.total
    } else {
      buckets.value = response.data.data
      bucketTotal.value = response.data.data.length
    }
  } catch (error) {
    ElMessage.error('获取存储桶列表失败')
      } finally {
    loadingBuckets.value = false
  }
}

// 处理分页
const handleBucketPageChange = (page) => {
  bucketPage.value = page
  fetchBuckets()
}

// 处理分页大小变化
const handleBucketPageSizeChange = (size) => {
  bucketPageSize.value = size
  bucketPage.value = 1
  fetchBuckets()
}

// 获取对象列表
const fetchObjects = async () => {
  if (!currentBucket.value) {
    objects.value = []
    total.value = 0
    return
  }

  try {
    loadingObjects.value = true
    const response = await axios.get(`/api/storages/${currentStorage.value.id}/objects`, {
      params: {
        bucket: currentBucket.value,
        prefix: currentPath.value,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })
    objects.value = response.data.data.objects
    total.value = response.data.data.total
  } catch (error) {
    ElMessage.error('获取对象列表失败')
  } finally {
    loadingObjects.value = false
  }
}

// 处理存储桶点击
const handleBucketClick = (row) => {
  currentBucket.value = row.name
  currentPath.value = ''
  currentPage.value = 1
  activeTab.value = 'objects'
  fetchObjects()
}

// 处理对象点击
const handleObjectClick = (row) => {
  if (row.type === 'directory') {
    currentPath.value = row.prefix
    currentPage.value = 1
    fetchObjects()
  }
}

// 处理面包屑点击
const handleS3BreadcrumbClick = (path) => {
  if (!currentBucket.value) return 
  currentPath.value = path
  currentPage.value = 1
  fetchObjects()
}

// 处理面包屑点击
const handleNASBreadcrumbClick = (path) => {
  currentPath.value = path
  currentPage.value = 1
  fetchFiles()
}

// 处理分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1  // 重置到第一页
  if (currentStorage.value.type === 'nas') {
    fetchFiles()
  } else {
  fetchObjects()
  }
}

// 处理页码变化
const handleCurrentChange = (val) => {
  currentPage.value = val
  if (currentStorage.value.type === 'nas') {
    fetchFiles()
  } else {
  fetchObjects()
  }
}

// 处理下载
const handleS3Download = async (row) => {
  try {
    const response = await axios.get(`/api/storages/${currentStorage.value.id}/download`, {
      params: {
        bucket: currentBucket.value,
        key: row.key
      },
      responseType: 'blob'
    })
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', row.name)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 关闭抽屉
const handleDrawerClose = () => {
  drawerVisible.value = false
  activeTab.value = 'basic'
  currentStorage.value = {}
  buckets.value = []
  bucketPage.value = 1
  bucketPageSize.value = 10
  bucketTotal.value = 0
  objects.value = []
  currentBucket.value = ''
  currentPath.value = ''
  currentPage.value = 1
  total.value = 0
}

// 添加提供商相关的辅助函数
const getProviderType = (provider) => {
  const types = {
    'aws': 'success',
    'google': 'danger',
    'tencent': 'warning',
    'aliyun': 'primary',
    'huawei': 'info',
    'minio': 'success',
    'other': 'info'
  }
  return types[provider] || 'info'
}

const getProviderText = (provider) => {
  const texts = {
    'aws': 'AWS',
    'google': 'Google Cloud',
    'tencent': '腾讯云',
    'aliyun': '阿里云',
    'huawei': '华为云',
    'minio': 'MinIO',
    'other': '其他'
  }
  return texts[provider] || '未知'
}

// 处理添加存储
const handleAddStorage = (type) => {
  dialogType.value = 'add'
  form.value = {
    name: '',
    type: type,
    config: {
      // S3 配置
      provider: type === 's3' ? 'aws' : null,
      access_key: '',
      secret_key: '',
      endpoint: '',
      region: '',
      bucket: '',
      path_style: false,
      protocol: type === 's3' ? 'https' : 'cifs', // 根据类型设置默认协议

      // NAS 配置
      server: '',
      path: '',
      permission: 'rw',
      version: '',
      options: '',
      port: '',
      workgroup: '',
      username: '',
      password: ''
    }
  }
  // 打印初始化的表单数据，用于调试
  console.log('初始化的表单数据:', form.value)
  dialogVisible.value = true
}

// 表单验证规则
const formRules = computed(() => {
  const rules = {
  name: [
    { required: true, message: '请输入存储名称', trigger: 'blur' }
    ]
  }
  
  if (form.value.type === 's3') {
    rules['config.provider'] = [
    { required: true, message: '请选择提供商', trigger: 'change' }
    ]
    rules['config.access_key'] = [
    { required: true, message: '请输入Access Key', trigger: 'blur' }
    ]
    rules['config.secret_key'] = [
    { required: true, message: '请输入Secret Key', trigger: 'blur' }
    ]
    rules['config.endpoint'] = [
    { required: true, message: '请输入Endpoint', trigger: 'blur' }
    ]
    rules['config.region'] = [
    { 
      required: true, 
      message: '请输入区域', 
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (form.value.config.provider === 'minio') {
          callback()
        } else if (!value) {
          callback(new Error('请输入区域'))
        } else {
          callback()
        }
      }
    }
  ]
    rules['config.bucket'] = [
      { required: true, message: '请输入存储桶名称', trigger: 'blur' }
    ]
  } else if (form.value.type === 'nas') {
    rules['config.server'] = [
      { required: true, message: '请输入服务器地址', trigger: 'blur' }
    ]
    rules['config.path'] = [
      { required: true, message: '请输入共享目录路径', trigger: 'blur' }
    ]
    rules['config.protocol'] = [
      { required: true, message: '请选择协议类型', trigger: 'change' }
    ]
    rules['config.permission'] = [
      { required: true, message: '请选择读写权限', trigger: 'change' }
    ]
    rules['config.version'] = [
      { required: true, message: '请选择协议版本', trigger: 'change' }
    ]
  }
  
  return rules
})

const formRef = ref(null)

// 处理对话框关闭
const handleDialogClose = () => {
  dialogVisible.value = false
  form.value = {
    name: '',
    type: 'nas',
    config: {
      // S3 配置
      provider: 'aws',
      access_key: '',
      secret_key: '',
      endpoint: '',
      region: '',
      bucket: '',
      path_style: false,
      // NAS 配置
      protocol: 'cifs',
      server: '',
      path: '',
      permission: 'rw',
      version: '',
      port: '',
      options: '',
      workgroup: '',
      username: '',
      password: ''
    }
  }
}

// 处理表单提交
const handleSubmit = async () => {
  try {
    await formRef.value.validate()
    
    // 根据存储类型构建配置对象
    let config = {}
    if (form.value.type === 's3') {
      config = {
        provider: form.value.config.provider || 'aws',
        access_key: form.value.config.access_key || '',
        secret_key: form.value.config.secret_key || '',
        endpoint: form.value.config.endpoint || '',
        region: form.value.config.provider === 'minio' ? 'cn-north-1' : (form.value.config.region || ''),
        bucket: form.value.config.bucket || '',
        path_style: form.value.config.path_style || false,
        protocol: 'https'  // 默认使用https协议
      }
    } else if (form.value.type === 'nas') {
      config = {
        protocol: form.value.config.protocol || '',
        permission: form.value.config.permission || '',
        server: form.value.config.server || '',
        path: form.value.config.path || '',
        version: form.value.config.version || '',
        options: form.value.config.options || '',
        workgroup: form.value.config.workgroup || '',
        username: form.value.config.username || '',
        password: form.value.config.password || ''
      }
    }

    const submitData = {
      id: form.value.id,
      name: form.value.name,
      type: form.value.type,
      config: config
    }
    
    if (dialogType.value === 'add') {
      const response = await axios.post('/api/storages', submitData)
      ElMessage.success('添加存储成功')
    } else {
      const response = await axios.put(`/api/storages/${form.value.id}`, submitData)
      ElMessage.success('更新存储成功')
    }
    dialogVisible.value = false
    fetchStorages()
  } catch (error) {
    console.error('提交错误:', error)
    if (error.response) {
      console.error('错误响应:', error.response.data)
      ElMessage.error(error.response.data.message || '操作失败')
    } else if (error.message) {
      ElMessage.error(error.message)
    }
  }
}

// 获取可用节点列表（只显示在线且Agent已安装的节点）
const fetchAvailableNodes = async () => {
  try {
    const response = await axios.get('/api/nodes')
    // 只保留在线且Agent已安装的节点
    availableNodes.value = (response.data.data || []).filter(
      node => node.status === 'online' && node.agent_status === 'running'
    )
  } catch (error) {
    ElMessage.error('获取节点列表失败')
  }
}

// 打开对话框时拉取节点
watch(dialogVisible, (val) => {
  if (val) fetchAvailableNodes()
})

// 处理测试连接
const handleTestConnect = async () => {
  try {
    await formRef.value.validate()
    if (!testNodeId.value) {
      ElMessage.warning('请先选择一个测试节点')
      return
    }
    // 根据存储类型构建配置对象
    let config = {}
    if (form.value.type === 's3') {
      config = {
        provider: form.value.config.provider || 'aws',
        access_key: form.value.config.access_key || '',
        secret_key: form.value.config.secret_key || '',
        endpoint: form.value.config.endpoint || '',
        region: form.value.config.provider === 'minio' ? 'cn-north-1' : (form.value.config.region || ''),
        bucket: form.value.config.bucket || '',
        path_style: form.value.config.path_style || false,
        protocol: 'https'
      }
    } else if (form.value.type === 'nas') {
      config = {
        protocol: form.value.config.protocol || '',
        permission: form.value.config.permission || '',
        server: form.value.config.server || '',
        path: form.value.config.path || '',
        version: form.value.config.version || '',
        options: form.value.config.options || '',
        workgroup: form.value.config.workgroup || '',
        username: form.value.config.username || '',
        password: form.value.config.password || ''
      }
    }
    const submitData = {
      type: form.value.type,
      config: config,
      node_id: testNodeId.value
    }
    const response = await axios.post('/api/storages/test-connection', submitData)
    if (response.data.status == "success") { 
      ElMessage.success("测试连接成功: " + (response.data.data?.message || ''))
    } else {
      ElMessage.error(response.data.message || '测试连接失败')
    }
    } catch (error) {
    if (error.response) {
      ElMessage.error(error.response.data.message || '操作失败')
    } else if (error.message) {
      ElMessage.error(error.message)
    }
  }
}

// 上传相关
const uploadHeaders = computed(() => ({
  Authorization: `Bearer ${localStorage.getItem('token')}`
}))

const uploadData = computed(() => ({
  storage_id: currentStorage.value.id
}))

const beforeUpload = (file) => {
  // 可以在这里添加文件大小、类型等限制
  return true
}

const handleUploadSuccess = (response) => {
  if (response.status === 'success') {
    ElMessage.success('上传成功')
    fetchObjects(currentStorage.value.id)
  } else {
    ElMessage.error(response.message || '上传失败')
  }
}

const handleUploadError = () => {
  ElMessage.error('上传失败')
}

// 修改刷新统计信息函数
const refreshStats = async () => {
  try {
    await ElMessageBox.confirm('此动作将会重新调用接口，如果桶数据量较多那么时间会较长，请耐心等待', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    
    refreshingStats.value = true
    const response = await axios.get(`/api/storages/${currentStorage.value.id}/stats`)
    storageStats.value = response.data.data
    ElMessage.success('统计信息已更新')
  } catch (error) {
    // 如果是用户取消操作,不显示错误提示
    if (error !== 'cancel') {
      ElMessage.error('获取统计信息失败')
    }
  } finally {
    refreshingStats.value = false
  }
}

// 监听协议类型变化
watch(() => form.value.config.protocol, (newProtocol) => {
  // 根据协议类型设置默认版本
  if (newProtocol === 'nfs') {
    form.value.config.version = '3'  // 默认使用 NFSv3
  } else if (newProtocol === 'cifs') {
    form.value.config.version = '2.0'  // 默认使用 CIFSv2.0
  }
})

// 添加事件监听
onMounted(() => {
  fetchStorages()

  // 监听编辑存储事件
  window.addEventListener('edit-storage', (event) => {
    showEditDialog(event.detail)
  })

  // 监听更新存储统计信息事件
  window.addEventListener('update-storage-stats', (event) => {
    storageStats.value = event.detail
  })
})

// 在组件卸载时移除事件监听
onUnmounted(() => {
  window.removeEventListener('edit-storage', showEditDialog)
  window.removeEventListener('update-storage-stats', (event) => {
    storageStats.value = event.detail
  })
})
</script>

<style scoped>
.storages-container {
  padding: 20px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-actions {
  display: flex;
  gap: 16px;
  align-items: center;
}

.search-input {
  width: 300px;
}

.storage-sections {
  margin-bottom: 30px;
  padding: 20px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 500;
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

.count-tag {
  margin-left: 8px;
  font-size: 12px;
}

.storage-name-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon-nas {
  color: var(--el-color-warning);
}

.icon-nfs {
  color: var(--el-color-success);
}

.icon-s3 {
  color: var(--el-color-primary);
}

:deep(.el-collapse-item__header) {
  font-size: 16px;
  padding: 12px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 4px;
  margin-bottom: 8px;
}

:deep(.el-collapse-item__content) {
  padding: 16px 5px;
}

:deep(.el-table__row) {
  transition: all 0.3s ease;
}

:deep(.el-table__row:hover) {
  background-color: var(--el-color-primary-light-9);
}

@media screen and (max-width: 768px) {
  .header-actions {
    flex-direction: column;
    width: 100%;
  }

  .header-right {
    margin-top: 15px;
  }

  .search-input {
    width: 100%;
  }
}

:deep(.el-button .iconify) {
  margin-right: 4px;
  font-size: 16px;
}

:deep(.el-button--text .iconify) {
  margin-right: 8px;
  font-size: 18px;
}

.iconify {
  vertical-align: middle;
}

:deep(.el-table) {
  width: 100% !important;
  table-layout: auto !important;
}

:deep(.el-table__body) {
  width: 100% !important;
}

:deep(.el-table__header) {
  width: 100% !important;
}

:deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

:deep(.el-table__header-wrapper) {
  overflow-x: hidden;
}

.storage-form {
  padding: 0 0;
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

:deep(.el-select) {
  width: 100%;
}

:deep(.el-form-item) {
  margin-bottom: 22px;
}

:deep(.el-dialog__body) {
  padding: 20px 0;
}

.buckets-content,
.objects-content {
  padding: 20px;
}

.bucket-name,
.object-name {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.breadcrumb {
  margin-bottom: 16px;
  padding: 8px 16px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 4px;
}

.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  padding: 0 20px;
}

:deep(.el-pagination) {
  justify-content: flex-end;
  margin: 0;
}

:deep(.el-pagination .el-select .el-input) {
  width: 100px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  padding: 10px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background-color: var(--el-color-primary-light-8);
  border-radius: 8px;
  color: var(--el-color-primary);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

:deep(.el-card__header) {
  padding: 12px 20px;
  border-bottom: 1px solid var(--el-border-color-light);
}

:deep(.el-card__body) {
  padding: 20px;
}

.info-card {
  margin-bottom: 20px;
}

.info-card:last-child {
  margin-bottom: 0;
}

/* 添加旋转动画 */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 修改加载样式 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-loading-spinner) {
  margin-top: 20px;
}

:deep(.el-loading-text) {
  margin-top: 10px;
  color: var(--el-color-primary);
}

/* 文件浏览相关样式 */
.files-content {
  padding: 20px;
}

.file-name {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.file-name:hover {
  color: var(--el-color-primary);
}

.breadcrumb {
  margin-bottom: 16px;
  padding: 8px 16px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 4px;
}

/* 统计信息卡片样式 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  padding: 10px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 8px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

.stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  background-color: var(--el-color-primary-light-8);
  border-radius: 8px;
  color: var(--el-color-primary);
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin-top: 4px;
}

/* 旋转动画 */
.rotating {
  animation: rotate 1s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 加载状态样式 */
:deep(.el-loading-mask) {
  background-color: rgba(255, 255, 255, 0.9);
}

:deep(.el-loading-spinner) {
  margin-top: 20px;
}

:deep(.el-loading-text) {
  margin-top: 10px;
  color: var(--el-color-primary);
}

/* 添加表单提示样式 */
.form-tip {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
}

.form-tip .el-icon {
  font-size: 14px;
  color: var(--el-color-info);
}

:deep(.el-collapse-item) {
  margin-bottom: 3px;
}

:deep(.el-collapse-item__header) {
  font-size: 14px;
  color: var(--el-text-color-primary);
  background-color: white;
  border-radius: 4px;
  padding: 8px 16px;
  margin-bottom: 0.9px;
}

:deep(.el-collapse-item__content) {
  padding: 16px;
  border-radius: 0 0 4px 4px;
  margin-top: 4px;
}

/* 存储高级选项样式 */
.storage-advanced-section {
  margin-top: 8px;
}

.storage-advanced-section :deep(.el-collapse-item__header) {
  font-size: 14px;
  color: var(--el-text-color-primary);
  border: none;
}

.storage-advanced-section :deep(.el-collapse-item__header::before) {
  display: none;
}

.storage-advanced-section :deep(.el-collapse-item__content) {
  padding: 0;
  border: none;
}

.storage-advanced-section :deep(.el-collapse-item__wrap) {
  border: none;
}

/* 存储表单提示样式 */
.storage-form-tip {
  display: flex;
  align-items: flex-start;
  gap: 4px;
  margin-top: 4px;
  color: var(--el-text-color-secondary);
  font-size: 12px;
  line-height: 1.4;
}

.storage-form-tip .el-icon {
  font-size: 14px;
  color: var(--el-color-info);
  margin-top: 2px;
}
</style> 