# 营业性演出报批 · 公开去敏版

版本：`v2026.09.06.1` · [English](README.en.md) · [更新记录](CHANGELOG.md)

包含材料准备与网页上传两套 Codex skill，覆盖国内及涉外／港澳台项目。此公开包提供通用流程、可复用脚本和占位配置；实际制作需在本地补齐自有模板、公司资质、公章和适用审批要求，并完成验证。

## 本次更新

- 国内和涉外共用一个配置中的申报主体，主体策略与分支判断、场地方角色分开。
- 精简主入口，按任务读取参考；重用已验证资料，只重做受影响的材料。
- 修复初始化参数、未分类项目状态、旧主体迁移及缓存失效；阻止旧成品继续冒充就绪材料。
- 加入配套上传 skill：结构／材料／网页三个检查层次，核对当前账号和草稿，按文件哈希防止重复上传，有界等待与恢复。
- 发布前扫描文件白名单、敏感值和 Git 历史；本版无真实公司配置、证件、签章、固定附件或业务案例。

## 目录

```text
skill/live-performance-approval/    材料准备与验证
skill/performance-approval-upload/  国内与涉外网页上传
scripts/verify_public_package.py   公开发布检查
```

## 本地设置

1. 将两个 skill 目录分别安装到本机 Codex skills 目录。
2. 复制材料 skill 的 `assets/config/company-profile.example.json` 为忽略跟踪的 `company-profile.local.json`，填写本机构信息。
3. `applicant_policy.company_key` 与国内、涉外的 `applicant_company_key` 必须一致；场地方单独配置。占位值不能用于正式初始化。
4. 上传 skill 同样需要本地申报主体配置，详见其 `references/handoff.md`；两个 skill 的主体全称必须一致。
5. 在本地私有位置补齐模板、公章、字体和固定附件，再检查环境。公开版不包含这些资产，也不保证适用每个地区的表单。

```bash
python3 skill/live-performance-approval/scripts/check_environment.py
python3 skill/live-performance-approval/scripts/init_project.py \
  --config skill/live-performance-approval/assets/config/company-profile.local.json \
  --project-dir ./example-project --event-name "示例演出" \
  --event-date 2026-11-13 --approval-type auto
```

`auto` 表示等待演员证件确认分支。材料校验通过后仍要独立核对真实网页账号、事项和草稿，才能录入或上传。旧项目迁移会保留原成品并使其失效，需要重建和复核。

## 文档

- [配置说明](docs/zh-CN/配置说明.md)
- [环境说明](docs/zh-CN/环境说明.md)
- [执行与恢复](skill/live-performance-approval/references/shared/execution-contract.md)
- [公开去敏策略](docs/zh-CN/公开去敏策略.md)

真实证件、合同、公章、公司私有配置和完整业务案例应留在本地或内部存储。GitHub Issue 只讨论通用流程，请勿附带真实材料。
