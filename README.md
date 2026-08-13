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
        category="Common",
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
| `category` | `str` | `"Common"` | หมวดหมู่ที่จะนำเมนูไปวางไว้ (ตัวอย่าง: `'จัดการไฟล์'`, `'Selection'`, `'Common'`, `'Model / Texture'`, `'Rig'`, `'Animation'`) |
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
* `จัดการไฟล์`
* `Selection`
* `Common`
* `Model / Texture`
* `Rig`
* `Animation`
*(หากมี Category นอกเหนือจากนี้ จะถูกนำไปต่อท้าย)*


3. เรียงลำดับเมนูภายใน Category เดียวกันตามค่า `order`
4. สร้าง Submenu (ถ้ามีการระบุ `sub_menu`) และวาดปุ่มกดตาม `command` ที่กำหนดไว้



---

## 🌐 Public Module Exports

โมดูล `UkoreMenu` ส่งออก (Export) ตัวแปรสำคัญสองตัวให้ใช้งานหลัก ได้แก่:

```python
from UkoreMenu import registry, MenuItemSpec

```

* `registry` (`MenuRegistry`): Instance หลักสำหรับใช้งานระบบ Registry
* `MenuItemSpec` (`MenuItemSpec`): Data class สำหรับสร้างวัตถุข้อมูลเมนู

---

## 💻 Usage Examples

### 1. ลงทะเบียนเมนูด้วย Python String Command

```python
from UkoreMenu import registry, MenuItemSpec

registry.register_item(
    MenuItemSpec(
        id="file_export_tool",
        label="Export Asset...",
        category="จัดการไฟล์",
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
        category="Model / Texture",
        sub_menu="Utilities",  # วางไว้ใน Submenu ชื่อ "Utilities"
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