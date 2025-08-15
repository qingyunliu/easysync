# 国际化测试指南

## 测试步骤

### 1. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

### 2. 测试语言切换功能

1. **访问登录页面**

   - 打开浏览器访问 `http://localhost:3000`
   - 检查页面是否显示中文内容

2. **测试语言切换器**

   - 点击头部导航栏的语言切换器（🌐 图标）
   - 选择 "English"
   - 检查页面内容是否切换为英文
   - 再次切换回中文

3. **测试登录页面国际化**

   - 在登录页面测试语言切换
   - 检查表单字段、按钮、错误消息等是否都正确翻译

4. **测试主布局国际化**
   - 登录后进入主页面
   - 检查侧边栏菜单项是否正确翻译
   - 检查用户下拉菜单是否正确翻译
   - 检查问候语是否正确翻译

### 3. 验证功能

#### 登录页面测试项

- [ ] 页面标题：数据同步管理平台 / Data Sync Management Platform
- [ ] 欢迎信息：欢迎登录 / Welcome Back
- [ ] 用户名输入框：用户名 / Username
- [ ] 密码输入框：密码 / Password
- [ ] 验证码输入框：验证码 / Captcha
- [ ] 登录按钮：登录 / Login
- [ ] 注册链接：立即注册 / Register Now
- [ ] 忘记密码链接：忘记密码？ / Forgot Password?

#### 主布局测试项

- [ ] 侧边栏菜单项

  - [ ] 仪表板 / Dashboard
  - [ ] 资源管理 / Resource Management
  - [ ] 运维管理 / Operations Management
  - [ ] 监控告警 / Monitoring & Alerts
  - [ ] 系统管理 / System Management
  - [ ] 个人中心 / Personal Center

- [ ] 用户菜单

  - [ ] 个人资料 / Profile
  - [ ] 退出登录 / Logout

- [ ] 问候语
  - [ ] 早上好 / Good Morning
  - [ ] 中午好 / Good Noon
  - [ ] 下午好 / Good Afternoon
  - [ ] 晚上好 / Good Evening
  - [ ] 深夜好 / Good Night

### 4. 常见问题排查

#### 问题 1：图标导入错误

**错误信息**：`The requested module does not provide an export named 'Globe'`

**解决方案**：

- 使用正确的 Element Plus 图标名称
- 或者使用 emoji 图标作为替代

#### 问题 2：语言切换不生效

**可能原因**：

- 检查 `vue-i18n` 是否正确配置
- 检查语言包是否正确导入
- 检查 `setLocale` 函数是否正确调用

#### 问题 3：部分文本未翻译

**可能原因**：

- 检查是否使用了 `$t()` 或 `t()` 函数
- 检查语言包中是否包含对应的键值
- 检查键名是否正确

### 5. 开发调试

#### 检查当前语言

```javascript
// 在浏览器控制台中
console.log(i18n.global.locale.value);
```

#### 检查语言包内容

```javascript
// 在浏览器控制台中
console.log(i18n.global.getLocaleMessage("zh-CN"));
console.log(i18n.global.getLocaleMessage("en-US"));
```

#### 手动切换语言

```javascript
// 在浏览器控制台中
i18n.global.locale.value = "en-US";
```

### 6. 性能测试

1. **语言切换响应时间**

   - 测量语言切换的响应时间
   - 确保切换流畅，无明显延迟

2. **内存使用**

   - 检查语言包加载是否影响内存使用
   - 确保没有内存泄漏

3. **包大小**
   - 检查国际化功能是否显著增加包大小
   - 考虑按需加载语言包

## 测试报告模板

### 测试环境

- 浏览器：Chrome/Firefox/Safari
- 操作系统：Windows/macOS/Linux
- 前端版本：v0.1.0

### 测试结果

- [ ] 语言切换功能正常
- [ ] 所有页面文本正确翻译
- [ ] 响应式布局正常
- [ ] 性能表现良好

### 发现的问题

1. 问题描述
2. 复现步骤
3. 预期结果
4. 实际结果

### 建议改进

1. 改进建议 1
2. 改进建议 2
