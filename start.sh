#!/bin/bash

# URL to Markdown and Extract URL - 启动脚本
# 作者: Assistant
# 描述: 启动FastAPI服务器

set -e  # 遇到错误时退出

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

# 检查conda是否安装
check_conda() {
    if command -v conda &> /dev/null; then
        return 0
    fi
    
    # 检查常见的conda安装路径
    local conda_paths=(
        "$HOME/miniconda3/bin/conda"
        "$HOME/anaconda3/bin/conda"
        "/opt/miniconda3/bin/conda"
        "/opt/anaconda3/bin/conda"
        "/usr/local/miniconda3/bin/conda"
        "/usr/local/anaconda3/bin/conda"
    )
    
    for path in "${conda_paths[@]}"; do
        if [ -f "$path" ]; then
            export PATH="$(dirname "$path"):$PATH"
            return 0
        fi
    done
    
    return 1
}

# 检查Python是否安装
check_python() {
    if command -v python &> /dev/null; then
        return 0
    else
        return 1
    fi
}

# 检查环境是否存在
check_environment() {
    local env_name="url-to-markdown"
    
    if check_conda; then
        if conda env list | grep -q "^${env_name} "; then
            return 0
        else
            return 1
        fi
    else
        return 1
    fi
}

# 激活conda环境
activate_environment() {
    local env_name="url-to-markdown"
    
    print_info "激活conda环境: ${env_name}"
    
    # 检测shell类型并初始化conda
    if [[ "$SHELL" == *"zsh"* ]]; then
        # zsh (macOS默认)
        if [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
            source "$HOME/miniconda3/etc/profile.d/conda.sh"
        elif [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
            source "$HOME/anaconda3/etc/profile.d/conda.sh"
        elif [ -f "/opt/miniconda3/etc/profile.d/conda.sh" ]; then
            source "/opt/miniconda3/etc/profile.d/conda.sh"
        elif [ -f "/opt/anaconda3/etc/profile.d/conda.sh" ]; then
            source "/opt/anaconda3/etc/profile.d/conda.sh"
        else
            # 尝试使用conda init
            eval "$(conda shell.zsh hook)"
        fi
    else
        # bash
        eval "$(conda shell.bash hook)"
    fi
    
    # 激活环境
    conda activate "${env_name}"
    
    if [ $? -eq 0 ]; then
        print_success "环境激活成功"
        return 0
    else
        print_error "环境激活失败"
        return 1
    fi
}







# 检查应用文件
check_app_files() {
    if [ ! -f "app/main.py" ]; then
        print_error "未找到app/main.py文件"
        exit 1
    fi
    
    print_success "应用文件检查通过"
}

# 启动服务器
start_server() {
    local host=${1:-"0.0.0.0"}
    local port=${2:-"9998"}
    
    print_info "启动FastAPI服务器..."
    print_info "服务器地址: http://${host}:${port}"
    print_info "API文档: http://${host}:${port}/docs"
    print_info "健康检查: http://${host}:${port}/api/v1/health"
    print_info "按 Ctrl+C 停止服务器"
    echo
    
    # 启动uvicorn服务器
    python -m uvicorn app.main:app --reload --host "${host}" --port "${port}"
}

# 主函数
main() {
    echo "=========================================="
    echo "  URL to Markdown and Extract URL"
    echo "  FastAPI 服务器启动脚本"
    echo "=========================================="
    echo
    
    # 显示系统信息
    print_info "操作系统: $(uname -s)"
    print_info "Shell: $SHELL"
    echo
    
    # 检查Python
    if ! check_python; then
        print_error "Python未安装，请先安装Python"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_info "macOS安装Python建议:"
            print_info "1. 使用Homebrew: brew install python"
            print_info "2. 从官网下载: https://www.python.org/downloads/"
        fi
        exit 1
    fi
    
    # 检查conda
    if ! check_conda; then
        print_warning "Conda未安装，将使用系统Python环境"
        print_info "建议安装Conda以获得更好的环境管理"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_info "macOS安装Conda建议:"
            print_info "1. 使用Homebrew: brew install miniconda"
            print_info "2. 从官网下载: https://docs.conda.io/en/latest/miniconda.html"
        fi
    else
        print_success "检测到Conda安装"
        
        # 检查环境
        if ! check_environment; then
            print_warning "Conda环境 'url-to-markdown' 不存在"
            print_info "正在创建环境..."
            if [ -f "environment.yml" ]; then
                conda env create -f environment.yml
                if [ $? -ne 0 ]; then
                    print_error "环境创建失败"
                    exit 1
                fi
            else
                print_error "未找到environment.yml文件，无法创建环境"
                exit 1
            fi
        fi
        
        # 激活环境
        if ! activate_environment; then
            print_error "无法激活conda环境"
            print_info "尝试手动激活环境: conda activate url-to-markdown"
            exit 1
        fi
    fi
    
    # 跳过依赖安装 - 假设依赖已预先安装
    print_info "跳过依赖安装，假设依赖已预先安装"
    
    # 检查应用文件
    check_app_files
    
    # 启动服务器
    start_server "$@"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项] [主机] [端口]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -v, --version  显示版本信息"
    echo
    echo "参数:"
    echo "  主机           服务器主机地址 (默认: 0.0.0.0)"
    echo "  端口           服务器端口 (默认: 9998)"
    echo
    echo "示例:"
    echo "  $0                    # 使用默认设置启动"
    echo "  $0 127.0.0.1 9998    # 在127.0.0.1:9998启动"
    echo "  $0 localhost 9998     # 在localhost:9998启动"
    echo
    echo "macOS特定说明:"
    echo "  - 确保已安装Chrome浏览器"
    echo "  - 确保已安装所有必要的Python依赖"
    echo "  - 如果遇到权限问题，请检查Chrome的访问权限"
}

# 显示版本信息
show_version() {
    echo "URL to Markdown and Extract URL - 启动脚本 v1.0.0"
}

# 解析命令行参数
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    -v|--version)
        show_version
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
