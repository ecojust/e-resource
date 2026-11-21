# 德义大楼临街立面核验

网页近档和原始各有168,810面，远档44,288面。Blender重开了可编辑网格并核对材料、顶点和三角面。对比首张原生图后，窗间墙补上错位铺砌的焦褐色与浅橙色短砖。[初稿](preflight/before-upper-brickwork.png) · [2014年对照](2014-street-corner.jpg)。三档各有149条首表面或留空射线，覆盖底层橱窗、钢窗凹槽、砖墩、转角石带、顶缘和路面。[四件清单](../../../assets/models/candidates/jingan-denis-apartments/manifest.json) · [原生复核](geometry-native.json) · [表面实测](surface-probes.json) · [原生取景](native-framing.json)

宏块14-13719-6694内的993号地块与具名OSM足迹双向重合99.04%和99.50%。近档保留底模投影的55.13%，远档保留55.26%。沿街窄带单独配准，临街橱窗内侧有碰撞，外侧人行道留空。同组322、617和对面的同孚大楼1964均保留。[源几何与碰撞](footprint-review.json) · [城市登记](final-placement-contract.json) · [桌面与手机取景估算](../../../source/precise/jingan-denis-apartments/camera-preflight.json) · [原照与授权](photo-credits.md)

正式23195与23196源站分别返回232、233处地标的目录。此前192处候选行逐字节对应。实取1367份文件，共1,183,261,247字节。运行时只对993号的临街弧面实施局部归属裁切；地面验证覆盖两条街的橱窗、转角内外、背面保留区和邻楼。[两代目录](renderer-parent-controls.json) · [全量实取](renderer-release-http.json) · [运行时通行与邻楼](renderer-runtime-placement.json)

独立模型页已在桌面和手机各切换一次近景与远景。四张实图均能分辨南京西路一侧的窗间砖墩、底层店面和连续二层石带。桌面的四个下载按钮分别取得原始、近景、远景与可编辑Blender文件，实收文件与清单SHA一致。[交互与下载记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

正式31195和31196城市目录从232处增至233处。390×844手机触屏打开德义大楼，可从弧形转角屋顶看到临街橱窗。790×590桌面用鼠标打开同栋时已载入168,810面近景模型，地点牌挡住地面层一部分；点一下「拉近视角」后，城市近景瓦片也已载入。两个默认视角均保留。屋顶图能辨随街角弯折的女儿墙，路口低位图可见两条街交接处的石带、店面大窗和窗间墩。[手机默认](city-31196/phone/map-mobile-settled.png) · [桌面默认](city-31196/desktop/map-desktop.png) · [拉近一次](city-31196/desktop/map-desktop-after-zoom-button.png) · [屋顶](city-31196/architecture/map-roof.png) · [转角底层橱窗](city-31196/shopfront/map-corner-retail-glazing.png)

街区内鼠标和触屏分别点中同一栋楼，街沿内外和邻楼共19处地面检测符合登记，远档实载44,288面。单体页两端切换近远档，四种下载共16,605,883字节，文件逐件与制作清单一致。初轮桌面检查曾在默认缩放17.05等待街区近瓦片，正式街区模块的启用阈值为17.3。原次记录及其哈希可供还原。[入场与下载](city-31196/visual-review.json) · [原桌面等待记录](city-31196/first-desktop-attempt/source-and-recovery.json) · [原专项等待记录](city-31196/first-architecture-attempt/source-and-recovery.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 42 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/9234f7012eea783d3e6a2ad040ab19402bf4927e/projects/shanghai/index.html#landmark=jingan-denis-apartments&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 42 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
