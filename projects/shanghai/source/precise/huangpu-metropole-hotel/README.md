# 都城饭店（江西中路180号转角主楼）

上海市房屋管理局第二批优秀历史建筑名录2A038记为「都城饭店」，登记时使用名称为「新城饭店」。它立在江西中路与福州路圆形路口的东北角。福州路以南的170号是汉弥尔登大楼（今福州大楼），街对面的原工部局和北侧江西中路200号的金城银行也各有独立地块。[房管局第二批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [街区关系图](../../../data/audit/metropole-hotel-v1/street-blocks.png)

上海发布2022年的建筑资料将建成年份记为1934年，介绍了钢框架、底层沿街花岗石、八层以上的退台，以及入口和塔楼上的装饰艺术图案。同篇整栋夜照、门廊近照和从入口下方拍摄的照片可互相定位。2012年日间照片、2013年丹尼尔·凯斯拍摄的正面照及街角双楼同框照用于复核。二手资料记饭店1935年开业、1964年改名新城饭店。模型把14层、约65米作为估计比例。[上海发布《建筑可阅读》](https://news.qq.com/rain/a/20221113A05L5600) · [照片作者、年代、许可和文件指纹](reference-review.json)

模型取转角主楼。五段内凹街面沿半径约13.93米的弧形展开，中间为三开间的石门廊；雨篷下可见独立门洞、台阶和两盏多边形悬灯。入口上方有三扇拱窗，再往上是十排客房窗。两侧窗廊先收，中央三券塔部继续升高，顶部是圆角切面的塔冠。两段短翼分别沿江西中路和福州路伸展。窄窗、窗套、女儿墙与塔冠分档建模，房间内部、后部设备和历次修缮仍待查证。[查看独立模型](../../../metropole-hotel.html) · [模型验收](../../../data/audit/metropole-hotel-v1/README.md)

作者局部X沿圆弧切线向东南，Y从街口向东北，Z向上，单位为米。弧形中央落在东经121.4829932°、北纬31.2372085°。位置依据冻结城市地块358和具名OSM道路、建筑核对；与现行实名界线相交并集比为97.16%。原始地块与低邻楼724在东北侧有约1.96平方米交叠，配准另按楼高处理交接部位。新建成品的实体轮廓止于本楼。各层实际净高、背墙、窗框与灯具的尺寸依照片估计。[原始分块、道路和三个年份的屋顶影像](footprint-review.json) · [城市地图](../../../index.html#landmark=huangpu-metropole-hotel&mode=overview)

## 重新生成

几何、图片中的原创示意图及专属代码按仓库MIT许可。照片与卫星原图仅通过其来源外链。地图数据署名 © OpenStreetMap contributors（ODbL）和 Overture Maps Foundation，历史航片由 Esri World Imagery Wayback 及影像提供者发布。使用 Python 3、NumPy、Shapely 2.1、Node、Blender、gltfpack、ImageMagick 7 和 Open Image Denoise。由 `projects/shanghai/` 运行以下命令。

```sh
python -B source/precise/huangpu-metropole-hotel/source/build_model.py \
  --out /tmp/metropole/assets --audit /tmp/metropole/audit --decoded /tmp/metropole/decoded
python -B source/precise/huangpu-metropole-hotel/source/check_surfaces.py \
  --manifest /tmp/metropole/assets/manifest.json --out /tmp/metropole/audit/surfaces.json
```
