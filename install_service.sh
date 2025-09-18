#!/bin/bash

# URL to Markdown and Extract URL - 系统服务安装脚本
# 作者: Assistant
# 描述: 安装systemd服务文件并配置系统服务

set -e

# 配置变量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="url-to-markdown"
SERVICE_FILE="${SERVICE_NAME}.service"
SYSTEMD_DIR="/etc/systemd/system"
PROJECT_DIR="$SCRIPT_DIR"
LOG_DIR="/var/log/${SERVICE_NAME}"

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
        print_info "请使用: sudo $0"
        exit 1
    fi
}

# 检查systemd是否可用
check_systemd() {
    if ! command -v systemctl &> /dev/null; then
        print_error "systemd未安装或不可用"
        exit 1
    fi
    
    print_success "检测到systemd"
}

# 检查服务文件是否存在
check_service_file() {
    if [ ! -f "$SCRIPT_DIR/$SERVICE_FILE" ]; then
        print_error "服务文件不存在: $SCRIPT_DIR/$SERVICE_FILE"
        exit 1
    fi
    
    print_success "找到服务文件: $SERVICE_FILE"
}

# 更新服务文件中的路径
update_service_file() {
    print_info "更新服务文件中的路径..."
    
    # 创建临时服务文件
    local temp_service="/tmp/${SERVICE_FILE}.tmp"
    
    # 替换服务文件中的路径
    sed "s|/Users/ubanillx/Code/URL_to_markdown_and_extract_url|$PROJECT_DIR|g" \
        "$SCRIPT_DIR/$SERVICE_FILE" > "$temp_service"
    
    # 检查conda路径并更新
    local conda_path=""
    if [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
        conda_path="/opt/miniconda3"
    elif [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
        conda_path="/opt/anaconda3"
    elif [ -f "/usr/local/miniconda3/etc/profile.d/conda.sh" ]; then
        conda_path="/usr/local/miniconda3"
    elif [ -f "/usr/local/anaconda3/etc/profile.d/conda.sh" ]; then
        conda_path="/usr/local/anaconda3"
    else
        print_warning "未找到conda安装路径，请手动编辑服务文件"
    fi
    
    if [ -n "$conda_path" ]; then
        sed -i "s|/opt/miniconda3|$conda_path|g" "$temp_service"
        print_success "更新conda路径为: $conda_path"
    fi
    
    echo "$temp_service"
}

# 安装服务文件
install_service_file() {
    local temp_service="$1"
    
    print_info "安装服务文件到 $SYSTEMD_DIR..."
    
    # 备份现有服务文件
    if [ -f "$SYSTEMD_DIR/$SERVICE_FILE" ]; then
        print_info "备份现有服务文件..."
        cp "$SYSTEMD_DIR/$SERVICE_FILE" "$SYSTEMD_DIR/${SERVICE_FILE}.backup.$(date +%Y%m%d_%H%M%S)"
    fi
    
    # 复制服务文件
    cp "$temp_service" "$SYSTEMD_DIR/$SERVICE_FILE"
    chmod 644 "$SYSTEMD_DIR/$SERVICE_FILE"
    
    print_success "服务文件已安装"
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
    
    # 确保项目目录权限正确
    chmod 755 "$PROJECT_DIR"
    print_success "设置项目目录权限: $PROJECT_DIR"
}

# 重新加载systemd配置
reload_systemd() {
    print_info "重新加载systemd配置..."
    systemctl daemon-reload
    print_success "systemd配置已重新加载"
}

# 启用服务
enable_service() {
    print_info "启用服务..."
    systemctl enable "$SERVICE_NAME"
    print_success "服务已启用"
}

# 显示服务状态
show_status() {
    print_info "服务状态:"
    systemctl status "$SERVICE_NAME" --no-pager || true
    
    echo
    print_info "服务管理命令:"
    echo "  启动服务: systemctl start $SERVICE_NAME"
    echo "  停止服务: systemctl stop $SERVICE_NAME"
    echo "  重启服务: systemctl restart $SERVICE_NAME"
    echo "  查看状态: systemctl status $SERVICE_NAME"
    echo "  查看日志: journalctl -u $SERVICE_NAME -f"
    echo "  禁用服务: systemctl disable $SERVICE_NAME"
}

# 卸载服务
uninstall_service() {
    print_info "卸载服务..."
    
    # 停止服务
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        print_info "停止服务..."
        systemctl stop "$SERVICE_NAME"
    fi
    
    # 禁用服务
    if systemctl is-enabled --quiet "$SERVICE_NAME"; then
        print_info "禁用服务..."
        systemctl disable "$SERVICE_NAME"
    fi
    
    # 删除服务文件
    if [ -f "$SYSTEMD_DIR/$SERVICE_FILE" ]; then
        print_info "删除服务文件..."
        rm -f "$SYSTEMD_DIR/$SERVICE_FILE"
    fi
    
    # 重新加载systemd配置
    systemctl daemon-reload
    
    print_success "服务已卸载"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  install     安装系统服务 (默认)"
    echo "  uninstall   卸载系统服务"
    echo "  status      显示服务状态"
    echo "  help        显示此帮助信息"
    echo
    echo "安装后管理命令:"
    echo "  systemctl start $SERVICE_NAME      # 启动服务"
    echo "  systemctl stop $SERVICE_NAME       # 停止服务"
    echo "  systemctl restart $SERVICE_NAME    # 重启服务"
    echo "  systemctl status $SERVICE_NAME     # 查看状态"
    echo "  journalctl -u $SERVICE_NAME -f     # 实时查看日志"
    echo "  systemctl enable $SERVICE_NAME     # 开机自启"
    echo "  systemctl disable $SERVICE_NAME    # 禁用开机自启"
}

# 主函数
main() {
    case "${1:-install}" in
        install)
            echo "=========================================="
            echo "  安装 $SERVICE_NAME 系统服务"
            echo "=========================================="
            echo
            
            check_root
            check_systemd
            check_service_file
            
            # 更新服务文件路径
            local temp_service=$(update_service_file)
            
            # 安装服务
            install_service_file "$temp_service"
            create_directories
            reload_systemd
            enable_service
            
            # 清理临时文件
            rm -f "$temp_service"
            
            echo
            print_success "服务安装完成！"
            show_status
            ;;
        uninstall)
            echo "=========================================="
            echo "  卸载 $SERVICE_NAME 系统服务"
            echo "=========================================="
            echo
            
            check_root
            uninstall_service
            print_success "服务卸载完成！"
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "未知选项: $1"
            echo
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
