# 浙江第一商业银行大楼 · 江西中路与汉口路街面

上海市房管局第二批保护名录2A040列「浙江第一商业银行」，现名栏为「华东建筑设计研究院」，地址汉口路151号。地方志另记江西中路222号。市文旅局刊载的馆藏照片显示，银行营业厅的大门朝西临江西中路，办公入口朝北临汉口路，两个门牌属于同一栋建筑。[房管局名录](https://fgj.sh.gov.cn/yxlsjz/20210922/8f72fa07617c4828a25ef948cd1c5da7.html) · [来源、作者、日期和图片摘要](reference-review.json)

1909年创设的浙江银行在1923年官商分拆后，商股成立浙江实业银行，1948年10月改名浙江第一商业银行。浙江兴业银行为另一家「南三行」成员。1940年原设计开始打桩后因战事中断，1947年行号图仍将地块标为空地。1948年由华盖建筑事务所陈植重新设计，11月开工，1951年9月15日竣工。华建集团档案馆照片记录最初的八层与退层，地方志记后曾加建；2019年航照可见改造后的顶缘。[上海金融志、上海名建筑志及1948年图签](reference-review.json) · [上海市文化和旅游局《建筑可阅读》](https://new.qq.com/rain/a/20220702A01Y0Y00)

西正面保留七排水平条窗和遮阳板。磨光金山石基座在营业厅门两侧各有三大开间，门洞向内退入。斜切的街角接续下部六排水平窗，顶部为小窗和院名。汉口路短面以通高竖窗、脚下的办公门和较低窗墙构成。模型使用2019至2022年街面可见状态。照片中的屋顶花园、后排屋面及上部增建的室内范围未作复原。[2019年Legolas1024航照，CC BY-SA 4.0](https://commons.wikimedia.org/wiki/File:浙一大楼·华东设计研究院·航拍.jpg) · [单体页](../../../chekiang-first-bank.html)

冻结城市来源1477与现行OSM地块w380339941的投影交并比97.88%。西正面、斜角、北边分别约44.04米、15.77米、21.06米。用三处地面角点和顶缘与航照作单像拟合，主檐约35米，控制点分量均方根误差约10像素。高度、退深、窗格、砖色及门廊细部都有估计成分。地图数据署名 OpenStreetMap contributors（ODbL 1.0）及 Overture Maps Foundation。几何按项目MIT许可证发布，门面用字为独立字体子集。[地块与坐标](footprint-review.json) · [图像拟合](photo-fit.json) · [字体及许可](source/fonts/provenance.json) · [项目许可证](../../../../../LICENSE)

从 `projects/shanghai` 重建需要 Python、Shapely、NumPy、mapbox-earcut、fontTools、Node、Blender、gltfpack、ImageMagick 7 和 Open Image Denoise。原生工程保存后重新打开，校验实际网格并生成渲染。网页近、远两档分别实解码后再与对应源网格核对材质与三角面朝向。

```sh
python source/precise/huangpu-chekiang-first-commercial-bank/source/build_model.py \
  --out assets/models/candidates/huangpu-chekiang-first-commercial-bank \
  --audit data/audit/chekiang-first-bank-v1
```
