# 宏恩医院历史主楼北翼与中部门诊连接体

从北面可见题有“华东医院”的券门，入口两旁有灯，三列窗向上贯穿中央突出部分。朝东的短墙能辨三处三角窗楣。模型包含这座短翼、平屋面及通往南侧病房楼的中段门诊。此前制作的三处山花花园立面属于南翼，二者为同一座1926年历史建筑的不同构件。[南翼花园立面](../jingan-country-hospital/README.md)

[主图定位](../../../index.html#landmark=jingan-country-hospital-north-block&mode=overview) · [独立预览](../../../country-hospital-north.html) · [清单与SHA256](../../../assets/models/candidates/jingan-country-hospital-north-block/manifest.json) · [实物表面验证](../../../data/audit/country-hospital-north-v1/surface-checks.json)

[原始GLB](../../../assets/models/candidates/jingan-country-hospital-north-block/jingan-country-hospital-north-block-raw.glb)（2.237 MB） · [网页GLB](../../../assets/models/candidates/jingan-country-hospital-north-block/jingan-country-hospital-north-block-web.glb)（0.838 MB） · [远景LOD](../../../assets/models/candidates/jingan-country-hospital-north-block/jingan-country-hospital-north-block-lod.glb)（0.245 MB） · [Blender](../../../assets/models/candidates/jingan-country-hospital-north-block/jingan-country-hospital-north-block.blend)（0.553 MB）

## 年代和出处

该楼在今日静安区延安西路221号。上海市文旅推广网记载邬达克设计了工字形建筑，北部每层约500平方米，中央门诊宽10.5米、长18米，连接南北两楼。旧院北部建筑与今日院区的现代北楼名称容易混淆，模型按历史平面上的北侧短翼定位。[上海市文旅推广网](https://www.meet-in-shanghai.net/cn/shanghai-cultural-relics-protection-unit/gratia-hospital-398778/)

2021年《阅读建筑》转载资料中的原建筑平面和1930年代航拍清楚显示南翼、北翼、中臂及两侧露天院落。文章分别署图源为维多利亚大学图书馆和布里斯托尔大学 Historical Photographs of China。1990年代鸟瞰图显示现代楼和另设的西侧连廊。图注为“北立面及主入口”的邱力立照片提供了券门、牌匾、两灯及三列中央窗的信息，拍摄日未载。2014年 Legolas1024 所摄院内斜面照片提供了相邻窗墙、宝瓶栏杆和东面窗楣细节。门前遮棚、封窗及树木遮挡有年代差异。各图按可见范围使用。[历史平面、航拍与北入口近照所在文章](https://bbs.co188.com/thread-10209397-1-1.html) · [2014年院内照片](https://commons.wikimedia.org/wiki/File:Huadong_Hospital,_Shanghai.jpg) · [逐图观察、取得时间、像素尺寸与SHA256](reference-review.json)

本模型主要表现2021年整体顶升前、上述来源能辨认的外貌。2021年的报道记载整座旧楼顶升1.2米，工程还涉及西侧连廊和外立面。地坪高差、后来增改的入口和维护设施需要新的竣工资料核对。[工程报道](https://www.westca.com/News/article/sid=852797/full=1/lang=tchinese.html)

## 尺寸和未建范围

局部坐标原点位于北侧长墙中部地面，约东经121.436773、北纬31.220421。X 向西沿墙，方位角255°；Y 向南入楼，方位角165°。北翼主体约35.4 × 14.6米，中央入口宽约6.2米、外凸约1.9米。中部门诊的宽、长取文字记载，地图位置及屋顶高度、窗洞尺寸、字样字体和饰件深度为估计。玻璃、窗框、凹门、灯和牌匾均用实际几何制作。[屋面及地图源对照](footprint-review.json) · [几何源码](source/north_block.py)

北翼与中臂交接以及两侧院落可从上方分辨。中臂侧墙、北翼西墙和朝院一侧未核清各层开窗，按体量封边。另留待查的范围有南病房楼的侧后墙、楼梯塔、屋顶设备、历史院落与后期连接。入口深处只给门洞背衬，室内未制作。

## 重建

需要 Python 3、NumPy、Shapely 2.1 以上、FontTools、Node.js、gltfpack 0.25、Blender 4.3、ImageMagick 7 与 Open Image Denoise 2.5。把 `blender`、`magick`、`gltfpack` 和 `oidnDenoise` 放在 PATH，或在构建命令用 `--blender`、`--gltfpack` 和 `--oidn` 指定位置。以下从仓库根目录执行。

```sh
python -B projects/shanghai/source/precise/jingan-country-hospital-north-block/source/build_model.py \
  --out /tmp/country-north-assets --audit /tmp/country-north-evidence
python -B projects/shanghai/source/precise/jingan-country-hospital-north-block/source/check_north_surfaces.py \
  --manifest /tmp/country-north-assets/manifest.json --out /tmp/country-north-evidence/surface-checks.json
```

完整和远景模型均需通过解压后逐材质三角面比对。独立检查另外从正面、东面及顶部发射射线，验证北门背衬、窗洞深度、中臂屋面、两侧空院及与南病房楼的截断处。[模型打包入口](source/build_model.py) · [共享打包器](../../../tools/package_architectural_model.py) · [实物表面检查脚本](source/check_north_surfaces.py)

## 许可

原创模型和程序使用 MIT。入口四字采用 Noto Serif CJK SC 派生的 SIL OFL 1.1 子集，经授权字体轮廓生成几何；字体子集单独保留许可证和命名说明。第三方图像仅供研究，全模型无照片贴图。Wikimedia 的2014年照片由 Legolas1024 拍摄，许可为 CC BY-SA 4.0。地图建筑数据归属 © OpenStreetMap contributors（ODbL）及 Overture 相应来源；Esri 及图像供应方航片仅用于判断轮廓、方向与时期。[MIT 许可](../../../../../LICENSE) · [字体溯源](source/fonts/provenance.json) · [OFL 许可](source/fonts/OFL.txt) · [图像记录](reference-review.json) · [地图来源](footprint-review.json)
