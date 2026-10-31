# MiniMax H3 官方 API 通道

2026-10-26 按[官方 V2 创建接口](https://platform.minimax.cn/docs/api-reference/video-generation-v2-create)核对。入口与模型分别确认，不能把官网概览只列出的 H3 / Max 当作完整型号表。

| 工作室选项 | 官方模型键 | 分辨率 | 整数时长 | 提示词 |
| --- | --- | --- | --- | --- |
| 超高细节 | `MiniMax-H3` | 768P、2K | 4～15 秒 | 单个 text 最多 7000 字符 |
| 超高速 | `MiniMax-H3-Highspeed` | 768P | 4～15 秒 | 单个 text 最多 7000 字符 |

Highspeed 与 `MiniMax-H3-Max` 是不同型号，不自行替换。标准继续走已选本机入口，快速继续走 LibTV；不同平台的模型键、限制与回执不能混用。官方视频模型不用于生成静态封面或身份看板，图片沿用对应图片模型。

## 完整中文提示词

用户明确要求：官方 API 两个模式都写完整中文提示词，保留主体完整形体、部件比例、身份细节、参考角色、时间线、动作条件、镜头、光影、遮挡、反射和声音。仍按[格式契约](prompt-contract.md)使用基础三字段或 Ref2VA 六段、保留 retention_analysis、固定标记与用户原文。

官方 API **不执行提示词压缩、超限二次改写、自动截断或以删细节换长度**，不调用 Context-IR 改写。7000 是上限，不是必须凑满的目标。超过上限时保存完整原稿和计数，停止提交并说明具体超限；待用户调整范围或选择其它入口。不能把文字拆成多个 text 绕过限制。提交时完整正文与已确认原稿逐字一致，保存 SHA256。

## 请求与素材

- `POST https://api.minimax.cn/v2/video_generation`，认证仅由受控执行器读取本机密钥，不能写进提示词、任务文件或日志。
- 请求包含 `model`、`content`、`duration`、`resolution`。content 必有一个非空 `{type: "text", text: 完整提示词}`；素材项使用 `image_url` / `video_url` / `audio_url`，逐项按真实输入指定 role。
- 首帧为 `first_frame`、尾帧为 `last_frame`；全参考为 `reference_image` / `reference_video` / `reference_audio`。关键帧与全参考角色不能混用。两张边界帧由已确认首尾素材取得，不能额外塞入看板当关键帧。
- 文生视频 ratio 必填且不可为 adaptive。关键帧模式为 adaptive，画幅由输入图片决定；全参考可用 adaptive 或 21:9、16:9、4:3、1:1、3:4、9:16。
- 图片最多9张（首、尾各最多1张），单张≤30 MB；视频最多3段、单段2～15秒、总≤15秒、单段≤50 MB；音频最多3段、单段2～15秒、总≤15秒、单段≤15 MB。混合素材总数≤12；请求体≤64 MB。图片/视频宽高256～5760，宽高比0.4～2.5；视频帧率23.976～60，H.264/H.265，原视频音频AAC/MP3。其它格式按当次官方接口核验。
- 素材可用公网URL、已上传的 `mm_file://` 或官方支持的data URI。顺序与提示词编号一致；兼容副本保留原片来源与哈希，不缩短原片或静默换素材。
- 当前 H3 / Highspeed 没有公开的 extra 提示词扩写参数；不把 Max 独有的 `prompt_expansion_mode` 塞入这两个型号。

## 单次提交与恢复

提交前保存原稿、请求参数与素材顺序/哈希，先登记唯一提交意图。获得 task_id 后立即保存，按[官方查询接口](https://platform.minimax.cn/docs/api-reference/video-generation-v2-query) GET `/v2/query/video_generation/{task_id}` 查询原任务。成功后取 task.content.url，下载并保存供应商结果、SHA与回执。超时、连接断开或返回不明时保留未知状态，不能自动再次POST；已有ID只继续查询。查询范围官方当前为最近7天。

官方API接入、技能维护和提示词交付不自动授权新增付费制作、充值或重做历史项目。所有产品按已有授权与本次交付要求执行；返回交付沿[统一规则](../../workflow/references/return-delivery.md)，代码测试不冒充真实供应商执行。
