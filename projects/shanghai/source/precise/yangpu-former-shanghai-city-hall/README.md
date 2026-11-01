# 旧上海特别市政府大楼（绿瓦大楼）

[在上海全局模型中查看](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=yangpu-former-shanghai-city-hall&mode=overview)

对应第一批名录 `sh-historic-b1-020`，地点为杨浦区清源环路650号、上海体育大学内；修缮资料另记长海路399号。本楼与黄浦区公共租界工部局“老市府大楼”分别建模。

## 建模范围与可见特征

范围为三段相连的历史主楼，以及经独立映射确定的南向台阶桥和必要侧阶。中央桥跨越弧形车道，桥下拱洞应保留；校园其他楼栋、后花园及塑像、运动设施和广场绿地均不并入主楼。

外观依据实看照片概括：中部高、两翼低的三段绿瓦屋面，金黄脊饰和翘檐，中央侧山墙及屋面交接；南面通高大红柱、上下格窗带、浅色有窗基座与栏杆。中央约五个主要开间，入口两侧各约两个，宽浅色端块带小窗；入口上有小挑出彩绘门罩。西侧为圆拱门、台阶、小阳台及单组上下红框窗。北面和东侧上部存在树遮，隐藏细节按作者估计处理。

主楼底图与桥阶地物须分别审核。冻结底图识别为 `3904106e-f668-46d4-a302-a13ccd00866a` / `w43779987@10`；摆放、底图替换和附属桥阶范围见[映射合同](../../../data/audit/yangpu-city-hall-v1/footprint-review.json)，地理配准与作者尺寸仍含估计。

## 已实际阅读的资料

- [维基百科：旧上海特别市政府大楼，所读版本94194159](https://zh.wikipedia.org/w/index.php?title=旧上海特别市政府大楼&oldid=94194159)：身份、四层及1933年落成、1934年迁入等次级资料。保存页自带该版本号，未另抓固定链接。
- [《中华遗产》2010年第05期：市政厅](https://www.dili360.com/ch/article/p5350c3d9b966835.htm)：周松青撰文；实际阅读公开导读与元数据，未取得付费全文。百科所列2023年引文日期不代替杂志出版年。
- [高校基建2018年修缮史与四立面转载](https://www.sohu.com/a/218602199_741845)：记四层混凝土结构、局部地下室、93米长及25/20米宽，并提供南北东西立面。文末署同程建设科技、我的大学、上海体育学院官网；原始机构测绘报告未独立取得。
- [新民晚报2019年4月9日现场报道](https://newsxmwb.xinmin.cn/xinminyx/2019/04/09/31512728.html)：孙中钦摄影报道，实际阅读正文并查看五张施工实照，补充瓦、脊饰和屋面衔接。

## 照片与时点

本次实际查看 **11张照片**：5张2018年转载中的修复前立面照片、[1张2019年10月20日东南高位完成照片](https://commons.wikimedia.org/wiki/File:上海市政府大楼·上海体育学院·俯视（东南）.jpg)，以及5张2019年4月新民施工照片。完成图作者为 Legolas1024，许可 CC BY-SA 4.0。转载及新闻照片无已确认的开放许可，仅私下观察。

施工图用于辨认三段屋面、中央山墙与翼部接合、脊饰和桥的位置；灰色基层、瓦堆、工人、脚手架及围护不进入完成模型。材料与颜色主要参考2019年10月完成图。所有图片的来源、署名、尺寸、文件哈希、实际查看记录和观察限制见 [source-register.json](source-register.json)；仓库不存原照片、全文或照片纹理。

## 尺寸与年代口径

- **米高未确定。** 底图的22米来自 CNBH 10米分辨率估值，不是实测檐高或脊高。屋顶、楼层、基座和桥洞采用明确标注的作者估计。
- 转载记长93米、中部宽25米、两翼各宽20米。优先解释为93米总长、25/20米分别为中部及翼部进深，与照片和粗底图相容；没有原尺寸图确证，不把三项宽度相加成65米正面宽。
- 转载的8982平方米为各层总面积，百科将8928平方米称为占地；数值和范围分歧未解决，不作为占地缩放依据。
- 继承名录记1935年；建筑叙述记1933年10月10日竣工、1934年元旦迁入，两者是不同事件。开工另有1930年7月、1931年6月/7月说法，保留来源分歧。

文字与照片证据分别见 [文字审阅](../../../data/audit/yangpu-city-hall-v1/documentary-review.json) 和 [照片审阅](../../../data/audit/yangpu-city-hall-v1/photo-review.json)。本目录记录来源与原创外观表达依据；资产及重建命令见下文。

## 资产与作者尺度

[四资产清单](../../../assets/models/candidates/yangpu-former-shanghai-city-hall/manifest.json)：原始GLB15,024,020字节、网页GLB6,621,884字节、远景GLB1,658,804字节、Blender7,560,381字节，合计30,865,089字节。完整近景221,980面，远景60,940面，单件均小于100 MB。

作者主楼底图长约96.31米、中央深约28.03米；中央屋脊26.7米、翼脊23.2米、最高脊饰约28.36米、南平台4.3米与桥宽10.4米为模型估计，不能作为实测尺寸。完整外包包括侧阶及南桥，约105.45×68.83×28.36米。桥与主门按照片对中；地图步行线约4.1米的轴线偏差保留在映射记录，不当作精测桥轴。

原始版与网页全量版的FLOAT32有向三角面及材质严格一致；远景单独保留主形、窗洞与桥孔，面数与投影有实际简化差异。三档各117项作者表面射线及59项独立射线通过，组件分别闭合、绕序一致且正体积，不宣称整楼布尔并集成一个实体。原生文件实际重新打开并与原始几何核对。[完整交付检查](../../../data/audit/yangpu-city-hall-v1/README.md)。

主源525及有界原近景外檐完整替换，校园邻楼保留。主楼室内采用保守地面阻挡；桥面保持架空，桥下东西向道路不会被整个桥面投影封住。当前仅开放全局俯瞰，桥面、楼梯和室内步行尚未开放。

原创细部与代码采用[MIT许可](LICENSE)；地理轮廓与相关派生元数据署名© OpenStreetMap contributors，按ODbL-1.0处理。参考照片未分发或用作贴图。

## 重建

从仓库根目录重建（Python 依赖见 `source/requirements.txt`；另需 Blender 4.3.2 与 gltfpack 0.25）：

```bash
python projects/shanghai/source/precise/yangpu-former-shanghai-city-hall/source/build_model.py --out /tmp/yangpu-build
python projects/shanghai/source/precise/yangpu-former-shanghai-city-hall/source/build_model.py --out /tmp/yangpu-build --lod
blender -b -t 4 --python-exit-code 1 --python projects/shanghai/source/precise/yangpu-former-shanghai-city-hall/source/build_native.py -- --raw /tmp/yangpu-build/yangpu-former-shanghai-city-hall-raw.glb --out /tmp/yangpu-build/yangpu-former-shanghai-city-hall.blend --previews /tmp/yangpu-native --samples 16 --views front,oblique,rear,roof,bridge,side,porch
python projects/shanghai/source/precise/yangpu-former-shanghai-city-hall/source/package_assets.py --raw /tmp/yangpu-build/yangpu-former-shanghai-city-hall-raw.glb --lod /tmp/yangpu-build/yangpu-former-shanghai-city-hall-lod.glb --native /tmp/yangpu-build/yangpu-former-shanghai-city-hall.blend --out /tmp/yangpu-assets --gltfpack /path/to/gltfpack
python projects/shanghai/source/precise/yangpu-former-shanghai-city-hall/source/verify_geometry.py --assets /tmp/yangpu-assets --out /tmp/yangpu-packaged.json --gltfpack /path/to/gltfpack --blender /path/to/blender
```
