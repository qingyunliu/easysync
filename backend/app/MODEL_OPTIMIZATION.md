# 数据库模型优化总结

## 问题分析

### 重复的模型定义：
1. **`alert.py`**：包含 `Alert` 和 `AlertRule` 模型（较简单）
2. **`alert_policy.py`**：包含 `AlertPolicy`、`AlertPolicyRule`、`NotificationChannel`、`NotificationTarget`、`AlertPolicyAssignment`、`AlertInstance` 模型（更完整）

### 使用情况分析：
- **`Alert` 和 `AlertRule`**：被 `monitor` 模块使用
- **`AlertPolicy` 等**：被 `alerts` 模块使用

## 优化方案

### 1. 合并模型文件
**删除 `alert_policy.py`，将所有模型合并到 `alert.py` 中**

#### 新的 `alert.py` 结构：
```python
# 兼容旧版本的模型
class Alert(BaseModel):
    """告警模型 - 兼容旧版本"""
    # ... 现有代码

class AlertRule(BaseModel):
    """告警规则模型 - 兼容旧版本"""
    # ... 现有代码

# 新的告警策略模型
class AlertPolicy(BaseModel):
    """告警策略模型"""
    # ... 新代码

class AlertPolicyRule(BaseModel):
    """告警策略规则模型"""
    # ... 新代码

class NotificationChannel(BaseModel):
    """通知渠道模型"""
    # ... 新代码

class NotificationTarget(BaseModel):
    """通知对象模型"""
    # ... 新代码

class AlertPolicyAssignment(BaseModel):
    """告警策略分配模型"""
    # ... 新代码

class AlertInstance(BaseModel):
    """告警实例模型"""
    # ... 新代码
```

### 2. 更新导入引用

#### 修改 `backend/app/models/__init__.py`：
```python
from .alert import (
    Alert, AlertRule, AlertPolicy, AlertPolicyRule, 
    NotificationChannel, NotificationTarget, 
    AlertPolicyAssignment, AlertInstance
)
```

### 3. 保持向后兼容
- 保留原有的 `Alert` 和 `AlertRule` 模型
- 添加新的告警策略模型
- 确保现有代码不受影响

## 优化效果

### 1. 消除重复
- ✅ 删除重复的模型定义文件
- ✅ 统一所有告警相关模型到一个文件
- ✅ 减少维护成本

### 2. 清晰的结构
- ✅ 兼容旧版本的模型（Alert, AlertRule）
- ✅ 新的告警策略模型（AlertPolicy 等）
- ✅ 明确的功能分工

### 3. 更好的组织
- ✅ 所有告警相关模型集中管理
- ✅ 清晰的模型关系
- ✅ 统一的命名规范

## 实施步骤

### 1. 备份现有数据
```bash
# 备份数据库
pg_dump your_database > backup.sql
```

### 2. 删除重复文件
```bash
rm backend/app/models/alert_policy.py
```

### 3. 更新模型文件
- 将 `alert_policy.py` 中的模型合并到 `alert.py`
- 保持现有 `Alert` 和 `AlertRule` 模型不变
- 添加新的告警策略模型

### 4. 更新导入引用
- 修改 `models/__init__.py`
- 检查所有使用这些模型的文件

### 5. 测试验证
- 运行单元测试
- 检查API功能
- 验证数据库迁移

## 模型关系图

```
Alert (旧版本)
├── AlertRule (旧版本)
└── 用户、客户端、节点关联

AlertPolicy (新版本)
├── AlertPolicyRule
├── NotificationChannel
├── NotificationTarget
├── AlertPolicyAssignment
└── AlertInstance
```

## 注意事项

### 1. 数据库迁移
- 需要创建数据库迁移脚本
- 确保现有数据不丢失
- 测试迁移过程

### 2. 代码兼容性
- 保持现有API接口不变
- 确保前端代码正常工作
- 逐步迁移到新模型

### 3. 性能考虑
- 合理设计数据库索引
- 优化查询性能
- 监控数据库性能

## 总结

通过这次优化，我们：

1. **消除了重复的模型定义**
2. **统一了告警相关的模型管理**
3. **保持了向后兼容性**
4. **提高了代码的可维护性**

优化后的架构更加清晰，为后续功能扩展奠定了良好基础。 