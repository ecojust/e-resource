# 四号楼南廊、乘车门廊与望楼

学校现称四号楼的霍格别墅有东侧乘车门廊、三米深南廊和望楼。三层拱廊格致楼属另一栋。校方现状南面、望楼窗格、折铁皮翘檐、老照片和草坪鸟瞰都已逐张核对。[建筑身份与图片](../../../source/precise/changning-st-johns-administration-building/reference-review.json)

首稿通长的屋檐挡住中央上层木框和浅色墙带。修订后三段铁皮檐分别起落，中央额枋露出，望楼、带帽烟囱和车道雨篷可各自识别。Blender 4.3.2重开了80个可编辑网格、14种原创材质。原始与网页近景各46,008个三角面，远景20,272个。[修订前](preflight/before-frieze-roof.png) · [最终原生渲染](changning-st-johns-administration-building-preview.png) · [按材质核验](geometry-native.json)

三份GLB分别实测南廊净深、栏板孔与实体、后墙门窗、上廊木窗、车道净空、门廊柱、望楼窗与独立烟囱，共150项。默认视角在两种屏幕尺寸各测3219个实物采样点，地面车道和望楼均可见。[射线收据](veranda-checks.json) · [取景初核](camera-preflight.json)

冻结底图中四号楼为14-13717-6694内的320号地块，与现行具名地块重合97.91%。南侧上廊和车道局部纳入替换，北半房间继续保留。现行四号楼与名录新科学馆、思颜堂、思孟堂、西门堂分别与独立轮廓对应。[建筑与航片](../../../source/precise/changning-st-johns-administration-building/footprint-review.json) · [独立地块核验](placement-geometry.json)

162处版本逐一取回761个发布输入及6份本地城市源文件，共767个HTTP请求、701,195,514字节，全部匹配。近景组新增6片，其他校园楼在两种矢量来源中均保留。[HTTP收据](frozen-http.json) · [生产运行时检查](runtime-placement.json)

在1250×820桌面和390×844手机上，通过独立页切换了近景与远景。四张实图中均可辨认望楼、南廊及右侧车道雨篷。页面四项下载的实际字节均与清单一致。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机远景](viewer-mobile-lod.png) · [浏览器与下载收据](viewer.json)

在161处和162处的正式主地图用同一校园街区作前后对照。加入四号楼后，手机与桌面能看到南廊格栏、望楼和东端车道雨篷，拉远时实际切至20,272面的远景资源。24个地面采样点与预期一致。两版最终检测均无报错，首次前态旁侧瓦片的502和随后复取的原始散列一并留存。[原城市街块](city-23124/map-before.png) · [手机](city-23124/map-mobile.png) · [桌面](city-23124/map-desktop.png) · [南廊近景](city-23124/map-street-facade.png) · [屋顶](city-23124/map-roof.png) · [远景](city-23124/map-distant.png) · [浏览器与下载](city-23124/main-browser.json) · [视图与签名](city-23124/visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/15028d8b4c4fbd8b430b7f4f1b794bde372214ab/projects/shanghai/index.html#landmark=changning-st-johns-administration-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
