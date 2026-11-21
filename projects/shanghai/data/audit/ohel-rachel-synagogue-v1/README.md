# 西摩路会堂院内柱廊与侧窗

陕西北路500号教育机构院内的西摩路会堂，在市房管局第二批名录中为2B014。世界古迹基金会的现场铭牌照片标有1920年。1930年前后的入口斜照、2013至2026年的院内实照和基金会航拍可以辨认东向双柱凹廊、石环圆窗、下窗的断山花、门廊后方带半圆窗的山墙、长墙的两排窗，以及红瓦双坡屋面。基金会的窗框近照可辨圆拱内的金属曲线。现有南京西路722号犹太人总会南楼的模型锚点距此1,012.19米。[制作范围与原照](../../../source/precise/jingan-ohel-rachel-synagogue/README.md) · [照片、地址和航片记录](../../../source/precise/jingan-ohel-rachel-synagogue/reference-review.json) · [既有模型距离](prior-model-coverage.json)

原生场景重开后有60组可编辑网格。原始与网页近档各29,008个三角面，远档20,356个。三档各量39条射线，核对双柱的柱座、柱身、顶板、圆窗石环、门扇、半圆气窗、阳光下可见的檐部、五组侧窗及瓦坡。早期试测有五条瞄准玻璃的射线恰好击中横窗框，最终保留这些窗框测试并另测相邻玻璃。山墙最高12.84米是模型估算值。[原生图](jingan-ohel-rachel-synagogue-preview.png) · [原生几何核验](geometry-native.json) · [三档表面实测](surface-checks.json) · [四件交付文件](../../../assets/models/candidates/jingan-ohel-rachel-synagogue/manifest.json)

与具名建筑OSM 206515891第5版比较，城市场景1701号原件的地面范围重合97.62%。原件近、远两档的估高都是31.09米。模型边界仅替换会堂，本组其余13栋和院内通道均保留；最近的3158号楼在近档距裁剪边缘10.29米。地面边界把入口内凹处扣除，按解码网格加回两根独立柱的柱座。16处样点包括柱间净空、柱后通道和门后实体。两种屏宽分别从公开默认机位核对了八处外观视线。[底图与邻栋](../../../source/precise/jingan-ohel-rachel-synagogue/footprint-review.json) · [实际网格和地面范围](placement-geometry.json) · [两屏视线](camera-sightlines.json)

独立查看器用桌面鼠标和390×844触屏实测。正面可见柱间退入的门和两翼圆窗，斜视可见山墙后退及两排侧窗。手机全貌下不能读出浮雕细部。桌面实际点击保存四份文件并逐件复核长度与SHA-256。[查看器实测和四件下载](viewer.json) · [桌面正面](viewer-desktop-full.png) · [桌面斜视](viewer-desktop-portico-and-side-windows.png) · [手机斜视](viewer-mobile-portico-and-side-windows.png) · [单体页面](../../../ohel-rachel-synagogue.html)

在高阳大楼已加入的262处城市目录中，按全部222个既有候选的建筑边界重查本址。既有犹太总会的放置范围距会堂966.88米，最近的望德堂院内门廊与曲线山墙仍相离219.57米。会堂地物1701此前没有归入模型，新版沿用校园内各邻栋的底图。[262处前版完整核对](final-prior-coverage.json)

两端最终地图的目录、入口模块和原底图近远档均已发起HTTP请求。263处版本又核对了单体查看页、脚本、清单和四个下载。最终站逐项读取1,618个文件、1,340,677,073字节，五次范围请求均与完整文件对应位置的字节相同。[前后版本及冻结底图](signed-stations/real-28k-predecessor-and-new-building.json) · [逐层签名](signed-stations/26k-comparison.json) · [最终全量HTTP](signed-stations/28k-all-http.json)

31226正式站的七个地图场景完成10幅实拍，独立页面另存6幅桌面与手机图，四件下载逐字复核。地图和独立页初次失败及随后成功均有记录。[地图实测](final-map-31226/results.json) · [六图四下载](final-map-31226/independent/viewer.json) · [初次记录](city-31226/archived-browser-attempts.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/224c39fa21ac4c0c44a9d804b2189f4a77f697b1/projects/shanghai/index.html#landmark=jingan-ohel-rachel-synagogue&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
