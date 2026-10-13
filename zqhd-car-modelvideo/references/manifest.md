# 确定性排版 manifest

`scripts/build_boards.py` 只读取本地图片和人工核验清单，用 SVG 内嵌原始编码图像。它不生成新视角、不改写源照片、不联网、不提交任何图片或视频生成任务。Pillow 只读取尺寸、格式、帧数和 EXIF；裁切使用 SVG 视窗。EXIF 方向为 2–8 时，仅在内存中的嵌入副本归一方向元数据，再用 SVG 几何变换旋正，不重编码像素。

清单不是图像识别结果。`ready: true` 只代表人工核验元数据满足交付条件，不代表脚本检测过车色、字形、轮毂或左右侧。

**本文列出的 SVG、单视图/局部图、HTML 和收据全部是内部工作产物。** Skill 的默认用户交付固定为两张 PNG：将八个角度汇总成 `01-汽车八视图.png`，将所有关键细节与限制标注汇总成 `02-细节约束看板.png`。调整单张 B 画布高度容纳细节，不能分页或额外交付无字版、独立图、预览网页和资料包。最终交付目录只放这两张 PNG。

## 用法

```bash
python3 scripts/build_boards.py /绝对路径/manifest.json --output-dir /绝对路径/看板输出
python3 scripts/build_boards.py /绝对路径/manifest.json --validate-only
python3 scripts/build_boards.py /绝对路径/manifest.json --validate-only --require-ready
python3 scripts/build_boards.py /绝对路径/manifest.json --output-dir /绝对路径/看板输出 --single-views
```

运行环境需要 Pillow。若当前 Python 缺少 Pillow，使用已配备该库的运行环境，不为本任务擅自改变系统 Python。`--validate-only` 不写文件；默认允许缺角度的草稿，`--require-ready` 则在未通过核验时退出，不输出新看板。

## 示例结构

```json
{
  "vehicle": {
    "name": "车辆身份名称",
    "body_color": "照片可证实的车漆描述；官方色号未确认",
    "note": "仅锁定已确认的同一辆车与同一改装状态",
    "side_designs_differ": true
  },
  "sources": [
    {"id": "S01", "path": "../photos/left.jpg", "role": "左侧整车与前门贴纸"}
  ],
  "details": [
    {
      "id": "D01", "title": "左前门贴纸", "source_id": "S01",
      "bbox": [0.35, 0.42, 0.57, 0.62], "side": "left",
      "position": "左前门下半部，门缝与把手可见",
      "status": "uncertain", "text_exact": "",
      "lock": "形状、底色、位置、字序与大小比例；模糊字禁止自行补写",
      "critical": true,
      "question": "请确认这张图是车辆左侧还是右侧？",
      "options": ["左侧", "右侧"]
    }
  ],
  "views": [
    {"id": "L", "path": "../approved-views/L.png", "status": "draft", "qa_note": "等待与 S01 核对"}
  ]
}
```

此示例是结构说明，路径需要替换为实际存在的图片。不足八视图时，`views` 可以是空数组或只提供已有角度，不能用其他角度代替。

## 字段与约束

| 字段 | 含义与要求 |
| --- | --- |
| `vehicle.name/body_color/note` | 可选字符串。车色可用照片确认的描述，不要求未知的官方色号。 |
| `vehicle.side_designs_differ` | 可选布尔值，默认 false。为 true 时，除八格外，自动对已提供的六个侧相关角度分别输出无字单图。 |
| `sources` | 至少一张原图。每项包含唯一 `id` 与实际存在的 `path`，`role` 是可选用途说明。 |
| `details` | 可为空的细节数组。每项 `id` 唯一，`source_id` 必须对应 sources 中的原图。 |
| `details[].bbox` | `[x0,y0,x1,y1]`；**基于 EXIF 旋正后图片**，左上原点，归一化 0–1，分别是裁切框左上与右下；`0<=x0<x1<=1`、`0<=y0<y1<=1`，严格不得越界。 |
| `details[].title/position` | 可选字符串；标题与在车身上的物理位置。位置说明应包含门缝、把手、轮心等可追溯基准。 |
| `details[].side` | `left/right/front/rear/roof/bilateral/unknown`；默认 `unknown`。左右按车辆行驶方向定义。`bilateral` 只用于两侧分别有证据并已核验的细节。 |
| `details[].status` | `confirmed/uncertain`，默认 `uncertain`。肉眼不能辨认、被挡住、原图失焦均应保持 uncertain。 |
| `details[].text_exact` | 可选字符串。逐字可读才填写；不清楚时留空，并在 lock 中写清禁止补字。 |
| `details[].lock` | 字符串或字符串数组，描述要锁定的形状、颜色、字形、物理位置、比例与禁止变化。 |
| `details[].critical` | 布尔值，默认 true。身份相关的车标、车牌、改装、轮毂、贴纸等通常是关键细节。 |
| `details[].question/options` | 可选问题字符串与选项字符串数组。尚未确认的问题会出现在 receipt.pending_questions，脚本不会代替用户作答，也不会实现问答界面。 |
| `views` | 可为空的视图数组，每个 id 最多一项。每项 `path` 指向实际存在的该角度成图。 |
| `views[].id` | 严格为 `F/B/L/R/FL45/FR45/RL45/RR45`。分别是正前、正后、左侧、右侧、左前45°、右前45°、左后45°、右后45°。 |
| `views[].status` | `approved/draft`，默认 draft。approved 必须在外部完成人工逐格一致性核验后填写。 |
| `views[].qa_note` | 可选核验说明，建议填写与哪些原图、哪些细节对照及还存在哪些问题。 |

`id` 使用 1–64 位英文字母、数字、短横线或下划线，首位为字母或数字。三类数组分别拒绝重复 id。路径可以是绝对本地路径，或相对 manifest 所在目录的路径；不接受网址。实际图像格式只接受静态 PNG、JPEG、WebP，不接受动图或普通多帧图。苹果照片库的 HDR JPEG 可能由 Pillow 识别为 MPO，脚本接受其主 JPEG，以 `image/jpeg` 内嵌原始编码数据，仅读取主图尺寸与 EXIF，receipt 标记 `source_format=MPO`、`display_mode=primary-display`。这不等于 HDR、辅助图或增益图细节保真已核验；浏览器色调映射可能不同。

左右侧的差异不能用水平镜像消除。此脚本不改变图片构图或生成镜像；指定视图是否正确由人工核验负责。

## 输出

| 文件 | 用途 |
| --- | --- |
| `sources.svg` | 自包含原图索引，显示 source id、用途、旋正后尺寸与摘要。 |
| `details.svg` | 细节证据看板：较大原图局部、整图定位框、标题、侧别、状态、逐字文字与锁定说明。过长说明在图上截短，完整内容保留在 receipt。 |
| `details-clean.svg` | 无文字细节图版；仅原图局部，以与 details 相同的顺序排列。 |
| `detail-01.svg` 等 | 每个细节独立无文字图，最长边 1600，保留裁切宽高比。数字顺序对应 manifest.details。 |
| `multiview.svg` | 固定两行四列，依次 F/B/L/R、FL45/FR45/RL45/RR45。缺角度明确写“缺少该角度”，草稿写“未核验”。 |
| `multiview-clean.svg` | 无字固定八格，顺序一致。缺角度保持灰色空格。只有全部核验后才可作为完整视频参考。 |
| `view-F.svg` 等 | 加 `--single-views` 时输出所有已提供角度的无文字单图；左右设计不同则自动分别输出已提供的 L/R/FL45/FR45/RL45/RR45，缺角度不能补假图。 |
| `index.html` | 内嵌五张看板的本地预览，无 JavaScript、无外部图片或网络资源；单图链接指向同目录 SVG。 |
| `receipt.json` | 原图与视图的实际 SHA256、原始/旋正尺寸、EXIF 方向、输出尺寸与摘要、缺视图、未核验视图、关键未确认细节、pending_questions 及 ready 状态。 |

SVG 内图片都是 base64 自包含数据，可移走照片库后独立打开。不同查看器的中文字体可能不同，图片内容不会因此重画。SVG 本身不等于可上传的 PNG；模型不支持 SVG 时，需用可信 SVG 渲染工具导出 PNG，随后打开核对图像、文字与方向。

脚本拒绝输出覆盖清单或图片，也拒绝输出文件是符号链接。为了避免旧文件混入，版本更新或条目增减时使用新的输出目录；脚本不删除上一次多出来的单图文件。

## PNG 导出

已有 Playwright 与本地 Chromium/Chrome 时，使用 `scripts/export_png.cjs` 渲染本助手生成的 SVG，不会联网或增加原图细节：

```bash
node /绝对路径/zqhd-car-modelvideo/scripts/export_png.cjs /绝对路径/看板输出 --module-dir /本地/node_modules --browser-executable /本地/浏览器可执行文件
```

先通过当前环境的依赖定位工具查已有运行时，不把某一机器的缓存路径写成通用依赖。模块可正常解析、Playwright 浏览器已安装时可省略两个路径参数。`--max-edge 4096` 可限制最长边，仅缩小；省略时按 SVG 的排版尺寸导出。不会下载浏览器、连接用户现有标签或修改源图。输出与 SVG 同名的 PNG 和 `png-export-receipt.json`，记录尺寸与文件摘要；为避免覆盖，目标 PNG 已存在时退出，重新导出使用新版本目录。

无字 SVG 导出后仍应检查 PNG 是否包含标签、框线、裁切错误或方向错误。浏览器成功解码与生成看板一致性通过是不同的证据；尤其 MPO 主图的色调映射需实际查看。

## 交付状态

仅当以下条件同时成立，`ready` 才为 true：

- 八种规定角度全部存在，且每项 `status=approved`。
- 至少一项 `critical=true` 的细节约束，全部关键细节 `status=confirmed`。
- 所有关键细节的 `side` 已知，不存在 `unknown`。

源图可读、SVG 排版成功与上述状态是不同的证据。脚本不能判断照片里是否真的是某个角度，不能保证生成模型会遵循约束，也不能把模糊文字恢复成真实文字。核验人员必须将每个视图与原图证据和细节标注逐项对照，再更新元数据。
