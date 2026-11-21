# 东平路9号爱庐甲楼花园敞廊

上海市第二批优秀历史建筑名录2D046将东平路9号的音乐学院附校甲楼、乙楼合列为住宅。甲楼的参照照片题为「爱庐 东平路9号 音乐学院附校甲楼」。原图相机EXIF记载2015年7月18日18时18分拍摄，7月22日上传，定位字段只保留了GPS版本号。乙楼的独立照片可见白色外墙、砖角石和深色高山墙，与甲楼的灰色水刷石双层敞廊有别。两张原图相隔28秒，均为同日下午拍摄。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [Fayhoo的甲楼照片，CC BY-SA 3.0](https://commons.wikimedia.org/wiki/File:Ailu.jpg) · [乙楼对照照片](https://commons.wikimedia.org/wiki/File:French_garden_residence_on_Route_Garnier.JPG)

有关爱庐的记述提到蒋介石与宋美龄1927年结婚及婚房的传说。OSM登记了1930年，市房管局这条名录没有记载具体建成年份，现有资料不足以确定今天这栋甲楼的竣工日。模型取2015年照片所见外观。[相关史事](https://zh.wikipedia.org/wiki/爱庐) · [原始网页、日期、照片与足迹收据](reference-review.json)

独立地物3522与OSM建筑w674602920第1版的足迹交并比为98.73%，东平路9号爱庐地点标注落在其中。图片右侧为铺装侧道，宽券面向花园，东侧返身为较窄的上下两重券。对照2021与2024两个历史影像服务的坡屋顶、南侧庭院及东侧铺面，园侧长边约23.49米，朝向约为182.5°。影像年份为服务版本标识。实际拍摄者的精确站位无法从GPS恢复。[地块和方向](footprint-review.json) · [OSM原建筑](https://www.openstreetmap.org/way/674602920)

模型包含园侧两座敞廊、宽券与窄侧券、分块券石与角石、上层石栏及凸出的中央阳台、较低的西侧窗与斜瓦雨篷、西侧老虎窗、两根白色烟囱和一段东墙。主券后可见一处带琥珀色半圆窗的木窗。券径、栏杆曲线、廊深、屋顶高度和烟囱位置按照片比例估算。北部屋面、被遮的侧背面、室内和乙楼留待独立查证。建筑模型与构建代码采用本仓库MIT许可证，外部照片仅用于观察。

从仓库根目录使用Python、NumPy、Shapely、Blender、Node.js、gltfpack、ImageMagick及Open Image Denoise重新构建模型。

    python projects/shanghai/source/precise/xuhui-ailu-residence-garden-loggia/source/build_model.py --out ./build/ailu-build --audit ./build/ailu-audit --decoded ./build/ailu-decoded

[单体预览](../../../ailu-residence.html) · [地图地点](../../../index.html#landmark=xuhui-ailu-residence-garden-loggia&mode=overview) · [四件下载](../../../assets/models/candidates/xuhui-ailu-residence-garden-loggia/manifest.json) · [几何与地点验收](../../../data/audit/ailu-residence-v1/)
