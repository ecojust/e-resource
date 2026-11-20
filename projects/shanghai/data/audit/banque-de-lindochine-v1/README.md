# 外滩29号临江立面验收

四个正式下载包含55,976个三角面的原始及网页近景、34,124个三角面的网页远景，以及含75个可编辑几何对象的 Blender 工程。重新打开工程并按材质逐面比对，八类材质的方向及三顶点坐标与原始 GLB 一致。近、远两个压缩文件均经独立解码。[下载清单](../../../assets/models/candidates/huangpu-banque-de-lindochine/manifest.json) · [工程与解码记录](geometry-native.json) · [Blender 正面渲染](huangpu-banque-de-lindochine-preview.png)

逐档38条射线，共114条，核验底层四拱窗、二层五窗、三层九个矩形窗、两根大柱、后退门扇、折断门冠、屋顶的实体与透空部分及浅剖面边界。参考2017年正照，模型可见明确的五开间比例、两端较高的实心女儿墙、中部石栏；浮雕花叶、行名字形及砂石色泽为按像片辨认后的简化。[实测射线、材料及距离](surface-checks.json) · [原址资料和年代](../../../source/precise/huangpu-banque-de-lindochine/README.md)

## 城市配准

现场楼体沿外滩排列。两端边点取自城市冻结楼2037的东边，临江面向东，作者正向北。面前是中山东一路，南邻格林邮船大楼，隔北京东路后才到怡和洋行。[底图、源版本、现行地块与道路](../../../source/precise/huangpu-banque-de-lindochine/footprint-review.json) · [真实街坊示意](street-blocks.png)

地图保留本楼余下进深。核验按原始三角面分别量取近、远模型之保留比例，近景保留95.7844%、远景保留95.9022%，以一条截线封合后续粗模，另解码格林邮船及怡和所在近、远组核验相离。中央门后退的可行走门槛在碰撞轮廓中单独处理。[配准合同](final-placement-contract.json) · [本楼与独立邻楼测量](placement-geometry.json)

101处直接运行目录的冻结指纹已登记。运行时代码验证了本源、两种矢量底图和相邻源。全市合计386个裁剪三角形，分在8张宏块表内，单表最大141个。[登记输入](production-snapshot.json) · [运行时回归](runtime-placement.json) · [参考照片与成品渲染对照](visual-review.json)

独立预览在1250×820桌面和390×844手机均可切换两个细节档。四项下载按实际响应大小、SHA-256校验，检查中页面异常为零。[实测报告](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

## 真实主地图

100处对照中的普通方窗楼，在101处手机及桌面默认视角改为五开间石立面，两旁原楼继续可见。近景装载55,976面，远景切换至34,124面。九处真实碰撞点包括可走门槛、闭合门扇、两侧墙、保留的旧楼核心和三处邻楼。320×568手机的全城图另核101个独立中心和101个实像灯牌，真实触按101号打开本栋。[前态100](control-browser.json) · [主图101](main-browser.json) · [101处实像与触控](compact-browser.json) · [默认手机视角](map-mobile.png) · [101号灯牌](map-101-markers.png) · [画面复核](map-visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 32 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/47e46c4989b7be3a4136a272e167e41556fc98c1/projects/shanghai/index.html#landmark=huangpu-banque-de-lindochine&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 32 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
