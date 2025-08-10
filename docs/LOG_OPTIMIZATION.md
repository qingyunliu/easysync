# 任务日志优化方案

## 🎯 问题描述

proxy 上报的进度日志过于频繁，导致：
- 数据库记录膨胀（80,000+ 条记录）
- 前端渲染性能问题
- 用户体验差（用户只需要看最新进度）

## 🚀 解决方案

### 1. 数据库层面优化

#### 1.1 UPSERT 模式
- **位置**: `backend/app/tasks/service.py`
- **功能**: 对于进度日志，使用 upsert 模式，只保留最新的一条
- **实现**: 
  ```python
  if '同步进度' in message:
      existing_log = TaskLog.query.filter(
          TaskLog.task_id == task_id,
          TaskLog.message.like('%同步进度%')
      ).first()
      if existing_log:
          # 更新现有记录
          existing_log.message = message
          existing_log.details = details or {}
          existing_log.updated_at = datetime.utcnow()
          return existing_log
  ```

#### 1.2 定期清理机制
- **位置**: `backend/app/tasks/service.py`
- **功能**: 
  - `cleanup_old_progress_logs(task_id=None, days=7)`: 清理过期的进度日志（默认7天）
  - `cleanup_duplicate_progress_logs(task_id)`: 清理指定任务的重复进度日志
  - `cleanup_all_duplicate_progress_logs()`: 清理所有任务的重复进度日志
- **定时任务**: 每天凌晨2点和3点自动执行全局清理

### 2. API 层面优化

#### 2.1 日志获取API优化
- **位置**: `backend/app/tasks/routes.py`
- **功能**:
  - 支持分页查询
  - 支持状态过滤
  - 默认只返回最新进度日志
  - 支持 `latest_progress_only` 参数

#### 2.2 日志清理API
- **单个任务清理**: `POST /api/tasks/{task_id}/logs/cleanup`
  - `type`: 'old' 或 'duplicate'
  - `days`: 保留天数（默认7天）
- **全局清理**: `POST /api/tasks/logs/cleanup`
  - `type`: 'old' 或 'duplicate'
  - `days`: 保留天数（默认7天）

### 3. 前端层面优化

#### 3.1 日志显示优化
- **位置**: `frontend/src/views/Tasks.vue`
- **功能**:
  - 进度日志只显示最新的一条
  - 其他日志正常显示
  - 支持分页浏览
  - 添加清理按钮

#### 3.2 性能优化
- 分页加载（默认20条/页）
- 虚拟滚动支持
- 按时间倒序排列

### 4. 定时任务

#### 4.1 自动清理
- **位置**: `backend/app/tasks/scheduler.py`
- **调度**:
  - 每天凌晨2点：清理过期日志
  - 每天凌晨3点：清理重复进度日志

## 📊 效果对比

### 优化前
- 数据库记录：80,000+ 条
- 前端渲染：缓慢
- 用户体验：差

### 优化后
- 数据库记录：每个任务最多1条进度日志
- 前端渲染：快速
- 用户体验：良好

## 🔧 使用方法

### 手动清理日志
1. 在任务日志对话框中点击"清理重复日志"
2. 或点击"清理过期日志"

### API 调用示例
```bash
# 清理重复日志
curl -X POST /api/tasks/logs/cleanup \
  -H "Authorization: Bearer <token>" \
  -d '{"type": "duplicate"}'

# 清理过期日志
curl -X POST /api/tasks/logs/cleanup \
  -H "Authorization: Bearer <token>" \
  -d '{"type": "old", "days": 7}'
```

## 🎯 业界标准

本方案遵循以下业界标准：

1. **UPSERT 模式**: 避免重复记录
2. **分页查询**: 提高查询性能
3. **定期清理**: 防止数据膨胀
4. **增量更新**: 只更新必要的数据
5. **用户友好**: 只显示用户关心的信息

## 📈 性能提升

- **数据库查询**: 从 O(n) 降低到 O(1)
- **前端渲染**: 从 80,000+ 条记录降低到 20 条/页
- **内存使用**: 显著减少
- **用户体验**: 大幅提升 