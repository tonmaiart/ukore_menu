# 📘 API Documentation: Ukore Menu (`ukore_menu`)

ระบบ Central Menu Registry สำหรับ Maya ช่วยให้ปลั๊กอิน, เครื่องมือ (Tools), หรือสคริปต์ภายนอกสามารถเพิ่มรายการเมนู (Menu Items) เข้ามายังเมนูหลัก **"Ukore Tools"** ใน Maya ได้อย่างอิสระผ่านระบบ Registry กลาง โดยไม่ต้องแก้ไขโค้ดหลักของเมนู

---

## 🛠️ Overview & Usage Concept

1. **Import Module**: เรียกใช้ `registry` และ `MenuItemSpec` จาก `UkoreMenu`
2. **Define Spec**: สร้าง instance ของ `MenuItemSpec` กำหนดชื่อ, คำสั่ง, หมวดหมู่ และลำดับ
3. **Register**: ส่ง spec เข้าสู่ `registry.register_item()` เพื่อวาดเมนูขึ้น Maya GUI ทันที

```python
from UkoreMenu import registry, MenuItemSpec

# ตัวอย่างการลงทะเบียนเมนูใหม่
registry.register_item(
    MenuItemSpec(
        id="my_custom_tool",
        label="My Custom Tool...",
        category="General",
        command="import my_tool; my_tool.run()",
        order=10,
    )
)

```

---

## ⚠️ ข้อกำหนดบังคับ: ต้อง auto-import ตอน Maya เปิดไฟล์ (ไม่ใช่แค่ตอนเปิดเครื่องมือ)

`registry.register_item()` จะรัน **ก็ต่อเมื่อโมดูล `maya-scripts/<ToolPackage>/__init__.py`
ของปลั๊กอินนั้นถูก import จริง** — แค่มีโค้ด `register_item()` อยู่ใน `__init__.py`
**ไม่พอ** ถ้าไม่มีอะไรสั่ง import แพ็กเกจนั้นตั้งแต่ Maya เปิดไฟล์ เมนูจะไม่โผล่
จนกว่าจะมีอะไรสักอย่าง import แพ็กเกจนั้นก่อน (เช่น ผู้ใช้กดเปิดเครื่องมือนั้นจากปุ่มอื่นเอง
ครั้งแรกก่อน — ค่อยเห็นเมนูหลังจากนั้น) ซึ่งเป็นบั๊กที่เคยเกิดขึ้นจริงกับ
`MayaFileBrowser` (เทียบกับ `UkoreReferenceEditor` ที่ทำถูกตั้งแต่แรก)

**ทุกปลั๊กอินที่ต้องการให้เมนูของตัวเองโผล่ใน "Ukore Tools" ตั้งแต่ Maya เปิดไฟล์แรก
(ไม่ใช่หลังผู้ใช้กดเปิดเครื่องมือเองก่อน 1 ครั้ง) ต้องประกาศ `launch_hooks` เข้าไปใน
`maya_launcher_env_bridge` config store จากฝั่ง UkoreHub เอง (`plugin.py`'s
`register(api)`) ควบคู่กับการ contribute `PYTHONPATH`:**

```python
hooks = bridge.get("launch_hooks", {})
hooks[TOOL_ID] = {
    "order": 10,  # ต้องน้อยกว่า UkoreMenu เอง (order 99) เพื่อให้ import
                  # (และ register_item) รันเสร็จก่อน UkoreMenu สั่ง rebuild_menu
    "post_open_mel": 'python("try:\\n    import <ToolPackage>\\nexcept ImportError:\\n    pass");',
}
bridge.set("launch_hooks", hooks)
```

- `<ToolPackage>` คือชื่อแพ็กเกจใต้ `maya-scripts/` ของปลั๊กอินนั้น (เช่น
  `UkoreBrowser`, `UkoreReferenceEditor`) — ต้องตรงกับชื่อโฟลเดอร์ที่มี
  `__init__.py` ที่เรียก `registry.register_item()` อยู่จริง
- `order` ต้อง **น้อยกว่า 99** เสมอ (ค่าที่ UkoreMenu ใช้เอง) ไม่งั้น
  `rebuild_menu()` ของ UkoreMenu จะรันไปก่อนที่ปลั๊กอินจะทันได้ register
  ตัวเองเข้า registry
- อ้างอิงตัวอย่างจริงได้จาก `UkoreReferenceEditor/plugin.py`'s `register()`
  (ปลั๊กอินอ้างอิงที่ทำถูกตั้งแต่แรก) — ห้ามใช้แค่การ contribute `PYTHONPATH`
  เพียงอย่างเดียวแล้วคิดว่าเมนูจะโผล่เอง

---

## 📦 Data Classes

### `MenuItemSpec`

คลาสสำหรับกำหนดข้อกำหนด (Specification) ของเมนูรายการหนึ่งๆ

```python
@dataclass
class MenuItemSpec:
    id: str
    label: str
    command: str | Callable
    category: str = "Common"
    icon: Optional[str] = None
    order: int = 100
    divider_after: bool = False
    sub_menu: Optional[str] = None

```

#### Field Details

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `id` | `str` | *(Required)* | รหัสระบุตัวตนที่ไม่ซ้ำกันของรายการเมนู (Unique ID) เช่น `'maya_file_browser'` |
| `label` | `str` | *(Required)* | ข้อความที่จะแสดงบนปุ่มเมนูใน Maya เช่น `'Maya File Browser...'` |
| `command` | `str | Callable` | *(Required)* | คำสั่งที่จะทำงานเมื่อกดเมนู รองรับทั้ง Python string command และ Python function/callable |
| `category` | `str` | `"General"` | หมวดหมู่ที่จะนำเมนูไปวางไว้ — ค่ามาตรฐาน 4 ค่า: `'General'`, `'Model'`, `'Rig'`, `'Anim'` (ดูหัวข้อ "Category Rendering" ด้านล่าง) |
| `icon` | `Optional[str]` | `None` | Path หรือชื่อไฟล์ไอคอนที่จะแสดงหน้าข้อความเมนู |
| `order` | `int` | `100` | ลำดับการจัดเรียงภายในหมวดหมู่เดียวกัน (ตัวเลขน้อยจะอยู่ด้านบน) |
| `divider_after` | `bool` | `False` | หากเป็น `True` จะใส่เส้นคั่น (Divider) ต่อท้ายเมนูนี้ |
| `sub_menu` | `Optional[str]` | `None` | ชื่อของ Submenu หากต้องการนำเมนูนี้ไปซ้อนไว้ภายใต้เมนวย่อย |

---

## 🏛️ Classes

### `MenuRegistry` *(Singleton)*

คลาสหลักสำหรับบริหารจัดการและลงทะเบียนเมนูทั้งหมด รวมถึงการวาดเมนูบนหน้าต่าง Maya Window

> **Note:** เป็น Singleton Instance สามารถเข้าถึงได้ผ่านตัวแปร `registry`

#### Class Attributes

* `MENU_MAIN` (`str`): `"UkoreToolsMenu"` - ชื่ออ้างอิง UI ของเมนูหลัก
* `MENU_LABEL` (`str`): `"Ukore Tools"` - ข้อความบนแถบเมนูหลักของ Maya
* `MENU_PARENT` (`str`): `"MayaWindow"` - Parent UI Control หลักใน Maya

---

### Methods

#### `register_item(spec: MenuItemSpec) -> None`

ลงทะเบียน หรืออัปเดตข้อมูลเมนูรายการใหม่ลงใน Registry และสั่งวาดเมนูบน Maya GUI ใหม่ทันที (`rebuild_menu`)

* **Parameters:**
* `spec` (`MenuItemSpec`): Spec ของเมนูที่ต้องการลงทะเบียน



---

#### `unregister_item(item_id: str) -> None`

ลบรายการเมนูออกจาก Registry ด้วย ID และทำการวาดเมนูบน Maya GUI ใหม่ทันที

* **Parameters:**
* `item_id` (`str`): `id` ของเมนูที่ต้องการลบ



---

#### `rebuild_menu() -> None`

ทำลายเมนูเดิมบน Maya Window แล้วสร้างขึ้นใหม่ทั้งหมดตามข้อมูลล่าสุดที่ถูกบันทึกไว้ใน Registry

* **Logic การจัดวาง:**
1. จัดกลุ่มรายการเมนูตาม `category`
2. เรียงหมวดหมู่ตามลำดับมาตรฐาน:
* `General`
* `Common`
* `Model`
* `Rig`
* `Anim`
*(หากมี Category นอกเหนือจากนี้ จะถูกนำไปต่อท้าย)*
3. เรียงลำดับเมนูภายใน Category เดียวกันตามค่า `order`
4. สร้าง Submenu (ถ้ามีการระบุ `sub_menu`) และวาดปุ่มกดตาม `command` ที่กำหนดไว้

---

## 📐 Category Rendering (2026-08-14)

Category ไม่ได้ถูก flatten เป็น divider ทั้งหมดเหมือนเดิมอีกต่อไป — เพื่อไม่ให้เมนู
"Ukore Tools" รกเกินไปเมื่อมีปลั๊กอินมาลงทะเบียนเพิ่มขึ้นเรื่อยๆ:

* **`"General"`** — หมวดเดียวที่ยังคง flatten (แค่ divider คั่น เหมือนพฤติกรรมเดิม
  ของทุก category) — ใช้กับเครื่องมือที่ใช้งานบ่อย/เข้าถึงเร็ว เช่น
  Maya File Browser, Save Increment, Ukore Reference Editor
* **`"Common"` / `"Model"` / `"Rig"` / `"Anim"`** — กลายเป็น Submenu จริงของตัวเอง
  (ไม่ใช่แค่ divider) เพื่อรวบรวมเครื่องมือเฉพาะทางจำนวนมากไว้โดยไม่กินพื้นที่หน้า
  เมนูหลัก — `"Common"` เก็บเครื่องมือ selection/general-purpose (Renamer,
  Attribute, Flip Selection, Sort by Type, ฯลฯ — เดิมกระจายอยู่ใน `Selection`
  กับ `Common` แยกกัน)
* Category ใดๆ ที่ไม่ใช่ `"General"` (รวมถึงชื่อ category อื่นที่ไม่รู้จัก) จะถูก
  วาดเป็น Submenu เสมอ — ดู `MenuRegistry.rebuild_menu()`'s ใน `core.py`
* `sub_menu` field ของ `MenuItemSpec` ยังทำงานเหมือนเดิม โดยจะซ้อนอยู่ภายใต้
  category submenu นั้นๆ อีกชั้นหนึ่ง (หรือใต้ `MENU_MAIN` โดยตรงถ้า category
  เป็น `"General"`)
* **Icon ของ submenu**: `core.py`'s `CATEGORY_ICONS` map ชื่อ category ไปยัง
  ไอคอนของมันเอง (คนละเรื่องกับ `MenuItemSpec.icon` ที่เป็นไอคอนของแต่ละเมนูไอเทม)
  — สืบทอดมาจากไอคอนเดิมที่ `maya-plug-ins/ukoreMaya.py`'s `loadMenu()`
  เคยตั้งให้แต่ละ subMenu ก่อนจะถูก retire: `Common` → `layerEditor.png`,
  `Model` → `cube.png`, `Rig` → `kinJoint.png`, `Anim` → `character.svg`.
  Category ที่ไม่มีอยู่ใน map นี้ (รวมถึง `"General"` ซึ่งไม่ใช่ submenu) จะไม่มี
  ไอคอน — เพิ่ม entry ใหม่ใน `CATEGORY_ICONS` เองถ้าต้องการไอคอนให้ category อื่น

**ปลั๊กอินเก่าที่ยังใช้ category แบบเดิม** (`'จัดการไฟล์'`, `'Selection'`,
`'Model / Texture'`, `'Animation'`) ต้องอัปเดตเป็นชุดค่ามาตรฐานใหม่ — มิฉะนั้นเมนู
ของปลั๊กอินนั้นจะกลายเป็น Submenu แยกต่างหากที่ใช้ชื่อเดิม (ยังทำงานได้ ไม่ error
แต่ไม่ตรงกับโครงสร้างที่ตั้งใจไว้ และจะไม่มีไอคอนเพราะไม่อยู่ใน `CATEGORY_ICONS`).
ตัวอย่างการ mapping ที่ใช้จริงใน `MayaToolkit`, `UkoreReferenceEditor`,
`MayaFileBrowser`, `dw_publish_picker`: `จัดการไฟล์` → `General`,
`Selection`/`Common` (เดิม) → `Common` (ใหม่), `Model / Texture` → `Model`,
`Rig` → `Rig` (ไม่เปลี่ยน), `Animation` → `Anim` (ยกเว้นรายการที่เป็นเครื่องมือที่
ใช้บ่อย/มีรายการเดียว เช่น `dw_publish_picker` ซึ่งย้ายไป `General` แทนที่จะเป็น
`Anim`).

---

## 🔁 Reload Plugin System (2026-08-19)

นอกจาก Menu Item Registry แล้ว `UkoreMenu` ยังสร้างปุ่ม **"Reload Plugin"**
ไว้ล่างสุดของเมนู "Ukore Tools" ให้เองโดยอัตโนมัติ (นอก Category ใดๆ ทั้งสิ้น
— แสดงเสมอไม่ว่าจะมีปลั๊กอินมา register reload handler ไว้กี่ตัวก็ตาม) เมื่อกด
ปุ่มนี้ ระบบจะไล่รัน `callback` ของทุก Reload Handler ที่ปลั๊กอินต่างๆ
ลงทะเบียนไว้ตามลำดับ `order` จากน้อยไปมาก, `rebuild_menu()` อีกครั้งเพื่อความ
ชัวร์, แล้วสรุปผลเป็น `inViewMessage` ว่าปลั๊กอินไหน reload สำเร็จ/ล้มเหลวบ้าง
— **1 handler พังไม่ทำให้ handler อื่นหยุดทำงานตาม** (แต่ละตัวถูกครอบด้วย
try/except แยกกัน, error รายละเอียดขึ้น `cmds.warning` ให้ดูใน Script Editor)

### `ReloadHandlerSpec`

```python
@dataclass
class ReloadHandlerSpec:
    id: str
    label: str
    callback: Callable[[], None]
    order: int = 100

```

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `id` | `str` | *(Required)* | รหัสระบุตัวตนที่ไม่ซ้ำกันของ handler เช่น `'ukore_browser'` |
| `label` | `str` | *(Required)* | ชื่อที่จะโชว์ในสรุปผล `inViewMessage` หลังกด Reload |
| `callback` | `Callable[[], None]` | *(Required)* | ฟังก์ชันไม่รับ argument ที่จะถูกเรียกตอนกด Reload — โค้ดปลั๊กอินต้อง reload โมดูลของตัวเอง (และ re-register อะไรก็ตามที่ reference ค้างอยู่ เช่น `MenuItemSpec.command` ที่เป็น callable ไม่ใช่ string) |
| `order` | `int` | `100` | ลำดับการรันข้าม handler ต่างๆ (เลขน้อยรันก่อน) |

### `registry.register_reload_handler(spec: ReloadHandlerSpec) -> None`

ลงทะเบียน (หรืออัปเดต) reload handler ของปลั๊กอินหนึ่งๆ — เรียกจุดเดียวกับที่
เรียก `registry.register_item()` อยู่แล้ว (ต้อง auto-import ตอน Maya เปิดไฟล์
เหมือนกันทุกประการ — ดูหัวข้อ "ข้อกำหนดบังคับ" ด้านบน ไม่มีข้อกำหนดเพิ่มเติม
เพราะใช้ launch_hooks ตัวเดียวกัน)

### `registry.unregister_reload_handler(handler_id: str) -> None`

ลบ reload handler ออกจาก Registry ด้วย `id`

### `reload_package(package_name: str) -> None`

Helper กลางสำหรับปลั๊กอินส่วนใหญ่ที่ไม่ได้มี reload logic พิเศษของตัวเองอยู่
แล้ว (เทียบกับ `MayaToolkit`'s `UkoreMaya/core/Plugin.py`'s
`reload_plugins()` ที่ reload แบบเจาะจงลำดับโมดูลเอง เพราะมี dependency
ข้าม module ที่ต้อง reload ตามลำดับที่กำหนด) — reload ทุก submodule ที่เคย
ถูก import แล้วของ `package_name` (จาก `sys.modules`, เรียงจากลึกสุดไปตื้นสุด
แล้วค่อย reload package หลักเป็นตัวสุดท้าย) โมดูลไหน reload พังจะแค่ขึ้น
`cmds.warning` แล้วข้ามไป ไม่ทำให้ตัวอื่น/handler อื่นพังตาม

**สำคัญ:** ถ้าปลั๊กอินนั้น register เมนู/reload handler ไว้ใน module-level
code ของ package หลักเอง (แบบเดียวกับที่ `register_item()` ต้องทำตาม
ข้อกำหนดบังคับด้านบนอยู่แล้ว) `reload_package()` จะ re-register ให้ฟรี
เพราะการ reload `__init__.py` คือการรันโค้ดนั้นซ้ำ — แต่ถ้าปลั๊กอินไหน
register ผ่านฟังก์ชันแยกที่ถูกเรียกจาก MEL launch hook แทน (เช่น
`dw_publish_picker`'s `DwPublishPicker.register_menu()` ที่ถูกเรียกจาก
`post_open_mel`, ไม่ใช่ตอน import) ต้องเรียกฟังก์ชัน register นั้นซ้ำเองใน
`callback` หลัง `reload_package()` คืนค่ากลับมาด้วย — ดูตัวอย่างจริงได้จาก
`dw_publish_picker/maya-scripts/DwPublishPicker/picker_loader.py`'s
`_reload_dw_publish_picker()`

### ตัวอย่างการใช้งาน (ปลั๊กอินทั่วไปที่ไม่มี reload logic พิเศษ)

```python
from UkoreMenu import registry, MenuItemSpec, ReloadHandlerSpec, reload_package

registry.register_item(MenuItemSpec(id="my_tool", label="My Tool...", command="...", order=10))

registry.register_reload_handler(
    ReloadHandlerSpec(
        id="my_tool",
        label="My Tool",
        callback=lambda: reload_package("MyToolPackage"),
        order=50,
    )
)

```

### ตัวอย่างการใช้งาน (ปลั๊กอินที่มี reload logic ของตัวเองอยู่แล้ว)

```python
from UkoreMenu import registry, ReloadHandlerSpec
from UkoreMaya.core.Plugin import reload_plugins

registry.register_reload_handler(
    ReloadHandlerSpec(id="maya_toolkit", label="MayaToolkit", callback=reload_plugins, order=10)
)

```

---

## 🌐 Public Module Exports

โมดูล `UkoreMenu` ส่งออก (Export) ตัวแปรสำคัญให้ใช้งานหลัก ได้แก่:

```python
from UkoreMenu import registry, MenuItemSpec, ReloadHandlerSpec, reload_package

```

* `registry` (`MenuRegistry`): Instance หลักสำหรับใช้งานระบบ Registry (ทั้ง
  menu item และ reload handler)
* `MenuItemSpec` (`MenuItemSpec`): Data class สำหรับสร้างวัตถุข้อมูลเมนู
* `ReloadHandlerSpec` (`ReloadHandlerSpec`): Data class สำหรับสร้างวัตถุ
  reload handler — ดูหัวข้อ "Reload Plugin System" ด้านบน
* `reload_package` (`Callable[[str], None]`): Helper กลางสำหรับ reload
  ทุก submodule ของ package หนึ่งๆ ที่เคยถูก import แล้ว

---

## 💻 Usage Examples

### 1. ลงทะเบียนเมนูด้วย Python String Command

```python
from UkoreMenu import registry, MenuItemSpec

registry.register_item(
    MenuItemSpec(
        id="file_export_tool",
        label="Export Asset...",
        category="General",
        command="import asset_exporter; asset_exporter.export_dialog()",
        order=1,
        divider_after=True
    )
)

```

### 2. ลงทะเบียนเมนูด้วย Python Function / Callback

```python
from UkoreMenu import registry, MenuItemSpec

def open_rigging_tool():
    print("Opening Rigging Helper...")

registry.register_item(
    MenuItemSpec(
        id="rigging_helper",
        label="Rig Helper Tools",
        category="Rig",
        command=open_rigging_tool,
        order=20
    )
)

```

### 3. ลงทะเบียนเมนูภายใต้ Submenu

```python
from UkoreMenu import registry, MenuItemSpec

registry.register_item(
    MenuItemSpec(
        id="clean_unused_nodes",
        label="Clean Unused Nodes",
        category="Model",
        sub_menu="Utilities",  # วางไว้ใน Submenu ย่อยชื่อ "Utilities" ภายใต้ Submenu "Model" อีกที
        command="import model_utils; model_utils.clean_nodes()",
        order=10
    )
)

```

### 4. ลบเมนูออกจากระบบ (Unregister)

```python
from UkoreMenu import registry

registry.unregister_item("file_export_tool")

```