# 清心堂主堂东北内庭

现存主堂位于黄浦区大昌街30号。1860年成立的上海长老会第一会堂曾在清心书院聚会，书院原址在今陆家浜路597号。1919年信徒迁出书院，在大佛昌街筹建新堂，1923年元旦落成。1958年主堂成为南市区联合礼拜场所，1979年9月9日复堂。市房管局第二批优秀历史建筑登记为2A058（2E003），原名和登记时名称均为清心堂。上海市文旅推广网另载其于2014年4月4日列为上海市文物保护单位。[市房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [中国基督教两会堂点](https://www.ccctspm.org/churchinfo/206) · [上海市文旅推广网](https://www.meet-in-shanghai.net/cn/shanghai-cultural-relics-protection-unit/qingxintang-917865/)

从院门进入，可见两条互相垂直的红砖墙。两趟石梯沿墙向上，在正中拱门上方的平台会合。两会堂点的正照、2016年《福音时报》转引的徐汇老寿摄影、2018年从院门望进的实照，都可辨认门额、灰色实心栏板及两翼弧顶木窗。文旅条目另述沿街钟楼，2018年照片也把院外十字架门和院内主堂拍进了同一组图。建模范围止于内庭墙体、门洞和台阶。街口附属建筑及历史校舍另行登记。[堂点内庭照](https://www.ccctspm.org/backstage/uploads/ueditor/image/20180223/1519351166115675.jpg) · [2016年刊发的斜照](https://gospeltimes.online/article/index/id/36823) · [2018年院门与院内对照](https://k.sina.cn/article_2705103264_a13c99a000100a8ff.html) · [原件署名和校验值](reference-review.json)

底图338与现行OpenStreetMap同一具名主堂的平面交并比为97.14%。2022、2024和2026年发布的三期航片都有东北向凹角及其相接的两面屋坡。这些轴线决定两翼的相对位置。局部墙长、屋檐、平台、砖拱和混凝土踏步的尺寸结合地块与照片估计。所呈现的是东北内庭外观，门洞后方以暗色截面收口。沿街校舍、主堂完整屋面及室内装饰通过各自来源继续核查。[平面证据与影像归属](footprint-review.json) · [尺寸估算](elevation-study.json) · [在城市地图查看](../../../index.html#landmark=huangpu-pure-heart-church&mode=overview) · [独立模型页](../../../pure-heart-church.html) · [四件模型清单](../../../assets/models/candidates/huangpu-pure-heart-church/manifest.json) · [内庭验收记录](../../../data/audit/pure-heart-church-v1/README.md)

在 `projects/shanghai` 目录执行下列命令可重建原创网格、近远景和可编辑Blender文件。工具包括Python、NumPy、Shapely、mapbox-earcut、fontTools、Node、gltfpack、Blender、ImageMagick 7和Open Image Denoise。

```sh
python source/precise/huangpu-pure-heart-church/source/build_model.py \
  --out assets/models/candidates/huangpu-pure-heart-church \
  --audit data/audit/pure-heart-church-v1
python source/precise/huangpu-pure-heart-church/source/check_surfaces.py \
  --out data/audit/pure-heart-church-v1/surface-checks.json
```

建筑照片仅作为观察来源，权利归原作者。模型采用项目MIT许可证。三字堂额使用重新命名的Noto Serif CJK SC子集，保留SIL OFL 1.1。底图使用OpenStreetMap与Overture Maps，影像来源与图层链接见平面记录。[项目许可证](../../../../../LICENSE) · [字体来源与修改](source/fonts/provenance.json) · [OFL](source/fonts/OFL.txt)
