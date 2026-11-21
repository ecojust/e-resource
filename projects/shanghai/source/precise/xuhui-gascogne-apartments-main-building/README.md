# 盖司康公寓主楼南向前院立面

市房管局第二批优秀历史建筑2D003在淮海中路1202号登记“盖司康公寓／淮海公寓”。第三批3D003另列淮海中路1204至1218号的淮海公寓2号楼。1202号主楼在庭院北侧，共十三层。五层的2号楼紧贴淮海中路，有商铺和弧形转角。从2013年12月的对街实照可以同时看到两栋。[第二批2D003](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) [第三批3D003](https://fgj.sh.gov.cn/yxlsjz/20210922/bc5957926d80432b8bea0157eb16bb94.html) [Livelikerw，2013年12月25日街景](https://commons.wikimedia.org/wiki/File:Gascogne_Apartments.JPG)

万国储蓄会投资建造公寓，赉安洋行设计，中法营造厂承建，1935年竣工。1937年的黑白照片已能分辨中央抬高的塔冠、从中部向两侧递减的体量、成对的凹阳台，以及两座楼之间的空间。2018年上观新闻逐一说明两栋门牌与层数。2023年1月，乐游上海发表于上观新闻的图文给出了前院高位照、底部双门、仰拍立面、屋面和背面。上海老底子同月转载了该组图文。[1937年旧照](https://imagepphcloud.thepaper.cn/pph/image/233/255/357.jpg) [2018年两栋门牌说明](https://www.shobserver.cn/wx/detail.do?id=76900) [乐游上海2023年图文](https://www.jfdaily.com/wx/detail.do?id=569952) [同图组转载及近景](https://www.thepaper.cn/newsDetail_forward_21494199)

这次制作正对庭院的一面。三条水泥竖带从双入口雨篷上方延伸到冠部，两侧各有两列内凹的阳台，浅色阳台边板之上另设细金属栏。基座铺深色石材，雨篷底可以分辨三组带格透光板，门前有弧角石阶。两个开敞门洞在洞后可见范围内收住。屋面局部、门框与凹阳台的深度及砖缝尺度据图估算。背街部分和庭院里的建筑、花池与喷水池留在原有地图。[中央竖带与阳台](https://imagepphcloud.thepaper.cn/pph/image/233/255/368.jpg) [双门、雨篷和石阶](https://imagepphcloud.thepaper.cn/pph/image/233/255/370.jpg) [主楼南面与前院](https://imagepphcloud.thepaper.cn/pph/image/233/255/372.jpg)

具名建筑环w495913753明确记载1202号、十三层及1935年，和冻结地图107的足迹交并比98.34%。庭院侧墙线两端相距49.26米，中心位于东经121.44845277度、北纬31.21665522度。按资料所载主楼约53米与照片内的比例，模型最高52.51米。底图对其体量统一估高41.6米。街边另一栋来源4703对应w495913755，名录与照片决定其归属，671平方米足迹乘五层也与书刊所载约3318平方米接近。它在主楼以南，完整保留。[主楼原始地图环](https://www.openstreetmap.org/way/495913753) [五层街边建筑环](https://www.openstreetmap.org/way/495913755) [来源、拍摄时间和签名](reference-review.json) [地理配准](footprint-review.json) [两栋地块图](../../../data/audit/gascogne-main-front-v1/registered-buildings.png)

[旋转查看本栋](../../../gascogne-apartments-main.html) · [上海主地图](../../../index.html#landmark=xuhui-gascogne-apartments-main-building&mode=overview) · [三份GLB和Blender工程](../../../assets/models/candidates/xuhui-gascogne-apartments-main-building/manifest.json) · [几何与地面检查](../../../data/audit/gascogne-main-front-v1/README.md)

## 从源码生成

需要Python 3、NumPy、Shapely、Node.js、Blender、gltfpack、ImageMagick 7的 `magick` 和Open Image Denoise的 `oidnDenoise`。在 `projects/shanghai` 目录执行以下命令。

```sh
python -B source/precise/xuhui-gascogne-apartments-main-building/source/build_model.py --out /tmp/gascogne-main-model --audit /tmp/gascogne-main-native --decoded /tmp/gascogne-main-decoded --gltfpack gltfpack --oidn oidnDenoise
python -B source/precise/xuhui-gascogne-apartments-main-building/source/check_surfaces.py --manifest /tmp/gascogne-main-model/manifest.json --out /tmp/gascogne-main-surfaces.json
```

原创几何、材质及代码按项目MIT许可。公开图片归原作者或出版者，模型未使用照片贴图。地理轮廓使用OpenStreetMap贡献者及Overture Maps开放数据。2013年Livelikerw的街景照片采用CC BY-SA 3.0授权。[照片作者和授权页](https://commons.wikimedia.org/wiki/File:Gascogne_Apartments.JPG)
