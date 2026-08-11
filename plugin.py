from __future__ import annotations

import sys
from pathlib import Path

_PLUGIN_DIR = Path(__file__).resolve().parent
if str(_PLUGIN_DIR) not in sys.path:
    sys.path.insert(0, str(_PLUGIN_DIR))

TOOL_ID = "ukore_menu"
TOOL_LABEL = "Ukore Menu"
MAYA_ENV_BRIDGE_PLUGIN_ID = "maya_launcher_env_bridge"
ANY_VERSION = "*"


def register(api) -> None:
    tool_root = Path(__file__).resolve().parent

    bridge = api.project_plugin_config_store(MAYA_ENV_BRIDGE_PLUGIN_ID)
    if bridge is None:
        return

    contributions = bridge.get("contributions", {})
    contributions[TOOL_ID] = {
        "PYTHONPATH": {ANY_VERSION: [str(tool_root / "maya-scripts")]},
    }
    bridge.set("contributions", contributions)

    labels = bridge.get("labels", {})
    labels[TOOL_ID] = TOOL_LABEL
    bridge.set("labels", labels)

    # 🟢 สั่ง Import เครื่องมือลูกเพื่อกระตุ้น __init__.py แล้วค่อยวาดเมนู
    hooks = bridge.get("launch_hooks", {})
    hooks[TOOL_ID] = {
        "order": 99,
        "post_open_mel": 'python("try:\\n    import UkoreBrowser\\nexcept ImportError:\\n    pass\\nimport UkoreMenu.core; UkoreMenu.core.registry.rebuild_menu()");',
        "diagnostic_msg": "UkoreMenu initialized via launch hook"
    }
    bridge.set("launch_hooks", hooks)