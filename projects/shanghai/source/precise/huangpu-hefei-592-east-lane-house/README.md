# 合肥路592弄弄口与东侧山墙

2015年2月的冬季街景能同时辨认弄口西柱的“592弄”、敞开的铁门和东侧住宅西山墙上的三处红棕色百叶。两扇上窗各有一片浅色背面朝外，分别绕原铰轴打开，底层两扇在该期照片中关闭。2017年的树叶及窗扇状态已有变化。门牌字形使用可再分发的近似字形，原位置、牌框和四个字符已经逐处核过。

墙脚灰勒脚的上边约为1.06米，2015年的21条采样与2017年的16条采样都保存在[地坪与墙脚测量](measurements/gate-plinth-and-paving-observations.json)。排水孔贯入墙脚，入口宽约31厘米、高约5厘米。屋檐在树木后交会，脊点依据两段可见的斜线估计。模型只保留靠弄口、沿着实见山墙的一带灰墙和瓦面。[檐线及截面范围](measurements/gable-roof-and-visible-extent.json)

市名录登记合肥路592弄住宅。向东的沿街店宅另有590和586号门牌。原城市建筑107覆盖一段连排住宅，本件作为独立模型展示。[门牌与地图对照](measurements/footprint-review.json)

在项目根运行以下命令可重建原始和简化几何，完整近景保留每片曲瓦、百叶及铁杆独立的编辑名称。

```sh
python source/precise/huangpu-hefei-592-east-lane-house/source/paint.py
python source/precise/huangpu-hefei-592-east-lane-house/source/build_model.py --output hefei-592.glb
python source/precise/huangpu-hefei-592-east-lane-house/source/build_model.py --lod --output hefei-592-lod.glb
python source/precise/huangpu-hefei-592-east-lane-house/source/build_model.py --help
```

工程使用项目现有的Python网格工具、NumPy、Shapely、Pillow与Blender。7个可复用机位见[相机文件](source/cameras.json)。[资料与许可](SOURCES-LICENSE.md)
