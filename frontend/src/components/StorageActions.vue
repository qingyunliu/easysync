<template>
  <div class="storage-actions">
    <el-button-group>
      <el-button 
        type="primary" 
        size="small" 
        @click="handleEdit"
      >
        <Icon icon="mdi:pencil" />&nbsp;编辑
      </el-button>
      <el-button 
        type="danger" 
        size="small" 
        @click="handleDelete"
      >
        <Icon icon="mdi:delete" />&nbsp;删除
      </el-button>
      <el-dropdown trigger="click">
        <el-button type="primary" size="small">
          更多<Icon icon="mdi:chevron-down" class="el-icon--right" />
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleTestConnection">
              <el-button 
                type="text" 
                :loading="storage.testingRealtime"
                :disabled="storage.status === 'error'"
              >
                <Icon icon="mdi:flash" />&nbsp;测试连接
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item @click="handleGetInfo">
              <el-button 
                type="text" 
                :loading="storage.fetchingRealtime"
                :disabled="storage.status === 'error'"
              >
                <Icon icon="mdi:flash-circle" />&nbsp;获取信息
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item v-if="storage.type === 'nas'" @click="handleBrowseFiles">
              <el-button 
                type="text" 
                :loading="storage.browsing"
                :disabled="storage.status === 'error'"
              >
                <Icon icon="mdi:folder-open" />&nbsp;浏览文件
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item v-if="storage.type === 's3'" @click="handleBrowseBuckets">
              <el-button 
                type="text" 
                :loading="storage.browsing"
                :disabled="storage.status === 'error'"
              >
                <Icon icon="mdi:bucket" />&nbsp;浏览存储桶
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item v-if="storage.type === 's3'" @click="handleBrowseBucketObjects">
              <el-button 
                type="text" 
                :loading="storage.browsing"
                :disabled="storage.status === 'error'"
              >
                <Icon icon="mdi:files" />&nbsp;浏览存储对象
              </el-button>
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </el-button-group>
  </div>
</template>

<script setup>
import { ElMessage, ElMessageBox } from 'element-plus'
import { Icon } from '@iconify/vue'
import axios from 'axios'

const props = defineProps({
  storage: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['refresh'])

// 编辑存储
const handleEdit = () => {
  // 创建一个新的事件，包含完整的存储数据
  const event = new CustomEvent('edit-storage', {
    detail: {
      ...props.storage,
      // 确保所有必要的字段都被包含
      id: props.storage.id,
      name: props.storage.name,
      type: props.storage.type,
      config: props.storage.config || {}
    }
  })
  window.dispatchEvent(event)
}

// 删除存储
const handleDelete = async () => {
  try {
    await ElMessageBox.confirm('确定要删除该存储吗？', '提示', {
      type: 'warning'
    })
    await axios.delete(`/api/storages/${props.storage.id}`)
    ElMessage.success('删除成功')
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 实时测试连接
const handleTestConnection = async () => {
  try {
    // 检查是否有可用的测试节点
    const nodesResponse = await axios.get('/api/nodes')
    const availableNodes = (nodesResponse.data.data || []).filter(
      node => node.status === 'online' && node.agent_status === 'running'
    )
    
    if (availableNodes.length === 0) {
      ElMessage.error('没有可用的测试节点，请确保有节点在线且Agent已启动')
      return
    }
    
    // 使用第一个可用节点进行测试
    const testNode = availableNodes[0]
    
    props.storage.testingRealtime = true
    
    const response = await axios.post(`/api/storages/${props.storage.id}/test-connection`, {
      node_id: testNode.id
    })
    
    if (response.data.status === 'success') {
      const result = response.data.data
      ElMessage.success(`实时连接测试成功！响应时间: ${(result.response_time || 0).toFixed(2)}ms`)
    } else if (response.data.status === 'timeout') {
      ElMessage.warning('连接测试超时，请检查网络或存储配置')
    } else {
      ElMessage.error(response.data.message || '实时连接测试失败')
    }
  } catch (error) {
    ElMessage.error('实时连接测试失败')
  } finally {
    props.storage.testingRealtime = false
  }
}

// 实时获取信息
const handleGetInfo = async () => {
  try {
    // 检查是否有可用的节点
    let targetNodeId = props.storage.node_id
    
    if (!targetNodeId) {
      const nodesResponse = await axios.get('/api/nodes')
      const availableNodes = (nodesResponse.data.data || []).filter(
        node => node.status === 'online' && node.agent_status === 'running'
      )
      
      if (availableNodes.length === 0) {
        ElMessage.error('没有可用的节点，请确保有节点在线且Agent已启动')
        return
      }
      
      targetNodeId = availableNodes[0].id
    }
    
    props.storage.fetchingRealtime = true
    
    const response = await axios.get(`/api/storages/${props.storage.id}/stats`, {
      params: { node_id: targetNodeId }
    })
    
    if (response.data.status === 'success') {
      const result = response.data.data
      
      // 触发事件更新存储统计信息
      window.dispatchEvent(new CustomEvent('update-storage-stats', { 
        detail: result 
      }))
      
      ElMessage.success(`实时获取信息成功！执行时间: ${(response.data.execution_time || 0).toFixed(2)}s`)
    } else if (response.data.status === 'timeout') {
      ElMessage.warning('获取信息超时，请检查网络或存储配置')
    } else {
      ElMessage.error(response.data.message || '实时获取信息失败')
    }
  } catch (error) {
    ElMessage.error('实时获取信息失败')
  } finally {
    props.storage.fetchingRealtime = false
  }
}

// 浏览对象存储文件(OBS/S3)
const handleBrowseBucketObjects = async () => { 
  try {
    let targetNodeId = props.storage.node_id
    let bucket = props.storage.config.bucket
    
    if (!targetNodeId) {
      const nodesResponse = await axios.get('/api/nodes')
      const availableNodes = (nodesResponse.data.data || []).filter(
        node => node.status === 'online' && node.agent_status === 'running'
      )
      
      if (availableNodes.length === 0) {
        ElMessage.error('没有可用的节点，请确保有节点在线且Agent已启动')
        return
      }
      
      targetNodeId = availableNodes[0].id
    }
    
    props.storage.browsing = true
    
    const response = await axios.get(`/api/storages/${props.storage.id}/objects`, {
      params: { 
        node_id: targetNodeId,
        bucket: bucket,
        prefix: '',
        page: 1,
        page_size: 50
      }
    })
    
    if (response.data.status === 'success') {
      const result = response.data.data
      
      // 触发事件显示文件浏览器
      window.dispatchEvent(new CustomEvent('show-file-browser', { 
        detail: {
          storage: props.storage,
          files: result.files || result.objects || [],
          total: result.total || 0
        }
      }))
      
      ElMessage.success('对象存储列表获取成功')
    } else {
      ElMessage.error(response.data.message || '获取对象存储列表失败')
    }
  } catch (error) {
    ElMessage.error('获取对象存储列表失败')
  } finally {
    props.storage.browsing = false
  }
}

// 浏览文件（NAS）
const handleBrowseFiles = async () => {
  try {
    let targetNodeId = props.storage.node_id
    
    if (!targetNodeId) {
      const nodesResponse = await axios.get('/api/nodes')
      const availableNodes = (nodesResponse.data.data || []).filter(
        node => node.status === 'online' && node.agent_status === 'running'
      )
      
      if (availableNodes.length === 0) {
        ElMessage.error('没有可用的节点，请确保有节点在线且Agent已启动')
        return
      }
      
      targetNodeId = availableNodes[0].id
    }
    
    props.storage.browsing = true
    
    const response = await axios.get(`/api/storages/${props.storage.id}/files`, {
      params: { 
        node_id: targetNodeId,
        path: '',
        page: 1,
        page_size: 50
      }
    })
    
    if (response.data.status === 'success') {
      const result = response.data.data
      
      // 触发事件显示文件浏览器
      window.dispatchEvent(new CustomEvent('show-file-browser', { 
        detail: {
          storage: props.storage,
          files: result.files || result.objects || [],
          total: result.total || 0
        }
      }))
      
      ElMessage.success('文件列表获取成功')
    } else {
      ElMessage.error(response.data.message || '获取文件列表失败')
    }
  } catch (error) {
    ElMessage.error('获取文件列表失败')
  } finally {
    props.storage.browsing = false
  }
}

// 浏览存储桶（S3/OBS）
const handleBrowseBuckets = async () => {
  try {
    let targetNodeId = props.storage.node_id
    
    if (!targetNodeId) {
      const nodesResponse = await axios.get('/api/nodes')
      const availableNodes = (nodesResponse.data.data || []).filter(
        node => node.status === 'online' && node.agent_status === 'running'
      )
      
      if (availableNodes.length === 0) {
        ElMessage.error('没有可用的节点，请确保有节点在线且Agent已启动')
        return
      }
      
      targetNodeId = availableNodes[0].id
    }
    
    props.storage.browsing = true
    
    const response = await axios.get(`/api/storages/${props.storage.id}/buckets`, {
      params: { 
        node_id: targetNodeId,
        page: 1,
        page_size: 50
      }
    })
    
    if (response.data.status === 'success') {
      const result = response.data.data
      
      // 触发事件显示存储桶浏览器
      window.dispatchEvent(new CustomEvent('show-bucket-browser', { 
        detail: {
          storage: props.storage,
          buckets: result.buckets || [],
          total: result.total || 0
        }
      }))
      
      ElMessage.success('存储桶列表获取成功')
    } else {
      ElMessage.error(response.data.message || '获取存储桶列表失败')
    }
  } catch (error) {
    ElMessage.error('获取存储桶列表失败')
  } finally {
    props.storage.browsing = false
  }
}
</script>

<style scoped>
.storage-actions {
  display: flex;
  gap: 8px;
  flex-wrap: nowrap;
  justify-content: flex-start;
  min-width: 260px;
}

:deep(.el-button-group) {
  display: flex;
  gap: 0;
  flex-wrap: nowrap;
}

:deep(.el-button-group .el-button) {
  flex-shrink: 0;
}

:deep(.el-dropdown-menu__item) {
  padding: 0;
  line-height: normal;
}

:deep(.el-dropdown-menu) {
  text-align: left;
}

:deep(.el-dropdown-menu .el-dropdown-menu__item) {
  text-align: left;
}

:deep(.el-button--text) {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 16px;
  white-space: nowrap;
  justify-content: flex-start;
  text-align: left;
}

:deep(.el-button .iconify) {
  margin-right: 4px;
  font-size: 16px;
  flex-shrink: 0;
}

:deep(.el-button--text .iconify) {
  margin-right: 8px;
  font-size: 18px;
  flex-shrink: 0;
}

:deep(.el-dropdown) {
  margin-left: 0;
}
</style> 