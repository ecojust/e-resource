# 外滩6号 · 中国通商银行大楼

这是中山东一路6号的逐栋照片参照模型，按中国通商银行／Imperial Bank of China识别，不与9号轮船招商局、16号现招商银行或郑州同名建筑混用。原始足迹、锚点与稳定要素ID见 `geometry-input.json`。

主依据为已实际查看的Suicasmo于2025年5月1日拍摄的CC0原图，并结合上海城建档案东立面照片和1908年公版书的斜视照片。主体地层、二层与阁楼采用2／2／3／2／2共11窗；第三主层中央为4窗、全层12窗。三个主层、山墙阁楼、南端独立平顶附楼三窗轴、五座山墙、四个圆尖塔、中央三拱柱廊及各层不同券形均有实体几何。墙体一次三角化形成连续开孔墙，窗洞、侧壁、深窗框与玻璃有真实退距。

中央三层四扇窗按原图细分为四列、七排，采用独立玻璃实体和连续厚框。共127片可见玻璃使用原图的逐片采样：三层中央111片、二层中央两侧16片。黑框、石柱、墙面均不贴照片；底层、附楼、其余窗以及被阳台前景玻璃遮挡的窗片保留普通玻璃。原JPEG原字节嵌入一次，单材质 `PhotoFacade_Bund06Glass`，EXIF方向1，UV对应原始5184×3456像素。这里的反射来自一张照片，会固定在窗片上；不是全立面多视角摄影测量。

总高没有可靠实测出处。独立近似相机标定与256次敏感性分析见 `calibration-independent.json`，控制线见 `calibration-independent-controls.json`；使用地图32.218m主立面宽、照片EXIF22mm镜头及厂家传感器尺寸。约4.80／9.45／13.95m层带、22.99m最高花饰及构件厚度仍是估计。约21.25m屋脊与6.9m后退的透视一致性见 `calibration-independent-depth-check.json`，不能把这个检查当独立测高。OSM六层标签与原19.2m楼层换算没有被当成实测。

`photo-glass-controls.json`中的逐片原像素边界比初始粗窗框矩形更细：早期矩形包含了邻接白色立柱，不能继续当净窗宽。地层窗另见 `ground-opening-photo-check.json`：普通窗采用抬高窗台，中央入口保持落地拱口、不加普通窗台。附翼不在主立面平面内，其尺寸延续为明确估计。后立面缺乏清晰当代证据，保留真实非矩形地图轮廓的简单围护与屋面。1908年的铁制屋脊栏、烟囱簇和招牌未移植到当代模型。

```sh
python source/bund/photo-rebuild-v6/bund06/build_model.py --output /independent/bund06-output
python source/bund/photo-rebuild-v6/bund06/check_photo_glazing.py \
  /independent/bund06-output/bund06-raw.glb \
  --report /independent/bund06-output/bund06-photo-embedded-check.json
```

依赖Python、NumPy和Shapely2.1以上，从相邻 `../common/photo_architecture.py` 导入共用几何。构建输出GLB、构件几何清单、连续墙与全部构件FLOAT32拓扑检查、逐片UV报告；校验脚本再检查原JPEG字节、单一照片材质与合法UV。代码不渲染、不压缩、不发布。当前原始GLB为13.01 MB、91,111三角形，严格小于100 MB。预览由上层发布流程独立渲染，源码检查不替代视觉验收。

`evidence.json`汇总来源与推定边界；`references/2025-suicasmo-cc0.jpg`是CC0原图，`references/1908-imperial-bank-book-page446.jpg`是已核验的1908公版原书页。机构东立面照片未发现开放再分发许可，临时观察后已删除，未装入模型或源码包。研究缓存、生成输出副本和未确认许可素材均不在 `source-review-manifest.json` 的可发布清单中。

原创生成代码与几何采用MIT；地图足迹©OpenStreetMap contributors，ODbL-1.0。照片保留各自许可与署名；2025玻璃照片作者Suicasmo，CC0-1.0。

## 玻璃嵌框修订

本轮只把同种窗构造的玻璃前移到现有窗框前脸后20mm，玻璃厚度仍20mm；这是明确的构造估计，不是实测退距。墙洞、窗框前后面和形状、照片、UV、锚点及三角形总数保持。细节和源SHA见[修订依据](glazing-depth-revision.json)，逐材质及玻璃实体差异见[几何比较](glazing-depth-difference.json)。旧源码快照与原生预览另存 [glazing-depth-history](glazing-depth-history/README.md)，附完整输入 SHA 校验和独立恢复命令，仅适用于旧模型。新候选已通过构建、闭合、原图与UV检查；原生预览已由root明确核对，浏览器复验仍单独进行。修订已同步到项目源码与模型；最终浏览器复验仍待完成。

## 修订资产与原生检查

原始、网页、Blender及无照片远景变体已独立打包。原始与原生副本保留原字节，网页经实际解码核对三角位置、法线与UV；原JPEG保留。当前文件大小如下（MB），每件均小于100 MB。

| 文件 | 大小（MB） | 下载 |
|---|---:|---|
| 原始GLB | 13.01 | [下载](../../../../assets/models/bund/bund06.glb) |
| 网页GLB | 8.44 | [下载](../../../../assets/models/bund/web/bund06.glb) |
| Blender工程 | 18.72 | [下载](../../../../assets/native/bund/bund06.blend) |
| 远景GLB（无照片） | 0.96 | [下载](../../../../assets/models/bund/lod-v4/bund06.glb) |

root已实际查看本修订的原生预览；照片和窗框的核对范围见[记录](native-preview-review.json)。浏览器同视角及场景复验另行完成，不以原生预览替代。完整封装、LOD与来源版权检查见[打包摘要](packaging-summary.json)。

[本修订原生预览](../../../../assets/previews/bund/bund06-v6.png)；[公开玻璃差异审计](../../../../data/audit/precise-buildings-v6/bund06/glass-depth-difference.json)。
