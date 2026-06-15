# Live Performance Approval Automation 中文说明

这个仓库提供一套给 AI agent 使用的演出报批材料生成工作流，用于整理和生成现场音乐演出相关的营业性演出报批资料。

它支持两类报批分支：

- **国内报批**：所有上台演员均为中国大陆居民身份证。
- **涉外/港澳台报批**：任意上台演员使用外国护照、香港/澳门/台湾相关通行证，或演员名单中出现外国、香港、澳门、台湾身份。

这是公开去敏版本，不包含真实公司公章、真实营业性演出许可证号、真实公司地址、完成案例、身份证、护照、签名或私人联系方式。

## 仓库结构

```text
docs/                                  面向使用者的 GitHub 文档
docs/zh-CN/                            中文文档
skill/live-performance-approval/       Codex skill 目录
skill/live-performance-approval/scripts
skill/live-performance-approval/references
skill/live-performance-approval/assets
```

## 快速开始

1. 按 [中文环境说明](docs/zh-CN/环境说明.md) 安装依赖。
2. 复制 `skill/live-performance-approval/assets/config/company-profile.example.json` 为本地私有配置。
3. 在 `skill/live-performance-approval/assets/templates/` 中放入你自己的 Word 模板。
4. 真实公章只放在本地私有配置或私有分支中，不要提交到公开仓库。
5. 让 agent 使用 `skill/live-performance-approval` 初始化项目并生成报批材料。

示例：

```bash
python3 skill/live-performance-approval/scripts/check_environment.py
python3 skill/live-performance-approval/scripts/init_project.py \
  --config skill/live-performance-approval/assets/config/company-profile.example.json \
  --project-dir ./example-project \
  --event-name "Example Band（示例乐队）2026 Tour" \
  --event-date 2026-11-13 \
  --approval-type auto \
  --subject applicant_a
```

## 中文资料索引

- [环境说明](docs/zh-CN/环境说明.md)
- [整体流程](docs/zh-CN/整体流程.md)
- [Agent 执行手册](docs/zh-CN/Agent执行手册.md)
- [配置说明](docs/zh-CN/配置说明.md)
- [分支策略](docs/zh-CN/分支策略.md)
- [公开去敏策略](docs/zh-CN/公开去敏策略.md)

## 安全边界

不要把真实公司资料推送到公开 GitHub。真实公司信息、公章、身份证、护照、签名、完成案例，应放在单独的私有仓库或本地未跟踪文件中。

详细规则见 [公开去敏策略](docs/zh-CN/公开去敏策略.md)。
