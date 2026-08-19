"""Central Menu Registry System for Ukore Studio Tools in Maya."""

from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass
from typing import Callable, Optional
import maya.cmds as cmds

MENU_MAIN = "UkoreToolsMenu"
MENU_LABEL = "Ukore Tools"
MENU_PARENT = "MayaWindow"

# Icons carried over from the old per-plugin "Ukore Studio Tool" menu
# (retired maya-plug-ins/ukoreMaya.py's loadMenu()), which set an `image=`
# on each of its own subMenu buttons. Category submenus here use the same
# icons so the menu looks the same as before, just centrally registered.
CATEGORY_ICONS = {
    "Common": "layerEditor.png",
    "Model": "cube.png",
    "Rig": "kinJoint.png",
    "Anim": "character.svg",
}


@dataclass
class MenuItemSpec:
    """Specification for registering a menu item or submenu button.

    Attributes:
        id: Unique identifier for the menu item (e.g. 'maya_file_browser').
        label: Text displayed on the menu item.
        command: Python function, string command, or module execution string.
        category: Top-level section name (e.g. 'General', 'Model', 'Rig',
            'Anim'). 'General' renders flat (divider only); any other
            category becomes its own real Maya submenu — see
            MenuRegistry.rebuild_menu.
        icon: Optional icon filename for the menu item.
        order: Priority order within its category (lower numbers appear first).
        divider_after: Whether to place a menu divider line after this item.
    """
    id: str
    label: str
    command: str | Callable
    category: str = "General"
    icon: Optional[str] = None
    order: int = 100
    divider_after: bool = False
    sub_menu: Optional[str] = None


@dataclass
class ReloadHandlerSpec:
    """Specification for a plugin's own reload behavior, run when the user
    clicks "Reload Plugin" at the bottom of the "Ukore Tools" menu.

    Attributes:
        id: Unique identifier for this reload handler (e.g. 'ukore_browser').
        label: Short display name used in the reload summary toast.
        callback: No-arg callable that reloads this plugin's own Python
            modules and re-registers anything whose reference would
            otherwise go stale (e.g. a MenuItemSpec.command that's a bound
            function rather than a string — re-registering after reload
            refreshes it to point at the new function object). One
            handler raising never stops the others from running — see
            MenuRegistry._run_reload_handlers.
        order: Run order across handlers (lower runs first) — matters when
            one plugin's reload depends on another's already having
            finished.
    """
    id: str
    label: str
    callback: Callable[[], None]
    order: int = 100


def reload_package(package_name: str) -> None:
    """Reload every already-imported submodule of `package_name` (deepest
    submodules first, so by the time a package's own __init__ is reloaded
    last, everything it re-imports is already fresh), skipping any module
    not currently in sys.modules (nothing to do — it'll import fresh next
    time it's used anyway).

    A plugin whose menu/reload registration happens in its top package's
    own module-level code (the same convention this module's README
    requires for register_item to run at Maya startup) gets re-registered
    for free, since re-executing __init__.py re-runs those
    registry.register_item()/register_reload_handler() calls. A plugin
    whose registration lives outside its package's import-time code (e.g.
    behind a separate MEL launch hook, like DwPublishPicker's
    register_menu()) must call that registration function again itself
    after reload_package() returns — reload_package only reloads code, it
    never re-registers anything on its own.

    One bad submodule (e.g. a syntax error mid-edit) is reported via
    cmds.warning and skipped rather than aborting the rest of the reload.
    """
    prefix = package_name + "."
    submodule_names = sorted(
        (name for name in sys.modules if name == package_name or name.startswith(prefix)),
        key=lambda name: name.count("."),
        reverse=True,
    )
    for name in submodule_names:
        module = sys.modules.get(name)
        if module is None:
            continue
        try:
            importlib.reload(module)
        except Exception as exc:
            cmds.warning(f"[Ukore Menu] reload_package: failed to reload '{name}': {exc}")


class MenuRegistry:
    """Singleton Registry storing all registered menu specifications and drawing
    them into Maya's main menu bar."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._items = {}
            cls._instance._reload_handlers = {}
            # Default category display order. "General" is rendered flat
            # (no submenu — see rebuild_menu) so common/frequently-used
            # items stay one click away; every other category becomes its
            # own real Maya submenu.
            cls._instance._categories_order = [
                "General",
                "Common",
                "Model",
                "Rig",
                "Anim",
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

    def register_reload_handler(self, spec: ReloadHandlerSpec) -> None:
        """Register or update a plugin's reload handler, then refresh the
        Maya UI menu (mirrors register_item's own refresh-on-register)."""
        self._reload_handlers[spec.id] = spec
        self.rebuild_menu()

    def unregister_reload_handler(self, handler_id: str) -> None:
        """Remove a reload handler by ID and refresh the Maya UI menu."""
        if handler_id in self._reload_handlers:
            del self._reload_handlers[handler_id]
            self.rebuild_menu()

    def _run_reload_handlers(self, *_args) -> None:
        """Run every registered reload handler in registration-order,
        isolating each one's failure so a single broken plugin never blocks
        the rest — same isolation contract as UkoreHub's own
        on_app_start/on_repo_changed lifecycle hooks."""
        handlers = sorted(self._reload_handlers.values(), key=lambda h: h.order)
        succeeded: list[str] = []
        failed: list[str] = []

        for spec in handlers:
            try:
                spec.callback()
                succeeded.append(spec.label)
            except Exception as exc:
                failed.append(spec.label)
                cmds.warning(f"[Ukore Menu] Reload handler '{spec.id}' ({spec.label}) failed: {exc}")

        self.rebuild_menu()

        if not handlers:
            message = "[Ukore Menu] No plugins registered a reload handler."
        elif failed:
            message = f"Reloaded {len(succeeded)}/{len(handlers)} plugin(s) — {len(failed)} failed (see Script Editor)"
        else:
            message = f"Reloaded {len(succeeded)} plugin(s): {', '.join(succeeded)}"

        cmds.inViewMessage(amg=message, pos="botCenter", fade=True)

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
            # "General" stays flat (divider only, same as every category used
            # to render) — everything else becomes its own real submenu so
            # the main menu doesn't get flattened/cluttered as more tools
            # register into it.
            if cat_name == "General":
                cmds.menuItem(divider=True, dividerLabel=cat_name, parent=MENU_MAIN)
                cat_parent = MENU_MAIN
            else:
                submenu_kwargs = {
                    "subMenu": True,
                    "label": cat_name,
                    "parent": MENU_MAIN,
                    "tearOff": True,
                }
                if cat_name in CATEGORY_ICONS:
                    submenu_kwargs["image"] = CATEGORY_ICONS[cat_name]
                cat_parent = cmds.menuItem(**submenu_kwargs)

            # Dictionary เก็บ reference ของ Submenu ที่สร้างขึ้นภายใน Category นี้
            created_submenus: dict[str, str] = {}

            for spec in items_by_cat[cat_name]:
                target_parent = cat_parent

                # ถ้ามีการระบุ sub_menu ให้สร้างหรือดึง Submenu นั้นมาเป็น Parent
                if spec.sub_menu:
                    sub_key = f"{cat_name}|{spec.sub_menu}"
                    if sub_key not in created_submenus:
                        sub_item = cmds.menuItem(
                            subMenu=True,
                            label=spec.sub_menu,
                            parent=cat_parent,
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

        # "Reload Plugin" — always present at the very bottom of the main
        # menu (never inside a category submenu), regardless of how many
        # plugins have actually registered a reload handler. See
        # register_reload_handler/_run_reload_handlers above.
        if active_cats:
            cmds.menuItem(divider=True, parent=MENU_MAIN)
        cmds.menuItem(
            label="Reload Plugin",
            parent=MENU_MAIN,
            command=lambda *args: self._run_reload_handlers(),
        )


# Global Singleton Instance
registry = MenuRegistry()

# ให้วาดเมนูทันทีเมื่อ GUI ของ Maya พร้อม
def _auto_init_menu(*args):
    if cmds.control(MENU_PARENT, exists=True):
        registry.rebuild_menu()

if not cmds.about(batch=True):
    cmds.evalDeferred(_auto_init_menu, lowestPriority=True)