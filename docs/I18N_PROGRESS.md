# EasySync 国际化工程进度报告

## 项目概述

EasySync 数据同步管理平台的国际化工程，支持中文（zh-CN）和英文（en-US）两种语言。采用 vue-i18n 进行前端国际化，计划使用 Flask-Babel 进行后端国际化。

## 技术架构

### 前端国际化架构

```
frontend/src/i18n/
├── index.js              # 国际化配置和实例
├── locales/
│   ├── zh-CN.js         # 中文语言包
│   └── en-US.js         # 英文语言包
```

### 语言包结构

```javascript
{
  common: {
    // 通用文本：按钮、状态、分页、提示等
  },
  auth: {
    // 认证相关：登录、注册、密码重置
  },
  nav: {
    // 导航菜单：侧边栏、顶部菜单
  },
  dashboard: {
    // 仪表板：统计信息、图表、状态
  },
  storage: {
    // 存储管理：NAS、S3、文件浏览、操作
  },
  // 其他模块...
}
```

## 已完成工作 ✅

### 1. 国际化基础架构

- [x] **vue-i18n 配置** (`frontend/src/i18n/index.js`)

  - [x] 创建 i18n 实例
  - [x] 配置默认语言和回退语言
  - [x] 集成到 Vue 应用 (`frontend/src/main.js`)
  - [x] 语言检测和切换功能

- [x] **语言切换组件** (`frontend/src/components/LanguageSwitch.vue`)
  - [x] 下拉菜单式语言切换
  - [x] 动态语言切换功能
  - [x] Element Plus 语言同步

### 2. 语言包内容

#### 2.1 通用文本 (common)

- [x] **基础操作按钮**

  - [x] 确认、取消、保存、删除、编辑、添加
  - [x] 刷新、搜索、重置、导出、导入
  - [x] 上一步、下一步、完成、返回

- [x] **状态和状态描述**

  - [x] 在线/离线、运行中/已停止、成功/失败
  - [x] 启用/禁用、正常/异常、活跃/非活跃

- [x] **分页相关文本**

  - [x] 页码、每页条数、总数、跳转
  - [x] 上一页、下一页、首页、末页

- [x] **错误和提示消息**

  - [x] 操作成功/失败、加载中、无数据
  - [x] 确认删除、网络错误、权限不足

- [x] **问候语和时间**
  - [x] 早上好、下午好、晚上好
  - [x] 欢迎回来、再见

#### 2.2 认证相关文本 (auth)

- [x] **登录页面** (`frontend/src/views/Login.vue`)

  - [x] 页面标题和欢迎信息
  - [x] 表单字段标签和占位符
  - [x] 按钮文本（登录、注册、忘记密码）
  - [x] 验证规则消息
  - [x] 错误提示消息（用户名不存在、密码错误等）
  - [x] 成功提示消息

- [x] **注册页面** (`frontend/src/views/Register.vue`)

  - [x] 页面标题和说明
  - [x] 表单字段标签和占位符
  - [x] 按钮文本（注册、返回登录）
  - [x] 验证规则消息
  - [x] 错误和成功提示消息

- [x] **密码重置页面** (`frontend/src/views/ForgotPassword.vue`)
  - [x] 页面标题和说明
  - [x] 表单字段标签和占位符
  - [x] 按钮文本（发送重置邮件、返回登录）
  - [x] 验证规则消息
  - [x] 错误和成功提示消息

#### 2.3 导航菜单文本 (nav)

- [x] **主布局页面** (`frontend/src/views/Home.vue`)
  - [x] 侧边栏菜单项
  - [x] 菜单分组标题（控制台、资源管理、运维管理、监控告警、系统管理）
  - [x] 用户下拉菜单（个人中心、设置、退出登录）
  - [x] 问候语和欢迎消息
  - [x] 面包屑导航

#### 2.4 仪表板相关文本 (dashboard)

- [x] **仪表板页面** (`frontend/src/views/Dashboard.vue`)
  - [x] 页面标题和描述
  - [x] 系统状态卡片（节点状态、存储状态、任务状态）
  - [x] 资源统计（总节点数、总存储数、总任务数）
  - [x] 任务统计（运行中、已完成、失败）
  - [x] 通知管理（未读消息、系统通知）
  - [x] 表格列标题和状态标签
  - [x] 按钮和操作文本
  - [x] 空状态和加载状态提示

#### 2.5 存储管理相关文本 (storage)

- [x] **存储管理页面** (`frontend/src/views/Storages.vue`)

  - [x] **页面基础信息**

    - [x] 页面标题和描述
    - [x] 搜索框占位符
    - [x] 添加存储下拉菜单

  - [x] **NAS 存储部分**

    - [x] 表格列标题（名称、协议类型、服务器、共享目录、挂载状态、创建时间、绑定节点）
    - [x] 状态标签（已挂载/未挂载、已绑定/未绑定）
    - [x] 协议类型标签（NFS/CIFS）
    - [x] 空状态提示

  - [x] **OBS/S3 存储部分**

    - [x] 表格列标题（名称、提供商、访问密钥、端点、区域、创建时间、绑定节点）
    - [x] 提供商标签（AWS、Google Cloud、腾讯云、阿里云、华为云、MinIO、其他）
    - [x] 状态标签（已绑定/未绑定）
    - [x] 空状态提示

  - [x] **存储详情抽屉**

    - [x] 抽屉标题和加载状态
    - [x] 基本信息标签页
    - [x] 存储类型、协议、服务器、路径等详细信息
    - [x] 统计信息卡片（总大小、已用大小、文件数、对象数）
    - [x] 刷新按钮和加载提示

  - [x] **文件浏览功能**

    - [x] 面包屑导航
    - [x] 文件状态信息（文件数量、当前路径）
    - [x] 文件列表表格（名称、大小、修改时间、操作）
    - [x] 下载按钮
    - [x] 分页组件
    - [x] 空目录提示

  - [x] **存储桶和对象列表**

    - [x] 存储桶列表表格
    - [x] 对象列表表格
    - [x] 面包屑导航
    - [x] 对象状态信息
    - [x] 下载按钮
    - [x] 分页组件
    - [x] 空状态提示

  - [x] **存储编辑对话框**

    - [x] 对话框标题
    - [x] 表单字段标签和占位符
    - [x] 协议选择（NFS/CIFS）
    - [x] 协议版本选择（NFSv3、NFSv4.0、NFSv4.1、CIFSv2.0、CIFSv3.0）
    - [x] 提供商选择
    - [x] 高级选项折叠面板
    - [x] 测试节点选择
    - [x] 按钮文本（确认、取消、测试连接）

  - [x] **表单验证规则**

    - [x] 存储名称验证
    - [x] 提供商选择验证
    - [x] Access Key 验证
    - [x] Secret Key 验证
    - [x] Endpoint 验证
    - [x] 区域验证
    - [x] 存储桶名称验证
    - [x] 服务器地址验证
    - [x] 共享目录路径验证
    - [x] 协议类型验证
    - [x] 读写权限验证
    - [x] 协议版本验证

  - [x] **操作反馈消息**

    - [x] 添加存储成功/失败
    - [x] 更新存储成功/失败
    - [x] 删除存储确认/成功/失败
    - [x] 测试连接成功/失败/超时
    - [x] 获取信息成功/失败/超时
    - [x] 文件列表获取成功/失败
    - [x] 对象列表获取成功/失败
    - [x] 存储桶列表获取成功/失败
    - [x] 上传成功/失败
    - [x] 下载成功/失败
    - [x] 统计信息获取/更新成功/失败

  - [x] **错误提示消息**

    - [x] 无可用测试节点
    - [x] 存储未绑定节点相关错误
    - [x] 节点离线或 Agent 未运行
    - [x] 网络连接错误
    - [x] 权限不足错误
    - [x] 文件不存在错误
    - [x] 存储配置错误

  - [x] **任务相关消息**
    - [x] 任务创建成功提示
    - [x] 任务执行状态提示
    - [x] 任务完成/失败提示

- [x] **StorageActions 组件** (`frontend/src/components/StorageActions.vue`)

  - [x] **按钮文本**

    - [x] 编辑、删除、更多
    - [x] 测试连接、获取信息
    - [x] 浏览文件、浏览存储桶、浏览对象

  - [x] **操作反馈消息**

    - [x] 删除确认对话框
    - [x] 删除成功/失败提示
    - [x] 测试连接成功/失败/超时提示
    - [x] 获取信息成功/失败/超时提示
    - [x] 文件列表获取成功/失败提示
    - [x] 对象列表获取成功/失败提示
    - [x] 存储桶列表获取成功/失败提示

  - [x] **错误提示消息**
    - [x] 无可用测试节点提示
    - [x] 节点状态检查错误提示

### 3. 国际化覆盖范围统计

#### 3.1 页面覆盖情况

- [x] 登录页面 (Login.vue) - 100%
- [x] 注册页面 (Register.vue) - 100%
- [x] 密码重置页面 (ForgotPassword.vue) - 100%
- [x] 主布局页面 (Home.vue) - 100%
- [x] 仪表板页面 (Dashboard.vue) - 100%
- [x] 存储管理页面 (Storages.vue) - 100%
- [ ] 任务管理页面 (Tasks.vue) - 0%
- [ ] 用户管理页面 (Users.vue) - 0%
- [ ] 监控告警页面 (Monitoring.vue) - 0%
- [ ] 系统设置页面 (Settings.vue) - 0%
- [ ] 404 页面 (NotFound.vue) - 0%

#### 3.2 组件覆盖情况

- [x] 语言切换组件 (LanguageSwitch.vue) - 100%
- [x] 存储操作组件 (StorageActions.vue) - 100%
- [ ] 任务向导组件 (task-wizard/) - 0%
- [ ] 其他业务组件 - 0%

#### 3.3 消息类型覆盖情况

- [x] **ElMessage 消息** - 100%

  - [x] 成功提示消息
  - [x] 错误提示消息
  - [x] 警告提示消息
  - [x] 信息提示消息

- [x] **ElMessageBox 消息** - 100%

  - [x] 确认对话框
  - [x] 警告对话框
  - [x] 信息对话框

- [x] **表单验证消息** - 100%

  - [x] 必填字段验证
  - [x] 格式验证
  - [x] 自定义验证

- [x] **页面状态消息** - 100%
  - [x] 加载状态
  - [x] 空状态
  - [x] 错误状态

## 待完成工作 📋

### 1. 前端页面国际化（继续）

#### 1.1 核心功能页面

- [x] **任务管理页面** (`frontend/src/views/Tasks.vue`)

  - [x] 页面标题和描述
  - [x] 任务列表表格
  - [x] 任务状态标签
  - [x] 任务操作按钮
  - [x] 任务详情对话框
  - [x] 任务创建向导
  - [x] 任务日志查看
  - [x] 任务统计信息
  - [x] 表单验证规则
  - [x] 操作反馈消息

- [ ] **用户管理页面** (`frontend/src/views/Users.vue`)

  - [ ] 页面标题和描述
  - [ ] 用户列表表格
  - [ ] 用户状态标签
  - [ ] 用户操作按钮
  - [ ] 用户编辑对话框
  - [ ] 角色权限管理
  - [ ] 用户统计信息
  - [ ] 表单验证规则
  - [ ] 操作反馈消息

- [ ] **监控告警页面** (`frontend/src/views/Monitoring.vue`)

  - [ ] 页面标题和描述
  - [ ] 监控仪表板
  - [ ] 告警列表
  - [ ] 告警规则管理
  - [ ] 监控图表
  - [ ] 告警配置
  - [ ] 通知设置
  - [ ] 操作反馈消息

- [ ] **系统设置页面** (`frontend/src/views/Settings.vue`)
  - [ ] 页面标题和描述
  - [ ] 系统配置表单
  - [ ] 安全设置
  - [ ] 邮件配置
  - [ ] 备份设置
  - [ ] 日志配置
  - [ ] 表单验证规则
  - [ ] 操作反馈消息

#### 1.2 辅助页面

- [ ] **404 页面** (`frontend/src/views/NotFound.vue`)
  - [ ] 页面标题和描述
  - [ ] 错误提示信息
  - [ ] 返回按钮

#### 1.3 业务组件

- [ ] **任务向导组件** (`frontend/src/components/task-wizard/`)

  - [ ] 步骤导航
  - [ ] 表单字段
  - [ ] 验证规则
  - [ ] 操作按钮
  - [ ] 进度提示

- [ ] **其他业务组件**
  - [ ] 文件上传组件
  - [ ] 图表组件
  - [ ] 表格组件
  - [ ] 表单组件

### 2. 后端国际化

#### 2.1 国际化工具配置

- [ ] 配置 Flask-Babel 或类似工具
- [ ] 设置语言检测机制
- [ ] 配置翻译文件结构
- [ ] 集成到 Flask 应用

#### 2.2 API 响应国际化

- [ ] **成功响应消息**

  - [ ] 创建成功
  - [ ] 更新成功
  - [ ] 删除成功
  - [ ] 操作完成

- [ ] **错误响应消息**

  - [ ] 验证错误
  - [ ] 权限错误
  - [ ] 资源不存在
  - [ ] 服务器错误
  - [ ] 网络错误

- [ ] **业务逻辑消息**
  - [ ] 任务状态变更
  - [ ] 存储连接状态
  - [ ] 节点状态变更
  - [ ] 系统通知

#### 2.3 日志输出国际化

- [ ] 系统日志消息
- [ ] 错误日志消息
- [ ] 调试日志消息
- [ ] 审计日志消息

#### 2.4 邮件模板国际化

- [ ] 用户注册邮件
- [ ] 密码重置邮件
- [ ] 任务完成通知
- [ ] 系统告警邮件
- [ ] 欢迎邮件

### 3. 代码注释和文档

#### 3.1 前端代码注释

- [ ] Vue 组件注释
- [ ] JavaScript 函数注释
- [ ] CSS 样式注释
- [ ] 配置文件注释

#### 3.2 后端代码注释

- [ ] Python 函数注释
- [ ] 类和方法注释
- [ ] API 接口注释
- [ ] 配置文件注释

#### 3.3 项目文档

- [ ] README 文档
- [ ] API 文档
- [ ] 部署文档
- [ ] 用户手册
- [ ] 开发者指南

### 4. 测试和优化

#### 4.1 功能测试

- [ ] 语言切换功能测试
- [ ] 翻译完整性测试
- [ ] 动态内容测试
- [ ] 错误处理测试

#### 4.2 用户体验测试

- [ ] 响应式布局测试
- [ ] 语言切换流畅性测试
- [ ] 文本长度适配测试
- [ ] 字体显示测试

#### 4.3 性能优化

- [ ] 语言包加载优化
- [ ] 翻译缓存优化
- [ ] 动态导入优化
- [ ] 内存使用优化

## 使用指南

### 前端国际化使用

#### 在模板中使用

```vue
<template>
  <!-- 基础文本 -->
  <h1>{{ $t("auth.welcomeBack") }}</h1>

  <!-- 带参数的文本 -->
  <p>{{ $t("storage.fileCount", { count: total }) }}</p>

  <!-- 按钮文本 -->
  <el-button>{{ $t("common.confirm") }}</el-button>

  <!-- 表单验证 -->
  <el-form-item :label="$t('auth.username')" prop="username">
    <el-input v-model="form.username" :placeholder="$t('auth.enterUsername')" />
  </el-form-item>
</template>
```

#### 在脚本中使用

```vue
<script setup>
import { useI18n } from "vue-i18n";

const { t } = useI18n();

// 基础文本
const message = t("auth.loginSuccess");

// 带参数的文本
const errorMessage = t("storage.testNodeOffline", { nodeName: "Node-001" });

// 在 ElMessage 中使用
ElMessage.success(t("storage.addStorageSuccess"));

// 在表单验证中使用
const rules = {
  username: [
    {
      required: true,
      message: t("auth.validation.usernameRequired"),
      trigger: "blur",
    },
  ],
};
</script>
```

#### 语言切换

```javascript
import { setLocale } from "@/i18n";

// 切换到英文
setLocale("en-US");

// 切换到中文
setLocale("zh-CN");
```

### 后端国际化使用（计划）

#### 在 Flask 中使用

```python
from flask_babel import gettext, ngettext

# 基础文本
message = gettext('User created successfully')

# 带参数的文本
message = gettext('User %(name)s created successfully', name=user.name)

# 复数形式
message = ngettext('%(count)d file', '%(count)d files', count)
```

## 最佳实践

### 1. 文本提取原则

- 所有用户可见的文本都应该国际化
- 使用有意义的键名，便于理解和维护
- 按功能模块组织翻译键
- 避免硬编码文本

### 2. 翻译质量保证

- 保持中英文翻译的一致性
- 注意文化差异和表达习惯
- 定期审查和更新翻译
- 建立翻译术语表

### 3. 技术实现建议

- 使用 TypeScript 类型检查翻译键
- 实现翻译键自动补全
- 建立翻译键命名规范
- 定期清理未使用的翻译键

### 4. 维护流程

- 新增功能时同步更新翻译
- 定期检查翻译完整性
- 建立翻译更新流程
- 版本控制翻译文件

## 注意事项

1. **文本提取**：确保所有硬编码的中文文本都被提取到语言包中
2. **一致性**：保持中英文翻译的一致性和准确性
3. **用户体验**：确保语言切换的流畅性和响应性
4. **维护性**：建立良好的国际化维护流程
5. **性能**：注意语言包大小和加载性能
6. **兼容性**：确保在不同浏览器和设备上的兼容性

## 贡献指南

1. **新增文本时**：同时更新中英文语言包
2. **使用有意义的键名**：便于理解和维护
3. **遵循现有的语言包结构**：保持组织的一致性
4. **测试语言切换功能**：确保新增内容正常工作
5. **更新文档**：及时更新相关文档和进度报告

## 国际化完成情况详细统计

### 存储管理模块国际化完成度：100% ✅

### 任务管理模块国际化完成度：100% ✅

#### 已完成的国际化内容：

**1. 页面基础元素**

- ✅ 页面标题和描述 (`storage.title`, `storage.description`)
- ✅ 搜索框占位符 (`storage.searchStorage`)
- ✅ 添加存储下拉菜单 (`storage.addStorage`, `storage.addNasStorage`, `storage.addObsStorage`)
- ✅ 存储类型标签 (`storage.nasDevices`, `storage.obsStorage`)

**2. 表格列标题和状态**

- ✅ NAS 表格列标题：名称、协议类型、服务器、共享目录、挂载状态、创建时间、绑定节点
- ✅ OBS 表格列标题：名称、提供商、访问密钥、端点、区域、创建时间、绑定节点
- ✅ 状态标签：已挂载/未挂载、已绑定/未绑定、在线/离线
- ✅ 协议类型标签：NFS/CIFS (`storage.protocols.nfs`, `storage.protocols.cifs`)

**3. 存储详情抽屉**

- ✅ 抽屉标题和加载状态 (`storage.storageDetails`, `storage.loadingStorageDetails`)
- ✅ 基本信息标签页 (`storage.basicInfo`)
- ✅ 统计信息卡片 (`storage.storageUsage`, `storage.statistics`)
- ✅ 文件浏览标签页 (`storage.fileBrowse`)
- ✅ 存储桶列表标签页 (`storage.buckets`)
- ✅ 对象列表标签页 (`storage.objectList`)

**4. 文件浏览功能**

- ✅ 面包屑导航 (`storage.rootDirectory`)
- ✅ 文件状态信息 (`storage.fileCount`, `storage.currentPathLabel`)
- ✅ 文件列表表格：名称、大小、修改时间、操作
- ✅ 下载按钮 (`storage.download`)
- ✅ 分页组件
- ✅ 空目录提示 (`storage.emptyDirectory`)

**5. 存储桶和对象列表**

- ✅ 存储桶列表表格
- ✅ 对象列表表格
- ✅ 对象状态信息 (`storage.objectCount`)
- ✅ 空状态提示 (`storage.selectBucketFirst`, `storage.selectBucketToBrowse`)

**6. 存储编辑对话框**

- ✅ 对话框标题 (`storage.addStorage`, `storage.editStorage`)
- ✅ 表单字段标签和占位符
- ✅ 协议选择：NFS/CIFS
- ✅ 协议版本选择：NFSv3、NFSv4.0、NFSv4.1、CIFSv2.0、CIFSv3.0
- ✅ 提供商选择：AWS、Google Cloud、腾讯云、阿里云、华为云、MinIO、其他
- ✅ 高级选项折叠面板 (`storage.advancedOptions`)
- ✅ 测试节点选择
- ✅ 按钮文本：确认、取消、测试连接

**7. 表单验证规则 (validation)**

- ✅ 存储名称验证 (`validation.enterStorageName`)
- ✅ 提供商选择验证 (`validation.selectProvider`)
- ✅ Access Key 验证 (`validation.enterAccessKey`)
- ✅ Secret Key 验证 (`validation.enterSecretKey`)
- ✅ Endpoint 验证 (`validation.enterEndpoint`)
- ✅ 区域验证 (`validation.enterRegion`)
- ✅ 存储桶名称验证 (`validation.enterBucketName`)
- ✅ 服务器地址验证 (`validation.enterServerAddress`)
- ✅ 共享目录路径验证 (`validation.enterSharedDirectoryPath`)
- ✅ 协议类型验证 (`validation.selectProtocolType`)
- ✅ 读写权限验证 (`validation.selectReadWritePermission`)
- ✅ 协议版本验证 (`validation.selectProtocolVersion`)

**8. 操作反馈消息**

- ✅ 添加存储成功/失败 (`addStorageSuccess`, `operationFailed`)
- ✅ 更新存储成功/失败 (`updateStorageSuccess`, `operationFailed`)
- ✅ 删除存储确认/成功/失败 (`deleteConfirm`, `deleteSuccess`, `deleteFailed`)
- ✅ 测试连接成功/失败/超时 (`testConnectionSuccess`, `testConnectionFailed`, `testConnectionTimeout`)
- ✅ 获取信息成功/失败/超时 (`getInfoSuccess`, `getInfoFailed`, `getInfoTimeout`)
- ✅ 文件列表获取成功/失败 (`fileListGetSuccess`, `fileListGetFailed`)
- ✅ 对象列表获取成功/失败 (`objectListGetSuccess`, `objectListGetFailed`)
- ✅ 存储桶列表获取成功/失败 (`bucketListGetSuccess`, `bucketListGetFailed`)
- ✅ 上传成功/失败 (`uploadSuccess`, `uploadFailed`)
- ✅ 下载成功/失败 (`downloadSuccess`, `downloadFailed`)
- ✅ 统计信息获取/更新成功/失败 (`getStatsFailed`, `statsUpdated`, `updateStatsFailed`)

**9. 错误提示消息**

- ✅ 无可用测试节点 (`noAvailableTestNodes`)
- ✅ 存储未绑定节点相关错误 (`noBoundNodeForDetails`, `noBoundNodeForStats`, `noBoundNodeForDownload`, `noBoundNodeForFileList`, `noBoundNodeForBucketList`, `noBoundNodeForObjectList`, `noBoundNodeForRefreshStats`)
- ✅ 节点离线或 Agent 未运行 (`boundNodeOffline`, `boundNodeAgentNotRunning`, `testNodeOffline`, `testNodeAgentNotRunning`)
- ✅ 网络连接错误 (`getStorageListFailed`, `getNodeListFailed`)
- ✅ 权限不足错误
- ✅ 文件不存在错误
- ✅ 存储配置错误

**10. 任务相关消息**

- ✅ 任务创建成功提示 (`statsTaskCreated`, `downloadTaskCreated`, `fileListTaskCreated`, `bucketListTaskCreated`, `objectListTaskCreated`, `connectionTestTaskCreated`)
- ✅ 任务执行状态提示 (`creatingConnectionTestTask`)
- ✅ 任务完成/失败提示

**11. StorageActions 组件**

- ✅ 按钮文本：编辑、删除、更多、测试连接、获取信息、浏览文件、浏览存储桶、浏览对象
- ✅ 操作反馈消息：删除确认、成功/失败提示
- ✅ 错误提示消息：无可用测试节点提示

**12. 空状态和提示信息**

- ✅ 无 NAS 存储设备 (`noNasStorages`)
- ✅ 无 S3 存储设备 (`noS3Storages`)
- ✅ 当前目录为空 (`emptyDirectory`)
- ✅ 无数据提示 (`none`)
- ✅ 当前路径标签 (`currentPath`)
- ✅ 存储桶标签 (`bucket`)

**13. 提供商和协议选项**

- ✅ 提供商选项：AWS、Google Cloud、腾讯云、阿里云、华为云、MinIO、其他
- ✅ 协议选项：NFS、CIFS
- ✅ 协议版本：NFSv3、NFSv4.0、NFSv4.1、CIFSv2.0、CIFSv3.0

**14. 统计信息标签**

- ✅ 总大小、已用大小、总文件数、总对象数
- ✅ 存储桶数量、对象数量、总存储量、最后修改时间
- ✅ 刷新按钮和加载提示

### 任务管理模块国际化完成度：100% ✅

#### 已完成的国际化内容：

**1. 页面基础元素**

- ✅ 页面标题和描述 (`tasks.title`, `tasks.description`)
- ✅ 创建任务按钮 (`tasks.createTask`)
- ✅ 复制任务标题 (`tasks.copyTask`)

**2. 统计面板**

- ✅ 总任务数 (`tasks.stats.totalTasks`)
- ✅ 运行中 (`tasks.stats.running`)
- ✅ 等待中 (`tasks.stats.pending`)
- ✅ 已完成 (`tasks.stats.completed`)
- ✅ 已失败 (`tasks.stats.failed`)
- ✅ 在线节点 (`tasks.stats.onlineNodes`)

**3. 工具栏**

- ✅ 搜索框占位符 (`tasks.searchPlaceholder`)
- ✅ 状态筛选 (`tasks.statusFilter`)
- ✅ 类型筛选 (`tasks.typeFilter`)
- ✅ 筛选选项 (`tasks.all`, `tasks.statuses.*`, `tasks.types.*`)
- ✅ 刷新按钮 (`tasks.refresh`, `tasks.pauseRefresh`, `tasks.enableRefresh`)

**4. 批量操作**

- ✅ 已选择任务数量 (`tasks.selectedTasks`)
- ✅ 批量操作按钮 (`tasks.batchCancel`, `tasks.batchRetry`, `tasks.batchDelete`)

**5. 表格列标题**

- ✅ 任务名称 (`tasks.taskName`)
- ✅ 任务描述 (`tasks.taskDescription`)
- ✅ 类型 (`tasks.type`)
- ✅ 状态 (`tasks.status`)
- ✅ 进度 (`tasks.progress`)
- ✅ 执行节点 (`tasks.executionNode`)
- ✅ 优先级 (`tasks.priority`)
- ✅ 创建时间 (`tasks.createTime`)
- ✅ 操作 (`tasks.actions`)
- ✅ 无描述提示 (`tasks.noDescription`)
- ✅ 未分配提示 (`tasks.unassigned`)

**6. 任务类型和状态**

- ✅ 任务类型文本 (`tasks.types.sync`, `tasks.types.copy`, `tasks.types.mountCheck`)
- ✅ 任务状态文本 (`tasks.statuses.*`)
- ✅ 优先级文本 (`tasks.priorities.*`)

**7. 操作按钮**

- ✅ 启动/暂停/恢复/取消/重试按钮 (`tasks.actions.*`)
- ✅ 更多操作下拉菜单 (`tasks.actions.more`)
- ✅ 查看日志/详情/复制任务/删除 (`tasks.actions.*`)

**8. 任务详情和日志**

- ✅ 任务详情标题 (`tasks.taskDetail`, `tasks.taskDetailTitle`)
- ✅ 任务日志标题 (`tasks.taskLogs`, `tasks.taskLogsTitle`)
- ✅ 日志级别筛选 (`tasks.logLevels.*`)
- ✅ 刷新间隔选项 (`tasks.refreshInterval`, `tasks.closeRefresh`, `tasks.seconds`, `tasks.minutes`)
- ✅ 自动刷新/手动刷新 (`tasks.autoRefresh`, `tasks.manualRefresh`)
- ✅ 清理日志按钮 (`tasks.refreshDuplicateLogs`, `tasks.refreshOldLogs`)

**9. 消息和验证**

- ✅ 操作成功/失败消息 (`tasks.messages.*`)
- ✅ 确认对话框消息 (`tasks.messages.confirm*`)
- ✅ 验证规则消息 (`tasks.validation.*`)

**10. 通用文本**

- ✅ 时间列标题 (`common.time`)
- ✅ 消息列标题 (`common.message`)

### 任务详情组件国际化完成度：100% ✅

#### 已完成的国际化内容：

**1. 基础信息**

- ✅ 基础信息标题 (`taskDetail.basicInfo`)
- ✅ 任务名称、类型、状态、进度、优先级、执行节点 (`taskDetail.taskName`, `taskDetail.type`, `taskDetail.status`, `taskDetail.progress`, `taskDetail.priority`, `taskDetail.executionNode`)
- ✅ 创建时间、开始时间、完成时间 (`taskDetail.createTime`, `taskDetail.startTime`, `taskDetail.completeTime`)
- ✅ 未分配、未开始、未完成状态 (`taskDetail.unassigned`, `taskDetail.notStarted`, `taskDetail.notCompleted`)

**2. 源端信息**

- ✅ 源端信息标题 (`taskDetail.sourceInfo`)
- ✅ 存储名称、存储类型、源端路径 (`taskDetail.storageName`, `taskDetail.storageType`, `taskDetail.sourcePath`)
- ✅ 客户端名称、IP 地址 (`taskDetail.clientName`, `taskDetail.ipAddress`)
- ✅ 无源端信息提示 (`taskDetail.noSourceInfo`)

**3. 目标端信息**

- ✅ 目标端信息标题 (`taskDetail.targetInfo`)
- ✅ 目标路径 (`taskDetail.targetPath`)
- ✅ 无目标端信息提示 (`taskDetail.noTargetInfo`)

**4. 同步选项**

- ✅ 同步选项标题 (`taskDetail.syncOptions`)
- ✅ 删除多余文件、校验和检查、压缩传输 (`taskDetail.deleteExtraFiles`, `taskDetail.checksumCheck`, `taskDetail.compressTransfer`)
- ✅ 带宽限制、最大连接数、重试次数 (`taskDetail.bandwidthLimit`, `taskDetail.maxConnections`, `taskDetail.retryCount`)
- ✅ 无限制、默认值、无同步选项提示 (`taskDetail.noLimit`, `taskDetail.default`, `taskDetail.noSyncOptions`)

**5. 传输统计**

- ✅ 传输统计标题 (`taskDetail.transferStatistics`)
- ✅ 已传输文件、总文件数、已传输大小、总大小 (`taskDetail.transferredFiles`, `taskDetail.totalFiles`, `taskDetail.transferredSize`, `taskDetail.totalSize`)
- ✅ 传输速度、预计剩余时间、完成进度 (`taskDetail.transferSpeed`, `taskDetail.estimatedTime`, `taskDetail.completionProgress`)

**6. 当前阶段和文件**

- ✅ 当前阶段、阶段、已处理文件 (`taskDetail.currentPhase`, `taskDetail.phase`, `taskDetail.processedFiles`)
- ✅ 当前传输文件、文件路径、文件大小、已传输 (`taskDetail.currentTransferFile`, `taskDetail.filePath`, `taskDetail.fileSize`, `taskDetail.transferred`)

**7. 任务统计和错误信息**

- ✅ 任务统计标题、已处理大小 (`taskDetail.taskStatistics`, `taskDetail.processedSize`)
- ✅ 错误信息标题 (`taskDetail.errorInfo`)
- ✅ 最后更新时间 (`taskDetail.lastUpdate`)

**8. 函数文本**

- ✅ 任务状态文本 (`tasks.statuses.*`)
- ✅ 任务类型文本 (`tasks.types.*`)
- ✅ 优先级文本 (`tasks.priorities.*`)
- ✅ 阶段文本 (`taskDetail.phases.*`)
- ✅ 节点名称 (`taskDetail.node`)
- ✅ 存储类型文本 (`taskDetail.storageTypes.*`)

### 任务创建向导组件国际化完成度：100% ✅

#### 已完成的国际化内容：

**1. 复制任务提示**

- ✅ 复制任务配置标题 (`taskWizard.copyTaskConfig`)
- ✅ 复制任务配置描述 (`taskWizard.copyingTaskConfig`)

**2. 步骤配置**

- ✅ 选择源端、选择目标端、任务参数、确认配置 (`taskWizard.steps.selectSource`, `taskWizard.steps.selectTarget`, `taskWizard.steps.configureParameters`, `taskWizard.steps.confirmConfig`)
- ✅ 步骤描述文本 (`taskWizard.steps.*Desc`)

**3. 步骤内容**

- ✅ 选择源端存储和文件标题 (`taskWizard.selectSourceStorageAndFiles`)
- ✅ 选择源端存储和文件描述 (`taskWizard.selectSourceStorageAndFilesDesc`)

**4. 按钮和进度**

- ✅ 上一步、下一步、重置按钮 (`taskWizard.previousStep`, `taskWizard.nextStep`, `taskWizard.reset`)
- ✅ 创建任务、创建副本按钮 (`taskWizard.createTask`, `taskWizard.createCopy`)
- ✅ 步骤进度显示 (`taskWizard.stepProgress`)

**5. 消息提示**

- ✅ 完善配置信息提示 (`taskWizard.messages.completeAllRequiredConfig`)
- ✅ 任务创建成功/失败提示 (`taskWizard.messages.taskCreatedSuccess`, `taskWizard.messages.createTaskFailed`)

### 语言包统计

**中文语言包 (zh-CN.js)**

- 通用文本 (common): 45+ 个键值对
- 认证相关 (auth): 35+ 个键值对
- 导航菜单 (nav): 25+ 个键值对
- 仪表板 (dashboard): 30+ 个键值对
- 存储管理 (storage): 120+ 个键值对
- 任务管理 (tasks): 80+ 个键值对
- 任务详情 (taskDetail): 60+ 个键值对
- 任务创建向导 (taskWizard): 30+ 个键值对
- 任务参数 (taskParameters): 35+ 个键值对
- 任务确认 (taskConfirmation): 25+ 个键值对
- 目标选择器 (targetSelector): 50+ 个键值对
- 源选择器 (sourceSelector): 30+ 个键值对
- OBS 到 OBS 选项 (obsToObsOptions): 25+ 个键值对
- OBS 到 NAS 选项 (obsToNasOptions): 25+ 个键值对
- NAS 到 OBS 选项 (nasToObsOptions): 25+ 个键值对
- NAS 到 NAS 选项 (nasToNasOptions): 20+ 个键值对
- 通知管理 (notifications): 55+ 个键值对
- 事件管理 (events): 70+ 个键值对
- 告警策略管理 (alertPolicies): 85+ 个键值对
- 系统监控 (monitoring): 45+ 个键值对
- 节点管理 (nodes): 150+ 个键值对
- 源端服务器管理 (clients): 150+ 个键值对
- **总计**: 1419+ 个翻译键值对

**英文语言包 (en-US.js)**

- 通用文本 (common): 45+ 个键值对
- 认证相关 (auth): 35+ 个键值对
- 导航菜单 (nav): 25+ 个键值对
- 仪表板 (dashboard): 30+ 个键值对
- 存储管理 (storage): 120+ 个键值对
- 任务管理 (tasks): 80+ 个键值对
- 任务详情 (taskDetail): 60+ 个键值对
- 任务创建向导 (taskWizard): 30+ 个键值对
- 任务参数 (taskParameters): 35+ 个键值对
- 任务确认 (taskConfirmation): 25+ 个键值对
- 目标选择器 (targetSelector): 50+ 个键值对
- 源选择器 (sourceSelector): 30+ 个键值对
- OBS 到 OBS 选项 (obsToObsOptions): 25+ 个键值对
- OBS 到 NAS 选项 (obsToNasOptions): 25+ 个键值对
- NAS 到 OBS 选项 (nasToObsOptions): 25+ 个键值对
- NAS 到 NAS 选项 (nasToNasOptions): 20+ 个键值对
- 通知管理 (notifications): 55+ 个键值对
- 事件管理 (events): 70+ 个键值对
- 告警策略管理 (alertPolicies): 105+ 个键值对
- 系统监控 (monitoring): 49+ 个键值对
- 个人信息 (profile): 35+ 个键值对
- 系统设置 (settings): 105+ 个键值对
- **总计**: 1269+ 个翻译键值对

### Notifications.vue 国际化完成度：100% ✅

**已完成内容：**

**1. 页面标题和描述**

- ✅ 页面标题 (`notifications.pageTitle`)
- ✅ 页面描述 (`notifications.pageDescription`)

**2. 操作按钮**

- ✅ 全部已读按钮 (`notifications.markAllAsRead`)
- ✅ 清空消息按钮 (`notifications.clearAllMessages`)
- ✅ 刷新按钮 (`notifications.refresh`)

**3. 统计信息面板**

- ✅ 总消息数 (`notifications.totalMessages`)
- ✅ 未读消息 (`notifications.unreadMessages`)
- ✅ 信息类型 (`notifications.infoType`)
- ✅ 警告/错误 (`notifications.warningError`)

**4. 过滤器**

- ✅ 消息级别占位符 (`notifications.messageLevel`)
- ✅ 阅读状态占位符 (`notifications.readStatus`)
- ✅ 消息类型占位符 (`notifications.messageType`)
- ✅ 搜索通知内容占位符 (`notifications.searchNotifications`)
- ✅ 过滤器选项：全部、信息、警告、错误、成功、未读、已读 (`notifications.all`, `notifications.info`, `notifications.warning`, `notifications.error`, `notifications.success`, `notifications.unread`, `notifications.read`)
- ✅ 消息类型过滤器选项：系统通知、任务通知、存储通知、用户通知 (`notifications.systemNotification`, `notifications.taskNotification`, `notifications.storageNotification`, `notifications.userNotification`)

**5. 空状态和按钮**

- ✅ 暂无通知消息 (`notifications.noNotifications`)
- ✅ 刷新页面按钮 (`notifications.refreshPage`)

**6. 下拉菜单项**

- ✅ 标为未读 (`notifications.markAsUnread`)
- ✅ 标为已读 (`notifications.markAsRead`)
- ✅ 删除 (`common.delete`)

**7. 详情弹窗**

- ✅ 通知详情标题 (`notifications.notificationDetails`)
- ✅ 创建时间标签 (`notifications.createdTime`)
- ✅ 阅读状态标签 (`notifications.readStatus`)
- ✅ 关闭按钮 (`common.close`)
- ✅ 标记已读按钮 (`notifications.markAsRead`)

**8. 消息提示**

- ✅ 标记已读成功/失败 (`notifications.messages.markedAsRead`, `notifications.messages.markAsReadFailed`)
- ✅ 批量标记已读确认/成功/失败 (`notifications.messages.confirmMarkAllAsRead`, `notifications.messages.markedMultipleAsRead`, `notifications.messages.markAllAsReadFailed`)
- ✅ 清空消息确认/成功/失败 (`notifications.messages.confirmClearAll`, `notifications.messages.clearedAllMessages`, `notifications.messages.clearAllFailed`)
- ✅ 删除通知确认/成功/失败 (`notifications.messages.confirmDelete`, `notifications.messages.notificationDeleted`, `notifications.messages.deleteFailed`)
- ✅ 标记未读成功/失败 (`notifications.messages.markedAsUnread`, `notifications.messages.markAsUnreadFailed`)
- ✅ 获取通知列表失败 (`notifications.messages.getNotificationsFailed`)

**9. 函数文本**

- ✅ 消息级别标签 (`notifications.levels.*`)
- ✅ 消息类型标签 (`notifications.types.*`)
- ✅ 时间格式 (`notifications.time.*`)

**10. 分页组件国际化**

- ✅ Element Plus locale 配置
- ✅ 动态语言切换支持

### Events.vue 国际化完成度：100% ✅

**已完成内容：**

**1. 页面标题和描述**

- ✅ 页面标题 (`events.pageTitle`)
- ✅ 页面描述 (`events.pageDescription`)

**2. 操作按钮**

- ✅ 刷新数据按钮 (`events.refreshData`)
- ✅ 导出数据按钮 (`events.exportData`)
- ✅ 清理旧事件按钮 (`events.cleanupEvents`)

**3. 统计信息面板**

- ✅ 总事件数 (`events.totalEvents`)
- ✅ 失败事件 (`events.failedEvents`)
- ✅ 告警数量 (`events.alertCount`)
- ✅ 今日事件 (`events.todayEvents`)

**4. 过滤器**

- ✅ 事件类型选择器 (`events.selectEventType`)
- ✅ 事件动作选择器 (`events.selectEventAction`)
- ✅ 事件结果选择器 (`events.selectEventResult`)
- ✅ 时间范围选择器 (`events.to`, `events.startTime`, `events.endTime`)
- ✅ 过滤器选项：全部类型、存储事件、客户端事件、代理事件、系统事件
- ✅ 事件动作选项：创建、更新、删除、连接、断开
- ✅ 事件结果选项：成功、失败、超时、错误、警告
- ✅ 重置筛选和应用筛选按钮

**5. 事件列表**

- ✅ 事件列表标题 (`events.eventList`)
- ✅ 总记录数显示 (`events.totalRecords`)
- ✅ 表格列标题：事件 ID、事件类型、事件动作、事件结果、事件消息、时间、操作
- ✅ 详情按钮 (`events.details`)

**6. 事件详情对话框**

- ✅ 事件详情标题 (`events.eventDetails`)
- ✅ 详细信息标签：事件 ID、事件类型、事件动作、事件结果、用户 ID、客户端 ID、节点 ID、创建时间、事件时间、事件消息
- ✅ 详细信息标题 (`events.detailedInfo`)

**7. 清理事件对话框**

- ✅ 清理旧事件标题 (`events.cleanupEvents`)
- ✅ 保留天数字段 (`events.retentionDays`, `events.enterRetentionDays`)
- ✅ 清理提示信息 (`events.cleanupTip`)
- ✅ 确认清理按钮 (`events.confirmCleanup`)
- ✅ 取消按钮 (`common.cancel`)

**8. 工具函数**

- ✅ 事件类型标签 (`events.storage`, `events.client`, `events.agent`, `events.system`)
- ✅ 事件动作标签 (`events.create`, `events.update`, `events.delete`, `events.connect`, `events.disconnect`, `events.testConnection`, `events.listBuckets`, `events.listObjects`, `events.listFiles`, `events.download`, `events.mountCheck`)
- ✅ 事件结果标签 (`events.success`, `events.failed`, `events.timeout`, `events.error`, `events.warning`)

**9. 消息提示**

- ✅ 导出成功/失败 (`events.messages.exportSuccess`, `events.messages.exportFailed`)
- ✅ 清理成功/失败 (`events.messages.cleanupSuccess`, `events.messages.cleanupFailed`)
- ✅ 获取事件列表失败 (`events.messages.getEventsFailed`)

### AlertPolicies.vue 国际化完成度：100% ✅

**已完成内容：**

**1. 页面标题和描述**

- ✅ 页面标题 (`alertPolicies.pageTitle`)
- ✅ 页面描述 (`alertPolicies.pageDescription`)
- ✅ 创建告警策略按钮 (`alertPolicies.createAlertPolicy`)
- ✅ 编辑告警策略标题 (`alertPolicies.editAlertPolicy`)

**2. 筛选栏**

- ✅ 策略类型选择器 (`alertPolicies.policyType`)
- ✅ 告警级别选择器 (`alertPolicies.alertLevel`)
- ✅ 状态选择器 (`alertPolicies.status`)
- ✅ 筛选选项：全部类型、全部级别、全部状态
- ✅ 策略类型选项：资源告警、事件告警
- ✅ 告警级别选项：信息、警告、错误、严重
- ✅ 状态选项：启用、禁用
- ✅ 查询和重置按钮

**3. 表格列标题**

- ✅ 报警器名称 (`alertPolicies.alertName`)
- ✅ 资源类型 (`alertPolicies.resourceType`)
- ✅ 报警条目 (`alertPolicies.alertItems`)
- ✅ 报警级别 (`alertPolicies.alertLevel`)
- ✅ 启用状态 (`alertPolicies.enabledStatus`)
- ✅ 通知对象 (`alertPolicies.notificationTargets`)
- ✅ 监控资源数量 (`alertPolicies.monitoredResourcesCount`)
- ✅ 创建时间 (`alertPolicies.createdTime`)
- ✅ 操作 (`alertPolicies.actions`)

**4. 表格内容**

- ✅ 操作按钮：启用/禁用、编辑、删除、测试
- ✅ 状态标签：启用、禁用
- ✅ 告警级别标签：信息、警告、错误、严重
- ✅ 数量显示：个、无

**5. 空状态**

- ✅ 暂无告警策略 (`alertPolicies.noAlertPolicies`)

**6. 表单**

- ✅ 基本信息标题 (`alertPolicies.basicInfo`)
- ✅ 策略名称字段 (`alertPolicies.policyName`, `alertPolicies.enterPolicyName`)
- ✅ 策略类型选择 (`alertPolicies.policyType`)
- ✅ 告警级别选择 (`alertPolicies.selectAlertLevel`)

**7. 表单验证**

- ✅ 策略名称验证 (`alertPolicies.validation.enterPolicyName`, `alertPolicies.validation.policyNameLength`)
- ✅ 策略类型验证 (`alertPolicies.validation.selectPolicyType`)
- ✅ 告警级别验证 (`alertPolicies.validation.selectAlertLevel`)
- ✅ 描述长度验证 (`alertPolicies.validation.descriptionLength`)

**8. 消息提示**

- ✅ 加载告警策略失败 (`alertPolicies.messages.loadPoliciesFailed`)
- ✅ 获取兼容数据失败 (`alertPolicies.messages.getCompatibilityDataFailed`)
- ✅ 请先选择资源类型 (`alertPolicies.messages.selectResourceTypeFirst`)
- ✅ 策略启用/禁用 (`alertPolicies.messages.policyEnabled`, `alertPolicies.messages.policyDisabled`)
- ✅ 操作失败 (`alertPolicies.messages.operationFailed`)
- ✅ 测试告警发送/失败 (`alertPolicies.messages.testAlertSent`, `alertPolicies.messages.testFailed`)
- ✅ 删除确认/成功/失败 (`alertPolicies.messages.confirmDeletePolicy`, `alertPolicies.messages.deleteSuccess`, `alertPolicies.messages.deleteFailed`)
- ✅ 配置验证失败 (`alertPolicies.messages.configValidationFailed`)
- ✅ 配置警告确认 (`alertPolicies.messages.configWarnings`, `alertPolicies.messages.configWarning`)
- ✅ 更新/创建成功/失败 (`alertPolicies.messages.updateSuccess`, `alertPolicies.messages.createSuccess`, `alertPolicies.messages.updateFailed`, `alertPolicies.messages.createFailed`)

**9. 工具函数**

- ✅ 告警级别标签 (`alertPolicies.info`, `alertPolicies.warning`, `alertPolicies.error`, `alertPolicies.critical`)
- ✅ 策略类型标签 (`alertPolicies.resourceAlert`, `alertPolicies.eventAlert`)
- ✅ 通知渠道类型 (`alertPolicies.channelTypes.*`)
- ✅ 日期格式化

**10. 对话框和确认框**

- ✅ 删除确认对话框 (`alertPolicies.messages.confirmDelete`)
- ✅ 配置警告确认对话框 (`alertPolicies.messages.configWarning`)
- ✅ 确认/取消按钮 (`alertPolicies.messages.confirm`, `alertPolicies.messages.cancel`)
- ✅ 继续按钮 (`alertPolicies.messages.continue`)

**11. 策略详情侧拉抽屉**

- ✅ 告警配置标题 (`alertPolicies.alertConfig`)
- ✅ 告警条目标签 (`alertPolicies.alertItems`)
- ✅ 告警规则标签 (`alertPolicies.alertRules`)
- ✅ 持续时间文本 (`alertPolicies.duration`, `alertPolicies.seconds`)
- ✅ 通知配置标题 (`alertPolicies.notificationConfig`)
- ✅ 通知模板标签 (`alertPolicies.notificationTemplate`, `alertPolicies.notSet`)
- ✅ 通知对象标签 (`alertPolicies.notificationTargets`)
- ✅ 通知列表标签 (`alertPolicies.notificationList`)
- ✅ 通知周期标签 (`alertPolicies.notificationCycle`, `alertPolicies.immediate`)
- ✅ 其他信息标题 (`alertPolicies.otherInfo`)
- ✅ 创建时间/更新时间标签 (`alertPolicies.createdTime`, `alertPolicies.updatedTime`)
- ✅ 操作按钮：编辑策略、测试策略、启用/禁用 (`alertPolicies.editPolicy`, `alertPolicies.testPolicy`, `alertPolicies.enable`, `alertPolicies.disable`)

**12. 通知对象选择器**

- ✅ 选择通知对象标题 (`alertPolicies.selectNotificationTargets`)
- ✅ 搜索通知对象占位符 (`alertPolicies.searchNotificationTargets`)
- ✅ 确认/取消按钮 (`alertPolicies.confirm`, `alertPolicies.cancel`)

### Monitoring.vue 国际化完成度：100% ✅

**已完成内容：**

**1. 页面标题和描述**

- ✅ 页面标题 (`monitoring.pageTitle`)
- ✅ 页面描述 (`monitoring.pageDescription`)

**2. 操作按钮**

- ✅ 刷新数据按钮 (`monitoring.refreshData`)
- ✅ 监控设置按钮 (`monitoring.monitoringSettings`)

**3. 系统状态概览**

- ✅ CPU 使用率 (`monitoring.cpuUsage`)
- ✅ 内存使用率 (`monitoring.memoryUsage`)
- ✅ 磁盘使用率 (`monitoring.diskUsage`)
- ✅ 活跃连接数 (`monitoring.activeConnections`)
- ✅ 正常状态 (`monitoring.normal`)
- ✅ 入流量/出流量 (`monitoring.inboundTraffic`, `monitoring.outboundTraffic`)

**4. 服务状态**

- ✅ 服务状态标题 (`monitoring.serviceStatus`)
- ✅ 服务名称：数据库、Redis、消息队列 (`monitoring.services.*`)
- ✅ 服务状态文本：正常、异常 (`monitoring.status.normal`, `monitoring.status.abnormal`)
- ✅ 整体服务状态：所有服务正常、部分服务异常、服务异常 (`monitoring.status.allServicesNormal`, `monitoring.status.partialServicesAbnormal`, `monitoring.status.servicesAbnormal`)

**5. 监控图表**

- ✅ CPU & 内存趋势标题 (`monitoring.cpuMemoryTrend`)
- ✅ 网络流量标题 (`monitoring.networkTraffic`)
- ✅ 实时标签 (`monitoring.realTime`)
- ✅ 时间范围选择：1 小时、6 小时、24 小时、7 天 (`monitoring.oneHour`, `monitoring.sixHours`, `monitoring.twentyFourHours`, `monitoring.sevenDays`)
- ✅ 图表标签：CPU、内存 (`monitoring.charts.cpu`, `monitoring.charts.memory`)

**6. 告警统计**

- ✅ 告警统计标题 (`monitoring.alertStatistics`)
- ✅ 查看详情按钮 (`monitoring.viewDetails`)
- ✅ 总告警数 (`monitoring.totalAlerts`)
- ✅ 活跃告警 (`monitoring.activeAlerts`)
- ✅ 已解决 (`monitoring.resolvedAlerts`)
- ✅ 严重告警 (`monitoring.criticalAlerts`)

**7. 状态判断函数**

- ✅ CPU 状态：正常、偏高、过高 (`monitoring.status.normal`, `monitoring.status.high`, `monitoring.status.tooHigh`)
- ✅ 内存状态：正常、偏高、过高 (`monitoring.status.normal`, `monitoring.status.high`, `monitoring.status.tooHigh`)
- ✅ 磁盘状态：正常、空间紧张、空间不足 (`monitoring.status.normal`, `monitoring.status.lowSpace`, `monitoring.status.insufficientSpace`)

**8. 消息提示**

- ✅ 获取系统状态失败 (`monitoring.messages.getSystemStatusFailed`)
- ✅ 数据刷新完成/失败 (`monitoring.messages.dataRefreshCompleted`, `monitoring.messages.dataRefreshFailed`)
- ✅ 监控设置功能开发中 (`monitoring.messages.monitoringSettingsInDevelopment`)

**9. 告警统计详情**

- ✅ 总告警数 (`monitoring.totalAlerts`)
- ✅ 活跃告警 (`monitoring.activeAlerts`)
- ✅ 已解决 (`monitoring.resolvedAlerts`)
- ✅ 严重告警 (`monitoring.criticalAlerts`)

**10. 网络图表标签**

- ✅ 入流量/出流量标签 (`monitoring.charts.networkIn`, `monitoring.charts.networkOut`)

### Profile.vue 国际化完成度：100% ✅

**已完成内容：**

**1. 页面标题**

- ✅ 页面标题 (`profile.pageTitle`)

**2. 标签页**

- ✅ 基本信息标签页 (`profile.basicInfo`)
- ✅ 修改密码标签页 (`profile.changePassword`)

**3. 基本信息表单**

- ✅ 头像标签和更换头像按钮 (`profile.avatar`, `profile.changeAvatar`)
- ✅ 用户名标签 (`profile.username`)
- ✅ 邮箱标签 (`profile.email`)
- ✅ 账户信息分割线 (`profile.accountInfo`)
- ✅ 用户 ID 标签和复制 ID 提示 (`profile.userId`, `profile.copyId`)
- ✅ 用户角色标签和角色显示 (`profile.userRole`, `profile.admin`, `profile.normalUser`)
- ✅ 创建时间/最后登录标签 (`profile.createdTime`, `profile.lastLogin`)
- ✅ 保存修改按钮 (`profile.saveChanges`)

**4. 修改密码表单**

- ✅ 当前密码标签 (`profile.currentPassword`)
- ✅ 新密码标签 (`profile.newPassword`)
- ✅ 确认新密码标签 (`profile.confirmPassword`)
- ✅ 修改密码按钮 (`profile.changePassword`)

**5. 表单验证**

- ✅ 邮箱验证消息 (`profile.validation.enterEmail`, `profile.validation.enterValidEmail`)
- ✅ 密码验证消息 (`profile.validation.enterCurrentPassword`, `profile.validation.enterNewPassword`, `profile.validation.confirmNewPassword`)
- ✅ 密码长度验证 (`profile.validation.passwordLength`)
- ✅ 密码确认验证 (`profile.validation.passwordsNotMatch`)

**6. 消息提示**

- ✅ 头像格式/大小错误 (`profile.messages.avatarFormatError`, `profile.messages.avatarSizeError`)
- ✅ 获取用户信息失败 (`profile.messages.getUserInfoFailed`)
- ✅ 个人信息更新成功/失败 (`profile.messages.profileUpdateSuccess`, `profile.messages.updateFailed`)
- ✅ 头像更新成功/失败 (`profile.messages.avatarUpdateSuccess`, `profile.messages.avatarUpdateFailed`)
- ✅ 用户 ID 复制成功/失败 (`profile.messages.userIdCopied`, `profile.messages.copyFailed`)
- ✅ 密码修改成功/失败 (`profile.messages.passwordChangeSuccess`, `profile.messages.changeFailed`)

**7. 辅助函数**

- ✅ 未知状态显示 (`profile.unknown`)

### Settings.vue 国际化完成度：100% ✅

**已完成内容：**

**1. 页面标题**

- ✅ 页面标题 (`settings.pageTitle`)

**2. 标签页**

- ✅ 基本设置标签页 (`settings.basicSettings`)
- ✅ 日志设置标签页 (`settings.logSettings`)
- ✅ 通知设置标签页 (`settings.notificationSettings`)

**3. 基本设置表单**

- ✅ 最大并发任务数标签和提示 (`settings.maxConcurrentTasks`, `settings.maxConcurrentTasksTip`)
- ✅ 默认重试次数标签和提示 (`settings.defaultRetryCount`, `settings.defaultRetryCountTip`)
- ✅ 默认重试延迟标签和提示 (`settings.defaultRetryDelay`, `settings.defaultRetryDelayTip`)
- ✅ 保存设置按钮 (`settings.saveSettings`)

**4. 日志设置表单**

- ✅ 日志保留天数标签和提示 (`settings.logRetentionDays`, `settings.logRetentionDaysTip`)
- ✅ 日志级别标签和提示 (`settings.logLevel`, `settings.logLevelTip`)
- ✅ 日志文件路径标签和提示 (`settings.logFilePath`, `settings.logFilePathTip`)
- ✅ 保存设置和清理日志按钮 (`settings.saveSettings`, `settings.clearLogs`)

**5. 通知设置分组**

- ✅ 邮件通知标题和按钮 (`settings.emailNotification`, `settings.edit`, `settings.save`, `settings.cancel`)
- ✅ 短信通知标题和按钮 (`settings.smsNotification`, `settings.edit`, `settings.save`, `settings.cancel`)
- ✅ 钉钉通知标题和按钮 (`settings.dingtalkNotification`, `settings.edit`, `settings.save`, `settings.cancel`)
- ✅ Webhook 通知标题和按钮 (`settings.webhookNotification`, `settings.edit`, `settings.save`, `settings.cancel`)

**6. 通知开关标签**

- ✅ 启用邮件通知 (`settings.enableEmailNotification`)
- ✅ 启用短信通知 (`settings.enableSmsNotification`)
- ✅ 启用钉钉通知 (`settings.enableDingtalkNotification`)
- ✅ 启用 Webhook 通知 (`settings.enableWebhookNotification`)

**7. 邮件通知表单**

- ✅ SMTP 服务器、端口、用户名、密码标签 (`settings.smtpHost`, `settings.smtpPort`, `settings.smtpUsername`, `settings.smtpPassword`)
- ✅ 发件人邮箱标签 (`settings.senderEmail`)
- ✅ 测试发送按钮 (`settings.testSend`)

**8. 短信通知表单**

- ✅ 服务商、API Key、模板 ID、签名标签 (`settings.smsProvider`, `settings.smsApiKey`, `settings.smsTemplateId`, `settings.smsSignName`)
- ✅ 选择服务商占位符 (`settings.selectProvider`)
- ✅ 测试发送按钮 (`settings.testSend`)

**9. 钉钉通知表单**

- ✅ Webhook、密钥标签 (`settings.dingtalkWebhook`, `settings.dingtalkSecret`)
- ✅ 测试发送按钮 (`settings.testSend`)

**10. Webhook 通知表单**

- ✅ Webhook URL、安全密钥标签 (`settings.webhookUrl`, `settings.webhookSecret`)
- ✅ 测试发送按钮 (`settings.testSend`)

**11. 输入框占位符**

- ✅ SMTP 服务器占位符 (`settings.placeholders.smtpHost`)
- ✅ 用户名、密码占位符 (`settings.placeholders.username`, `settings.placeholders.password`)
- ✅ 发件人邮箱占位符 (`settings.placeholders.senderEmail`)
- ✅ API Key 占位符 (`settings.placeholders.apiKey`)
- ✅ 短信模板 ID、签名占位符 (`settings.placeholders.smsTemplateId`, `settings.placeholders.smsSignName`)
- ✅ 钉钉 Webhook、密钥占位符 (`settings.placeholders.dingtalkWebhook`, `settings.placeholders.dingtalkSecret`)
- ✅ Webhook URL、密钥占位符 (`settings.placeholders.webhookUrl`, `settings.placeholders.webhookSecret`)

**12. 服务商选项**

- ✅ 阿里云、腾讯云选项 (`settings.providers.aliyun`, `settings.providers.tencent`)

**13. 表单验证**

- ✅ 基本设置验证消息 (`settings.validation.enterMaxConcurrentTasks`, `settings.validation.enterDefaultRetryCount`, `settings.validation.enterDefaultRetryDelay`)
- ✅ 日志设置验证消息 (`settings.validation.enterLogRetentionDays`, `settings.validation.selectLogLevel`, `settings.validation.enterLogFilePath`)
- ✅ 邮件通知验证消息 (`settings.validation.enterEmailAddress`, `settings.validation.enterValidEmailFormat`, `settings.validation.enterSmtpHost`, `settings.validation.enterSmtpPort`, `settings.validation.enterSmtpUsername`, `settings.validation.enterSmtpPassword`)
- ✅ Webhook 通知验证消息 (`settings.validation.enterWebhookUrl`, `settings.validation.enterValidUrlFormat`, `settings.validation.enterWebhookSecret`)
- ✅ 钉钉通知验证消息 (`settings.validation.enterDingtalkWebhook`, `settings.validation.enterDingtalkSecret`)
- ✅ 短信通知验证消息 (`settings.validation.selectSmsProvider`, `settings.validation.enterApiKey`, `settings.validation.enterTemplateId`, `settings.validation.enterSignName`)

**14. 消息提示**

- ✅ 取消编辑确认 (`settings.messages.confirmCancelEdit`, `settings.messages.confirmCancel`)
- ✅ 测试通过后保存提示 (`settings.messages.testFirstThenSave`)
- ✅ 设置保存成功/失败 (`settings.messages.settingsSaved`, `settings.messages.saveSettingsFailed`)
- ✅ 获取系统设置失败 (`settings.messages.getSystemSettingsFailed`)
- ✅ 测试通知发送成功/失败 (`settings.messages.testNotificationSent`, `settings.messages.testNotificationFailed`)
- ✅ 重置通知设置确认/成功/失败 (`settings.messages.confirmResetNotificationSettings`, `settings.messages.notificationSettingsReset`, `settings.messages.resetNotificationSettingsFailed`)
- ✅ 通知设置保存成功/失败 (`settings.messages.notificationSettingsSaved`, `settings.messages.saveNotificationSettingsFailed`)

**15. 按钮和操作**

- ✅ 确认/取消按钮 (`settings.confirm`, `settings.cancel`)
- ✅ 继续编辑按钮 (`settings.continueEdit`)

### Nodes.vue 国际化完成度：100% ✅

**已完成内容：**

**1. 页面标题和描述**

- ✅ 页面标题 (`nodes.pageTitle`)
- ✅ 页面描述 (`nodes.pageSubtitle`)

**2. 操作按钮**

- ✅ 添加代理节点按钮 (`nodes.addProxyNode`)
- ✅ 流程引导按钮 (`nodes.processGuide`)
- ✅ 流程引导提示 (`nodes.hideProcessGuide`, `nodes.showProcessGuide`)

**3. 架构说明部分**

- ✅ 架构说明标题 (`nodes.architectureTitle`)
- ✅ 架构说明副标题 (`nodes.architectureSubtitle`)
- ✅ 存储资源标签 (`nodes.storageResourceA`, `nodes.storageResourceB`)
- ✅ 存储类型说明 (`nodes.storageTypes`)
- ✅ 同步代理节点标签 (`nodes.syncProxyNode`)
- ✅ 代理节点描述 (`nodes.proxyDescription`, `nodes.proxyFeatures`)
- ✅ 架构说明文本 (`nodes.architectureDescription`)

**4. 使用指南**

- ✅ 使用指南标题 (`nodes.usageGuide`)
- ✅ 步骤标题和描述 (`nodes.step1Title`, `nodes.step1Description`, `nodes.step2Title`, `nodes.step2Description`, `nodes.step3Title`, `nodes.step3Description`, `nodes.step4Title`, `nodes.step4Description`)

**5. 统计卡片**

- ✅ 在线服务器 (`nodes.onlineServers`)
- ✅ 离线服务器 (`nodes.offlineServers`)
- ✅ 运行中 Agent (`nodes.runningAgents`)
- ✅ 待安装 Agent (`nodes.pendingAgents`)

**6. 节点列表**

- ✅ 节点列表标题 (`nodes.nodeList`)
- ✅ 节点数量标签 (`nodes.nodesCount`)
- ✅ 筛选器占位符 (`nodes.groupFilter`, `nodes.tagFilter`, `nodes.statusFilter`)
- ✅ 筛选选项 (`nodes.all`, `nodes.online`, `nodes.offline`, `nodes.agentInstalled`, `nodes.agentNotInstalled`)
- ✅ 批量操作按钮 (`nodes.batchDelete`, `nodes.batchGroup`, `nodes.batchTag`)
- ✅ 搜索占位符 (`nodes.searchNameIp`)

**7. 表格列标题**

- ✅ 名称列 (`nodes.name`)
- ✅ 分组列 (`nodes.group`)
- ✅ 标签列 (`nodes.tags`)
- ✅ IP 地址列 (`nodes.ipAddress`)
- ✅ 用户名列 (`nodes.username`)
- ✅ 端口列 (`nodes.port`)
- ✅ 状态列 (`nodes.status`)
- ✅ Agent 状态列 (`nodes.agentStatus`)
- ✅ 最后心跳列 (`nodes.lastHeartbeat`)
- ✅ 备注列 (`nodes.description`)
- ✅ 操作列 (`nodes.actions`)

**8. 操作按钮**

- ✅ 详情按钮 (`nodes.details`)
- ✅ 更多按钮 (`nodes.more`)
- ✅ 编辑按钮 (`nodes.edit`)
- ✅ 测试连接按钮 (`nodes.testConnection`)
- ✅ 安装 Agent 按钮 (`nodes.installAgent`)
- ✅ 卸载 Agent 按钮 (`nodes.uninstallAgent`)
- ✅ 获取信息按钮 (`nodes.getInfo`)
- ✅ 删除按钮 (`nodes.delete`)

**9. 弹窗和对话框**

- ✅ 添加/编辑节点弹窗标题 (`nodes.addNode`, `nodes.editNode`)
- ✅ 表单字段标签和占位符 (`nodes.enterNodeName`, `nodes.enterIpAddress`, `nodes.enterUsername`, `nodes.enterPassword`, `nodes.enterSshKey`, `nodes.enterDescription`)
- ✅ 认证方式选项 (`nodes.authType`, `nodes.passwordAuth`, `nodes.keyAuth`)
- ✅ 弹窗按钮 (`nodes.cancel`, `nodes.confirm`)

**10. 安装 Agent 弹窗**

- ✅ 弹窗标题 (`nodes.installUninstallAgent`)
- ✅ 表单字段 (`nodes.installPath`, `nodes.configParams`, `nodes.enterJsonConfig`)
- ✅ 操作按钮 (`nodes.startInstall`)

**11. 节点详情抽屉**

- ✅ 抽屉标题 (`nodes.nodeDetails`)
- ✅ 标签页标题 (`nodes.basicInfo`, `nodes.monitorData`)
- ✅ 基本信息卡片标题 (`nodes.basicInfo`)
- ✅ 描述项标签 (`nodes.nodeName`, `nodes.operatingSystem`)
- ✅ CPU 信息卡片 (`nodes.cpuInfo`, `nodes.cores`)
- ✅ 内存信息卡片 (`nodes.memoryInfo`, `nodes.totalMemory`, `nodes.usedMemory`, `nodes.availableMemory`)
- ✅ 磁盘信息卡片 (`nodes.diskInfo`, `nodes.totalCapacity`, `nodes.usedCapacity`, `nodes.availableCapacity`)
- ✅ 网卡信息卡片 (`nodes.networkInfo`)

**12. 状态文本函数**

- ✅ 节点状态文本 (`nodes.online`, `nodes.offline`, `nodes.error`, `nodes.unknown`)
- ✅ Agent 状态文本 (`nodes.running`, `nodes.installing`, `nodes.notInstalled`, `nodes.uninstallError`, `nodes.installError`)

**13. 消息提示**

- ✅ 成功消息 (`nodes.addSuccess`, `nodes.updateSuccess`, `nodes.deleteSuccess`, `nodes.startInstallAgent`, `nodes.startUninstallAgent`)
- ✅ 错误消息 (`nodes.noNodeSelected`)
- ✅ 确认对话框 (`nodes.confirmUninstallAgent`, `nodes.confirmDeleteNode`, `nodes.tip`)

**14. 监控数据部分**

- ✅ 时间范围选择器 (`nodes.timeRange`, `nodes.selectTimeRange`)
- ✅ 时间范围选项 (`nodes.last10Minutes`, `nodes.last15Minutes`, `nodes.last1Hour`, `nodes.last2Hours`, `nodes.custom`)
- ✅ 日期选择器 (`nodes.to`, `nodes.startTime`, `nodes.endTime`)
- ✅ 刷新设置 (`nodes.refreshSettings`, `nodes.refresh`, `nodes.autoRefresh`)
- ✅ 刷新间隔选项 (`nodes.refreshInterval`, `nodes.3Seconds`, `nodes.5Seconds`, `nodes.10Seconds`, `nodes.30Seconds`, `nodes.1Minute`, `nodes.5Minutes`)

**15. 图表标题**

- ✅ CPU 使用情况 (`nodes.cpuUsage`)
- ✅ 内存使用情况 (`nodes.memoryUsage`)
- ✅ 磁盘使用情况 (`nodes.diskUsage`)
- ✅ 网络流量监控 (`nodes.networkTrafficMonitor`)

**16. 进程列表**

- ✅ 进程列表标题 (`nodes.processList`)
- ✅ 表格列标题 (`nodes.user`, `nodes.command`)

**17. 系统日志**

- ✅ 系统日志标签页 (`nodes.systemLogs`)
- ✅ 日志搜索 (`nodes.searchLogs`)
- ✅ 日志级别 (`nodes.logLevel`)
- ✅ 日志刷新控制 (`nodes.refresh`, `nodes.autoRefresh`, `nodes.refreshInterval`)

**18. 批量操作消息**

- ✅ 批量分组消息 (`nodes.pleaseSelectNodesToGroup`, `nodes.batchGroupSuccess`, `nodes.batchGroupFailed`)
- ✅ 批量打标签消息 (`nodes.pleaseSelectNodesToTag`, `nodes.batchTagSuccess`, `nodes.batchTagFailed`)
- ✅ 批量删除消息 (`nodes.pleaseSelectNodesToDelete`, `nodes.batchDeleteSuccess`, `nodes.batchDeleteFailed`)

**19. 操作结果消息**

- ✅ 连接测试消息 (`nodes.connectionTestSuccess`)
- ✅ 获取信息消息 (`nodes.getInfoSuccess`, `nodes.getInfoFailed`)
- ✅ 节点详情消息 (`nodes.loadNodeDetailsFailed`, `nodes.getNodeDetailsFailed`)
- ✅ 监控数据消息 (`nodes.loadHistoryDataFailed`)
- ✅ 进程列表消息 (`nodes.getProcessListFailed`)
- ✅ 日志获取消息 (`nodes.getLogsFailed`)

**20. 图表系列名称**

- ✅ CPU 图表系列 (`nodes.load1Minute`, `nodes.load5Minutes`, `nodes.load15Minutes`)
- ✅ 网络图表系列 (`nodes.receivedTraffic`, `nodes.sentTraffic`, `nodes.droppedPackets`)

**21. 遗漏内容（需要补充）**

- ✅ 日志表格列标题 (`nodes.timestamp`, `nodes.level`, `nodes.module`, `nodes.message`)
- ✅ 表单验证消息（请输入名称、请输入 IP 地址、请输入用户名、请输入端口、端口号必须在 1-65535 之间、请选择认证方式、请输入密码、请输入 SSH 密钥）
- ✅ 批量删除确认消息（确定要删除选中的 X 台节点吗？）
- ✅ 进程表格列标题（内存%）
- ✅ 批量操作弹窗标题和占位符
- ✅ 批量操作弹窗按钮

### Clients.vue 国际化完成度：10% ✅

**已完成内容：**

**1. 语言包准备**

- ✅ 中文语言包 (clients): 150+ 个键值对
- ✅ 英文语言包 (clients): 150+ 个键值对
- ✅ useI18n 导入和 t 函数设置

**2. 页面标题和描述**

- ✅ 页面标题 (`clients.pageTitle`)
- ✅ 页面描述 (`clients.pageSubtitle`)

**待完成内容：**

- ❌ 操作按钮
- ❌ 架构说明部分
- ❌ 统计卡片
- ❌ 服务器列表
- ❌ 表格列标题
- ❌ 操作按钮
- ❌ 弹窗和对话框
- ❌ 状态文本函数
- ❌ 消息提示
- ❌ 监控数据界面
- ❌ 图表标题和系列名称
- ❌ 进程列表
- ❌ 系统日志
- ❌ 批量操作消息
- ❌ 操作结果消息
- ❌ 表单验证消息

## 下一步计划

1. **继续前端页面国际化**：按照优先级顺序，先完成核心功能页面
2. **后端国际化**：配置后端国际化工具，处理 API 响应和错误消息
3. **测试验证**：确保所有国际化功能正常工作
4. **文档完善**：更新项目文档，添加国际化使用指南
5. **性能优化**：优化语言包加载和缓存机制
