# Refresh Token 过期机制

## 概述

为了提高系统安全性，我们实现了refresh token的过期机制。现在用户的登录状态会在指定时间后自动过期，要求重新登录。

## 功能特性

### 后端改进
- ✅ **配置化过期时间**: 支持通过环境变量配置token过期时间
- ✅ **区分环境配置**: 开发环境7天，生产环境3天（可配置）
- ✅ **详细错误码**: 返回具体的错误码，便于前端处理
- ✅ **审计日志**: 记录token刷新成功/失败的操作日志

### 前端改进
- ✅ **友好提示**: refresh token过期时显示用户友好的提示信息
- ✅ **自动清理**: 自动清除所有认证相关的本地存储
- ✅ **延迟跳转**: 给用户时间阅读提示信息后再跳转登录页

### 错误码说明
- `REFRESH_TOKEN_EXPIRED`: refresh token已过期
- `REFRESH_TOKEN_INVALID`: refresh token无效（用户不存在或邮箱未验证）
- `REFRESH_TOKEN_ERROR`: token刷新过程中的其他错误

## 环境变量配置

### 开发环境 (.env)
```bash
# JWT配置
JWT_ACCESS_TOKEN_EXPIRES_HOURS=1      # access token过期时间（小时）
JWT_REFRESH_TOKEN_EXPIRES_DAYS=7      # refresh token过期时间（天）
```

### 生产环境 (.env.production)
```bash
# JWT配置 - 生产环境更严格
JWT_ACCESS_TOKEN_EXPIRES_MINUTES=30   # access token过期时间（分钟）
JWT_REFRESH_TOKEN_EXPIRES_DAYS=3      # refresh token过期时间（天）
FLASK_ENV=production                   # 使用生产环境配置
```

## 用户体验

### refresh token过期时
1. 用户进行需要认证的操作
2. 系统检测到access token过期，自动尝试刷新
3. 发现refresh token也过期，显示提示："登录已过期，请重新登录"
4. 1秒后自动跳转到登录页面
5. 清除所有本地认证信息

### 建议的过期时间设置

#### 开发环境
- Access Token: 1小时（便于开发调试）
- Refresh Token: 7天（减少开发时频繁登录）

#### 生产环境  
- Access Token: 30分钟（提高安全性）
- Refresh Token: 3天（安全性和用户体验的平衡）

#### 高安全性环境
- Access Token: 15分钟
- Refresh Token: 1天

## 部署注意事项

1. **环境变量设置**: 确保在部署时设置正确的环境变量
2. **数据库迁移**: 不需要数据库结构变更
3. **前端缓存**: 部署后清除浏览器缓存，确保新的JS代码生效
4. **监控告警**: 建议监控refresh token过期的频率，避免设置过短

## 测试验证

### 手动测试步骤
1. 登录系统获取token
2. 修改系统时间或等待token过期
3. 执行需要认证的操作
4. 验证是否显示正确的过期提示
5. 验证是否正确跳转到登录页

### 环境变量测试
```bash
# 设置很短的过期时间进行测试
export JWT_REFRESH_TOKEN_EXPIRES_DAYS=0.0007  # 约1分钟
export JWT_ACCESS_TOKEN_EXPIRES_HOURS=0.0083  # 约30秒
```

## 安全建议

1. **生产环境**: 建议refresh token过期时间不超过7天
2. **敏感系统**: 建议refresh token过期时间设为1-3天
3. **定期轮换**: 建议定期更换JWT密钥
4. **监控异常**: 监控异常的token刷新行为，可能表示安全问题

这个改进大大提高了系统的安全性，同时保持了良好的用户体验。用户会在适当的时间被要求重新认证，避免了永久登录带来的安全风险。