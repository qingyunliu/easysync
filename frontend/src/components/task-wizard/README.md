# 任务创建向导

## 概述

任务创建向导是一个分步骤的任务创建流程，帮助用户通过直观的界面创建复杂的同步任务。

## 组件结构

```
task-wizard/
├── TaskWizard.vue          # 主向导组件
├── SourceSelector.vue       # 源端选择器
├── TargetSelector.vue       # 目标端选择器
├── TaskParameters.vue       # 任务参数配置
├── TaskConfirmation.vue     # 任务确认
├── scenarios/              # 场景特定参数
│   ├── NasToNasOptions.vue
│   ├── NasToObsOptions.vue
│   ├── ObsToNasOptions.vue
│   └── ObsToObsOptions.vue
└── README.md              # 说明文档
```

## 使用流程

### 步骤 1: 选择源端

- 选择源端存储类型（NAS、OBS 等）
- 浏览并选择要同步的文件和目录
- 支持多选和树形结构浏览

### 步骤 2: 选择目标端

- 选择目标端存储
- 指定目标路径
- 支持新建文件夹
- 数据覆盖警告

### 步骤 3: 任务参数

- 基础信息配置（任务名称、描述、优先级）
- 同步选项（删除、压缩、校验等）
- 传输策略（重试次数、间隔等）
- 高级参数（缓冲区、超时等）
- 场景特定参数（根据源端和目标端类型）

### 步骤 4: 确认配置

- 展示所有配置信息
- 预估传输时间和大小
- 最终确认并创建任务

## 特性

### 智能参数配置

根据源端和目标端的存储类型，自动显示相关的配置选项：

- **NAS → NAS**: rsync 参数配置
- **NAS → OBS**: rclone 上传参数
- **OBS → NAS**: rclone 下载参数
- **OBS → OBS**: 对象存储间传输参数

### 数据安全

- 相同存储覆盖警告
- 路径验证
- 传输完整性校验

### 用户体验

- 分步骤引导
- 实时验证
- 进度指示
- 响应式设计

## API 集成

向导最终会调用以下 API 创建任务：

```javascript
POST /api/tasks
{
  name: "任务名称",
  description: "任务描述",
  type: "sync",
  priority: 2,
  source_type: "storage",
  source_storage_id: "存储ID",
  source_path: "源端路径",
  target_storage_id: "目标存储ID",
  target_path: "目标路径",
  options: {
    delete: false,
    compress: false,
    checksum: true,
    bandwidth_limit: 0,
    max_connections: 1,
    retry_options: {
      max_retries: 3,
      retry_interval: 30
    }
  }
}
```

## 组件使用示例

```vue
<template>
  <TaskWizard v-model:visible="wizardVisible" @created="handleTaskCreated" />
</template>

<script setup>
import TaskWizard from "@/components/task-wizard/TaskWizard.vue";

const wizardVisible = ref(false);

const handleTaskCreated = (task) => {
  console.log("任务创建成功:", task);
  // 处理任务创建成功后的逻辑
};
</script>
```

## 扩展指南

### 添加新的存储类型

1. 在 `SourceSelector.vue` 和 `TargetSelector.vue` 中添加新的存储类型选项
2. 在 `TaskParameters.vue` 中添加对应的场景参数组件
3. 创建新的场景参数组件（如 `LocalToObsOptions.vue`）

### 添加新的参数类型

1. 在 `TaskParameters.vue` 中添加新的参数卡片
2. 在 `TaskConfirmation.vue` 中添加对应的展示逻辑
3. 更新 API 调用以包含新参数

## 注意事项

1. **存储状态检查**: 确保选择的存储状态为可用
2. **路径验证**: 目标路径会自动验证
3. **权限检查**: 确保有足够的权限访问源端和目标端
4. **网络连接**: 确保节点与存储之间的网络连接正常

## 故障排除

### 常见问题

1. **存储不可用**: 检查存储配置和连接状态
2. **路径访问失败**: 验证路径权限和网络连接
3. **参数验证失败**: 检查必填参数和参数格式
4. **任务创建失败**: 查看后端日志获取详细错误信息

### 调试模式

在开发环境中，可以启用调试模式查看详细的 API 调用和参数传递：

```javascript
// 在 TaskWizard.vue 中
const debugMode = process.env.NODE_ENV === "development";
```
