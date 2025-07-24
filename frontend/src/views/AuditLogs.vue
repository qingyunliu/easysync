<template>
  <div class="audit-logs-container">
    <el-card>
      <div class="header">
        <h2>登录审计日志</h2>
      </div>
      <el-table :data="logs" style="width: 100%">
        <el-table-column prop="user_id" label="用户ID" width="320" />
        <el-table-column prop="action" label="操作" width="180" />
        <el-table-column prop="details.login_time" label="审计时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.details.login_time) }}
          </template>
        </el-table-column>
        <el-table-column prop="details.ip" label="IP地址" width="140" />
        <el-table-column prop="details.user_agent" label="客户端" />
      </el-table>
      <el-pagination
        v-model:current-page="page"
        :page-size="perPage"
        :total="total"
        layout="prev, pager, next"
        @current-change="fetchLogs"
        class="pagination"
      />
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const logs = ref([])
const page = ref(1)
const perPage = ref(20)
const total = ref(0)

const fetchLogs = async () => {
  const res = await axios.get('/api/auth/audit-logs', {
    params: { page: page.value, per_page: perPage.value }
  })
  logs.value = res.data.logs
  total.value = res.data.total
}

const formatTime = (t) => t ? new Date(t).toLocaleString() : ''

onMounted(fetchLogs)
</script>

<style scoped>
.audit-logs-container {
  padding: 24px;
}
.header {
  margin-bottom: 16px;
}
.pagination {
  margin-top: 16px;
  text-align: right;
}
</style> 