# 慈修庵正院北殿与两厢木廊

榛岭街15号的正院保有三间北殿和两翼木廊。1994年市政府设置的铭牌与门牌可在同一张实地照片中辨认；保护名录的2A056（原2E001）写作“秦岭街15号”。1917年火灾后的重建、1980年代修葺和后来安装的玻璃院顶分别列入来源记录。2019年现场影像可见院内钢架、格子门、宝瓶栏杆和“大雄寶殿”横匾。2001年置换的方浜中路593号另院及黄色街门保持独立。[来源与公开照片](../../../source/precise/huangpu-cixiu-nunnery-courtyard/reference-review.json) · [文字说明](../../../source/precise/huangpu-cixiu-nunnery-courtyard/README.md)

具名OSM建筑w494395699@2与冻结宏块14-13720-6694的448号建筑重合约97.9%。制作时以北殿的面院门槛作为原点，横向沿屋面长边朝东偏北，面向院内约162°。对照2022、2024和2026三个发布日期的航片，采用早两期可辨的北侧屋面、两翼与院内浅色顶盖以及2019年实景作为外观依据。2026年版周边已有施工，不能确定最新院顶内部构造。百度南门标记距具名庵屋最近约58米。[源登记、局部范围及邻房](../../../source/precise/huangpu-cixiu-nunnery-courtyard/footprint-review.json)

网页模型中的玻璃材料名为 `later translucent courtyard glazing`，采用20%不透明度。原生版本独立保存钢架与玻璃，并使用同样的不透明度，避免通过材质排序或删除顶棚来显示木廊。[几何源文件](../../../source/precise/huangpu-cixiu-nunnery-courtyard/source/courtyard_geometry.py) · [原生材质与相机](../../../source/precise/huangpu-cixiu-nunnery-courtyard/source/make_native_courtyard.py)

原始模型和网页近景各有29,110个三角面，远景有19,042个。用Blender 4.3.2重新打开原生文件后，67个可编辑网格、9种材质的三角面与原始交付件逐一对应。玻璃在原生材质和浏览器近、远档中的不透明度均为0.20。桌面和390像素手机实点三个视角，俯视可透过玻璃辨认红色木廊、天井铺地和钢架投影。原生渲染左廊阴影较深。四个下载按钮取得的文件均已核对大小和SHA-256。[原生实图](huangpu-cixiu-nunnery-courtyard-preview.png) · [网页正面](viewer-desktop-full-front.png) · [网页俯瞰](viewer-desktop-full-above.png) · [手机俯瞰](viewer-mobile-full-above.png) · [渲染比较](native-web-visual-review.json) · [六张图与下载记录](viewer.json) · [四个交付文件](../../../assets/models/candidates/huangpu-cixiu-nunnery-courtyard/manifest.json)

原始、网页近景与远景模型各通过101项表面和空隙检查，覆盖廊柱之间的通路、楼上木栏的空处、北殿格扇、匾额及院顶。将三份模型放回相同的城市场景坐标后，核对44个地面样点，其中31处可通行，13处有柱、墙或其他建筑实体。模型投影214.40平方米，地面碰撞93.82平方米。对448号原地块局部裁剪后，近、远源网格分别保留57.78%和57.65%的投影面积，补上两段高6.4米的截面。与同一绘制组中其他近景网格的最近距离为5.63米。[303项射线](surface-checks.json) · [逐栋网格与44处地面检查](placement-geometry.json) · [落位、裁剪及补面](final-placement-contract.json)

这栋建筑使全市入口从181处增至182处。初次登记沿用的显示程序在黄浦区宏块已有320个裁剪三角面，慈修庵局部的两个三角面将其增至322个，旧版在加载全目录时抛出“候选模型局部边界过于复杂”。同一渲染器按原建筑逐项复算可重现320+2。原始182快照与分页显示修订分别保存，以便核对修复前后的结果。[原始182处的941项签名](production-snapshot.json) · [旧版渲染的复现](unpaged-runtime-182.json)

22145版将裁剪数据分配到可独立读取的纹理页，保留448号所在宏块的全部322个三角面。949份HTTP输入的实收字节数为930,050,563。用分页运行时复查整城后，慈修庵及邻房共47个地面样点、8项矢量检查通过；额外以网页真实近、远模型复查显示、深度、距离和阴影。[182处完整裁剪复核](paged-runtime-182.json) · [模型与邻房落位](runtime-placement.json) · [实际阴影与像素](paged-shadow-check.json)

### 市中心高密度分区

慈修庵接入后，分区 `14-13720-6694` 的裁剪三角面从 320 个增至 322 个。第 144 项和第 145 项的实际目录可以复现旧渲染器拒绝更新的情况。新渲染器将超过一页的分区按源建筑编号排序，把远景面的编号定位到连续的纹理记录。此分区的单个建筑最多检查 24 个裁剪面。没有逐顶点编号的近景，沿用底图瓦片公布的建筑成员表。慈修庵所在近景瓦片只接收属于 448 号源的两个裁剪面。

用原近、远瓦片的三角面实测，448 号楼在替换区内的旧屋面和投影一同消失，同楼其余屋顶和邻楼 30 的阴影保留。四组真实阴影纹理分别取自两个细节级别的方向光深度图和点光源立方投影图集。另用第 323、324 条记录检查了分页末尾，在有源编号的远景和无逐顶点编号的近景均能命中。[前后目录与旧版复现](renderer-legacy-reproduction.json) · [原始网格、颜色与阴影像素](native-shadow-atlases.json) · [整城裁剪、矢量和地面](renderer-runtime-placement.json) · [实际发布文件与 SHA-256](renderer-release-http.json)

## 正式全城地图实测

24144版登记前，同机位显示448号旧建筑的连续屋面。24145版从1280×800桌面目录和独立390×844手机目录进入，院内可见红木两厢、透光顶棚和北殿的上层窗栏。较高的保留楼体遮住了从街面看向北殿的部分底层。在院中可通行处取景，镜头对准北殿后，能辨右起“大雄寶殿”四字、横枋和下方格扇。近图中横梁遮住字的上缘，棚架的影子斜过字面。最初的廊道镜头只拍到近处瓦面，原图也一并保留。[登记前同镜位](city-24145/before/map-before.png) · [桌面全院](city-24145/desktop/map-desktop.png) · [手机触控放大](city-24145/phone/map-mobile-zoom.png) · [北殿正面](city-24145/inside-court/central-north-hall.png) · [从东厢看北殿](city-24145/inside-court/east-gallery-to-hall.png) · [逐图判读](city-24145/city-visual-review.json)

正式场景含182个目录入口，前后两版签入的输入分别为943和954项。北殿所在的原建筑448号保有两段截面，地面47处和矢量8项检查均通过。分页渲染保留该宏块全部322个裁剪三角面，远近两档的颜色、深度与阴影均在真实浏览器中复核。首次补拍时有一份相邻建筑文件返回502。按固定Git对象恢复后，两站都重新下载到相同的76,849字节，重新进入院内的全过程无HTTP或WebGL错误。[真实地图与碰撞检查](city-24145/desktop/main-browser.json) · [分页与截面](city-24145/paged-runtime.json) · [实际阴影](city-24145/paged-real-shadows.json) · [相邻文件恢复](city-24145/source-recovery/restored-http.json) · [院内复拍与相机](city-24145/inside-court/inside-court.json) · [独立页六图与四个下载](city-24145/viewer/viewer.json)

GitHub 固定提交的地图入口、运行模块、来源和四种下载等 39 个公开文件均实际返回 HTTP 200，字节数及 SHA-256 均与 Git 对应文件相同。 本次固定提交在第三方地图预览服务的入口响应为 500。主图交互依据本页所列的同版本浏览器实测。[GitHub 版本目录](https://github.com/ecojust/e-resource/tree/d1968852e369491d4bb4a6591fb8947097c0586a/projects/shanghai) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项，10 项返回其他版本的内容，11 项未返回 HTTP 200。[首次 master 核验](publication-master-initial.json)

随后复查，第三方预览的地图入口已正常返回 HTML。固定版本的 39 个文件及地图实际引用的模块链均与 Git 对应字节一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/d1968852e369491d4bb4a6591fb8947097c0586a/projects/shanghai/index.html#landmark=huangpu-cixiu-nunnery-courtyard&mode=overview) · [预览复查](public-preview-recheck.json)
