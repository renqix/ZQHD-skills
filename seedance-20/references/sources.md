# Seedance 2.0 来源登记

核对日期：2026-10-30。动态平台参数再次使用前仍需刷新。

## 官方

- [火山方舟 Seedance 2.0 系列提示词指南](https://docs.volcengine.com/docs/ark/seedance-2-0-prompt-guide?lang=zh)：本轮取得正文；明确参考、编辑、延长与组合任务，主体绑定、顺序分镜、声音符号；提示精确时间控制不稳定。视频数量/总长有官方条目，但不据此补全未核对的其它上限。镜像入口可能因语言/抓取状态返回不同内容，以取得的正文为准。

- [Seedance 2.0 官方模型页](https://seed.bytedance.com/zh/seedance2_0)：确认文字、图片、音频、视频四模态输入，以及参考对表演、光影、运镜和音画联合生成的定位。
- [Seedance 2.0 官方发布文](https://seed.bytedance.com/en/blog/seedance-2-0-%E6%AD%A3%E5%BC%8F%E5%8F%91%E5%B8%83)：确认 2.0 的统一多模态音视频联合生成架构和四种输入模态。
- [Seedance 2.0 User Manual 官方 Lark 入口](https://bytedance.larkoffice.com/wiki/A5RHwWhoBiOnjukIIw6cu5ybnXQ)：2026-09-03 曾被登录拦截；本轮未重读，不把旧访问状态当作当前不可访问的证明。
- [Seedance 2.0 Real-world Cases 官方 Lark 入口](https://bytedance.larkoffice.com/wiki/LJXzwehluiFdzKkb1recZdfonZg)：历史来源，本轮未重读。

## 社区

- [Emily2040/seedance-2.0](https://github.com/Emily2040/seedance-2.0)：社区项目；吸收导演意图、镜头合同、连续性状态、首尾帧和失败诊断，不直接继承动态参数、平台矩阵、价格或模型 ID。
- [dexhunter/seedance2-skill](https://github.com/dexhunter/seedance2-skill)：社区 2.0 提示词 Skill；吸收参考素材角色、镜头语言和可复制模板，不把其输入限制表当成跨平台官方限制。
- [ByteDance/agentkit-samples 的 Seedance 广告复刻 Skill](https://github.com/bytedance/agentkit-samples/blob/main/skills/byted-bp-seedance-viral-creative-rewrite-skill/SKILL.md)：本轮通过 GitHub 读取。它是官方组织的特定广告重写示例，区分参考模板的结构与产品图的身份；其专属确认状态机不升级为本技能通用门控，不取代用户已有授权，也不是通用 2.0 手册。

## 说明

本 Skill 不保存密钥，不承诺任何平台可用性；需要 LibTV 时先读取 `libtv-cli` 并查询当次模型/节点 schema。任何 `star-video2-mini` 等本地模型键都只能作为已核对的平台适配结果，不能当成通用 Seedance ID。
