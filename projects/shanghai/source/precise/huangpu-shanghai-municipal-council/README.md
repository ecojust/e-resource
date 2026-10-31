# 上海公共租界工部局历史主楼

[在上海主地图查看](../../../index.html#landmark=huangpu-shanghai-municipal-council&mode=overview)

## 资料与范围

本件表现工部局大楼／老市府大楼的北、东及部分南侧历史翼楼，保留北西历史转角与短西回翼。东北主入口的凹弧门廊、柱群和圆挑阳台，东南角的地面拱道，以及北西角的高拱窗、柱式与方门各有不同，依据实际照片分别制作。院侧以较朴素的浅色墙面和方格窗为主。

[来源登记](source-register.json)、[文献复核](../../../data/audit/municipal-council-v1/documentary-review.json)与[图像复核](../../../data/audit/municipal-council-v1/photo-review.json)记录实际取得的地方志、更新报道和设计方项目资料，以及实际查看的9张照片、3张图纸／图示和1张方案效果图。地方志记钢筋混凝土基础与框架、砖墙外贴花岗石、钢窗，由工务处建筑师特纳设计、裕昌泰营造厂承建。

名录原地址为汉口路153号，地方志记193–223号，百科另列江西中路209／215号及汉口路193号；不静默更改原始名录。名录年份1919、地方志中的1913／1915年开工与1924年（一说1922年）竣工，以及更新报道的1914年动工、1922年完工，保留各自出处，不强合成一个未经核定的日期。

地方志记原三层、局部四层，后来普遍增至四层，没有提供可信的现存米高。文中的50米塔楼是已取消的方案，不能用作建筑高度。设计方剖面带10米图尺，按原图粗略估读，典型历史翼楼的顶层外墙／屋面约18–20米，局部栏墙与角部可有差异；后退新增屋顶亭台明显更高。模型标高采用作者估计，不把新增屋顶层并作历史墙顶，也不将剖面像素估读称为测绘值。

更新工程中的西侧及西南侧围合段、后退屋顶亭台、独立红色B楼、新多功能厅和地下工程分开处理。设计方现状照片直接显示北西历史短回翼与现代简化方窗立面的接缝；改造前高位照片和项目平面支持南翼仅部分属于原楼。地方志没有这些接缝的测绘坐标，旧、新OSM轮廓的偏移也不能直接解释为拆建范围。具体保留源、局部替换与接缝估计见[定位复核](../../../data/audit/municipal-council-v1/footprint-review.json)。

设计方称原方案完成约四分之三，2024年新闻引用项目负责人称约三分之二，两者都说明原围合未完成；不按任一分数反推历史面积或切分位置。历史文献的占地4832平方米、建筑面积22705.6平方米与更新项目的整体面积口径不同，也不用于缩放地图轮廓。

2011年院景、2013年街景记录改造前状态；2024年主入口照片及设计方现状照片用于对照保留构造和新旧关系。方案效果图明确按效果图处理。照片、图纸和全文只作私人研究参考，不随模型分发、不作贴图；公开文件保留事实摘要、来源链接、作者／许可、文件散列与原创几何说明。

## 资产与重建

[四资产清单](../../../assets/models/candidates/huangpu-shanghai-municipal-council/manifest.json)：原始GLB18.64 MB、网页GLB5.96 MB、远景GLB3.33 MB、Blender9.39 MB；合计37,328,295字节。近景302,192面、远景152,708面，外包约125.54×120.70×20.20米；这些是作者模型值。375个窗洞、四主层和三种转角各自建模，未使用照片贴图。

东南拱道在街墙和对应院墙均有真实开口，内部简化侧壁、顶板与断面为作者估计；几何贯通不表示已开放用户入内行走。两个人工西端面朴素收口，屋顶为明确标注的估计封闭；没有将整个现状街坊或历史名录判为完成。各作者构件分别闭合、正体积，未宣称整楼经过布尔并集合为一个实体。[交付检查](../../../data/audit/municipal-council-v1/README.md)。

从仓库根目录重建，依赖见[source/requirements.txt](source/requirements.txt)，另需Blender与gltfpack：

```sh
python projects/shanghai/source/precise/huangpu-shanghai-municipal-council/source/build_model.py --out /tmp/municipal-build
python projects/shanghai/source/precise/huangpu-shanghai-municipal-council/source/build_model.py --out /tmp/municipal-build --lod
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-shanghai-municipal-council/source/build_native.py -- --raw /tmp/municipal-build/huangpu-shanghai-municipal-council-raw.glb --out /tmp/municipal-build/huangpu-shanghai-municipal-council.blend --previews /tmp/municipal-native --samples 16 --suffix=-v2
python projects/shanghai/source/precise/huangpu-shanghai-municipal-council/source/package_assets.py --raw /tmp/municipal-build/huangpu-shanghai-municipal-council-raw.glb --lod /tmp/municipal-build/huangpu-shanghai-municipal-council-lod.glb --native /tmp/municipal-build/huangpu-shanghai-municipal-council.blend --out /tmp/municipal-assets --gltfpack /path/to/gltfpack
python projects/shanghai/source/precise/huangpu-shanghai-municipal-council/source/verify_geometry.py --assets /tmp/municipal-assets --out /tmp/municipal-packaged.json --gltfpack /path/to/gltfpack --blender /path/to/blender
```
