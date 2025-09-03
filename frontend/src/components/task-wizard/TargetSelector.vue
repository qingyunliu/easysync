<template>
  <div class="target-selector">
    <!-- 存储选择 -->
    <div class="storage-selection">
      <div class="selection-header">
        <h3>{{ $t('targetSelector.selectTargetStorage') }}</h3>
        <p class="selection-description">{{ $t('targetSelector.selectTargetStorageDesc') }}</p>
      </div>

      <el-form :model="form" label-width="120px">
        <el-form-item :label="$t('targetSelector.targetStorage')" required>
          <el-select v-model="form.selectedStorageId" :placeholder="$t('targetSelector.selectTargetStoragePlaceholder')"
            style="width: 100%" @change="handleStorageChange">
            <el-option-group :label="$t('targetSelector.nasStorage')">
              <el-option v-for="storage in nasStorages" :key="storage.id"
                :label="`${storage.name} (${storage.config.protocol.toUpperCase()})`" :value="storage.id">
                <div class="storage-option">
                  <Icon icon="mdi:folder-network" class="storage-icon" />
                  <div class="storage-info">
                    <div class="storage-name">{{ storage.name }}</div>
                    <div class="storage-detail">{{ storage.config.server }}:{{ storage.config.path }}</div>
                  </div>
                  <el-tag :type="storage.config.is_mounted ? 'success' : 'warning'" size="small">
                    {{ storage.config.is_mounted ? $t('targetSelector.mounted') : $t('targetSelector.notMounted') }}
                  </el-tag>
                </div>
              </el-option>
            </el-option-group>
            <el-option-group :label="$t('targetSelector.obsStorage')">
              <el-option v-for="storage in obsStorages" :key="storage.id"
                :label="`${storage.name} (${storage.config.provider.toUpperCase()})`" :value="storage.id">
                <div class="storage-option">
                  <Icon icon="mdi:cloud" class="storage-icon" />
                  <div class="storage-info">
                    <div class="storage-name">{{ storage.name }}</div>
                    <div class="storage-detail">{{ storage.config.endpoint }}</div>
                  </div>
                  <el-tag type="primary" size="small">
                    {{ getProviderText(storage.config.provider) }}
                  </el-tag>
                </div>
              </el-option>
            </el-option-group>
          </el-select>
        </el-form-item>
      </el-form>
    </div>

    <!-- 数据覆盖警告 -->
    <div v-if="showOverrideWarning" class="override-warning">
      <el-alert :title="$t('targetSelector.dataOverrideWarning')" type="warning" :description="overrideWarningText"
        show-icon :closable="false" />
    </div>

    <!-- 目标路径配置 -->
    <div v-if="selectedStorage" class="target-path-section">
      <!-- OBS 存储配置 -->
      <template v-if="selectedStorage.type === 's3'">
        <div class="obs-config">
          <div class="config-header">
            <h4>{{ $t('targetSelector.configureTargetLocation') }}</h4>
            <p class="config-description">{{ $t('targetSelector.configureTargetLocationDesc') }}</p>
          </div>

          <div class="config-content">
            <el-form :model="obsForm" label-width="120px">
              <el-form-item :label="$t('targetSelector.operationMode')" required>
                <el-radio-group v-model="obsForm.mode" @change="handleObsModeChange">
                  <el-radio label="browse">{{ $t('targetSelector.browseExistingBucket') }}</el-radio>
                  <el-radio label="create">{{ $t('targetSelector.createNewBucket') }}</el-radio>
                </el-radio-group>
              </el-form-item>

              <!-- 创建新存储桶模式 -->
              <template v-if="obsForm.mode === 'create'">
                <el-form-item :label="$t('targetSelector.bucketName')" required>
                  <el-input v-model="obsForm.bucketName" :placeholder="$t('targetSelector.enterBucketName')"
                    @input="updateTargetPath" />
                </el-form-item>
                <el-form-item :label="$t('targetSelector.targetPath')">
                  <el-input v-model="obsForm.targetPath" :placeholder="$t('targetSelector.targetPathPlaceholder')"
                    @input="updateTargetPath" />
                </el-form-item>
              </template>

              <!-- 浏览现有存储桶模式 -->
              <template v-else>
                <el-form-item :label="$t('targetSelector.bucket')" required>
                  <el-select v-model="obsForm.selectedBucket" :placeholder="$t('targetSelector.selectBucket')"
                    @change="handleBucketChange" style="width: 100%">
                    <el-option v-for="bucket in buckets" :key="bucket.name" :label="bucket.name" :value="bucket.name">
                      <div class="bucket-option">
                        <Icon icon="mdi:bucket" class="bucket-icon" />
                        <span>{{ bucket.name }}</span>
                        <el-tag size="small" type="info">
                          {{ formatDate(bucket.created_at) }}
                        </el-tag>
                      </div>
                    </el-option>
                  </el-select>
                </el-form-item>

                <el-form-item :label="$t('targetSelector.targetPath')">
                  <div class="path-input-group">
                    <el-input v-model="obsForm.targetPath" :placeholder="$t('targetSelector.selectOrEnterTargetPath')"
                      @input="updateTargetPath">
                      <template #append>
                        <el-button @click="toggleObsPathSelector">
                          <Icon icon="mdi:folder-open" />
                          {{ $t('targetSelector.browse') }}
                        </el-button>
                      </template>
                    </el-input>
                  </div>
                </el-form-item>
              </template>
            </el-form>

            <!-- OBS 路径选择器 -->
            <div v-if="showObsPathSelector && obsForm.selectedBucket" class="obs-path-selector">
              <div class="path-selector-header">
                <h5>{{ $t('targetSelector.browseBucketContent') }}</h5>
                <div class="path-actions">
                  <el-button @click="refreshObsTree" :loading="obsLoading" size="small">
                    <Icon icon="mdi:refresh" />
                    {{ $t('targetSelector.refresh') }}
                  </el-button>
                  <el-button @click="expandAllObs" size="small">
                    <Icon icon="mdi:arrow-expand-all" />
                    {{ $t('targetSelector.expandAll') }}
                  </el-button>
                  <el-button @click="collapseAllObs" size="small">
                    <Icon icon="mdi:arrow-collapse-all" />
                    {{ $t('targetSelector.collapseAll') }}
                  </el-button>
                </div>
              </div>

              <div class="breadcrumb">
                <el-breadcrumb separator="/">
                  <el-breadcrumb-item @click="navigateToObsPath('')" class="breadcrumb-link">
                    {{ obsForm.selectedBucket }}
                  </el-breadcrumb-item>
                  <el-breadcrumb-item v-for="(segment, index) in obsPathSegments" :key="index"
                    @click="navigateToObsPath(obsPathSegments.slice(0, index + 1).join('/'))" class="breadcrumb-link">
                    {{ segment }}
                  </el-breadcrumb-item>
                </el-breadcrumb>
              </div>

              <!-- OBS 状态信息 -->
              <div v-if="!obsLoading && obsPagination.total > 0" class="status-info">
                <el-tag type="info" size="small">
                  {{ $t('targetSelector.totalObjects', { count: obsPagination.total }) }}
                </el-tag>
                <el-tag type="success" size="small" v-if="obsPathSegments.length > 0">
                  {{ $t('targetSelector.currentPath') }}: {{ obsPathSegments.join('/') }}
                </el-tag>
              </div>

              <div class="table-wrapper">
                <el-table :data="obsCurrentItems" v-loading="obsLoading" @row-click="handleObsItemClick"
                  class="directory-table" highlight-current-row
                  :empty-text="obsLoading ? $t('targetSelector.loadingObjectList') : $t('targetSelector.currentDirectoryEmpty')"
                  :max-height="tableMaxHeight">
                  <el-table-column width="50">
                    <template #default="{ row }">
                      <Icon :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'"
                        :class="['file-icon', row.type === 'directory' ? 'folder' : 'file']" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="name" :label="$t('targetSelector.name')">
                    <template #default="{ row }">
                      <span :class="{ 'directory-name': row.type === 'directory' }">
                        {{ row.name }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="size" :label="$t('targetSelector.size')" width="120">
                    <template #default="{ row }">
                      {{ row.type === 'directory' ? '-' : formatSize(row.size) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="lastModified" :label="$t('targetSelector.lastModified')" width="180">
                    <template #default="{ row }">
                      {{ formatDate(row.lastModified) }}
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('targetSelector.actions')" width="120">
                    <template #default="{ row }">
                      <el-button v-if="row.type === 'directory'" size="small" @click.stop="selectObsDirectory(row)">
                        {{ $t('targetSelector.select') }}
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- OBS 分页 -->
              <div v-if="obsPagination.total > 0" class="pagination-container">
                <el-pagination v-model:current-page="obsPagination.currentPage"
                  v-model:page-size="obsPagination.pageSize" :page-sizes="[10, 20, 50, 100]"
                  :total="obsPagination.total" layout="total, sizes, prev, pager, next"
                  @size-change="handleObsSizeChange" @current-change="handleObsPageChange" background />
              </div>
            </div>
          </div>
        </div>
      </template>

      <!-- NAS/NFS 存储配置 -->
      <template v-else>
        <div class="nas-config">
          <div class="config-header">
            <h4>{{ $t('targetSelector.configureTargetLocation') }}</h4>
            <p class="config-description">{{ $t('targetSelector.configureTargetLocationNasDesc') }}</p>
          </div>

          <div class="config-content">
            <el-form :model="nasForm" label-width="120px">
              <el-form-item :label="$t('targetSelector.targetPath')" required>
                <div class="path-input-group">
                  <el-input v-model="nasForm.targetPath" :placeholder="$t('targetSelector.selectOrEnterTargetPath')"
                    @input="updateTargetPath">
                    <template #append>
                      <el-button @click="toggleNasPathSelector">
                        <Icon icon="mdi:folder-open" />
                        {{ $t('targetSelector.browse') }}
                      </el-button>
                    </template>
                  </el-input>
                </div>
              </el-form-item>
            </el-form>

            <!-- NAS 路径选择器 -->
            <div v-if="showNasPathSelector" class="nas-path-selector">
              <div class="path-selector-header">
                <h5>{{ $t('targetSelector.browseDirectoryStructure') }}</h5>
                <div class="path-actions">
                  <el-button @click="refreshNasTree" :loading="nasLoading" size="small">
                    <Icon icon="mdi:refresh" />
                    {{ $t('targetSelector.refresh') }}
                  </el-button>
                  <el-button @click="expandAllNas" size="small">
                    <Icon icon="mdi:arrow-expand-all" />
                    {{ $t('targetSelector.expandAll') }}
                  </el-button>
                  <el-button @click="collapseAllNas" size="small">
                    <Icon icon="mdi:arrow-collapse-all" />
                    {{ $t('targetSelector.collapseAll') }}
                  </el-button>
                </div>
              </div>

              <div class="breadcrumb">
                <el-breadcrumb separator="/">
                  <el-breadcrumb-item @click="navigateToNasPath('')" class="breadcrumb-link">
                    {{ $t('targetSelector.rootDirectory') }}
                  </el-breadcrumb-item>
                  <el-breadcrumb-item v-for="(segment, index) in nasPathSegments" :key="index"
                    @click="navigateToNasPath(nasPathSegments.slice(0, index + 1).join('/'))" class="breadcrumb-link">
                    {{ segment }}
                  </el-breadcrumb-item>
                </el-breadcrumb>
              </div>

              <!-- NAS 状态信息 -->
              <div v-if="!nasLoading && nasPagination.total > 0" class="status-info">
                <el-tag type="info" size="small">
                  {{ $t('targetSelector.totalFilesFolders', { count: nasPagination.total }) }}
                </el-tag>
                <el-tag type="success" size="small" v-if="nasPathSegments.length > 0">
                  {{ $t('targetSelector.currentPath') }}: {{ nasPathSegments.join('/') }}
                </el-tag>
              </div>

              <div class="table-wrapper">
                <el-table :data="nasCurrentItems" v-loading="nasLoading" @row-click="handleNasItemClick"
                  class="directory-table" highlight-current-row
                  :empty-text="nasLoading ? $t('targetSelector.loadingFileList') : $t('targetSelector.currentDirectoryEmpty')"
                  :max-height="tableMaxHeight">
                  <el-table-column width="50">
                    <template #default="{ row }">
                      <Icon :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'"
                        :class="['file-icon', row.type === 'directory' ? 'folder' : 'file']" />
                    </template>
                  </el-table-column>
                  <el-table-column prop="name" label="名称">
                    <template #default="{ row }">
                      <span :class="{ 'directory-name': row.type === 'directory' }">
                        {{ row.name }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column prop="size" :label="$t('storage.size')" width="120">
                    <template #default="{ row }">
                      {{ row.type === 'directory' ? '-' : formatSize(row.size) }}
                    </template>
                  </el-table-column>
                  <el-table-column prop="modified_time" :label="$t('storage.lastModifiedTime')" width="180">
                    <template #default="{ row }">
                      {{ formatDate(row.modified_time) }}
                    </template>
                  </el-table-column>
                  <el-table-column :label="$t('common.action')" width="120">
                    <template #default="{ row }">
                      <el-button v-if="row.type === 'directory'" size="small" @click.stop="selectNasDirectory(row)">
                        {{ $t('common.select') }}
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>

              <!-- NAS 分页 -->
              <div v-if="nasPagination.total > 0" class="pagination-container">
                <el-pagination v-model:current-page="nasPagination.currentPage"
                  v-model:page-size="nasPagination.pageSize" :page-sizes="[10, 20, 50, 100]"
                  :total="nasPagination.total" layout="total, sizes, prev, pager, next"
                  @size-change="handleNasSizeChange" @current-change="handleNasPageChange" background />
              </div>
            </div>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import axios from 'axios'

const { t } = useI18n()

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({
      storageId: '',
      storageName: '',
      storageType: '',
      targetPath: ''
    })
  },
  sourceStorage: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 响应式数据
const storages = ref([])
const loading = ref(false)
const nasLoading = ref(false)
const obsLoading = ref(false)

// 表单数据
const form = ref({
  selectedStorageId: ''
})

// OBS 相关数据
const obsForm = ref({
  mode: 'browse', // 'browse' 或 'create'
  selectedBucket: '',
  bucketName: '',
  targetPath: ''
})

const buckets = ref([])
const showObsPathSelector = ref(false)
const obsCurrentItems = ref([])
const obsPathSegments = ref([])

// OBS 分页数据
const obsPagination = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// NAS 相关数据
const nasForm = ref({
  targetPath: ''
})

const showNasPathSelector = ref(false)
const nasCurrentItems = ref([])
const nasPathSegments = ref([])

// NAS 分页数据
const nasPagination = ref({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 计算属性
const selectedStorage = computed(() => {
  return storages.value.find(s => s.id === form.value.selectedStorageId)
})

// 计算表格最大高度
const tableMaxHeight = computed(() => {
  // 根据页面大小动态调整表格高度，预留更多空间给表格头部
  const pageSize = Math.max(obsPagination.value.pageSize, nasPagination.value.pageSize)

  // 基础行高约40px，加上头部和边距
  const baseRowHeight = 40
  const headerHeight = 60
  const padding = 30

  if (pageSize <= 20) {
    return 350
  } else if (pageSize <= 50) {
    return 450
  } else if (pageSize <= 100) {
    // 为100行提供足够空间：100 * 40 + 60 + 30 = 4090px，但限制在合理范围内
    return Math.min(650, pageSize * baseRowHeight + headerHeight + padding)
  } else {
    // 为更大的页面大小提供足够空间
    return Math.min(750, pageSize * baseRowHeight + headerHeight + padding)
  }
})

const nasStorages = computed(() => {
  return storages.value.filter(s => s.type === 'nas')
})

const obsStorages = computed(() => {
  return storages.value.filter(s => s.type === 's3')
})

const showOverrideWarning = computed(() => {
  return selectedStorage.value &&
    props.sourceStorage.storageId &&
    selectedStorage.value.id === props.sourceStorage.storageId
})

const overrideWarningText = computed(() => {
  if (selectedStorage.value?.type === 's3') {
    return t('targetSelector.overrideWarningObs')
  } else {
    return t('targetSelector.overrideWarningNas')
  }
})

// 方法
const fetchStorages = async () => {
  try {
    const response = await axios.get('/api/storages')
    if (response.data.status === 'success') {
      storages.value = response.data.storages || []
    } else {
      ElMessage.error(t('targetSelector.messages.getStorageListFailed'))
    }
  } catch (error) {
    ElMessage.error(t('targetSelector.messages.getStorageListFailed'))
  }
}

const handleStorageChange = async (storageId) => {
  if (!storageId) return

  // 重置表单
  obsForm.value = {
    mode: 'browse',
    selectedBucket: '',
    bucketName: '',
    targetPath: ''
  }
  nasForm.value = {
    targetPath: ''
  }

  // 重置分页状态
  obsPagination.value = {
    currentPage: 1,
    pageSize: 10,
    total: 0
  }
  nasPagination.value = {
    currentPage: 1,
    pageSize: 10,
    total: 0
  }

  // 关闭路径选择器
  showObsPathSelector.value = false
  showNasPathSelector.value = false

  const storage = storages.value.find(s => s.id === storageId)
  if (!storage) return

  // 如果是 OBS 存储，获取存储桶列表
  if (storage.type === 's3') {
    await fetchBuckets(storage.id)
  }

  updateModelValue()
}

const fetchBuckets = async (storageId) => {
  try {
    obsLoading.value = true
    const response = await axios.get(`/api/storages/${storageId}/buckets`)
    if (response.data.status === 'success') {
      buckets.value = response.data.data.buckets || []
    }
  } catch (error) {
    ElMessage.error(t('targetSelector.messages.getBucketListFailed'))
  } finally {
    obsLoading.value = false
  }
}

const handleObsModeChange = () => {
  if (obsForm.value.mode === 'create') {
    obsForm.value.selectedBucket = ''
    obsForm.value.targetPath = ''
  } else {
    obsForm.value.bucketName = ''
    obsForm.value.targetPath = ''
  }
  updateTargetPath()
}

const handleBucketChange = async (bucketName) => {
  obsForm.value.targetPath = ''
  obsPathSegments.value = []
  obsCurrentItems.value = []
  showObsPathSelector.value = false

  // 重置 OBS 分页状态
  obsPagination.value = {
    currentPage: 1,
    pageSize: 10,
    total: 0
  }

  if (bucketName) {
    await loadObsRoot(selectedStorage.value.id, bucketName)
  }

  updateTargetPath()
}

const toggleObsPathSelector = () => {
  if (!obsForm.value.selectedBucket) {
    ElMessage.warning(t('targetSelector.messages.selectBucketFirst'))
    return
  }
  showObsPathSelector.value = !showObsPathSelector.value
  if (showObsPathSelector.value && obsCurrentItems.value.length === 0) {
    loadObsRoot(selectedStorage.value.id, obsForm.value.selectedBucket)
  }
}

const toggleNasPathSelector = () => {
  showNasPathSelector.value = !showNasPathSelector.value
  if (showNasPathSelector.value && nasCurrentItems.value.length === 0) {
    loadNasRoot()
  }
}

const refreshObsTree = async () => {
  if (obsForm.value.selectedBucket) {
    await loadObsRoot(selectedStorage.value.id, obsForm.value.selectedBucket)
  }
}

const refreshNasTree = async () => {
  await loadNasRoot()
}

const expandAllObs = () => {
  // 实现展开全部逻辑
}

const collapseAllObs = () => {
  // 实现收起全部逻辑
}

const expandAllNas = () => {
  // 实现展开全部逻辑
}

const collapseAllNas = () => {
  // 实现收起全部逻辑
}

// OBS 分页事件处理
const handleObsPageChange = async (page) => {
  obsPagination.value.currentPage = page
  await loadObsCurrentPage()
}

const handleObsSizeChange = async (size) => {
  obsPagination.value.pageSize = size
  obsPagination.value.currentPage = 1
  await loadObsCurrentPage()
}

const loadObsCurrentPage = async () => {
  try {
    obsLoading.value = true
    const currentPath = obsPathSegments.value.join('/')
    const prefix = currentPath ? currentPath + '/' : ''

    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/objects`, {
      params: {
        node_id: selectedStorage.value.node_id,
        bucket: obsForm.value.selectedBucket,
        prefix: prefix,
        page: obsPagination.value.currentPage,
        page_size: obsPagination.value.pageSize
      }
    })

    if (response.data.status === 'success') {
      const data = response.data.data
      const objects = data.objects || []
      obsCurrentItems.value = objects.map(obj => ({
        name: obj.name,
        key: obj.key,
        type: obj.type,
        size: obj.size,
        lastModified: obj.lastModified,
        bucket: obsForm.value.selectedBucket
      }))

      // 更新分页信息
      if (data.pagination) {
        obsPagination.value.total = data.pagination.total_count || 0
      }
    }
  } catch (error) {
    ElMessage.error(t('targetSelector.messages.getObjectListFailed'))
  } finally {
    obsLoading.value = false
  }
}

// NAS 分页事件处理
const handleNasPageChange = async (page) => {
  nasPagination.value.currentPage = page
  await loadNasCurrentPage()
}

const handleNasSizeChange = async (size) => {
  nasPagination.value.pageSize = size
  nasPagination.value.currentPage = 1
  await loadNasCurrentPage()
}

const loadNasCurrentPage = async () => {
  try {
    nasLoading.value = true
    const currentPath = nasPathSegments.value.join('/')

    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/files`, {
      params: {
        node_id: selectedStorage.value.node_id,
        path: currentPath,
        page: nasPagination.value.currentPage,
        page_size: nasPagination.value.pageSize
      }
    })

    if (response.data.status === 'success') {
      const data = response.data.data
      const files = data.objects || []
      nasCurrentItems.value = files.map(file => ({
        name: file.name,
        path: file.path,
        type: file.type,
        size: file.size,
        modified_time: file.modified_time
      }))

      // 更新分页信息
      if (data.pagination) {
        nasPagination.value.total = data.pagination.total_count || 0
      }
    }
  } catch (error) {
    ElMessage.error(t('targetSelector.messages.getFileListFailed'))
  } finally {
    nasLoading.value = false
  }
}

const loadObsRoot = async (storageId, bucketName) => {
  try {
    obsLoading.value = true
    // 重置分页
    obsPagination.value.currentPage = 1

    const response = await axios.get(`/api/storages/${storageId}/objects`, {
      params: {
        node_id: selectedStorage.value.node_id,
        bucket: bucketName,
        prefix: '',
        page: obsPagination.value.currentPage,
        page_size: obsPagination.value.pageSize
      }
    })

    if (response.data.status === 'success') {
      const data = response.data.data
      const objects = data.objects || []
      obsCurrentItems.value = objects.map(obj => ({
        name: obj.name,
        key: obj.key,
        type: obj.type,
        size: obj.size,
        lastModified: obj.lastModified,
        bucket: bucketName
      }))

      // 更新分页信息
      if (data.pagination) {
        obsPagination.value.total = data.pagination.total_count || 0
      }
    }
  } catch (error) {
    ElMessage.error('获取对象列表失败')
  } finally {
    obsLoading.value = false
  }
}

const navigateToObsPath = async (path) => {
  obsPathSegments.value = path ? path.split('/').filter(Boolean) : []

  try {
    obsLoading.value = true
    // 重置分页
    obsPagination.value.currentPage = 1

    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/objects`, {
      params: {
        node_id: selectedStorage.value.node_id,
        bucket: obsForm.value.selectedBucket,
        prefix: path + '/',
        page: obsPagination.value.currentPage,
        page_size: obsPagination.value.pageSize
      }
    })

    if (response.data.status === 'success') {
      const data = response.data.data
      const objects = data.objects || []
      obsCurrentItems.value = objects.map(obj => ({
        name: obj.name,
        key: obj.key,
        type: obj.type,
        size: obj.size,
        lastModified: obj.lastModified,
        bucket: obsForm.value.selectedBucket
      }))

      // 更新分页信息
      if (data.pagination) {
        obsPagination.value.total = data.pagination.total_count || 0
      }
    }
  } catch (error) {
    ElMessage.error('获取对象列表失败')
  } finally {
    obsLoading.value = false
  }
}

const handleObsItemClick = (row) => {
  if (row.type === 'directory') {
    const newPath = obsPathSegments.value.length > 0
      ? obsPathSegments.value.join('/') + '/' + row.name
      : row.name
    navigateToObsPath(newPath)
  }
}

const selectObsDirectory = (row) => {
  const path = obsPathSegments.value.length > 0
    ? obsPathSegments.value.join('/') + '/' + row.name
    : row.name
  obsForm.value.targetPath = path
  showObsPathSelector.value = false
  updateTargetPath()
}

const loadNasRoot = async () => {
  try {
    nasLoading.value = true
    // 重置分页
    nasPagination.value.currentPage = 1

    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/files`, {
      params: {
        node_id: selectedStorage.value.node_id,
        path: '',
        page: nasPagination.value.currentPage,
        page_size: nasPagination.value.pageSize
      }
    })

    if (response.data.status === 'success') {
      const data = response.data.data
      const files = data.objects || []
      nasCurrentItems.value = files.map(file => ({
        name: file.name,
        path: file.path,
        type: file.type,
        size: file.size,
        modified_time: file.modified_time
      }))

      // 更新分页信息
      if (data.pagination) {
        nasPagination.value.total = data.pagination.total_count || 0
      }
    }
  } catch (error) {
    ElMessage.error('获取文件列表失败')
  } finally {
    nasLoading.value = false
  }
}

const navigateToNasPath = async (path) => {
  nasPathSegments.value = path ? path.split('/').filter(Boolean) : []

  try {
    nasLoading.value = true
    // 重置分页
    nasPagination.value.currentPage = 1

    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/files`, {
      params: {
        node_id: selectedStorage.value.node_id,
        path: path,
        page: nasPagination.value.currentPage,
        page_size: nasPagination.value.pageSize
      }
    })

    if (response.data.status === 'success') {
      const data = response.data.data
      const files = data.objects || []
      nasCurrentItems.value = files.map(file => ({
        name: file.name,
        path: file.path,
        type: file.type,
        size: file.size,
        modified_time: file.modified_time
      }))

      // 更新分页信息
      if (data.pagination) {
        nasPagination.value.total = data.pagination.total_count || 0
      }
    }
  } catch (error) {
    ElMessage.error('获取文件列表失败')
  } finally {
    nasLoading.value = false
  }
}

const handleNasItemClick = (row) => {
  if (row.type === 'directory') {
    const newPath = nasPathSegments.value.length > 0
      ? nasPathSegments.value.join('/') + '/' + row.name
      : row.name
    navigateToNasPath(newPath)
  }
}

const selectNasDirectory = (row) => {
  const path = nasPathSegments.value.length > 0
    ? nasPathSegments.value.join('/') + '/' + row.name
    : row.name
  nasForm.value.targetPath = path
  showNasPathSelector.value = false
  updateTargetPath()
}

const updateTargetPath = () => {
  let targetPath = ''

  if (selectedStorage.value?.type === 's3') {
    if (obsForm.value.mode === 'create') {
      targetPath = obsForm.value.bucketName
      if (obsForm.value.targetPath) {
        targetPath += '/' + obsForm.value.targetPath
      }
    } else {
      if (obsForm.value.selectedBucket) {
        targetPath = obsForm.value.selectedBucket
        if (obsForm.value.targetPath) {
          targetPath += '/' + obsForm.value.targetPath
        }
      }
    }
  } else {
    targetPath = nasForm.value.targetPath
  }

  updateModelValue(targetPath)
}

const updateModelValue = (targetPath = '') => {
  // 确定目标路径
  let finalTargetPath = targetPath
  if (!finalTargetPath) {
    if (selectedStorage.value?.type === 's3') {
      if (obsForm.value.mode === 'create') {
        finalTargetPath = obsForm.value.bucketName + (obsForm.value.targetPath ? '/' + obsForm.value.targetPath : '')
      } else {
        finalTargetPath = obsForm.value.selectedBucket + (obsForm.value.targetPath ? '/' + obsForm.value.targetPath : '')
      }
    } else {
      finalTargetPath = nasForm.value.targetPath
    }
  }

  // 清理最终路径，移除多余的斜杠
  finalTargetPath = finalTargetPath.replace(/\/+/g, '/').replace(/^\/+|\/+$/g, '')

  const value = {
    storageId: form.value.selectedStorageId,
    storageName: selectedStorage.value?.name || '',
    storageType: selectedStorage.value?.type || '',
    targetPath: finalTargetPath
  }

  emit('update:modelValue', value)
  emit('change', value)
}

// 辅助函数
const formatSize = (bytes) => {
  if (!bytes || bytes === 0) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB', 'TB']
  let size = bytes
  let unitIndex = 0
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const formatDate = (date) => {
  if (!date) return ''
  return new Date(date).toLocaleString('zh-CN')
}

const getProviderText = (provider) => {
  const texts = {
    'aws': 'AWS',
    'google': 'Google',
    'tencent': '腾讯云',
    'aliyun': '阿里云',
    'huawei': '华为云',
    'minio': 'MinIO',
    'other': '其他'
  }
  return texts[provider] || '未知'
}

// 新增：设置初始状态的方法
const setInitialState = async (initialData) => {
  if (!initialData) {
    form.value.selectedStorageId = ''
    nasForm.value.targetPath = ''
    obsForm.value.targetPath = ''
    obsForm.value.selectedBucket = ''
    return
  }

  if (!initialData.storageId) return
  // 设置存储选择
  form.value.selectedStorageId = initialData.storageId

  // 等待存储列表加载完成
  if (storages.value.length === 0) {
    await fetchStorages()
  }

  // 触发存储变更，确保selectedStorage正确设置
  await handleStorageChange(initialData.storageId)

  // 等待存储类型确定后再设置目标路径
  await new Promise(resolve => setTimeout(resolve, 200))

  // 设置目标路径
  if (initialData.targetPath) {
    if (selectedStorage.value?.type === 's3') {
      const cleanPath = initialData.targetPath.replace(/\/+/g, '/').replace(/^\/+|\/+$/g, '')
      const pathParts = cleanPath.split('/')
      if (pathParts.length > 0 && pathParts[0]) {
        obsForm.value.selectedBucket = pathParts[0]
        if (pathParts.length > 1) {
          obsForm.value.targetPath = pathParts.slice(1).join('/')
        } else {
          obsForm.value.targetPath = ''
        }
      }
    } else {
      nasForm.value.targetPath = initialData.targetPath
    }

    const value = {
      storageId: form.value.selectedStorageId,
      storageName: selectedStorage.value?.name || '',
      storageType: selectedStorage.value?.type || '',
      targetPath: initialData.targetPath || ''
    }
    emit('update:modelValue', value)
  }
}

// 获取当前状态
const getCurrentState = () => {
  return {
    form: form.value,
    nasForm: nasForm.value,
    obsForm: obsForm.value,
    selectedStorage: selectedStorage.value
  }
}

// 设置状态
const setState = (state) => {
  if (state) {
    if (state.form) {
      form.value.selectedStorageId = state.form.selectedStorageId || ''
    }
    if (state.nasForm) {
      nasForm.value.targetPath = state.nasForm.targetPath || ''
    }
    if (state.obsForm) {
      obsForm.value.targetPath = state.obsForm.targetPath || ''
    }
    updateModelValue()
  }
}

// 暴露方法给父组件
defineExpose({
  setInitialState,
  getCurrentState,
  setState
})

watch(() => props.modelValue, (newValue, oldValue) => {
  if (newValue && newValue.storageId && newValue.storageId !== form.value.selectedStorageId) {
    form.value.selectedStorageId = newValue.storageId || ''
    if (newValue.storageId) {
      handleStorageChange(newValue.storageId)
    }

    setTimeout(() => {
      updateModelValue()
    }, 100)
  }

  if (newValue && newValue.targetPath) {
    const cleanPath = newValue.targetPath.replace(/\/+/g, '/').replace(/^\/+|\/+$/g, '')

    let shouldUpdate = false

    if (selectedStorage.value?.type === 's3') {
      const pathParts = cleanPath.split('/')
      const expectedBucket = pathParts.length > 0 ? pathParts[0] : ''
      const expectedPath = pathParts.length > 1 ? pathParts.slice(1).join('/') : ''

      shouldUpdate = obsForm.value.selectedBucket !== expectedBucket || obsForm.value.targetPath !== expectedPath
    } else {
      shouldUpdate = nasForm.value.targetPath !== cleanPath
    }

    if (shouldUpdate) {
      if (selectedStorage.value?.type === 's3') {
        const pathParts = cleanPath.split('/')
        if (pathParts.length > 0 && pathParts[0]) {
          obsForm.value.selectedBucket = pathParts[0]
          if (pathParts.length > 1) {
            obsForm.value.targetPath = pathParts.slice(1).join('/')
          } else {
            obsForm.value.targetPath = ''
          }
        }
      } else {
        nasForm.value.targetPath = cleanPath
      }
      setTimeout(() => {
        updateModelValue()
      }, 100)
    }
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  fetchStorages()
})
</script>

<style scoped>
.target-selector {
  padding: 20px;
}

.storage-selection {
  margin-bottom: 30px;
}

.selection-header {
  margin-bottom: 20px;
}

.selection-header h3 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 20px;
  font-weight: 600;
}

.selection-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.storage-option {
  display: flex;
  align-items: center;
  width: 100%;
  gap: 12px;
}

.storage-icon {
  font-size: 20px;
  color: var(--el-color-primary);
}

.storage-info {
  flex: 1;
  min-width: 0;
}

.storage-name {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

.storage-detail {
  font-size: 12px;
  color: var(--el-text-color-secondary);
  margin-top: 2px;
}

.override-warning {
  margin-bottom: 20px;
}

.target-path-section {
  border: 1px solid var(--el-border-color);
  border-radius: 8px;
  overflow: hidden;
  background: var(--el-bg-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.config-header {
  padding: 20px 24px;
  background: linear-gradient(135deg, var(--el-color-primary-light-9) 0%, var(--el-color-primary-light-8) 100%);
  border-bottom: 1px solid var(--el-border-color);
}

.config-header h4 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 18px;
  font-weight: 600;
}

.config-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.config-content {
  padding: 24px;
}

.obs-config,
.nas-config {
  background: var(--el-bg-color);
}

.path-input-group {
  margin-bottom: 16px;
}

.bucket-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bucket-icon {
  color: #409eff;
}

.obs-path-selector,
.nas-path-selector {
  margin-top: 20px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
  background: var(--el-bg-color-page);
}

.path-selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-border-color);
}

.path-selector-header h5 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 16px;
  font-weight: 500;
}

.path-actions {
  display: flex;
  gap: 8px;
}

.breadcrumb {
  padding: 12px 20px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color);
}

.breadcrumb-link {
  cursor: pointer;
  color: var(--el-color-primary);
  transition: color 0.2s;
}

.breadcrumb-link:hover {
  color: var(--el-color-primary-dark-2);
  text-decoration: underline;
}

/* 确保表格容器有合适的高度 */
.obs-path-selector,
.nas-path-selector {
  max-height: 750px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* 表格包装器样式 */
.table-wrapper {
  flex: 1;
  min-height: 0;
  position: relative;
  overflow: hidden;
  padding-bottom: 10px;
  /* 增加底部边距 */
}

/* 表格区域样式 */
.directory-table {
  height: 100%;
  width: 100%;
}

/* 确保表格头部固定 */
:deep(.el-table__header-wrapper) {
  position: sticky;
  top: 0;
  z-index: 2;
  background: var(--el-bg-color);
}

/* 确保表格体可以滚动 */
:deep(.el-table__body-wrapper) {
  overflow-y: auto !important;
  overflow-x: hidden;
  max-height: calc(100% - 60px) !important;
  /* 增加头部预留空间 */
  scroll-padding-bottom: 15px;
  /* 增加滚动底部边距 */
  scroll-behavior: smooth;
}

/* 确保表格有足够的底部空间 */
:deep(.el-table__body) {
  overflow: visible !important;
  padding-bottom: 15px;
  /* 增加底部边距 */
}

/* 确保表格容器不会阻止滚动 */
:deep(.el-table) {
  overflow: visible;
}

/* 确保表格行有足够的可见性 */
:deep(.el-table__row) {
  cursor: pointer;
  min-height: 40px;
}

/* 确保表格单元格内容可以正常显示 */
:deep(.el-table__cell) {
  overflow: visible;
}

/* 优化滚动条样式 */
:deep(.el-table__body-wrapper::-webkit-scrollbar) {
  width: 8px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-track) {
  background: var(--el-border-color-lighter);
  border-radius: 4px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-thumb) {
  background: var(--el-border-color);
  border-radius: 4px;
}

:deep(.el-table__body-wrapper::-webkit-scrollbar-thumb:hover) {
  background: var(--el-border-color-dark);
}

.pagination-container {
  padding: 16px 20px;
  background: var(--el-bg-color-page);
  border-top: 1px solid var(--el-border-color);
  display: flex;
  justify-content: center;
}

.status-info {
  padding: 12px 20px;
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  gap: 8px;
  align-items: center;
}

.file-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.folder {
  color: #f7ba2a;
}

.file {
  color: #67c23a;
}

.directory-name {
  font-weight: 500;
  color: var(--el-color-primary);
}

:deep(.el-form-item__label) {
  font-weight: 500;
  color: var(--el-text-color-primary);
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px var(--el-border-color) inset;
  transition: box-shadow 0.2s;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-input__wrapper.is-focus) {
  box-shadow: 0 0 0 1px var(--el-color-primary) inset;
}

:deep(.el-button) {
  border-radius: 6px;
  font-weight: 500;
  transition: all 0.2s;
}

:deep(.el-button:hover) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

:deep(.el-radio__label) {
  font-weight: 500;
}

:deep(.el-table) {
  border-radius: 6px;
  overflow: hidden;
}

:deep(.el-table th) {
  background-color: var(--el-color-primary-light-9);
  font-weight: 600;
  color: var(--el-text-color-primary);
}

:deep(.el-table td) {
  padding: 8px 0;
}

:deep(.el-table th) {
  padding: 10px 0;
}

:deep(.el-alert) {
  border-radius: 8px;
  border: none;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

:deep(.el-table tbody tr:hover > td) {
  background-color: var(--el-color-primary-light-9) !important;
}

:deep(.el-table tbody tr.current-row > td) {
  background-color: var(--el-color-primary-light-8) !important;
}

:deep(.el-select-dropdown__item) {
  height: auto;
  padding: 12px 20px;
  line-height: normal;
}

:deep(.el-option-group__title) {
  padding: 12px 20px 8px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}
</style>