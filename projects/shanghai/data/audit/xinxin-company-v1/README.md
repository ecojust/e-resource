# 新新公司南侧商店临街外观交付

[主地图直接查看](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=huangpu-xinxin-company&mode=overview) · [来源与范围](../../../source/precise/huangpu-xinxin-company/README.md) · [四资产清单](../../../assets/models/candidates/huangpu-xinxin-company/manifest.json)

本件为南京东路720号新新公司／第一食品商店的南面与两侧前段，包含浅色柱带、凹窗、双矩形墙板、挑廊与托臂、栏杆、两级中空方塔和两南角亭。**北旅馆、未知天井、室内及真实南北分界未建。** 后切面为展示封口，不是已核对的后立面；原底图北体与后续任务保留。

## 来源与估计

[文献复核](documentary-review.json)实际取得官方建筑志，确认南部七层、高“30余米”，北部沿街延至天津路、贵州路设旅馆入口。官方没有给出北部层数、分界或高度测量端点。[照片复核](photo-review.json)实际查看八张2013至2025年照片，其中部分近似角度已注明，不能当作八面独立覆盖；照片不随资产分发，也不作纹理。

文献记1949年南中塔拆除，现代照片存在塔楼；复建年代与原构造身份未定。文献“六楼挑阳台”与作者依照片分配的层段并列保留。本件不是1925年原貌复原。作者选择廊顶29.2米、中央塔实体顶37.5米；实际外包51.750×30.862×37.500米，轴数、层段、窗格、栏花、屋面与约31米展示进深仍为估计。截断线不是实测商店／旅馆分界，展示屋面也不能排除未查明的内院。

## 冻结资产与真实几何检查

| 资产 | 字节 | 三角面 |
|---|---:|---:|
| 原始GLB | 4,546,352 | 79,884 |
| 网页GLB | 1,422,636 | 79,884 |
| 远景GLB | 715,384 | 37,960 |
| 可编辑Blender | 2,393,681 | 79,884（建筑网格） |

四件合计9,078,053字节，每件小于100 MB，SHA见清单。[几何检查](geometry.json)核对实际序列化几何、1795／1507个分别闭合的作者构件以及15项实际表面检查。[打包检查](packaged.json)实际解码压缩网页及远景GLB，逐材质核对有向三角面一致，验证两层塔贯通、0.32米窗后退、1.45米入口及2.47米退廊等设计深度。作者构件分别闭合，不声称全楼是一个布尔合并实体。

[原生检查](native.json)实际重开Blender，建筑网格与源GLB一致，摄影棚不计入建筑；GLB和Blender均无照片贴图。[独立审查](independent-model-review.json)另行读取实际顶点与索引，核对五个高度截面、塔空腔及柱实体正控、窗和入口深度、最后资产及图像哈希。

[正面](native-front-v2.png)、[斜面](native-oblique-v2.png)、[北切面](native-rear-v2.png)与[南面细部](native-south-detail-v2.png)均经过实际查看，结果见[原生视觉记录](native-visual-review.json)。北侧末端柱已收回展示范围，封口共面细线已修正。原始试作图未作为本轮最终证据发布。

## 部分接入主地图

[定位复核](footprint-review.json)绑定唯一源 `building / 7e69180c-6b22-4417-a40b-f5dcd2235bb9`，宏块 `14-13720-6694`、localId1453。灯牌和模型原点位于南部已建范围中心，约121.47222314、31.23733860，方位−14.44415747°；这是近似配准，不是测绘验收。原整源局部系的 `y≤−8m` 展示边界，重基点后为模型系 `y≤15.2194298128m`，世界位置保持不变。

真实解码的原始／网页／远景水平外包一致。0.05米配准余量同时受唯一源足迹和北侧截断限制，只替换南部约1570.611平方米，保留北部约2394.552平方米（60.3897%）。与先施模型碰撞边界仍相隔约7.928米，邻源替换范围无交集。

默认查看方向为东南侧，方位−59.44415747°、俯角35°。完整城市楼块加载后，原西南视角会被对面高楼挡住，因此仅调整本条模型的默认镜头；附近建筑和北侧保留楼体保持可见。相机调整及几何未变的核对见定位记录和独立审查。

[增量接入检查](global-integration-checks.json)确认原31个候选记录和旧审计保持不变，裁剪三角形从62增至66／128；只对自身源做部分替换。[运行时检查](runtime-checks.json)包含33项灯牌／镜头测试和8项跨轮资产增量回归。本轮新资产清单核验四件文件，目录生成另沿用既有两件派生廊道资产检查；没有重跑旧模型全量资产矩阵。旧灯牌运行时代码保持不变，现有窄屏编号布局可容纳72项。[生成及导航复核](root-checks.json)另含12项实际导航／目录测试。

[北源实际几何检查](baseline-north-geometry.json)另行解码当前楼块的城市远景与近景资产，确认localId1453、北部屋顶和墙面实际存在，未以平面差集代替三维几何证据。

[真实浏览器检查](browser.json)完成七张截图和[逐图实际查看](browser-visual-review.json)：[近景](browser-auxiliary-desktop-full-b8b5f6a4-93a2383d.png)、[远景](browser-auxiliary-desktop-lod-b8b5f6a4-93a2383d.png)、[手机模型页](browser-auxiliary-mobile-full-b8b5f6a4-93a2383d.png)、[主图桌面](browser-global-default-desktop-29494443-93a2383d.png)、[北侧保留楼体](browser-global-retained-north-29494443-93a2383d.png)、[主图手机](browser-global-default-mobile-29494443-resume-6e75ffb1.png)、[320像素下72个灯牌](browser-beacons-320-city-72-29494443-resume-6e75ffb1.png)。近远景资产、主图实际收到的目录哈希、72个导航入口和16区对应通过；控制台错误、警告和HTTP失败均为零。窄屏72张编号牌均可见、无重叠且中心命中正确；原生触控编号72后，从新永安切换到新新，地址片段、名称、地图中心和目标资产可见状态均改变。

截图等待城市远近景加载队列、要素状态写入、实际宏块显示和两次渲染帧稳定。首段取得五张有效图后，手机尺寸切换时DOM已缩到390像素、地图画布尚为960像素，镜头断言拒绝了这次取景；[初始记录](browser-initial-run.json)保留该失败。同一浏览器等待画布、地图内部尺寸及界面布局稳定后，使用[续跑脚本](resume-browser.cjs)补齐手机与灯牌两图；没有重新生成前五图或修改生产代码。两段脚本及图像的哈希分别保留，静态状态不代替实际像素检查。

## README 与 TODO

两份README及地标目录均为72项、16区，黄浦24项；全部模型查看入口进入 `projects/shanghai/index.html`。原40项保留既有室外漫游，32件候选提供近似定位的全局俯瞰，入口数不代表逐栋完整复原数量。

[TODO与目录检查](todo-directory-checks.json)确认26项已交付任务与46项既有库存退出活动制作列表。原始1058条建筑登记、1036条具名源、1038条道路线索及旧审计保留。7条主楼任务仍已移除，历史建筑／构件及调查线索剩1051条；新新条目保留北旅馆、天井与南北连接。具名源按图层与ID精确关联17条，剩1019条待查。下一制作项为南京东路830号大新公司历史主楼，参考尚待实际核对。

## 重建与复验

从仓库根目录执行，Python依赖见[source/requirements.txt](../../../source/precise/huangpu-xinxin-company/source/requirements.txt)，另需Blender与gltfpack：

```sh
python projects/shanghai/source/precise/huangpu-xinxin-company/source/build_model.py --out /tmp/xinxin-build
python projects/shanghai/source/precise/huangpu-xinxin-company/source/build_model.py --out /tmp/xinxin-build --lod
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-xinxin-company/source/build_native.py -- --raw /tmp/xinxin-build/huangpu-xinxin-company-raw.glb --out /tmp/xinxin-build/huangpu-xinxin-company.blend --previews /tmp/xinxin-native --samples 20 --suffix=-v2
python projects/shanghai/source/precise/huangpu-xinxin-company/source/package_assets.py --raw /tmp/xinxin-build/huangpu-xinxin-company-raw.glb --lod /tmp/xinxin-build/huangpu-xinxin-company-lod.glb --native /tmp/xinxin-build/huangpu-xinxin-company.blend --out /tmp/xinxin-assets --gltfpack /path/to/gltfpack
python projects/shanghai/source/precise/huangpu-xinxin-company/source/verify_geometry.py --assets /tmp/xinxin-assets --out /tmp/xinxin-packaged.json --gltfpack /path/to/gltfpack --blender /path/to/blender
python projects/shanghai/tools/build_candidate_city_integrations.py --check
python projects/shanghai/tools/build_model_todo.py --check
python projects/shanghai/tools/build_landmark_directory.py --check
python projects/shanghai/data/audit/xinxin-company-v1/todo-directory-checks.py
```

浏览器脚本[qa-browser.cjs](qa-browser.cjs)需Playwright、Chromium和提供本项目及稀疏资产的HTTP服务。设置 `NODE_PATH`、`MODEL_BASE_URL`、`CHROMIUM_PATH` 后执行 `node projects/shanghai/data/audit/xinxin-company-v1/qa-browser.cjs --run`。使用一个浏览器页面顺序检查资产页、目录、主图和手机触控。工具版本和渲染器可能影响原生字节及像素；更改模型后应更新四资产、清单、部分替换合同和对应检查。

本次原脚本按实际执行字节保留，续跑专用于上述五图后保留的同一个Chrome页面，不能单独启动新浏览器。先将原报告另存 `browser-initial-run.json`，记录并暂停原Node控制进程，将PID写入 `QA_INITIAL_PID_FILE` 指定文件，再执行 `node projects/shanghai/data/audit/xinxin-company-v1/resume-browser.cjs --run`。续跑只检查手机与灯牌，合并浏览器事件后关闭原Chrome；完整执行分段和已解决的失败见 `browser.json`。
