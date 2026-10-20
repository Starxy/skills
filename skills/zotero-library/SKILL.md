---
name: zotero-library
disable-model-invocation: true
description: Use when the user invokes this skill to search, read, organize, annotate, import, export, or update a Zotero user/group library through the official Zotero Web API, including synced full text, notes, tags, collections, stored attachments, and batch maintenance.
---

# Zotero Library

通过 Python 脚本调用 Zotero 官方 Web API v3。Python 3.10+，只使用标准库，无需 MCP、pyzotero 或运行 Zotero Desktop。

## 调用与配置

以本 `SKILL.md` 所在目录为 skill 根目录，执行 `scripts/zotero_library.py`。安装后的路径可能不在当前工作目录，先根据已加载的 skill 路径定位脚本，再使用绝对路径调用。

下文 `$Z` 是该脚本的绝对路径。PowerShell 调用示例：

```powershell
python $Z config
python $Z capabilities
python $Z search "attention" --limit 10 --detail keys_only
```

个人库只需配置环境变量 `ZOTERO_API_KEY`。未提供 `--library-id` 和 `ZOTERO_LIBRARY_ID` 时，脚本调用官方密钥信息接口，用返回的 `userID` 自动选择 key 所属用户的个人库，`config` 命令也会显示解析后的 ID。自动识别不授予额外权限，私有读取及写入仍由 key 的实际权限决定。不要把密钥写进脚本、笔记或报告。

库 ID 的优先级为 `--library-id` → `ZOTERO_LIBRARY_ID` → API key 自动识别；已明确提供 ID 时不请求自动识别。`ZOTERO_LIBRARY_TYPE` 为 `user` 或 `group`，默认 `user`；群组库必须明确提供数字 ID，不会回退为个人库。读取公开库时可明确提供 ID 并省略 key。

`--library-id ID --library-type group` 可在单次命令中覆盖环境变量；客户端按文献库隔离。`ZOTERO_LOCAL` 不启用本地访问。可用 `libraries` 列出文献库，`key-info` 检查 key 权限，`library-info` 读取当前库版本和条目数。

## 写入行为

用户的任务已明确目标和修改内容时，直接执行相应写命令。**写操作默认执行，不要求二次确认、强制 dry-run、`--execute` 或先展示变更再等待批准。** 原 `--execute` 仅作为兼容参数保留，不是写入门槛。

只有用户请求预览时才添加 `--dry-run`。它可放在子命令前后，允许读取模板及当前状态，但不提交远端变更。缺少目标、遇到同名集合歧义或 API 权限不足时，说明具体缺失信息，不把它包装成通用确认流程。

`delete-item` 默认移入回收站，`--permanent` 永久删除；`delete-note`、`delete-annotation` 永久删除相应类型的子项。集合移动默认替换原 memberships；仅追加时使用 `add-to-collection`。

## 搜索 → keys → 操作

1. 用 `search`、`collections --query`、`tags` 找到真实 item/collection keys，避免根据标题或名称猜 key。
2. 用 `item KEY` 查看完整元数据，`children KEY` 找附件和笔记，`fulltext KEY` 读取云端已同步的附件索引文本。
3. 对这些 keys 执行读取或修改；写入返回实际结果。批量命令报告已经成功的记录及失败位置。

| 需求 | 命令 |
| --- | --- |
| 标题、作者、年份关键词 | `search "query"` |
| 包含已同步全文的关键词 | `search "query" --mode fulltext`（API `qmode=everything`） |
| 标签交集 | `search --tag reviewed --tag important` |
| 已保存引用键 | `search smith2026 --mode citekey`（同步字段或 Extra） |
| 笔记 / 标注文本 | `search "query" --mode notes` / `--mode annotations` |
| 元数据组合条件 | `advanced-search --conditions @conditions.json --join all` |
| 集合 / 最近条目 | `collection-items COLLECTION` / `recent` |
| 跨库搜索 | `search "query" --all-libraries`，保留返回的文献库身份 |

列表默认一页。返回 `next_start` 时继续 `--start N`，需要全量时显式用 `--all`。`keys_only` 适合初筛，`--detail full` 读取原始记录。

所有命令输出单个 JSON 对象：

```json
{"ok": true, "command": "search", "schema": 1, "data": {"items": []}}
{"ok": false, "command": "update-item", "schema": 1, "error": {"code": "version_conflict", "message": "..."}}
```

失败退出码为 1。检查 `ok`、`error.code` 及 `details.completed`；不能把 HTTP 200 中的失败记录当成功。遇到版本冲突时读取最新状态后再判断如何继续，不盲目重放已经部分完成的批量写入。

## 内容与维护

- **文献、集合和标签**：模板创建、Zotero JSON 批量导入、版本化更新、回收站/永久删除、集合路径解析、标签增删/改名、批量修改。
- **笔记**：`create-note`、`update-note`、`delete-note`。`--text` 转为转义后的段落、标题和列表；已有 HTML 用 `--html`；长文本用 UTF-8 文件或 `--text -`。JSON 参数支持 `@file.json` 或 `-` 从 stdin 读取，避免复杂 shell 转义。
- **标注**：`annotations` 读取 Zotero 已同步的原生标注；`create-annotation` 接受明确的 `annotationPosition` JSON。必须使用已知的 Zotero 位置数据，不从论文文字猜坐标，也不声称能自动定位高亮。
- **附件**：`attach --parent KEY --file PATH` 使用官方存储上传流程；`--url` 只创建链接型附件，不抓取 URL；`download ATTACHMENT_KEY` 下载云端存储文件。未同步、仅本地链接或仅在 WebDAV 的文件不可通过此脚本取得。
- **引用和关联**：`export` 调用官方格式/CSL 样式导出，`related`、`add-relation`、`remove-relation` 管理库内关联。`synthesize` 返回按论文分组的真实笔记和标注，综合解释由 agent 完成。
- **去重**：`find-duplicates` 比较官方元数据；`merge-duplicates KEEP OTHER...` 通过普通 API 写入合并字段、标签、集合和子项，并把重复父项移入回收站。它是客户端组合操作，跨多条请求不具备事务性；检查部分失败及保留的字段冲突。
- **同步**：`changes --since VERSION`（兼容名 `sync`）返回变更版本和删除记录；它不触发桌面同步，也不自动下载所有变更对象。保存下一 checkpoint 前需获取对象、应用删除，并检查各端点版本一致。

完整参数、写入示例和常见失败见 [commands.md](references/commands.md)。需要修改 HTTP 行为、了解实际 API 路由或判断与 zotero-mcp 的能力差异时，读 [web-api.md](references/web-api.md)。

## 能力边界

仅实现 Zotero 官方 Web API 提供的数据访问和由这些 API 组合出的库管理。全文依赖已同步的索引及其完整度；空结果不能推断未同步的本地文献不存在。保存的搜索只提供定义的管理，不能执行桌面端 saved search。

不实现语义检索、embedding、本地数据库/Local API、PDF 解析/页图/布局、自动标注定位、第三方 DOI/ISBN 元数据补全、开放获取下载、Scite/OpenAlex、桌面 RSS 或阅读器 UI 控制。DOI/URL/ISBN 可作为明确的元数据字段写入，但不能宣称仅凭标识符自动获取了完整元数据。
