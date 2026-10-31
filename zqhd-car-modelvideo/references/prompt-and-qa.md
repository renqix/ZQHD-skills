# 原片车辆替换的提示词与交付

本文件只把已核验的车辆素材映射到所选模型，不再维护第二套比例、保留或交付规则。替换语义沿[唯一合同](../../zqhd-video-ai/components/workflow/references/subject-replacement.md)，车辆细节沿[车辆规则](../../zqhd-video-ai/references/vehicle-core.md)；同轮已读即复用。

## 素材和路由

按实际输入固定：原视频负责镜头、场景、动作和时间；整体图负责完整目标车形体；细节图补局部。不虚构第二张图或Audio标签，不拿旧片失败画面做新车外观正向参考。已有本次模型/素材/生成授权直接沿用，未选定且影响路由时才询问。仅写词不上传、不生成。

- H3 使用[共享格式契约](../../zqhd-video-ai/components/h3/references/prompt-contract.md)；Ref2VA保留以下六段，首次/有歧义时再核对官方原文。
- Seedance 按已选2.0/2.5及其真实入口，不套H3六段、标签或另一版本参数。

## H3 Ref2VA 填写框架

下例只有本次存在相应素材时才填写；替换占位内容后交付完整中文正文。具体形体与完整替换要写清，但不把编译规则全文复制进正文。

```text
subject_definitions:
<Subject 1> 是 <Picture 1> 中的完整目标车辆：[本次可见的车身形式、车顶/座舱/尾部和部件关系]；<Picture 2> 仅补充[真实局部用途，有图才保留]。
<Video 1> 是原视频编辑源，负责[实际场景、相机、动作和时间]，不提供目标车外观。

summary:
[video editing + reference generation] 在[用户指定的完整时间范围]，完整移除[原片唯一旧车]并换入同一台<Subject 1>；新车从首次出现到最后出现始终一致，不保留旧车再渐变，不只换表面或零件。其余内容沿原片及用户明确例外。

retention_analysis:
<Subject 1> (appears in [实际镜头范围]): fully_preserved - [具体目标形体、身份与关键部件关系]。
<Video 1> (appears in [实际镜头范围]): partially_preserved - 保留[实际空间、动作、镜头和时间]；旧车身份与完整形体被替换，不继承其轮廓或部件坐标。

detailed_description:
[Shot 1] [原片初始状态，出现时即为完整新车，动作与运镜]。
[Shot N] At [实际切点], [同一完整新车的当前状态、实际动作、接触与原运镜；只补本镜必要变化，不重抄全套身份]。
[其余实际镜头与已确认尾部处理，不另造镜头或动作。]

overall_soundscape:
[实际声音方案；原音要求后期回填时如实写明，不虚构独立音轨输入。]

non_diegetic_music:
[实际约定的配乐或N/A，不凭空新增。]
```

新车按原场景等比适配，阴影/倒影跟随新形体；通用几何细节不在此重复。对超限稿按[入口长度规则](../../zqhd-video-ai/components/workflow/references/prompt-authoring-and-limits.md)同义合并，保留具体形体与全部替换范围，不能只剩“按图保持”。

## 交付

保留原稿、实际提交稿、素材顺序、回执及未核验项。返回沿[统一交付规则](../../zqhd-video-ai/components/workflow/references/return-delivery.md)执行；用户明确要求诊断时，沿[问题诊断路径](../../zqhd-video-ai/components/workflow/references/subject-replacement.md#交付与指定问题诊断)对照同一时间的输入与结果，不以文件可读替代效果结论。
