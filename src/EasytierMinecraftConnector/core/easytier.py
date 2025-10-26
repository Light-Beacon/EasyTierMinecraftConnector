import platform
import requests
import logging
import os
import zipfile
import subprocess
import time
from subprocess import DEVNULL
from pathlib import Path
#from tqdm import tqdm
import stat


logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

DOWNLOAD_PLATFORM_STRS = {
    ("windows", "x86_64"): "windows-x86_64",
    ("windows", "arm64"): "windows-arm64",
    ("windows", "i686"): "windows-i686",
    ("linux", "x86_64"): "linux-x86_64",
    ("linux", "aarch64"): "linux-aarch64",
    ("linux", "arm"): "linux-arm",
    ("linux", "armhf"): "linux-armhf",
    ("linux", "armv7"): "linux-armv7",
    ("linux", "armv7hf"): "linux-armv7hf",
    ("linux", "mips"): "linux-mips",
    ("linux", "mipsel"): "linux-mipsel",
    ("darwin", "x86_64"): "macos-x86_64",
    ("darwin", "arm64"): "macos-aarch64",
}

class PlatformNotSupportedError(Exception):
    pass

class EasyTierNotInstalledError(Exception):
    pass

class EasyTierActionError(Exception):
    pass

class EasyTierInstaller:
    @classmethod
    def get_latest_version(cls) -> str:
        """获取 EasyTier 的最新版本号"""
        logger.info("获取 EasyTier 的最新版本信息...")
        try:
            response = requests.get("https://api.github.com/repos/EasyTier/EasyTier/releases/latest", timeout=10)
            response.raise_for_status()
            data = response.json()
            result = data["tag_name"]
            logger.info("EasyTier 最新版本:%s", result)
        except requests.RequestException as e:
            logger.error("获取最新版本信息失败: %s，使用默认版本号", e)
            return "v2.4.5"  # 返回一个默认版本号
        return result

    @classmethod
    def generate_platform_str(cls) -> str:
        """生成平台字符串"""
        system = platform.system().lower()
        machine = platform.machine().lower()
        logger.info("系统架构: %s %s", system, machine)
        architecture_str = DOWNLOAD_PLATFORM_STRS.get((system, machine))
        if architecture_str is None:
            raise PlatformNotSupportedError(f"EasyTier 不支持的平台: {system} {machine}")
        return architecture_str

    @classmethod
    def generate_download_link(cls, use_mirror: bool = False) -> str:
        """生成 EasyTier 的下载链接"""
        architecture_str = cls.generate_platform_str()
        latest_version = cls.get_latest_version()
        url = f"https://github.com/EasyTier/EasyTier/releases/download/{latest_version}/easytier-{architecture_str}-{latest_version}.zip"
        if use_mirror:
            url = "https://ghfast.top/" + url
        return url

    @classmethod
    def download(cls):
        """下载 EasyTier"""
        url = cls.generate_download_link()
        logger.info("下载链接: %s", url)
        print("正在下载...请稍后")
        response = requests.get(url, stream=True, timeout=10)
        total_size = int(response.headers.get('content-length', 0))
        with open("easytier.zip", "wb") as f:
            f.write(response.content)
            #for data in tqdm(response.iter_content(chunk_size=1024), position=0, total=total_size // 1024, unit="KB"):
            #    f.write(data)
        logger.info("下载完成！")

    @classmethod
    def unzip(cls):
        """解压下载的 EasyTier"""
        logger.info("正在解压...请稍后")
        with zipfile.ZipFile("easytier.zip", "r") as zip_ref:
            zip_ref.extractall("easytier")

        # 在类 Unix 系统上确保可执行文件有执行权限（zip 解压有时不保留 exec 位）
        if platform.system().lower() != "windows":
            logger.info("为解压后的可执行文件设置执行权限")
            exec_names = {"easytier-core", "easytier-cli", "easytier-core.exe", "easytier-cli.exe"}
            for root, _, files in os.walk("easytier"):
                for name in files:
                    if name in exec_names or (name.startswith("easytier-") and ("core" in name or "cli" in name)):
                        path = os.path.join(root, name)
                        try:
                            st = os.stat(path)
                            os.chmod(path, st.st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
                            logger.debug("设置执行权限: %s", path)
                        except OSError as e:
                            logger.warning("无法设置执行权限 %s: %s", path, e)

        logger.info("解压完成！")

    @classmethod
    def remove_zip(cls):
        """删除下载的 EasyTier zip 文件"""
        try:
            os.remove("easytier.zip")
            logger.info("已删除下载的 EasyTier zip 文件")
        except OSError as e:
            logger.warning("删除 EasyTier zip 文件时出错: %s", e)

    @classmethod
    def install(cls):
        """下载并解压 EasyTier"""
        cls.download()
        cls.unzip()
        cls.remove_zip()

    @classmethod
    def get_path(cls) -> Path:
        """获取 EasyTier 的安装路径"""
        if not os.path.exists("easytier"):
            raise EasyTierNotInstalledError()
        dire = Path("easytier") / ("easytier-" + cls.generate_platform_str())
        if not dire.exists():
            raise EasyTierNotInstalledError()
        if platform.system().lower() == "windows":
            if not (dire / "easytier-core.exe").exists() or not (dire / "easytier-cli.exe").exists():
                raise EasyTierNotInstalledError()
        else:
            if not (dire / "easytier-core").exists() or not (dire / "easytier-cli").exists():
                raise EasyTierNotInstalledError()
        return dire
    

class EasyTier:
    def __init__(self):
        self._core_process = None
        try:
            easytier_dire = EasyTierInstaller.get_path()
        except EasyTierNotInstalledError:
            logger.warning("EasyTier 未安装，正在安装...")
            try:
                EasyTierInstaller.install()
            except (requests.RequestException, IOError, zipfile.BadZipFile, OSError) as e:
                logger.error("安装 EasyTier 失败: %s", e)
                exit(1)
            easytier_dire = EasyTierInstaller.get_path()
        self._easytier_core_path = easytier_dire / ("easytier-core.exe" if platform.system().lower() == "windows" else "easytier-core")
        self._easytier_cli_path = easytier_dire / ("easytier-cli.exe" if platform.system().lower() == "windows" else "easytier-cli")

    #region 核心进程管理
    def start_core(self, args: list) -> subprocess.Popen:
        """在后台启动 easytier-core，返回 Popen 对象"""
        if self._core_process and self._core_process.poll() is None:
            logger.info("EasyTier 核心已在运行 (pid=%s)", self._core_process.pid)
            return self._core_process

        cmd = [str(self._easytier_core_path)] + args
        logger.info("后台启动 EasyTier 核心: %s", " ".join(cmd))
        # 在不同平台上使用合适的参数使进程在后台并独立于父进程会话
        if platform.system().lower() == "windows":
            # CREATE_NEW_PROCESS_GROUP 在 Windows 上有用；在运行时安全地获取常量
            creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL, creationflags=creationflags)
        else:
            # start_new_session=True 在 POSIX 上分离会话
            proc = subprocess.Popen(cmd, stdout=DEVNULL, stderr=DEVNULL, start_new_session=True)

        self._core_process = proc
        logger.info("EasyTier 核心已启动，pid=%s", proc.pid)
        time.sleep(0.5) # 确保进程有时间启动，避免 cli 命令执行失败
        return proc

    def stop_core(self, timeout: float = 5.0) -> bool:
        """尝试通过 easytier-cli 停止核心；超时或失败则强制结束。

        返回 True 表示已停止或确认停止，False 表示仍然运行（最后尝试强制结束）。
        """
        logger.info("请求停止 EasyTier 核心")

        # 仅针对我们启动并记录的子进程采取动作
        if not self._core_process:
            logger.info("没有记录到核心子进程，跳过停止")
            return True

        if self._core_process.poll() is None:
            logger.info("核心仍在运行，尝试优雅终止 pid=%s", self._core_process.pid)
            try:
                self._core_process.terminate()
                try:
                    self._core_process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    logger.warning("优雅终止超时，强制 kill pid=%s", self._core_process.pid)
                    try:
                        self._core_process.kill()
                        self._core_process.wait(timeout=2)
                    except (OSError, ValueError) as e:
                        logger.exception("强制 kill 失败: %s", e)
            except (OSError, ValueError) as e:
                logger.exception("尝试终止/杀死核心时出错: %s", e)
        else:
            logger.info("核心已退出，退出码=%s", self._core_process.returncode)

        # 最后确认
        if self._core_process and self._core_process.poll() is None:
            logger.error("无法停止 EasyTier 核心 (pid=%s)", self._core_process.pid)
            return False

        logger.info("EasyTier 核心已停止")
        return True
    #endregion
    def __del__(self):
        """析构函数，结束 easytier-core 进程"""
        logger.info("正在结束 EasyTier 核心进程...")
        try:
            stopped = self.stop_core()
            if not stopped:
                logger.warning("尝试停止 EasyTier 核心未成功")
        except (OSError, FileNotFoundError, subprocess.SubprocessError) as e:
            logger.exception("析构时停止 EasyTier 核心出现异常: %s", e)

    def add_port_forwarding(self, protocol: str, bind_address: str, dest_address: str):
        """添加端口转发规则"""
        logger.info("添加端口转发: %s %s %s", protocol, bind_address, dest_address)
        cmd = [
            str(self._easytier_cli_path),
            "port-forward",
            "add",
            protocol,
            bind_address,
            dest_address,
        ]
        try:
            # 捕获输出，若 stderr 有内容则记录为 error
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=False)
            if proc.returncode != 0:
                logger.error("添加端口转发时出现错误: %s", proc.stderr.strip())
                #raise EasyTierActionError()
        except FileNotFoundError as e:
            logger.error("找不到 easytier-cli 可执行文件: %s", e)
        except OSError as e:
            logger.exception("执行 easytier-cli 时发生系统错误: %s", e)


if __name__ == "__main__":
    easytier = EasyTier()