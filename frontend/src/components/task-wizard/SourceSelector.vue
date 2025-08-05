<template>
  <div class="source-selector">
    <!-- 存储选择 -->
    <div class="storage-selection">
      <el-form :model="form" label-width="120px">
        <el-form-item label="源端存储" required>
          <el-select 
            v-model="form.selectedStorageId" 
            placeholder="请选择源端存储" 
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

    <!-- 目录树选择 -->
    <div v-if="selectedStorage" class="directory-tree">
      <div class="tree-header">
        <h4>选择要同步的目录或文件</h4>
        <div class="tree-actions">
          <el-button @click="refreshTree" :loading="loading" size="small">
            <Icon icon="mdi:refresh" />
            刷新
          </el-button>
          <el-button @click="expandAll" size="small">
            <Icon icon="mdi:arrow-expand-all" />
            展开全部
          </el-button>
          <el-button @click="collapseAll" size="small">
            <Icon icon="mdi:arrow-collapse-all" />
            收起全部
          </el-button>
        </div>
      </div>

      <!-- NAS 目录树 -->
      <template v-if="selectedStorage.type === 'nas'">
        <el-tree
          ref="nasTreeRef"
          :data="treeData"
          :props="treeProps"
          show-checkbox
          node-key="path"
          :load="loadNasNode"
          lazy
          v-loading="loading"
          @check="handleCheck"
          class="file-tree"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <Icon 
                :icon="data.type === 'directory' ? 'mdi:folder' : 'mdi:file'" 
                :class="['node-icon', data.type === 'directory' ? 'folder-icon' : 'file-icon']"
              />
              <span class="node-name">{{ node.label }}</span>
              <div class="node-info">
                <span v-if="data.size !== undefined" class="file-size">
                  {{ formatSize(data.size) }}
                </span>
                <span v-if="data.modified_time" class="modified-time">
                  {{ formatDate(data.modified_time) }}
                </span>
              </div>
            </div>
          </template>
        </el-tree>
      </template>

      <!-- OBS 存储桶和对象树 -->
      <template v-else-if="selectedStorage.type === 's3'">
        <el-tree
          ref="obsTreeRef"
          :data="treeData"
          :props="treeProps"
          show-checkbox
          node-key="key"
          :load="loadObsNode"
          lazy
          v-loading="loading"
          @check="handleCheck"
          class="file-tree"
        >
          <template #default="{ node, data }">
            <div class="tree-node">
              <Icon 
                :icon="getBucketIcon(data)" 
                :class="['node-icon', getBucketIconClass(data)]"
              />
              <span class="node-name">{{ node.label }}</span>
              <div class="node-info">
                <span v-if="data.size !== undefined" class="file-size">
                  {{ formatSize(data.size) }}
                </span>
                <span v-if="data.lastModified" class="modified-time">
                  {{ formatDate(data.lastModified) }}
                </span>
              </div>
            </div>
          </template>
        </el-tree>
      </template>
    </div>

    <!-- 选中项统计 -->
    <div v-if="selectedItems.length > 0" class="selection-summary">
      <el-card>
        <template #header>
          <div class="summary-header">
            <span>已选择 {{ selectedItems.length }} 项</span>
            <el-button @click="clearSelection" size="small" type="danger" plain>
              清空选择
            </el-button>
          </div>
        </template>
        <div class="selected-items">
          <el-tag
            v-for="item in selectedItems"
            :key="item.key || item.path"
            closable
            @close="removeSelectedItem(item)"
            class="selected-item"
          >
            <Icon 
              :icon="item.type === 'directory' || item.type === 'bucket' ? 'mdi:folder' : 'mdi:file'" 
              class="tag-icon"
            />
            {{ item.name }}
          </el-tag>
        </div>
      </el-card>
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
      selectedPaths: []
    })
  }
})

const emit = defineEmits(['update:modelValue', 'change'])

// 响应式数据
const storages = ref([])
const loading = ref(false)
const treeData = ref([])
const selectedItems = ref([])
const nasTreeRef = ref(null)
const obsTreeRef = ref(null)

const form = ref({
  selectedStorageId: props.modelValue.storageId || ''
})

// 树组件配置
const treeProps = {
  children: 'children',
  label: 'name',
  isLeaf: 'isLeaf'
}

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

// 方法
const fetchStorages = async () => {
  try {
    console.log('开始获取存储列表...')
    const response = await axios.get('/api/storages')
    console.log('存储列表响应:', response.data)
    if (response.data.status === 'success') {
      storages.value = response.data.storages || []
      console.log('存储列表已更新:', storages.value)
    } else {
      console.error('获取存储列表失败:', response.data.message)
      ElMessage.error('获取存储列表失败')
    }
  } catch (error) {
    console.error('获取存储列表错误:', error)
    ElMessage.error('获取存储列表失败')
  }
}

const handleStorageChange = async (storageId) => {
  if (!storageId) return
  
  // 清空之前的选择
  selectedItems.value = []
  treeData.value = []
  
  const storage = storages.value.find(s => s.id === storageId)
  if (!storage) return

  // 更新父组件数据
  updateModelValue()
  
  // 加载根目录
  await loadRootDirectory(storage)
  
  // 重置树的选中状态
  updateTreeCheckedState()
}

const loadRootDirectory = async (storage) => {
  loading.value = true
  try {
    if (storage.type === 'nas') {
      await loadNasRoot()
    } else if (storage.type === 's3') {
      await loadObsRoot()
    }
  } catch (error) {
    ElMessage.error('加载目录失败')
  } finally {
    loading.value = false
  }
}

const loadNasRoot = async () => {
  try {
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
      treeData.value = files.map(file => ({
        name: file.name,
        path: file.path,
        type: file.type,
        size: file.size,
        modified_time: file.modified_time,
        isLeaf: file.type !== 'directory'
      }))
    } else {
      ElMessage.error(response.data.message || '获取文件列表失败')
    }
  } catch (error) {
    ElMessage.error('获取文件列表失败')
  }
}

const loadObsRoot = async () => {
  try {
    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/buckets`)
    
    if (response.data.status === 'success') {
      const buckets = response.data.data.buckets || []
      treeData.value = buckets.map(bucket => ({
        name: bucket.name,
        key: bucket.name,
        type: 'bucket',
        creationDate: bucket.creationDate,
        isLeaf: false
      }))
    } else {
      ElMessage.error(response.data.message || '获取存储桶列表失败')
    }
  } catch (error) {
    ElMessage.error('获取存储桶列表失败')
  }
}

// 懒加载NAS节点
const loadNasNode = async (node, resolve) => {
  if (!node.data || node.data.type !== 'directory') {
    resolve([])
    return
  }

  try {
    const response = await axios.get(`/api/storages/${selectedStorage.value.id}/files`, {
      params: {
        node_id: selectedStorage.value.node_id,
        path: node.data.path,
        page: 1,
        page_size: 1000
      }
    })
    
    if (response.data.status === 'success') {
      const files = response.data.data.objects || []
      const children = files.map(file => ({
        name: file.name,
        path: file.path,
        type: file.type,
        size: file.size,
        modified_time: file.modified_time,
        isLeaf: file.type !== 'directory'
      }))
      resolve(children)
    } else {
      resolve([])
      ElMessage.error(response.data.message || '获取文件列表失败')
    }
  } catch (error) {
    resolve([])
    ElMessage.error('获取文件列表失败')
  }
}

// 懒加载OBS节点
const loadObsNode = async (node, resolve) => {
  if (!node.data) {
    resolve([])
    return
  }

  // 如果是存储桶，加载对象列表
  if (node.data.type === 'bucket') {
    try {
      const response = await axios.get(`/api/storages/${selectedStorage.value.id}/objects`, {
        params: {
          node_id: selectedStorage.value.node_id,
          bucket: node.data.name,
          prefix: '',
          page: 1,
          page_size: 1000
        }
      })
      
      if (response.data.status === 'success') {
        const objects = response.data.data.objects || []
        const children = objects.map(obj => ({
          name: obj.name,
          key: obj.key || `${node.data.name}/${obj.name}`,
          type: obj.type,
          size: obj.size,
          lastModified: obj.lastModified,
          bucket: node.data.name,
          isLeaf: obj.type !== 'directory'
        }))
        resolve(children)
      } else {
        resolve([])
        ElMessage.error(response.data.message || '获取对象列表失败')
      }
    } catch (error) {
      resolve([])
      ElMessage.error('获取对象列表失败')
    }
  } else if (node.data.type === 'directory') {
    // 如果是目录，加载子对象
    try {
      const prefix = node.data.key.replace(node.data.bucket + '/', '') + '/'
      const response = await axios.get(`/api/storages/${selectedStorage.value.id}/objects`, {
        params: {
          node_id: selectedStorage.value.node_id,
          bucket: node.data.bucket,
          prefix: prefix,
          page: 1,
          page_size: 1000
        }
      })
      
      if (response.data.status === 'success') {
        const objects = response.data.data.objects || []
        const children = objects.map(obj => ({
          name: obj.name,
          key: obj.key,
          type: obj.type,
          size: obj.size,
          lastModified: obj.lastModified,
          bucket: node.data.bucket,
          isLeaf: obj.type !== 'directory'
        }))
        resolve(children)
      } else {
        resolve([])
      }
    } catch (error) {
      resolve([])
    }
  } else {
    resolve([])
  }
}

const updateTreeCheckedState = () => {
  const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
  if (!treeRef) return

  // 获取所有选中的节点路径
  const checkedKeys = selectedItems.value.map(item => item.key || item.path)
  
  // 更新树的选中状态
  treeRef.setCheckedKeys(checkedKeys)
}

const handleCheckChange = (data, checked) => {
  const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
  if (!treeRef) return

  if (checked) {
    // 如果是目录，添加目录本身和所有子项
    if (data.type === 'directory' || data.type === 'bucket') {
      // 获取所有子节点
      const getAllChildren = (node) => {
        const children = []
        if (node.childNodes) {
          node.childNodes.forEach(child => {
            children.push(child.data)
            children.push(...getAllChildren(child))
          })
        }
        return children
      }

      const node = treeRef.getNode(data.key || data.path)
      if (node) {
        const allChildren = getAllChildren(node)
        
        // 添加目录本身
        if (!selectedItems.value.find(item => (item.key || item.path) === (data.key || data.path))) {
          selectedItems.value.push(data)
        }
        
        // 添加所有子项
        allChildren.forEach(child => {
          if (!selectedItems.value.find(item => (item.key || item.path) === (child.key || child.path))) {
            selectedItems.value.push(child)
          }
        })
      }
    } else {
      // 如果是文件，只添加文件本身
      if (!selectedItems.value.find(item => (item.key || item.path) === (data.key || data.path))) {
        selectedItems.value.push(data)
      }
    }
  } else {
    // 取消选择时，只移除当前节点，不影响其他已选择的项目
    selectedItems.value = selectedItems.value.filter(
      item => (item.key || item.path) !== (data.key || data.path)
    )
  }
  
  updateModelValue()
}

// 监听树的选中状态变化，同步到 selectedItems
const handleCheck = (data, checkedInfo) => {
  // 获取所有选中的节点
  const checkedNodes = checkedInfo.checkedNodes || []
  
  // 更新 selectedItems，只包含完全选中的节点
  selectedItems.value = checkedNodes
  
  updateModelValue()
}

const removeSelectedItem = (item) => {
  selectedItems.value = selectedItems.value.filter(
    selected => (selected.key || selected.path) !== (item.key || item.path)
  )
  
  // 更新树的选中状态
  updateTreeCheckedState()
  updateModelValue()
}

const clearSelection = () => {
  selectedItems.value = []
  updateTreeCheckedState()
  updateModelValue()
}

const refreshTree = async () => {
  if (selectedStorage.value) {
    await loadRootDirectory(selectedStorage.value)
  }
}

const expandAll = async () => {
  console.log('expandAll 方法被调用')
  const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
  console.log('treeRef:', treeRef)
  console.log('selectedStorage:', selectedStorage.value)
  
  if (treeRef) {
    console.log('treeRef.root:', treeRef.root)
    console.log('treeRef.root.childNodes:', treeRef.root?.childNodes)
    
    // 获取所有节点并展开，同时触发懒加载
    const expandAllNodes = async (nodes) => {
      console.log('展开节点数量:', nodes.length)
      for (const node of nodes) {
        console.log('处理节点:', node)
        
        // 如果节点是目录且未加载过子节点，先触发懒加载
        if (node.data && (node.data.type === 'directory' || node.data.type === 'bucket')) {
          if (!node.childNodes || node.childNodes.length === 0) {
            console.log('触发懒加载获取子节点:', node.data)
            try {
              // 触发懒加载
              await new Promise((resolve) => {
                if (selectedStorage.value.type === 'nas') {
                  loadNasNode(node, resolve)
                } else {
                  loadObsNode(node, resolve)
                }
              })
            } catch (error) {
              console.error('懒加载失败:', error)
            }
          }
        }
        
        // 展开当前节点
        if (node.expanded !== undefined) {
          node.expanded = true
          console.log('设置节点展开状态为 true')
        }
        
        // 递归展开子节点
        if (node.childNodes && node.childNodes.length > 0) {
          await expandAllNodes(node.childNodes)
        }
      }
    }
    
    // 从根节点开始展开
    if (treeRef.root && treeRef.root.childNodes) {
      await expandAllNodes(treeRef.root.childNodes)
    } else {
      console.log('没有找到根节点或子节点')
    }
  } else {
    console.log('treeRef 不存在')
  }
}

const collapseAll = () => {
  console.log('collapseAll 方法被调用')
  const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
  console.log('treeRef:', treeRef)
  
  if (treeRef) {
    console.log('treeRef.root:', treeRef.root)
    console.log('treeRef.root.childNodes:', treeRef.root?.childNodes)
    
    // 获取所有节点并收起
    const collapseAllNodes = (nodes) => {
      console.log('收起节点数量:', nodes.length)
      nodes.forEach(node => {
        console.log('处理节点:', node)
        // 收起当前节点
        if (node.expanded !== undefined) {
          node.expanded = false
          console.log('设置节点展开状态为 false')
        }
        // 递归收起子节点
        if (node.childNodes && node.childNodes.length > 0) {
          collapseAllNodes(node.childNodes)
        }
      })
    }
    
    // 从根节点开始收起
    if (treeRef.root && treeRef.root.childNodes) {
      collapseAllNodes(treeRef.root.childNodes)
    } else {
      console.log('没有找到根节点或子节点')
    }
  } else {
    console.log('treeRef 不存在')
  }
}

const updateModelValue = () => {
  const value = {
    storageId: form.value.selectedStorageId,
    storageName: selectedStorage.value?.name || '',
    storageType: selectedStorage.value?.type || '',
    selectedPaths: selectedItems.value.map(item => ({
      name: item.name,
      path: item.path || item.key,
      type: item.type,
      size: item.size,
      bucket: item.bucket
    }))
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

const getBucketIcon = (data) => {
  if (data.type === 'bucket') return 'mdi:bucket'
  if (data.type === 'directory') return 'mdi:folder'
  return 'mdi:file'
}

const getBucketIconClass = (data) => {
  if (data.type === 'bucket') return 'bucket-icon'
  if (data.type === 'directory') return 'folder-icon'
  return 'file-icon'
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
  if (newValue.storageId !== form.value.selectedStorageId) {
    form.value.selectedStorageId = newValue.storageId
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
.source-selector {
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

.directory-tree {
  border: 1px solid var(--el-border-color);
  border-radius: 6px;
  overflow: hidden;
}

.tree-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--el-color-primary-light-9);
  border-bottom: 1px solid var(--el-border-color);
}

.tree-header h4 {
  margin: 0;
  color: var(--el-text-color-primary);
  font-size: 16px;
}

.tree-actions {
  display: flex;
  gap: 8px;
}

.file-tree {
  max-height: 400px;
  overflow-y: auto;
  padding: 10px;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 4px 0;
}

.node-icon {
  font-size: 16px;
  flex-shrink: 0;
}

.folder-icon {
  color: #f7ba2a;
}

.file-icon {
  color: #67c23a;
}

.bucket-icon {
  color: #409eff;
}

.node-name {
  flex: 1;
  color: var(--el-text-color-primary);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.node-info {
  display: flex;
  gap: 12px;
  font-size: 12px;
  color: var(--el-text-color-secondary);
}

.selection-summary {
  margin-top: 30px;
}

.summary-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selected-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.tag-icon {
  font-size: 14px;
}

:deep(.el-tree-node__content) {
  height: auto;
  padding: 6px 0;
}

:deep(.el-tree-node__content:hover) {
  background-color: var(--el-color-primary-light-9);
}

:deep(.el-tree-node__expand-icon) {
  padding: 6px;
}

:deep(.el-checkbox) {
  margin-right: 8px;
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