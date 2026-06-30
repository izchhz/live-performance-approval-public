# Live Performance Approval Automation 中文说明

这是中文说明副本。GitHub 首页默认显示的中文介绍见 [README.md](README.md)。

当前公开版版本：`v2026.06.30.1`。更新记录见 [CHANGELOG.md](CHANGELOG.md)。

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
4. 按 `skill/live-performance-approval/assets/fonts/README.md` 安装或配置本机字体。
5. 真实公章只放在本地私有配置或私有分支中，不要提交到公开仓库。
6. 让 agent 使用 `skill/live-performance-approval` 初始化项目并生成报批材料。

示例：

```bash
python3 skill/live-performance-approval/scripts/check_environment.py
python3 skill/live-performance-approval/scripts/prepare_agent_context.py \
  --project-dir ./example-project \
  --source-dir ./example-project/01_原始资料 \
  --extract-text \
  --scan-cn-id \
  --scan-mrz
python3 skill/live-performance-approval/scripts/init_project.py \
  --config skill/live-performance-approval/assets/config/company-profile.example.json \
  --project-dir ./example-project \
  --event-name "Example Band（示例乐队）2026 Tour" \
  --event-date 2026-11-13 \
  --approval-type auto \
  --subject applicant_a
```

## 中文资料索引

- [更新记录](CHANGELOG.md)
- [环境说明](docs/zh-CN/环境说明.md)
- [字体要求](skill/live-performance-approval/assets/fonts/README.md)
- [整体流程](docs/zh-CN/整体流程.md)
- [Agent 执行手册](docs/zh-CN/Agent执行手册.md)
- [配置说明](docs/zh-CN/配置说明.md)
- [分支策略](docs/zh-CN/分支策略.md)
- [公开去敏策略](docs/zh-CN/公开去敏策略.md)

## 安全边界

不要把真实公司资料推送到公开 GitHub。真实公司信息、公章、身份证、护照、签名、完成案例，应放在单独的私有仓库或本地未跟踪文件中。

详细规则见 [公开去敏策略](docs/zh-CN/公开去敏策略.md)。

## v2026.06.30.1 策略更新

- 固化国内政府公文版式：`00` 保持一页并使用可嵌入宋体；`03/04` 从最终 Word 直接导出 PDF，确保行距、签名、公章和分页一致。
- 修复 LibreOffice 字体替换引起的行距放大与溢页：使用已安装、可嵌入的宋体，并把相对行距换算为视觉等值的固定行距。
- 国内演员名单上传版多页时逐页盖章；场地同意函公章同时覆盖场地方公司名称和日期。
- 加强节目单列宽、外文歌词逐句翻译、全角括号、标题跨页和证件有效期起止日期规则。
- 明确涉外文件不写提供人、涉外消防文件原样输出，并删除歌词中的非歌词结构标签。
- 记录已验证的 Word、PPT、Excel、数据处理和 PDF 本地 Python 工具链版本。
- 公开版仍不包含真实公司资料、公章、证件、私人字体、固定证明或完成案例。

## v2026.06.26.1 策略更新

- 新增本地中国居民身份证 OCR 脚本 `scan_cn_id_ocr.py`：使用 PaddleOCR 提取姓名、性别、民族、出生日期、身份证号、签发机关和有效期限，并输出结构化 JSON/Markdown 报告。
- 新增本地护照/港澳台证件 MRZ 脚本 `scan_passport_mrz.py`：按 ICAO Doc 9303 校验护照 MRZ；支持已训练的港澳台通行证 MRZ 字段提取和校验策略。
- 新增 `prepare_agent_context.py` 上下文包：可通过 `--scan-cn-id` 和 `--scan-mrz` 在 agent 阅读原始证件图片前先完成本地结构化提取，减少敏感图像进入上下文。
- 公开版保留通用脚本和占位项目主档，不包含真实公司主体、公章、许可证号、地址、营业执照、消防许可、身份证、护照或完成案例。

## v2026.06.24.1 策略更新

- 补充国内报批高风险规则：`00` 号申请表必须严格沿用训练好的 Word 模板和页面几何，不得用手动画表或简化版式替代。
- 明确总演员名单和单曲参与人员的区别：`00/01/02/03/04/08` 使用所有实际上台人员；`05/06/07` 按每首歌实际参与人员填写，特殊曲目写入提醒清单。
- 强化字体与签名 QA：提供人、核验文字和授权签名必须使用配置中的固定手写字体，先做字形覆盖检查；出现方框、缺字或溢出时停止交付。
- 公开版去敏策略新增授权人姓名、固定身份证明、营业执照、消防许可等附件检查项。

## v2026.06.22.2 策略更新

- 港澳台证件如果存在 MRZ，也应优先用 MRZ 提取和核对信息。
- 已测试台湾居民往来大陆/内地通行证三行 MRZ，可校验通行证号码、有效期和出生日期。
- 身份信息锁定流程优化：先完成证件 OCR + MRZ 校验 + 异常提醒，再生成 01/02/03/04 等下游文件。

## v2026.06.22.1 策略更新

- 补充公开更新记录中遗漏的涉外护照 MRZ 校验策略：护照信息需要按 ICAO Doc 9303 TD3 机读码字段和 `7, 3, 1` 模 10 权重校验后，再填写护照号、出生日期和有效期。
- 涉外歌词标题只保留 `序号 + 歌名（歌名翻译）`，不得在歌曲标题后附带演员名单、乐队成员名单或艺人名单；歌词正文和翻译规则不变。
- 本次歌词标题修改只适用于涉外/港澳台报批，国内歌词规则不变。

## v2026.06.17.1 策略更新

- 涉外拼盘项目的视频材料按乐队/艺人组合分别计算：每个乐队通常需要 1-2 首视频，不按整场项目只准备 1-2 首。
- 涉外 `02_艺人证件扫描件` 的 Word 页面只放证件或护照扫描图像本身，不额外添加姓名、标题或说明文字；姓名只保留在文件名中。
- 涉外 `04_艺人同意函` 的模拟签名按姓名文字系统区分：英文/拉丁姓名使用英文 signature 字体，中文姓名使用中文手写字体；如有真实签名且人数匹配，优先使用真实签名。
