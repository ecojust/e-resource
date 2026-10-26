# 外滩13栋建筑：源码、资料与重建

此目录对应外滩2、3、5、6、12、13、14、15、17、18、19、20、23号的近景模型。公开照片用于辨识开间、柱廊、屋顶和立面构件，OSM轮廓用于平面与地理定位。模型包含真正开孔的墙面、内退玻璃、洞口侧壁及独立柱、窗套、栏杆等几何；细小雕刻与未见侧后立面含解释和简化。**这些是照片参照下的建筑重建，不是全城测绘、摄影测量或可游览室内模型。**

发布入口为[外滩资产清单](../../data/bund/manifest.json)，全市网页的建筑清单为[data/landmarks.json](../../data/landmarks.json)。下表原始GLB适合编辑，网页GLB供运行时压缩加载；.blend保留原生网格、材质与相应预览场景。预览地面、相机和灯光不属于建筑GLB。

| 建筑 | 当前生成入口 | 发布文件 |
|---|---|---|
| 2号 · 上海总会 | [bund_classics/wall-v4.4/](bund_classics/wall-v4.4/README.md) | [网页GLB](../../assets/models/bund/web/bund02.glb) · [原始GLB](../../assets/models/bund/bund02.glb) · [.blend](../../assets/native/bund/bund02.blend) |
| 3号 · 有利大楼 · 外滩3号 | [bund_classics/wall-v4.4/](bund_classics/wall-v4.4/README.md) | [网页GLB](../../assets/models/bund/web/bund03.glb) · [原始GLB](../../assets/models/bund/bund03.glb) · [.blend](../../assets/native/bund/bund03.blend) |
| 5号 · 日清大楼 | [photo-rebuild-v6/bund05/](photo-rebuild-v6/bund05/README.md) | [网页GLB](../../assets/models/bund/web/bund05.glb) · [原始GLB](../../assets/models/bund/bund05.glb) · [.blend](../../assets/native/bund/bund05.blend) |
| 6号 · 中国通商银行旧址 | [photo-rebuild-v6/bund06/](photo-rebuild-v6/bund06/README.md) | [网页GLB](../../assets/models/bund/web/bund06.glb) · [原始GLB](../../assets/models/bund/bund06.glb) · [.blend](../../assets/native/bund/bund06.blend) |
| 12号 · 汇丰银行大楼 | [classical_bank/wall-v4.4/](classical_bank/wall-v4.4/README.md)（包含照片前置基线） | [网页GLB](../../assets/models/bund/web/bund12.glb) · [原始GLB](../../assets/models/bund/bund12.glb) · [.blend](../../assets/native/bund/bund12.blend) |
| 13号 · 江海关大楼 | [customs_refined/customs_house_v3.py](customs_refined/customs_house_v3.py) | [网页GLB](../../assets/models/bund/web/bund13.glb) · [原始GLB](../../assets/models/bund/bund13.glb) · [.blend](../../assets/native/bund/bund13.blend) |
| 14号 · 交通银行旧址 | [photo-rebuild-v6/bund14/](photo-rebuild-v6/bund14/README.md) | [网页GLB](../../assets/models/bund/web/bund14.glb) · [原始GLB](../../assets/models/bund/bund14.glb) · [.blend](../../assets/native/bund/bund14.blend) |
| 15号 · 华俄道胜银行大楼 | [classical_bank/curtain-v4.4/](classical_bank/curtain-v4.4/README.md)（墙修复后） | [网页GLB](../../assets/models/bund/web/bund15.glb) · [原始GLB](../../assets/models/bund/bund15.glb) · [.blend](../../assets/native/bund/bund15.blend) |
| 17号 · 字林西报大楼 | [bund_classics/photo-v4.4/](bund_classics/photo-v4.4/README.md) | [网页GLB](../../assets/models/bund/web/bund17.glb) · [原始GLB](../../assets/models/bund/bund17.glb) · [.blend](../../assets/native/bund/bund17.blend) |
| 18号 · 麦加利银行 · 外滩18号 | [chartered_bank/photo-v4.4/](chartered_bank/photo-v4.4/README.md) | [网页GLB](../../assets/models/bund/web/bund18.glb) · [原始GLB](../../assets/models/bund/bund18.glb) · [.blend](../../assets/native/bund/bund18.blend) |
| 19号 · 和平饭店南楼 · 汇中饭店 | [art_deco/wall-v4.4/](art_deco/wall-v4.4/README.md) | [网页GLB](../../assets/models/bund/web/bund19.glb) · [原始GLB](../../assets/models/bund/bund19.glb) · [.blend](../../assets/native/bund/bund19.blend) |
| 20号 · 和平饭店北楼 · 沙逊大厦 | [art_deco/wall-v4.4/](art_deco/wall-v4.4/README.md) | [网页GLB](../../assets/models/bund/web/bund20.glb) · [原始GLB](../../assets/models/bund/bund20.glb) · [.blend](../../assets/native/bund/bund20.blend) |
| 23号 · 中国银行大楼 | [art_deco/wall-v4.4/](art_deco/wall-v4.4/README.md) | [网页GLB](../../assets/models/bund/web/bund23.glb) · [原始GLB](../../assets/models/bund/bund23.glb) · [.blend](../../assets/native/bund/bund23.blend) |

[网页街景预览](../../assets/previews/bund-street.png) · [汇丰柱廊细部](../../assets/previews/bund/hsbc-column-detail.png) · [麦加利柱廊细部](../../assets/previews/bund/chartered-column-detail.png) · [海关窗洞细部](../../assets/previews/bund/customs-window-detail.png)

## v6逐栋照片重建与源码链

5、6、14号使用[photo-rebuild-v6](photo-rebuild-v6/README.md)的独立构建器和相邻common工具：冻结真实轮廓、照片控制点与逐栋推定说明，先建立连续开孔墙、深窗洞和独立框，再为明确可见的玻璃逐片映射原JPEG。三栋分别为6窗112片、6窗127片、28窗137片；其余窗、被遮挡分格和未见侧后部分按各包说明保留几何材质或推定。原始与网页GLB保留照片；远景轻量变体不携带照片。

当前三栋玻璃位于框前脸后约20mm的估计槽位；该深度不冒称测量，墙洞、框和照片UV不随之改形。网页的明确照片玻璃使用captured-radiance显示：保留原 `toneMapped`、颜色系数与EXIF补偿，取消重复场景受光和HDR；照片石墙与普通玻璃不套用该转换。这是HTML材质显示修正，不是把已拍到的光影消除为PBR数据。见[渲染说明](photographic-glass-rendering.md)及[逐栋细化验收标准](../../data/audit/precise-buildings-v6/DETAIL_STANDARD.md)。

正常设备局部阴影为4096×4096、48m半范围（低内存1024×1024，并按硬件上限约束）。[街景追加源码](street/frontage-v6/README.md)另为05／06／14主立面前补入844.50㎡估计铺装和3个0.075m支持面；原街景几何、家具／树障碍及来源孔洞保留。当前完整街景入口为项目根 `tools/build_bund_street.py`，直接运行旧 `street/build_street.py`只重建历史v5基线。

新增源码不依赖旧版墙体基线。原10栋仍按下列v4.4及v3入口重建，旧源码和来源记录继续保留。三栋数值几何、照片字节、原生预览与压缩检查已完成；本批三栋网页技术检查通过，主审实际查看10张截图后接受本轮接入表现；采集早于后续网络／样式补丁；补丁后的v6解压启动包另通过05号与清单重置冒烟，具体范围见[REALISM_V6](../../data/bund/REALISM_V6.md)。

v6启动包已生成并通过归档校验和实际解压后的05号／清单重置冒烟。本地保存原14栋核心地标，本批新增3栋的模型、远景变体及参考照片从固定提交按需联网加载；17栋是项目地标总数，不表示17栋模型字节全部随ZIP打包。07、09及222仍为未上线候选。

## v4.4墙体修正与源码链

2、3、12、15、17、19、20、23号整合了相邻结构墙。旧墙块在接触处留下反向重叠内部面，正面边缘也有未共用节点的接缝，近看会出现黑线、虚线或闪烁。当前源码按墙面和厚度清理内部面并连接网格，保留真正窗洞、洞口侧壁、玻璃退距及墙面前后层次。18号补连续墙芯，封住原先贯通的空缝；真实石材接缝、凹槽和已有照片映射保留。13号原有墙体未发现同类问题，继续使用原生成入口。

12号的当前`classical_bank/wall-v4.4`以完成六窗照片采样的基线为输入，再清理结构墙；照片前置阶段保留于`classical_bank/photo-v4.4`。15号先完成`classical_bank/wall-v4.4`，再用`classical_bank/curtain-v4.4`修正窗帘体朝向并去掉内部穿插褶皱。17号当前`bund_classics/photo-v4.4`已包含墙体清理、24窗采样与双侧屋顶石塔修正。18号使用`chartered_bank/photo-v4.4`；其他建筑按上表的`wall-v4.4`入口重建。各包保留必要基线、依赖与检查记录，具体命令以该包README为准。旧基线文件用于追溯和重建前置步骤，不能直接当作当前发布模型。

## 基础源码与资料对应关系

下表保留原始几何生成器及资料位置。除新增photo-rebuild-v6、13号和街道入口外，单独运行这些基础生成器只会得到历史v3几何，当前发布版本须继续执行上面的v4.4源码链。

| 目录 | 建筑与必要输入 | 说明 |
|---|---|---|
| [bund_classics/](bund_classics/README.md) | 2、3号用build_classics.py；17号用build_news.py；保留mesh_utils.py、footprints.json、news-footprint.json及相互导入的脚本 | architecture-evidence.json、reference-photos.json记录开间与屋顶资料；两类脚本共用几何工具 |
| [classical_bank/](classical_bank/README.md) | 12、15号；build_classical_banks.py、geometry-input.json、assets/字体子集 | sources.json、references/保留照片与历史图纸；现状照片优先于历史立面图 |
| [customs_refined/](customs_refined/SOURCES_AND_METHOD.md) | 13号；customs_house_v3.py与facade_geometry.py | 源组件JSON/GeoJSON、照片和覆盖验证一并保留；官方高度与后翼排除范围单独说明 |
| [chartered_bank/](chartered_bank/SOURCES.md) | 18号；build_chartered_bank.py、building-source.json、photo-source.json | 三个文件生成历史v3基础几何；当前入口为photo-v4.4，参考照片、来源说明与验证报告应随发布保留 |
| [art_deco/](art_deco/README.md) | 19、20、23号；build_art_deco.py、architecture.py、footprints.json、assets/字体子集 | references.json保留照片证据；中国银行主楼、西翼及其高度解释需按本包资料区分 |
| [photo-rebuild-v6/](photo-rebuild-v6/README.md) | 5、6、14号；各build_model.py、geometry-input.json、控制点与照片，保留相邻common/ | 当前逐栋照片构建入口；具体可见范围、尺寸推定和依赖以各包说明为准 |
| [street/](street/) | 当前入口[tools/build_bund_street.py](../../tools/build_bund_street.py)；保留frontage-v6冻结基线、追加工具及原v5源 | 单街景道具：原道路／设施与新增三栋楼前有界铺装；位置有源，铺装宽度、地面构造量和设施尺度仍含推定 |

[bund-candidates.json](bund-candidates.json)保存所选建筑的地图轮廓、锚点与临街边线。每个源码包保留自身冻结输入，重建不应重新以名称搜索或用包围盒代替实际足迹。

## 高度与可核实范围

| 建筑 | 尺度依据与推定范围 |
|---|---|
| 2号 上海总会 | 公开文字、照片和真实平面用于主体比例；柱廊、顶层拱窗与双亭按照片辨识。屋顶亭阁和构件高度含推定，主屋面与总包围高度不能混用。 |
| 3号 有利大楼 | 层数、转角塔楼及双街立面参考照片与建筑资料；高度取公开二手资料和比例解释，各层分配、塔冠细节非实测。 |
| 5号 日清大楼 | 地图主立面约20.14m，主檐约23.8m、山花约28.9m按照片标定；34.5m模型包围高度包括推定旗杆。凸窗深度、侧后开间与构件尺寸仍为推定。 |
| 6号 中国通商银行 | 地图主立面约32.22m，主檐约13.95m、山墙石尖约22.03m、最高花饰约22.99m按近似相机尺度核对；并非实测。南附翼及隐蔽部分单独说明。 |
| 12号 汇丰银行 | 现状照片结合历史立面/平面图核对六柱柱廊、中庭与穹顶；未取得可核验的完整竖向测量，鼓座、穹顶及分层高度属于推定。 |
| 13号 江海关 | 官方存档给出主楼约36.2m、钟楼部分约43m、总高约79.2m、钟盘直径5.4m；墙厚、窗退距、角亭分层和未见后立面按照片解释。模型不包含西侧独立后翼。 |
| 14号 交通银行 | 地图主立面约23.17m，主体平檐约24.6m、塔冠约33.4m按照片与地图面宽推定；后翼高程、侧后窗数及槽深未实测。 |
| 15号 华俄道胜银行 | 真实轮廓与照片支持五开间、柱廊及拱券；约29m包围高度及分层、侧后墙面按照片比例推定。 |
| 17号 字林西报 | 窄临街面、深进轮廓、双侧屋顶石塔及浅弧顶冠按照片比例推定；资料层数存在口径差异，采用照片可辨层次，约40m为模型估计。 |
| 18号 麦加利银行 | 正面三开间、爱奥尼柱、山花与栏杆据照片；主檐口约24.65m、山花顶约28.36m、旗杆顶约34.45m均为照片比例估计，侧后细节为同风格推定。 |
| 19号 和平南楼 | 文字资料的主体约30m结合六层立面照片；角亭、铜顶和屋面附属部分按照片比例推定。 |
| 20号 和平北楼 | 公开建筑说明给出约77m屋顶、83m旗杆顶；各层高度、雕花、背面与内庭细节含推定，真实地图内庭保持为空洞。 |
| 23号 中国银行 | 东塔与后接西翼分别采用真实轮廓；主楼退台、牌匾和中式檐口按照片辨识。西翼层数资料有冲突，未见部分与剩余足迹的立面按包内说明解释，可信度低于临江主楼。 |

清单中的height_m是模型包围高度，可能含旗杆、亭阁和尖顶；height_estimated及逐栋来源说明用于判断其依据。模型坐标小数、网格与源轮廓吻合度只反映计算与导出一致性，不证明源数据或现场尺寸具有同等精度。

## 本地重建与历史v3命令

新三栋先用普通Python、NumPy、Shapely及所需字体依赖生成GLB，再由共享工具生成Blender原生文件；具体命令见各包。旧版生成脚本以Blender 4.3系列验证。当前版本请按首表及对应v6／v4.4源码链选择包，并执行该包README中的完整流程；12号先完成照片步骤，再进行墙体修正。若只搬迁单个源码包，应保留其列出的辅助脚本、冻结基线、JSON与assets/。照片模型嵌入局部映射的原照片，许可与采样范围见各包。

以下命令在项目根目录运行，保留为**历史v3基础构建记录**，不包含本轮墙体、照片与屋顶修正，不能直接替代当前发布流程。13号本轮未改，所列命令仍是它的当前入口。

```sh
# 历史v3：2、3号；17号单独生成
BUND_CLASSICS_OUTPUT=exported/bund-classics BUND_CLASSICS_RENDER=0 blender --background --python source/bund/bund_classics/build_classics.py
BUND_CLASSICS_OUTPUT=exported/bund-classics BUND_CLASSICS_RENDER=0 blender --background --python source/bund/bund_classics/build_news.py

# 历史v3：12、15号；加 --render 生成预览
blender --background --python source/bund/classical_bank/build_classical_banks.py -- --building hsbc --output exported/classical-bank
blender --background --python source/bund/classical_bank/build_classical_banks.py -- --building russo --output exported/classical-bank

# 13号：本轮保持，仍为当前入口
CUSTOMS_OUTPUT_DIR=exported/bund13 CUSTOMS_RENDER=0 blender --background --python source/bund/customs_refined/customs_house_v3.py

# 历史v3：18号；加 --render 生成预览
blender --background --python source/bund/chartered_bank/build_chartered_bank.py -- --output exported/bund18

# 历史v3：19、20、23号；输出在源码包内对应建筑子目录
blender --background --python source/bund/art_deco/build_art_deco.py -- peace_south --no-render
blender --background --python source/bund/art_deco/build_art_deco.py -- peace_north --no-render
blender --background --python source/bund/art_deco/build_art_deco.py -- bank_china --no-render
```

中文牌匾字体子集随classical_bank/assets/与art_deco/assets/附带，许可分别见各包Noto字体许可/OFL记录；导出时转换为网格，网页无需字体文件。街道生成使用普通Python及城市生成器依赖，入口为street/build_street.py；完整项目目录是它的默认依赖根目录。

各包生成器使用hsbc、russo、chartered-bank等原始输出名，发布目录统一命名为bundNN；[资产清单](../../data/bund/manifest.json)负责这一对应关系。直接重建得到的是原始可编辑GLB，网页优化副本是后续压缩产物，不应拿压缩差异当作源几何变化。

## 地理定位与城市替换

GLB采用米制 **X向东、Y向上、Z向南**，地面为0，地理朝向已烘焙；位置根据各自WGS84锚点设置。不能再次把包围盒中心移到原点，也不要重复施加建筑朝向。各原生Blender场景采用对应的东/北/上坐标。

v3全市背景仍为1,708块，包含1,796,419个普通要素：1,796,116个源可渲染要素，按精确ID替换98个，再加401处父体剩余足迹。v2历史核验的402处残差中有1处已由中国银行细模接管；原始402处报告是可追溯证据，当前普通残差数量为401。只替换已经确认覆盖的对象或组件，不能按半径删去周围建筑。

v6的5、6、14号由独立可见状态控制三个精确源对象的替换，普通基线仍保持1,796,419要素、1,708宏块和169,320近景分块。只有细模成功加载并实际可见时，才隐藏对应普通楼；模型退出后恢复，不按半径删除邻楼。

[坐标验证](../../data/bund/geometry-frame-validation.json)、[分块替换验证](../../data/bund/validation/city-patches.json)和[各建筑几何验证](../../data/bund/validation/)记录检查方法。凹窗检查包含从洞外向内的射线首命中验证；海关另有源组件与最终GLB底面覆盖比对。这些验证确认几何实现和定位过程，不证明未拍到的立面、室内或估计高度与现场一致。

## 参考照片与许可

以下主要参考图的作者、来源和许可按[data/bund/manifest.json](../../data/bund/manifest.json)列出。点击原图页面可查看作者上传记录；随附参考图仍保留其原许可。不同建筑可能使用同一作者的不同照片。

| 建筑 | 作者 | 照片许可 | 原图与副本 |
|---|---|---|---|
| 2号 · 上海总会 | Legolas1024 | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) | [原图页面](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E7%B8%BD%E6%9C%83.JPG) · [随附参考图](../../assets/references/bund/bund02.jpg) |
| 3号 · 有利大楼 · 外滩3号 | Suicasmo | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [原图页面](https://commons.wikimedia.org/wiki/File:Union_Building,_Shanghai_20250501.jpg) · [随附参考图](../../assets/references/bund/bund03.jpg) |
| 5号 · 日清大楼 | Suicasmo | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | [原图页面](https://commons.wikimedia.org/wiki/File:Nissin_Building_20250501.jpg) · [随附参考图](../../assets/references/bund/bund05.jpg) |
| 6号 · 中国通商银行旧址 | Suicasmo | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | [原图页面](https://commons.wikimedia.org/wiki/File:China_Merchants_Bank_Building,_Shanghai_20250501.jpg) · [随附参考图](../../assets/references/bund/bund06.jpg) |
| 12号 · 汇丰银行大楼 | Suicasmo | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [原图页面](https://commons.wikimedia.org/wiki/File:HSBC_Building,_Shanghai_20250501-1.jpg) · [随附参考图](../../assets/references/bund/bund12.jpg) |
| 13号 · 江海关大楼 | Diomidis Spinellis | [CC BY 2.5](https://creativecommons.org/licenses/by/2.5/) | [原图页面](https://commons.wikimedia.org/wiki/File:ShanghaiBundCustomsHouse.jpg) · [随附参考图](../../assets/references/bund/bund13.jpg) |
| 14号 · 交通银行旧址 | Suicasmo | [CC0](https://creativecommons.org/publicdomain/zero/1.0/) | [原图页面](https://commons.wikimedia.org/wiki/File:Bank_of_Communications_Building,_Shanghai_20250501.jpg) · [随附参考图](../../assets/references/bund/bund14.jpg) |
| 15号 · 华俄道胜银行大楼 | Suicasmo | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [原图页面](https://commons.wikimedia.org/wiki/File:Former_Russo-Chinese_Bank_Building,_Shanghai_20250501.jpg) · [随附参考图](../../assets/references/bund/bund15.jpg) |
| 17号 · 字林西报大楼 | Suicasmo | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [原图页面](https://commons.wikimedia.org/wiki/File:North_China_Daily_News_Building_20250501.jpg) · [随附参考图](../../assets/references/bund/bund17.jpg) |
| 18号 · 麦加利银行 · 外滩18号 | ScareCriterion12 | [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0) | [原图页面](https://commons.wikimedia.org/wiki/File:%E4%B8%8A%E6%B5%B7%E5%A4%96%E6%BB%A9%E9%BA%A6%E5%8A%A0%E5%88%A9%E9%93%B6%E8%A1%8C%E6%97%A7%E5%9D%802021.jpg) · [随附参考图](../../assets/references/bund/bund18.jpg) |
| 19号 · 和平饭店南楼 · 汇中饭店 | Livelikerw | [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0) | [原图页面](https://commons.wikimedia.org/wiki/File:Shanghai_Palace_Hotel_1.JPG) · [随附参考图](../../assets/references/bund/bund19.jpg) |
| 20号 · 和平饭店北楼 · 沙逊大厦 | Suicasmo | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [原图页面](https://commons.wikimedia.org/wiki/File:Sassoon_House_20250501.jpg) · [随附参考图](../../assets/references/bund/bund20.jpg) |
| 23号 · 中国银行大楼 | Suicasmo | [CC0](http://creativecommons.org/publicdomain/zero/1.0/deed.en) | [原图页面](https://commons.wikimedia.org/wiki/File:Bank_of_China_Building,_Shanghai_20250501.jpg) · [随附参考图](../../assets/references/bund/bund23.jpg) |

补充照片和历史图纸见各包sources.json、references.json、reference-photos.json、photo-source.json或SOURCES_AND_METHOD.md。其中海关补充正面照片作者Onedesign23，CC BY-SA 4.0；和平北楼补充正面照片作者ScareCriterion12，CC BY-SA 4.0。所有复制的图片都应按其各自记录署名，不能仅用上表一张主图的许可概括整个源码包。

原创生成代码适用项目[MIT许可](../../LICENSE)；OSM及其派生平面数据库按ODbL 1.0署名 **© OpenStreetMap contributors**。照片、历史图纸、字体和外部数据保持各自许可，**不因放入本目录而变成MIT**。v4.3外滩18号部分下部石墙与六块主窗使用原照片纹理，派生GLB及Blender资产按CC BY-SA 4.0署名；v4.4的17号24扇主窗与12号右翼六窗使用Suicasmo的CC0原照片，并修正实体主窗框；精细格栅和帘布仍有照片细节。v6的5、6、14号另采用Suicasmo于2025年5月1日拍摄的CC0玻璃局部采样；补充侧视和历史照片仍各自保留许可，包括5号的Can Pac Swire 2011年CC BY-SA 2.0照片及6号1908年公版书页。其余区域使用照片参照几何。以上均不属于测绘级三维资产。

## 外滩18号当前版本

v4.3主檐口和各层按原照片比例重新调整，整体竖向系数1.037，包含旗杆的模型包围高度35.72465m；这个小数只反映模型输出，不是实测精度。v4.4沿用照片校准，并补连续墙芯封住贯通空缝，保留外层石缝、真窗洞与照片采样。请使用[当前重建流程](chartered_bank/photo-v4.4/README.md)；[v4.3流程](chartered_bank/photo-v4.3/README.md)及前文v3生成器保留为来源历史。原锚点、地理平面和城市分块排除范围保持原值。
