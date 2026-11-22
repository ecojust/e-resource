# 陕西北路186号荣氏花园住宅

本模型取花园立面西南端的多面角塔和相接的一开间双层柱廊。沿陕西北路看，树后露出红褐色圆顶和尖饰，中层三个折面的窗下各挂一道花环。从花园看过去，还能分辨下层拱窗、楼上深色窗框、两层独立柱、黑色铁栏和屋面上的石栏瓶柱。市房管局第四批表将186号登记为4B002「荣氏花园住宅」，早期公示称「荣家老宅」。[现行市表](https://fgj.sh.gov.cn/yxlsjz/20200331/e3b99cf457ae48cab87ad5c02aa0fee3.html) · [市政府原公示存档](https://web.archive.org/web/20161130014959/http://www.shanghai.gov.cn/nw2/nw2314/nw2319/nw12344/u26aw2359.html)

Prada集团于2011年启动修缮，2017年10月12日重新开放住宅。模型取开放后的花园面外观。Livelikerw在2015年1月21日从街上拍摄的原图可核窗下花饰、塔面折角、圆顶板缝与尖饰。花园实照则能辨出落柱位置和栏杆。原照按索引保留摄影者和许可，公开模型的铜板、抹灰、玻璃与花饰均独立制作。[业主的修缮记述及花园正照](https://www.pradagroup.com/en/perspectives/stories/sezione-progetti-speciali/prada-rong-zhai.html) · [Livelikerw街面原照](https://commons.wikimedia.org/wiki/File:186_North_Shanxi_Rd._Shanghai.JPG) · [照片、图幅和署名](reference-review.json)

市图原有建筑749与带4B002登记号的地图轮廓相交约97.9%。花园一侧的外轮廓边长约22.58米。两组俯视影像可以辨认伸向花园的敞廊和圆顶，树冠遮住了部分楼基。模型以中央窗面约3.30米及下层腰线约4.50米作尺度假设，从两张照片的25个点估算其余层高和收分。回投误差中位数2.72像素，最大8.90像素。模型尖饰约高17.78米。这些数值供外观重建使用。[原有地块与尺度依据](measurements/footprint-and-scale.json) · [逐点误差与两处摄影机位](measurements/two-photo-fit.json) · [重算程序](measurements/measure_tower.py)

近景保留三个开窗折面和每扇窗的凹进深度，下层半圆拱有凸起的拱心石。花环分出搭接叶片、垂带和中心小果，檐下有齿饰。圆顶使用独立生成的错缝铜板表面，八条凸肋通向顶部双节尖饰。相邻一开间的上下层均可横向穿行，后墙的门扇位于柱后。其余开间、主屋其他立面、花园围墙和室内另列。[角塔与花饰](source/garden_tower.py) · [园廊](source/colonnade.py) · [铜板表面](source/copper_roof.py)

原城住宅的西南角与首间敞廊占用了新模型的位置，沿两条与主屋相接的边补上截面。原有主屋约84.7%的投影面积得以保留。庭园内的定位精度约4米。[原城建筑的识别](footprint-review.json) · [原有主屋与园廊的位置关系](../../../data/audit/rong-residence-garden-tower-v1/placement-notes.md)

在上海项目目录运行 `python source/precise/jingan-rong-residence-garden-tower/source/build_model.py --out 输出目录 --audit 检查目录 --decoded 解码目录` 可重建网格、近远两档、可编辑的Blender文件和预览。可以用 `--blender`、`--gltfpack` 或 `--oidn` 指定工具路径。[建模入口](source/build_model.py) · [三档网格实测](../../../data/audit/rong-residence-garden-tower-v1/preflight/geometry-rays.json)
