---
name: zqhd-car-modelvideo
description: 负责原视频主体替换业务：依据原图建立主体与目标素材对应关系，按实际需要制作参考图板，再调用所选模型的底层提示词规范。支持车辆及其它主体、多主体分别绑定或显式合并共用目标图，也支持只制作两张参考图。
---

# 主体参考图板与原视频替换

本技能负责业务：替换谁、采用哪份目标素材、改变哪些内容、保留哪些原片内容，以及需要何种参考图板。`zqhd-video-ai`负责[共用替换合同](../zqhd-video-ai/components/workflow/references/subject-replacement.md)和所选模型提示词格式。已有素材映射时直接编译模型正文，不再加载完整广告流程或重新分配业务。

中文交流，称呼换老师。用户本轮已选择的制作范围、主体、目标图片、模型、模式和参数直接沿用；只有缺项确实影响执行时集中澄清。单独维护技能或只写提示词不提交生成，已有明确生成授权不重复询问。

## 1. 固定素材与主体关系

按原素材ID/SHA、实际路径和原件建立一次观察，原件只读。原视频提供旧对象定位、镜头、动作、时间和用户指定保留的场景；目标图片提供各自新主体的形体和身份。通用语义只读[唯一替换合同](../zqhd-video-ai/components/workflow/references/subject-replacement.md)，车辆证据按需补读[车辆规则](../zqhd-video-ai/references/vehicle-core.md)，不另抄一份比例规则。

分别绑定、显式合并、上传重传与重新提交均沿[固定映射](../zqhd-video-ai/components/workflow/references/subject-replacement.md#一次定位固定映射)。本业务只为已选主体收集所需目标图，同一物体跨帧仍是同一主体。

视频标注可用全片概览或用户指定原帧。制作观察密度、连续动作与真实切镜的区分、特写裁切及适配时间码，统一沿[从观察编译镜头](../zqhd-video-ai/components/workflow/references/subject-replacement.md#从观察编译镜头)，已有同SHA观察直接复用。

## 2. 只做需要的参考图板

- 已有参考图板且用户已选择使用时，直接复用，不重新制作。
- 各主体已有独立目标图时，保留原图，按需要生成带来源的编号/对应图；不为满足旧车辆模板额外生成八视图或索要多角度照片。
- 本次明确制作车辆多视图时，读取[车辆看板制作](references/vehicle-boards.md)及[生成模板](references/generation-and-qa.md)。默认两张PNG：整体多视图与细节约束图。车辆八角度是该交付的布局，不套用于人物、动物及其它物品。
- 只制作两张图的任务到此交付，不默认索取视频或扩大为视频制作。内部SVG、局部和中间图按项目保存，用户未要求时不增加交付份数。

原图中可见的具体形体用于制作；不可读文字和未见细节保留未知，不补造，不追加视觉确认门。原图局部只补本次身份或明确点名需要的部位，不重复裁切和OCR。

## 3. 编译所选模型的完整提示词

先读取[提示词初稿与实际入口超限处理](../zqhd-video-ai/components/workflow/references/prompt-authoring-and-limits.md)，再只读对应模型规范：

- **MiniMax H3**：[H3格式契约](../zqhd-video-ai/components/h3/references/prompt-contract.md)及本次模式的一份官方原文。原视频加参考图通常用Ref2VA，保留六段和`retention_analysis`；关键帧模式按实际首尾帧对齐，不混用。官方API的两个模式另读[官方通道](../zqhd-video-ai/components/h3/references/official-api.md)。
- **Seedance**：[版本路由](../zqhd-video-ai/components/seedance/guide.md)及已选2.0或2.5边界，只用该版本参数，不套H3字段。
- **Wan 3.0 / Kling 4.0**：分别读取 [Wan 规范](../zqhd-video-ai/components/wan/guide.md)或 [Kling 规范](../zqhd-video-ai/components/kling/guide.md)，明确编辑的原视频与新主体参考；不套 H3 六段，不继承其它模型的标签与参数。

每份新主体与原对象分别映射，原片时间线、动作和用户例外落实到实际镜头。完整正文采用中文，模型字段、真实素材标签、专名及用户台词/画面文字保留原文。按[原片提示词适配](references/prompt-and-qa.md)组织，不把固定规则全文抄入正文，不只留下品牌名或“按图保持”。保留完整原稿、实际提交稿、素材顺序及来源；每次改稿给完整版本。

## 4. 沿原授权执行与恢复

模型、模式和平台沿用户已有选择，规格以当前确认快照为准，不暗中换模型、降级、加次数或改变费用。LibTV调用当前`libtv-cli`，本机调用当前`minimaxh3-m1max-video`，优云沿已选运行器；只读相关入口，不装新工具或更改在跑服务。

上传前核对所选模型和实际平台的格式、容量、时长、角色和顺序；H3才读取[H3输入素材要求](../zqhd-video-ai/components/h3/references/media-preflight-and-failures.md)，其它模型沿上文对应规范。大原件需要适配时另建副本，保留原件及映射；不把某一平台限制扩成用户原件上传限制。

提交一次并保存原回执。仍在运行跟进原进程；提交未知先查原请求；分析完成复用原记录；已有文件只续传。修改规则或提示词不授权重投、改账、解除暂停或公开发布。

## 5. 返回与交付

统一使用[返回文件交付规则](../zqhd-video-ai/components/workflow/references/return-delivery.md)，本技能不再定义返回验收。已约定的原音回填和时间线适配属于制作；最终按原文件和回执登记交付，不追加门槛。

用户指定手机/iCloud位置时沿其配置回传，分别记录写入与设备端收到的实际证据。交付提供文件位置、原任务、实际元信息和完整提示词位置；只报告真实完成状态。
