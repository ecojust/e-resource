# 杨树浦路713号住宅的红砖山花

上海市第五批优秀历史建筑名录的5G006项原名为“住宅”，公布时使用名称为“平凉路派出所”。2017年关于杨树浦路改造的报道提到这座民国时期的花园住宅，具体建造年份待考。[上海市房屋管理局](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [新华网转载条目](https://www.toutiao.com/article/6501787894393340429/)

Fayhoo在2015年4月6日拍下这处双坡山花。两道灰色斜檐随砖墙在右侧折起，短颈和叠台托住半圆顶饰。扇肋从底部中心向外放射，下面的通风圆眼有四处凸键和一组横百叶。单张照片能辨饰面色泽及突出关系，灰色饰面的具体材料仍待考。2024年同址影像中的另一处白色三角窗额带圆球顶饰。[Fayhoo 原照与许可](https://commons.wikimedia.org/wiki/File:Pinglianglu_Paichusuo.JPG) · [2024年同址影像](https://www.toutiao.com/video/7323397837855818267/)

模型的37个独立构件分属砖墙、坡檐、通风眼和顶饰四组。图中的砖皮约2.36至2.44像素，按每皮约66毫米换算，模型展陈宽约12.4米、高约4.8米。墙厚、饰面厚度和横向比例均为估计。照片左脚受前景栏杆遮挡，模型在可见墙带内作水平截断。[比例和图像材料](measurements/documentary-sources.json) · [模型与2015年原照对照](../../../data/audit/yangshupu-road-713-historic-residence-v1/gable-comparison.jpg)

红砖和灰色饰面各有一幅程序生成的循环纹理。Blender工程中逐件保留几何、贴图坐标和六台相机。模型与自绘纹理按MIT许可共享，对照图中的Fayhoo照片裁切及合版按CC BY-SA 3.0共享。[MIT](https://opensource.org/license/mit) · [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/)

## 从源码重建

在完整项目的 `projects/shanghai` 目录中运行，安装项目Python依赖、Blender、Node和gltfpack。下面的路径以本模型源码为起点。

```bash
s=source/precise/yangpu-yangshupu-road-713-historic-residence
python "$s/source/finishes.py"
python "$s/measurements/check-solids.py" near exports
python "$s/measurements/check-solids.py" far exports
python "$s/measurements/package-web-model.py" exports assets-test audit-test --gltfpack gltfpack
python "$s/source/build_blender_source.py" prepare exports/near.glb native-test
python "$s/source/build_blender_source.py" run exports/near.glb native-test
python "$s/measurements/check_gable_photo.py" exports/near.glb exports/decoded-near.glb exports/decoded-far.glb --out audit-test/photo-rays.json
```
