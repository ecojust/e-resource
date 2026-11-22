# 虹桥疗养院的四层退台与日光晒台

1934年前后的虹桥疗养院位于老伊犁路2号，主楼由建筑师奚福泉设计。南侧阳台逐层内收，让日光照到各层病房。这里重建南立面的一个剖段、四层退台和顶层晒台。1938年迁至霞飞路的是后来的院址。[上海城建档案图文](https://www.thepaper.cn/newsDetail_forward_6240784) · [地址及两处院址](measurements/sources.json) · [模型预览](../../../hongqiao-sanatorium-sun-terraces.html)

## 剖面与晒台

剖面左上有标为0到4的图尺，每一分格约53个像素。三段退距分别为2.06、2.34、2.32格，与档案文章所说的每层后退“六七尺”相合。扫描图上的图尺单位难以辨认，重建按一格约一米换算；从四楼廊柱到外栏约4.59米。[剖面取点](measurements/drawn-section.json) · [尺度换算与假定](measurements/terrace-frame.json)

晒台原照保留了方砖交点、两根廊柱、四道转角栏杆和两个花盆。近处23个格点参与拟合，另外20个格点留作核查。模型用1,700块有独立灰缝的方砖铺地，名义边长约0.228米。用近景模型中四块砖的实际端角还原每个留出的交点，与原照相比，平均平方根误差约2.37个原始像素。该误差描述图像对位，建筑尺寸均为估算。[独立格点](measurements/terrace-checker-grid.json) · [相机](measurements/terrace-camera.json) · [交点核查](../../../data/audit/hongqiao-sanatorium-sun-terraces-v1/preflight/fitted-floor-grid.json)

两把摇椅朝向不同。近椅的连续低弧、扶手和布座边缘，远椅的靠背小环和交叠的前弧，分别从原照记录与拟合。方格地面给出两把椅子的位置，扶手厚度、布缝、隐蔽连接及花盆内枝叶为近似。模型用低饱和材质表现黑白照片可辨的明暗，原饰面配色未能查实。[两椅122个可见点](measurements/chair-observations.json) · [摇架的空间曲线](measurements/chair-profiles.json) · [两个花盆](measurements/potted-evergreens.json)

名录的历史名称为虹桥疗养院，所列使用单位为上海血液中心。现存资料能用于辨认老主楼；1934年楼基相对当代街区的位置还待查证，模型以独立历史场景发布。[历史主楼照片](measurements/historic-main-block.jpg) · [独立场景范围](../../../data/audit/hongqiao-sanatorium-sun-terraces-v1/preflight/final-placement-review.json)

## 编辑与重建

原创几何、方砖纹理和脚本均采用 MIT 许可。按下列命令可生成近景、远景和可编辑资产。[来源及许可](SOURCES-LICENSE.md)

```sh
python source/build_model.py --output sanatorium-terraces.glb
python source/build_model.py --lod --output sanatorium-terraces-lod.glb
python source/build_model.py --blender blender --out ./exports --audit ./audit
```

如需从史料图重算数字，把上海城建档案文章中的原图按来源清单存为 `archive-3.jpg`（剖面）、`archive-4.jpg`（晒台），再将环境变量 `HONGQIAO_ARCHIVES` 指向存放目录。模型重建直接读取已保存的测量结果。[图像尺寸、SHA256与原始链接](measurements/sources.json)
