# ZQHD Skills

中文 AI 视频提示词与原视频主体替换技能。当前发布快照：2026-10-31。

## 本次更新

| 技能 | 用途 |
| --- | --- |
| [zqhd-video-ai](zqhd-video-ai/SKILL.md) | 完整视频/广告编排或单条提示词；覆盖 MiniMax H3 五种模式、Seedance 2.0/2.5、Wan 3.0（万相）、Kling 4.0（可灵） |
| [zqhd-car-modelvideo](zqhd-car-modelvideo/SKILL.md) | 建立原片对象与目标素材的对应关系，按需要制作参考图板，再编译所选模型提示词；支持车辆、人物、动物及物品，多主体可分别绑定或按明确要求合并共用目标图 |
| [seedance-20](seedance-20/SKILL.md) | 上述入口使用的 2.0 写作依赖：参考、编辑、延长、首尾帧及连续镜头 |
| [seedance-25](seedance-25/SKILL.md) | 上述入口使用的 2.5 写作依赖：长叙事、多模态参考、延长、时间戳编辑及空间控制 |

车辆八视图与细节图只在本次确有需要时制作；已有目标图或固定映射直接复用。只要求两张图时交付图片，只要求提示词时交付完整正文；实际生成沿用户已选模型、平台、素材和授权范围执行。

本次模型资料核对日期为 2026-10-30。各指南分别标注官方能力、当前平台参数、社区参考和本地模板。Seedance 两版参数隔离；MiniMax、Wan、Kling 也分别使用自己的格式和素材角色。

## 安装

```bash
git clone https://github.com/renqix/ZQHD-skills.git
```

将以下四个完整目录放在同一个技能父目录，保留相对结构：

```text
skills/
├── zqhd-video-ai/
├── zqhd-car-modelvideo/
├── seedance-20/
└── seedance-25/
```

Codex 可使用 `~/.codex/skills/`；Claude Code 可使用 `~/.claude/skills/`。目标目录已有版本时，先备份再合并更新。不要只复制 `SKILL.md`，组件、参考、脚本及 Seedance 依赖也需要保留；这些目录之间通过相对路径读取唯一规则源。

只写提示词不需要平台凭据或付费生成工具。实际生成需用户当前环境已安装的执行能力，例如 `libtv-cli`、`minimaxh3-m1max-video` 或 `minimax-mac-gpu`，并按本次任务确认真实入口的模型与参数；本仓库此次不打包这些执行器。

参考图板的本地排版使用 Python；图片处理可使用 Pillow，已有 SVG 的 PNG 导出需要用户环境提供 Playwright 和浏览器。图片/视频模型生成依赖当前已授权的相应工具；排版脚本不替代 AI 图片生成。

## 调用示例

- “使用 $zqhd-video-ai，按 Wan 3.0 写一条 10 秒提示词，只写词。”
- “使用 $zqhd-video-ai，按 Kling 4.0 编写参考视频与产品图的素材合同和完整提示词。”
- “使用 $zqhd-video-ai，按 Seedance 2.0 编辑这条视频；保留未指定修改的内容。”
- “使用 $zqhd-car-modelvideo，把原片中的指定对象替换为目标图主体，使用 MiniMax H3，先交付完整提示词。”
- “使用 $zqhd-car-modelvideo，只制作车辆整体多视图和细节约束两张 PNG。”

既有素材、主体映射和授权直接沿用。提示词完成、供应商提交、文件取得与交付分别记录；修改规则或正文不等于授权重投、充值或公开发布。返回文件沿各技能引用的统一交付合同处理。

## 发布快照与依赖

[PUBLICATION.json](PUBLICATION.json) 记录每个发布文件的相对来源、源文件 SHA256、发布 SHA256 和适配项。个人技能目录里的内部别名在本次发布中固化为普通文件，便于下载和跨系统安装；这些副本是同一源的发布快照，应从源重新导出，避免分别手改造成分歧。Seedance 依赖一并更新。

发布版将执行技能的本机绝对路径改为按已安装技能名称查找，其它规则沿当前源文件。包中包含技能正文、必要参考、通用脚本及离线测试；排除系统隐藏文件、缓存、历史备份、个人素材、运行日志及凭据。用户本地的源技能不因发布适配而改写。

## 来源

- MiniMax H3 格式依据 [MiniMax-AI/MiniMax-H3](https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing)；官方原文及引用保留，中文正文策略在共享格式契约中明确标为本地约定。
- Wan 3.0 依据[阿里云官方提示词指南](https://www.alibabacloud.com/help/en/model-studio/wan3-video-generation-prompt-guide)。
- Kling 4.0 依据[官方发布说明](https://kling.ai/blog/kling40-kling-visual-realism-creative-control-introducing-storytelling)及[klingai-tech/skills](https://github.com/klingai-tech/skills)。
- Seedance 依据字节 Seed 与火山官方资料，具体来源和取得范围见两版的 `references/sources.md`。
- 视频生产流程参考 calesthio/OpenMontage（AGPL-3.0），保留原来源说明；各第三方材料按其原有授权与标注使用。

## 历史独立技能

仓库还保留 [h3-prompt-writing](h3-prompt-writing/) 与 [h3-product-ad](h3-product-ad/) 的历史发布目录，本次没有同步它们。使用本次多模型规则时，从 `zqhd-video-ai` 进入。
