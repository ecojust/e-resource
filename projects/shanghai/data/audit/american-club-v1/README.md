# 美国花旗总会福州路主立面核对

市房管局第二批2A031登记在福州路209号，原称栏为“美国花旗银行”，公布时名称为“高级法院”。《上海名建筑志》、黄浦区政务现场报道、Virtual Shanghai建筑569及照片1341共同辨认此处为旅沪美侨总会。历史斜视和2013–2023年当代影像支持七开间临街立面、四柱门廊、通长铁栏、顶层白石拱窗和紧邻转角的首跨。[名称及图像来源](../../../source/precise/huangpu-american-club/reference-review.json)

原始及网页模型均有80,432个三角面，简化远景为36,554个。Blender重开逐材质核对85个可编辑网格与12种材质。七个拱窗与中段三排窗上下对位，前凸的三开间门廊由四根圆柱支承，下方可见扇形顶光和两面门扇。两端挑檐已用沿整条U形转角连续的石带建模，正面与短侧面之间的接缝闭合，窄内侧露出深色屋面。51个几何及材质射线核对覆盖三份GLB，两个外檐转角均沿正面达到完整挑出深度。[文件及哈希](../../../assets/models/candidates/huangpu-american-club/manifest.json) · [原生核对](geometry-native.json) · [预览](huangpu-american-club-preview.png) · [射线验证](opening-rays.json) · [目视记录](visual-review.json)

原生地图的1488号来自同一实名OSM建筑。地图仅移除精细主立面、两侧短段与原生重合部分，保留近景投影的90.58%、远景的90.73%。共享瓦片另外9个所有者零重叠。精细模型与遮罩的源侧距离和六处通行查询可复核，含前廊内、柱脚、门扇与公共人行道。[固定底图与实名OSM](../../../source/precise/huangpu-american-club/footprint-review.json) · [近远源核验](footprint-review.json) · [放置合同](final-placement-contract.json) · [默认镜头视线](overview-sightlines.json)

从上海项目目录运行，MACRO为14-13720-6694原始宏区目录，WORK为空目录。

    python -B data/audit/american-club-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/american-club-check
    python -B data/audit/american-club-v1/check-openings.py --work "$WORK" --report /tmp/american-club-check/opening-rays.json

在正式单体页面用 Chromium 156 分别打开桌面和手机视口，切换近景及远景。桌面与手机的两个层级均完整显示七开间、中央四柱及顶层的连续拱窗。网页实际下载的三份 GLB 和 Blender 原文件逐一通过 SHA-256 核对。[浏览器记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

以HTTP读取前序和当前两个冻结站的完整目录，核对前序模型条目逐项一致、本站仅新增本文模型及其裁剪合同。[前后两份目录的响应哈希](predecessor-controls.json)

### 114处上海主图

从黄浦区建筑目录打开福州路209号，桌面和390×844手机均展示七开间正面、中央四柱门廊与浅色顶层拱窗。入口、顶层、后段屋顶接缝及街区远景另取四个机位。桌面默认的名称牌覆盖部分高窗，手机名称牌位于屋顶上方。仅裁剪同块十个所有者中的1488号，六处地面碰撞符合模型边界。远处实际切换并核对简化模型。[桌面](main-desktop.png) · [四柱门廊](tuscan-portico.png) · [顶层拱窗](marble-arcade.png) · [保留的后部](retained-source.png) · [街区远景](distant.png) · [手机](main-mobile.png)

桌面初次进入即选用详细目录。手机初次进入时退回粗分块，验收程序在同一页重新请求项目的详细目录并成功加载。手机截图反映重试成功后的状态。四种模型文件经HTTP下载并与成品清单逐项校验。真实浏览器核对了162项同源运行输入和4项生成记录；逐图说明保留浮动标签和邻屋前景的遮挡情况。[浏览器](main-map-browser.json) · [运行输入](main-map-inputs.json) · [逐图说明](main-map-visual-review.json) · [114处发布快照](production-snapshot.json)

完整六图的实拍目录哈希为 `f05e62e8…`。其后更新了尚贤坊门楼与董家渡天主堂的默认镜头，原始拍摄输入维持可追溯。新旧对照逐项核实美国总会的机位、四件模型、源体裁剪及其余建筑条目，并列出当前发布目录的完整哈希。[新旧输入差异](camera-input-revision/input-difference.json) · [机位参数核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收10,153,623字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/bbf07f8cdbd30a16bd55ff40fbb0821074725551/projects/shanghai/index.html#landmark=huangpu-american-club&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

更新后的114处正式站点从黄浦区目录重新实测默认入口。1000×700桌面画面可见七开间砖墙、顶层弧窗及底层四柱，灯牌叠在檐线中央上方。浏览器命中本楼灯牌，载入1488号所在十个所有者的近景瓦片，并核对目录、运行模块和网页模型等八个HTTP文件。[新版默认桌面](camera-input-revision/current-default-desktop.png) · [实机、下载指纹与相机](camera-input-revision/current-default-browser.json)
