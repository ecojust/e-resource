# 建设大楼 · 福州路口凹入塔面

市房管局第二批保护名录2A039原名栏为「建设大厦」，现名栏为「冶金工业局」，登记门牌江西中路171至181号单号。市住建委和市历保中心的外立面修缮介绍采用「建设大楼」。原中国建设银公司总部坐落在福州路与江西中路路口西南侧，通常以江西中路181号标识。路口另三角为西北的工部局大厦、东北的都城饭店和东南的汉弥尔登大楼。西边的福州路185号总巡捕房及更北面的浙一大楼，分别属于其他地块。[市房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [项目逐项来源](reference-review.json)

建筑1934年开工，1936年落成，地上高度67.97米。1936年3月31日《大陆报》已报道设备搬入新楼。原建筑用花岗岩砌块、黑花岗石贴面、水刷石、条纹水刷石、黄砂水泥、黑钢窗及窗下金属板，2021年启动外墙修缮。较早照片偏暗，按修缮后照片取色，未把不同时间、光照造成的明暗差逐块复制。[市住建委、市历保中心街口建筑介绍](https://www.sohu.com/a/918319951_121106832) · [转载历史报页及日期](https://m.thepaper.cn/newsDetail_forward_7538626)

模型从面向街心的黑花岗石矩形门向上，表现中央三列十六排钢窗和六道冠顶短竖肋，两边单列高窗较低。转过侧翼，两排凹入的窗轴与临街短返面共同围成小广场，肩部为八排窗。黑门内的暗色玻璃与门槛按2019年正照近似。原图指向本栋的建筑外观，修缮报道中的附属小门仅提供石材依据。观景立面后侧的办公房、非临街外墙、内部空间和附属房顶没有逐层图纸实证。[2013年Livelikerw斜照](https://commons.wikimedia.org/wiki/File:Development_Building_(2).JPG) · [2019年Shanghai88正面](https://commons.wikimedia.org/wiki/File:Development_Building_Shanghai.jpg) · [2025年Boubloub图像，CC0](https://commons.wikimedia.org/wiki/File:Shanghai_CDFC_Tower.jpg) · [单体页](../../../development-building.html)

现行OSM来源w447017703及冻结来源2551位于同一凹角，面积交并比约97.13%。弧边约25.48米，首尾弦长约21.89米。原城市高度57.6米按18层估算，工程所用总高度据现状保护资料。三期卫星影像的楼顶视差明显，屋顶未按单期卫星图水平移动。模型各段退深、窗宽、饰板、侧面接缝及颜色均为摄影比例估计。地图署名OpenStreetMap contributors（ODbL 1.0）及Overture Maps Foundation；Wayback影像归Esri及各期供图方。模型为原创，使用项目MIT许可证。[按来源配准](footprint-review.json) · [影像与许可](reference-review.json) · [项目许可证](../../../../../LICENSE)

从 `projects/shanghai` 重建时需要 Python、NumPy、Shapely、mapbox-earcut、Node、gltfpack、Blender、ImageMagick 7 和 Open Image Denoise。默认构建保存并重新打开Blender工程，把原始及两档实解码三角面按材质和顶点朝向核对。

```sh
python source/precise/huangpu-development-building/source/build_model.py \
  --out assets/models/candidates/huangpu-development-building \
  --audit data/audit/development-building-v1
```
