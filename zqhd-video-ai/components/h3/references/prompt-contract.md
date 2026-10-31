# H3 共享提示词格式与语言契约

此文件统一 H3 字段、标签、模式对齐和默认语言。模型参数、素材规格与运行器能力仍按当前入口核验；创意 brief、广告三段式编译稿和模式案例是创作层，最终模型正文映射到本契约，不把文档段名当作 API 参数。

提示词语言遵循下方公共规则：换老师已明确指定新项目正文默认中文。字段名、标签、镜头编号、关键帧对齐指令保持官方写法，台词、歌词和画面文字逐字保留原文。官方 GitHub 改写原文的英文要求作为来源保留，本地中文策略不冒称官方统一要求。

按实际模式读取一份权威原文：[基础模式](base-en.txt) 或 [Ref2VA](ref-en.txt)。以下为共用摘记；官方原文更新时同步核对本契约和中文蒸馏，不能只更换原文就声称整套规则已经兼容。

2026-10-30 已核对[官方 GitHub 写作技能](https://github.com/MiniMax-AI/MiniMax-H3/tree/main/skills/h3-prompt-writing)：该目录最新提交 `a107547fa6`（2026-08-11），本地两份原文与官方一致，本轮没有改写官方 txt。官网[视频说明](https://platform.minimax.cn/docs/guides/video-generation)与[功能示例](https://platform.minimax.cn/docs/guides/video-prompt)也已核对；官网中文示例与 GitHub 英文改写策略分别保留。这里维护 H3，不把旧 Hailuo 型号的运镜标签或其它模型模板当作 H3 固定文法。

初稿与执行前长度处理统一读取 [提示词初稿与实际入口超限处理](../../workflow/references/prompt-authoring-and-limits.md)：先按官方格式准确书写，以真实参考图减少无效重复；不无条件压缩。超限处理按公共规则区分实际通道，不在本契约另设优化次数。H3 的模式、六段或三字段、对齐指令与用户文字不能因此改变。

## 字段与对齐规则

### 3.1 对齐指令（仅关键帧模式）

必须是提示词**第一行**，后空一行再接核心字段。T2VA 没有对齐指令，直接从核心字段开始。

- I2VA：
```text
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.
```
- FL2VA：
```text
How the reference pictures align with the target video — Picture 1 (from Shot 1) aligns with the 0.00-second mark of the target video; Picture 2 (from Shot N) aligns with the S.SS-second mark of the target video.
```
- L2VA：
```text
How the reference pictures align with the target video — <Picture 1> (from [Shot N]) aligns with the S.SS-second mark of the target video.
```

`N` 是实际最后一个镜头的编号，`S.SS` 是实际时长、保留两位小数。

### 3.2 三个核心字段（T2VA / I2VA / FL2VA / L2VA，顺序固定）

```text
integrated_multimodal_description: [Shot 1] ...

overall_soundscape: ...

non_diegetic_music: ...
```

- `integrated_multimodal_description`：沿时间线写视觉、动作、镜头、说话人、台词、演唱和画面内声音。
- `overall_soundscape`：汇总全片环境声、物理动作声和非语言人声；全静音才写 `N/A`。
- `non_diegetic_music`：只写观众能听到的配乐（乐器、速度、节奏、动态起伏）；无配乐写 `N/A`。禁止"cinematic""beautiful"这类抽象词。

### 3.3 Ref2VA 六段（顺序固定）

`subject_definitions` → `summary` → `retention_analysis` → `detailed_description` → `overall_soundscape` → `non_diegetic_music`

参考标签 `<Subject N>`、`<Picture N>`、`<Video N>`、`<Audio N>` 一经定义，在六段中含义必须保持一致。`retention_analysis` 的可见内容关系只使用 `fully_preserved`、`partially_preserved`、`attribute_transfer`、`weak_reference`。

音频关系另用 `fully_copy`、`partially_copy`、`reference`、`weak_reference`：分别表示全片完整音轨直接复用、部分时段/声部复用或复制后改动、只参考音色/节奏等属性、宽泛声音氛围。不能用视觉保留标记代替音频关系；仅借音色时不继承原台词。

这些标记表达目标关系，不证明运行器已按原信号复制声音。本机、自托管及托管入口的实际接线仍分别核验；精确保留原音时按既定制作方案回填/合成，不把提示词写成已经完成的处理。

`<Video N>` 与 `<Audio N>` 独立编号。源视频含声不自动创建音频标签；只有启用并明确使用其声音时才定义对应音轨。声音属于哪个层就在哪个字段说明复用关系：环境/音效写 `overall_soundscape`，观众侧配乐写 `non_diegetic_music`，对白和画内演唱写镜头正文。

### 3.4 时间线、镜头与文字

- `[Shot 1]` 不写时间戳，先建立风格、构图、主体、场景与光线。
- 后续镜头写 `[Shot N] At MM:SS.mmm, ...`，时间戳严格递增且落在视频时长内。
- 运镜写成自然句子：类型 + 必要时幅度 + 必要时速度；只有距离或角度微变时优先运镜，不切镜。
- 每个镜头写全描述要素：构图、主体、环境、动作、运镜、声音，以及参考内容在该镜头出现的精确时间点。
- 发声者按首次发声顺序使用稳定 `(S1)`、`(S2)`；不发声者不编号。
- 参考音频绑定发声者时复用同一个全局 `(Sx)`，不另起编号；`retention_analysis` 不写发声者编号。直接复用完整配乐中的人声片段不凭空增加角色或旁白。
- 台词、歌词逐字保留在 `<d>[语言] 原文</d>` 内；旁白用 `says in an off-screen voiceover` 并说明画面人物嘴唇闭合。
- 画面内可见文字用双引号包住原文，不翻译、不改写。
- 对白跨切镜或被片尾截断时，按所选官方原文使用 `<scenetrans>` / `<cutoff>` 并写出声音的延续；不要仅靠相同时间戳推断串联。用户原文仍逐字保留，任何必要标点规范化先说明，不悄悄改词。

