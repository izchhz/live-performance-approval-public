# 报批上传数据交接

## 文件位置与旧数据迁移

先查项目根目录，再查 `00_项目主档/报批上传数据.json`。只有一份就原地维护；两处内容不同则先确定权威版本，不自动拼接。首次生成时有 `00_项目主档/` 就放该目录，否则放项目根；不放入最终提交材料目录。`project_root` 相对 JSON 所在目录解析：放主档子目录时通常为 `..`，放根目录时通常为 `.`。

从 [国内模板](../assets/domestic-upload-template.json) 或 [涉外模板](../assets/foreign-upload-template.json) 起步。`项目主档.json`、核对表用于交叉验证，最终附件以 `03_最终提交材料/` 正文为准。核对表从同一 JSON 生成，不另建第二套解析结果。

当前 `schema_version` 为 `2026-09-05-v6`。旧数据先保留带时间戳副本，再按新模板迁移已核实字段，保留来源与附件哈希；不能只升级版本号。涉外旧 `expected_applicant_entity` 合并到必填 `applicant_entity`，两者冲突就记录。两分支统一主体以 [配置](../assets/config/applicant-policy.example.json) 为准；任何旧主体材料必须先解决正文、许可证及委托关系冲突，不能只改 JSON 或替换已签章 PDF。新增门禁默认 `false`，旧网页状态全部失效。

私有或自定义 Skill 固定资产还须在同一配置的 `asset_pins` 中按 `asset_path` 登记 `sha256`、`size_bytes`、`slot`、`kind`、`approval_branch`；文件被替换后不能仅重算项目 JSON 来绕过原固定资产约束。合法换版须核对正文并显式更新配置中的 pin。

主体配置读取顺序为 `assets/config/applicant-policy.private.json` → `applicant-policy.local.json` → `applicant-policy.example.json`，使用第一份存在的文件；存在但无效时失败，不静默回退。公开版由示例复制为 local 并填写真实主体，空示例不能通过材料/上传校验。

## 字段与执行顺序

每个可复制字段含 `semantic_type`、`value`、非空 `source`、`target_field`。主体字段来源必须包含实际最终材料证据，配置只提供预期主体。页面枚举与原材料不同则另存 `source_value` 和 `mapping_reason`。

对象的 `sequence` 从 1 连续递增且与数组顺序一致。`stable_key` 用于续填，可由以下值的规范 JSON 做 SHA-256 并加对象类型前缀：演员 `[序号, 姓名, 证件类型, 证件号的SHA-256]`，节目 `[序号, 标题]`，国内计划 `[序号, 起止日期, 场所]`，涉外场次 `[序号, 日期, 场所, 起止时刻]`。键本身不暴露证件号。修改对应内容必须重建键；仍需逐字段与实际页面对账，不能只看键。

两分支演员都用 `performer_category.value: mainland | non_mainland`；国内不得包含非内地演员，涉外至少一名非内地演员，混合项目走涉外。涉外每个 `sessions` 元素代表一场，`represented_session_count` 固定为 1，数组长度等于 `declared_session_count`。

## 附件协议

附件仅放入 `performers[].upload_order`、`programs[].upload_order`、国内 `performance_plans[].upload_order` / `material_uploads` 或涉外 `venue.upload_order`。每个元素必须为对象，不能混用字符串路径清单。

| 字段 | 规则 |
|---|---|
| `target_key` | `branch/step/object_sequence/精确槽位`；step 为 `performer`、`program`、`plan`、`venue` 或 `materials`；后两者对象序号为 1 |
| `slot` / `kind` | 页面精确槽位 / 文件语义角色；主体申请表、主体许可证、委托书分别用 `application_form`、`applicant_license`、`authorization_letter`；节目单/名单用 `program_list` / `performer_list`；演员证件/同意函用 `performer_id` / `performance_agreement`，监护人同意函用 `guardian_consent`；国内场地证明/涉外场所同意材料用 `venue_proof` / `venue_consent`，消防用 `fire_safety` |
| `sequence` | 同一目标槽位中的顺序，从 1 连续；实际执行顺序为数组顺序 |
| `document_role` / `document_owner_entity` | 文件用途 / 正文所属单位；不适用时所有者可空，主体材料必须等于统一主体 |
| `upload_method` | `local`、`shared` 或 `skill_asset` |
| `path` / `asset_path` | `local` 用项目根相对路径，`skill_asset` 用 Skill 根相对路径；禁止绝对路径或越出根目录的符号链接 |
| `filename` / `size_bytes` / `sha256` | 完整文件名 / 实际非零字节数 / 小写 SHA-256 |
| `derived_from` | 转换件原始项目相对路径；原件为空 |
| `upload_id` | 本地及 Skill 资产为 `target_key + ":" + sha256` |

网页共享材料不填 `path`、`asset_path`、`size_bytes`、`sha256`，须填 `shared_material_title`、`shared_material_id`、真实 `document_owner_entity` 和 `document_role`，`upload_id = target_key + ":shared:" + shared_material_id`。上传前还须核对网页共享库中的真实单位，不能只相信 JSON。

公开模板不附场地或消防文件；配置适合本项目的本地材料，填写实际归属、大小和 hash。使用前核对正文场地、材料权属及有效性，不能将品牌名代替权属单位。国内每计划必须有 `venue_proof`，涉外必须有 `venue_consent`。场地与消防类材料所有者须非空。涉外 `venue.fire_safety_requirement` 记录 `required` 和非空 `source`；以当前场所类型、页面槽位或明确材料要求为依据，不能为过校验把 required 改为 false。材料规则不明时可先只读查网页；未完成材料/主体校验前仍不录入、不上传。要求消防时恰好一份，不要求时不硬传。

文件格式预检不验证 DOCX/PDF 内容、电子签名或媒体可播放性，正文、签章及必要渲染核验仍需完成。

## 材料和网页分别验证

### 材料阶段

在 Skill 根目录运行：

```bash
python3 scripts/validate_upload_data.py /项目绝对路径/报批上传数据.json --stage materials
```

默认也是 `materials`。验证器始终检查实际数据，不因保存的就绪值为 false 而跳过；空模板、旧主体、错误分支、缺文件、hash 不符、错误槽位、日期和重复项会失败。填写完所有材料核验 `qa` 后再运行；其中 `cross_file_consistent`、`signed_materials_checked`、`applicant_documents_match_policy` 等必须基于正文与签章观察，不能为通过脚本而改成 true。

成功输出 `MATERIALS_SHA256`，保存为本次网页核验预期摘要，并设 `ready_for_portal_check: true`。它只说明数据预检通过，不代表当前页面已核对。开发模板时 `--stage schema` 只检查结构，输出明确注明不能据此上传。

### 当前网页阶段

每次新会话、换账号、事项、草稿或材料改变，先重置 `ready_for_upload: false` 和 `runtime_qa`。只读核对 host、事项、当前演出/草稿、已有行和附件，以及账号和草稿实际主体。涉外主体不在表单显示时去企业信息/草稿详情查证；无法取得证据即阻塞写入。

用当前观察记录 `runtime_qa`：

- `checked_at`：含时区的 ISO 8601 时间，启动一次填写批次前 30 分钟内；超过时限时重新只读检查，不要求重新登录。
- `portal_session_fingerprint`：当前 host、账号/主体标记和本次会话随机标记的本地 SHA-256；不要把历史 JSON 值当当前值。
- `draft_fingerprint`：当前分支、演出名称、草稿 ID/URL 的本地 SHA-256。
- `observed_applicant_entity` 和 `applicant_evidence_source`：当前观察到的公司全称及页面证据位置，不写账号凭据。
- `materials_sha256`：本次材料校验输出的摘要；JSON 内容或附件改变后必须重验。
- 全部当前网页布尔核验项为 true 后，才设 `ready_for_upload: true`。

```bash
python3 scripts/validate_upload_data.py /项目绝对路径/报批上传数据.json --stage upload \
  --session-fingerprint 当前观察产生的64位摘要 \
  --draft-fingerprint 当前草稿产生的64位摘要
```

两个参数必须来自当前会话的观察，不能从旧 JSON 原样取值。脚本只校验记录一致性，不能认证登录状态或替代浏览器观察。长任务中在换对象/草稿或出现异常时重新确认当前上下文；不因时间经过而重复录入或上传。

校验器只打印错误代码、固定结构位置和材料摘要，不打印姓名、证件号或来源路径。退出码 0 仅对指定阶段有效；非 0 必须先处理。敏感 JSON、上传执行记录和已签章附件仅保存在本地项目或已授权私有存储。
