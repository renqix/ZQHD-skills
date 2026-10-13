# 原片车辆替换的提示词与验收

此文件在编译实际提示词或检查成片时读取，不代替平台技能和模型当前 schema。

## 素材合同

- 原始视频：镜头、空间、背景、运动和时间的最高依据。它既是编辑源，也是对照验收的母片。
- 已确认八视图：目标车辆身份、各角度几何、漆色及附件。
- 已确认细节板：真实物理侧别、贴纸/文字/车标/轮毂及其它保持条件。看板背景、格线和标注不进入成片。
- 照片和看板中静态灯轮状态不能自动覆盖用户的阶段要求；原视频中的错误或用户明确纠正的状态须独立写成局部例外。

## H3 六段编译框架

只填入已查看、真实上传的素材、时长和事件，不把此框架未替换的文字提交给模型。英文模型描述，画面文字保留原文；素材顺序改变后重新编号。按 `zqhd-video-ai` 读取当前 Ref2VA 正文规范，保留完整六段。源音默认后期复制，不凭视频带声音就虚构 Audio 标签。

```text
subject_definitions:
<Subject 1> is the confirmed target vehicle in <Picture 1>, with exact side-specific details defined by <Picture 2>: [visible confirmed identity and details].
<Video 1> is the original video to edit, defining camera projection, background, foreground occlusion, vehicle motion and the complete [actual source duration]-second timeline.

summary:
[video editing + reference generation] The target video is an edited version of <Video 1>. Replace only [identified source vehicle] with <Subject 1>. Retain the complete source timeline, background sequence, camera and motion. [Explicit user exceptions, if any.]

retention_analysis:
<Subject 1> (appears in [actual shots]): fully_preserved - [confirmed geometry, paint and details].
<Video 1> (appears in [actual shots]): partially_preserved - only the identified vehicle appearance and listed exceptions change; all other visible content and event timing are retained.

detailed_description:
[Actual original shot sequence with original cut timestamps.] Match the source vehicle's position, scale, orientation, tire contact, motion and occlusion at each time. [Explicit source-derived phases and light/wheel states.] Preserve the source camera height, projection, movement and speed profile. [Correct side-specific details.] Do not add an orbit, low-angle sweep, shot, duplicated car or mirrored body graphics. Do not render board labels or arrows.

overall_soundscape:
[Requested audible environment; original audio is restored in post when preservation is required.]

non_diegetic_music:
[Requested music layer or N/A; do not invent new music.]
```

将重要动作条件写成清楚的起点与终点，例如“窗台阶段轮辐固定，只有轮胎接触真实道路才开始滚动”，而不是只写“车轮自然”。原视频没有该情节时不添加这种阶段。照明变化允许改变车漆反射和明暗，不允许把银蓝底漆变成另一颜色。

## 同时刻验收

以原片实际切点和状态变化建立检查时间点，另外覆盖首中尾。密集检查遮挡、跨场景和比例变化的前后；轮辐状态用连续帧比较，不能凭一张轮毂截图判断静止。

| 检查 | 通过依据 | 常见未达标 |
| --- | --- | --- |
| 原时长与节奏 | 探测实际时长并对照事件时间，不仅看提交参数 | 对齐帧造成超长、全段变速、遗漏尾段 |
| 背景 | 同时间点背景、前景遮挡、光照和场景顺序对应 | 跳过隧道/车厢、重绘成另一城市、提前上路 |
| 相机 | 原机位、投影、地平线、运动轨迹一致 | 新增环绕/低角度/切镜、穿窗、方向反转 |
| 身份 | 按确认看板逐面检查，左右分别核验 | 图案镜像、贴错侧、附件变形、漆色漂移 |
| 灯轮 | 状态及变化时刻匹配合同，轮辐/接触连续 | 窗台轮转、灯提前点亮、轮胎打滑、车悬浮 |
| 原音 | 实际源音轨合成与起止同步可核验 | 使用生成音轨却称原声保留 |

记录“技术通过”“抽样视觉通过”“全段视觉/音频未覆盖”各自范围；不将尺寸、下载或一次截图当成所有项目通过。
