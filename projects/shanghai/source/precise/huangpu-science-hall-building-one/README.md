# 上海科学会堂一号楼 · 南花园

房管局第二批优秀历史建筑2C008登记原名「法国总会（老）」，现名「科学会堂（一号楼）」，门牌南昌路47号。原会所1917年建成。法国总会在1926年迁往茂名南路，南昌路房屋改作法国学堂。1927年南花园档案照片已经可以完整看见五个亭顶。1958年起用作科学会堂，国务院2019年公布的第八批全国重点文物保护单位名单按「上海科学会堂」收录，年代栏为1958年。[房管局原表](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [国务院第八批名录](https://www.gov.cn/zhengce/content/2019-10/16/content_5440577.htm) · [逐项证据](reference-review.json)

本栋于2011至2012年修缮，2012年12月竣工。设计团队记载的项目本体面积为5,233平方米。工程恢复原有木框门扇、外门窗和室外平台，清洗原灰色卵石外墙，补配缺石。2014年8月2日，Legolas1024拍到了工程完成后的南花园立面。花园近照还显示了中间亭三扇木窗合成的弧形窗头、底层入口及深色成组木牛腿。1927年图像用来校对开间与原有屋顶，其门廊形式与后来的露台存在差异。[修缮设计团队记录](https://www.archina.com/index.php?a=show&g=works&id=2262&m=index) · [2014年花园实照](https://commons.wikimedia.org/wiki/File:上海科學會堂.jpg) · [修缮前后对照](https://www.thepaper.cn/newsDetail_forward_11455180) · [1927年正面照](https://commons.wikimedia.org/wiki/File:The_Municipal_College_in_the_French_Concession_of_Shanghai_1927.jpg)

模型覆盖钟亭、两处中间亭和两端盔顶亭面向花园的一侧。四段有券窗的长廊连到中央露台与石阶。护栏、方柱、开敞廊面、窗棂、卵石表面、中央时钟、屋檐木牛腿和可见坡屋面用独立几何表现。窗宽、楼层高度、屋檐深度以及钟面指针近似自照片。现行一号楼来源与原城市4396的足迹交并比为98.50%；中央门廊伸入花园，前边实测约11.78米。将五处亭的测定轴线投影回1927年1020像素宽原片，五个观测窗洞中心与拟合曲线的均方根偏差约0.96像素。三期航片共同显示花园侧的红瓦屋面与两端低平顶延长部存在明确分界。[五亭照片控制点](pavilion-study.json) · [位置与航片](footprint-review.json) · [可下载模型](../../../assets/models/candidates/huangpu-science-hall-building-one/manifest.json) · [独立预览](../../../science-hall-one.html)

北面的南昌路入口、园内后期增建的建筑以及未由花园资料确认的屋顶后坡保留原城市形体。场地方的资料另将南昌路59号的思南楼记为2001年落成的16层楼房；周边5、7、8号楼、独立国际会议厅、科学技术展馆也均有各自的地块。地图几何署名© OpenStreetMap contributors（ODbL 1.0）及Overture Maps Foundation，航片归Esri及各期供图方。工程未嵌入研究照片，原创网格依项目MIT许可证提供。[场地方历史介绍](https://web.archive.org/web/20170601220732/http://www.sciencehall.org/cn/jieshao.htm) · [项目许可证](../../../../../LICENSE)

从 `projects/shanghai` 重建时需Python、NumPy、Shapely、mapbox-earcut、Node、gltfpack、Blender、ImageMagick 7 与 Open Image Denoise。

```sh
python source/precise/huangpu-science-hall-building-one/source/build_model.py \
  --out assets/models/candidates/huangpu-science-hall-building-one \
  --audit data/audit/science-hall-one-v1
```
