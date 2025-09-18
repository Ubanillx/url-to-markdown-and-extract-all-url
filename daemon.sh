#!/bin/bash

# URL to Markdown and Extract URL - Linux后台启动脚本
# 作者: Assistant
# 描述: 用于在Linux系统上后台运行FastAPI服务器
# 支持: start, stop, restart, status, logs 操作

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="url-to-markdown"
APP_NAME="URL to Markdown and Extract URL"
PID_FILE="/var/run/${PROJECT_NAME}.pid"
LOG_DIR="/var/log/${PROJECT_NAME}"
LOG_FILE="${LOG_DIR}/app.log"
ERROR_LOG_FILE="${LOG_DIR}/error.log"
HOST="0.0.0.0"
PORT="9998"
CONDA_ENV="url-to-markdown"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否为root用户
check_root() {
    if [ "$EUID" -ne 0 ]; then
        print_error "此脚本需要root权限运行"
        print_info "请使用: sudo $0 $@"
        exit 1
    fi
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."
    
    # 创建日志目录
    if [ ! -d "$LOG_DIR" ]; then
        mkdir -p "$LOG_DIR"
        chmod 755 "$LOG_DIR"
        print_success "创建日志目录: $LOG_DIR"
    fi
    
    # 创建PID文件目录
    local pid_dir=$(dirname "$PID_FILE")
    if [ ! -d "$pid_dir" ]; then
        mkdir -p "$pid_dir"
        chmod 755 "$pid_dir"
        print_success "创建PID目录: $pid_dir"
    fi
}

# 检查conda是否安装
check_conda() {
    if command -v conda &> /dev/null; then
        return 0
    fi
    
    # 检查常见的conda安装路径
    local conda_paths=(
        "/opt/miniconda3/bin/conda"
        "/opt/anaconda3/bin/conda"
        "/usr/local/miniconda3/bin/conda"
        "/usr/local/anaconda3/bin/conda"
        "/home/$(logname)/miniconda3/bin/conda"
        "/home/$(logname)/anaconda3/bin/conda"
    )
    
    for path in "${conda_paths[@]}"; do
        if [ -f "$path" ]; then
            export PATH="$(dirname "$path"):$PATH"
            return 0
        fi
    done
    
    return 1
}

# 激活conda环境
activate_environment() {
    print_info "激活conda环境: ${CONDA_ENV}"
    
    # 初始化conda
    if [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
        source "/opt/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
        source "/opt/anaconda3/etc/profile.d/conda.sh"
    elif [ -f "/usr/local/miniconda3/etc/profile.d/conda.sh" ]; then
        source "/usr/local/miniconda3/etc/profile.d/conda.sh"
    elif [ -f "/usr/local/anaconda3/etc/profile.d/conda.sh" ]; then
        source "/usr/local/anaconda3/etc/profile.d/conda.sh"
    else
        # 尝试使用conda init
        eval "$(conda shell.bash hook)"
    fi
    
    # 激活环境
    conda activate "${CONDA_ENV}"
    
    if [ $? -eq 0 ]; then
        print_success "环境激活成功"
        return 0
    else
        print_error "环境激活失败"
        return 1
    fi
}

# 检查进程是否运行
is_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            return 0
        else
            # PID文件存在但进程不存在，删除PID文件
            rm -f "$PID_FILE"
            return 1
        fi
    else
        return 1
    fi
}

# 启动服务
start_service() {
    print_info "启动 ${APP_NAME} 服务..."
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_warning "服务已在运行 (PID: $pid)"
        return 0
    fi
    
    # 切换到项目目录
    cd "$SCRIPT_DIR"
    
    # 检查应用文件
    if [ ! -f "app/main.py" ]; then
        print_error "未找到app/main.py文件"
        return 1
    fi
    
    # 检查conda环境
    if ! check_conda; then
        print_error "Conda未安装或未找到"
        return 1
    fi
    
    # 激活环境
    if ! activate_environment; then
        print_error "无法激活conda环境"
        return 1
    fi
    
    # 启动服务
    print_info "启动服务器在 ${HOST}:${PORT}..."
    
    # 使用nohup在后台启动服务
    nohup python -m uvicorn app.main:app \
        --host "${HOST}" \
        --port "${PORT}" \
        --workers 1 \
        --access-log \
        --log-level info \
        > "$LOG_FILE" 2> "$ERROR_LOG_FILE" &
    
    local pid=$!
    echo $pid > "$PID_FILE"
    
    # 等待服务启动
    sleep 3
    
    if is_running; then
        print_success "服务启动成功 (PID: $pid)"
        print_info "服务器地址: http://${HOST}:${PORT}"
        print_info "API文档: http://${HOST}:${PORT}/docs"
        print_info "日志文件: $LOG_FILE"
        print_info "错误日志: $ERROR_LOG_FILE"
    else
        print_error "服务启动失败"
        rm -f "$PID_FILE"
        return 1
    fi
}

# 停止服务
stop_service() {
    print_info "停止 ${APP_NAME} 服务..."
    
    if ! is_running; then
        print_warning "服务未运行"
        return 0
    fi
    
    local pid=$(cat "$PID_FILE")
    
    # 尝试优雅停止
    print_info "发送TERM信号到进程 $pid..."
    kill -TERM "$pid" 2>/dev/null || true
    
    # 等待进程停止
    local count=0
    while [ $count -lt 10 ]; do
        if ! ps -p "$pid" > /dev/null 2>&1; then
            break
        fi
        sleep 1
        count=$((count + 1))
    done
    
    # 如果进程仍在运行，强制杀死
    if ps -p "$pid" > /dev/null 2>&1; then
        print_warning "进程未响应TERM信号，发送KILL信号..."
        kill -KILL "$pid" 2>/dev/null || true
        sleep 2
    fi
    
    # 检查是否成功停止
    if ! ps -p "$pid" > /dev/null 2>&1; then
        rm -f "$PID_FILE"
        print_success "服务已停止"
    else
        print_error "无法停止服务"
        return 1
    fi
}

# 重启服务
restart_service() {
    print_info "重启 ${APP_NAME} 服务..."
    stop_service
    sleep 2
    start_service
}

# 查看服务状态
show_status() {
    print_info "${APP_NAME} 服务状态:"
    
    if is_running; then
        local pid=$(cat "$PID_FILE")
        print_success "服务正在运行 (PID: $pid)"
        print_info "服务器地址: http://${HOST}:${PORT}"
        print_info "PID文件: $PID_FILE"
        print_info "日志文件: $LOG_FILE"
        
        # 显示进程信息
        echo
        print_info "进程信息:"
        ps -p "$pid" -o pid,ppid,cmd,etime,pcpu,pmem
        
        # 显示端口占用情况
        echo
        print_info "端口占用情况:"
        netstat -tlnp 2>/dev/null | grep ":$PORT " || ss -tlnp 2>/dev/null | grep ":$PORT "
        
    else
        print_warning "服务未运行"
        if [ -f "$PID_FILE" ]; then
            print_warning "发现残留的PID文件: $PID_FILE"
        fi
    fi
}

# 查看日志
show_logs() {
    local lines=${1:-50}
    
    print_info "显示最近 $lines 行日志:"
    echo "=========================================="
    
    if [ -f "$LOG_FILE" ]; then
        tail -n "$lines" "$LOG_FILE"
    else
        print_warning "日志文件不存在: $LOG_FILE"
    fi
    
    echo "=========================================="
    
    if [ -f "$ERROR_LOG_FILE" ] && [ -s "$ERROR_LOG_FILE" ]; then
        print_info "错误日志:"
        echo "=========================================="
        tail -n "$lines" "$ERROR_LOG_FILE"
        echo "=========================================="
    fi
}

# 实时查看日志
follow_logs() {
    print_info "实时查看日志 (按 Ctrl+C 退出):"
    echo "=========================================="
    
    if [ -f "$LOG_FILE" ]; then
        tail -f "$LOG_FILE"
    else
        print_warning "日志文件不存在: $LOG_FILE"
    fi
}

# 显示帮助信息
show_help() {
    echo "用法: $0 {start|stop|restart|status|logs|follow|help}"
    echo
    echo "命令:"
    echo "  start     启动服务"
    echo "  stop      停止服务"
    echo "  restart   重启服务"
    echo "  status    查看服务状态"
    echo "  logs [n]  查看最近n行日志 (默认50行)"
    echo "  follow    实时查看日志"
    echo "  help      显示此帮助信息"
    echo
    echo "配置:"
    echo "  主机地址: $HOST"
    echo "  端口: $PORT"
    echo "  PID文件: $PID_FILE"
    echo "  日志目录: $LOG_DIR"
    echo "  Conda环境: $CONDA_ENV"
    echo
    echo "示例:"
    echo "  sudo $0 start          # 启动服务"
    echo "  sudo $0 stop           # 停止服务"
    echo "  sudo $0 restart        # 重启服务"
    echo "  sudo $0 status         # 查看状态"
    echo "  sudo $0 logs 100       # 查看最近100行日志"
    echo "  sudo $0 follow         # 实时查看日志"
}

# 主函数
main() {
    case "${1:-help}" in
        start)
            check_root
            create_directories
            start_service
            ;;
        stop)
            check_root
            stop_service
            ;;
        restart)
            check_root
            restart_service
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs "${2:-50}"
            ;;
        follow)
            follow_logs
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知命令: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
