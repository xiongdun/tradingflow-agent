# tests/test_plugin_system.py
# 插件系统全覆盖测试 — manifest / registry / loader / discovery / sandbox / marketplace

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest


# ═══════════════════════════════════════════════════════
#  1. PluginManifest 模型测试
# ═══════════════════════════════════════════════════════

class TestPluginManifest:
    """PluginManifest Pydantic 模型"""

    def _make(self, **kw):
        from backend.plugins.manifest import PluginManifest, PluginType, Permission
        defaults = {
            "name": "test_skill", "version": "1.0.0",
            "type": PluginType.SKILL, "description": "test",
            "entry_point": "test_skill:run",
            "permissions": [Permission.NETWORK],
        }
        defaults.update(kw)
        return PluginManifest(**defaults)

    def test_basic_creation(self):
        m = self._make()
        assert m.name == "test_skill"
        assert m.version == "1.0.0"
        assert m.enabled is True
        assert m.source == ""

    def test_skill_meta_conversion(self):
        m = self._make(
            markets=["a_share", "us_stock"], category="technical",
            params={"days": {"type": "integer", "default": 30}},
        )
        kw = m.to_skill_meta_kwargs()
        assert kw["name"] == "test_skill"
        assert kw["markets"] == ["a_share", "us_stock"]
        assert kw["category"] == "technical"

    def test_adapter_type_conversion(self):
        from backend.plugins.manifest import PluginType
        m = self._make(
            type=PluginType.ADAPTER, adapter_type="http",
            adapter_config={"url": "https://api.example.com"},
        )
        assert m.adapter_type == "http"
        assert m.adapter_config["url"] == "https://api.example.com"

    def test_compatibility_validation_fail(self):
        m = self._make(min_platform_version="99.0.0")
        err = m.validate_compatibility("1.0.0")
        assert err is not None and "平台" in err

    def test_compatibility_validation_pass(self):
        m = self._make(min_platform_version="0.1.0")
        assert m.validate_compatibility("1.0.0") is None

    def test_permission_enum_values(self):
        from backend.plugins.manifest import Permission
        assert Permission.NETWORK.value == "network"
        assert Permission.FULL_ACCESS.value == "full_access"
        assert len(Permission) == 6

    def test_plugin_type_enum(self):
        from backend.plugins.manifest import PluginType
        assert PluginType.SKILL.value == "skill"
        assert PluginType.ADAPTER.value == "adapter"
        assert PluginType.DATASOURCE.value == "datasource"


# ═══════════════════════════════════════════════════════
#  2. PluginRegistry 注册中心测试
# ═══════════════════════════════════════════════════════

class TestPluginRegistry:
    """插件注册中心 CRUD"""

    @pytest.fixture
    def reg(self, tmp_path):
        from backend.plugins.registry import PluginRegistry
        import backend.plugins.registry as reg_mod
        with patch.object(reg_mod, "_INSTALLED_FILE", tmp_path / "installed.json"):
            r = PluginRegistry()
            r._plugins = {}
            r._loaded = True
            yield r

    def _plugin(self, name="p1", version="1.0.0"):
        from backend.plugins.manifest import PluginManifest, PluginType
        return PluginManifest(
            name=name, version=version,
            type=PluginType.SKILL, description=f"test {name}",
        )

    def test_register_and_list(self, reg):
        reg.register(self._plugin())
        assert len(reg.list_plugins(enabled_only=False)) == 1
        assert reg.list_plugins(enabled_only=False)[0].name == "p1"

    def test_register_same_version_noop(self, reg):
        """同版本重复注册返回 False"""
        assert reg.register(self._plugin()) is True
        assert reg.register(self._plugin()) is False
        assert len(reg.list_plugins(enabled_only=False)) == 1

    def test_register_upgrade(self, reg):
        reg.register(self._plugin(version="1.0"))
        reg.register(self._plugin(version="2.0"))
        assert len(reg.list_plugins(enabled_only=False)) == 1
        assert reg.get("p1").version == "2.0"

    def test_unregister(self, reg):
        reg.register(self._plugin())
        assert reg.unregister("p1") is True
        assert reg.unregister("p1") is False
        assert len(reg.list_plugins(enabled_only=False)) == 0

    def test_enable_disable(self, reg):
        reg.register(self._plugin())
        assert reg.disable("p1") is True
        assert reg.get("p1").enabled is False
        assert reg.enable("p1") is True
        assert reg.get("p1").enabled is True

    def test_nonexistent(self, reg):
        assert reg.get("nope") is None
        assert reg.disable("nope") is False
        assert reg.enable("nope") is False

    def test_is_installed(self, reg):
        reg.register(self._plugin())
        assert reg.is_installed("p1") is True
        assert reg.is_installed("nope") is False

    def test_persistence(self, tmp_path):
        from backend.plugins.registry import PluginRegistry
        import backend.plugins.registry as reg_mod
        f = tmp_path / "db.json"
        with patch.object(reg_mod, "_INSTALLED_FILE", f):
            r1 = PluginRegistry()
            r1._plugins = {}
            r1._loaded = True
            r1.register(self._plugin())
            r1.save_to_disk()
            r2 = PluginRegistry()
            r2.load_from_disk()
            assert len(r2.list_plugins(enabled_only=False)) == 1
            assert r2.get("p1").version == "1.0.0"


# ═══════════════════════════════════════════════════════
#  3. PluginLoader 加载器测试
# ═══════════════════════════════════════════════════════

class TestPluginLoader:
    """5 种插件来源加载测试"""

    def test_load_from_local(self, tmp_path):
        from backend.plugins.loader import PluginLoader
        import backend.plugins.registry as reg_mod
        with patch.object(reg_mod, "_INSTALLED_FILE", tmp_path / "x.json"):
            loader = PluginLoader.__new__(PluginLoader)
            d = tmp_path / "my_skill"
            d.mkdir()
            (d / "manifest.json").write_text(json.dumps({
                "name": "local_skill", "version": "1.0.0",
                "type": "skill", "description": "local",
                "entry_point": "local_skill:run",
            }), encoding="utf-8")
            m = loader.load_from_local(d)
            assert m.name == "local_skill"
            assert m.version == "1.0.0"
            assert m.source == "local"

    def test_load_from_local_no_manifest(self, tmp_path):
        from backend.plugins.loader import PluginLoader, PluginLoadError
        import backend.plugins.registry as reg_mod
        with patch.object(reg_mod, "_INSTALLED_FILE", tmp_path / "x.json"):
            loader = PluginLoader.__new__(PluginLoader)
            d = tmp_path / "empty"
            d.mkdir()
            with pytest.raises(PluginLoadError):
                loader.load_from_local(d)

    def test_load_from_local_bad_json(self, tmp_path):
        from backend.plugins.loader import PluginLoader, PluginLoadError
        import backend.plugins.registry as reg_mod
        with patch.object(reg_mod, "_INSTALLED_FILE", tmp_path / "x.json"):
            loader = PluginLoader.__new__(PluginLoader)
            d = tmp_path / "bad"
            d.mkdir()
            (d / "manifest.json").write_text("not json", encoding="utf-8")
            with pytest.raises(PluginLoadError):
                loader.load_from_local(d)

    def test_uninstall(self, tmp_path):
        from backend.plugins.loader import PluginLoader
        from backend.plugins.registry import PluginRegistry
        from backend.plugins.manifest import PluginManifest, PluginType
        import backend.plugins.registry as reg_mod
        with patch.object(reg_mod, "_INSTALLED_FILE", tmp_path / "x.json"):
            reg = PluginRegistry()
            reg._plugins = {}
            reg._loaded = True
            reg.register(PluginManifest(
                name="rm", version="1", type=PluginType.SKILL, description="x"
            ))
            loader = PluginLoader.__new__(PluginLoader)
            with patch("backend.plugins.loader.plugin_registry", reg):
                assert loader.uninstall("rm") is True
                assert reg.get("rm") is None
                assert loader.uninstall("rm") is False


# ═══════════════════════════════════════════════════════
#  4. Discovery 发现测试
# ═══════════════════════════════════════════════════════

class TestPluginDiscovery:
    def test_discover_empty(self, tmp_path):
        from backend.plugins.discovery import discover_plugins
        import backend.plugins.discovery as disc_mod
        with patch.object(disc_mod, "_PLUGINS_DIR", tmp_path / "p"):
            (tmp_path / "p").mkdir(parents=True, exist_ok=True)
            count = discover_plugins()
            assert count == 0

    def test_register_skills_noop(self):
        from backend.plugins.discovery import register_plugin_skills
        register_plugin_skills()  # should complete silently

    def test_register_adapters_noop(self):
        from backend.plugins.discovery import register_plugin_adapters
        register_plugin_adapters()


# ═══════════════════════════════════════════════════════
#  5. Sandbox 沙箱测试
# ═══════════════════════════════════════════════════════

class TestSkillSandbox:
    def _manifest(self, source="local", perms=None):
        from backend.plugins.manifest import PluginManifest, PluginType, Permission
        return PluginManifest(
            name="test", version="1.0.0", type=PluginType.SKILL,
            description="t", source=source,
            permissions=perms or [Permission.FULL_ACCESS],
        )

    def test_local_full_access_no_block(self):
        from backend.plugins.sandbox import SkillSandbox
        m = self._manifest(source="local")
        assert SkillSandbox(m).validate_permissions() == []

    def test_remote_full_access_blocked(self):
        from backend.plugins.sandbox import SkillSandbox
        m = self._manifest(source="remote", perms=[])
        m.permissions = [__import__('backend.plugins.manifest', fromlist=['Permission']).Permission.FULL_ACCESS]
        blocked = SkillSandbox(m).validate_permissions()
        assert "full_access" in blocked

    def test_remote_network_ok(self):
        from backend.plugins.sandbox import SkillSandbox
        from backend.plugins.manifest import Permission
        m = self._manifest(source="remote", perms=[Permission.NETWORK])
        blocked = SkillSandbox(m).validate_permissions()
        assert "full_access" not in blocked
        assert "execute" not in blocked

    def test_determine_level_direct(self):
        from backend.plugins.sandbox import SkillSandbox
        m = self._manifest()
        s = SkillSandbox(m)
        assert s._determine_level() == "direct"

    def test_determine_level_subprocess(self):
        from backend.plugins.sandbox import SkillSandbox
        from backend.plugins.manifest import Permission
        m = self._manifest(source="remote", perms=[Permission.NETWORK])
        s = SkillSandbox(m)
        assert s._determine_level() == "subprocess"

    def test_determine_level_restricted(self):
        from backend.plugins.sandbox import SkillSandbox
        from backend.plugins.manifest import Permission
        m = self._manifest(source="remote", perms=[Permission.DATA_READ])
        s = SkillSandbox(m)
        assert s._determine_level() == "restricted"


# ═══════════════════════════════════════════════════════
#  6. Marketplace 市场客户端测试
# ═══════════════════════════════════════════════════════

class TestMarketplace:
    def test_has_required_methods(self):
        from backend.plugins.marketplace import marketplace
        for method in ("search", "get_plugin_info", "get_versions", "install", "get_categories"):
            assert hasattr(marketplace, method)

    def test_default_url(self):
        from backend.plugins.marketplace import marketplace
        assert marketplace._base_url.startswith("https://")
