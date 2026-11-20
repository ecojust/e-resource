# 多伦路250号住宅 · 弧形街面与中门

市房管局首批优秀历史建筑名录登记为 **1F004 多伦路250号住宅**，地址多伦路250号。资料中也有“孔祥熙公馆”之称。模型沿用保护名录名称，以现存两层街面为制作对象。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20200331/fe7b4d6f35774b708a2c5122849065bd.html) · [建筑史条目](https://zh.wikipedia.org/wiki/孔祥熙公馆_(虹口))

2014年12月的日间正面和2024年1月的夜景都拍到了西北侧中门。弧墙中段的一扇木门、两侧窄窗与上层三拱开口对齐，中央阳台出挑，屋顶女儿墙有三分格。弧面往两端展开，上层从成对窄窗过渡为五连窗，下层端段为三券。早在2008年上传的一张局部照片记录了五连窗下的雕饰带与三扇窗，拍摄日期未注明。[2014年正面](https://commons.wikimedia.org/wiki/File:250_Duolun_Rd._Shanghai.JPG) · [2024年夜景](https://commons.wikimedia.org/wiki/File:20240107_250_Duolun_Road.jpg) · [端部窗组](https://commons.wikimedia.org/wiki/File:250_Duolun_Road_Shanghai.jpg)

## 模型与位置

原始建筑面约352平方米，呈近矩形。屋面影像显示西北角沿步行街转弯，中央门楼斜对街面。依据航片及照片校正西北曲线，保留东、南侧的平直边界。地图中的“西北门”兴趣点落在另一栋建筑，入口位置取自这面有照片依据的门墙。

模型分开建立曲墙、下部门廊列柱、上层马蹄形和复合拱窗、中央小阳台、石饰带与顶层女儿墙。背侧窗位、屋面、曲墙半径和各标高为估计。石刻细纹以原创几何星纹近似。室内、绿化、附属低屋及相邻建筑不在模型范围内。[定位来源](footprint-review.json) · [影像来源与署名](reference-review.json)

Blender 文件使用米制。原生正视图面向中门，主图按实际地块旋转。网页远景缩减曲面分段、花格和栏杆，保留主要窗洞与轮廓。[单体页](../../../duolun-250.html) · [资产清单](../../../assets/models/candidates/hongkou-duolun-250/manifest.json)

```bash
python projects/shanghai/source/precise/hongkou-duolun-250/source/build_model.py \
  --out /tmp/duolun-model/assets --audit /tmp/duolun-model/audit
```
