# 利西路24弄5号戴宅

从街上向上看，戴宅的两道绿色曲边向内收拢，在上层拱窗头顶托起一座浅坡小屋顶。下面三扇绿框拱窗开向折角阳台。阳台前侧和斜侧各嵌一块圆环交叉石花格，从斜面可以透过孔洞看到窗墙。模型覆盖这一跨立面、两侧一小段瓦坡与阳台下的一道窗楣。[打开模型](../../../lixi-lane-24-dai-villa-gable.html)

长宁区规划和自然资源局记载，这座住宅约建于1920年，设计者为上海公利营业公司的工程师顾道生，后由戴伦庠继承。地块面积3233平方米，建筑面积约1347平方米。上海市第四批优秀历史建筑登记编号为4M024。[区级档案](https://www.shcn.gov.cn/col7698/20211207/1151472.html) · [市级名录](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html)

## 照片如何约束模型

- Antigng于2018年2月13日从街上拍摄的照片提供了三扇拱窗的独立宽高、栏板的两个转折面和主视图。以中央拱窗净宽约1米为比例基准，结合相机等效28毫米焦距、水平线与铅垂线求相机姿态。阳台左端与窗墙的局部间距估计为0.27米，栏板相对宽度和折线由照片射线与水平面相交确定。[沿街原照](https://commons.wikimedia.org/wiki/File:利西路24弄5号住宅.jpg) · [相机参数](measurements/street-camera.json) · [阳台剖面](measurements/balcony-section.json)
- 区级照片从较高的右侧看到瓦坡、绿色山墙的边界和石花格的孔洞。两幅照片用四个山墙点对齐。在区照上量取右侧11行色界后生成曲线，另用76行检验输出网格。换算到区照原始像素，近景均方根误差1.86像素，简化版1.90像素。这项误差只描述山墙平面右边线。[山墙量点](measurements/green-gable-profile.json) · [独立检验](measurements/independent-green-edge.json)
- 两组绿色窗框、玻璃分格、窗台花槽、出挑托头、弯曲泛水、小段陶瓦、折角阳台和镂空石环均为可编辑几何。背侧截面、屋面向后的长度、石花格截面、窗洞退深、瓦色与砂石颗粒依可见外观估计。树枝、晾晒衣物和相邻房屋均落在本次模型范围之外。[照片并置](measurements/photographic-comparisons.json) · [材料与许可](SOURCES-LICENSE.md)

门牌点到城市底图两处最近建筑轮廓分别为4.40米和4.80米，住宅屋面复杂，2018年照片的经纬度只记至整秒。两个原轮廓均留在城市底图；独立模型可检查到本组构件。[地图核对](../../../data/audit/lixi-lane-24-dai-villa-gable-v1/preflight/final-placement-review.json)

## 重建

在本目录运行以下命令可重建两档模型。省略输出路径时，项目打包器还会调用 Blender 生成可编辑源文件。源码中的曲线、三扇窗与两块花格可分别调整。[主脚本](source/build_model.py) · [相机](source/cameras.json)

```sh
python source/build_model.py --output dai-gable.glb
python source/build_model.py --lod --output dai-gable-lod.glb
python source/build_model.py --blender blender --out ./exports --audit ./audit
```
