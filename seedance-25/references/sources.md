# Seedance 2.5 来源登记

核对日期：2026-10-30。动态参数和账号权限再次使用前仍需刷新。

## 官方

- [火山方舟 Seedance 2.5 提示词指南](https://console.volcengine.com/ark/region%3Acn-beijing/docs/seedance-2-5-prompt-guide)：本轮取得检索正文，显示更新于 2026-10-22；按素材指代、事件概述、情节与全局约束写作，并区分编辑、首尾帧、延长的角色与参数。`docs.volcengine.com` 同名镜像本轮只返回页面壳（页壳显示 10-13），不据此宣称完整读取。具体摘记见 [prompt-writing.md](prompt-writing.md)。
- [火山方舟 Seedance 2.5 教程](https://console.volcengine.com/ark/region%3Acn-beijing/docs/seedance-2-5)：本轮检索正文显示更新于 2026-10-28；作为当前官方教程入口，不把官方发布容量直接视为第三方账号规格。

- [Seedance 2.5 官方发布文](https://seed.bytedance.com/en/blog/one-take-creation-flexible-referencing-introducing-seedance-2-5)：发布日期 2026-07-31；确认单次最长 30 秒、多轮延长、最多 30 图/10 视频/10 音频、时间戳级编辑、绿幕、摄像机视角、参考编辑、白模/黏土空间参考。
- [Seedance 2.5 官方模型页](https://seed.bytedance.com/en/seedance2_5)：本轮取得英文页正文；页面写 30 秒与可延长两次。发布文的“多轮”不意味着无限次，实际轮数和单次输出按入口确认。中文页的历史超时不当作本次访问结果。
- [Seedance 2.0 官方模型页](https://seed.bytedance.com/zh/seedance2_0)：仅用于理解共同的多模态音视频架构；不把 2.0 参数带入本 Skill。
- [即梦 AI 官方入口](https://jimeng.jianying.com/)：执行入口；当前可见功能、模型权限和参数以登录后的实际界面为准。

## 社区

- [LeonSooLab/seedance-2.5](https://github.com/LeonSooLab/seedance-2.5)：社区项目，仓库明确说明不是 ByteDance、即梦或 Dreamina 官方产品；吸收 2.5 的长叙事、延长、编辑、时间线和参考角色组织，不直接继承社区参数表。
- [Emily2040/seedance-2.0](https://github.com/Emily2040/seedance-2.0)：社区 2.0 Skill；只吸收导演意图、镜头合同、连续性状态、失败诊断和来源纪律，不将其 2.0 数字或平台表用于 2.5。
- [jeurtr/seedance-skill](https://github.com/jeurtr/seedance-skill)：社区合并版；吸收统一提示词骨架和故障排查，但该仓库混合多平台参数，不能照表执行。
- [ByteDance/agentkit-samples 的 Seedance 广告复刻 Skill](https://github.com/bytedance/agentkit-samples/blob/main/skills/byted-bp-seedance-viral-creative-rewrite-skill/SKILL.md)：本轮通过 GitHub 读取的官方组织特定业务示例，不是 2.5 通用手册；借用模板结构与产品身份分离，不把该业务专属的确认门、收费警示或返回检测引入所有提示词任务。

上述未注明“本轮”的社区项目保留为历史检索入口，未逐一重读，不宣称其当前内容已通过审核。

## 平台边界

官方发布文的能力不等于所有接入面都开放。当前平台的比例、清晰度、时长下限、音频开关、延长/编辑入口、价格、区域和模型 ID必须当次核对。若使用 LibTV，先读取 `libtv-cli` 并查询当前 schema；本地曾验证的 `star-video2.5` 只能作为本地适配结果，不是通用官方模型 ID。本文件不保存密钥或 Cookie。
