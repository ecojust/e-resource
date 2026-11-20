# 尚贤坊淮海中路主弄门楼

上海黄浦2022年发布的正面照片中，中央开间上层两扇小窗分列三字牌匾两侧，下层中央长窗和两扇窄窗位于穿楼弄道之上。模型保留这五组窗的实体洞口、红砖错缝、双侧石质壁柱、方尖碑、涡纹和分层曲线檐口。栅门的两扇侧屏向内退，中央可通行。[照片与分期](../../../source/precise/huangpu-shangxianfang-gate/reference-review.json) · [原生模型正面](huangpu-shangxianfang-gate-preview.png) · [门匾及窗](tablet-and-gable.png) · [弄道与铁栅](passage.png) · [模型与四种下载](../../../shangxianfang-gate.html)

近景59,336面，远景9,188面。三份实际GLB逐一检查中央开口、铁栅、墙体遮挡、檐下净空与凹窗，各37个见证，共111项。首稿的屋面前檐恰好穿入顶层的两处玻璃；正式版抬高临街檐线，两侧窗的首个玻璃交点均回到墙后0.374米。61个原生编辑件经Blender重开，逐面核对原模型。[首稿试验](preflight/first-roof-intersection.json) · [首稿外观](preflight/first-elevation.png) · [最终几何、射线与落位](placement-geometry.json) · [可编辑件及压缩复核](geometry-native.json)

保护地块的南侧长边和正射影像的主弄轴线用于估计门前位置。近档城市网格58,646面及远档76面中，距离模型包围范围最近的三角形分别至少相距4.75和4.82米。现有矢量楼面也保有间隔。地面碰撞约18.33平方米，穿过两列栅门的中线距最近障碍外缘0.703米，经过约11.7米深的整排门楼可抵后部巷道。[地理坐标与误差](../../../source/precise/huangpu-shangxianfang-gate/footprint-review.json) · [正式落位合同](final-placement-contract.json)

真实108处站点的独立页可以在手机与桌面切换近远模型。红砖山墙、五组窗与中央门道在两档均可辨，四种下载响应与正式文件逐一核对。[桌面近档](viewer-desktop-full.png) · [桌面远档](viewer-desktop-lod.png) · [手机近档](viewer-mobile-full.png) · [手机远档](viewer-mobile-lod.png) · [下载记录](viewer.json) · [原生近照目视](native-visual-review.json)

独立页的正面按钮显示「淮海中路立面」。桌面和390像素手机实点真实按钮，近远景各留一图，同次请求验证全部四个下载的长度与SHA-256。[桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [浏览器操作与下载](viewer.json) · [修正前的按钮记录](preflight/front-view-label.json)


## 主图视角与真实步行

最初的默认镜头取333.21796°、俯仰61°。刚加载门楼时能看见正面。等街对面2357的原生近景瓦片到场，桌面和手机上都只露出一条砖边。另设333.21796°、64°俯仰的街面镜头同样受挡。改为300°、61°后，牌匾、红砖立面、屋顶和中门在两端都可辨，街对面的2357、2541及门楼东侧的2597继续随真实城市图层显示。方向试验目录与含新落位签名的正式目录具有相同的108行模型。[原、新暖态及冷启动对照](preflight/camera-directions/readout.json) · [周围建筑与视线平面位置](camera-footprint-comparison.json)

在原始108处站点的第三人称模式实际按住Shift与W，角色从临街南侧走过中门，沿门廊一直到内院。起终点局部纵坐标为−3.10和13.03米。958次轮询包含39个不同位置，全程16.13米，中心未碰撞。另从门内向两边分别真实按A、D，原生控制器停止在横向−2.40和+2.40米，并都显示建筑阻挡提示。320×418小窗里，操作面板覆盖了较多内部画面。[逐位置通行记录](walking-course.json) · [进门时](map-walk-inside.png) · [抵达内院](map-walk-courtyard.png) · [两个方向的真实碰撞](wall-controller.json) · [原版主图与四个下载](main-browser-before-camera.json)


正式108处目录SHA-256以 `1c5b659a` 开头。手机和桌面从名录实际进入后，分别拍摄到站和近源就绪两态。两端均可点选门楼灯牌，最终暖态仍显示原生2357、2541、2597。街面近看时，灯牌会遮到部分上层砖饰，完整街景请同时参照手机默认镜头。正式近档59,336面，远档9,188面；四个模型下载和两份原生远近源均校验长度或哈希。真实107处前态没有门楼，原邻楼仍在相同街面位置。[手机默认暖态](registered-mobile-with-neighbors.png) · [桌面默认暖态](registered-desktop-with-neighbors.png) · [街面近看](registered-desktop-street.png) · [正式远景](registered-desktop-distant.png) · [107处对照](map-before.png) · [正式浏览器与四下载](main-browser.json) · [前态实测](control-browser.json) · [主树与冻结输入](primary-map-inputs.json)

320×568全市视图下，长建筑名会压缩编号的可用高度。原108处页面测得3个回退、6对牌面重叠，972个采样点中27个命中错误；实点外滩9号的一处牌面落入了金山卫瓮城。保持同一108处登记的修复试验页改用19×15及25×15像素的编号，972个采样点全部正确，108张牌分别落位，实触108号进入尚贤坊。图标模块与运行时发布版本分别记录。[原版实际截图](compact-capacity/registered/map-108-markers.png) · [修复试验截图](compact-capacity/repaired/map-108-markers.png) · [输入、几何、实触及像素对照](compact-capacity/comparison.json) · [先前超时记录](preflight/compact-grid-timeout/compact-browser.json)

此次调镜头涉及尚贤坊一处。其余67处可拟合镜头的建筑，在三种窗口尺寸下共201组取景参数均与原版一致。[两份目录的逐文件差异](camera-input-revision/input-difference.json) · [各建筑的实际镜头参数](camera-input-revision/camera-arguments.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/0a1aeb1e2b658fd02b93c30fd563570a4e88c005/projects/shanghai/index.html#landmark=huangpu-shangxianfang-gate&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
