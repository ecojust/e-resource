# 原图、模型与来源署名

## 2022 照片与模型纹理

钉钉，**上海市鹤龙美术馆.jpg**，拍摄于 2022-07-23 11:26:03，Wikimedia Commons，**CC BY-SA 4.0**。

- 页面：https://commons.wikimedia.org/?curid=121178626
- 许可：https://creativecommons.org/licenses/by-sa/4.0/
- 原图文件：`photos/commons-121178626.jpg`
- 原图 SHA256：`a0d7d235b58c3b6c2d1c79d4441921479cea1538439c44362e35116a260bfef3`

原 JPEG 字节未改写；v3 模型仅在中央草书牌板内面进行原图 UV 选择、映射。右门两片完整玻璃统一采用估计材质，没有照片贴片，也没有将旧小样本拉伸到整扇门。两个无遮挡小区域仅用来统计数值外观颜色，不导出新的纹理图；没有把人物、商品、室内自贩机或邻铺烘入立面。

该照片的牌匾纹理改编及所发布的带纹理模型仍声明 **CC BY-SA 4.0**，应保留作者、原页面、许可链接及改编说明，并按照相应 share-alike 条件继续分发。原 JPEG 和 `glass-material-estimate.json` 的采样来源署名均予保留。

## 2016 结构对照

Fayhoo，**Zhujiajiaozhen Beidajie 222 Hao Minzhai.JPG**，2016-02-07 12:56:56，Wikimedia Commons，**CC BY-SA 3.0**。

- 页面：https://commons.wikimedia.org/?curid=48402751
- 许可：https://creativecommons.org/licenses/by-sa/3.0/
- 随源包保留原字节：`metric-source/2016-fayhoo-original.jpg`
- SHA256：`0de9bdfd14748cbb624e3847bdff68d7a5adb4d18ff9027b25e3a71d5e72584b`

该图用于门牌、结构、透视相对比例核对，未嵌入 GLB。相机分析图/标记图保留其相应署名和许可。不要把作者归到 CC0 的外滩首批模板中。

## 地图来源

© Overture Maps Foundation。聚合建筑数据库 ODbL-1.0；本栋底层轮廓为 **Qian Shi et al., East Asian Buildings**, CC BY 4.0，https://doi.org/10.5281/zenodo.8174931 ，provider `zenodo`、版本 `2024-11-01`。原始来源记录与许可证据保存在 `geometry-input.json` 和 `evidence/zenodo-license-source.json`。

OSM 地址与街桥背景：© OpenStreetMap contributors，ODbL-1.0，https://www.openstreetmap.org/copyright 。**本栋建筑轮廓不是 OSM way，也不代表 OSM 或地籍测绘精度。**

Esri 等参考底图仅曾用于研究位置核对，没有在此源码包或模型中再分发，也没有用它另画一个新轮廓。

## 字体和源码

`fonts/Qingpu222SignSubset.otf` 从 Noto Serif CJK TC Bold 制作有限字形子集，采用 **SIL Open Font License 1.1**。保留 `fonts/OFL.txt` 和 `fonts/source.json`；子集已改名。字形可读但不是照片中的毛笔字体描摹。

本目录原创构建和验证脚本使用项目 MIT 许可。脚本许可不覆盖原照片、照片派生纹理模型、地图数据库或字体的独立条款。
