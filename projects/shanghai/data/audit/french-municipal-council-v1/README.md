# 法公董局旧址 · 现存北街面

2C001市房管局原表登记淮海中路381号，公布时为综合办公楼。工作名录另作375号、中环广场。现实正门的题字、实名街坊建筑与现状POI均指向381号。1999年改建保留及依原样恢复了部分街面构件，这件外观模型止于街面后约8米。原庭院、38层办公塔和其余裙房保留在各自城市位置。[历史分期和已核原表](../../../source/precise/huangpu-french-municipal-council-front/README.md) · [登记及街景资料](../../../source/precise/huangpu-french-municipal-council-front/reference-review.json)

三处街景提供正门交会位置，航片可独立识别中央浅色屋顶。模型原点约在旧源北边中点往东7.55米、向街3.62米处。两端及中央砖翼前出，两段连窗向后退。立面宽约59.3米，端点各有数米估计误差。照片中的石拱、题字、扇形上亮、三联窗及雨篷均以几何表达。[原始街坊及邻楼](../../../source/precise/huangpu-french-municipal-council-front/footprint-review.json) · [原生整体实图](huangpu-french-municipal-council-front-preview.png)

原始模型、网页近景各35,588个三角面，远景16,652个。Blender重开后逐材质比对85个可编辑网格。三份交付GLB各检验73条射线，逐一核对上下层所有主要窗组、正门扇形上亮的玻璃和辐条、六个屋顶窗、四级踏步及截面以外的空域，共219项通过。[原生重开](geometry-native.json) · [实解码射线](surface-checks.json) · [四项资产](../../../assets/models/candidates/huangpu-french-municipal-council-front/manifest.json)

原有源2541仅沿北缘裁去与新街面相接的部分。近景保留原投影面积79.43%，远景保留79.59%。L形接缝由两段封闭，截面实际源高9.60米。近景后侧有1,074个三角形中心靠近共享边界，全在裁剪范围以外。在裁剪边1米以内，归属源与第二近源的几何距离至少相差11.89米。高楼源1304和2476、对街2357及现有尚贤坊门楼的位置保持独立。四级台阶与门洞前段可步行，石门框和向后退的门扇可阻挡通行。[裁剪合同](final-placement-contract.json) · [两档源网格和地面实测](placement-geometry.json)

独立页在1250像素桌面与390像素手机上均实际切换近远两档，原始、网页近景、远景和原生文件均从页面下载并比对哈希。[独立页](../../../french-municipal-council.html) · [浏览器与下载](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

局部实图分别展示拱内辐条、门牌与沿街窗篷，以及西段屋顶窗的开口和帽盖。[正门细部](entrance-fanlight.png) · [西段屋面](west-shop-roof.png) · [三个原生视角的像素复核](native-visual-review.json)

法公董局临街立面加入后的城市目录共144处。全城运行时分配616个裁剪三角面，覆盖13个宏块，单块最多250个。该建筑所在的绘制组只启用两片，西侧尚贤坊和原有现代裙房分别保留。[运行时核验](runtime-placement.json) · [144处登记及输入指纹](production-snapshot.json)

桌面及手机实际从地图目录进入了淮海中路保留立面。前一版有143处，能看到原有现代裙房及对街建筑。144处的后态显示了红砖窗排、弧形门头和西段屋面的天窗，远景切到简化模型。对街的灰色窗墙挡住了中央入口的一部分，手机默认视角还有地标名称遮住门扇。查看完整的拱内辐条和门牌，可打开单体页的正门细部。全部15处地面点都符合预期，包含人行道、门阶、保留的1999年后部及四个独立邻接源。两次浏览器实测没有页面错误。[原143处](map-before.png) · [桌面](map-desktop.png) · [手机](map-mobile.png) · [街面](map-street-facade.png) · [屋面](map-roof.png) · [远景](map-distant.png)

浏览器实取了原始、网页、远景GLB与可编辑Blender文件以及近远两种城市源，逐份核对字节数和SHA-256。另对前版99至101项的20个公开固定地址复核，共16,565,000字节。[前态浏览器记录](control-browser.json) · [后态浏览器、地面及文件](main-browser.json) · [143与144处正式输入核对](143-144-preflight.json) · [前项公开下载](predecessor-public-downloads-143.json)

将143至144处测得的街景相机与原生轮廓叠合，源2357的30.15米屋顶四角与灰色前楼逐边一致。它位于道路对面，与本栋2541的裁切没有交集。[实图与轮廓叠合](retained-neighbor-2357.png) · [源号、相机及投影坐标](retained-neighbor-2357.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/240a6d6bbe9ba913974f6dd4f55a8e58e20df028/projects/shanghai/index.html#landmark=huangpu-french-municipal-council-front&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
