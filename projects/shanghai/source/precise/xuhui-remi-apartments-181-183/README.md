# 永康新村永康路181、183号双门山墙

永康路181、183号的两家住户各有一扇小券门，两门共用一座覆筒瓦的大券。沿街立面保留两层双窗、红砖腰线与高出屋面的墙墩。2013年发表的实地照片可读到183号绿牌，左门旁另有「HOUSE 181」小店招。2020年2月22日三处公共街景显示相同的门牌位置与开窗。沿街往西，另一座双门的197、199号门牌并排放在中间，可与本栋区分。[两户三维预览](../../../remi-apartments-181-183.html) · [现场照片、门额与街景来源](reference-review.json)

1994年2月15日上海市人民政府现场铭牌写「永康路109、175弄」，介绍中国建业地产公司建造、1931年竣工、俗称「外国弄堂」及其西班牙式花园里弄。市房管局第二批名录2D026的地址栏写「永康路580号」。2021年《商住交织的永康路城市更新过程及机制》将永康新村定位在永康路西段南侧。175弄向南入住宅街坊，另通太原路，109弄另有独立入口。两者之间的141弄为文安坊。网络条目所引的泛称与住宅形制无法确定某个门号。Fayhoo在Commons上传的住宅照片作为街坊用料参照。[市房管局名录、牌匾原图与论文](reference-review.json)

181、183号恰在两户共用界线的街端。冻结底图的2268、2598分别与当前OSM建筑面重叠95.38%、95.48%（交并比）。沿街前凸分为3.71米与4.36米。三个街景相机测得的门间牌中心与冻结界线前端相距约4.95米。地图沿该界线与沿街两户放置。建筑高约10.84米，尺寸由影像和地图估算。[地块配准与街景交会](footprint-review.json) · [立面尺寸](elevation-study.json)

两扇木门、窗棂、筒瓦、门牌数字与红砖线脚均为原创三维几何。室内、街坊其他建筑、地块绿化与临时设备可另行补证。遮挡区、后部结构及墙墩用途仍待建筑图纸。[模型及Blender工程](../../../assets/models/candidates/xuhui-remi-apartments-181-183/manifest.json) · [建筑专项审计](../../../data/audit/remi-apartments-181-183-v1/README.md)

在项目配置的Python环境运行下列命令，使用现有Shapely、NumPy、Blender、Node.js、gltfpack、ImageMagick与Open Image Denoise。原生模型及代码按项目MIT许可发布。Commons图片、摄影者原图、百度街景及学术图表仅用于辨认和比例参考；OSM数据遵循ODbL。

```bash
python source/precise/xuhui-remi-apartments-181-183/source/build_model.py --out /tmp/remi-assets --audit /tmp/remi-native --gltfpack /path/to/gltfpack --oidn /path/to/oidnDenoise
python source/precise/xuhui-remi-apartments-181-183/source/check_surfaces.py --manifest /tmp/remi-assets/manifest.json --out /tmp/remi-surfaces.json
```
