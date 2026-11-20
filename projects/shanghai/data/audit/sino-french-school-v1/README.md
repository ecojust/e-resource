# 光明中学教学楼（原中法学堂）

淮海东路70号是光明中学的校址。操场北侧的三层教学楼由西段和东翼组成，西端面向西藏南路。校方的2009年校史记载，1886年创办的法文书馆于1911年改名中法学堂。1913年学校迁入新址，先建的西段已达三层。1923年7月向东扩建，此后形成三翼面向操场的山字形平面。市房管局第二批名录以2A054登记此处。[校史、建筑年代及影像](../../../source/precise/huangpu-sino-french-school-teaching-building/reference-review.json) · [院内位置与西端街面](../../../source/precise/huangpu-sino-french-school-teaching-building/README.md)

从操场可见两段后退的五开间外廊，中央翼较宽，两侧各有两列窗，正中三开间形成外廊。2024年近照显示曲线形匾额上的校名从右向左书写，上有五颗星。西端墙成对的竖窗和中央入口取自早期街照。外轮廓以约84.9米的面宽对齐三期影像。最高点15.75米、各层层高、开廊的2.52米进深和屋面设备房尺寸均为估计。模型表现外墙、门窗和可以看入的外廊，教室内部资料有限。[历史全景照](https://www.virtualshanghai.net/Photos/Images?ID=1367) · [西端墙照片](https://www.virtualshanghai.net/Photos/Images?ID=1601) · [近年匾额与门廊](https://news.qq.com/rain/a/20240705A00UDX00) · [模型源码](../../../source/precise/huangpu-sino-french-school-teaching-building/source/school_geometry.py)

原始GLB与网页近景均有182,492个三角面，远景有61,040个。重新打开Blender文件后核对168个可编辑网格和八种材质。三份实际交付的GLB各通过141条射线检查，共423项。检查点涵盖外廊后墙、门窗玻璃、框料、曲匾、屋面和建筑外的空处。完整模型保留的一道细窗横档在远景中简化，分别验证横档和在同一高度可见的玻璃。[原生重开及导出](geometry-native.json) · [三档实测](surface-checks.json) · [原生总览](huangpu-sino-french-school-teaching-building-preview.png)

独立页在1250×820的桌面与390×844的手机上实际加载两档模型。手机全楼居中，触点命中“操场一侧的外廊”，两次触屏操作都收到了浏览器的真实点击事件。在桌面逐项下载了原始GLB、压缩近景、远景及Blender文件，并与清单逐字节核对。首轮手机自动化在等待控件动画帧时超时，另一次冷启动核实了真实触点、页面和两档模型的HTTP内容。[独立预览](../../../sino-french-school.html) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [手机远景](viewer-mobile-lod.png) · [下载与截图记录](viewer.json) · [首次运行](viewer-desktop-phase.json) · [触屏复测](mobile-viewer.json)

用重新打开的原生文件另取两张局部图。正面总览将整栋长立面收入画面，近平视的取景会压缩外廊的视觉深度。斜向的操场视角可以读到各层楼板、拱窗与前后柱列，西端图则可数出五开间以及成对的窄窗。[操场外廊近景](courtyard-gallery.png) · [西藏南路端墙](west-street-end.png) · [逐图复核](native-visual-review.json)

地图只替换宏块14-13720-6694的1709号教学楼。现行OSM轮廓、院门和操场位置、近三期影像共同确定建筑外轮廓。核验9,826个近景旧面和48个远景旧面均在裁剪边界内，同组60,120个近景邻面和52个远景邻面全部位于边界外侧，最近相距8.16米。地面碰撞使用实际GLB从铺地以上至两米高度的投影，并在离地11.9厘米处取实体切片保留砖墩。两侧各五开间、中央三开间的13处开口各取三个深度验证，10个独立砖墩和廊后教室仍有碰撞。合计69个见证点。步行边界合并了窗台、砖饰边缘的狭小凹口，合并后各处距实体至多20厘米。[冻结外圈、保留楼和照片方位](../../../source/precise/huangpu-sino-french-school-teaching-building/footprint-review.json) · [近远景和69个地面点](placement-geometry.json) · [落位和行走边界](final-placement-contract.json)

教学楼加入后全城目录共171处。运行期检查逐点核实三段外廊和教室碰撞，教学楼新增11个裁剪三角面，全城926面分布在16个宏块，单块最多316面。833个登记输入共804,859,243字节，逐项比对SHA-256通过。[运行期验证](runtime-placement.json) · [171处输入清单](production-snapshot.json)

24132原图和24133校舍加入后的实图在同一操场机位对照。390像素手机和870像素桌面均保留首次画面及城市近块就绪后的画面。操场近景可见两段退廊、正中三开间的栏杆、后墙及上方金字曲匾；从西藏南路看，五开间的顶层券窗清晰，地图牌遮住底层中央入口的一部分。街区远景实际使用61,040面，近景为182,492面。两代合计十张实图，实测72处地面与邻楼点位。后态从本站取得四种模型及近远城市底模共六份文件，独立页已保存的四次下载也与正式站逐字节一致。完整复测无失败请求、地图警告或WebGL错误，843份正式输入的实取总量为804,960,679字节。首轮前态页面因系统内存不足崩溃，释放空间后以相同机位重测并保留原记录。[十张实图与逐图观察](city-24133/visual-review.json) · [原城市底模](city-24133/map-before.png) · [操场廊柱和曲匾](city-24133/map-courtyard-gallery.png) · [西藏南路端墙](city-24133/map-west-street-end.png) · [正式地面与近远档](city-24133/main-browser.json) · [四项下载对照](city-24133/individual-downloads-rebound.json) · [完整签名实取](city-24133/133-all-http.json) · [首轮中断](city-24133/initial-control-failure.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/0f89d92aac992b04e112393a4116231ad7cc03c5/projects/shanghai/index.html#landmark=huangpu-sino-french-school-teaching-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 9 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
