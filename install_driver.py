import os
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ================== 配置项 ==================
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
CHROME_VERSION_CMD = ["google-chrome", "--version"]  # 获取版本命令

# 多个下载源配置
DOWNLOAD_SOURCES = [
    {
        "name": "npmmirror镜像",
        "base_url": "https://npmmirror.com/mirrors/chromedriver",
        "file_pattern": "{version}/chromedriver-linux64.zip"
    },
    {
        "name": "官方源",
        "base_url": "https://chromedriver.storage.googleapis.com",
        "file_pattern": "{version}/chromedriver_linux64.zip"
    },
    {
        "name": "Taobao镜像",
        "base_url": "https://npm.taobao.org/mirrors/chromedriver",
        "file_pattern": "{version}/chromedriver-linux64.zip"
    }
]


def get_chrome_version():
    """获取已安装 Chrome 浏览器的版本号"""
    try:
        result = subprocess.run(CHROME_VERSION_CMD, capture_output=True, text=True, check=True)
        version_line = result.stdout.strip()
        # 示例输出: "Google Chrome 129.0.6668.58"
        version = version_line.split()[-1]
        print(f"✅ Chrome 版本: {version}")
        return version
    except Exception as e:
        print("❌ 未安装 Google Chrome 或无法执行 --version")
        print("请先安装 Chrome: https://www.google.com/chrome/")
        raise e


def get_compatible_versions(chrome_version):
    """获取兼容的 chromedriver 版本列表"""
    # 解析主版本号
    major_version = chrome_version.split('.')[0]
    
    # 生成可能的版本列表（主版本号相同，尝试不同的补丁版本）
    compatible_versions = [chrome_version]
    
    # 尝试相近的版本
    version_parts = chrome_version.split('.')
    if len(version_parts) >= 3:
        major, minor, patch = version_parts[0], version_parts[1], version_parts[2]
        
        # 尝试不同的补丁版本（扩大范围）
        for offset in range(1, 11):  # 尝试前后10个版本
            # 向前版本
            new_patch = str(int(patch) + offset)
            compatible_versions.append(f"{major}.{minor}.{new_patch}")
            
            # 向后版本
            if int(patch) > offset:
                new_patch = str(int(patch) - offset)
                compatible_versions.append(f"{major}.{minor}.{new_patch}")
        
        # 尝试不同的次版本号
        for minor_offset in range(1, 3):  # 尝试前后2个次版本
            # 向前次版本
            new_minor = str(int(minor) + minor_offset)
            compatible_versions.append(f"{major}.{new_minor}.{patch}")
            
            # 向后次版本
            if int(minor) > minor_offset:
                new_minor = str(int(minor) - minor_offset)
                compatible_versions.append(f"{major}.{new_minor}.{patch}")
    
    return compatible_versions


def download_chromedriver(version):
    """从多个源下载指定版本的 chromedriver"""
    compatible_versions = get_compatible_versions(version)
    
    for attempt_version in compatible_versions:
        print(f"🔍 尝试版本: {attempt_version}")
        
        for source in DOWNLOAD_SOURCES:
            try:
                download_url = f"{source['base_url']}/{source['file_pattern'].format(version=attempt_version)}"
                print(f"📡 尝试从 {source['name']} 下载: {download_url}")
                
                # 先检查URL是否存在
                response = requests.head(download_url, timeout=10)
                if response.status_code == 200:
                    print(f"✅ 找到可用版本 {attempt_version} 在 {source['name']}")
                    
                    # 下载文件
                    zip_file = "chromedriver-linux64.zip"
                    with open(zip_file, "wb") as f:
                        print("⏬ 正在下载 chromedriver...")
                        r = requests.get(download_url, stream=True, timeout=30)
                        r.raise_for_status()
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    print("✅ 下载完成")
                    return attempt_version
                    
            except Exception as e:
                print(f"❌ {source['name']} 下载失败: {str(e)}")
                continue
    
    # 所有源都失败
    raise FileNotFoundError(f"未找到兼容版本 {version} 的 chromedriver")


def install_chromedriver():
    """解压并安装 chromedriver 到系统路径"""
    print("📦 解压并安装 chromedriver...")
    os.system("unzip -o chromedriver-linux64.zip")
    os.system(f"sudo mv chromedriver {CHROMEDRIVER_PATH}")
    os.system(f"sudo chmod +x {CHROMEDRIVER_PATH}")
    os.system("rm -f chromedriver-linux64.zip")
    print(f"✅ chromedriver 已安装到 {CHROMEDRIVER_PATH}")


def print_compatibility_info():
    """打印Chrome和ChromeDriver版本兼容性信息"""
    print("📋 Chrome 和 ChromeDriver 版本兼容性说明:")
    print("   • Chrome 和 ChromeDriver 的主版本号必须完全匹配")
    print("   • 次版本号可以有一定差异，但建议使用相近版本")
    print("   • 补丁版本号可以不同，但差异不应过大")
    print("   • 本脚本会自动尝试多个相近版本以确保兼容性")
    print("   • 如果自动安装失败，请手动下载对应版本")
    print()

def ensure_chromedriver():
    """主函数：确保 chromedriver 存在"""
    if os.path.exists(CHROMEDRIVER_PATH):
        print(f"🟢 已检测到 chromedriver: {CHROMEDRIVER_PATH}")
        return

    print_compatibility_info()
    
    try:
        chrome_version = get_chrome_version()
        downloaded_version = download_chromedriver(chrome_version)
        install_chromedriver()
        print(f"🎉 成功安装 chromedriver 版本: {downloaded_version}")
        print(f"✅ Chrome 版本: {chrome_version}")
        print(f"✅ ChromeDriver 版本: {downloaded_version}")
        print("🔗 版本兼容性检查通过！")
    except Exception as e:
        print("💥 自动安装失败:", str(e))
        print("👉 请手动下载并安装:")
        print("   - 官方源: https://chromedriver.chromium.org/downloads")
        print("   - 镜像源: https://npmmirror.com/mirrors/chromedriver")
        print("   - 确保下载的版本与你的Chrome版本兼容")
        raise


def main():
    """主程序：启动浏览器测试"""
    ensure_chromedriver()

    # 设置 Chrome 选项
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--headless")  # 可选：无头模式（后台运行）

    # 启动 WebDriver
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        driver.get("https://www.baidu.com")
        print("🎉 浏览器成功启动！标题:", driver.title)
    finally:
        driver.quit()


if __name__ == "__main__":
    main()