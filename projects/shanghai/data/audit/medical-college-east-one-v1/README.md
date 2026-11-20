# 国立上海医学院东一号楼

模型记录修缮前实照可辨的大礼堂和两翼方亭。公开来源区分1936年9月首期校舍建成与1937年4月启用。2017年草坪侧照片可核对三拱门、浅色立墩、朱红柱列和两端方亭，南侧斜照可逐个辨认九处老虎窗。2024年12月募资报道及2026年绿化公告记录了后续工程。[建筑范围与分期](../../../source/precise/xuhui-medical-college-east-building-one/README.md) · [照片、校园资料和登记地址](../../../source/precise/xuhui-medical-college-east-building-one/reference-review.json)

Blender重新打开原件，核对207个可编辑网格的带方向表面。原始及网页完整GLB各有165,976个三角面，简化版有58,980个。三份实际GLB各有30条首个交点射线，逐个检查九处老虎窗的玻璃、东西两端朝外的山花、双亭宝顶、楼梯窗、中央拱门和翼廊瓦面。翼部屋顶、柱距、彩绘和构件进深取照片估计。[带方向的网格与原生核验](geometry-native.json) · [三档共90条屋面与立面射线](opening-rays.json) · [原生南立面渲染](xuhui-medical-college-east-building-one-preview.png)

原生宏区14-13719-6696中的2076号源与校园地块w294625597的交叠面积占实名原始多边形的99.19%。近景与远景各自验证了目标源的完全替换和同组另外四栋的完整保留。模型裁剪边界距最近的其他原生建筑1938约2.22米。九个地面点分别测定草坪、入口踏步、方亭及南部楼梯凸体；北侧凹庭和与明道楼之间的通道保留为可通行空间。按照真实楼体边界与高程推算，650与844像素高度的默认镜头均可看见入口和两座方亭。[所有者与地面核验](footprint-review.json) · [安置及裁剪参数](final-placement-contract.json) · [两组视线](overview-sightlines.json)

在上海项目目录下以宏区来源收据的文件和空工作目录复核。

    python -B data/audit/medical-college-east-one-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/east-one-review
    python -B data/audit/medical-college-east-one-v1/check-openings.py --work "$WORK" --report /tmp/east-one-review/opening-rays.json
    python -B data/audit/medical-college-east-one-v1/check-overview-sightlines.py --feature-table "$MACRO/feature-table.json.gz" --contract /tmp/east-one-review/final-placement-contract.json --report /tmp/east-one-review/overview-sightlines.json

独立查看页的桌面与390×844手机均切换了近景和简化档。四个下载文件的实际响应逐一匹配签名，页面错误为零。主视角朝大礼堂北草坪，能同时看见中央浅色门廊、红砖两翼和两座方亭。[独立页浏览器报告](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [外观检查](visual-review.json)

正式城市目录从165处增至166处。两个实际HTTP服务返回的目录字节与各自冻结树一致，原有125个候选记录保持相同。[正式输入及SHA-256](production-snapshot.json) · [前后目录HTTP核对](predecessor-controls.json)

## 原取景的城市地图实测

从165处地图的中山医院3号楼出发，实测浏览器载入含1408、1426、2361、198和2076的原始近景组，当时东一号楼没有独立模型，组内五栋均完整显示。新增东一号楼后，同组只替换2076。主楼的完整模型165,976面、远景58,980面，两档均由实际地图加载。9个地面位置区分楼体、廊前和两侧草坪。[前态现场与完整原组](predecessor-map-browser.json) · [前态原图](map-before-23127.png) · [首次浏览器原始记录](first-map-browser.json) · [正式两站输入](city-23127-23128-preflight.json)

原桌面默认在900×650下，中山医院3号楼和东一号楼两块真实可选名牌挡住中央礼堂入口，两端方亭与主屋屋脊可见。390×844手机的默认缩放为17.136，原城市宏使用远层，选中建筑自身显示完整档。点一次页面“+”后缩放18.136，原近组随即加载。“手机加号后”的截图拍在这次操作之后。草坪门廊、老虎窗和东翼各有实际近取景。[原桌面默认](main-desktop.png) · [原手机默认](mobile-default-before-zoom.png) · [手机加号后](main-mobile.png) · [真实触控与加载门槛](mobile-threshold.json) · [北草坪入口](north-lawn-arches.png) · [屋面](nine-dormers.png) · [方亭与长廊](pavilion-and-gallery.png) · [远景](distant.png)

正常从东一号楼点到衡山路美童公学后，东一号楼模型退出，属于该栋的裁切已清空。本次初检将城市原生网格使用的 `localModel` 误归给新增候选，原报告保留这个断言与错误现场。随后在新增前的23127上分别从近景和远景离开、再返回，六个现场均保留同一城市远层建筑自身的 `localModel` 标记。其UUID为 `d2dc605e-5be1-4b23-89d9-bcd2c0aebdc1`，属于仍驻留的宏块14-13719-6696；中山医院3号楼另有独立UUID。[六个前态观察](predecessor-owner-states.json) · [两代同位置取样程序](check-owner-restoration.cjs)

## 修正取景后的正式主图

从正式目录选中东一号楼，900×650桌面和390×844手机均在默认画面看到礼堂三券门、两侧红砖柱、上方连廊和金色屋脊。截图前在同一画面检测七个位置，十四次均落在地图画布上且避开实际绘制的名牌；两端仍可从所选名牌中心点回本楼。桌面缩放18.524，手机17.905，直接从手机目录进入即可加载五栋原有建筑的近景组。青灰、红砖和金色屋顶可辨；左侧导航卡会挡住桌面画面远左侧一部分校园。[桌面默认](city-24128/main-desktop.png) · [手机默认](city-24128/main-mobile.png) · [桌面七点与名牌](city-24128/main-desktop-focus.json) · [手机七点与名牌](city-24128/main-mobile-focus.json)

城图仍将同组1408、1426、2361和198留给原有近景模型，只替换2076。北草坪入口、九处老虎窗和东翼方亭均有单独实景。九个地面点全部与草坪、门前和楼体的边界相符。[草坪立面](city-24128/north-lawn-arches.png) · [屋面细节](city-24128/nine-dormers.png) · [东侧方亭与长廊](city-24128/pavilion-and-gallery.png) · [远景](city-24128/distant.png)

在近景及远景分别从东一号楼点往美童公学，模型均离开，2076的候选裁切随即清空。相同地块原有的矢量状态与23127基线完全一致。再从地点列表返回，远景恢复58,980面，近景恢复165,976面以及五栋共用的近景组。四种下载已实际核对；两档城市源也与不可变的原始Git文件相符。[远档回返](city-24128/far-return-from-school.png) · [近档回返](city-24128/main-return-from-school.png) · [整套浏览器记录](city-24128/main-map-browser.json)

24127与24128的城市登记由165处增至166处，前125条候选记录逐条相同。正式服务的803项输入留有版本签名；本次浏览器实际观察到的141条资源路径，连同额外实取的原始GLB和Blender下载，共143件、103,748,767字节，已独立重新下载并逐一校验。另有6个本地登记和几何输入完成字节核对。[版本与取景绑定](city-24128/release-binding.json) · [实测文件白名单和SHA-256](city-24128/main-map-inputs.json) · [可复跑的正式测试](check-final-main-map.cjs)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/9adf9ece13cd72ce6249a752455bbd0c70bb5310/projects/shanghai/index.html#landmark=xuhui-medical-college-east-building-one&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 0 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
