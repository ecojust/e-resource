# 永嘉路西爱村与恒爱里共用弄口

沿永嘉路的人行道向内看，灰色过街门屋连接西爱村19弄与恒爱里21弄。门屋的正洞净宽约3.46米，梁底高约2.93米。用2015年12月18日的三个拍摄站配准后，两侧二层窗在同一张立面上定了位置。右窗的两片扇向外打开；左窗上方有浅挑眉，两窗之间的金属架可分别选取。[街面相机与尺寸](measurements/yongjia-street-cameras.json)

弄名与绿色路牌按2020年较清楚的街面影像辨读。木牌书体和印刷路牌字使用可再分发的替代字体；文字位置和四角取自实照，绿色小字牌最下方的细字在几张影像上都难以确认。2017年侧视图补充了内道梁和卷在洞侧的铁门。入口模型保留两道梁之间的通行空间。[门牌与弄名辨读](measurements/gatehouse-sign-readings.json)

模型限于共用门屋和从街面可见的通道。左邻17号商铺及别户窗墙有独立的街面边界。入口处落到市级简化建筑模型的接缝上，故在独立页展示。净宽由街道多站摄影推算。[门屋与原城市地块](measurements/footprint-review.json)

在项目根运行以下命令可生成完整或简化的可编辑部件。程序使用项目既有网格工具、NumPy、Shapely和Pillow，制作原生工程另需Blender。照片仅作研究对照，贴图由脚本生成。[七个观察位置](source/cameras.json)

```sh
python source/precise/huangpu-xiai-hengai-common-lane-gate/source/paint.py
python source/precise/huangpu-xiai-hengai-common-lane-gate/source/build_model.py --output yongjia-gate.glb
python source/precise/huangpu-xiai-hengai-common-lane-gate/source/build_model.py --lod --output yongjia-gate-lod.glb
python source/precise/huangpu-xiai-hengai-common-lane-gate/source/build_model.py --help
```
