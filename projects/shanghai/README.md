# 上海漫游 · Shanghai Explorer v6

上海16区三维地图与第三人称漫游项目，现有17栋独立地标（13栋外滩历史建筑、4栋陆家嘴地标）。v6首批新增外滩5号日清大楼、6号中国通商银行旧址和14号交通银行旧址，按逐栋照片建立真实窗洞、厚窗框、屋顶与立面构件，并为40扇窗的376片清晰玻璃分别加入实景采样。全市基线仍为1,708个宏块、1,796,419个普通建筑及部件要素、169,320个近景分块。**逐栋照片参照重建与普通楼的参数推定细化精度不同；全市同等精度的逐栋复原仍在继续。**

[在线预览](https://rawcdn.githack.com/ecojust/e-resource/ac388a7c598b81af3b6ac9fc79d4b63ee59a3ad4/projects/shanghai/index.html#mode=walk)（固定应用版本）。

![外滩第三人称街景](assets/previews/bund-street.png)

[下载v6启动包](downloads/shanghai-web-launcher.zip)（74.99 MB；74,988,136字节，按需联网）。解压后按包内说明启动HTTP服务。本地包含原14栋核心地标；新增3栋、远景变体、参考照片与全市分块从上述固定提交按需加载。[启动包核验](data/audit/precise-buildings-v6/release/launcher/README.md)包括实际解压后的05号与清单重置冒烟；不是重跑全部三栋或全城场景。

## v6 首批逐栋照片重建

新增三栋保留各自真实地图轮廓和地理锚点。日清大楼重建双山花、三面凸窗、门柱及分组阳台；中国通商银行重建五山墙、四圆尖塔、三拱柱廊和独立附翼；交通银行重建四排八轴窗、黑石入口、实体字牌和阶梯塔冠。照片只用于逐片选中的玻璃，避开黑框与遮挡物；墙体、窗洞、厚框及雕饰仍由几何构件形成。

三栋玻璃现位于对应窗框前脸后约**20mm**的槽内，避免玻璃脱离厚框；该深度是构造估计，不是测量值，墙洞、窗框和照片UV保持原值。HTML对明确标记的照片玻璃直接显示已捕获的光照与反射，取消重复场景受光、阴影及额外HDR；仍保留原材质颜色系数和应用统一色调映射，不把照片假装成去光照的PBR纹理，照片石墙与普通玻璃沿用原路径。

正常设备局部阴影使用4096×4096贴图、48m半范围；低内存设备使用1024×1024，并受硬件贴图上限约束。三栋楼前另新增约**844.50㎡**有界灰石铺装与3个行走支持面，顶面沿用模型0.075m基准；这是依据临街边与既有道路边界的估计范围，保留道路、水体、已有铺装、源孔洞、草床和已知建筑排除边界。[逐栋细化验收标准](data/audit/precise-buildings-v6/DETAIL_STANDARD.md)列明证据和几何要求。

三栋细模加载并可见时，分别替换相应的普通建筑源对象；卸载后恢复原表示，邻楼与全市基线计数保持不变。模型、原生预览、压缩与照片字节检查已通过，完整自动测试已通过。首批三栋已通过15组网页技术记录与10张截图的有限视觉核对；该轮采集早于后续网络／样式补丁；补丁后的实际解压启动包另通过05号与清单重置冒烟。范围见[本轮网页审计](data/audit/precise-buildings-v6/release/README.md)。

[本轮范围、来源与验证](data/bund/REALISM_V6.md) · [三栋重建源码与下载](source/bund/photo-rebuild-v6/README.md)。原10栋外滩建筑及v5城市近景、街景成果继续保留。07、09及222仍为后续候选，本版未上线。

## v5 城市近景与外滩环境（保留成果）

外滩10栋临街建筑前补齐约3,357.13m²铺装；17、18号对面的两条草床加入按2010年照片定位与估计的7棵树、支撑和近景草叶。滨江灯、道路灯及护栏按公开照片调整实体形态，地面、低路缘与街景设施加入对应的行走及镜头碰撞。沥青在中距离保留更自然的细微变化。

普通建筑近景采用家宅、公寓、工业、办公和未知五类生成实体门窗，保留源轮廓、高度依据与126处已核验屋顶。完整GeoParquet审计未发现新增真实窗门资料，因此新窗位、入口和构件尺度均保留推定标记。近景分块 **169,320** 个，合计 **9,329,009,466** 字节。全量文件与覆盖、全部远景解码、87份近景分层解码样本及126处屋顶检查均已通过，见[发布审计](data/audit/city-detail-v5/release/README.md)；[浏览器场景验收](data/audit/city-detail-v5/release/browser.json)也已通过。

![普通建筑近景的实体窗框与窗台](assets/previews/shanghai-near-v5.png)

详见[本轮范围、来源与验证](data/bund/REALISM_V5.md)、[普通建筑细化源码](source/city/detail/README.md)和[外滩街景源码](source/bund/street/README.md)。完整防汛平台高差和每栋普通楼的真实窗位尚未复原。

## 历史更新

以下记录各版本发布时的范围；“本次”“尚未”等表述对应当时状态，当前情况以顶部v6说明为准。

### v4.4 墙面、逐窗与屋顶修正

修正外滩9栋建筑近看时的墙面黑线与虚线。2、3、12、15、17、19、20、23号原先相邻墙块留下了反向重叠的内部面，部分墙面边缘也未共用节点；现将结构墙整合，保留真正的窗洞、洞口侧壁和内退。18号补连续墙芯，封住原先贯通的空缝；石材本身的接缝与凹槽继续保留。13号未发现同类问题，保持原模型。

字林西报大楼24扇主窗、汇丰大楼右翼六窗改用各自的实景玻璃采样，并按照片修正实体主窗框。字林顶部的旧开放亭纠正为厚石塔、深窗、层叠檐帽和浅弧顶冠。照片保留原字节、作者与CC0许可；不是整面墙照片平板，细格栅和帘布仍有照片细节。

华俄道胜银行同时修正十个窗帘体的面朝向，并去掉造成窗内竖向杂纹的穿插构件，保留窗洞和主窗框。

远处12、17号使用无照片的几何变体，离开区域后释放隐藏的大照片模型；正常设备局部阴影提高到2048。详见[本轮修改、来源及限制](data/bund/REALISM_V4_4.md)。本次仍是外滩局部完善，全市普通建筑尚未达到近距离真实复原精度。

### v4.3 外滩近景修正

外滩18号重新校正中央开间、柱距、窗宽及窗格比例，保留三维窗洞、独立窗框、柱和檐口。部分下部石墙与六块主窗分别映射2021年实景照片；交通灯遮挡、檐口和容易错位的区域保留几何材质，避免窗框重影。原图完整嵌入近景、远景和Blender文件，模型资产按 **CC BY-SA 4.0** 署名发布；[重建源码与照片控制点](source/bund/chartered_bank/photo-v4.3/README.md)。

17、18号前两处原来留白的凹口，依据能定位建筑和路口的2010年CC0俯视照片，按源四角补为浅种植带；新增石边、草土表面与扫描材质。玻璃增加上海沿江实拍HDR反射；它是光照素材，不是外滩原址的全景。已有照片玻璃保留拍摄时反射，避免重复染色。

[本轮范围与验证](data/bund/REALISM_V4_3.md)。此次改善仍是局部照片参照重建；主立面未见部分、树木、平台完整高差和全城普通建筑细节尚未完整复原，不能称为全市摄影测量。照片纹理也保留拍摄时的阴影，不是经过消光照处理的PBR颜色数据。

### v4.2 外滩前景铺装

外滩18号前方两处地图过街线之间，按现有道路边带和步行区边缘补充约189㎡连接铺装；这是施工边界估算，并非新发现的测绘足迹。保留两处用途不明的来源凹口及已标注内洞，不把它们推定为平整地面。现有场景仍采用统一地面高程，未复原实际台阶、坡道和滨江平台高差。

参照[滨江实景照片](source/bund/street/references/README.md)，石板调为中性灰、较宽板块和较弱接缝。1.20×0.60m板块及4mm接缝为照片比例估算；继续复用原有CC0表面纹理。建筑几何、道路、岸线和全部城市分块保持此前版本，新增几何仅为连接铺装。

### v4.1 局部屋顶补充

从已保存的179万条源要素中筛出126个可核验的屋顶：29个双坡、97个单坡，分布在嘉定3个、普陀79个、长宁27个、黄浦17个。原先平顶体块的相应部分现按原始屋型、坡高和方向生成斜屋面；总高、足迹与建筑ID保持一致，双坡采用居中对称屋脊。只重建6个分块，其余1,702个模型及其构建状态保持原字节。

[屋顶筛选与全部来源](data/roofs/README.md)、[几何核验](data/roofs/geometry-validation.json)和[分块核验](data/roofs/roof-validation.json)记录每个采用的OSM历史版本及生成假设。这里增加的是局部参数化屋顶；其余普通建筑仍以简模为主，也没有由屋顶标签推造真实窗位或照片纹理。全城逐栋真实复原尚未完成。

### v4 近景观感

[v4 表现与限制](data/bund/REALISM_V4.md)说明渲染、街道与模型切换的具体范围。本版保留 v3 的建筑几何和全市范围，改进外滩近距离观看：石材与路面使用 CC0 扫描表面纹理，细微法线与粗糙度随距离衰减；玻璃加入天空反射，附近建筑使用缓存的日光投影。外滩 2、3、17 号修复了部分构件的反向面序，保持原有顶点位置和尺寸；原始 `.blend` 和近景 GLB 没有因远景优化而降低精度。网页新增的表面效果由渲染模块应用，不包含在旧版原始 GLB 材质里。

中山东一路的路面、车道线与过街线按公开道路资料制作；漫游时不把地下隧道地图线画成地面道路。10辆静态车辆用于街景尺度示意，位置限定在公开道路范围内，不代表实时交通；排水口间距、部分线位和表面纹理尺度仍有推定。纹理是表现材料质感的通用扫描样本，不能当作这些建筑真实石种或风化分布的测量。v4初版反射使用程序天空；v4.3改用上海沿江实拍HDR并保留程序天空作为读取失败时的回退，并非外滩现场全景。详见[表面来源与许可](assets/materials/realism-v4/README.md)、[街道输入与范围](source/bund/street/README.md)。

远处外滩建筑在相机距离约400米后切换为轻量变体，回到300米内恢复完整近景模型；两套模型原子替换，加载失败保留已显示的版本。新角色与较低的跟随视角为立面留出更多画面。默认从外滩步道开始，仍可切换城市俯瞰并访问全部16区。

## 打开页面与操作

无需npm安装或构建。在本目录运行：

```sh
python -m http.server 8000
```

打开 **http://localhost:8000**。入口为[index.html](index.html)，需HTTP加载模块与GLB，不能直接用file://打开。道路、水体、中文标注及远景地图仍需联网。

- **城市俯瞰**：拖动、缩放；选择行政区或建筑，或双击地图选择上海范围内的街区起点。
- **第三人称**：WASD/方向键行走、Shift加速、拖动转向、滚轮调镜头；Q/E转动、R重置。
- **手机**：左侧摇杆、按住加速、拖动视角；支持区级跳转和面板收起。
- 支持建筑、水体碰撞和落点检查；外滩已加载街景增加铺装、低路缘、种植带和设施碰撞。地图加载后可能校正落点。完整桥面、立交和滨江平台高差尚未恢复。

## 外滩近景模型

网页使用优化后的GLB；原始GLB和Blender文件供继续编辑。所有发布文件均受 **100,000,000字节**上限检查，按建筑或城市分块保存，无需Git LFS。

| 建筑 | 可见结构重点 | GLB下载 | Blender原生文件 |
|---|---|---|---|
| 2号 · 上海总会 | 六柱柱廊、顶层拱窗与双亭 | [网页版](assets/models/bund/web/bund02.glb) · [原始GLB](assets/models/bund/bund02.glb) | [.blend](assets/native/bund/bund02.blend) |
| 3号 · 有利大楼 · 外滩3号 | 转角塔楼、双街立面与窗套 | [网页版](assets/models/bund/web/bund03.glb) · [原始GLB](assets/models/bund/bund03.glb) | [.blend](assets/native/bund/bund03.blend) |
| 5号 · 日清大楼 | 双山花、三面凸窗、门柱与112片照片玻璃 | [网页版](assets/models/bund/web/bund05.glb) · [原始GLB](assets/models/bund/bund05.glb) | [.blend](assets/native/bund/bund05.blend) |
| 6号 · 中国通商银行旧址 | 五山墙、四圆尖塔、三拱柱廊与127片照片玻璃 | [网页版](assets/models/bund/web/bund06.glb) · [原始GLB](assets/models/bund/bund06.glb) | [.blend](assets/native/bund/bund06.blend) |
| 12号 · 汇丰银行大楼 | 六柱柱廊、鼓座、穹顶与中庭 | [网页版](assets/models/bund/web/bund12.glb) · [原始GLB](assets/models/bund/bund12.glb) | [.blend](assets/native/bund/bund12.blend) |
| 13号 · 江海关大楼 | 钟塔、凹窗与源轮廓四角亭 | [网页版](assets/models/bund/web/bund13.glb) · [原始GLB](assets/models/bund/bund13.glb) | [.blend](assets/native/bund/bund13.blend) |
| 14号 · 交通银行旧址 | 八轴窗、黑石入口、阶梯塔冠与137片照片玻璃 | [网页版](assets/models/bund/web/bund14.glb) · [原始GLB](assets/models/bund/bund14.glb) | [.blend](assets/native/bund/bund14.blend) |
| 15号 · 华俄道胜银行大楼 | 柱廊、拱券与窗洞 | [网页版](assets/models/bund/web/bund15.glb) · [原始GLB](assets/models/bund/bund15.glb) | [.blend](assets/native/bund/bund15.blend) |
| 17号 · 字林西报大楼 | 窄面深进、照片窗与双侧屋顶石塔 | [网页版](assets/models/bund/web/bund17.glb) · [原始GLB](assets/models/bund/bund17.glb) | [.blend](assets/native/bund/bund17.blend) |
| 18号 · 麦加利银行 · 外滩18号 | 爱奥尼柱廊、山花与栏杆 | [网页版](assets/models/bund/web/bund18.glb) · [原始GLB](assets/models/bund/bund18.glb) | [.blend](assets/native/bund/bund18.blend) |
| 19号 · 和平饭店南楼 · 汇中饭店 | 红砖壁柱、山花与角亭 | [网页版](assets/models/bund/web/bund19.glb) · [原始GLB](assets/models/bund/bund19.glb) | [.blend](assets/native/bund/bund19.blend) |
| 20号 · 和平饭店北楼 · 沙逊大厦 | 装饰艺术窗带、退台与铜屋顶 | [网页版](assets/models/bund/web/bund20.glb) · [原始GLB](assets/models/bund/bund20.glb) | [.blend](assets/native/bund/bund20.blend) |
| 23号 · 中国银行大楼 | 主楼、后接西翼与中式屋檐 | [网页版](assets/models/bund/web/bund23.glb) · [原始GLB](assets/models/bund/bund23.glb) | [.blend](assets/native/bund/bund23.blend) |

[外滩源码与逐栋资料](source/bund/README.md)说明每栋的生成入口、参考照片、尺寸依据与推定部分；[外滩资产清单](data/bund/manifest.json)记录地理原点、模型链接、包围高度和照片署名。细部可查看[汇丰柱廊](assets/previews/bund/hsbc-column-detail.png)、[麦加利柱廊](assets/previews/bund/chartered-column-detail.png)、[海关窗洞](assets/previews/bund/customs-window-detail.png)。

这里的建筑细节是照片参照下的几何重建，**不是测绘、激光扫描或摄影测量成果**。窗洞具有实际退距，柱、窗框、栏杆等采用几何构件；雕刻纹样有简化。不可见侧后立面、墙厚、洞深和部分楼层高度含推定，未重建可游览室内。海关总高约79.2m有官方文字依据；其余建筑的总高或屋顶附属部分需结合逐栋说明判断，不能把清单中的小数视为实测精度。模型包围高度可能包含旗杆、灯亭或尖顶，不等于主檐口高度。

## 陆家嘴与全市建筑

| 地标 | 公开总高 | GLB下载 | Blender原生文件 |
|---|---:|---|---|
| 上海中心大厦 | 632 m | [网页版](assets/models/optimized/shanghai-tower.glb) · [原始GLB](assets/models/shanghai-tower.glb) | [四地标合并场景](assets/native/shanghai-landmarks.blend) |
| 东方明珠电视塔 | 468 m | [网页版](assets/models/optimized/oriental-pearl.glb) · [原始GLB](assets/models/oriental-pearl.glb) | [四地标合并场景](assets/native/shanghai-landmarks.blend) |
| 上海环球金融中心 | 492 m | [网页版](assets/models/optimized/swfc.glb) · [原始GLB](assets/models/swfc.glb) | [四地标合并场景](assets/native/shanghai-landmarks.blend) |
| 金茂大厦 | 420.5 m | [网页版](assets/models/optimized/jin-mao.glb) · [原始GLB](assets/models/jin-mao.glb) | [四地标合并场景](assets/native/shanghai-landmarks.blend) |

陆家嘴四栋复原球体、扭转塔身、环球金融中心顶部通孔及金茂退台等可辨识造型；与外滩逐栋近景模型的细化范围不同。[高度与坐标来源](data/audit/poi-sources.json)保留官方或可靠公开资料。

16区覆盖黄浦、徐汇、长宁、静安、普陀、虹口、杨浦、闵行、宝山、嘉定、浦东新区、金山、松江、青浦、奉贤、崇明。[全域分块清单](assets/city/README.md)与[机器清单](assets/city/manifest.json)提供下载和地理定位信息；每块具有独立经纬度原点与米制坐标。assets/districts/仅保留旧版每区1km²样本，当前HTML使用全域分块。

普通建筑近景的门窗具有实体厚度与退距，窗位、开间和多数材料仍由参数推定；远景保留较轻的建筑表示。道路宽度优先公开width/lanes字段，否则按等级估算。全域公开源仍可能漏楼、错分轮廓或具有年代差异；“全域”指本次来源范围内的处理覆盖。v5近景覆盖见上方保留记录；v6新增三栋采用动态精确替换，不改变该基线统计。

## 数据依据与版本变化

- **全域来源**：Overture 2026-10-21.0。v2核验检查2,892个相交z14格，其中1,734个有源瓦片；下载/解码失败及全局重复UUID均为0。保留1,796,667个唯一地上建筑/部件，地下11个另行记录。[轮廓快照](data/fullcity-raw/manifest.json)支持离线重建。
- **行政边界**：OSM的16区几何有效，45个检查点通过，覆盖崇明、长兴、横沙、机场、临港及外围区域。河海行政水域面积不等于官方6,340.5km²陆域面积。[地理审计](data/audit/ACCURACY.md)保留政府资料对照和边界处理说明。
- **父体剩余足迹**：v2逐一核验551个父体，恢复402处原先被分部处理遗漏的剩余足迹，约953,690m²；这些是历史核验总量。v3中国银行详细模型接管其中1处，当前普通模型保留**401处**。残差高度单独估算，不把塔楼总高直接用作裙房高度；原始阈值、面积及402处证据仍保留供追溯。
- **精确替换**：v3按源对象ID及组件关系替换**98个可渲染要素**。普通模型当前计数为 **1,796,116 − 98 + 401 = 1,796,419**，不是独立楼宇数量。外滩细模不按半径粗删邻楼；海关仅替换确认的前楼、钟楼和四角亭，独立后翼继续保留。[v3分块核验](data/bund/validation/city-patches.json)与[构件核验记录](data/bund/validation/)记录替换依据。

v6新增5、6、14号采用独立源对象的动态替换；1,796,419个要素的基线没有减去这三条。只有对应细模加载成功且实际可见时，才隐藏相应普通表示，卸载后恢复。详见[本轮范围](data/bund/REALISM_V6.md)。

高度优先级为：源height → 楼层数×3.2m → CMAB严格轮廓匹配的预测高度 → CNBH 10m栅格估计 → GHSL区域均高 → 明确标注的12m缺省。CMAB在16区抽样1,280个足迹作对齐检查，不采用简单最近邻或无依据的GCJ偏移。

**栅格估计会明显低估高楼。** 在375条来源高度/楼层的一致性检查中，CNBH绝对差中位16.45m、P90为124.47m；这不是独立地面真值评估。CMAB、CNBH、GHSL与Overture年代也不同，不能据此宣称全城真实天际线或测绘级精度。[高度数据及比较](data/heights/HEIGHT_SOURCES.md)保留v2来源、许可和验证证据；其中历史计数应与上述v3替换变化区分。

[全域高细节数据可行性核查](data/audit/HIGH_DETAIL_DATA.md)补充检查了六类来源，分别记录实际细节等级、上海覆盖、许可及访问结果。本轮未取得可直接公开分发的全市精细模型包；有照片和尺寸依据的单体仍可继续逐栋重建。

## 加载、检查与重建

页面按当前位置加载附近城市分块和详细建筑；普通楼近景准备好后才替换相应远景，失败时保留已有模型。网页GLB经过压缩，地标原始可编辑GLB继续保留。v5普通楼的可重建产物以源码、输入和压缩分块提供。城市分块离开缓存范围后释放；加载失败时保留在线建筑回退。正常的Overture建筑通过GERS标识与本地分块直接关联。服务临时不可用、切换到OSM备用建筑时，则先检查完整建筑几何是否被已加载且可见的模型覆盖，再按实际OpenMapTiles建筑要素ID隐藏重复体块；两者不是同一套ID，也不假定两套数据逐栋对应。跨出覆盖范围、缺少ID、存在未覆盖瓦片片段或精细地标尚未加载的建筑会保留，模型退出后恢复备用建筑。

备用模式的包含检查处理凹多边形和孔洞，替代了地图引擎不支持建筑多边形的`within`表达式。部分OSM要素把多栋独立建筑合并为同一ID：这时按原有多边形组件判断覆盖，未覆盖组件以原轮廓、孔洞、属性和高度保留在独立备用图层，待其完成渲染才隐藏原ID；不裁剪轮廓、不扩大覆盖边界。跨界的单个多边形仍保留，无法判定的重叠瓦片碎片也保留原表示。真实OpenMapTiles要素23809960的46组件案例和失败恢复顺序由[组件回归测试](tests/osm-building-residual-plans.test.mjs)覆盖，另有[包含与ID测试](tests/osm-building-suppression.test.mjs)及[备用图层生命周期测试](tests/osm-residual-layer.test.mjs)。帧率与内存占用取决于设备、浏览器、视野和模型密度，不承诺固定帧率。[运行验证](tests/verification.json)和[建筑几何验证](data/bund/validation/)记录各自的检查范围。

```sh
python tools/check_assets.py
npm test
python data/audit/build_audit.py --project .
python data/heights/verify_release.py
```

- [外滩源码说明](source/bund/README.md)：13栋建筑、配套街道及各自输入资料。
- [全域生成说明](source/city/FULLCITY_BUILD.md)：建筑分块、精确替换、父体残差与压缩。
- [高度重建说明](data/heights/REBUILD.md)：下载、裁剪、匹配与配置锁；超限上游原始下载不纳入仓库。
- [陆家嘴源码](source/landmarks/)：四地标生成与导出，运行方式见文件头部。

普通建筑近景发布为 `.glb.gz`。下载时保留同一宏块的 `READY.json` 和 `near/` 相对路径，工具会校验压缩文件与解码GLB，再转换为可导入Blender等编辑器的普通GLB。外滩也可直接下载上表原始GLB或.blend。以下示例从项目根目录运行：

```sh
npm ci --prefix source/city/detail/tooling --ignore-scripts
python tools/unpack_model.py assets/city-detail/macros/14-13719-6695/near/-3_1-s1-s0-s0.glb.gz exported/ordinary-near.glb --gltfpack source/city/detail/tooling/node_modules/.bin/gltfpack
```

随后在Blender选择“文件 → 导入 → glTF 2.0”打开 `exported/ordinary-near.glb`。该普通楼样本已实际导入Blender 4.3.2：转换文件963,416B，4,144个网格实例、91,936个三角，三角数与源清单一致、坐标有限。[导入记录](data/audit/city-detail-v5/blender-import.json)只验证这个样本，不是全城Blender审计。

## 许可与署名

原创界面、控制器和生成代码采用[MIT](LICENSE)。OSM/Overture轮廓及派生建筑数据库遵循ODbL-1.0，署名 **© OpenStreetMap contributors** 及相应来源；East Asian Buildings、CMAB、CNBH、GHSL按各自CC BY 4.0记录署名。Microsoft比较栅格采用CDLA-Permissive 2.0，仅用于验证。第三方库许可位于[licenses/](licenses/)。

外滩参考照片保留原作者和各自的CC0、CC BY或CC BY-SA许可；逐栋署名以[data/bund/manifest.json](data/bund/manifest.json)及[源码照片表](source/bund/README.md#参考照片与许可)为准，补充照片见各源码包的引用文件。外滩18号局部石墙和主窗使用CC BY-SA 4.0照片；v4.4的17号24扇主窗、12号右翼六窗使用Suicasmo的CC0原照片，其余照片用于几何参照；随附照片仍受原许可约束，**代码的MIT许可不覆盖照片、字体和外部数据**。

新增表面贴图及上海沿江HDR采用 Poly Haven CC0-1.0，作者与来源见[表面署名](assets/materials/realism-v4/SOURCES.md)。原创示意车辆与角色代码采用项目 MIT 许可；车辆摆放使用的道路数据仍保留 OSM/ODbL 说明。
