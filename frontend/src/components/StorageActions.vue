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
                :loading="storage.testing"
                :disabled="storage.status === 'error'"
              >
                <Icon icon="mdi:connection" />&nbsp;测试连接
              </el-button>
            </el-dropdown-item>
            <el-dropdown-item @click="handleGetInfo">
              <el-button 
                type="text" 
                :loading="storage.fetching"
                :disabled="storage.status === 'error'"
              >
                <Icon icon="mdi:information" />&nbsp;获取信息
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

// 测试连接
const handleTestConnection = async () => {
  try {
    props.storage.testing = true
    const response = await axios.post(`/api/storages/${props.storage.id}/test-connection`)
    if (response.data.status === 'success') {
      ElMessage.success('连接测试成功')
    }
  } catch (error) {
    ElMessage.error('连接测试失败')
  } finally {
    props.storage.testing = false
  }
}


// 获取存储信息
const handleGetInfo = async () => {
  try {
    props.storage.fetching = true
    const response = await axios.get(`/api/storages/${props.storage.id}/info`)
    // 通过事件总线或其他方式更新父组件的存储统计信息
    window.dispatchEvent(new CustomEvent('update-storage-stats', { 
      detail: response.data.data 
    }))
    ElMessage.success('获取信息成功')
  } catch (error) {
    ElMessage.error('获取信息失败')
  } finally {
    props.storage.fetching = false
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

:deep(.el-button--text) {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 8px 16px;
  white-space: nowrap;
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