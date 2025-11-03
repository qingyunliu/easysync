# 测试指南

## 测试结构

```
tests/
├── __init__.py
├── conftest.py              # pytest配置和fixtures
├── test_auth.py            # 认证相关测试
├── test_utils.py         # 工具函数测试
├── test_api_integration.py # API集成测试
└── README.md             # 本文档
```

## 运行测试

### 安装测试依赖

```bash
pip install -r requirements-dev.txt
```

### 运行所有测试

```bash
# 运行所有测试
pytest

# 运行并显示覆盖率
pytest --cov=backend --cov-report=html

# 运行特定标记的测试
pytest -m unit          # 只运行单元测试
pytest -m integration  # 只运行集成测试
pytest -m api          # 只运行API测试
pytest -m auth         # 只运行认证相关测试
```

### 运行特定测试文件

```bash
pytest tests/test_auth.py
pytest tests/test_utils.py
```

### 运行特定测试函数

```bash
pytest tests/test_auth.py::TestUserModel::test_create_user
```

## 测试标记

使用 `@pytest.mark` 装饰器标记测试：

- `@pytest.mark.unit` - 单元测试
- `@pytest.mark.integration` - 集成测试
- `@pytest.mark.api` - API端点测试
- `@pytest.mark.slow` - 慢速测试
- `@pytest.mark.auth` - 认证相关测试
- `@pytest.mark.db` - 数据库相关测试

## 测试覆盖率

目标覆盖率：70%+

查看覆盖率报告：

```bash
# HTML报告
pytest --cov=backend --cov-report=html
open htmlcov/index.html

# 终端报告
pytest --cov=backend --cov-report=term-missing
```

## Fixtures

### app
Flask应用实例，自动创建和清理数据库。

### client
测试客户端，用于发送HTTP请求。

### test_user
创建测试用户，测试完成后自动清理。

### admin_user
创建管理员用户，测试完成后自动清理。

### auth_headers
获取认证头（需要mock验证码）。

## 编写新测试

### 单元测试示例

```python
@pytest.mark.unit
class TestMyFunction:
    def test_my_function_success(self, app):
        # 测试代码
        pass
```

### API测试示例

```python
@pytest.mark.api
@pytest.mark.integration
def test_api_endpoint(client, auth_headers):
    response = client.get('/api/endpoint', headers=auth_headers)
    assert response.status_code == 200
```

## 注意事项

1. 所有测试使用独立的测试数据库（SQLite内存数据库）
2. 每个测试自动清理数据库
3. 认证测试需要mock验证码验证
4. 测试不应依赖外部服务（如真实数据库、API等）

## CI/CD集成

在CI/CD中运行测试：

```yaml
# .github/workflows/test.yml 示例
- name: Run tests
  run: |
    pip install -r requirements-dev.txt
    pytest --cov=backend --cov-report=xml
```

