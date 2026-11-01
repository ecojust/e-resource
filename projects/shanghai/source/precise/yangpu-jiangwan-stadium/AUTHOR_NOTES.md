# 江湾体育场历史主场模型制作说明

本件以两半独立地图看台源1646／1816约束平面，制作敞开的普通阶梯看台、红砖外圈、西门三大拱外立面及带局部平棚的场内特别台、有界东侧平台，并概括南、北短端不同的入口。西门内外归属由1934设计图标题和2013／2017／2021照片共同支持；短端朝向是照片背景与地图长轴对应的推断，不是照片GPS测绘。

内场保持真正空白，不在建筑资产中加入草地、跑道或场地板。现代高尔夫棚网、照明高塔、场内独立建筑、体育馆与游泳馆不属于本模型；主图已有独立源由定位合同保留。本件不等于整个名录b1-021或某一历史年份的完整复原。

全部米高、开间、隐藏构造及雕饰尺寸均为作者估计。普通近景28级座席、远景20级，顶11.15米，外圈石压顶12.01米；20级远景是简化档，不能当作确认的现状座席数。西门主墙16.4米，双鼎最高约18.63356米，局部棚板顶14.075米、前檐顶14.225米。文献20米是次级司令台说法，未设置成整圈高度；760米设计周长和17米看台宽度不是现状高程。

南端概括四竖块、中央矩形通道与两小侧拱，中央通口7.2米宽、6.2米高，最高约15.1米；北端单口双侧块，通口7米宽、5.7米高，最高约13.24米。两端中央通口沿原地图间隙真正贯通。西门外三大拱约5.5米深处保留小拱门后止挡，场内三小拱和普通砖拱也有铁门／阶梯封挡，不能冒称所有门都直通草场。当前仅提供俯瞰，不开放室内或座席登阶步行。

西特别台场内墙与座台核心之间的连续前沿平台按2017照片补齐，顶4.50米、底4.35米，跨接两侧接缝而不填成地面墙；三小拱前部凹进和后门保持。西门两中柱到棚后缘另有13.40–13.75米高位连接梁，属于作者对隐藏构造的有界估计。新原始／完整网页档在西粗源内剩余49.906平方米平面差值，远景档49.922平方米，其中北侧翼约28.27平方米、场内外缘约17.19平方米；精确差值以定位合同逐档记录为准，不能把差值全部解释为已核实的天井或通道，也不宣称逐面复刻全部源占地。完整替换指旧粗略城市源的显示替换。

普通看台体与外墙独立闭合，在墙后保留门窗的局部凹进；顶层11.10–11.25米的窄后步道连接看台与外墙，它是架空上层结构，不能投影成地面障碍。作者组件分别闭合、正体积、绕序一致，未宣称全模型经过布尔并集。字牌保持无字板，雕花、石缝、檐带和鼎为原创简化几何；六张参考照片仅供研究，不嵌入模型或随仓库分发。

## 重建

脚本放置于 `source/`，与 `common/photo_architecture.py`、`model-parameters.json` 保持相对位置。Python依赖见 `source/requirements.txt`；原生文件需Blender4.3.2，打包使用gltfpack0.25。

```sh
python source/build_model.py --out /tmp/jiangwan-build
python source/build_model.py --lod --out /tmp/jiangwan-build
python source/verify_author.py --out /tmp/jiangwan-build/author-geometry-checks.json
python source/verify_author.py --lod --out /tmp/jiangwan-build/author-geometry-checks-lod.json
blender -b -t 2 -P source/build_native.py -- --raw /tmp/jiangwan-build/yangpu-jiangwan-stadium-raw.glb --out /tmp/jiangwan-build/yangpu-jiangwan-stadium.blend --previews /tmp/jiangwan-native --views front,oblique,rear,roof,gate,grandstand,end --samples 12
python source/package_assets.py --raw /tmp/jiangwan-build/yangpu-jiangwan-stadium-raw.glb --lod /tmp/jiangwan-build/yangpu-jiangwan-stadium-lod.glb --native /tmp/jiangwan-build/yangpu-jiangwan-stadium.blend --out /tmp/jiangwan-assets --gltfpack /path/to/gltfpack
python source/verify_serialized.py --asset /tmp/jiangwan-assets/yangpu-jiangwan-stadium-raw.glb --probes /tmp/jiangwan-build/surface-probes.json --out /tmp/jiangwan-build/serialized-raw.json
```

压缩网页版需先用gltfpack解码后执行同一实际三角检查，不能把压缩扩展未加载的空网格当作通过。完整网页档保留全部原始三角的有向FLOAT32坐标与材质，远景档独立重建并逐项检查；三档都需验证内场和两端中央洞口实际为空。

共用闭合拉伸、立面坐标、车削／杆件及GLB导出工具沿用仓库内MIT代码，来源见 `source/HELPER_PROVENANCE.json`。本栋参数与阶梯环、西门、短端门构造为新编原创几何。地图平面参考遵循ODbL-1.0；文献和照片保留各自权利。
