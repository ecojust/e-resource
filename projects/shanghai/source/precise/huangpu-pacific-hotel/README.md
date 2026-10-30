# 金门饭店／华安大楼历史主楼外观候选

[查看模型](../../../pacific-hotel.html) · [资产清单与下载](../../../assets/models/candidates/huangpu-pacific-hotel/manifest.json) · [检查记录](../../../data/audit/pacific-hotel-v1/README.md)

本件制作南京西路104号历史主楼及屋顶钟塔。华安合群人寿保险公司大楼、华安大楼、华侨饭店和金门饭店是同一历史建筑的名称／用途沿革，不能按别名拆为两栋。经营资料另见108号；现代酒店北楼、邻近高楼和室内不在本件范围，未原址配准或替换城市地图对象。

## 资料与尺寸

[来源登记](source-register.json)和[文献复核](../../../data/audit/pacific-hotel-v1/documentary-review.json)保存实际读取来源、摘要、字节与SHA256。2024年上海市国资委介绍及《上海名建筑志》记载38.16米、工字形平面、石柱底层和屋顶9米钟塔。另一官方志书记36.16米；各来源的8／9／10层及改建叙述未完全统一。本模型选择38.16米为总高，钟塔从29.16米到38.16米是作者的造型解释，**并未核实9米塔高与建筑总高的计量端点**。

2026年招标镜像另列南楼40.1米、北楼24米及不同建筑面积，属于未与历史尺寸绑定的项目量；不能直接用于校正本件或把北楼并入。官方资料记1924年开工、1926年竣工，名录／百科中的1933年另保留为冲突。

42×36米主体、中央前退4米／后退6米均为设计估计。两翼9层、中央8层只是模型分层，不代表已证实的历史楼层数。冻结地图只有约44.31×43.11米的粗四边形，不能验证完整工字形轮廓、天井、朝向或北楼分界，本模型没有直接挤出该地图对象。[地图范围审查](../../../data/audit/pacific-hotel-v1/footprint-review.json)

实际查看Livelikerw摄于2013年12月5日的[Commons照片](https://commons.wikimedia.org/wiki/File:Pacific_Hotel_Shanghai.JPG)，许可为[CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)。保留其可见的两侧高翼、中央后退墙面、五层通高窗带、三处石栏阳台、重檐及双层柱廊钟塔，钟塔含金色圆顶和红褐色小灯亭。树木遮挡的入口、侧背面、屋面连接、柱式、雕饰和尺寸为推估。照片中钟塔下的中央抬高窗亭（拱形中龛、两侧列柱及小尖饰）在模型中压为平直窗带和屋顶；中央顶部小窗层、复合重檐、钟塔下部曲面及浮雕均简化，不能用本件层数和屋顶高差反推实楼尺寸。钟面10:10为示意；颜色为纯色近似。照片仅供观察，没有取样、嵌入或随包分发；本件原创建模代码与几何采用MIT。文字来源不推定具有全文再发布许可。[独立照片复核](../../../data/audit/pacific-hotel-v1/photo-review.json)

## 重建与检查

从仓库根目录执行；Python依赖见[source/requirements.txt](source/requirements.txt)，另需Blender和gltfpack。

```bash
python projects/shanghai/source/precise/huangpu-pacific-hotel/source/build_model.py --out /tmp/pacific-build
python projects/shanghai/source/precise/huangpu-pacific-hotel/source/build_model.py --out /tmp/pacific-build --lod
python projects/shanghai/source/precise/huangpu-pacific-hotel/source/verify_geometry.py --assets /tmp/pacific-build --out /tmp/pacific-geometry.json
blender -b --python projects/shanghai/source/precise/huangpu-pacific-hotel/source/build_native.py -- --raw /tmp/pacific-build/huangpu-pacific-hotel-raw.glb --out /tmp/pacific-build/huangpu-pacific-hotel.blend --previews /tmp/pacific-previews
python projects/shanghai/source/precise/huangpu-pacific-hotel/source/package_assets.py --raw /tmp/pacific-build/huangpu-pacific-hotel-raw.glb --lod /tmp/pacific-build/huangpu-pacific-hotel-lod.glb --native /tmp/pacific-build/huangpu-pacific-hotel.blend --out projects/shanghai/assets/models/candidates/huangpu-pacific-hotel --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
python projects/shanghai/source/precise/huangpu-pacific-hotel/source/verify_geometry.py --assets projects/shanghai/assets/models/candidates/huangpu-pacific-hotel --out /tmp/pacific-packaged.json --blender /usr/bin/blender --gltfpack projects/shanghai/source/city/detail/tooling/node_modules/.bin/gltfpack
```

作者构件分别闭合，相接构件未做整栋布尔并集。压缩器合并底墙与地台的同位边后，花岗岩底座材质批次存在索引拓扑绕序告警；逐材质有向三角面（含重复次数）与未压缩导出完全一致，未发生面翻转。报告保留该拓扑限制，不宣称整栋是单一流形。近远景保持相同整体包络，远景减少窗格、齿饰和圆形分段。Blender文件包含另计的摄影棚地面、灯光和相机。

网页检查需Playwright与Chromium。启动`python -m http.server 8782 --directory projects/shanghai`，运行`node projects/shanghai/data/audit/pacific-hotel-v1/qa-browser.cjs`。可用`MODEL_URL`和`QA_OUTPUT_DIR`指定页面及报告目录。仅支持模型外包以外的平地漫游，不支持进入门厅、登楼或室内；35米模型范围、46米场地边界沿用共享运行代码。
