"""Central Menu Registry System for Ukore Studio Tools in Maya."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional
import maya.cmds as cmds

MENU_MAIN = "UkoreStudioToolMenu"
MENU_LABEL = "Ukore Studio Tool"
MENU_PARENT = "MayaWindow"


@dataclass
class MenuItemSpec:
    """Specification for registering a menu item or submenu button.

    Attributes:
        id: Unique identifier for the menu item (e.g. 'maya_file_browser').
        label: Text displayed on the menu item.
        command: Python function, string command, or module execution string.
        category: Section divider/category name (e.g. 'จัดการไฟล์', 'Rig', 'Model / Texture').
        icon: Optional icon filename for the menu item.
        order: Priority order within its category (lower numbers appear first).
        divider_after: Whether to place a menu divider line after this item.
    """
    id: str
    label: str
    command: str | Callable
    category: str = "Common"
    icon: Optional[str] = None
    order: int = 100
    divider_after: bool = False
    sub_menu: Optional[str] = None  

class MenuRegistry:
    """Singleton Registry storing all registered menu specifications and drawing
    them into Maya's main menu bar."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._items = {}
            # Default category display order
            cls._instance._categories_order = [
                "จัดการไฟล์",
                "Selection",
                "Common",
                "Model / Texture",
                "Rig",
                "Animation",
            ]
        return cls._instance

    def register_item(self, spec: MenuItemSpec) -> None:
        """Register or update a menu item, then refresh the Maya UI menu."""
        self._items[spec.id] = spec
        self.rebuild_menu()

    def unregister_item(self, item_id: str) -> None:
        """Remove a menu item by ID and refresh the Maya UI menu."""
        if item_id in self._items:
            del self._items[item_id]
            self.rebuild_menu()

    def rebuild_menu(self) -> None:
        """Draw or rebuild the main Ukore Studio Tool menu in Maya's main window."""
        if not cmds.control(MENU_PARENT, exists=True):
            return

        if not cmds.menu(f"{MENU_PARENT}|{MENU_MAIN}", exists=True):
            cmds.menu(
                MENU_MAIN,
                label=MENU_LABEL,
                parent=MENU_PARENT,
                tearOff=True,
                allowOptionBoxes=True,
            )
        else:
            cmds.menu(f"{MENU_PARENT}|{MENU_MAIN}", edit=True, deleteAllItems=True)

        items_by_cat: dict[str, list[MenuItemSpec]] = {}
        for spec in sorted(self._items.values(), key=lambda x: x.order):
            items_by_cat.setdefault(spec.category, []).append(spec)

        active_cats = [c for c in self._categories_order if c in items_by_cat]
        for c in items_by_cat:
            if c not in active_cats:
                active_cats.append(c)

        for cat_name in active_cats:
            cmds.menuItem(divider=True, dividerLabel=cat_name, parent=MENU_MAIN)

            # Dictionary เก็บ reference ของ Submenu ที่สร้างขึ้นภายใน Category นี้
            created_submenus: dict[str, str] = {}

            for spec in items_by_cat[cat_name]:
                target_parent = MENU_MAIN

                # ถ้ามีการระบุ sub_menu ให้สร้างหรือดึง Submenu นั้นมาเป็น Parent
                if spec.sub_menu:
                    sub_key = f"{cat_name}|{spec.sub_menu}"
                    if sub_key not in created_submenus:
                        sub_item = cmds.menuItem(
                            subMenu=True,
                            label=spec.sub_menu,
                            parent=MENU_MAIN,
                            tearOff=True,
                        )
                        created_submenus[sub_key] = sub_item
                    target_parent = created_submenus[sub_key]

                if callable(spec.command):
                    cmd_fn = spec.command
                    cmd_val = lambda *args, fn=cmd_fn: fn()
                else:
                    cmd_val = str(spec.command)

                item_kwargs = {
                    "label": spec.label,
                    "parent": target_parent,
                    "command": cmd_val,
                }

                
                if spec.icon:
                    item_kwargs["image"] = spec.icon

                cmds.menuItem(**item_kwargs)

                if spec.divider_after:
                    cmds.menuItem(divider=True, parent=target_parent)


# Global Singleton Instance
registry = MenuRegistry()

# ให้วาดเมนูทันทีเมื่อ GUI ของ Maya พร้อม
def _auto_init_menu(*args):
    if cmds.control(MENU_PARENT, exists=True):
        registry.rebuild_menu()

if not cmds.about(batch=True):
    cmds.evalDeferred(_auto_init_menu, lowestPriority=True)