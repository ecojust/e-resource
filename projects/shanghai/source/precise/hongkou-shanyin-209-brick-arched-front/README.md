# 山阴路209弄3号三券花园正面

2015 年的照片同时拍到了绿色的 3 号门牌、底层三道砖券和二层外挑花架。达奇珍访谈记述，209 弄内有成对建造的花园住宅，外墙用青砖并加红砖腰线，屋顶铺四坡红瓦。房管局第五批名录的 5F006 项还登记了 229 弄 1–6 号。这件展品取自 209 弄 3 号，做到前方台阶、主要屋坡和后部在照片中露出的高瓦面。建造年代和整座院宅的平面有待考证。[名录与门牌考证](measurements/two-lane-source-history.json) · [来源与许可](SOURCES-LICENSE.md)

## 三道券与两扇屋窗

底层左券内有伸出的金属栅罩、辐条、后窗和小蓝篷。中、右两券内凹，三步台阶通向右券内的廊面。二层三扇窗各有弧形上亮、红色径向券砖、浅色窗下墙与金属花架。主要屋坡以逐行瓦片和西侧斜脊收边，左屋窗有浅色人字边，右屋窗保留偏斜的瓦檐和向外开启的红窗扇。[花园正面同机位对照](../../../data/audit/shanyin-209-brick-arched-front-v1/garden-front/garden-front-survey.jpg) · [上层砖券](../../../data/audit/shanyin-209-brick-arched-front-v1/arches/three-upper-arches.jpg) · [底层廊券](../../../data/audit/shanyin-209-brick-arched-front-v1/ground-arcade/ground-arcade.jpg) · [双屋窗](../../../data/audit/shanyin-209-brick-arched-front-v1/roof-dormers/two-dormers.jpg)

## 比例与可见范围

三个墙垛的灰缝在原照中平均每皮约 4.81 像素。以一皮暂取 6.3 厘米，183 像素宽的中央净窗在模型中取 2.38 米。若原砖一皮为 5.5–7 厘米，同一窗宽约为 2.09–2.66 米。全件采用这个展示尺度。正檐进深和两扇屋窗的位置还受第二张同户照片约束，主瓦坡约 29°。较高后瓦面的截止位置由第二视角可见的天空推估，背坡、毗邻 4 号及院中树木、晾衣物不在本件内。花园廊背部只建了原照中可识别的门框、砖墙和落地面。[砖皮与瓦垄取样](measurements/brick-and-tile-course-survey.json) · [两机位檐口计算](measurements/eave-two-photo.json) · [屋窗双照交会](measurements/two-view-dormer-points.json) · [后瓦面范围](measurements/roof-surface-notes.json)

## 重建与核查

在本目录执行以下命令。普通打包入口会生成网页近景、远景、原始 GLB 和可编辑的 Blender 工程。

```sh
mkdir -p output
python source/build_model.py --output output/garden-front.glb
python source/build_model.py --lod --output output/garden-front-lod.glb
python source/build_model.py --out output/delivery --audit output/review
```

原始网格和网页近景各 116,740 个三角面，远景 82,600 个。三个网格各通过 116 处建筑截面、256 处底层券廊及 180 处上层砖券检查。两扇屋窗在 2015 年图的 40 个标记均落在对应材质的 4 像素以内。第二张照片的 23 处中有 22 处在 2 像素以内，余下 1 处在照片中为浅色窗框，在网格中落在玻璃。模型两档各有七个保存的视角。[模型页](../../../shanyin-209-brick-arched-front.html) · [双屋窗两机位核查](../../../data/audit/shanyin-209-brick-arched-front-v1/roof-dormers/roof-window-survey.json)
