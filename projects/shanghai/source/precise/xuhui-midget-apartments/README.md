# 密丹公寓武康路与湖南路转角立面

上海市房屋管理局第二批优秀历史建筑表将2D037登记为武康路115号密丹公寓。工作名录列1931年、六层、混合结构；建筑条目记同年、五层、钢筋混凝土。立面模型依据三次街拍中实际可见的开口排布。竣工剖面和结构尚待核实。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [各项出处及图像指纹](reference-review.json)

武康路与湖南路会合处的街角有窄切面。两扇顶窗之间保留实墙，往下是两层大横窗、浅色窗间板以及带金属护栏的深窗。深窗两边的阶形构件有独立挑出部分，侧墙上能看到折面凸窗。下部商铺经历更替，模型按2026年浅灰基座和店面开口制作。模糊的招牌文字、远端窗列、后院及内部空间仍待取证。[2013年正面](https://commons.wikimedia.org/wiki/File:Midget_Apartments.JPG) · [2015年正面](https://commons.wikimedia.org/wiki/File:Shanghai_Midget_Apartments.jpg) · [2026年正面](https://commons.wikimedia.org/wiki/File:20260209_Midget_Apartments.jpg)

城市底图14-13718-6695的2974号对应OSM建筑w582302423。两条道路的交点距地块边10.1米。名楼兴趣点偏出边界5.75米，带115号门牌的当期店铺点与孙道临故居点均落在轮廓内。两期影像上的树遮挡了部分屋顶，平面采用原楼西南边约4.81米的切面。两段短墙分别取约5.8米、5.95米，保留原楼纵深及独立邻楼。层高、开间与构件进深是比例估值。[屋顶核对](roof-registration.json) · [地块和近远原始模型](footprint-review.json) · [参数](source/parameters.json)

可调几何、材质和相机均在本目录。模型以米计，局部X轴从武康路侧指向湖南路侧，局部Y轴向楼内，Z轴向上。源程序生成三档GLB，并由Blender生成可编辑工程。需安装项目共用的几何依赖、Blender、gltfpack、ImageMagick及Open Image Denoise。在上海项目根目录运行以下命令。[构件源码](source/corner_front.py) · [独立预览和四种下载](../../../midget-apartments.html)

```sh
python -B source/precise/xuhui-midget-apartments/source/build_model.py \
  --out /tmp/midget-model --audit /tmp/midget-review --decoded /tmp/midget-decoded \
  --blender blender --gltfpack gltfpack --oidn oidnDenoise
```
