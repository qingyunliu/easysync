<template>
  <div class="storage-actions">
    <el-button-group>
      <el-button type="primary" size="small" @click="handleEdit">
        <Icon icon="mdi:pencil" />&nbsp;{{ $t('storage.actions.edit') }}
      </el-button>
      <el-button type="danger" size="small" @click="handleDelete">
        <Icon icon="mdi:delete" />&nbsp;{{ $t('storage.actions.delete') }}
      </el-button>
      <el-dropdown trigger="click">
        <el-button type="primary" size="small">
          {{ $t('storage.actions.more') }}
          <Icon icon="mdi:chevron-down" class="el-icon--right" />
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="handleTestConnection">
              <el-button type="text" :loading="storage.testingRealtime" :disabled="storage.status === 'error'">
                <Icon icon="mdi:flash" />&nbsp;{{ $t('storage.actions.testConnection') }}
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item @click="handleGetInfo">
              <el-button type="text" :loading="storage.fetchingRealtime" :disabled="storage.status === 'error'">
                <Icon icon="mdi:flash-circle" />&nbsp;{{ $t('storage.actions.getInfo') }}
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item v-if="storage.type === 'nas'" @click="handleBrowseFiles">
              <el-button type="text" :loading="storage.browsing" :disabled="storage.status === 'error'">
                <Icon icon="mdi:folder-open" />&nbsp;{{ $t('storage.actions.browseFiles') }}
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item v-if="storage.type === 's3'" @click="handleBrowseBuckets">
              <el-button type="text" :loading="storage.browsing" :disabled="storage.status === 'error'">
                <Icon icon="mdi:bucket" />&nbsp;{{ $t('storage.actions.browseBuckets') }}
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item v-if="storage.type === 's3'" @click="handleBrowseBucketObjects">
              <el-button type="text" :loading="storage.browsing" :disabled="storage.status === 'error'">
                <Icon icon="mdi:files" />&nbsp;{{ $t('storage.actions.browseObjects') }}
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
import { useI18n } from 'vue-i18n'
import axios from 'axios'

const { t } = useI18n()

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
    await ElMessageBox.confirm(t('storage.deleteConfirm'), t('common.tip'), {
      type: 'warning'
    })
    await axios.delete(`/api/storages/${props.storage.id}`)
    ElMessage.success(t('storage.deleteSuccess'))
    emit('refresh')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(t('storage.deleteFailed'))
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
      ElMessage.error(t('storage.noAvailableTestNodes'))
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
      ElMessage.success(t('storage.testConnectionSuccess', { time: (result.response_time || 0).toFixed(2) }))
    } else if (response.data.status === 'timeout') {
      ElMessage.warning(t('storage.testConnectionTimeout'))
    } else {
      ElMessage.error(response.data.message || t('storage.testConnectionFailed'))
    }
  } catch (error) {
    ElMessage.error(t('storage.testConnectionFailed'))
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
        ElMessage.error(t('storage.noAvailableTestNodes'))
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

      ElMessage.success(t('storage.getInfoSuccess', { time: (response.data.execution_time || 0).toFixed(2) }))
    } else if (response.data.status === 'timeout') {
      ElMessage.warning(t('storage.getInfoTimeout'))
    } else {
      ElMessage.error(response.data.message || t('storage.getInfoFailed'))
    }
  } catch (error) {
    ElMessage.error(t('storage.getInfoFailed'))
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
        ElMessage.error(t('storage.noAvailableTestNodes'))
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

      ElMessage.success(t('storage.objectListGetSuccess'))
    } else {
      ElMessage.error(response.data.message || t('storage.objectListGetFailed'))
    }
  } catch (error) {
    ElMessage.error(t('storage.objectListGetFailed'))
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
        ElMessage.error(t('storage.noAvailableTestNodes'))
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

      ElMessage.success(t('storage.fileListGetSuccess'))
    } else {
      ElMessage.error(response.data.message || t('storage.fileListGetFailed'))
    }
  } catch (error) {
    ElMessage.error(t('storage.fileListGetFailed'))
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
        ElMessage.error(t('storage.noAvailableTestNodes'))
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

      ElMessage.success(t('storage.bucketListGetSuccess'))
    } else {
      ElMessage.error(response.data.message || t('storage.bucketListGetFailed'))
    }
  } catch (error) {
    ElMessage.error(t('storage.bucketListGetFailed'))
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