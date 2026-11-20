# 泰安路115弄6号周谷城旧居庭院立面模型核对

2026年11月20日核对2014庭院入口立面的原创模型。原始与近景 GLB 各 12,840 个三角面，远景 6,480 个。Blender 4.3.2 重开原生文件，按11种材质逐面比对68个可编辑网格。两档压缩模型分别解码，并与各自原始几何按面方向和材质比对。[模型文件清单](../../../assets/models/candidates/changning-zhou-gucheng-courtyard/manifest.json) · [几何及原生文件对照](geometry-native.json) · [原生预览](changning-zhou-gucheng-courtyard-preview.png) · [实照与成品对照](visual-review.json)

单体网页在桌面与手机均实载近、远两档，并逐字节复核四个下载文件。两种屏幕都可看见入口、连续窗组和铁栏阳台。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [单体浏览器记录](viewer.json)

三份实际 GLB 共接受45次射线检查。门扇、两侧三联窗、中央细格长窗、筒瓦雨篷、三级门阶、悬挑板与铁栏分别命中相应材质及前后深度。被低层附屋遮挡的西端下部保留开口。[实际门窗检测](opening-rays.json)

城市底图14-13718-6695的原生677对应6号。剖切前部约两米后，近景仍留81.21%的投影，远景留81.61%。同一近景文件另有十个建筑编号，实际近、远邻几何与裁剪面均无重叠。断面按原粗模型的实有顶高校准，地面碰撞按二米以下实物单独求得，庭院入口前与西端架空处仍可通行。[源面与地理关系](../../../source/precise/changning-zhou-gucheng-courtyard/footprint-review.json) · [实际近远层检查](footprint-review.json) · [配准合同](final-placement-contract.json)

原计划157°的默认视线会穿过独立的387号前排住宅。保留该栋，在桌面、手机两种规格用北偏西的摄影站位反算，把默认方位改为174°；四个目标点的视线均避开邻楼高度包络。[相机与邻楼视线核对](overview-sightlines.json)

从上海项目目录运行。将 MACRO 指向14-13718-6695原始文件所在目录，WORK 指向新的空目录。

    python -B data/audit/zhou-gucheng-courtyard-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/zhou-gucheng/placement
    python -B data/audit/zhou-gucheng-courtyard-v1/check-openings.py --work "$WORK" --report /tmp/zhou-gucheng/opening-rays.json


### 98处主地图

桌面与手机均从长宁区目录进入第98处。北偏西的庭院立面能看见两侧窗组、筒瓦门篷和中央小阳台，选中标牌在部分近景覆盖门窗下缘。近景瓦片包含11个所有者，只对677进行两三角形裁剪，运行时建立一道源断面。斜视可同时看到22.483米估高的原生后部、保留的邻楼和浅层立面。五处地面查询、全量近景、远景切换与四个实际下载均经核对。共绑定126项同源资源与四项生成记录。[桌面](main-desktop.png) · [手机](main-mobile.png) · [临院入口](courtyard-door.png) · [小阳台](balcony-window.png) · [保留体块](retained-source.png) · [远景](distant.png) · [视觉记录](main-map-visual-review.json) · [浏览器状态](main-map-browser.json) · [请求收据](main-map-inputs.json) · [98处目录快照](production-snapshot.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 32 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/339e9b3290ef6c6b437531727b289290850ef601/projects/shanghai/index.html#landmark=changning-zhou-gucheng-courtyard&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 32 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
