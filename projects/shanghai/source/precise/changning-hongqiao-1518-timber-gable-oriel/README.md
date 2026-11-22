# 虹桥路1518号花园住宅的木构山墙与三面凸窗

从花园向南立面望去，两座深色木构山墙夹着一段露台。模型截取右侧较高的一座。山墙顶部收成小片瓦坡，下部木柱和弯撑环绕四扇阁窗。凸窗的三片瓦坡下，能看到浅色交叉带饰，两只托臂从墙面向前挑出。底层弧窗分为五段。[打开三维模型](../../../hongqiao-1518-timber-gable-oriel.html) · [花园照片与模型对照](study-views/garden-source-and-model.jpg)

市级第四批名录将虹桥路1518号登记为“花园住宅”，编号4M040，建造年代记为不详。2018年花园侧照片使用“白崇禧旧居”题名，居住时段仍待文献确认。2014年的另一张照片从虹桥路北门向内拍摄，两处视点见来源记录。[名录与地址](measurements/city-register.json) · [带署名的两张原照](SOURCES-LICENSE.md)

## 怎样还原窗和屋顶

建模以四片蓝灰玻璃的十六个角点拟合花园相机。窗心名义间距取0.455米，假定单片玻璃宽0.296米。小瓦顶、暴露木构、三面凸窗和弧窗共用这一相机。主瓦坡分七行，凸窗的三个小坡面各铺五行，两处屋顶共有六道分节筒脊。[阁窗测量](measurements/attic-glass.json) · [相机与尺度](measurements/garden-camera.json) · [瓦行与檐口进深](measurements/tiled-hip-roofs.md)

正中窗面宽，两侧窗面斜向收回。模型将各面的玻璃、木框、抹灰窗洞与下部浮雕各自成形。图中左侧窗透视很窄，窗洞沿观察方向展开，以保留真正可见的玻璃。凸窗估计前挑0.70米，前檐再挑约0.20米。浮雕交叉处的遮挡、两托臂背面的接合和墙后截取的1.07米深度均为近似。[三面窗测量](measurements/oriel-facets.json) · [浮雕与托臂轮廓](measurements/garden-bay-relief-and-brackets.json) · [浮雕图像对照](study-views/oriel-carving-and-photo.jpg)

公开底图的建筑轮廓2039覆盖同名地点，两份屋顶地图也能区分北侧道路与南侧庭院。右侧凸窗在当代轮廓上两个端点的位置仍待确认，本次作为独立局部展示。[街面、花园与底图](measurements/garden-and-street-elevations.json)

## 编辑与重建

原始网格、近景和远景 GLB 与 Blender 工程列在模型页的下载栏。Blender 工程保留可单独编辑的瓦行、筒瓦、玻璃、窗框、浅饰和托臂，以及七个观察相机。模型使用程序生成的米色抹灰纹理。[模型与图片许可](SOURCES-LICENSE.md)

```sh
python source/build_model.py --output garden-gable.glb
python source/build_model.py --lod --output garden-gable-lod.glb
python source/build_model.py --blender blender --out ./exports --audit ./audit
```

原始照片按来源链接下载。把环境变量 `HONGQIAO_GARDEN_PHOTO` 指向 Fayhoo 的原图，依次运行 `measure-attic-glass.py`、`register-garden-camera.py` 和 `measure-three-facets.py`，可重算照片测量。生成模型直接读取随附的测量结果。

斜脊的十四个中间位置留作独立核对。沿每一列从天空向下求近景模型的第一次实体交点，与原照片的瓦边比较，均方根偏差约1.18个像素（在800 × 600坐标中）。这些点没有参与相机和屋顶端点的拟合。[预留列](measurements/upper-hip-holdout-pixels.json) · [三档实际网格逐列结果](measurements/garden-photo-three-meshes.json)
