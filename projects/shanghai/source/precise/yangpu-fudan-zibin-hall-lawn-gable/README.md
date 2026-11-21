# 复旦大学子彬院草坪侧三角山墙与阳台

子彬院原供心理学教学、科研使用。1925年开始筹建，1926年落成，后来用作数学楼。上海市第四批优秀历史建筑名录将子彬楼与相辉堂、图书馆、校门合列为4G008，地址为邯郸路220号。[校史资料与市级名录](measurements/building-identification.json)

从草坪向上看，浅色的两条斜檐在顶珠下方交会。阁楼双窗上方有一块五边形镶面，左右各有两块灰色镶面。阳台后的三对高窗由壁柱隔开，前沿的三个开敞栏段各有独立的瓶形栏杆。2005年照片中还可辨认三处带圆形格栅的浅色外壳。[观看模型](../../../fudan-zibin-hall-lawn-gable.html) · [原照与模型并置](study-views/photograph-and-lawn-gable.jpg) · [阁楼](study-views/photograph-and-attic-fields.jpg) · [栏杆](study-views/photograph-and-balustrade.jpg)

## 照片与尺度

Roalood的原照保留了拍摄时间2005年5月30日13时15分59秒。这里使用原始1024 × 768像素坐标，分别记录窗洞角点、横向线组、两段斜檐和五块镶面。以一扇阁楼窗可见净宽1.32米为假设，反算中央山墙两端相距约13.43米。出挑深度、墙厚、窗脚的遮挡部分和石栏回转剖面采用估算。17个另读的檐边位置与导出模型的剖面相符，在这一假设尺度下，高差的均方根约0.017米。原照片上中央凸部仅约200像素宽，读点误差与绝对尺寸须分别考虑。[署名原照](measurements/signed-photograph.json) · [原图控制点](measurements/photograph-plane-controls.json) · [斜檐剖面检查](measurements/independent-rake-check.json)

模型截取中央凸部的上层。城市已有的整栋轮廓在原处保留。子彬院实名楼体与现有轮廓重叠约98.55%。三段平行的正面朝向约149°，其正前方最近草地距正面中点约12.17米，具名的相辉堂草坪则位于楼体西南。校园地图能确定楼体，局部山墙的横向位置仍靠照片推定。[楼体与草坪测算](measurements/building-and-lawn.json) · [定位复核](../../../data/audit/fudan-zibin-hall-lawn-gable-v1/preflight/final-placement-review.json)

## 模型制作与核查

近景模型含27,468个三角面，远景模型含11,694个。两档保留八个真实窗洞、分格窗框和玻璃、贯通栏隙、带顶珠的斜檐和瓦屋面截段。模型使用原创的可重复灰色抹灰纹理。原始网格和两个网页解码文件各接受196次几何检查，涵盖窗扇深度、斜向窗缝、栏杆间隙、瓦面高度与格栅位置。[制作程序](source/build_model.py) · [制作尺寸](source/dimensions.json) · [几何复核](../../../data/audit/fudan-zibin-hall-lawn-gable-v1/preflight/geometry-rays.json) · [来源与许可](SOURCES-LICENSE.md)

从仓库根目录可重建两个编辑网格。命令需要项目已有的 Python、NumPy、SciPy、Shapely 和 Pillow。

```sh
python projects/shanghai/source/precise/yangpu-fudan-zibin-hall-lawn-gable/source/build_model.py --output /tmp/zibin-full.glb
python projects/shanghai/source/precise/yangpu-fudan-zibin-hall-lawn-gable/source/build_model.py --lod --output /tmp/zibin-lod.glb
```
