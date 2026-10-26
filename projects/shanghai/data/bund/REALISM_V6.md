# v6 首批逐栋照片参照重建

本轮新增外滩5、6、14号三栋，项目独立地标扩展为17栋：13栋外滩历史建筑与4栋陆家嘴地标。全市逐栋照片复原继续进行，尚未达到所有普通楼与这些历史建筑相同的现场细节精度。

16区普通楼基线保持1,796,419个建筑及部件要素、1,708个宏块和169,320个近景分块。既有126处有源屋顶、401处父体残差与历史98要素精确替换记录均保留。本轮三个新模型通过独立源对象动态替换普通楼表示，没有再次减少基线计数，也不按半径删除邻楼。

## 新增模型与照片范围

| 建筑 | 本轮实体结构 | 实景玻璃范围 | 未使用照片的部分 |
|---|---|---|---|
| 5号 · 日清大楼 | 双山花、跨三层三面凸窗、连续檐口、门柱、字牌、通风口与分组阳台 | 中央6窗、112片独立玻璃 | 折线凸窗、阁楼、下层门窗及墙框保持几何材质；部分侧后开间含推定 |
| 6号 · 中国通商银行旧址 | 五山墙、四圆尖塔、三拱柱廊、独立南附翼、普通地层高窗台与落地入口 | 中央6窗、127片：三层111片、二层16片 | 地层、附楼、外围窗及二层被阳台玻璃遮挡的分格保持普通玻璃 |
| 14号 · 交通银行旧址 | 四排八轴窗、48个真实正面窗洞、黑石入口、金格栅、实体字牌与阶梯塔冠 | 上部28窗、137片独立玻璃 | 4整窗与17个边界不可靠或被遮挡的分格保持普通玻璃；后翼部分尺寸及开间含推定 |

合计40窗、376片玻璃。照片采样逐片避开原图黑窗框、石柱、灯具、路牌和其他遮挡物；实体框、洞口侧壁、墙面和雕饰继续作为三维几何保留。三张2025年CC0原始JPEG分别以原字节嵌入，每栋使用单一照片玻璃材质；05、14号按EXIF方向6回转到原始存储像素，06号为方向1。照片中的反射固定在窗片上，并非多视角摄影测量或动态环境反射。

## 下载与实际文件大小

以下为已安装资产元数据及实际文件大小，单位均为**字节**。每个发布文件严格小于100,000,000字节；不使用Git LFS。

| 建筑 | 网页GLB | 原始GLB | Blender原生文件 | 远景GLB | 原始三角形数 |
|---|---:|---:|---:|---:|---:|
| 5号 · 日清大楼 | [8,733,620](../../assets/models/bund/web/bund05.glb) | [14,906,152](../../assets/models/bund/bund05.glb) | [24,069,984](../../assets/native/bund/bund05.blend) | [2,070,252](../../assets/models/bund/lod-v4/bund05.glb) | 146,056 |
| 6号 · 中国通商银行旧址 | [8,438,924](../../assets/models/bund/web/bund06.glb) | [13,010,488](../../assets/models/bund/bund06.glb) | [18,715,384](../../assets/native/bund/bund06.blend) | [956,784](../../assets/models/bund/lod-v4/bund06.glb) | 91,111 |
| 14号 · 交通银行旧址 | [6,725,708](../../assets/models/bund/web/bund14.glb) | [9,844,376](../../assets/models/bund/bund14.glb) | [15,048,712](../../assets/native/bund/bund14.blend) | [1,443,684](../../assets/models/bund/lod-v4/bund14.glb) | 77,324 |

当前三栋安装文件的SHA256已与各自 `data/bund/models/*-web.json`、原始metadata及实际文件逐一核对：

| 建筑 | 文件 | SHA256 |
|---|---|---|
| bund05 | 原始GLB | `a125c8e72bfe8f4eb8abb7c402d9789e01387d2d16f3eee045bf6f7c3aaf5212` |
| bund05 | 网页GLB | `779cacbfb1ef1fe973c204164f685f2bee5ea33a470118538f1042df7d413d59` |
| bund05 | 远景GLB | `6da511ad35e72659c1112be66ad6bffb4b3d5ba001d4be27810e44f3663298ff` |
| bund05 | Blender原生 | `a45fba4947c7cf43dcd8c959b21bcd673c74e26afe321a5980ce1f9dae3dfd5a` |
| bund06 | 原始GLB | `641bc6f0b747df3a7405bda467b65311f9758493f6b32d6d463d18cb94eed0a6` |
| bund06 | 网页GLB | `bd7e553e55a09efe4f01279cd68650cbfb2fe324aeee0228eabb712d2054a596` |
| bund06 | 远景GLB | `433f701a74159017e0df0c76872245d5b56ff8100705bd4ce81a8fdcf65c5996` |
| bund06 | Blender原生 | `c57b8c8c0f5714cfd08deb7e218fb1876c497cd3c3d528bcf2b12c28c7ce9474` |
| bund14 | 原始GLB | `dcd09ce14eaa59ac016e66dffd7a672360e2a8cff6c5af6d8ae051142e8c7bdf` |
| bund14 | 网页GLB | `a838ad7887713c5cd43b2abd6e139b3d52744465c0a4ea82608571e9af7b8801` |
| bund14 | 远景GLB | `a4a7fc70ee4e7fd4cdae7d4efbdc933c4ff8ae66d7c3830be3a359af0db423df` |
| bund14 | Blender原生 | `d935a015f94bf3266b7bfe28c72e4bdd914d2e0ef50b5258c47dd1588a9c76cc` |

[资产清单](manifest.json)保存SHA256、锚点、模型高度及来源。原始和网页近景保留照片；约400m外使用无照片轻量变体，返回约300m内恢复近景，切换失败继续保留可见模型。Blender文件包含可编辑建筑网格和独立预览场景，预览地面与灯光不属于建筑GLB。

v6启动包尚待生成及核验；规划仍为本地保存原14栋核心地标，本批新增3栋的模型、远景变体及参考照片从固定版本按需联网加载。17栋是项目地标总数，不表示17栋模型字节全部随ZIP打包；旧v5包不代表本轮更新。

## 嵌框玻璃、网页显示与楼前铺装

三栋玻璃调整到对应窗框前脸后约**20mm**的槽内，避免原先与厚框分离、受到框体过度遮挡。此嵌框深度属于明确的构造估计（`measured:false`）；真实墙洞、实体窗框、照片采样UV及JPEG字节保持原值。

网页将带实际照片map且名称明确为 `PhotoFacade_…Glass…`／`PhotoFacade_…Glazing…` 的玻璃转为 `MeshBasicMaterial`，显示拍摄时已捕获的光照和反射（captured radiance）。它们不再接受重复场景光照／投影，也不叠加第二套HDR；原颜色系数、透明度、EXIF补偿和 `toneMapped` 设置仍保留，显示继续经过应用统一色调映射，不能声称屏幕像素与原图逐值一致。此处理不是去光照PBR重建；照片石墙、无照片窗框和普通玻璃保持原材质路径。材质转换按导入group去重，照片及共享Bitmap到模型卸载时才按归属释放。

局部阴影正常设备为4096×4096、48m半范围，低内存设备为1024×1024；最终尺寸仍受设备 `maxTextureSize` 上限约束。保留缓存更新与近景范围机制，未用全市实时阴影冒充全面光照模拟。

05／06／14主临街边与已建道路边界之间补入约**844.50㎡**灰石铺装，复用原单一 `bund-streets` 道具，新增352个三角形和3块0.075m行走支持面。原138,478个三角形及3,479个家具／树障碍保留；总街景为138,830个三角形。新增范围以实际道路外边缘及冻结立面边构成，按道路、水体、旧铺装、源孔洞、草床和已知建筑边界排除，不推定内部庭院、未见台阶或新的真实标高。面积和0.075m顶面是模型构造量，非测绘结论。见[街景追加源码](../../source/bund/street/frontage-v6/README.md)与[核验](validation/street-frontage-v6.json)。

后续逐栋工作遵循[细化验收标准](../audit/precise-buildings-v6/DETAIL_STANDARD.md)。当前仍为17栋地标（13栋外滩＋4栋陆家嘴）；07、09及222候选尚未上线。

## 尺度与证据

三栋采用冻结的OSM真实多边形与原地理锚点，按可辨正面、斜视照片和历史资料确认开间、券形、附翼及屋顶。近似相机标定利用EXIF镜头资料、传感器尺寸、控制线和地图面宽，不能当作实测尺寸。

- 日清：主立面约20.14m，主檐约23.8m、山花约28.9m；34.5m包围高度含推定旗杆。2011年南侧照片补充阳台及附属立面证据，轴线分配和不可见后部仍有推定。
- 中国通商：主立面约32.22m、南附面约6.12m；主檐约13.95m、石山墙尖约22.03m、含花饰最高约22.99m。细窗边界与普通地层窗台另经原图复核。没有按OSM六层标签机械堆出六层，也没有把6号与9号轮船招商局混用。
- 交通银行：主立面约23.17m，主体平檐约24.6m、石塔冠约33.4m。多年代斜视支持塔体进深、折返与西伸后翼；后翼檐高、部分侧后窗数和沟槽深度仍为估计。

所有高程小数是计算或导出值，不代表测绘精度。后立面、隐蔽屋面、构件厚度与精细雕刻按各栋说明保留推定或简化，未建立可游览室内。全市普通楼仍主要依轮廓、高度及类型参数生成门窗，不能与这些照片参照细模混称同等精度。

## 来源与许可

三张主参考图均为Suicasmo于2025年5月1日拍摄，CC0-1.0：

- 5号 · 日清大楼：[Commons原图](https://commons.wikimedia.org/wiki/File:Nissin_Building_20250501.jpg) · [随附原图](../../assets/references/bund/bund05.jpg) · [逐栋源码与证据](../../source/bund/photo-rebuild-v6/bund05/README.md)。
- 6号 · 中国通商银行旧址：[Commons原图](https://commons.wikimedia.org/wiki/File:China_Merchants_Bank_Building,_Shanghai_20250501.jpg) · [随附原图](../../assets/references/bund/bund06.jpg) · [逐栋源码与证据](../../source/bund/photo-rebuild-v6/bund06/README.md)。
- 14号 · 交通银行旧址：[Commons原图](https://commons.wikimedia.org/wiki/File:Bank_of_Communications_Building,_Shanghai_20250501.jpg) · [随附原图](../../assets/references/bund/bund14.jpg) · [逐栋源码与证据](../../source/bund/photo-rebuild-v6/bund14/README.md)。

日清另含Can Pac Swire的2011年CC BY-SA 2.0侧视参考；中国通商含1908年公版书页；交通银行的各年代斜视分别保留作者与CC BY／CC BY-SA许可，完整记录见该栋研究清单。未发现再分发许可的机构照片只保留观察结论和来源链接，不嵌入或打包原图。

原创程序和独立生成几何采用项目MIT约定；地图轮廓及派生定位保留©OpenStreetMap contributors／Overture及ODbL-1.0署名。字牌所用字体子集及许可保留于共享common/fonts，近似实体字形不冒称照片书法描摹。照片和字体不因进入源码目录而改为MIT。

## 已完成检查与最终场景状态

三栋已完成逐构件拓扑、FLOAT32零面积检查，原始／网页／轻量模型压缩检查，原JPEG字节与逐片UV检查，以及独立Blender原生预览核对。06、14号还保留独立目录源码重建一致性记录，适用模型SHA以报告为准；玻璃嵌框修订另有逐实体位移和字节保持证明。检查对应的具体对象和限制写在各报告内，不将单体原生预览称为全网页验收。

- 封装及文件证据：[05](../audit/precise-buildings-v6/bund05-packaging.json)、[06](../audit/precise-buildings-v6/bund06-packaging.json)、[14](../audit/precise-buildings-v6/bund14-packaging.json)。
- 原生预览：[05](../audit/precise-buildings-v6/bund05/native-preview-review.json)、[06](../audit/precise-buildings-v6/bund06/native-preview-review.json)、[14](../audit/precise-buildings-v6/bund14/native-preview-review.json)。
- 普通楼替换：[几何守恒](../audit/precise-buildings-v6/geometry-validation.json)、[独立可见状态与退出恢复](../audit/precise-buildings-v6/runtime-owner-validation.json)、[地图接入核对](../audit/precise-buildings-v6/map-integration-review.json)。保留源三角位置与FLOAT32法线，三个对象可分别隐藏，邻楼保留。
- 完整 `npm test` 已通过；[三栋网页技术报告](../audit/precise-buildings-v6/release/browser.json)包含15组采集记录与6份近／远景资产SHA核验，精确归属、14栋邻楼保留和reset通过。
- [独立视觉记录](../audit/precise-buildings-v6/release/visual-review.json)实际查看10张完整近景／斜视／远景及reset截图，接受本批三栋与局部铺装的接入表现；另外5组仅技术记录。远景城市背景仍是可见的推定建筑，细微阴影锯齿仍保留。
- 采集发生在后续网络deadline／可选shield filter补丁之前；最终应用和v6启动包需后续冒烟核验。原报告20条warning、1条预期取消均保留，不把0个错误写成0条warning；详见[本批审计范围](../audit/precise-buildings-v6/release/README.md)。

旧v5全市构建和场景报告继续保留于[原发布审计](../audit/city-detail-v5/release/README.md)，它们不替代本批新增三栋的网页测试。[v5说明](REALISM_V5.md)及更早版本记录保留为历史来源。
