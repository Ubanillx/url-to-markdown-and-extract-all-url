# Linux 后台启动脚本使用说明

本项目提供了两种在Linux系统上后台运行服务的方式：

## 方式一：使用 daemon.sh 脚本

### 功能特性
- 支持 start/stop/restart/status/logs/follow 操作
- 自动PID文件管理
- 日志记录到 `/var/log/url-to-markdown/`
- 自动conda环境激活
- 进程监控和状态检查

### 使用方法

1. **给脚本添加执行权限**：
   ```bash
   chmod +x daemon.sh
   ```

2. **启动服务**：
   ```bash
   sudo ./daemon.sh start
   ```

3. **停止服务**：
   ```bash
   sudo ./daemon.sh stop
   ```

4. **重启服务**：
   ```bash
   sudo ./daemon.sh restart
   ```

5. **查看服务状态**：
   ```bash
   sudo ./daemon.sh status
   ```

6. **查看日志**：
   ```bash
   # 查看最近50行日志
   sudo ./daemon.sh logs
   
   # 查看最近100行日志
   sudo ./daemon.sh logs 100
   
   # 实时查看日志
   sudo ./daemon.sh follow
   ```

7. **查看帮助**：
   ```bash
   sudo ./daemon.sh help
   ```

### 配置说明
- **主机地址**: 0.0.0.0 (默认)
- **端口**: 9998 (默认)
- **PID文件**: `/var/run/url-to-markdown.pid`
- **日志目录**: `/var/log/url-to-markdown/`
- **Conda环境**: url-to-markdown

## 方式二：使用 systemd 系统服务

### 功能特性
- 系统级服务管理
- 开机自启动
- 自动重启
- 日志集成到 systemd journal
- 安全配置和资源限制

### 安装步骤

1. **安装系统服务**：
   ```bash
   chmod +x install_service.sh
   sudo ./install_service.sh install
   ```

2. **启动服务**：
   ```bash
   sudo systemctl start url-to-markdown
   ```

3. **设置开机自启**：
   ```bash
   sudo systemctl enable url-to-markdown
   ```

### 服务管理命令

```bash
# 启动服务
sudo systemctl start url-to-markdown

# 停止服务
sudo systemctl stop url-to-markdown

# 重启服务
sudo systemctl restart url-to-markdown

# 查看服务状态
sudo systemctl status url-to-markdown

# 实时查看日志
sudo journalctl -u url-to-markdown -f

# 查看最近日志
sudo journalctl -u url-to-markdown -n 100

# 禁用开机自启
sudo systemctl disable url-to-markdown

# 启用开机自启
sudo systemctl enable url-to-markdown
```

### 卸载服务

```bash
sudo ./install_service.sh uninstall
```

## 环境要求

### 系统要求
- Linux 系统 (Ubuntu, CentOS, RHEL, Debian 等)
- Python 3.7+
- Conda 或 Miniconda

### 依赖检查
脚本会自动检查以下依赖：
- Python 安装
- Conda 环境
- 项目文件完整性

### Conda 环境
确保已创建并配置好 `url-to-markdown` conda 环境：
```bash
conda env create -f environment.yml
# 或
conda create -n url-to-markdown python=3.9
conda activate url-to-markdown
pip install -r requirements.txt
```

## 日志管理

### daemon.sh 日志
- **应用日志**: `/var/log/url-to-markdown/app.log`
- **错误日志**: `/var/log/url-to-markdown/error.log`

### systemd 日志
使用 journalctl 查看日志：
```bash
# 实时查看日志
sudo journalctl -u url-to-markdown -f

# 查看今天的日志
sudo journalctl -u url-to-markdown --since today

# 查看最近100行日志
sudo journalctl -u url-to-markdown -n 100

# 查看错误日志
sudo journalctl -u url-to-markdown -p err
```

## 故障排除

### 常见问题

1. **权限问题**：
   ```bash
   # 确保脚本有执行权限
   chmod +x daemon.sh install_service.sh
   
   # 使用sudo运行
   sudo ./daemon.sh start
   ```

2. **Conda环境问题**：
   ```bash
   # 检查conda环境是否存在
   conda env list
   
   # 重新创建环境
   conda env create -f environment.yml --force
   ```

3. **端口占用问题**：
   ```bash
   # 检查端口占用
   sudo netstat -tlnp | grep :9998
   # 或
   sudo ss -tlnp | grep :9998
   
   # 杀死占用进程
   sudo kill -9 <PID>
   ```

4. **服务启动失败**：
   ```bash
   # 查看详细错误信息
   sudo ./daemon.sh logs
   # 或
   sudo journalctl -u url-to-markdown -n 50
   ```

### 调试模式

如果需要调试，可以手动启动服务：
```bash
# 激活conda环境
conda activate url-to-markdown

# 手动启动服务
python -m uvicorn app.main:app --host 0.0.0.0 --port 9998 --reload
```

## 安全注意事项

1. **文件权限**：确保日志目录和PID文件有正确的权限
2. **网络安全**：默认绑定到 0.0.0.0，请确保防火墙配置正确
3. **用户权限**：服务以root用户运行，请确保系统安全

## 性能优化

1. **工作进程数**：根据CPU核心数调整 `--workers` 参数
2. **内存限制**：在systemd服务文件中调整 `LimitNPROC` 和 `LimitNOFILE`
3. **日志轮转**：配置logrotate管理日志文件大小

## 监控和维护

### 健康检查
```bash
# 检查服务是否响应
curl http://localhost:9998/api/v1/health

# 检查API文档
curl http://localhost:9998/docs
```

### 定期维护
- 定期清理日志文件
- 监控服务状态
- 更新依赖包
- 备份配置文件
