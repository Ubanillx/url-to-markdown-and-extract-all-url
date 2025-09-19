import os
import subprocess
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

# ================== 配置项 ==================
CHROMEDRIVER_PATH = "/usr/local/bin/chromedriver"
MIRROR_BASE_URL = "https://npmmirror.com/mirrors/chromedriver"  # 国内镜像
CHROME_VERSION_CMD = ["google-chrome", "--version"]  # 获取版本命令


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


def download_chromedriver(version):
    """从国内镜像下载指定版本的 chromedriver"""
    zip_file = "chromedriver-linux64.zip"
    download_url = f"{MIRROR_BASE_URL}/{version}/{zip_file}"

    print(f"🔍 尝试从镜像下载: {download_url}")
    
    try:
        response = requests.get(f"{MIRROR_BASE_URL}/{version}/", timeout=10)
        if response.status_code != 200:
            raise Exception("版本在镜像中不存在")
    except:
        print("❌ 镜像中未找到该版本，请尝试升级 Chrome 或手动下载")
        raise FileNotFoundError(f"未找到版本 {version} 的驱动")

    # 下载 zip 包
    with open(zip_file, "wb") as f:
        print("⏬ 正在下载 chromedriver...")
        r = requests.get(download_url, stream=True)
        r.raise_for_status()
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
    print("✅ 下载完成")


def install_chromedriver():
    """解压并安装 chromedriver 到系统路径"""
    print("📦 解压并安装 chromedriver...")
    os.system("unzip -o chromedriver-linux64.zip")
    os.system(f"sudo mv chromedriver {CHROMEDRIVER_PATH}")
    os.system(f"sudo chmod +x {CHROMEDRIVER_PATH}")
    os.system("rm -f chromedriver-linux64.zip")
    print(f"✅ chromedriver 已安装到 {CHROMEDRIVER_PATH}")


def ensure_chromedriver():
    """主函数：确保 chromedriver 存在"""
    if os.path.exists(CHROMEDRIVER_PATH):
        print(f"🟢 已检测到 chromedriver: {CHROMEDRIVER_PATH}")
        return

    try:
        chrome_version = get_chrome_version()
        download_chromedriver(chrome_version)
        install_chromedriver()
    except Exception as e:
        print("💥 自动安装失败:", str(e))
        print("👉 请手动下载并安装: https://npmmirror.com/mirrors/chromedriver")
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