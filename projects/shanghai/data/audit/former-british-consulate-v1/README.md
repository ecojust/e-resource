# 原英国驻沪领事馆办公主楼

模型匹配中山东一路33号花园内南边的办公主楼。1911至1913年档案中的南面五券廊、东花园廊和随主楼延伸的西侧法院外墙可以逐一核对。原办公主楼（1873年）与北边另建的住宅（1882年）均有独立照片和轮廓。[档案与修缮资料](../../../source/precise/huangpu-former-british-consulate/reference-review.json) · [建模说明和重建命令](../../../source/precise/huangpu-former-british-consulate/README.md)

近景134,672面，远景62,872面。原始、网页和远景各作68个射线检查，覆盖南廊、东廊、窗扇退深、西侧石柱、烟囱及屋盖。初稿重开后，修正南墙与两侧墙相交处的重面，向下延伸西侧屋顶采光构件的底座，并按1913年照片区分北墙的矩形窗和拱形窗。[重开原生样张](huangpu-former-british-consulate-preview.png) · [原生零件与参数](geometry-native.json) · [204项实际几何取样](exterior-checks.json) · [四件下载](../../../assets/models/candidates/huangpu-former-british-consulate/manifest.json)

旧城市源3111在近、远两档均高约53.9米。照片所见两层办公楼和烟囱模型最高15.535米，窗台与檐口的标高均为估算。源3111在近、远档分别有72,584面和28面；源边界内的原顶已完全移除。两档中其他原生楼的投影均无损失。独立住宅1074与办公楼原轮廓相隔26.09米。依据门廊后墙、石柱、石栏杆和南北花园位置核对了12处地面点。[放置合同](final-placement-contract.json) · [近远档实测](placement-geometry.json)

默认从南、东间的花园侧俯看，朝向−47°，俯角48°。在桌面、手机两种窗口的几何预检中，南侧中央底层廊均可见。其他楼体保留。[相机预检](camera-preflight.json)

145处地图的577个冻结输入和4件城市源文件已逐个通过HTTP读取，581个响应共455,103,944字节。144处父目录的地标记录均保留。用该站实际加载的裁切与矢量实现核对后，办公楼所在9栋的近景组只有3111的6个裁切三角形，北侧独立宅邸1074保留。全市622个裁切三角形分在13张纹理，单张最大250。记录覆盖两种底图来源和廊内、庭园、住宅等地面取样。[冻结目录](production-snapshot.json) · [HTTP收据](frozen-http.json) · [全市运行配置回放](runtime-placement.json)

145处版本的独立页在1250×820桌面及390×844手机上切换了近远两套模型。近景134,672面，远景62,872面；南廊五个券洞、两层石栏、屋脊和西侧相接的法院外墙均在画面内。四件文件通过页面下载并逐一核对SHA256，页面未报告运行错误。[桌面近景](standalone/viewer-desktop-full.png) · [手机近景](standalone/viewer-mobile-full.png) · [桌面远景](standalone/viewer-desktop-lod.png) · [手机远景](standalone/viewer-mobile-lod.png) · [浏览器及四件下载](standalone/viewer.json) · [网页输入](standalone/served-inputs.json)

从144处前一版进入同一地块，可见3111的原有体块。145处版本在同一位置载入办公主楼，街面近景可见南面五券及东侧长廊，俯视可见烟囱及西侧法院的长方形屋面采光带。远景降为62,872面。16个地面取样覆盖南廊、石墩、东侧露台、西法院与1882年住宅。近远GLB与两份城市源GLB均核对了实际下载字节。[旧地图同位](final-map/map-before.png) · [花园街面](final-map/map-street-facade.png) · [屋面](final-map/map-roof.png) · [远景](final-map/map-distant.png) · [主图与地面检验](final-map/main-browser.json) · [前一版完整报告](final-map/control-browser.json)

145处版本原默认相机采用−47°方位、48°俯角。首次从目录进入时，两端均先收到模型，街区裁切尚未就绪，原粗楼短时遮住南廊。等原生城区近景组加载完毕，原粗楼自行隐去。复核时保持目录给出的相机，手机缩放18.078，桌面18.095。南侧2007独立楼和北部1074宅邸都保留。手机原默认的选中灯牌仍盖住一段廊面。[手机首次帧](final-map/map-mobile.png) · [桌面首次帧](final-map/map-desktop.png) · [同机位手机加载后](final-map/original-default/warm-mobile.png) · [同机位桌面加载后](final-map/original-default/warm-desktop.png) · [两端加载状态、近源组和选中模型收据](final-map/original-default/warmed-browser.json)

在相同145个入口、相同模型与原有建筑的独立取景对照中，焦点改为南侧券廊与东角。方位和俯角沿用−47°及48°，实际手机缩放19.328、桌面19.501。两端的楼下五个券洞和上层栏廊从左到右均可辨认，选中灯牌落在屋顶。按四张实图各自的相机回射，原手机可见南廊中的217个底层模型表面点，局部取景下为225个，各点到眼睛之间均通畅。原视角下南侧2007遮住中央廊以外的少量表面，手机60个取样、桌面2个。该对照在浏览器中单独替换了候选目录响应，正式站实测按各自版本记录。[手机局部取景](final-map/focus-comparison/focus-mobile.png) · [桌面局部取景](final-map/focus-comparison/focus-desktop.png) · [对照浏览器收据](final-map/focus-comparison/warmed-browser.json) · [四机位首碰计数](final-map/focus-comparison/sightlines.json)

前一版本144处地图的第100至102项已有固定提交下的20个文件下载核验，共14,394,966字节，全部匹配SHA256。[144处版本的公开下载收据](predecessor-public-downloads-144.json)

南廊局部取景已纳入正式145处目录。登记了19.35的缩放值及覆盖南廊主体的取景边界；逐行比对确认其余144个地点以及办公楼的模型、所有者、裁剪、碰撞和步行参数保持一致。正式浏览器输入共582项，包括重新计算的放置几何签名与源检查程序。原始取景的合同和检查程序保存在同一审计下。[变更字段与前后取景依据](south-arcade-framing-revision.json) · [本版实际HTTP核验](consulate-south-arcade-http.json) · [生产文件比对](production-inputs.json) · [相邻来源及前版登记](catalog-preservation.json)

正式南廊焦点接入后的项目测试通过417项Node及20项Python检查，另复核第100和101项的8件已公开实图与收据，共1,922,228字节。[项目回归](project-regressions.json) · [前序实图复核](preceding-viewer-evidence.json)

正式145处目录采用南廊局部取景后，从地标卡实际进入，手机和桌面均收到完整的134,672面模型及3111的近景裁切，南面上下两层五间廊完整可见。两端默认图与独立取景试验逐字节相同。随后核对了花园侧街面、屋面、62,872面远景、16个地面点及6件下载；浏览器无错误。前后对照沿用同一144处旧版控制。[正式手机默认](final-map/accepted/map-mobile.png) · [正式桌面默认](final-map/accepted/map-desktop.png) · [街面](final-map/accepted/map-street-facade.png) · [屋面](final-map/accepted/map-roof.png) · [远景](final-map/accepted/map-distant.png) · [完整实机报告](final-map/accepted/main-browser.json) · [正式网页输入](final-map/accepted/accepted-verified-inputs.json) · [144处父版同位](final-map/map-before.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/1a8e3da5b74acf2b4ad5b07ec25e38284161899b/projects/shanghai/index.html#landmark=huangpu-former-british-consulate&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 11 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
