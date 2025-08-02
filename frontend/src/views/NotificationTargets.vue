<template>
  <div class="notification-targets-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-left">
        <h1>通知对象</h1>
        <p class="page-description">管理告警接收人和分组，配置通知时间和联系方式</p>
      </div>
      <div class="header-right">
        <el-button type="primary" @click="openCreateDialog">
          <el-icon><Plus /></el-icon>
          创建对象
        </el-button>
        <el-button @click="refreshData">
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
    </div>

    <!-- 过滤器 -->
    <el-card class="filter-card" shadow="never">
      <div class="filter-container">
        <div class="filter-left">
          <el-select v-model="filters.target_type" placeholder="对象类型" style="width: 140px" @change="handleFilterChange">
            <el-option label="全部类型" value="" />
            <el-option label="用户" value="user" />
            <el-option label="组" value="group" />
            <el-option label="角色" value="role" />
            <el-option label="外部联系人" value="external" />
          </el-select>
          
          <el-select v-model="filters.enabled" placeholder="启用状态" style="width: 120px" @change="handleFilterChange">
            <el-option label="全部状态" value="" />
            <el-option label="已启用" value="true" />
            <el-option label="已禁用" value="false" />
          </el-select>
        </div>
        
        <div class="filter-right">
          <el-input
            v-model="filters.search"
            placeholder="搜索对象名称"
            style="width: 260px"
            @input="handleFilterChange"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
      </div>
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" shadow="never">
      <el-table
        v-loading="loading"
        :data="targets"
        style="width: 100%"
        empty-text="暂无通知对象"
      >
        <el-table-column prop="name" label="对象名称" min-width="180">
          <template #default="{ row }">
            <div class="target-name">
              <el-icon class="target-icon" :color="getTargetTypeColor(row.target_type)">
                <component :is="getTargetTypeIcon(row.target_type)" />
              </el-icon>
              <span>{{ row.name }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="target_type" label="类型" width="100">
          <template #default="{ row }">
            <el-tag :type="getTargetTypeTagType(row.target_type)" size="small">
              {{ getTargetTypeLabel(row.target_type) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        
        <el-table-column label="配置信息" min-width="220">
          <template #default="{ row }">
            <div class="config-info">
              <template v-if="row.target_type === 'user'">
                <el-tag size="small" v-for="userId in (row.target_config.user_ids || [])" :key="userId">
                  用户: {{ userId }}
                </el-tag>
              </template>
              <template v-else-if="row.target_type === 'group'">
                <el-tag size="small" type="success">
                  组: {{ row.target_config.group_id }}
                </el-tag>
              </template>
              <template v-else-if="row.target_type === 'role'">
                <el-tag size="small" type="warning" v-for="role in (row.target_config.roles || [])" :key="role">
                  {{ role }}
                </el-tag>
              </template>
              <template v-else-if="row.target_type === 'external'">
                <div class="external-info">
                  <div v-if="row.target_config.emails?.length">
                    <el-icon><Message /></el-icon>
                    {{ row.target_config.emails.length }} 个邮箱
                  </div>
                  <div v-if="row.target_config.phones?.length">
                    <el-icon><Phone /></el-icon>
                    {{ row.target_config.phones.length }} 个手机号
                  </div>
                </div>
              </template>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="通知时间" width="150">
          <template #default="{ row }">
            <div v-if="row.notification_schedule && row.notification_schedule.working_hours">
              <div class="schedule-info">
                <el-icon><Clock /></el-icon>
                {{ row.notification_schedule.working_hours.start }} - {{ row.notification_schedule.working_hours.end }}
              </div>
              <div class="schedule-days">
                工作日: {{ formatWorkdays(row.notification_schedule.working_hours.weekdays) }}
              </div>
            </div>
            <span v-else class="no-schedule">24小时</span>
          </template>
        </el-table-column>
        
        <el-table-column prop="enabled" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.enabled"
              @change="handleStatusChange(row)"
              :loading="row.updating"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="editTarget(row)">
              <el-icon><Edit /></el-icon>
              编辑
            </el-button>
            <el-button link type="danger" @click="deleteTarget(row)">
              <el-icon><Delete /></el-icon>
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'create' ? '创建通知对象' : '编辑通知对象'"
      width="800px"
      @close="resetForm"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="left"
      >
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="对象名称" prop="name">
              <el-input v-model="form.name" placeholder="请输入对象名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="对象类型" prop="target_type">
              <el-select v-model="form.target_type" placeholder="选择对象类型" @change="handleTargetTypeChange">
                <el-option label="用户" value="user" />
                <el-option label="组" value="group" />
                <el-option label="角色" value="role" />
                <el-option label="外部联系人" value="external" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" placeholder="请输入对象描述" />
        </el-form-item>

        <!-- 对象配置 -->
        <el-form-item label="配置信息" prop="target_config">
          <div class="config-container">
            <!-- 用户配置 -->
            <div v-if="form.target_type === 'user'" class="config-form">
              <el-form-item label="选择用户" prop="target_config.user_ids" label-width="100px">
                <el-select
                  v-model="form.target_config.user_ids"
                  multiple
                  placeholder="选择用户"
                  style="width: 100%"
                  filterable
                >
                  <el-option
                    v-for="user in availableUsers"
                    :key="user.id"
                    :label="user.username"
                    :value="user.id"
                  />
                </el-select>
              </el-form-item>
            </div>

            <!-- 组配置 -->
            <div v-else-if="form.target_type === 'group'" class="config-form">
              <el-form-item label="组ID" prop="target_config.group_id" label-width="100px">
                <el-input v-model="form.target_config.group_id" placeholder="请输入组ID" />
              </el-form-item>
              <el-form-item label="包含成员" label-width="100px">
                <el-switch v-model="form.target_config.include_members" />
                <span style="margin-left: 8px; color: var(--el-text-color-regular);">
                  是否包含组内所有成员
                </span>
              </el-form-item>
            </div>

            <!-- 角色配置 -->
            <div v-else-if="form.target_type === 'role'" class="config-form">
              <el-form-item label="选择角色" prop="target_config.roles" label-width="100px">
                <el-select
                  v-model="form.target_config.roles"
                  multiple
                  placeholder="选择角色"
                  style="width: 100%"
                >
                  <el-option label="管理员" value="admin" />
                  <el-option label="操作员" value="operator" />
                  <el-option label="查看者" value="viewer" />
                  <el-option label="开发者" value="developer" />
                </el-select>
              </el-form-item>
            </div>

            <!-- 外部联系人配置 -->
            <div v-else-if="form.target_type === 'external'" class="config-form">
              <el-form-item label="邮箱地址" label-width="100px">
                <el-input
                  v-model="newEmail"
                  placeholder="请输入邮箱地址"
                  @keyup.enter="addEmail"
                >
                  <template #append>
                    <el-button @click="addEmail">添加</el-button>
                  </template>
                </el-input>
                <div class="tag-list" v-if="form.target_config.emails?.length">
                  <el-tag
                    v-for="(email, index) in form.target_config.emails"
                    :key="email"
                    closable
                    @close="removeEmail(index)"
                    style="margin: 4px 4px 0 0"
                  >
                    {{ email }}
                  </el-tag>
                </div>
              </el-form-item>

              <el-form-item label="手机号码" label-width="100px">
                <el-input
                  v-model="newPhone"
                  placeholder="请输入手机号码"
                  @keyup.enter="addPhone"
                >
                  <template #append>
                    <el-button @click="addPhone">添加</el-button>
                  </template>
                </el-input>
                <div class="tag-list" v-if="form.target_config.phones?.length">
                  <el-tag
                    v-for="(phone, index) in form.target_config.phones"
                    :key="phone"
                    closable
                    @close="removePhone(index)"
                    style="margin: 4px 4px 0 0"
                  >
                    {{ phone }}
                  </el-tag>
                </div>
              </el-form-item>
            </div>
          </div>
        </el-form-item>

        <!-- 通知时间配置 -->
        <el-form-item label="通知时间">
          <div class="schedule-container">
            <el-checkbox v-model="hasSchedule" @change="handleScheduleChange">
              启用通知时间限制
            </el-checkbox>
            
            <div v-if="hasSchedule" class="schedule-form">
              <el-row :gutter="20">
                <el-col :span="8">
                  <el-form-item label="时区" label-width="60px">
                    <el-select v-model="form.notification_schedule.timezone" placeholder="选择时区">
                      <el-option label="北京时间" value="Asia/Shanghai" />
                      <el-option label="UTC时间" value="UTC" />
                      <el-option label="东京时间" value="Asia/Tokyo" />
                      <el-option label="纽约时间" value="America/New_York" />
                    </el-select>
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="开始时间" label-width="80px">
                    <el-time-picker
                      v-model="startTime"
                      format="HH:mm"
                      value-format="HH:mm"
                      placeholder="选择时间"
                    />
                  </el-form-item>
                </el-col>
                <el-col :span="8">
                  <el-form-item label="结束时间" label-width="80px">
                    <el-time-picker
                      v-model="endTime"
                      format="HH:mm"
                      value-format="HH:mm"
                      placeholder="选择时间"
                    />
                  </el-form-item>
                </el-col>
              </el-row>
              
              <el-form-item label="工作日" label-width="60px">
                <el-checkbox-group v-model="workdays">
                  <el-checkbox :label="1">周一</el-checkbox>
                  <el-checkbox :label="2">周二</el-checkbox>
                  <el-checkbox :label="3">周三</el-checkbox>
                  <el-checkbox :label="4">周四</el-checkbox>
                  <el-checkbox :label="5">周五</el-checkbox>
                  <el-checkbox :label="6">周六</el-checkbox>
                  <el-checkbox :label="7">周日</el-checkbox>
                </el-checkbox-group>
              </el-form-item>
            </div>
          </div>
        </el-form-item>

        <el-form-item label="启用状态">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>

      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitLoading">
            {{ dialogType === 'create' ? '创建' : '更新' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Refresh, Search, Edit, Delete, User, UserFilled, Avatar, Message, Phone, Clock } from '@element-plus/icons-vue'
import request from '@/utils/request'

// 响应式数据
const loading = ref(false)
const targets = ref([])
const dialogVisible = ref(false)
const dialogType = ref('create')
const submitLoading = ref(false)
const formRef = ref()
const availableUsers = ref([])

// 表单辅助数据
const newEmail = ref('')
const newPhone = ref('')
const hasSchedule = ref(false)
const startTime = ref('09:00')
const endTime = ref('18:00')
const workdays = ref([1, 2, 3, 4, 5])

// 过滤器
const filters = reactive({
  target_type: '',
  enabled: '',
  search: ''
})

// 表单数据
const form = reactive({
  name: '',
  description: '',
  target_type: '',
  enabled: true,
  target_config: {},
  notification_schedule: {
    timezone: 'Asia/Shanghai',
    working_hours: {
      start: '09:00',
      end: '18:00',
      weekdays: [1, 2, 3, 4, 5]
    }
  }
})

// 表单验证规则
const formRules = {
  name: [
    { required: true, message: '请输入对象名称', trigger: 'blur' }
  ],
  target_type: [
    { required: true, message: '请选择对象类型', trigger: 'change' }
  ],
  'target_config.user_ids': [
    { required: true, message: '请选择用户', trigger: 'change' }
  ],
  'target_config.group_id': [
    { required: true, message: '请输入组ID', trigger: 'blur' }
  ],
  'target_config.roles': [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// 页面加载时获取数据
onMounted(() => {
  fetchTargets()
  fetchUsers()
})

// 监听时间和工作日变化
watch([startTime, endTime, workdays], () => {
  if (hasSchedule.value) {
    form.notification_schedule.working_hours.start = startTime.value
    form.notification_schedule.working_hours.end = endTime.value
    form.notification_schedule.working_hours.weekdays = [...workdays.value]
  }
})

// 获取通知对象列表
const fetchTargets = async () => {
  loading.value = true
  try {
    const params = {}
    if (filters.target_type) params.target_type = filters.target_type
    if (filters.enabled !== '') params.enabled = filters.enabled === 'true'
    if (filters.search) params.search = filters.search

    const response = await request.get('/api/alerts/notification-targets', { params })
    targets.value = response.data || []
  } catch (error) {
    ElMessage.error('获取通知对象列表失败')
  } finally {
    loading.value = false
  }
}

// 获取可用用户列表
const fetchUsers = async () => {
  try {
    const response = await request.get('/api/users')
    availableUsers.value = response.data || []
  } catch (error) {
    console.error('获取用户列表失败:', error)
  }
}

// 过滤条件改变
const handleFilterChange = () => {
  fetchTargets()
}

// 刷新数据
const refreshData = () => {
  fetchTargets()
  fetchUsers()
}

// 打开创建对话框
const openCreateDialog = () => {
  dialogType.value = 'create'
  resetForm()
  dialogVisible.value = true
}

// 编辑对象
const editTarget = (row) => {
  dialogType.value = 'edit'
  Object.assign(form, {
    ...row,
    target_config: { ...row.target_config },
    notification_schedule: row.notification_schedule ? { ...row.notification_schedule } : {
      timezone: 'Asia/Shanghai',
      working_hours: {
        start: '09:00',
        end: '18:00',
        weekdays: [1, 2, 3, 4, 5]
      }
    }
  })
  
  // 设置时间和工作日
  if (row.notification_schedule?.working_hours) {
    hasSchedule.value = true
    startTime.value = row.notification_schedule.working_hours.start || '09:00'
    endTime.value = row.notification_schedule.working_hours.end || '18:00'
    workdays.value = row.notification_schedule.working_hours.weekdays || [1, 2, 3, 4, 5]
  } else {
    hasSchedule.value = false
  }
  
  dialogVisible.value = true
}

// 重置表单
const resetForm = () => {
  Object.assign(form, {
    name: '',
    description: '',
    target_type: '',
    enabled: true,
    target_config: {},
    notification_schedule: {
      timezone: 'Asia/Shanghai',
      working_hours: {
        start: '09:00',
        end: '18:00',
        weekdays: [1, 2, 3, 4, 5]
      }
    }
  })
  
  newEmail.value = ''
  newPhone.value = ''
  hasSchedule.value = false
  startTime.value = '09:00'
  endTime.value = '18:00'
  workdays.value = [1, 2, 3, 4, 5]
  
  nextTick(() => {
    formRef.value?.clearValidate()
  })
}

// 对象类型改变
const handleTargetTypeChange = (type) => {
  form.target_config = {}
  if (type === 'user') {
    form.target_config = { user_ids: [] }
  } else if (type === 'group') {
    form.target_config = { group_id: '', include_members: true }
  } else if (type === 'role') {
    form.target_config = { roles: [] }
  } else if (type === 'external') {
    form.target_config = { emails: [], phones: [] }
  }
}

// 通知时间配置改变
const handleScheduleChange = (enabled) => {
  if (!enabled) {
    form.notification_schedule = null
  } else {
    form.notification_schedule = {
      timezone: 'Asia/Shanghai',
      working_hours: {
        start: startTime.value,
        end: endTime.value,
        weekdays: [...workdays.value]
      }
    }
  }
}

// 添加邮箱
const addEmail = () => {
  if (!newEmail.value.trim()) return
  
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(newEmail.value)) {
    ElMessage.error('请输入有效的邮箱地址')
    return
  }
  
  if (!form.target_config.emails) {
    form.target_config.emails = []
  }
  
  if (form.target_config.emails.includes(newEmail.value)) {
    ElMessage.error('邮箱地址已存在')
    return
  }
  
  form.target_config.emails.push(newEmail.value)
  newEmail.value = ''
}

// 移除邮箱
const removeEmail = (index) => {
  form.target_config.emails.splice(index, 1)
}

// 添加手机号
const addPhone = () => {
  if (!newPhone.value.trim()) return
  
  const phoneRegex = /^1[3-9]\d{9}$/
  if (!phoneRegex.test(newPhone.value)) {
    ElMessage.error('请输入有效的手机号码')
    return
  }
  
  if (!form.target_config.phones) {
    form.target_config.phones = []
  }
  
  if (form.target_config.phones.includes(newPhone.value)) {
    ElMessage.error('手机号码已存在')
    return
  }
  
  form.target_config.phones.push(newPhone.value)
  newPhone.value = ''
}

// 移除手机号
const removePhone = (index) => {
  form.target_config.phones.splice(index, 1)
}

// 提交表单
const submitForm = async () => {
  try {
    await formRef.value.validate()
    submitLoading.value = true

    const data = { ...form }
    
    // 处理通知时间配置
    if (hasSchedule.value) {
      data.notification_schedule = {
        timezone: form.notification_schedule.timezone,
        working_hours: {
          start: startTime.value,
          end: endTime.value,
          weekdays: [...workdays.value]
        }
      }
    } else {
      data.notification_schedule = null
    }
    
    if (dialogType.value === 'create') {
      await request.post('/api/alerts/notification-targets', data)
      ElMessage.success('通知对象创建成功')
    } else {
      await request.put(`/api/alerts/notification-targets/${form.id}`, data)
      ElMessage.success('通知对象更新成功')
    }

    dialogVisible.value = false
    fetchTargets()
  } catch (error) {
    if (error.errors) {
      ElMessage.error('表单验证失败，请检查输入')
    } else {
      ElMessage.error(dialogType.value === 'create' ? '创建失败' : '更新失败')
    }
  } finally {
    submitLoading.value = false
  }
}

// 状态切换
const handleStatusChange = async (row) => {
  row.updating = true
  try {
    await request.put(`/api/alerts/notification-targets/${row.id}`, {
      enabled: row.enabled
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    row.enabled = !row.enabled // 恢复原状态
    ElMessage.error('状态更新失败')
  } finally {
    row.updating = false
  }
}

// 删除对象
const deleteTarget = async (row) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除通知对象「${row.name}」吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    await request.delete(`/api/alerts/notification-targets/${row.id}`)
    ElMessage.success('删除成功')
    fetchTargets()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 辅助函数
const getTargetTypeLabel = (type) => {
  const labels = {
    user: '用户',
    group: '组',
    role: '角色',
    external: '外部'
  }
  return labels[type] || type
}

const getTargetTypeTagType = (type) => {
  const types = {
    user: '',
    group: 'success',
    role: 'warning',
    external: 'info'
  }
  return types[type] || ''
}

const getTargetTypeIcon = (type) => {
  const icons = {
    user: User,
    group: UserFilled,
    role: Avatar,
    external: Message
  }
  return icons[type] || User
}

const getTargetTypeColor = (type) => {
  const colors = {
    user: '#409EFF',
    group: '#67C23A',
    role: '#E6A23C',
    external: '#909399'
  }
  return colors[type] || '#409EFF'
}

const formatWorkdays = (weekdays) => {
  if (!weekdays || !weekdays.length) return '无'
  const dayNames = ['', '一', '二', '三', '四', '五', '六', '日']
  return weekdays.map(day => dayNames[day]).join('、')
}

const formatTime = (timeStr) => {
  if (!timeStr) return '-'
  return new Date(timeStr).toLocaleString('zh-CN')
}
</script>

<style scoped>
.notification-targets-page {
  padding: 0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 20px;
  padding: 0 4px;
}

.header-left h1 {
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.page-description {
  margin: 0;
  color: var(--el-text-color-regular);
  font-size: 14px;
}

.header-right {
  display: flex;
  gap: 12px;
}

.filter-card {
  margin-bottom: 20px;
}

.filter-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-left {
  display: flex;
  gap: 16px;
}

.table-card {
  margin-bottom: 20px;
}

.target-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.target-icon {
  font-size: 16px;
}

.config-info {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.external-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: var(--el-text-color-regular);
}

.external-info div {
  display: flex;
  align-items: center;
  gap: 4px;
}

.schedule-info {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
}

.schedule-days {
  font-size: 11px;
  color: var(--el-text-color-regular);
  margin-top: 2px;
}

.no-schedule {
  color: var(--el-text-color-regular);
  font-size: 12px;
}

.config-container {
  width: 100%;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 16px;
  background-color: var(--el-bg-color-page);
}

.config-form {
  width: 100%;
}

.schedule-container {
  width: 100%;
  border: 1px solid var(--el-border-color-light);
  border-radius: 4px;
  padding: 16px;
  background-color: var(--el-bg-color-page);
}

.schedule-form {
  margin-top: 16px;
}

.tag-list {
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

:deep(.el-form-item) {
  margin-bottom: 18px;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-table) {
  font-size: 14px;
}

:deep(.el-table .cell) {
  padding: 8px 12px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
</style>