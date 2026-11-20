# 景灵堂昆山路北门山墙与修复花窗

模型采用2025年修缮验收后的昆山路135号北立面。验收报告公布的主窗高10.56米、宽5.44米。2017年街照中横贯窗洞的题字匾和六格旧窗属于修前状态。最终工程呈现三片红砖山墙、中央六列玻璃窗、十二瓣玫瑰、两枚侧花、门廊的十一处三叶拱饰及花岗岩台阶。玻璃水纹与人物用原创网格近似，近景保留铅条与色块的独立材质。[来源和两个年代的照片](../../../source/precise/hongkou-jingling-church-north-front/README.md) · [原尺寸与照片对照](elevation-photo-comparison.json) · [最终渲染](hongkou-jingling-church-north-front-preview.png) · [图像复核](visual-review.json)

Blender 4.3.2重开原生文件后测得75个网格、15种材质和73,848个三角面。网页近景保留73,848面，远景46,704面。三个版本分别通过113条射线检查，涵盖玫瑰花瓣和圆花、玻璃与铅条、三叶拱饰、圆窗、门框、台阶与山墙。独立页、脚本、清单和四种模型文件均已通过HTTP字节签名检查。[独立模型](../../../jingling-church-north-front.html) · [下载清单](../../../assets/models/candidates/hongkou-jingling-church-north-front/manifest.json) · [逐档射线结果](surface-checks.json) · [原生工程及压缩核验](geometry-native.json) · [网页与下载签名](standalone-http.json)

地图仅替换地块2766临昆山路的门面，保留主堂近景投影面积94.78%、远景94.99%，两个级别在原墙交界各填补一处截面。人行道和两侧阶前空地可通行。正门、石阶和墙体的模型碰撞范围合计47.19平方米。最近的独立几何组与裁切边线至少相隔6.61米。预设镜头朝170°、俯仰31°，在900×650及390×844窗口分别复算九处地物，门、窗、十字顶等九点均在可视图面且未与周边既有体量相交。[地块核对](../../../source/precise/hongkou-jingling-church-north-front/footprint-review.json) · [近远景及地面核对](placement-geometry.json) · [相机视线](overview-sightlines.json) · [地图放置](final-placement-contract.json) · [进入地图](../../../index.html#landmark=hongkou-jingling-church-north-front&mode=overview)

本次地图从178项增加至179项。917个冻结文件通过HTTP传输，共914,472,835字节。运行时裁剪表为全城956个三角、19张宏区纹理，单表最多318个三角。两种矢量源均保留原主堂剩余部分。[登记增量](inventory-increment.json) · [生产签名](production-snapshot.json) · [实际传输](frozen-http-summary.json) · [运行时核验](runtime-placement.json)

在正式独立页上，1250×820桌面和390×844手机分别切换了近景和远景。四幅画面均可辨认三片山墙、中央尖拱窗、窗下门廊和台阶。四个下载按钮实际保存了原始GLB、网页近景、网页远景及可编辑Blender文件，字节摘要与清单一致。[四次保存和视图签名](viewer.json) · [桌面近景](viewer-desktop-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png)


## 正式城市图中的北立面

在24141和24142的同一街面机位，登记前可见原城市体量，登记后可以辨认中央尖拱花窗与两旁红砖山墙。390×844手机从地点目录进入，九个检查点都在屏内，灯牌和面板没有遮住它们。点一次加号后可细看中央花窗与门廊，东侧小圆窗超出右侧边界。870×660桌面展开目录时，本楼灯牌与台阶底部的一个检查点重叠，另八点可见。主动切换到正面近景后，底部地点卡覆盖同一台阶点。独立页保留了台阶的完整正视图。[前版同机位](final-map-24142/map-before.png) · [手机默认](final-map-24142/map-mobile-same-camera.png) · [手机放大](final-map-24142/map-mobile-public-zoom.png) · [桌面默认](final-map-24142/map-desktop-same-camera.png) · [街面近景](final-map-24142/map-street-facade.png) · [斜上方](final-map-24142/map-roof.png)

用键盘搜索怀恩堂后，景灵堂的模型和局部裁切随视点卸载。再从目录搜索景灵堂，恢复同一立面，远景切换至对应低细节模型。灰色屋面属于保留的原主堂。现场读取3,550个矢量建筑要素，人行道、门前台阶、原主堂和四处独立邻楼的15个检查点均符合预期。两版城市目录从178处增加到179处，原有138条候选模型记录逐字段相同。24142实际读取927个签名输入，共914,574,271字节。两次浏览器运行均无页面错误或失败请求。[返回景灵堂](final-map-24142/map-returned.png) · [远景](final-map-24142/map-distant.png) · [城市实测与15处地面](final-map-24142/main-browser.json) · [两个版本的文件及下载](final-map-24142/pair-and-standalone-http.json) · [927项实取](final-map-24142/142-all-http.json)
