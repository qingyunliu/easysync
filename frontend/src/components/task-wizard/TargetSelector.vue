<template>
  <div class="target-selector">
    <!-- 存储选择 -->
    <div class="storage-selection">
      <el-form :model="form" label-width="120px">
        <el-form-item label="目标端存储" required>
          <el-select 
            v-model="form.selectedStorageId" 
            placeholder="请选择目标端存储" 
            style="width: 100%"
            @change="handleStorageChange"
          >
            <el-option-group label="NAS 存储">
              <el-option
                v-for="storage in nasStorages"
                :key="storage.id"
                :label="`${storage.name} (${storage.config.protocol.toUpperCase()})`"
                :value="storage.id"
              >
                <div class="storage-option">
                  <Icon icon="mdi:folder-network" class="storage-icon" />
                  <div class="storage-info">
                    <div class="storage-name">{{ storage.name }}</div>
                    <div class="storage-detail">{{ storage.config.server }}:{{ storage.config.path }}</div>
                  </div>
                  <el-tag 
                    :type="storage.config.is_mounted ? 'success' : 'warning'" 
                    size="small"
                  >
                    {{ storage.config.is_mounted ? '已挂载' : '未挂载' }}
                  </el-tag>
                </div>
              </el-option>
            </el-option-group>
            <el-option-group label="OBS 存储">
              <el-option
                v-for="storage in obsStorages"
                :key="storage.id"
                :label="`${storage.name} (${storage.config.provider.toUpperCase()})`"
                :value="storage.id"
              >
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
      <el-alert
        title="数据覆盖警告"
        type="warning"
        :description="overrideWarningText"
        show-icon
        :closable="false"
      />
    </div>

    <!-- 目标路径配置 -->
    <div v-if="selectedStorage" class="target-path-config">
      <div class="config-header">
        <h4>配置目标位置</h4>
        <p class="config-description">
          {{ getConfigDescription() }}
        </p>
      </div>

      <!-- OBS 存储配置 -->
      <template v-if="selectedStorage.type === 's3'">
        <div class="obs-config">
          <el-form :model="obsForm" label-width="120px">
            <el-form-item label="操作模式" required>
              <el-radio-group v-model="obsForm.mode" @change="handleObsModeChange">
                <el-radio label="browse">浏览现有存储桶</el-radio>
                <el-radio label="create">创建新存储桶</el-radio>
              </el-radio-group>
            </el-form-item>

            <!-- 创建新存储桶模式 -->
            <template v-if="obsForm.mode === 'create'">
              <el-form-item label="存储桶名称" required>
                <el-input 
                  v-model="obsForm.bucketName" 
                  placeholder="请输入存储桶名称"
                  @input="updateTargetPath"
                />
              </el-form-item>
              <el-form-item label="目标路径">
                <el-input 
                  v-model="obsForm.targetPath" 
                  placeholder="可选：指定存储桶内的路径，如 folder1/subfolder"
                  @input="updateTargetPath"
                />
              </el-form-item>
            </template>

            <!-- 浏览现有存储桶模式 -->
            <template v-else>
              <el-form-item label="存储桶" required>
                <el-select 
                  v-model="obsForm.selectedBucket" 
                  placeholder="请选择存储桶"
                  @change="handleBucketChange"
                  style="width: 100%"
                >
                  <el-option
                    v-for="bucket in buckets"
                    :key="bucket.name"
                    :label="bucket.name"
                    :value="bucket.name"
                  >
                    <div class="bucket-option">
                      <Icon icon="mdi:bucket" class="bucket-icon" />
                      <span>{{ bucket.name }}</span>
                      <el-tag size="small" type="info">
                        {{ formatDate(bucket.creationDate) }}
                      </el-tag>
                    </div>
                  </el-option>
                </el-select>
              </el-form-item>

              <el-form-item label="目标路径">
                <div class="path-input-group">
                  <el-input
                    v-model="obsForm.targetPath"
                    placeholder="请选择或输入目标路径"
                    @input="updateTargetPath"
                  >
                    <template #append>
                      <el-button @click="toggleObsPathSelector">
                        <Icon icon="mdi:folder-open" />
                        浏览
                      </el-button>
                    </template>
                  </el-input>
                </div>

                <!-- OBS 路径选择器 -->
                <div v-if="showObsPathSelector && obsForm.selectedBucket" class="obs-path-selector">
                  <div class="breadcrumb">
                    <el-breadcrumb separator="/">
                      <el-breadcrumb-item @click="navigateToObsPath('')" class="breadcrumb-link">
                        {{ obsForm.selectedBucket }}
                      </el-breadcrumb-item>
                      <el-breadcrumb-item 
                        v-for="(segment, index) in obsPathSegments" 
                        :key="index"
                        @click="navigateToObsPath(obsPathSegments.slice(0, index + 1).join('/'))"
                        class="breadcrumb-link"
                      >
                        {{ segment }}
                      </el-breadcrumb-item>
                    </el-breadcrumb>
                  </div>

                  <el-table
                    :data="obsCurrentItems"
                    v-loading="obsLoading"
                    @row-click="handleObsItemClick"
                    class="directory-table"
                    highlight-current-row
                  >
                    <el-table-column width="50">
                      <template #default="{ row }">
                        <Icon 
                          :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'" 
                          :class="['file-icon', row.type === 'directory' ? 'folder' : 'file']"
                        />
                      </template>
                    </el-table-column>
                    <el-table-column prop="name" label="名称">
                      <template #default="{ row }">
                        <span :class="{ 'directory-name': row.type === 'directory' }">
                          {{ row.name }}
                        </span>
                      </template>
                    </el-table-column>
                    <el-table-column prop="size" label="大小" width="120">
                      <template #default="{ row }">
                        {{ row.type === 'directory' ? '-' : formatSize(row.size) }}
                      </template>
                    </el-table-column>
                    <el-table-column prop="lastModified" label="修改时间" width="180">
                      <template #default="{ row }">
                        {{ formatDate(row.lastModified) }}
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="120">
                      <template #default="{ row }">
                        <el-button 
                          v-if="row.type === 'directory'"
                          size="small" 
                          @click.stop="selectObsDirectory(row)"
                        >
                          选择
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
              </el-form-item>
            </template>
          </el-form>
        </div>
      </template>

      <!-- NAS/NFS 存储配置 -->
      <template v-else>
        <div class="nas-config">
          <el-form :model="nasForm" label-width="120px">
            <el-form-item label="目标路径" required>
              <div class="path-input-group">
                <el-input
                  v-model="nasForm.targetPath"
                  placeholder="请选择或输入目标路径"
                  @input="updateTargetPath"
                >
                  <template #append>
                    <el-button @click="toggleNasPathSelector">
                      <Icon icon="mdi:folder-open" />
                      浏览
                    </el-button>
                  </template>
                </el-input>
              </div>

              <!-- NAS 路径选择器 -->
              <div v-if="showNasPathSelector" class="nas-path-selector">
                <div class="breadcrumb">
                  <el-breadcrumb separator="/">
                    <el-breadcrumb-item @click="navigateToNasPath('')" class="breadcrumb-link">
                      根目录
                    </el-breadcrumb-item>
                    <el-breadcrumb-item 
                      v-for="(segment, index) in nasPathSegments" 
                      :key="index"
                      @click="navigateToNasPath(nasPathSegments.slice(0, index + 1).join('/'))"
                      class="breadcrumb-link"
                    >
                      {{ segment }}
                    </el-breadcrumb-item>
                  </el-breadcrumb>
                </div>

                <el-table
                  :data="nasCurrentItems"
                  v-loading="nasLoading"
                  @row-click="handleNasItemClick"
                  class="directory-table"
                  highlight-current-row
                >
                  <el-table-column width="50">
                    <template #default="{ row }">
                      <Icon 
                        :icon="row.type === 'directory' ? 'mdi:folder' : 'mdi:file'" 
                        :class="['file-icon', row.type === 'directory' ? 'folder' : 'file']"
                      />
                    </template>
                  </el-table-column>
                  <el-table-column prop="name" label="名称">
                    <template #default="{ row }">
                      <span :class="{ 'directory-name': row.type === 'directory' }">
                        {{ row.name }}
                      </span>
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
                  <el-table-column label="操作" width="120">
                    <template #default="{ row }">
                      <el-button 
                        v-if="row.type === 'directory'"
                        size="small" 
                        @click.stop="selectNasDirectory(row)"
                      >
                        选择
                      </el-button>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </el-form-item>
          </el-form>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Icon } from '@iconify/vue'
import axios from 'axios'

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

// NAS 相关数据
const nasForm = ref({
  targetPath: ''
})

const showNasPathSelector = ref(false)
const nasCurrentItems = ref([])
const nasPathSegments = ref([])

// 计算属性
const selectedStorage = computed(() => {
  return storages.value.find(s => s.id === form.value.selectedStorageId)
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
    return '您选择了与源端相同的对象存储，可能会导致数据覆盖。请确保目标路径与源端路径不同。'
  } else {
    return '您选择了与源端相同的存储，可能会导致数据覆盖。请确保目标路径与源端路径不同。'
  }
})

// 方法
const fetchStorages = async () => {
  try {
    console.log('TargetSelector: 开始获取存储列表...')
    const response = await axios.get('/api/storages')
    console.log('TargetSelector: 存储列表响应:', response.data)
    if (response.data.status === 'success') {
      storages.value = response.data.storages || []
      console.log('TargetSelector: 存储列表已更新:', storages.value)
    } else {
      console.error('TargetSelector: 获取存储列表失败:', response.data.message)
      ElMessage.error('获取存储列表失败')
    }
  } catch (error) {
    console.error('TargetSelector: 获取存储列表错误:', error)
    ElMessage.error('获取存储列表失败')
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
    ElMessage.error('获取存储桶列表失败')
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
  
  if (bucketName) {
    await loadObsRoot(selectedStorage.value.id, bucketName)
  }
  
  updateTargetPath()
}

const toggleObsPathSelector = () => {
  if (!obsForm.value.selectedBucket) {
    ElMessage.warning('请先选择存储桶')
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

const loadObsRoot = async (storageId, bucketName) => {
  try {
    obsLoading.value = true
    const response = await axios.get(`/api/storages/${storageId}/objects`, {
      params: {
        bucket: bucketName,
        prefix: '',
        page: 1,
        page_size: 1000
      }
    })
    
    if (response.data.status === 'success') {
      const objects = response.data.data.objects || []
      obsCurrentItems.value = objects.map(obj => ({
        name: obj.name,
        key: obj.key,
        type: obj.type,
        size: obj.size,
        lastModified: obj.lastModified,
        bucket: bucketName
      }))
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
    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/objects`, {
      params: {
        bucket: obsForm.value.selectedBucket,
        prefix: path + '/',
        page: 1,
        page_size: 1000
      }
    })
    
    if (response.data.status === 'success') {
      const objects = response.data.data.objects || []
      obsCurrentItems.value = objects.map(obj => ({
        name: obj.name,
        key: obj.key,
        type: obj.type,
        size: obj.size,
        lastModified: obj.lastModified,
        bucket: obsForm.value.selectedBucket
      }))
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
    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/files`, {
      params: {
        node_id: selectedStorage.value.node_id,
        path: '',
        page: 1,
        page_size: 1000
      }
    })
    
    if (response.data.status === 'success') {
      const files = response.data.data.objects || []
      nasCurrentItems.value = files.map(file => ({
        name: file.name,
        path: file.path,
        type: file.type,
        size: file.size,
        modified_time: file.modified_time
      }))
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
    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/files`, {
      params: {
        node_id: selectedStorage.value.node_id,
        path: path,
        page: 1,
        page_size: 1000
      }
    })
    
    if (response.data.status === 'success') {
      const files = response.data.data.objects || []
      nasCurrentItems.value = files.map(file => ({
        name: file.name,
        path: file.path,
        type: file.type,
        size: file.size,
        modified_time: file.modified_time
      }))
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
  const value = {
    storageId: form.value.selectedStorageId,
    storageName: selectedStorage.value?.name || '',
    storageType: selectedStorage.value?.type || '',
    targetPath: targetPath || (selectedStorage.value?.type === 's3' 
      ? (obsForm.value.mode === 'create' 
        ? (obsForm.value.bucketName + (obsForm.value.targetPath ? '/' + obsForm.value.targetPath : ''))
        : (obsForm.value.selectedBucket + (obsForm.value.targetPath ? '/' + obsForm.value.targetPath : '')))
      : nasForm.value.targetPath)
  }
  emit('update:modelValue', value)
  emit('change', value)
}

const getConfigDescription = () => {
  if (selectedStorage.value?.type === 's3') {
    return '您可以选择浏览现有存储桶或创建新的存储桶来作为同步目标。'
  } else {
    return '请选择目标目录路径，您可以通过浏览功能查看目录结构。'
  }
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

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue && newValue.storageId !== form.value.selectedStorageId) {
    form.value.selectedStorageId = newValue.storageId || ''
    if (newValue.storageId) {
      handleStorageChange(newValue.storageId)
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

.target-path-config {
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
}

.config-header {
  padding: 16px 20px;
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-border-color);
}

.config-header h4 {
  margin: 0 0 8px 0;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.config-description {
  margin: 0;
  color: var(--el-text-color-secondary);
  font-size: 14px;
}

.obs-config,
.nas-config {
  padding: 20px;
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
  margin-top: 16px;
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
}

.breadcrumb {
  padding: 12px 16px;
  background: var(--el-bg-color-page);
  border-bottom: 1px solid var(--el-border-color);
}

.breadcrumb-link {
  cursor: pointer;
  color: var(--el-color-primary);
}

.breadcrumb-link:hover {
  text-decoration: underline;
}

.directory-table {
  max-height: 400px;
  overflow-y: auto;
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