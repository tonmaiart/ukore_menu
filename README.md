# cache/plugins/UkoreMenu/

Central Menu Registry for Maya. Provides a clean, decoupled API letting independent tools, plugins, and custom scripts register menu items into the main "Ukore Studio Tool" Maya menu without editing the core menu builder code.

## How Other Tools Register Items

Inside Maya, any script or tool plugin can import `UkoreMenu.core` and register its items:

```python
from UkoreMenu.core import registry, MenuItemSpec

registry.register_item(
    MenuItemSpec(
        id="maya_file_browser",
        label="Maya File Browser...",
        category="จัดการไฟล์",
        command="from tmlib.core import File; File.launch('UkoreBrowser')",
        order=10,
    )
)# ukore_menu
