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
    const response = await axios.get('/api/storages')
    if (response.data.status === 'success') {
      storages.value = response.data.storages || []
    } else {
      ElMessage.error('获取存储列表失败')
    }
  } catch (error) {
    console.error('获取存储列表错误:', error)
    ElMessage.error('获取存储列表失败')
  }
}

const handleStorageChange = async (storageId) => {
  if (!storageId) return
  
  // 在复制任务时，不清空已选择的项目
  const isCopyMode = props.modelValue && props.modelValue.selectedPaths && props.modelValue.selectedPaths.length > 0
  if (!isCopyMode) {
    selectedItems.value = []
  }
  treeData.value = []
  
  const storage = storages.value.find(s => s.id === storageId)
  if (!storage) return

  // 更新父组件数据 - 在复制任务时不触发change事件
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
  // 注意：这里不触发change事件，避免覆盖父组件的数据
  
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
  if (!treeRef) {
    console.warn('树组件未找到，无法更新选中状态')
    return false
  }

  // 获取所有选中的节点路径
  const checkedKeys = selectedItems.value.map(item => item.key || item.path)
  
  // 更新树的选中状态
  treeRef.setCheckedKeys(checkedKeys)
  return true
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
  const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
  
  if (treeRef) {
    
    // 获取所有节点并展开，同时触发懒加载
    const expandAllNodes = async (nodes) => {
      for (const node of nodes) {
        
        // 如果节点是目录且未加载过子节点，先触发懒加载
        if (node.data && (node.data.type === 'directory' || node.data.type === 'bucket')) {
          if (!node.childNodes || node.childNodes.length === 0) {
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
      ElMessage.error('没有找到根节点')
    }
  } else {
    ElMessage.error('树不存在')
  }
}

const collapseAll = () => {
  const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
  
  if (treeRef) {
    // 获取所有节点并收起
    const collapseAllNodes = (nodes) => {
      nodes.forEach(node => {
        // 收起当前节点
        if (node.expanded !== undefined) {
          node.expanded = false
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
      ElMessage.error('没有找到根节点')
    }
  } else {
    ElMessage.error('树不存在')
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

// 新增：设置初始状态的方法
const setInitialState = async (initialData) => {
  if (!initialData) {
    // 清理状态
    form.value.selectedStorageId = ''
    selectedItems.value = []
    treeData.value = []
    selectedStorage.value = null
    return
  }
  
  if (!initialData.storageId) return
  
  // 设置存储选择
  form.value.selectedStorageId = initialData.storageId
  
  // 等待存储列表加载完成
  if (storages.value.length === 0) {
    await fetchStorages()
  }
  
  // 触发存储变更，加载目录树
  await handleStorageChange(initialData.storageId)
  
  // 设置选中项
  if (initialData.selectedPaths && initialData.selectedPaths.length > 0) {
    selectedItems.value = initialData.selectedPaths.map(path => ({
      name: path.name || path.path.split('/').pop(),
      path: path.path,
      type: path.type || 'directory',
      size: path.size,
      bucket: path.bucket
    }))
    
    // 等待树组件加载完成后再设置选中状态
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 再次检查树组件是否可用
    const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
    if (!treeRef) {
      console.warn('树组件仍未加载完成，等待更长时间')
      await new Promise(resolve => setTimeout(resolve, 1000))
    }
    
    // 更新树的选中状态
    updateTreeCheckedState()
    
    // 确保树节点展开到选中项
    await expandToSelectedItems(initialData.selectedPaths)
    
    // 更新模型值 - 在初始化时不触发change事件
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
  }
}

// 展开到选中项的方法
const expandToSelectedItems = async (selectedPaths) => {
  if (!selectedPaths || selectedPaths.length === 0) return
  
  // 等待树组件完全加载
  await new Promise(resolve => setTimeout(resolve, 1000))
  
  const treeRef = selectedStorage.value?.type === 'nas' ? nasTreeRef.value : obsTreeRef.value
  if (!treeRef) {
    console.warn('树组件不可用，无法展开节点')
    return
  }
  
  // 对于每个选中的路径，展开到该路径
  for (const pathInfo of selectedPaths) {
    const path = pathInfo.path || pathInfo
    
    try {
      // 展开到该路径的父目录
      await expandToPath(treeRef, path)
    } catch (error) {
      console.error('展开路径失败:', path, error)
    }
  }
}

// 展开到指定路径的方法
const expandToPath = async (treeRef, targetPath) => {
  if (!treeRef || !targetPath) return
  
  // 获取路径的各个部分
  const pathParts = targetPath.split('/').filter(part => part)
  
  // 根据存储类型确定使用的key
  const isObs = selectedStorage.value?.type === 's3'
  const nodeKey = isObs ? 'key' : 'path'
  
  // 逐级展开
  for (let i = 0; i < pathParts.length; i++) {
    const currentPath = pathParts.slice(0, i + 1).join('/')
    
    // 等待一下，确保树组件响应
    await new Promise(resolve => setTimeout(resolve, 100))
    
    // 尝试展开当前路径
    try {
      // 使用Element Plus树组件的正确API
      // 根据存储类型确定使用的key
      const isObs = selectedStorage.value?.type === 's3'
      const nodeKey = isObs ? 'key' : 'path'
      
      // 查找对应的节点
      const node = treeRef.getNode(currentPath)
      if (node) {
        if (node.expand) {
          node.expand()
        }
      } else {
        const allNodes = treeRef.store.nodesMap
        if (allNodes) {
          const foundNode = Object.values(allNodes).find(n => 
            n.data && (n.data.path === currentPath || n.data.key === currentPath)
          )
          if (foundNode) {
            if (foundNode.expand) {
              foundNode.expand()
            }
          }
        }
        
        // 对于懒加载的树，可能需要先加载父节点
        if (i > 0) {
          const parentPath = pathParts.slice(0, i).join('/')
          const parentNode = treeRef.getNode(parentPath)
          if (parentNode && parentNode.expand) {
            parentNode.expand()
            // 等待子节点加载
            await new Promise(resolve => setTimeout(resolve, 300))
          }
        }
      }
    } catch (error) {
      console.error('展开路径失败:', currentPath, error)
    }
  }
}

// 获取当前状态
const getCurrentState = () => {
  return {
    selectedItems: selectedItems.value,
    treeData: treeData.value,
    selectedStorage: selectedStorage.value,
    form: form.value
  }
}

// 设置状态
const setState = async (state) => {
  if (state) {
    selectedItems.value = state.selectedItems || []
    selectedStorage.value = state.selectedStorage || null
    if (state.form) {
      form.value.selectedStorageId = state.form.selectedStorageId || ''
    }
    
    // 恢复树数据，避免重新加载
    if (state.treeData && state.treeData.length > 0) {
      treeData.value = state.treeData
    } else if (state.selectedStorage) {
      // 只有在没有缓存数据时才重新加载
      treeData.value = []
      await handleStorageChange(state.selectedStorage.id)
    } else {
      treeData.value = []
    }
    
    // 延迟更新树状态
    setTimeout(async () => {
      let retryCount = 0
      const maxRetries = 10
      
      const tryUpdateTree = () => {
        if (updateTreeCheckedState()) {
          // 延迟展开到选中项
          setTimeout(async () => {
            if (selectedItems.value.length > 0) {
              await expandToSelectedItems(selectedItems.value.map(item => ({ path: item.path })))
            }
          }, 1000)
        } else if (retryCount < maxRetries) {
          retryCount++
          setTimeout(tryUpdateTree, 300)
        }
      }
      
      tryUpdateTree()
    }, 1000)
  }
}

// 暴露方法给父组件
defineExpose({
  setInitialState,
  getCurrentState,
  setState
})

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

// 监听props变化 - 在复制任务时避免重置状态
watch(() => props.modelValue, (newValue, oldValue) => {
  // 如果是复制任务模式，避免重置已设置的状态
  if (newValue.storageId && newValue.storageId !== form.value.selectedStorageId) {
    form.value.selectedStorageId = newValue.storageId
    if (newValue.storageId) {
      handleStorageChange(newValue.storageId)
    }
  }
  
    // 在复制任务模式下，如果selectedPaths有内容，保持选中状态
  if (newValue.selectedPaths && newValue.selectedPaths.length > 0) {
    
    // 检查是否需要更新选中项
    const needsUpdate = selectedItems.value.length === 0 || 
                       selectedItems.value.length !== newValue.selectedPaths.length ||
                       !selectedItems.value.every((item, index) => 
                         (item.path || item.key) === newValue.selectedPaths[index].path
                       )
    
    if (needsUpdate) {
      selectedItems.value = newValue.selectedPaths.map(path => ({
        name: path.name || path.path.split('/').pop(),
        path: path.path,
        type: path.type || 'directory',
        size: path.size,
        bucket: path.bucket
      }))
      
      // 检查树数据是否为空，如果为空则重新加载
      if (treeData.value.length === 0 && newValue.storageId) {
        // 重新加载树数据
        handleStorageChange(newValue.storageId).then(() => {
        }).catch(error => {
          console.error('重新加载树数据失败:', error)
        })
      }
      
      // 延迟更新树状态，确保树组件已加载
      setTimeout(async () => {
        let retryCount = 0
        const maxRetries = 10 // 增加重试次数
        
        const tryUpdateTree = () => {
          if (updateTreeCheckedState()) {
            // 再次延迟展开到选中项
            setTimeout(async () => {
              await expandToSelectedItems(newValue.selectedPaths)
            }, 1000) // 增加延迟时间
          } else if (retryCount < maxRetries) {
            retryCount++
            setTimeout(tryUpdateTree, 300) // 增加重试间隔
          } else {
            console.warn('树组件加载超时，无法更新选中状态')
          }
        }
        
        tryUpdateTree()
      }, 1000) // 增加初始延迟时间
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