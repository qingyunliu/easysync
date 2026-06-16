<template>
  <div class="storages-container">
    <div class="header">
      <div class="header-left">
        <h2>{{ $t('storage.title') }}</h2>
        <p class="page-description">{{ $t('storage.description') }}</p>
      </div>
      <div class="header-right">
        <div class="header-actions">
          <el-input v-model="searchQuery" :placeholder="$t('storage.searchStorage')" clearable class="search-input">
            <template #prefix>
              <Icon icon="mdi:magnify" />
            </template>
          </el-input>
          <el-dropdown @command="handleAddStorage" trigger="click">
            <el-button type="primary">
              <Icon icon="mdi:plus" />&nbsp;{{ $t('storage.addStorage') }}
              <Icon icon="mdi:chevron-down" class="el-icon--right" />
            </el-button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="nas">{{ $t('storage.addNasStorage') }}</el-dropdown-item>
                <el-dropdown-item command="s3">{{ $t('storage.addObsStorage') }}</el-dropdown-item>
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
            <span>{{ $t('storage.nasDevices') }}</span>
            <el-tag type="warning" class="count-tag">{{ nasStorages.length }}</el-tag>
          </div>
        </template>

        <el-table :data="filteredNasStorages" style="width: 100%; background-color: var(--card-bg)" v-loading="loading" :fit="false"
          :empty-text="$t('storage.noNasStorages')">
          <el-table-column prop="name" :label="$t('storage.name')" min-width="180" :resizable="true">
            <template #default="{ row }">
              <div class="storage-name-cell">
                <Icon icon="mdi:folder-network" class="icon-nas" :width="20" />
                <el-link type="primary" @click="handleNameClick(row)">
                  {{ row.name }}
                </el-link>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="config.protocol" :label="$t('storage.protocolType')">
            <template #default="{ row }">
              <el-tag>{{ row.config.protocol === 'nfs' ? $t('storage.protocols.nfs') : $t('storage.protocols.cifs')
              }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="config.server" :label="$t('storage.server')" min-width="160" :resizable="true" />
          <el-table-column prop="config.path" :label="$t('storage.sharedDirectory')" min-width="180"
            :resizable="true" />
          <el-table-column prop="config.is_mounted" :label="$t('storage.mountStatus')" min-width="100"
            :resizable="true">
            <template #default="{ row }">
              <el-tag :type="row.config.is_mounted ? 'success' : 'info'">
                {{ row.config.is_mounted ? $t('storage.mounted') : $t('storage.unmounted') }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" :label="$t('storage.createTime')" min-width="160" :resizable="true" />
          <el-table-column prop="node_id" :label="$t('storage.boundNode')" min-width="140" :resizable="true">
            <template #default="{ row }">
              <el-tag v-if="row.node_id" type="success" size="small">{{ $t('storage.bound') }}</el-tag>
              <el-tag v-else type="warning" size="small">{{ $t('storage.unbound') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.actions')" min-width="280" fixed="right">
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
            <span>{{ $t('storage.obsStorage') }}</span>
            <el-tag type="primary" class="count-tag">{{ s3Storages.length }}</el-tag>
          </div>
        </template>

        <el-table :data="filteredS3Storages" style="width: 100%" v-loading="loading" :fit="false"
          :empty-text="$t('storage.noS3Storages')">
          <el-table-column prop="name" :label="$t('storage.name')" min-width="180" :resizable="true">
            <template #default="{ row }">
              <div class="storage-name-cell">
                <Icon icon="mdi:cloud" class="icon-s3" :width="20" />
                <el-link type="primary" @click="handleNameClick(row)">
                  {{ row.name }}
                </el-link>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="config.provider" :label="$t('storage.provider')" min-width="120" :resizable="true">
            <template #default="{ row }">
              <el-tag :type="getProviderType(row.config.provider)">
                {{ getProviderText(row.config.provider) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="config.access_key" :label="$t('storage.accessKeyId')" min-width="200"
            :resizable="true" />
          <el-table-column prop="config.endpoint" :label="$t('storage.endpoint')" min-width="200" :resizable="true" />
          <el-table-column prop="config.region" :label="$t('storage.region')" min-width="120" :resizable="true" />
          <el-table-column prop="created_at" :label="$t('storage.createTime')" min-width="160" :resizable="true" />
          <el-table-column prop="node_id" :label="$t('storage.boundNode')" min-width="140" :resizable="true">
            <template #default="{ row }">
              <el-tag v-if="row.node_id" type="success" size="small">{{ $t('storage.bound') }}</el-tag>
              <el-tag v-else type="warning" size="small">{{ $t('storage.unbound') }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column :label="$t('common.actions')" min-width="280" fixed="right">
            <template #default="{ row }">
              <StorageActions :storage="row" @refresh="fetchStorages" />
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <!-- 存储详情抽屉 -->
    <el-drawer v-model="drawerVisible" :title="$t('storage.storageDetails')" direction="rtl" size="60%"
      :before-close="handleDrawerClose" v-loading="isDrawerLoading"
      :element-loading-text="$t('storage.loadingStorageDetails')">
      <el-tabs v-model="activeTab" class="fixed-tabs">
        <!-- 基本信息标签页 -->
        <el-tab-pane :label="$t('storage.basicInfo')" name="basic">
          <div class="detail-content scrollable-content">
            <!-- 基本信息卡片 -->
            <el-card class="info-card">
              <template #header>
                <div class="card-header">
                  <span>{{ $t('storage.basicInfo') }}</span>
                </div>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item :label="$t('storage.storageName')">
                  <el-tag type="info">{{ currentStorage.name }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item :label="$t('storage.storageType')">
                  <el-tag :type="getStorageTypeTag(currentStorage.type)">
                    {{ getStorageTypeText(currentStorage.type) }}
                  </el-tag>
                </el-descriptions-item>
                <template v-if="currentStorage.type === 'nas'">
                  <el-descriptions-item :label="$t('storage.protocolType')">
                    <el-tag :type="currentStorage.config.protocol === 'nfs' ? 'success' : 'warning'">
                      {{ currentStorage.config.protocol === 'nfs' ? $t('storage.protocols.nfs') :
                        $t('storage.protocols.cifs') }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.server')">
                    {{ currentStorage.config.server }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.sharedDirectory')">
                    {{ currentStorage.config.path }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.protocolVersion')">
                    NFSv{{ currentStorage.config.version }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.mountOptions')">
                    {{ currentStorage.config.options || $t('storage.none') }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.readWritePermission')">
                    {{ currentStorage.config.permission }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.username')">
                    {{ currentStorage.config.username || $t('storage.none') }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.mountStatus')">
                    <el-tag :type="currentStorage.config.is_mounted ? 'success' : 'info'">
                      {{ currentStorage.config.is_mounted ? $t('storage.mounted') : $t('storage.unmounted') }}
                    </el-tag>
                  </el-descriptions-item>
                </template>
                <template v-else>
                  <el-descriptions-item :label="$t('storage.provider')">
                    <el-tag :type="getProviderType(currentStorage.config?.provider)">
                      {{ getProviderText(currentStorage.config?.provider) }}
                    </el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.endpoint')">
                    {{ currentStorage.config?.endpoint }}
                  </el-descriptions-item>
                  <el-descriptions-item :label="$t('storage.region')">
                    {{ currentStorage.config?.region }}
                  </el-descriptions-item>
                </template>
                <el-descriptions-item :label="$t('storage.createTime')">
                  {{ formatDate(currentStorage.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item :label="$t('storage.lastUpdate')">
                  {{ formatDate(currentStorage.updated_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </el-card>

            <!-- 统计信息卡片 -->
            <template v-if="currentStorage.type === 'nas'">
              <el-card class="info-card">
                <template #header>
                  <div class="card-header">
                    <span>{{ $t('storage.storageUsage') }}</span>
                    <el-button type="primary" link @click="refreshNASStats" :loading="refreshingStats">
                      <Icon icon="mdi:refresh" :class="{ 'rotating': refreshingStats }" />{{ $t('storage.refresh') }}
                    </el-button>
                  </div>
                </template>
                <div class="stats-grid" v-loading="refreshingStats || loadingNASStats"
                  :element-loading-text="$t('storage.loadingStorageStats')">
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:harddisk" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatSize(nasStats.total_size) }}</div>
                      <div class="stat-label">{{ $t('storage.totalSize') }}</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:database" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatSize(nasStats.used_size) }}</div>
                      <div class="stat-label">{{ $t('storage.usedSize') }}</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:file" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ nasStats.total_files || 0 }}</div>
                      <div class="stat-label">{{ $t('storage.totalFiles') }}</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:folder" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ nasStats.total_objects || 0 }}</div>
                      <div class="stat-label">{{ $t('storage.totalObjects') }}</div>
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
                    <span>{{ $t('storage.statistics') }}</span>
                    <el-button type="primary" link @click="refreshStats" :loading="refreshingStats"
                      :disabled="refreshingStats">
                      <Icon icon="mdi:refresh" :class="{ 'rotating': refreshingStats }" />{{ $t('storage.refresh') }}
                    </el-button>
                  </div>
                </template>
                <div class="stats-grid" v-loading="refreshingStats" :element-loading-text="$t('storage.loadingStats')">
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:bucket" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ storageStats.bucket_count || 0 }}</div>
                      <div class="stat-label">{{ $t('storage.bucketCount') }}</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:file" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ storageStats.object_count || 0 }}</div>
                      <div class="stat-label">{{ $t('storage.totalObjects') }}</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:database" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatSize(storageStats.total_size || 0) }}</div>
                      <div class="stat-label">{{ $t('storage.totalStorage') }}</div>
                    </div>
                  </div>
                  <div class="stat-item">
                    <div class="stat-icon">
                      <Icon icon="mdi:clock-outline" :width="24" />
                    </div>
                    <div class="stat-content">
                      <div class="stat-value">{{ formatDate(storageStats.last_modified) }}</div>
                      <div class="stat-label">{{ $t('storage.lastModified') }}</div>
                    </div>
                  </div>
                </div>
              </el-card>
            </template>

            <!-- 存储桶使用情况卡片 -->
            <el-card class="info-card" v-if="storageStats.bucket_stats && storageStats.bucket_stats.length > 0">
              <template #header>
                <div class="card-header">
                  <span>{{ $t('storage.bucketUsage') }}</span>
                </div>
              </template>
              <el-table :data="storageStats.bucket_stats" style="width: 100%">
                <el-table-column prop="name" :label="$t('storage.bucketName')" min-width="200">
                  <template #default="{ row }">
                    <div class="bucket-name">
                      <Icon icon="mdi:bucket" :width="20" />
                      <span>{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="object_count" :label="$t('storage.objectCount')" width="120" />
                <el-table-column prop="size" :label="$t('storage.storageSize')" width="120">
                  <template #default="{ row }">
                    {{ formatSize(row.size) }}
                  </template>
                </el-table-column>
                <el-table-column prop="last_modified" :label="$t('storage.lastModified')" width="180">
                  <template #default="{ row }">
                    {{ formatDate(row.last_modified) }}
                  </template>
                </el-table-column>
              </el-table>
            </el-card>
          </div>
        </el-tab-pane>

        <!-- 文件浏览标签页 -->
        <el-tab-pane v-if="currentStorage.type === 'nas'" :label="$t('storage.fileBrowse')" name="files">
          <div class="files-content scrollable-content">
            <!-- 面包屑导航 -->
            <div class="breadcrumb">
              <el-breadcrumb separator="/">
                <el-breadcrumb-item :class="{ 'is-disabled': !currentPath }"
                  @click="!currentPath && $event.preventDefault(); handleNASBreadcrumbClick('')"
                  style="cursor: pointer;">
                  {{ $t('storage.rootDirectory') }}
                </el-breadcrumb-item>
                <el-breadcrumb-item v-for="(path, index) in currentPath.split('/').filter(Boolean)" :key="index" @click="handleNASBreadcrumbClick(
                  currentPath.split('/').filter(Boolean).slice(0, index + 1).join('/') + '/'
                )" style="cursor: pointer;" :title="path">
                  <el-tooltip :content="path" placement="top" :show-after="500" :disabled="path.length <= 20">
                    <span class="breadcrumb-path">{{ path.length > 20 ? path.slice(0, 20) + '...' : path }}</span>
                  </el-tooltip>
                </el-breadcrumb-item>
              </el-breadcrumb>
            </div>

            <!-- 文件状态信息 -->
            <div class="file-status" v-if="!loadingFiles && total > 0">
              <el-tag type="info" size="small">
                {{ $t('storage.fileCount', { count: total }) }}
              </el-tag>
              <el-tag type="success" size="small" v-if="currentPath">
                <el-tooltip :content="$t('storage.currentPathLabel', { path: currentPath })" placement="top"
                  :show-after="300" :disabled="currentPath.length <= 40">
                  <span>{{ $t('storage.currentPathLabel', {
                    path: pathExpanded ? currentPath : truncatePath(currentPath,
                      40)
                  }) }}</span>
                </el-tooltip>
                <el-button v-if="currentPath.length > 40" type="text" size="small" @click="togglePathExpanded"
                  class="path-expand-button">
                  <Icon :icon="pathExpanded ? 'mdi:chevron-up' : 'mdi:chevron-down'" :width="12" />
                </el-button>
              </el-tag>
            </div>
            <!-- 加载状态信息 -->
            <div class="file-status" v-if="loadingFiles">
              <el-tag type="warning" size="small">
                <Icon icon="mdi:loading" class="rotating" />
                {{ $t('storage.loadingFiles') }}
              </el-tag>
            </div>
            <!-- 空状态信息 -->
            <div class="file-status" v-if="!loadingFiles && total === 0">
              <el-tag type="info" size="small">
                {{ $t('storage.emptyDirectory') }}
              </el-tag>
            </div>

            <!-- 文件列表 -->
            <el-table :data="files" style="width: 100%" v-loading="loadingFiles" @row-click="handleFileClick"
              :empty-text="loadingFiles ? $t('storage.loadingFiles') : $t('storage.emptyDirectory')">
              <el-table-column :label="$t('storage.name')" min-width="300">
                <template #default="{ row }">
                  <div class="file-name">
                    <Icon :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'" :width="20" />
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="size" :label="$t('storage.size')" width="120">
                <template #default="{ row }">
                  {{ row.type === 'directory' ? '-' : formatSize(row.size) }}
                </template>
              </el-table-column>
              <el-table-column prop="modified_time" :label="$t('storage.modifiedTime')" width="180">
                <template #default="{ row }">
                  {{ formatDate(row.modified_time) }}
                </template>
              </el-table-column>
              <el-table-column :label="$t('common.actions')" width="120" fixed="right">
                <template #default="{ row }">
                  <el-button v-if="row.type !== 'directory'" type="primary" size="small"
                    @click.stop="handleFileDownload(row)">
                    <Icon icon="mdi:download" />
                    {{ $t('storage.download') }}
                  </el-button>
                </template>
              </el-table-column>
            </el-table>

            <!-- 分页 -->
            <div class="pagination" v-if="total > 0">
              <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
                :page-sizes="[10, 20, 50, 100]" :total="total" layout="total, sizes, prev, pager, next"
                @size-change="handleSizeChange" @current-change="handleCurrentChange" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 存储桶列表标签页 -->
        <el-tab-pane v-if="currentStorage.type === 's3'" :label="$t('storage.buckets')" name="buckets">
          <div class="buckets-content scrollable-content">
            <el-table :data="buckets" style="width: 100%" v-loading="loadingBuckets" @row-click="handleBucketClick">
              <el-table-column prop="name" :label="$t('storage.bucketName')" min-width="200">
                <template #default="{ row }">
                  <div class="bucket-name">
                    <Icon icon="mdi:bucket" :width="20" />
                    <span>{{ row.name }}</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="creationDate" :label="$t('storage.createTime')" min-width="180">
                <template #default="{ row }">
                  {{ formatDate(row.creationDate) }}
                </template>
              </el-table-column>
              <el-table-column prop="region" :label="$t('storage.region')" min-width="120" />
            </el-table>
            <div class="pagination">
              <el-pagination v-model:current-page="bucketPage" v-model:page-size="bucketPageSize"
                :page-sizes="[10, 20, 50, 100]" :total="bucketTotal" layout="total, sizes, prev, pager, next"
                @size-change="handleBucketPageSizeChange" @current-change="handleBucketPageChange" />
            </div>
          </div>
        </el-tab-pane>

        <!-- 对象列表标签页 -->
        <el-tab-pane v-if="currentStorage.type === 's3'" :label="$t('storage.objectList')" name="objects">
          <div class="objects-content scrollable-content">
            <!-- 面包屑导航 -->
            <template v-if="currentBucket">
              <div class="breadcrumb">
                <el-breadcrumb separator="/">
                  <el-breadcrumb-item :class="{ 'is-disabled': !currentPath }"
                    @click="!currentPath && $event.preventDefault(); handleS3BreadcrumbClick('')"
                    style="cursor: pointer;">
                    {{ currentBucket }}
                  </el-breadcrumb-item>
                  <el-breadcrumb-item v-for="(path, index) in currentPath.split('/').filter(Boolean)" :key="index"
                    @click="handleS3BreadcrumbClick(
                      currentPath.split('/').filter(Boolean).slice(0, index + 1).join('/') + '/'
                    )" style="cursor: pointer;" :title="path">
                    <el-tooltip :content="path" placement="top" :show-after="500" :disabled="path.length <= 20">
                      <span class="breadcrumb-path">{{ path.length > 20 ? path.slice(0, 20) + '...' : path }}</span>
                    </el-tooltip>
                  </el-breadcrumb-item>
                </el-breadcrumb>
              </div>

              <!-- 对象状态信息 -->
              <div class="object-status" v-if="!loadingObjects && total > 0">
                <el-tag type="info" size="small">
                  {{ $t('storage.objectCount', { count: total }) }}
                </el-tag>
                <el-tag type="success" size="small" v-if="currentPath">
                  <el-tooltip :content="`${$t('storage.currentPath')}: ${currentPath}`" placement="top"
                    :show-after="300" :disabled="currentPath.length <= 40">
                    <span>{{ $t('storage.currentPath') }}: {{ pathExpanded ? currentPath : truncatePath(currentPath, 40)
                    }}</span>
                  </el-tooltip>
                  <el-button v-if="currentPath.length > 40" type="text" size="small" @click="togglePathExpanded"
                    class="path-expand-button">
                    <Icon :icon="pathExpanded ? 'mdi:chevron-up' : 'mdi:chevron-down'" :width="12" />
                  </el-button>
                </el-tag>
                <el-tag type="primary" size="small">
                  {{ $t('storage.bucket') }}: {{ currentBucket }}
                </el-tag>
              </div>
              <!-- 对象加载状态信息 -->
              <div class="object-status" v-if="loadingObjects">
                <el-tag type="warning" size="small">
                  <Icon icon="mdi:loading" class="rotating" />
                  {{ $t('storage.loadingObjects') }}
                </el-tag>
              </div>
              <!-- 对象空状态信息 -->
              <div class="object-status" v-if="!loadingObjects && total === 0">
                <el-tag type="info" size="small">
                  {{ $t('storage.emptyDirectory') }}
                </el-tag>
              </div>

              <!-- 对象列表 -->
              <el-table :data="objects" style="width: 100%" v-loading="loadingObjects" @row-click="handleObjectClick"
                :empty-text="loadingObjects ? $t('storage.loadingObjects') : $t('storage.emptyDirectory')">
                <el-table-column :label="$t('storage.name')" min-width="300">
                  <template #default="{ row }">
                    <div class="object-name">
                      <Icon :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'" :width="20" />
                      <span>{{ row.name }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column prop="size" :label="$t('storage.size')" width="120">
                  <template #default="{ row }">
                    {{ row.type === 'directory' ? '-' : formatSize(row.size) }}
                  </template>
                </el-table-column>
                <el-table-column prop="lastModified" :label="$t('storage.lastModifiedTime')" width="180">
                  <template #default="{ row }">
                    {{ formatDate(row.lastModified) }}
                  </template>
                </el-table-column>
                <el-table-column :label="$t('common.actions')" width="120" fixed="right">
                  <template #default="{ row }">
                    <el-button v-if="row.type !== 'directory'" type="primary" size="small"
                      @click.stop="handleS3Download(row)">
                      <Icon icon="mdi:download" />
                      {{ $t('storage.download') }}
                    </el-button>
                  </template>
                </el-table-column>
              </el-table>

              <!-- 分页 -->
              <div class="pagination" v-if="total > 0">
                <el-pagination v-model:current-page="currentPage" v-model:page-size="pageSize"
                  :page-sizes="[10, 20, 50, 100]" :total="total" layout="total, sizes, prev, pager, next"
                  @size-change="handleSizeChange" @current-change="handleCurrentChange" />
              </div>
            </template>
            <template v-else>
              <!-- 没有选择存储桶 -->
              <div class="empty-state">
                <div class="empty-icon">
                  <Icon icon="mdi:bucket-outline" :width="60" />
                </div>
                <h3>{{ $t('storage.selectBucketFirst') }}</h3>
                <p>{{ $t('storage.selectBucketToBrowse') }}</p>
                <el-button type="primary" @click="activeTab = 'buckets'">
                  <Icon icon="mdi:bucket" />
                  {{ $t('storage.viewBuckets') }}
                </el-button>
              </div>
            </template>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-drawer>

    <!-- 存储编辑对话框 -->
    <el-dialog :title="dialogType === 'add' ? $t('storage.addStorage') : $t('storage.editStorage')"
      v-model="dialogVisible" width="600px" :before-close="handleDialogClose" :close-on-click-modal="false">
      <el-form :model="form" :rules="formRules" ref="formRef" label-width="120px" class="storage-form">
        <el-form-item :label="$t('storage.storageName')" prop="name">
          <el-input v-model="form.name" :placeholder="$t('storage.enterStorageName')" />
        </el-form-item>

        <template v-if="form.type === 'nas'">
          <el-form-item :label="$t('storage.protocolType')" prop="config.protocol">
            <el-radio-group v-model="form.config.protocol">
              <el-radio label="cifs">{{ $t('storage.protocols.cifs') }}</el-radio>
              <el-radio label="nfs">{{ $t('storage.protocols.nfs') }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item :label="$t('storage.ipAddress')" prop="config.server">
            <el-input v-model="form.config.server" />
          </el-form-item>
          <el-form-item :label="$t('storage.sharedDirectory')" prop="config.path">
            <el-input v-model="form.config.path" />
          </el-form-item>
          <el-form-item :label="$t('storage.readWritePermission')" prop="config.permission">
            <el-radio-group v-model="form.config.permission">
              <el-radio label="rw">{{ $t('storage.readWrite') }}</el-radio>
              <el-radio label="ro">{{ $t('storage.readOnly') }}</el-radio>
            </el-radio-group>
          </el-form-item>
          <!-- NFS专属 -->
          <template v-if="form.config.protocol === 'nfs'">
            <el-form-item :label="$t('storage.protocolVersion')" prop="config.version">
              <el-select v-model="form.config.version">
                <el-option :label="$t('storage.protocolVersions.nfsv3')" value="3" />
                <el-option :label="$t('storage.protocolVersions.nfsv40')" value="4.0" />
                <el-option :label="$t('storage.protocolVersions.nfsv41')" value="4.1" />
              </el-select>
            </el-form-item>
          </template>
          <!-- CIFS专属 -->
          <template v-else>
            <el-form-item :label="$t('storage.protocolVersion')" prop="config.version">
              <el-select v-model="form.config.version">
                <el-option :label="$t('storage.protocolVersions.cifsv20')" value="2.0" />
                <el-option :label="$t('storage.protocolVersions.cifsv30')" value="3.0" />
              </el-select>
            </el-form-item>
            <el-form-item :label="$t('storage.username')" prop="config.username">
              <el-input v-model="form.config.username" />
            </el-form-item>
            <el-form-item :label="$t('storage.password')" prop="config.password">
              <el-input v-model="form.config.password" type="password" />
            </el-form-item>
            <el-form-item :label="$t('storage.workgroup')" prop="config.workgroup">
              <el-input v-model="form.config.workgroup" />
            </el-form-item>
          </template>

          <!-- 高级选项折叠面板 -->
          <div class="storage-advanced-section">
            <el-collapse v-model="advancedOptions">
              <el-collapse-item :title="$t('storage.advancedOptions')" name="advanced">
                <el-form-item :label="$t('storage.port')" prop="config.port">
                  <el-input v-model="form.config.port" :placeholder="$t('storage.defaultPorts')" />
                </el-form-item>
                <el-form-item :label="$t('storage.mountOptions')" prop="config.options">
                  <el-input v-model="form.config.options" :placeholder="$t('storage.mountOptionsExample')" />
                  <div class="storage-form-tip">
                    <el-icon>
                      <InfoFilled />
                    </el-icon>
                    <span>{{ $t('storage.nfsExample') }}</span>
                  </div>
                  <div class="storage-form-tip">
                    <el-icon>
                      <InfoFilled />
                    </el-icon>
                    <span>{{ $t('storage.cifsExample') }}</span>
                  </div>
                </el-form-item>
              </el-collapse-item>
            </el-collapse>
          </div>
        </template>

        <template v-else-if="form.type === 's3'">
          <el-form-item :label="$t('storage.provider')" prop="config.provider">
            <el-select v-model="form.config.provider" :placeholder="$t('storage.selectProvider')">
              <el-option :label="$t('storage.providers.aws')" value="aws" />
              <el-option :label="$t('storage.providers.googleCloud')" value="google" />
              <el-option :label="$t('storage.providers.tencentCloud')" value="tencent" />
              <el-option :label="$t('storage.providers.aliCloud')" value="aliyun" />
              <el-option :label="$t('storage.providers.huaweiCloud')" value="huawei" />
              <el-option :label="$t('storage.providers.minio')" value="minio" />
              <el-option :label="$t('storage.providers.other')" value="other" />
              <!-- 其他选项 -->
            </el-select>
          </el-form-item>
          <el-form-item :label="$t('storage.accessKeyId')" prop="config.access_key">
            <el-input v-model="form.config.access_key" :placeholder="$t('storage.enterAccessKey')" />
          </el-form-item>
          <el-form-item :label="$t('storage.secretKeyId')" prop="config.secret_key">
            <el-input v-model="form.config.secret_key" type="password" :placeholder="$t('storage.enterSecretKey')" />
          </el-form-item>
          <el-form-item :label="$t('storage.endpoint')" prop="config.endpoint">
            <el-input v-model="form.config.endpoint" :placeholder="$t('storage.enterEndpoint')" />
          </el-form-item>
          <el-form-item :label="$t('storage.region')" prop="config.region">
            <el-input v-model="form.config.region" :placeholder="$t('storage.enterRegion')" />
          </el-form-item>
          <el-form-item :label="$t('storage.bucket')" prop="config.bucket">
            <el-input v-model="form.config.bucket" :placeholder="$t('storage.enterBucketName')">
            </el-input>
          </el-form-item>
          <el-form-item :label="$t('storage.pathStyle')" prop="config.path_style">
            <el-switch v-model="form.config.path_style" />
          </el-form-item>
          <!-- 继续渲染 S3/OBS 相关项 -->
        </template>

        <el-form-item :label="$t('storage.testNode')" prop="test_node_id" style="margin-top: 10px;">
          <div style="display: flex; gap: 8px; align-items: center; flex:0.8;">
            <el-select v-model="testNodeId" :placeholder="$t('storage.selectNode')" style="flex: 1;">
              <el-option v-for="node in availableNodes" :key="node.id" :label="node.name + ' (' + node.ipaddress + ')'"
                :value="node.id">
                <div style="display: flex; align-items: center; justify-content: space-between;">
                  <span>{{ node.name }} ({{ node.ipaddress }})</span>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <el-tag size="small" type="success" v-if="node.status === 'online'">{{ $t('storage.online')
                    }}</el-tag>
                    <el-tag size="small" type="warning" v-else>{{ $t('storage.offline') }}</el-tag>
                    <el-tag size="small" type="primary" v-if="node.agent_status === 'running'">{{
                      $t('storage.agentRunning')
                    }}</el-tag>
                    <el-tag size="small" type="danger" v-else>{{ $t('storage.agentNotRunning') }}</el-tag>
                  </div>
                </div>
              </el-option>
            </el-select>
            <el-button type="primary" :icon="Refresh" circle size="small" @click="fetchAvailableNodes"
              :title="$t('storage.refreshNodeList')" />
          </div>
          <div style="font-size: 12px; color: #909399; margin-left: 8px;">
            <span v-if="availableNodes.length === 0">{{ $t('storage.noAvailableTestNodes') }}</span>
            <span v-else>{{ $t('storage.foundAvailableNodes', { count: availableNodes.length }) }}</span>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">{{ $t('common.cancel') }}</el-button>
          <el-button @click="handleTestConnect">{{ $t('storage.testConnection') }}</el-button>
          <el-button type="primary" @click="handleSubmit">{{ $t('common.confirm') }}</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, onUnmounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon } from '@iconify/vue'
import { Refresh, InfoFilled } from '@element-plus/icons-vue'
import StorageActions from '@/components/StorageActions.vue'
import axios from '@/utils/axios.mjs'

const { t } = useI18n()

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
    bucket: '',
    path_style: false,
    protocol: 'cifs', // 默认选中 CIFS

    // NAS 配置
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
    { required: true, message: t('storage.enterFolderName'), trigger: 'blur' }
  ]
}

const renameRules = {
  name: [
    { required: true, message: t('storage.enterNewName'), trigger: 'blur' }
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
// 添加 NAS 统计信息初始加载状态
const loadingNASStats = ref(false)

// 添加高级选项的响应式变量
const advancedOptions = ref([])  // 默认不展开

const testNodeId = ref('')
const availableNodes = ref([])

// 计算抽屉是否正在加载
const isDrawerLoading = computed(() => {
  if (currentStorage.value.type === 'nas') {
    return loadingNASStats.value || loadingFiles.value
  } else {
    return loadingObjects.value || loadingBuckets.value
  }
})

// 路径截断工具函数
const truncatePath = (path, maxLength = 50) => {
  if (!path || path.length <= maxLength) {
    return path
  }

  // 如果路径以 / 开头，保留开头的 /
  const hasLeadingSlash = path.startsWith('/')
  const cleanPath = hasLeadingSlash ? path.slice(1) : path

  // 分割路径
  const parts = cleanPath.split('/')

  if (parts.length <= 2) {
    // 如果只有1-2个部分，直接截断
    return (hasLeadingSlash ? '/' : '') + cleanPath.slice(0, maxLength - 3) + '...'
  }

  // 保留开头和结尾的部分
  const firstPart = parts[0]
  const lastPart = parts[parts.length - 1]
  const middleParts = parts.slice(1, -1)

  // 计算可用长度
  const availableLength = maxLength - firstPart.length - lastPart.length - 6 // '...' + '/' + '...'

  if (availableLength <= 0) {
    // 如果空间不够，只显示开头和结尾
    return (hasLeadingSlash ? '/' : '') + firstPart + '/.../' + lastPart
  }

  // 尝试保留一些中间部分
  let result = (hasLeadingSlash ? '/' : '') + firstPart + '/...'
  let currentLength = firstPart.length + 4

  for (const part of middleParts) {
    if (currentLength + part.length + 1 <= availableLength) {
      result += '/' + part
      currentLength += part.length + 1
    } else {
      break
    }
  }

  result += '/.../' + lastPart
  return result
}

// 路径展开状态
const pathExpanded = ref(false)

// 切换路径展开状态
const togglePathExpanded = () => {
  pathExpanded.value = !pathExpanded.value
}

// 获取存储列表
const fetchStorages = async () => {
  try {
    loading.value = true
    const response = await axios.get('/storages');
    storages.value = response.data.storages
  } catch (error) {
    ElMessage.error(t('storage.getStorageListFailed'))
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
      return t('storage.storageTypes.nas')
    case 's3':
      return t('storage.storageTypes.s3')
    default:
      return t('storage.storageTypes.unknown')
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
      return t('storage.statusTypes.active')
    case 'error':
      return t('storage.statusTypes.error')
    case 'disabled':
      return t('storage.statusTypes.disabled')
    default:
      return t('storage.statusTypes.unknown')
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
  // 设置当前绑定的节点ID
  testNodeId.value = row.node_id || ''
  // 打印编辑的表单数据，用于调试
  dialogVisible.value = true
}

// 获取存储信息
const getStorageInfo = async (row) => {
  try {
    row.fetching = true
    const response = await axios.get(`/storages/${row.id}/info`)
    storageStats.value = response.data.data
    ElMessage.success(t('storage.getInfoSuccess'))
  } catch (error) {
    ElMessage.error(t('storage.getInfoFailed'))
  } finally {
    row.fetching = false
  }
}

// 显示存储详情
const handleNameClick = async (row) => {
  try {
    // 检查存储是否有绑定的节点
    if (!row.node_id) {
      ElMessage.warning(t('storage.noBoundNodeForDetails'))
      return
    }

    // 检查绑定的节点是否在线
    const nodesResponse = await axios.get('/nodes')
    const boundNode = nodesResponse.data.data.find(node => node.id === row.node_id)

    if (!boundNode) {
      ElMessage.error(t('storage.boundNodeNotExists'))
      return
    }

    if (boundNode.status !== 'online') {
      ElMessage.warning(t('storage.boundNodeOffline', { nodeName: boundNode.name }))
    }

    if (boundNode.agent_status !== 'running') {
      ElMessage.warning(t('storage.boundNodeAgentNotRunning', { nodeName: boundNode.name }))
    }

    currentStorage.value = row
    drawerVisible.value = true
    activeTab.value = 'basic'
    bucketPage.value = 1
    bucketPageSize.value = 10

    if (row.type === "nas") {
      // 重置 NAS 文件浏览状态
      currentPath.value = ''
      currentPage.value = 1
      pageSize.value = 20
      total.value = 0
      files.value = []
      loadingFiles.value = true  // 设置为 true 以显示加载状态
      loadingNASStats.value = true  // 设置为 true 以显示统计信息加载状态

      // 获取存储统计信息
      await fetchNASDetails()
      // 获取根目录文件列表
      await fetchFiles()
    } else {
      // 重置 S3 对象浏览状态
      currentBucket.value = ''
      currentPath.value = ''
      currentPage.value = 1
      pageSize.value = 20
      total.value = 0
      objects.value = []
      loadingObjects.value = false

      await fetchBuckets()
    }
  } catch (error) {
    console.error(t('storage.logMessages.loadStorageDetailsFailed'), error)
    ElMessage.error(t('storage.loadStorageDetailsFailed'))
  }
}

// 处理文件点击
const handleFileClick = (row) => {
  if (row.type === 'directory') {
    currentPath.value = row.path
    currentPage.value = 1  // 重置到第一页
    total.value = 0  // 重置总数
    fetchFiles()
  }
}

// 获取 nas 存储信息
const fetchNASDetails = async () => {
  try {
    // 检查存储是否有绑定的节点
    if (!currentStorage.value.node_id) {
      ElMessage.error(t('storage.noBoundNodeForStats'))
      return
    }

    loadingNASStats.value = true
    const response = await axios.get(`/storages/${currentStorage.value.id}/stats`)

    if (response.data.status === 'task_created') {
      ElMessage.info(t('storage.statsTaskCreated', { taskId: response.data.task_id }))
    } else if (response.data.status === 'success') {
      nasStats.value = response.data.data
    } else {
      ElMessage.error(response.data.message || t('storage.getStatsFailed'))
    }
  } catch (error) {
    console.error(t('storage.logMessages.getNASStorageInfoFailed'), error)
    ElMessage.error(t('storage.getNASStorageInfoFailed'))
  } finally {
    loadingNASStats.value = false
  }
}

// 刷新 NAS 统计信息
const refreshNASStats = async () => {
  try {
    // 检查存储是否有绑定的节点
    if (!currentStorage.value.node_id) {
      ElMessage.error(t('storage.noBoundNodeForRefreshStats'))
      return
    }

    refreshingStats.value = true
    const response = await axios.get(`/storages/${currentStorage.value.id}/stats`)

    if (response.data.status === 'task_created') {
      ElMessage.info(t('storage.statsTaskCreated', { taskId: response.data.task_id }))
    } else if (response.data.status === 'success') {
      nasStats.value = response.data.data
      ElMessage.success(t('storage.statsUpdated'))
    } else {
      ElMessage.error(response.data.message || t('storage.updateStatsFailed'))
    }
  } catch (error) {
    console.error(t('storage.logMessages.updateStatsFailed'), error)
    ElMessage.error(t('storage.updateStatsFailed'))
  } finally {
    refreshingStats.value = false
  }
}

// 下载文件
const handleFileDownload = async (file) => {
  try {
    // 检查存储是否有绑定的节点
    if (!currentStorage.value.node_id) {
      ElMessage.error(t('storage.noBoundNodeForDownload'))
      return
    }

    const response = await axios.post(`/storages/${currentStorage.value.id}/download`, {
      params: {
        node_id: currentStorage.value.node_id,
        path: file.path,
        bucket: currentBucket.value,
      },
      responseType: 'blob'
    })

    if (response.data.status === 'task_created') {
      ElMessage.info(t('storage.downloadTaskCreated', { taskId: response.data.task_id }))
    } else if (response.data.status === 'success') {
      // 处理文件下载
      const url = window.URL.createObjectURL(new Blob([response.data.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', file.name)
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } else {
      ElMessage.error(response.data.message || t('storage.downloadFailed'))
    }
  } catch (error) {
    console.error(t('storage.logMessages.downloadFailed'), error)
    ElMessage.error(t('storage.downloadFailed'))
  }
}

// 获取文件列表
const fetchFiles = async () => {
  try {
    // 检查存储是否有绑定的节点
    if (!currentStorage.value.node_id) {
      ElMessage.error(t('storage.noBoundNodeForFileList'))
      return
    }

    loadingFiles.value = true
    const response = await axios.get(`/storages/${currentStorage.value.id}/files`, {
      params: {
        node_id: currentStorage.value.node_id,
        path: currentPath.value,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })

    if (response.data.status === 'task_created') {
      ElMessage.info(t('storage.fileListTaskCreated', { taskId: response.data.task_id }))
    } else if (response.data.status === 'success') {
      const responseData = response.data.data

      // 处理分页数据结构，与 fetchBuckets 保持一致
      if (responseData.objects && Array.isArray(responseData.objects)) {
        files.value = responseData.objects
        // 使用分页信息中的total_count
        if (responseData.pagination) {
          total.value = responseData.pagination.total_count
        } else {
          total.value = responseData.total || responseData.objects.length
        }
      } else {
        files.value = responseData
        total.value = responseData.length
      }
    } else {
      ElMessage.error(response.data.message || t('storage.getFileListFailed'))
    }
  } catch (error) {
    console.error(t('storage.logMessages.getFileListFailed'), error)
    ElMessage.error(t('storage.getFileListFailed'))
  } finally {
    loadingFiles.value = false
  }
}

// 获取对象存储存储桶列表
const fetchBuckets = async () => {
  try {
    // 检查存储是否有绑定的节点
    if (!currentStorage.value.node_id) {
      ElMessage.error(t('storage.noBoundNodeForBucketList'))
      return
    }

    loadingBuckets.value = true
    const response = await axios.get(`/storages/${currentStorage.value.id}/buckets`, {
      params: {
        page: bucketPage.value,
        page_size: bucketPageSize.value
      }
    })

    if (response.data.status === 'task_created') {
      ElMessage.info(t('storage.bucketListTaskCreated', { taskId: response.data.task_id }))
    } else if (response.data.status === 'success') {
      const responseData = response.data.data

      // 处理分页数据结构
      if (responseData.buckets && Array.isArray(responseData.buckets)) {
        buckets.value = responseData.buckets
        // 使用分页信息中的total_count
        if (responseData.pagination) {
          bucketTotal.value = responseData.pagination.total_count
        } else {
          bucketTotal.value = responseData.total || responseData.buckets.length
        }
      } else {
        buckets.value = responseData
        bucketTotal.value = responseData.length
      }
    } else {
      ElMessage.error(response.data.message || t('storage.getBucketListFailed'))
    }
  } catch (error) {
    console.error(t('storage.logMessages.getBucketListFailed'), error)
    ElMessage.error(t('storage.getBucketListFailed'))
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
    // 检查存储是否有绑定的节点
    if (!currentStorage.value.node_id) {
      ElMessage.error(t('storage.noBoundNodeForObjectList'))
      return
    }

    loadingObjects.value = true
    const response = await axios.get(`/storages/${currentStorage.value.id}/objects`, {
      params: {
        node_id: currentStorage.value.node_id,
        bucket: currentBucket.value,
        prefix: currentPath.value,
        page: currentPage.value,
        page_size: pageSize.value
      }
    })

    if (response.data.status === 'task_created') {
      ElMessage.info(t('storage.objectListTaskCreated', { taskId: response.data.task_id }))
    } else if (response.data.status === 'success') {
      const responseData = response.data.data

      // 处理分页数据结构，与 fetchFiles 保持一致
      if (responseData.objects && Array.isArray(responseData.objects)) {
        objects.value = responseData.objects
        // 使用分页信息中的total_count
        if (responseData.pagination) {
          total.value = responseData.pagination.total_count
        } else {
          total.value = responseData.total || responseData.objects.length
        }
      } else {
        objects.value = responseData
        total.value = responseData.length
      }
    } else {
      ElMessage.error(response.data.message || t('storage.getObjectListFailed'))
    }
  } catch (error) {
    console.error(t('storage.logMessages.getObjectListFailed'), error)
    ElMessage.error(t('storage.getObjectListFailed'))
  } finally {
    loadingObjects.value = false
  }
}

// 处理存储桶点击
const handleBucketClick = (row) => {
  currentBucket.value = row.name
  currentPath.value = ''
  currentPage.value = 1
  total.value = 0  // 重置总数
  activeTab.value = 'objects'
  fetchObjects()
}

// 处理对象点击
const handleObjectClick = (row) => {
  if (row.type === 'directory') {
    currentPath.value = row.prefix
    currentPage.value = 1  // 重置到第一页
    total.value = 0  // 重置总数
    fetchObjects()
  }
}

// 处理面包屑点击
const handleS3BreadcrumbClick = (path) => {
  if (!currentBucket.value) return
  currentPath.value = path
  currentPage.value = 1  // 重置到第一页
  total.value = 0  // 重置总数
  fetchObjects()
}

// 处理面包屑点击
const handleNASBreadcrumbClick = (path) => {
  currentPath.value = path
  currentPage.value = 1  // 重置到第一页
  total.value = 0  // 重置总数
  fetchFiles()
}

// 处理分页大小变化
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1  // 重置到第一页
  total.value = 0  // 重置总数
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
    const response = await axios.get(`/storages/${currentStorage.value.id}/download`, {
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
    ElMessage.error(t('storage.downloadFailed'))
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
  pageSize.value = 20  // 重置页面大小
  total.value = 0
  files.value = []  // 重置文件列表
  loadingFiles.value = false  // 重置加载状态
  loadingObjects.value = false  // 重置对象加载状态
  loadingNASStats.value = false  // 重置 NAS 统计信息加载状态
  pathExpanded.value = false  // 重置路径展开状态
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
  if (!provider) return t('storage.providers.unknown')
  
  const providerKey = `storage.providers.${provider}`
  // 检查是否有对应的翻译键
  return t(providerKey) !== providerKey ? t(providerKey) : t('storage.providers.unknown')
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
  dialogVisible.value = true
}

// 表单验证规则
const formRules = computed(() => {
  const rules = {
    name: [
      { required: true, message: t('storage.validation.enterStorageName'), trigger: 'blur' }
    ]
  }

  if (form.value.type === 's3') {
    rules['config.provider'] = [
      { required: true, message: t('storage.validation.selectProvider'), trigger: 'change' }
    ]
    rules['config.access_key'] = [
      { required: true, message: t('storage.validation.enterAccessKey'), trigger: 'blur' }
    ]
    rules['config.secret_key'] = [
      { required: true, message: t('storage.validation.enterSecretKey'), trigger: 'blur' }
    ]
    rules['config.endpoint'] = [
      { required: true, message: t('storage.validation.enterEndpoint'), trigger: 'blur' }
    ]
    rules['config.region'] = [
      {
        required: true,
        message: t('storage.validation.enterRegion'),
        trigger: 'blur',
        validator: (rule, value, callback) => {
          if (form.value.config.provider === 'minio') {
            callback()
          } else if (!value) {
            callback(new Error(t('storage.validation.enterRegion')))
          } else {
            callback()
          }
        }
      }
    ]
    rules['config.bucket'] = [
      { required: true, message: t('storage.validation.enterBucketName'), trigger: 'blur' }
    ]
  } else if (form.value.type === 'nas') {
    rules['config.server'] = [
      { required: true, message: t('storage.validation.enterServerAddress'), trigger: 'blur' }
    ]
    rules['config.path'] = [
      { required: true, message: t('storage.validation.enterSharedDirectoryPath'), trigger: 'blur' }
    ]
    rules['config.protocol'] = [
      { required: true, message: t('storage.validation.selectProtocolType'), trigger: 'change' }
    ]
    rules['config.permission'] = [
      { required: true, message: t('storage.validation.selectReadWritePermission'), trigger: 'change' }
    ]
    rules['config.version'] = [
      { required: true, message: t('storage.validation.selectProtocolVersion'), trigger: 'change' }
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

    // 检查是否选择了节点（仅在创建时强制要求）
    if (dialogType.value === 'add' && !testNodeId.value) {
      ElMessage.warning(t('storage.selectNodeToBindStorage'))
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
      config: config,
      node_id: testNodeId.value // 添加节点ID绑定
    }

    if (dialogType.value === 'add') {
      const response = await axios.post('/storages', submitData)
      ElMessage.success(t('storage.addStorageSuccess'))
    } else {
      const response = await axios.put(`/storages/${form.value.id}`, submitData)
      ElMessage.success(t('storage.updateStorageSuccess'))
    }
    dialogVisible.value = false
    fetchStorages()
  } catch (error) {
    console.error(t('storage.logMessages.submitError'), error)
    if (error.response) {
      console.error(t('storage.logMessages.errorResponse'), error.response.data)
      ElMessage.error(error.response.data.message || t('storage.operationFailed'))
    } else if (error.message) {
      ElMessage.error(error.message)
    }
  }
}

// 获取可用节点列表（只显示在线且Agent已安装的节点）
const fetchAvailableNodes = async () => {
  try {
    const response = await axios.get('/nodes')
    const allNodes = response.data.data || []

    // 过滤出在线且Agent已安装的节点
    const filteredNodes = allNodes.filter(
      node => node.status === 'online' && node.agent_status === 'running'
    )

    availableNodes.value = filteredNodes

    // 如果没有可用节点，给出提示
    if (filteredNodes.length === 0 && allNodes.length > 0) {
      console.warn(t('storage.noAvailableTestNodes'))
    }

  } catch (error) {
    console.error(t('storage.logMessages.getNodeListFailed'), error)
    ElMessage.error(t('storage.getNodeListFailed'))
    availableNodes.value = []
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

    // 检查是否选择了测试节点
    if (!testNodeId.value) {
      ElMessage.warning(t('storage.selectTestNodeFirst'))
      return
    }

    // 重新获取最新的节点状态
    await fetchAvailableNodes()

    // 检查选中的节点是否在线
    const selectedNode = availableNodes.value.find(node => node.id === testNodeId.value)
    if (!selectedNode) {
      ElMessage.error(t('storage.testNodeNotExists'))
      return
    }

    // 检查节点状态
    if (selectedNode.status !== 'online') {
      ElMessage.error(t('storage.testNodeOffline', { nodeName: selectedNode.name }))
      return
    }

    // 检查 Agent 状态
    if (selectedNode.agent_status !== 'running') {
      ElMessage.error(t('storage.testNodeAgentNotRunning', { nodeName: selectedNode.name }))
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

    // 显示加载状态
    ElMessage.info(t('storage.creatingConnectionTestTask', { nodeName: selectedNode.name, ipAddress: selectedNode.ipaddress }))

    const response = await axios.post('/storages/test-connection', submitData)
    if (response.data.status == "success") {
      // 检查返回的数据结构
      const result = response.data.result || response.data.data
      if (result && result.task_id) {
        // 如果返回了 task_id，说明创建了任务
        ElMessage.success(t('storage.connectionTestTaskCreated', { taskId: result.task_id }))
        // 可选：自动跳转到任务页面
        // router.push(`/tasks?task_id=${result.task_id}`)
      } else if (result && result.status === 'success') {
        // 实时测试成功
        ElMessage.success(response.data.message || t('storage.testConnectionSuccess'))
      } else {
        // 测试失败
        ElMessage.error(result?.message || response.data.message || t('storage.testConnectionFailed'))
      }
    } else {
      ElMessage.error(response.data.message || t('storage.testConnectionFailed'))
    }
  } catch (error) {
    if (error.response) {
      ElMessage.error(error.response.data.message || t('storage.operationFailed'))
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
    ElMessage.success(t('storage.uploadSuccess'))
    fetchObjects(currentStorage.value.id)
  } else {
    ElMessage.error(response.message || t('storage.uploadFailed'))
  }
}

const handleUploadError = () => {
  ElMessage.error(t('storage.uploadFailed'))
}

// 修改刷新统计信息函数
const refreshStats = async () => {
  try {
    // 检查存储是否有绑定的节点
    if (!currentStorage.value.node_id) {
      ElMessage.error(t('storage.noBoundNodeForRefreshStats'))
      return
    }

    await ElMessageBox.confirm(t('storage.refreshStatsConfirm'), t('common.tip'), {
      confirmButtonText: t('common.confirmButton'),
      cancelButtonText: t('common.cancelButton'),
      type: 'warning'
    })

    refreshingStats.value = true
    const response = await axios.get(`/storages/${currentStorage.value.id}/stats`)

    if (response.data.status === 'task_created') {
      ElMessage.info(t('storage.statsTaskCreated', { taskId: response.data.task_id }))
    } else if (response.data.status === 'success') {
      storageStats.value = response.data.data
      ElMessage.success(t('storage.statsUpdated'))
    } else {
      ElMessage.error(response.data.message || t('storage.getStatsFailed'))
    }
  } catch (error) {
    // 如果是用户取消操作,不显示错误提示
    if (error !== 'cancel') {
      console.error(t('storage.logMessages.getStatsFailed'), error)
      ElMessage.error(t('storage.getStatsFailed'))
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
  background: var(--card-bg);
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
  background: var(--card-bg);
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

.header-left h2 {
  margin: 0 0 5px 0;
  color: var(--text-color);
  font-size: 24px;
}

.page-description {
  margin: 0;
  color: var(--text-secondary);
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

:deep(.el-table__header th) {
  background: var(--bg-secondary);
  color: var(--text-secondary);
  font-weight: 600;
  border-bottom: 1px solid var(--border-color);
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

.breadcrumb :deep(.el-breadcrumb__item) {
  max-width: 200px;
}

.breadcrumb :deep(.el-breadcrumb__inner) {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 路径展开按钮样式 */
.path-expand-button {
  margin-left: 4px;
  padding: 0 4px;
  color: var(--el-color-primary);
  transition: all 0.3s ease;
}

.path-expand-button:hover {
  color: var(--el-color-primary-dark-2);
  transform: scale(1.1);
}

/* 路径标签样式 */
.path-tag {
  display: inline-flex;
  align-items: center;
  max-width: 100%;
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

.file-status {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}

.object-status {
  display: flex;
  gap: 8px;
  margin-bottom: 16px;
  align-items: center;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 60px 20px;
  text-align: center;
  color: var(--el-text-color-secondary);
}

.empty-icon {
  margin-bottom: 16px;
  color: var(--el-color-info);
}

.empty-state h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.empty-state p {
  margin: 0 0 20px 0;
  font-size: 14px;
  line-height: 1.5;
}

.breadcrumb-path {
  display: inline-block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: bottom;
}

.breadcrumb {
  margin-bottom: 16px;
  padding: 8px 16px;
  background-color: var(--el-color-primary-light-9);
  border-radius: 4px;
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
  background-color: var(--header-bg);
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