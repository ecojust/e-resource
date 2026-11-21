# 陈炳谦宅历史正立面核验

陕西北路80号第二批名录2B012*的双塔住宅约于1994年灭失。模型据2014年刊载的历史照片辨认出两座折坡角塔、上下各八跨的券廊、向后退入的窗面和花木上方一段低矮轮廓。照片拍摄年代未详。引用1948年航片用于区别园内诸楼。房管局第五批登记的5B032教研楼，以及现状地块上的其他建筑均保留。[照片及房管局两张名录的逐项核对](../../../source/precise/jingan-chen-bingqian-historic-residence/reference-review.json)

历史地点沿陕西北路80号的街区落点打开独立单体。该点为现址级线索，未以现存园内建筑轮廓推断原宅平面。地图合同保留空的建筑和部件来源列表、地面碰撞与替换边界。原照片和航片未写入模型纹理。[原址合同](final-placement-contract.json) · [历史状态复核程序](check-marker.mjs)

独立几何检查读取发布的原始网格并解码网页近远两档，逐项对照十六券后的窗面、跨间立柱、腰线和女儿墙、塔窗、折坡与低矮轮廓的前后关系。原生工程的重开校验另核对顶点、面片方向与材质归属。[几何探测结果](surface-checks.json) · [原生与网页网格校验](geometry-native.json)

Blender 工程重开后保有57个可编辑网格。原始和网页近景各34,956个三角面，远景为12,324个。三档分别通过63项表面和进深检查，共189项。桌面1250×820和手机390×844分别从独立页面切换到近、远两档，四幅实际画面均能完整看到双塔和两层券廊。桌面通过页面保存原始GLB、网页GLB、远景GLB及Blender工程，长度和摘要均符合清单。[桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [四图四件实测](viewer.json)

最终两期城市地点共254处和255处。前一期的214条候选记录逐项保留，新增陈炳谦宅的原址标记。实际网页的状态合并器返回零个场景模型、零个裁剪面和零个碰撞体，地点卡将1994年的名录登记、约1994年的灭失记录、2014年的旧照刊载分开显示。十一期技术视图均从各自的网页入口逐级实取12个资源，核对缓存键、两处间接引用和旧照片日期处理。最终站逐件实取1,550个签名输入，共1,307,992,796字节。[历史原址最终状态](final-marker-status.json) · [前后两期实际输入](final-marker-inputs.json) · [最终缓存链](http-cache-chain/cache-chain-26218.json) · [全站逐件回执](final-26218-http.json)

## 正式地图入口与历史影像

前一站的目录有254处。加入陕西北路80号陈炳谦宅后，目录有255处。两站以同一方位看登记点，底图上的现存建筑保持原貌。登记点可以定位，地面可通过，周围七栋建筑仍各自阻挡通行。新条目注明1994年名录登记、原建筑约1994年灭失，历史立面从地点卡片打开。[同机位前态](before/before-same-overview.png) · [触屏定位](phone/mobile-location.png) · [桌面定位](desktop/desktop-location.png)

在390×844的触屏和780×465的桌面逐一打开模型、切换远近并返回原地点。两端的查看器均注明照片于2014年刊载、拍摄年份未详。图中双塔分立两端，中央两层券廊、正面台阶、坡屋顶和中央三角形山花均可辨认。近景34,956面，远景12,324面。砖墙、浅色券边和屋面颜色为复原估计。[桌面近景](desktop/desktop-archive-near.png) · [桌面远景](desktop/desktop-archive-lod.png) · [触屏近景](phone/mobile-archive-near.png) · [触屏远景](phone/mobile-archive-lod.png)

桌面实测时，缩放按钮与历史入口中央局部重叠。历史入口仍可在左侧用鼠标点开，实际点击位于视口坐标（688，297）。本轮桌面浏览器报告2 GiB设备内存。桌面分别保存原始GLB、网页近景、远景和可编辑Blender文件，四件与独立页同名文件逐字相同。两个界面关闭历史立面后都回到登记点，七栋周邻的碰撞保持一致。[实际操作与四件下载](desktop/after.json)

[前后两站、触屏和桌面的实际记录](final-map-31218/results.json) · [街区及七栋现存建筑](final-map-31218/existing-city-geometry.json) · [桌面近景](final-map-31218/desktop/desktop-archive-near.png) · [手机远景](final-map-31218/phone/mobile-archive-lod.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/3d9681c52beba0a1753087e0674b87b35014efc6/projects/shanghai/index.html#landmark=jingan-chen-bingqian-historic-residence&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，15 项返回其他版本的内容，0 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)
