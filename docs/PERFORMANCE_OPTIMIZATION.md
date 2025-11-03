# 性能优化指南

## 概述

本文档介绍了 EasySync 项目的性能优化措施，包括缓存策略、限流机制、数据库优化等。

## 1. Redis 缓存

### 1.1 缓存管理器

位置：`backend/app/utils/cache.py`

缓存管理器提供了统一的缓存接口，支持：
- 自动JSON序列化/反序列化
- TTL过期控制
- 模式匹配删除
- 降级处理（Redis不可用时自动降级）

### 1.2 使用示例

#### 基本使用

```python
from backend.app.utils.cache import CacheManager

# 设置缓存
CacheManager.set('user:123', {'name': 'John'}, ttl=3600)

# 获取缓存
user = CacheManager.get('user:123')

# 删除缓存
CacheManager.delete('user:123')

# 按模式删除
CacheManager.delete_pattern('user:*')
```

#### 装饰器使用

```python
from backend.app.utils.cache import cached

@cached(ttl=300, key_prefix='dashboard')
def get_dashboard_data(user_id):
    # 昂贵的计算或数据库查询
    return expensive_operation()
```

### 1.3 缓存策略

#### 已实现的缓存

1. **仪表盘数据** (`dashboard/routes.py`)
   - 键格式：`dashboard:user:{user_id}`
   - TTL：5分钟
   - 理由：仪表盘数据变化不频繁，但查询较多

2. **用户信息**（建议实现）
   - 键格式：`user_profile:{user_id}`
   - TTL：1小时
   - 清除时机：用户信息更新时

3. **任务统计**（建议实现）
   - 键格式：`task_stats:{user_id}:{date}`
   - TTL：10分钟
   - 清除时机：任务状态变化时

### 1.4 缓存失效策略

```python
from backend.app.utils.cache import CacheManager

# 用户更新后清除相关缓存
CacheManager.clear_user_cache(user_id)
```

## 2. API 限流

### 2.1 限流器

位置：`backend/app/utils/rate_limit.py`

限流器使用 Redis 实现分布式限流，支持：
- 基于IP的限流
- 基于用户的限流
- 滑动窗口算法
- 优雅降级（Redis不可用时允许请求）

### 2.2 使用示例

#### 基本限流

```python
from backend.app.utils.rate_limit import rate_limit

@bp.route('/api/endpoint')
@rate_limit(limit=100, window=60)  # 每分钟100次
def endpoint():
    return jsonify({'data': 'ok'})
```

#### 用户限流

```python
from backend.app.utils.rate_limit import user_rate_limit

@bp.route('/api/user/action')
@jwt_required()
@user_rate_limit(limit=50, window=3600)  # 每小时50次/用户
def user_action():
    return jsonify({'data': 'ok'})
```

### 2.3 已实现的限流

1. **验证码接口**
   - 限制：每分钟10次
   - 目的：防止验证码暴力请求

2. **登录接口**
   - 限制：每5分钟5次
   - 目的：防止暴力破解

3. **仪表盘接口**
   - 限制：每分钟30次
   - 目的：防止过度请求

### 2.4 响应头

限流装饰器会自动添加响应头：
- `X-RateLimit-Limit`: 限制数量
- `X-RateLimit-Remaining`: 剩余次数
- `X-RateLimit-Reset`: 重置时间（Unix时间戳）

超出限制时返回 429 状态码。

## 3. 数据库查询优化

### 3.1 已实现的优化

#### 审计日志查询优化

位置：`backend/app/auth/routes.py`

使用子查询优化大表分页：
1. 先查询ID列表（只排序ID，减少内存占用）
2. 对ID进行分页
3. 根据ID列表获取完整数据

性能提升：
- 查询时间：5-10秒 → 0.1-0.5秒
- 内存占用：减少90%+

### 3.2 索引建议

```sql
-- 审计日志复合索引
CREATE INDEX idx_audit_logs_action_created_at ON audit_logs(action, created_at DESC);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);

-- 任务查询索引
CREATE INDEX idx_tasks_user_status ON tasks(user_id, status);
CREATE INDEX idx_tasks_created_at ON tasks(created_at DESC);

-- 存储查询索引
CREATE INDEX idx_storages_user_type ON storages(user_id, type);
```

### 3.3 查询优化最佳实践

1. **避免N+1查询**
   ```python
   # 错误
   for task in tasks:
       user = User.query.get(task.user_id)  # N+1
   
   # 正确：使用join或预先加载
   tasks = Task.query.options(joinedload(Task.user)).all()
   ```

2. **使用计数查询优化**
   ```python
   # 错误
   count = len(Model.query.all())
   
   # 正确
   count = Model.query.count()
   ```

3. **避免全表扫描**
   ```python
   # 错误
   tasks = Task.query.order_by(Task.created_at.desc()).all()
   
   # 正确：添加限制和过滤
   tasks = Task.query.filter_by(user_id=user_id)\
       .order_by(Task.created_at.desc())\
       .limit(20).all()
   ```

## 4. 连接池优化

### 4.1 数据库连接池

配置位置：`backend/app/config/default.py`

```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'connect_args': {
        'connect_timeout': 10,
        'read_timeout': 10,
        'write_timeout': 10
    }
}
```

### 4.2 Redis连接池

Redis客户端自动使用连接池，配置：
- `socket_connect_timeout`: 5秒
- `socket_timeout`: 5秒
- `health_check_interval`: 30秒

## 5. 性能监控

### 5.1 慢查询日志

启用MySQL慢查询日志：
```sql
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;  -- 2秒
```

### 5.2 缓存命中率监控

建议添加缓存统计：
- 命中率监控
- 缓存大小监控
- 过期键统计

## 6. 未来优化方向

### 6.1 查询缓存

实现SQL查询结果缓存：
```python
@cached(ttl=300, key_func=lambda query: f"query:{hash(str(query))}")
def execute_cached_query(query):
    return query.all()
```

### 6.2 异步处理

对于耗时操作使用异步任务：
- 大文件上传
- 批量数据处理
- 报告生成

### 6.3 CDN集成

静态资源使用CDN：
- 前端静态文件
- 用户上传的图片
- 文档资源

### 6.4 数据库读写分离

主从复制：
- 写操作 → 主库
- 读操作 → 从库（可选）

## 7. 性能基准

### 目标指标

- API响应时间 P95 < 500ms
- 数据库查询时间 < 100ms（简单查询）
- 缓存命中率 > 80%
- 错误率 < 0.1%

### 压力测试

建议使用以下工具进行压力测试：
- Apache Bench (ab)
- Locust
- JMeter

## 8. 故障排查

### 8.1 性能问题诊断步骤

1. 检查慢查询日志
2. 查看Redis连接状态
3. 监控数据库连接池使用情况
4. 检查缓存命中率
5. 分析API响应时间分布

### 8.2 常见问题

**Q: Redis连接失败**
A: 检查Redis服务状态，应用会自动降级（不使用缓存）

**Q: 限流不生效**
A: 检查Redis连接，限流依赖Redis

**Q: 缓存数据过期不及时**
A: 确保在数据更新时调用缓存清除

