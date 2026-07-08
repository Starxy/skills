# Pyzotero 工作流

当需要编写原生 pyzotero 调用，或修改内置 helper 时，使用本参考。官方文档：https://pyzotero.readthedocs.io/en/latest/

## 安装与连接

优先使用 `uv`：

```bash
uv add pyzotero
uv run --with pyzotero python skills/zotero-library/scripts/zotero_library.py --help
```

```python
from pyzotero import Zotero

zot = Zotero(library_id, "user", api_key)
group = Zotero(group_id, "group", api_key)
local_read_only = Zotero(library_id, "user", api_key, local=True)
```

`Zotero` 实例绑定到构造时指定的 user 或 group 文献库。不要跨文献库复用同一个 client。`local=True` 只用于本地只读访问；写操作使用 Web API。

## 读取方法

| 需求 | 方法 |
| --- | --- |
| 单个 item | `zot.item("ABC123")` |
| 子项、附件、notes | `zot.children("ABC123")` |
| collection 内 items | `zot.collection_items("COLLKEY")` |
| collections | `zot.collections()` 或 `zot.collections_top()` |
| 单个 collection | `zot.collection("COLLKEY")` |
| tags | `zot.tags()` 或 `zot.item_tags("ABC123")` |
| 按 tag 查 items | `zot.items(tag="old-tag")`，必要时再 `zot.everything(...)` |

读取某个 item 的 collection 名称：先 `zot.item(key)` 取 `data.collections`，再逐个 `zot.collection(collection_key)` 解析 `data.name`。

## Note

Zotero note 是 item 的 child item，`itemType` 为 `note`。为了在 Zotero UI 中更好展示，note 内容使用 HTML，而不是纯文本堆叠：

```python
note = zot.item_template("note")
note["note"] = "<h2>阅读笔记</h2><p>核心问题...</p><ul><li>贡献一</li></ul>"
checked = zot.check_items([note])
zot.create_items(checked, parentid="PARENT_ITEM_KEY")
```

helper 的 `create-note` 会把纯文本转为简单 HTML：

- `--heading` 转为 `<h2>`；
- 普通行转为 `<p>`；
- 以 `- ` 开头的连续行转为 `<ul><li>`。

## Collection 移动

追加到另一个 collection：

```python
item = zot.item("ABC123")
zot.addto_collection("TARGETCOLL", item)
```

移动到目标 collection：

1. `zot.item(item_key)` 读取当前 `data.collections`。
2. 如果目标 collection 不在当前列表中，先 `zot.addto_collection(target, item)`。
3. 从当前其他 collections 中逐个 `zot.deletefrom_collection(old_collection, item)`。
4. 重新读取 item 或 collection items 验证结果。

如果只想从某个来源 collection 移出，helper 的 `move-to-collection --from-collection OLD` 会只移除该来源。

## 全库 Tag Rename

pyzotero 没有单独的“rename tag”快捷方法；按 item 批量替换：

```python
items = zot.everything(zot.items(tag="old-tag"))
for item in items:
    tags = item["data"].get("tags", [])
    item["data"]["tags"] = [
        tag for tag in tags if tag.get("tag") != "old-tag"
    ]
    if not any(tag.get("tag") == "new-tag" for tag in item["data"]["tags"]):
        item["data"]["tags"].append({"tag": "new-tag"})
zot.update_items(items)
```

批量更新按 50 个 item 分块。执行后再查 `zot.items(tag="old-tag")` 和 `zot.items(tag="new-tag")` 验证。

## 普通 Item 更新

先 fetch，再 patch：

```python
item = zot.item("ABC123")
item["data"]["title"] = "Corrected title"
item["data"]["abstractNote"] = "New abstract"
zot.update_item(item)
```

保留 item 返回的 `version`，让 pyzotero 使用 `If-Unmodified-Since-Version`，避免覆盖并发修改。

## 自动化模式

1. 读取当前文献库状态，保存 item keys、collection keys、tags 和 versions。
2. 构建拟执行的 JSON change set。
3. dry-run，打印精确 pyzotero payload。
4. 执行最小批次。
5. 重新读取受影响 keys，对比预期字段。
6. 单独记录失败项；不要盲目重试破坏性写操作。
