# 中华路581号小南门警钟楼

警钟楼位于上海救火联合会旧址的院内。1907年成立的联合会曾在此办公。今人多将建塔年份记为1909年，1918年刊行的《上海县续志》卷二〈救火会〉则记警钟楼于宣统二年（1910年）落成。1911年上海光复时，塔钟曾用作信号。《上海县续志》记载原铜钟挂在第四层，值班室四面开窗。2017年进入塔内拍摄的Jude记录了瞭望室、旋梯与梯井，原铜钟当时已不在塔内。2024年8月，《上观新闻》三名记者进入保护围护区，确认周边旧房拆除时塔体仍在。[1918年版《上海县续志》卷二原页](https://upload.wikimedia.org/wikipedia/commons/f/f2/上海縣續志_-_民國七年_%281918%29.pdf#page=123) · [上海市房管局4A038](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [澎湃新闻现场与方志调查](https://m.thepaper.cn/newsDetail_forward_1452498) · [2017年塔内照片](https://chinaruins.eg2.fr/2017/06/08/xiaonanmen-bell-tower/) · [上观新闻2024年现场报道](https://export.shobserver.com/baijiahao/html/784483.html)

模型采用2016至2020年照片里的外观。四道高拱支在四个向外张开的角脚上。逐层收分的斜柱之间有交叉铁撑，各道横梁饰交织椭圆，底层拱缘有较小的曲线花饰。瞭望室下方的平台带透空栏杆。四面长窗都嵌入墙内，平屋顶有四个方形栏柱和外挑檐。临街司法入口、围墙、救火联合会办公楼各有独立位置。民国早期带横板小窗的值班室、历史铜钟和后期围护属于另外的年代。[2016年正面](https://commons.wikimedia.org/wiki/File:Bell_Tower_at_Xiaonanmen.jpg) · [2016年塔脚向上](https://commons.wikimedia.org/wiki/File:%E5%B0%8F%E5%8D%97%E9%97%A8%E8%AD%A6%E9%92%9F%E6%A5%BC.jpg) · [2020年院内俯视](https://commons.wikimedia.org/wiki/File:%E5%B0%8F%E5%8D%97%E9%97%A8%E8%AD%A6%E9%92%9F%E6%A5%BC%C2%B7%E4%B8%8A%E6%B5%B7%E6%95%91%E7%81%AB%E8%81%94%E5%90%88%E4%BC%9A%C2%B7%E4%B8%8A%E6%B5%B7.jpg) · [史料、年代与许可](measurements/historical-sources.json)

依照报道的35.2米总高，用正面和斜俯两个机位共同求取方形塔架的收分和水平梁高。估计基脚外宽约14.40米，底层拱顶横带约9.17米，中段横梁约16.70米，露台约24.06米，值班室下沿约29.15米，屋檐约33.29米。按720像素宽的影像量算，标点重投影误差中位数2.10像素，最大9.53像素。基脚局部被建筑与树冠挡住，故外宽和足部形状的误差大于檐带各层。这些尺寸来自影像拟合。[测点及逐点误差](measurements/two-camera-calibration.json) · [摄影资料、署名及原图编号](measurements/photographic-witnesses.json) · [可复算的标定程序](measurements/calibrate_tower.py)

从塔内向上和向下的实拍均可看出铁梯中央留有贯通的梯井。环形踏步连接内外圈，扁铁竖条与铁箍交接处可见铆钉。模型区分踏步、内外圈、紧固件与扶手，内井贯通到瞭望室地面。踏级数、铁条间距和旋转节距为照片估计。照片中可见的墙面泛白、混凝土斑驳及窗下雨痕以原创程序纹理表现，照片仅供量测和外观对照。[塔内仰视原照](https://chinaruins.eg2.fr/2017/06/08/xiaonanmen-bell-tower/) · [模型梯井](../../../data/audit/xiaonanmen-fire-bell-tower-v1/preflight/full-views/looking-up-the-open-stair-well.jpg) · [生成石材表面的程序](source/tower_finish.py)

原始与近景网格各141,126个三角形，远景45,476个。近景1,094个构件归入100个可编辑组。两档均保留四脚、四道通行拱、旋梯内井、瞭望室窗洞和屋顶平台。原始与两档解码后三种网格各接受79条实射，检查脚底、窗玻璃、三个开敞区间的铁撑、四向行走和塔内水平踏级。10个近景机位分别用相同视线再渲染远景。[三档实测](../../../data/audit/xiaonanmen-fire-bell-tower-v1/preflight/geometry-rays.json) · [看两面塔脚](../../../data/audit/xiaonanmen-fire-bell-tower-v1/preflight/full-views/courtyard-and-four-footings.jpg) · [瞭望室与平台](../../../data/audit/xiaonanmen-fire-bell-tower-v1/preflight/lod-views/watch-room-and-terrace.jpg)

在上海项目目录运行 `python source/precise/huangpu-xiaonanmen-fire-bell-tower/source/build_model.py --out 输出目录 --audit 检查目录 --decoded 解码目录`，可生成原始、近景、远景、Blender文件和预览。程序从本地生成混凝土表面。可分别用 `--blender`、`--gltfpack` 和 `--oidn` 指定工具路径。[建模入口](source/build_model.py) · [范围及照片登记](reference-review.json)

院内的瞭望塔和救火联合会办公楼分开定位。塔脚只占方形外轮廓的四角，铁梯位于中央，弧拱下方仍能通行。旧城地图中的邻屋全部保留。塔位来自四处街景与俯视图像配准，坐标用于展示。[塔脚、周围建筑与定位误差](footprint-review.json) · [地图和近远两档检查](../../../data/audit/xiaonanmen-fire-bell-tower-v1/README.md)
