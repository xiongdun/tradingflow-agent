# backend/plugins/loader.py
# 插件加载器 — 支持 5 种来源：本地目录 / Git / pip / 远程注册中心 / HTTP URL

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import httpx
from loguru import logger

from backend.plugins.manifest import PluginManifest, PLUGINS_DIR
from backend.plugins.registry import plugin_registry

# 使用共享常量，避免重复定义
_PLUGINS_DIR = PLUGINS_DIR
_REPOS_DIR = _PLUGINS_DIR / "repos"
_PKGS_DIR = _PLUGINS_DIR / "packages"
_URL_CACHE_DIR = _PLUGINS_DIR / "url_cache"


class PluginLoadError(Exception):
    """插件加载失败"""
    pass


class PluginLoader:
    """支持 5 种来源的插件加载器"""

    def __init__(self) -> None:
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        for d in [_PLUGINS_DIR, _REPOS_DIR, _PKGS_DIR, _URL_CACHE_DIR]:
            d.mkdir(parents=True, exist_ok=True)

    # ──────────────────── 1. 本地目录 ────────────────────

    def load_from_local(self, path: str | Path) -> PluginManifest:
        """从本地目录加载插件

        目录结构:
            my_plugin/
                manifest.json    # 插件清单（必须）
                __init__.py      # Python 包入口
                ...
        """
        plugin_dir = Path(path).resolve()
        if not plugin_dir.is_dir():
            raise PluginLoadError(f"目录不存在: {plugin_dir}")

        manifest = self._load_manifest(plugin_dir)
        manifest.source = "local"
        manifest.installed_path = str(plugin_dir)

        # 将插件目录添加到 sys.path 以便导入
        parent_dir = str(plugin_dir.parent)
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)

        plugin_registry.register(manifest)
        logger.info(f"[plugin] Loaded from local: {manifest.name} v{manifest.version}")
        return manifest

    # ──────────────────── 2. Git 仓库 ────────────────────

    def load_from_git(self, url: str, ref: str = "main") -> PluginManifest:
        """从 Git 仓库加载插件

        克隆到本地 repos/ 目录，然后作为本地插件加载。
        """
        repo_name = self._git_url_to_name(url)
        repo_dir = _REPOS_DIR / repo_name

        # 清理旧版本
        if repo_dir.exists():
            shutil.rmtree(repo_dir)

        logger.info(f"[plugin] Cloning {url} (ref={ref})...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", ref, url, str(repo_dir)],
                check=True, capture_output=True, timeout=120,
            )
        except subprocess.CalledProcessError as e:
            raise PluginLoadError(f"Git clone failed: {e.stderr.decode()}")
        except FileNotFoundError:
            raise PluginLoadError("git 命令未找到，请安装 Git")

        manifest = self._load_manifest(repo_dir)
        manifest.source = "git"
        manifest.source_url = url
        manifest.installed_path = str(repo_dir)

        # 确保 sys.path
        if str(repo_dir.parent) not in sys.path:
            sys.path.insert(0, str(repo_dir.parent))

        plugin_registry.register(manifest)
        logger.info(f"[plugin] Loaded from git: {manifest.name} v{manifest.version}")
        return manifest

    # ──────────────────── 3. pip 包 ────────────────────

    def load_from_pip(self, package: str, version: str = "") -> PluginManifest:
        """从 PyPI 安装并加载插件

        插件包必须包含 manifest.json（在包根目录或 data/ 目录下）。
        """
        spec = f"{package}=={version}" if version else package
        logger.info(f"[plugin] Installing {spec} via pip...")

        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "--target", str(_PKGS_DIR), spec],
                check=True, capture_output=True, timeout=180,
            )
        except subprocess.CalledProcessError as e:
            raise PluginLoadError(f"pip install failed: {e.stderr.decode()}")

        # 查找 manifest.json
        pkg_dir = _PKGS_DIR / package.replace("-", "_")
        if not pkg_dir.exists():
            pkg_dir = _PKGS_DIR / package
        if not pkg_dir.exists():
            pkg_dir = self._find_package_dir(_PKGS_DIR, package)  # type: ignore[assignment]

        if pkg_dir is None or not pkg_dir.exists():
            raise PluginLoadError(f"安装成功但未找到包目录: {package}")

        assert pkg_dir is not None  # for type checker
        manifest = self._load_manifest(pkg_dir)
        manifest.source = "pip"
        manifest.source_url = spec
        manifest.installed_path = str(pkg_dir)

        if str(_PKGS_DIR) not in sys.path:
            sys.path.insert(0, str(_PKGS_DIR))

        plugin_registry.register(manifest)
        logger.info(f"[plugin] Loaded from pip: {manifest.name} v{manifest.version}")
        return manifest

    # ──────────────────── 4. 远程注册中心 ────────────────────

    def load_from_registry(self, name: str, version: str = "latest",
                           registry_url: str = "") -> PluginManifest:
        """从远程注册中心下载并安装插件

        注册中心 API:
            GET {registry_url}/api/plugins/{name}/download -> ZIP 包
            GET {registry_url}/api/plugins/{name}/versions -> 版本列表
        """
        if not registry_url:
            registry_url = "https://plugins.tradingflow.dev"

        download_url = f"{registry_url.rstrip('/')}/api/plugins/{name}/download"
        if version != "latest":
            download_url += f"?version={version}"

        logger.info(f"[plugin] Downloading {name} from registry...")
        zip_data = self._download_bytes(download_url)
        return self._load_from_zip(zip_data, source="registry", source_url=download_url)

    # ──────────────────── 5. HTTP URL ────────────────────

    def load_from_url(self, url: str) -> PluginManifest:
        """从 HTTP/HTTPS URL 下载并加载插件

        支持两种格式：
        1. ZIP 压缩包（Content-Type: application/zip）
        2. 直接的 manifest.json URL
        """
        logger.info(f"[plugin] Downloading from {url}...")

        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")

        # ZIP 包
        if "zip" in content_type or url.endswith(".zip"):
            return self._load_from_zip(resp.content, source="url", source_url=url)

        # manifest.json
        if "json" in content_type or url.endswith(".json"):
            manifest_data = resp.json()
            manifest = PluginManifest(**manifest_data)
            if manifest.entry_point:
                module_name = manifest.entry_point.split(":")[0]
                module_url = f"{url.rsplit('/', 1)[0]}/{module_name}.py"
                module_data = self._download_bytes(module_url)
                plugin_dir = _PLUGINS_DIR / manifest.name
                plugin_dir.mkdir(parents=True, exist_ok=True)
                (plugin_dir / "manifest.json").write_text(
                    json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                (plugin_dir / f"{module_name}.py").write_bytes(module_data)
                manifest.source = "url"
                manifest.source_url = url
                manifest.installed_path = str(plugin_dir)
                plugin_registry.register(manifest)
                return manifest
            raise PluginLoadError("manifest.json 缺少 entry_point 字段")

        raise PluginLoadError(f"不支持的 Content-Type: {content_type}")

    # ──────────────────── 辅助方法 ────────────────────

    def _load_manifest(self, plugin_dir: Path) -> PluginManifest:
        """从插件目录加载 manifest.json"""
        manifest_path = plugin_dir / "manifest.json"
        if not manifest_path.exists():
            raise PluginLoadError(f"manifest.json 不存在: {manifest_path}")
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
            return PluginManifest(**data)
        except Exception as e:
            raise PluginLoadError(f"manifest.json 解析失败: {e}")

    def _load_from_zip(self, zip_data: bytes, source: str = "", source_url: str = "") -> PluginManifest:
        """从 ZIP 数据加载插件"""
        extract_dir = Path(tempfile.mkdtemp(prefix="plugin_zip_"))
        try:
            with zipfile.ZipFile(BytesIO(zip_data)) as zf:
                # 防止 zip-slip 攻击：验证所有条目路径在目标目录内
                for member in zf.namelist():
                    target = (extract_dir / member).resolve()
                    if not str(target).startswith(str(extract_dir.resolve())):
                        raise PluginLoadError(f"ZIP 包含路径逃逸: {member}")
                zf.extractall(extract_dir)

            manifests = list(extract_dir.rglob("manifest.json"))
            if not manifests:
                raise PluginLoadError("ZIP 包中未找到 manifest.json")
            manifest = self._load_manifest(manifests[0].parent)

            final_dir = _PLUGINS_DIR / manifest.name
            if final_dir.exists():
                shutil.rmtree(final_dir)
            shutil.move(str(manifests[0].parent), str(final_dir))
            manifest.source = source
            manifest.source_url = source_url
            manifest.installed_path = str(final_dir)

            if str(final_dir.parent) not in sys.path:
                sys.path.insert(0, str(final_dir.parent))

            plugin_registry.register(manifest)
            logger.info(f"[plugin] Loaded from {source}: {manifest.name} v{manifest.version}")
            return manifest
        finally:
            if extract_dir.exists():
                shutil.rmtree(extract_dir, ignore_errors=True)

    def _download_bytes(self, url: str) -> bytes:
        """下载二进制数据"""
        with httpx.Client(timeout=60, follow_redirects=True) as client:
            resp = client.get(url)
            resp.raise_for_status()
            return resp.content

    def _git_url_to_name(self, url: str) -> str:
        """将 Git URL 转换为本地目录名"""
        parsed = urlparse(url)
        name = parsed.path.rstrip("/").split("/")[-1]
        if name.endswith(".git"):
            name = name[:-4]
        return name

    def _find_package_dir(self, base: Path, package_name: str) -> Path | None:
        """在 base 目录下查找 pip 安装的包目录"""
        safe_name = package_name.replace("-", "_")
        for candidate in [safe_name, package_name]:
            if (base / candidate).is_dir():
                return base / candidate
        for d in base.iterdir():
            if d.is_dir() and d.name.startswith(safe_name.replace("_", "-")):
                return d
            if d.is_dir() and d.name.startswith(safe_name):
                return d
        return None

    def uninstall(self, name: str) -> bool:
        """卸载插件 — 删除文件并从注册中心移除"""
        manifest = plugin_registry.get(name)
        if not manifest:
            return False
        if manifest.installed_path:
            install_path = Path(manifest.installed_path).resolve()
            if install_path.exists() and install_path.is_relative_to(_PLUGINS_DIR.resolve()):
                shutil.rmtree(install_path, ignore_errors=True)
                logger.info(f"[plugin] Deleted files: {install_path}")
        return plugin_registry.unregister(name)


# 全局单例
plugin_loader = PluginLoader()
