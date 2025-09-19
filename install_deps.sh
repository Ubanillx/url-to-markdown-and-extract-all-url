#!/bin/bash

# URL to Markdown and Extract URL - 依赖安装脚本
# 作者: Assistant
# 描述: 使用conda创建环境并安装所有依赖

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

# 初始化conda
init_conda() {
    print_info "初始化conda环境..."
    
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
    
    print_success "Conda初始化完成"
}

# 检查环境是否存在
check_environment() {
    local env_name="url-to-markdown"
    
    if conda env list | grep -q "^${env_name} "; then
        return 0
    else
        return 1
    fi
}

# 创建conda环境
create_environment() {
    local env_name="url-to-markdown"
    
    print_info "创建conda环境: ${env_name}"
    
    if [ -f "environment.yml" ]; then
        print_info "使用environment.yml创建环境..."
        conda env create -f environment.yml
        if [ $? -eq 0 ]; then
            print_success "环境创建成功"
        else
            print_error "环境创建失败"
            return 1
        fi
    else
        print_error "未找到environment.yml文件"
        return 1
    fi
}

# 激活环境
activate_environment() {
    local env_name="url-to-markdown"
    
    print_info "激活conda环境: ${env_name}"
    conda activate "${env_name}"
    
    if [ $? -eq 0 ]; then
        print_success "环境激活成功"
        return 0
    else
        print_error "环境激活失败"
        return 1
    fi
}

# 更新环境（如果已存在）
update_environment() {
    local env_name="url-to-markdown"
    
    print_info "更新conda环境: ${env_name}"
    
    if [ -f "environment.yml" ]; then
        print_info "使用environment.yml更新环境..."
        conda env update -f environment.yml
        if [ $? -eq 0 ]; then
            print_success "环境更新成功"
        else
            print_error "环境更新失败"
            return 1
        fi
    else
        print_error "未找到environment.yml文件"
        return 1
    fi
}




# 验证安装
verify_installation() {
    print_info "验证安装..."
    
    # 检查Python版本
    python_version=$(python --version 2>&1)
    print_info "Python版本: $python_version"
    
    # 检查关键包
    local packages=(
        "fastapi"
        "uvicorn"
        "pydantic"
        "requests"
        "beautifulsoup4"
        "lxml"
    )
    
    for package in "${packages[@]}"; do
        if python -c "import $package" 2>/dev/null; then
            print_success "✓ $package 安装成功"
        else
            print_error "✗ $package 安装失败"
            return 1
        fi
    done
    
    
    print_success "所有依赖验证通过"
}

# 显示环境信息
show_environment_info() {
    local env_name="url-to-markdown"
    
    echo
    print_info "环境信息:"
    echo "  环境名称: $env_name"
    echo "  Python版本: $(python --version 2>&1)"
    echo "  Conda版本: $(conda --version 2>&1)"
    echo "  环境路径: $(conda info --envs | grep "^${env_name} " | awk '{print $2}')"
    echo
}

# 显示使用说明
show_usage_instructions() {
    echo
    print_info "使用说明:"
    echo "  1. 激活环境: conda activate url-to-markdown"
    echo "  2. 启动应用: ./start.sh"
    echo "  3. 或者直接运行: ./start.sh (会自动激活环境)"
    echo
    print_info "API访问地址:"
    echo "  - 服务器: http://localhost:9998"
    echo "  - API文档: http://localhost:9998/docs"
    echo "  - 健康检查: http://localhost:9998/api/v1/health"
    echo
}

# 主函数
main() {
    echo "=========================================="
    echo "  URL to Markdown and Extract URL"
    echo "  依赖安装脚本 (使用Conda)"
    echo "=========================================="
    echo
    
    # 显示系统信息
    print_info "操作系统: $(uname -s)"
    print_info "Shell: $SHELL"
    echo
    
    # 检查conda
    if ! check_conda; then
        print_error "Conda未安装，请先安装Conda"
        print_info "安装建议:"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            print_info "  macOS:"
            print_info "    1. 使用Homebrew: brew install miniconda"
            print_info "    2. 从官网下载: https://docs.conda.io/en/latest/miniconda.html"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            print_info "  Linux:"
            print_info "    1. 下载安装脚本: wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh"
            print_info "    2. 运行安装: bash Miniconda3-latest-Linux-x86_64.sh"
        fi
        exit 1
    fi
    
    print_success "检测到Conda安装"
    
    # 初始化conda
    init_conda
    
    # 检查环境是否存在
    if check_environment; then
        print_warning "Conda环境 'url-to-markdown' 已存在"
        read -p "是否要更新环境? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            update_environment
        else
            print_info "跳过环境更新"
        fi
    else
        print_info "Conda环境 'url-to-markdown' 不存在，正在创建..."
        create_environment
    fi
    
    # 激活环境
    if ! activate_environment; then
        print_error "无法激活conda环境"
        exit 1
    fi
    
    # 验证安装
    if ! verify_installation; then
        print_error "依赖验证失败"
        exit 1
    fi
    
    # 显示环境信息
    show_environment_info
    
    # 显示使用说明
    show_usage_instructions
    
    print_success "依赖安装完成！"
}

# 显示帮助信息
show_help() {
    echo "用法: $0 [选项]"
    echo
    echo "选项:"
    echo "  -h, --help     显示此帮助信息"
    echo "  -v, --version  显示版本信息"
    echo "  --force        强制重新创建环境"
    echo
    echo "描述:"
    echo "  使用conda创建Python环境并安装所有项目依赖"
    echo "  环境名称: url-to-markdown"
    echo "  Python版本: 3.11"
    echo
    echo "依赖包:"
    echo "  - FastAPI (Web框架)"
    echo "  - Uvicorn (ASGI服务器)"
    echo "  - Pydantic (数据验证)"
    echo "  - Requests (HTTP客户端)"
    echo "  - BeautifulSoup4 (HTML解析)"
    echo "  - LXML (XML/HTML解析器)"
    echo
}

# 显示版本信息
show_version() {
    echo "URL to Markdown and Extract URL - 依赖安装脚本 v1.0.0"
}

# 强制重新创建环境
force_recreate() {
    local env_name="url-to-markdown"
    
    print_warning "强制重新创建环境..."
    
    if check_environment; then
        print_info "删除现有环境: $env_name"
        conda env remove -n "$env_name" -y
    fi
    
    create_environment
    activate_environment
    verify_installation
    show_environment_info
    show_usage_instructions
    
    print_success "环境重新创建完成！"
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
    --force)
        # 检查conda
        if ! check_conda; then
            print_error "Conda未安装，请先安装Conda"
            exit 1
        fi
        init_conda
        force_recreate
        ;;
    *)
        main "$@"
        ;;
esac
