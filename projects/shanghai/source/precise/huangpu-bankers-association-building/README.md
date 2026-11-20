# 银行公会大楼的香港路立面

香港路59号在香港路南侧，位于四川中路与虎丘路之间。上海市房屋管理局第二批优秀历史建筑名录将其列为2A022，原名“银行公会大楼”，当时登记名称为“爱建公司”。现场保护牌记载大楼由东南建筑公司的过养默设计，1925年竣工。2018年《漫步黄浦》记述，1933年上海市银行票证交易所在此挂牌，后曾由上海工商学院和爱建公司使用。[上海市房管局第二批名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [黄浦最上海《漫步黄浦》，2018年1月15日](https://www.sohu.com/a/216800294_186647)

香港路上的三层立面左右对称。四根通高圆柱和两端的带槽壁柱划出五个开间。柱脚置于台阶及方基上，柱头可见两排叶饰和角卷，柱列后方是二层窗和退入的中央门。正门带网格气窗和绿色59号牌，两端壁段各嵌花环，第三层顶有一枚盾形石饰。2014年1月27日的独立街照与2018年发表的柱头、花环、门、盾牌近照均可辨认这些部位。[Livelikerw摄于2014年的原照](https://commons.wikimedia.org/wiki/File:Former_Building_of_The_Shanghai_Chinese_Banking_Association.JPG) · [照片像素与校验值](reference-review.json)

北侧临街边在冻结地图上宽21.64米，现行OSM边线测得21.85米，两份平面交并比为98.71%。原地图来源地块为2170，登记的八层和25.6米属于推算。《漫步黄浦》把建筑前、中、后段分别记为三、五、七层。三期航片均可见深进深楼体和中央凹入的屋顶，斜摄位移使后方各级退台的位置仍有不确定性。此次建模覆盖北面约4.2米深的临街范围，柱距、层高、出挑和叶饰按实照比例估计。其余楼体沿用已有地图体量。[当前及冻结地块](site-identification.json) · [航片、实际朝向及近景分组](footprint-review.json)

[独立交互与下载](../../../bankers-association.html) · [四件模型清单](../../../assets/models/candidates/huangpu-bankers-association-building/manifest.json) · [在上海主地图查看](../../../index.html#landmark=huangpu-bankers-association-building&mode=overview) · [几何及配准核验](../../../data/audit/bankers-association-v1/README.md)

## 重建

在 projects/shanghai 下运行，准备 Python 3、NumPy、Shapely、Node、Blender 4、gltfpack、ImageMagick 7 和 Open Image Denoise。脚本产生原始GLB、两种压缩GLB、可编辑工程和经独立解码的几何凭据。模型使用米，局部X沿香港路向西微偏南，局部Y向楼内，Z向上。

~~~sh
python -B source/precise/huangpu-bankers-association-building/source/build_model.py \
  --out /tmp/bankers/models --audit /tmp/bankers/audit \
  --decoded /tmp/bankers/decoded --gltfpack gltfpack --oidn oidnDenoise
python -B source/precise/huangpu-bankers-association-building/source/check_surfaces.py \
  --manifest /tmp/bankers/models/manifest.json --out /tmp/bankers/audit/surface-checks.json
~~~

网格和代码采用项目MIT许可。2014年影像由Livelikerw以CC BY-SA 3.0发布，2018年专题图保留作者权利，此处链接供对照。城市地块采用OpenStreetMap贡献者的ODbL 1.0数据、Overture Maps整理记录。航片由Esri World Imagery Wayback提供，使用各期原始影像核对屋面位置。
