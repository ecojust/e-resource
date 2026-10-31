# 峻岭公寓高层主体与入口雨棚交付

[主地图直接查看](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=huangpu-grosvenor-house&mode=overview) · [来源与范围](../../../source/precise/huangpu-grosvenor-house/README.md) · [四资产清单](../../../assets/models/candidates/huangpu-grosvenor-house/manifest.json)

本件为锦江饭店中楼的历史高层主体与有限入口雨棚，包含五折内凹立面、阶梯露台、中央及端部浅色竖饰、深凹冠槽、真实窗孔和雨棚框格。前庭两块未核源区域与西侧低层建筑保留；本件不关闭整条名录。

## 来源与范围

[文献复核](documentary-review.json)实际读取《上海名建筑志》峻岭公寓章节，确认1956年改名“茂名公寓”，不按两个旧称重复建高层。名录写“峻林公寓、茂名公寓”、茂名南路65－125号，文献主楼记59号；原始拼写和门牌范围保留。

文献记中央18层包括地下1层、高78米，两翼阶梯降低；另有地上18层与地下3层的百科记载。模型选择78米总高与17个地上层段，不重建地下空间，顶部端点及具体层高均为估计。1934年建成、1935年出租与名录1935年分别保留，不合成未经证实的单一事件。

[照片复核](photo-review.json)实际查看四图。2020年高位主图提供前庭、阶梯露台与部分屋顶，街景补充侧面及独立低楼；没有完整背面、墙脚与屋面覆盖。远景页面中的错误楼名已排除。照片只供观察，不作贴图、不随资产分发。

文献所提西侧六幢三层公寓的现存身份和名录归属仍待查。中央雨棚两侧的源台阶无法可靠判定为低裙房、全高凸出或空地；不为清空原地图而扩棚或编造高度。[设计范围](../../../source/precise/huangpu-grosvenor-house/design-scope.json)单独保留该限制。

## 模型与几何

| 资产 | 字节 | 三角面 |
|---|---:|---:|
| 原始GLB | 10,430,628 | 193,620 |
| 网页GLB | 3,310,388 | 193,620 |
| 远景GLB | 1,341,484 | 64,540 |
| 可编辑Blender | 5,668,340 | 193,620（建筑网格） |

四件共20,750,840字节，每件小于100 MB；外包约90.983×27.791×78米。[几何检查](geometry.json)与[打包检查](packaged.json)核对761个实际窗孔、2813／2768个分别闭合且正体积的作者构件、每档48项表面射线，以及实际Meshopt解码后的严格Float32有向面一致性。五级露台、冠槽背板、前庭空区和雨棚玻璃／金属上下双向射线均通过；本件材质批次未出现邻接歧义，也不宣称各独立构件已作全楼布尔并集。

[原生检查](native.json)实际重开Blender，建筑网格与源GLB一致且无照片贴图。v2将雨棚金属框改为实际18格开孔并收进边界，保留玻璃片，避免与前方独立源相交。[独立审查](independent-model-review.json)另行解码三档，各22项、共66项射线通过，raw/full逐材质有向面严格一致。

[正面](native-front-v2.png)、[斜面](native-oblique-v2.png)、[估计背面](native-rear-v2.png)、[冠部与退台](native-detail-v2.png)、[入口雨棚](native-canopy-detail-v2.png)五张最终原生图均由主代理实际查看，见[native-visual-review.json](native-visual-review.json)。早期v1保留作过程记录；两个细部视图有意局部取景，没有覆盖写图。

## 主图接入与保留区域

[定位复核](footprint-review.json)绑定独立高层源 `building / 6fa0e0aa-bfd0-4d9e-a4bb-16e9088d530e`，宏块 `14-13719-6695`、localId2398；原点约121.45728030、31.22126042，朝向32.69139103°。华懋、西侧相接低楼4270、前方小源3049和其他邻楼保持独立。

显示裁剪结合原源法向外扩0.12米的旧近景外檐边界，以及作者实际投影向外0.5米的有界范围。冻结原源明确保留两片35.036800平方米：西约18.605154、东约16.431647平方米；实际旧近景保留约36.276028平方米，24.7米粗略屋顶仍存在。这是原始地图数据的保留，不是确认该处真实建筑高24.7米。

总显示裁剪约1412.334830平方米，其中约25.330540平方米位于原源外、用于实际近景边界余量。模型、保守碰撞与外部邻源均无面积交叠，雨棚距3049源约0.585米。前庭负空间保持；同组近景的其他10个来源与裁剪范围无交集，西侧其他近景组沿用上一轮已验证的归属过滤。

新增26个裁剪三角，总113／128。[增量检查](global-integration-checks.json)7项通过，确认旧34条候选记录和历史审计不变，向量源剩余为两片，且与保留合同形状相同。运行时面积约35.036808平方米，与几何合同存在约0.000008平方米计算差异，按已列数值公差核验。

[运行时检查](runtime-checks.json)包含34项当前目录灯牌和镜头测试。长标题卡片使320像素可用空间变小时，仅在20像素高编号牌仍过载时改用22×18编号牌，文字仍为12像素；正常布局保留原尺寸。真实75条目录的长卡片、多个缩放层级、独立点击与避让界面均有回归。[根检查](root-checks.json)另含12项目录／导航测试及生成器一致性检查。

本轮库存只读取新四资产，继承华懋冻结证据；累计37份清单、148件资产、555,324,716字节。未重跑历史模型全量资产矩阵。

## 实际网页与灯牌

[浏览器记录](browser.json)保存同一个Chrome中的单体近景、远景、手机页、主图默认桌面、前庭俯视、主图手机及320像素全城灯牌七张图。[补充灯牌记录](short-beacons.json)另存320×548像素的实际22×18编号牌图。八张图均由主代理实际查看，见[browser-visual-review.json](browser-visual-review.json)。

默认桌面图能辨认前庭西、东两处保留的原源屋顶和独立3049小源；前庭俯视图显示雨棚及开敞空间，但东侧保留块被灯牌遮住，其像素保留以默认桌面图为依据。原源24.7米屋顶不作为真实建筑高度。西侧4270近景未获裁剪三角；[补充HTTP收据](western-source-http-receipt.json)分开记录原页面ResourceTiming与恢复后同一URL的只读200响应及字节哈希，不将补收响应冒充最初加载事件。

在320×568像素页面实际按相同CSS离屏测量全部75张标题卡片，最长卡片163像素高，顶部为328像素；华懋与峻岭实际143像素高，顶部348像素。标准全城图显示75个22×20编号牌。补图保持华懋选择，将视口减至320×548，使卡片顶部实际达到328像素，核对75个22×18编号牌、12像素文字、独立命中与界面避让；没有声称实际选择或加载了北大街222号旧模型。

补图后恢复320×568视口，使用原生触控点击峻岭编号牌，实际从华懋切至峻岭，标题、URL、镜头与可见目标模型均改变。最终浏览器检查完成并关闭唯一Chrome；页面错误、警告及失败HTTP列表为空。

原脚本曾错误要求短关键词“峻岭”只匹配一项，实际华懋范围说明也合法提及峻岭；恢复检查两项匹配及完整楼名唯一匹配。初版CDP恢复适配器又尝试序列化整个应用对象，已改为布尔就绪判断并保留失败版本。脚本、失败原因、恢复路径及输入哈希均留存；生产文件未在取证期间改变，城市队列归零、布局稳定和连续两帧渲染要求始终保留。

## 目录与 TODO

当前按区目录75处入口、16区，黄浦27处；原40项保留既有室外漫游，35件候选提供近似定位的全局俯瞰。README模型查看链接统一进入 `projects/shanghai/index.html`，同一目录生成所有精灵灯牌。

[TODO与目录检查](todo-directory-checks.json)确认29项已交付制作任务和46项既有库存退出活动制作列表，9条已完成主楼不重复列项，原始名录与审计保留。活动名录／构件及调查线索仍为1049条，因为b1-018继续列前庭余块及西侧低层住宅范围调查；新新北旅馆等原有未建部分继续保留。具名源关联18条、待查1018条。

下一制作项为上海公共租界工部局历史主楼，已经完成文献与图像预研；须先拆清历史街面翼楼、2024补建段与庭院独立建筑，取消的50米塔楼方案不能用作现存高度。

## 发布

模型提交为 `781a3e306a847b60feb3c535a3ffc3925e3f27b6`。[线上核验](publication.json)实际读取该不可变提交下的15个公开HTTP文件，包括两份README、主图、目录、灯牌与源裁剪脚本、单体辅助入口、来源说明及四模型资产；均返回200，字节与提交一致。[固定版本主图直达](https://raw.githack.com/ecojust/e-resource/781a3e306a847b60feb3c535a3ffc3925e3f27b6/projects/shanghai/index.html#landmark=huangpu-grosvenor-house&mode=overview)。模型版本日期随后从真实Git提交生成，未用制作中的占位日期冒充已发布记录。

## 重建与复验

从仓库根目录执行，Python依赖见[source/requirements.txt](../../../source/precise/huangpu-grosvenor-house/source/requirements.txt)，另需Blender和gltfpack：

```sh
python projects/shanghai/source/precise/huangpu-grosvenor-house/source/build_model.py --out /tmp/grosvenor-build
python projects/shanghai/source/precise/huangpu-grosvenor-house/source/build_model.py --out /tmp/grosvenor-build --lod
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-grosvenor-house/source/build_native.py -- --raw /tmp/grosvenor-build/huangpu-grosvenor-house-raw.glb --out /tmp/grosvenor-build/huangpu-grosvenor-house.blend --previews /tmp/grosvenor-native --samples 16 --suffix=-v2
python projects/shanghai/source/precise/huangpu-grosvenor-house/source/package_assets.py --raw /tmp/grosvenor-build/huangpu-grosvenor-house-raw.glb --lod /tmp/grosvenor-build/huangpu-grosvenor-house-lod.glb --native /tmp/grosvenor-build/huangpu-grosvenor-house.blend --out /tmp/grosvenor-assets --gltfpack /path/to/gltfpack
python projects/shanghai/source/precise/huangpu-grosvenor-house/source/verify_geometry.py --assets /tmp/grosvenor-assets --out /tmp/grosvenor-packaged.json --gltfpack /path/to/gltfpack --blender /path/to/blender
python projects/shanghai/tools/build_candidate_city_integrations.py --check
python projects/shanghai/tools/build_model_todo.py --check
python projects/shanghai/tools/build_landmark_directory.py --check
python projects/shanghai/data/audit/grosvenor-house-v1/todo-directory-checks.py
```

网页脚本[qa-browser.cjs](qa-browser.cjs)需Playwright、Chromium与项目HTTP服务。设置 `NODE_PATH`、`MODEL_BASE_URL`、`CHROMIUM_PATH` 后执行 `node projects/shanghai/data/audit/grosvenor-house-v1/qa-browser.cjs --run`，只使用一个浏览器，实际布局、地图队列和连续两次渲染稳定后才取证。
