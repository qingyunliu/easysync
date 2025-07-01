<template>
  <el-menu
    :default-active="activeMenu"
    class="sidebar-menu"
    background-color="#304156"
    text-color="#bfcbd9"
    active-text-color="#409EFF"
    router
  >
    <el-menu-item index="/">
      <el-icon><HomeFilled /></el-icon>
      <span>首页</span>
    </el-menu-item>
    
    <el-menu-item index="/storages">
      <el-icon><Folder /></el-icon>
      <span>存储管理</span>
    </el-menu-item>
    
    <el-menu-item index="/tasks">
      <el-icon><List /></el-icon>
      <span>任务管理</span>
    </el-menu-item>
    
    <el-menu-item index="/clients">
      <el-icon><Monitor /></el-icon>
      <span>客户端管理</span>
    </el-menu-item>
    
    <el-menu-item index="/nodes">
      <el-icon><Connection /></el-icon>
      <span>节点管理</span>
    </el-menu-item>
    
    <el-menu-item index="/notifications">
      <el-icon><Bell /></el-icon>
      <span>通知中心</span>
    </el-menu-item>
    
    <el-menu-item index="/settings">
      <el-icon><Setting /></el-icon>
      <span>系统设置</span>
    </el-menu-item>
  </el-menu>
</template>

<script setup>
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import {
  HomeFilled,
  Folder,
  List,
  Monitor,
  Connection,
  Bell,
  Setting
} from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = ref(route.path)

watch(() => route.path, (newPath) => {
  activeMenu.value = newPath
})
</script>

<style scoped>
.sidebar-menu {
  height: 100%;
  border-right: none;
}

.sidebar-menu .el-menu-item {
  display: flex;
  align-items: center;
}

.sidebar-menu .el-menu-item .el-icon {
  margin-right: 8px;
}
</style> 