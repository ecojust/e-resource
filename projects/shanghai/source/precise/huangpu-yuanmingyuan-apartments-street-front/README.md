# 圆明园公寓东立面与切角柱廊

圆明园公寓位于黄浦区圆明园路115号，列入上海市第五批优秀历史建筑，编号5A044。模型取沿街东立面、凹进的入口和两侧可从街上看见的切角。两道红砖券窗、两片三角山墙、石楣上的「圓明園公寓」和上方的英文建筑名均可近看。[查看模型](../../../yuanmingyuan-apartments-street-front.html)

Livelikerw 于2014年1月27日拍摄的东南街景保留了翼窗、砖拱、正门字牌和南角砖柱。2016年档案正照与斜照补充了北端、窗台、门后木扇及栏板下沿的细部。可复核的取样坐标、相机矩阵及照片索引一并保存。[照片与名录](measurements/heritage-register-and-street-photographs.json)

## 实物与尺寸

- 东立面两翼各有六处矩形窗洞。两组独立相机交会约束十字梃的深度，阁楼窗的深度参考同侧下层。窗框、玻璃和窗台可分别编辑。[翼窗测点](measurements/wing-window-observations.json)
- 入口两边的柱对共用砖台。四个柱头、后退的石楣、字面和英文金属字各有独立几何。五个中文字按2014原照的实笔轮廓放样，浅色石底从字孔中可见。入口内部的开门角度、约2.78米深的后门面和台阶深度为估计。[门廊双照交会](measurements/entrance-and-spandrel-stereo-controls.json)
- 南角可见曲面红砖栏、雕饰带、砖柱和有卷涡的石柱头。南侧塔面三层窗、短墙和定冠按东南照片定位，北端参考相反方向的档案照片。两处曲率、石刻的凸出量及遮住的一侧尺度为估计。[切角观察记录](measurements/east-return-and-doorway.json)
- 既有城市轮廓编号2981，其东侧街边长约28.70米。独立模型沿正面白墙定轴，保留原城轮廓及两侧相邻建筑。[位置与街界](measurements/footprint-review.json)

## 重建

在项目目录中使用 Python 3，并安装 NumPy、SciPy、Pillow、Shapely，以及项目建筑打包器所用的依赖。以下两条命令分别重建精细网格和远景网格。命令从当前目录运行。

```sh
python source/build_model.py --output yuanmingyuan-full.glb
python source/build_model.py --lod --output yuanmingyuan-lod.glb
```

可在 Blender 中打开网页提供的可编辑工程。项目中的建模脚本按材料、楼层和构件命名，砖面图案由固定随机种子的程序生成。原始着色贴图、相机参数、近远档下降的圆弧细分与构件组织均可检查。[建模入口](source/build_model.py) [照片与许可](SOURCES-LICENSE.md)
