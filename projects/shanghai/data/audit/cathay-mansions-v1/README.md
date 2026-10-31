# 华懋公寓历史主楼外观交付

[主地图直接查看](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=huangpu-cathay-mansions&mode=overview) · [来源与范围](../../../source/precise/huangpu-cathay-mansions/README.md) · [四资产清单](../../../assets/models/candidates/huangpu-cathay-mansions/manifest.json)

对象为锦江饭店北楼／锦北楼的独立历史主楼。包含褐砖长立面、浅色窗框、两列多边凸窗、北侧双凸翼及开敞凹部、小中央顶层与低层外观。峻岭公寓、礼堂、其他锦江楼栋、花园和室内不并入。

## 来源与估计

[文献复核](documentary-review.json)实际读取《上海名建筑志》华懋公寓章节。名录109号与文献189号保留分歧；十四层57米与十三层65米之说在同一章节并列，测量端点均未明。模型采用57米为作者选定总高，主体十三层段加中央顶层的分配、窗轴、退距和隐面均为估计。

[照片复核](photo-review.json)实际查看2006年花园侧、2019年西北街角及两张历史照片。两类现代方向互补，但花园下部受树木遮挡，东侧、屋顶和隐蔽构造未完整覆盖。历史广景用于区分华懋与峻岭，未将峻岭阶梯高冠搬入华懋。照片只供观察，不作贴图、不随项目分发。

## 模型和定位

| 资产 | 字节 | 三角面 |
|---|---:|---:|
| 原始GLB | 11,172,688 | 241,940 |
| 网页GLB | 3,046,720 | 241,940 |
| 远景GLB | 1,441,416 | 101,436 |
| 可编辑Blender | 6,251,495 | 241,940（建筑网格） |

四件共21,912,319字节，每件小于100 MB；实际外包约65.05×28.285×57米。[几何检查](geometry.json)与[打包检查](packaged.json)核对605个窗孔、4325／2622个分别闭合且正体积的作者部件，以及每档31条实际表面射线。压缩网页与远景GLB经实际Meshopt解码，与各自未压缩几何的Float32有向面逐材质严格一致，没有靠坐标容差掩盖丢面或翻面。

打包器将相接构件的共位置顶点合并，产生40条已逐件定位的接触边，涉及主墙／冠墙角、凸窗底板和基座交界。每条恰对应两个已验证闭合正体积部件，坐标与部件标签固定于源码；未知接触边仍判失败。不将材质合批网格宣传为单一布尔并集流形。

[原生检查](native.json)实际保存并重开Blender，建筑网格保持一致，摄影棚不计入建筑。[独立审查](independent-model-review.json)另行解码三档，各16条射线检查凹窗、凸窗、实体正控和北侧空区，并独立比较实际水平投影。[正面](native-front-v2.png)、[斜面](native-oblique-v2.png)、[北侧](native-rear-v2.png)及[凸窗细部](native-detail-v2.png)均由主代理实际查看，见[native-visual-review.json](native-visual-review.json)。v2补充照片可见的中央上段浅色竖饰，v1留作早期过程记录。

[定位复核](footprint-review.json)绑定独立源 `building / f6e4b883-ed86-4c90-aa96-2c717ff043c5`，宏块 `14-13719-6694`、localId3146，原点约121.45626564、31.22245828，朝向−12.52888883°。三档实际占地投影约1410.744平方米，0.65米有界配准对应原源1438.441平方米；北侧三处凹部保持，模型与碰撞均不侵入邻源。

旧近景屋檐比源轮廓外扩约0.07米。显示裁剪采用源轮廓法向外扩0.13米，覆盖实际旧屋檐且有至少0.0348米余量，源外裁剪面积26.600934平方米另行记录；这不改写原源面积。相同近景文件内另两楼与裁剪范围无交集。北楼源全部替换，无旧高楼细条作为保留范围。

东邻近景没有逐顶点源ID，其实际投影与本次显示裁剪交叠约1.838750平方米。生产裁剪器现按已知近景文件的归属列表过滤裁剪：北楼组接收3146的14个三角，东邻组接收0个。逐顶点ID路径、无归属信息路径和无指定源的通用裁剪保持原行为；释放、重绑及阴影／深度材质纳入回归。组过滤不会创造单个顶点身份，同组其他楼仍依靠经核验的空间边界保留。

[运行时检查](runtime-checks.json)包含38项裁剪及既有集成回归、33项当前目录灯牌和镜头测试。[增量检查](global-integration-checks.json)7项通过，裁剪总预算87／128，旧33项候选记录与历史审计保持原字节。[根检查](root-checks.json)另含12项实际目录／导航测试和生成器一致性检查。

库存本轮只读取新四资产，继承上一轮冻结记录；累计36份清单、144件资产、534,573,876字节。两份清单属于原有入口，不能把36份清单当作36个新增全局模型。

[真实浏览器检查](browser.json)完成七张截图，均由主代理[逐图实际查看](browser-visual-review.json)：[网页近景](browser-auxiliary-desktop-full-3958d7f5-0fee5124.png)、[网页远景](browser-auxiliary-desktop-lod-3958d7f5-0fee5124.png)、[手机模型页](browser-auxiliary-mobile-full-3958d7f5-0fee5124.png)、[主图桌面](browser-global-default-desktop-29494443-0fee5124.png)、[北侧凹部与邻楼](browser-global-north-recess-context-29494443-0fee5124.png)、[主图手机](browser-global-default-mobile-29494443-a5febd33.png)、[320像素74个灯牌](browser-beacons-320-city-74-29494443-74487685.png)。主楼完整入画，北凹可见地面，东邻低楼保留，未见旧41.6米屋顶残框。真实近远景切换、四资产下载校验、74条主图入口及原生触控从大新切至华懋均通过。

源组同时实际加载并可见时，北楼组只接收3146的14个裁剪三角，东邻组为0；真实近景HTTP字节及生产脚本SHA均匹配冻结输入。控制台错误、警告和HTTP失败均为零。只使用一个Chrome，最终已关闭。

软件渲染环境中先遇到手机面板30秒过渡等待超时，随后遇到320像素全城状态队列180秒等待超时；两次均未保存不稳定截图。原五图保留，通过[手机恢复脚本](qa-browser-resume.cjs)补第六图，再通过[灯牌恢复脚本](qa-browser-beacons-resume.cjs)补最后一图。保留各段脚本SHA、失败和队列进度；没有改变页面或放宽稳定判据，最终等地图状态队列归零并通过连续两次渲染确认。恢复过程见报告的`recoverySegments`及`recovery`。

## 目录和 TODO

当前目录74处入口、16区，黄浦26处；原40项保留既有室外漫游，34件候选提供近似定位的全局俯瞰。两份README模型查看链接统一进入 `projects/shanghai/index.html`，每处从相同目录生成精灵灯牌。

[TODO与目录检查](todo-directory-checks.json)确认28项已交付制作任务和46项既有库存退出活动制作列表，9条已完成主楼不重复列项；原始1058条名录保留，活动建筑／构件及调查线索余1049条。具名源关联仍为18条、余1018条，因为华懋源不在该具名快照内。下一项峻岭公寓高层主楼已接续制作；“茂名公寓”是其后称，西侧低层住宅与完整名录范围继续调查。

## 重建与复验

从仓库根目录执行，Python依赖见[source/requirements.txt](../../../source/precise/huangpu-cathay-mansions/source/requirements.txt)，另需Blender和gltfpack：

```sh
python projects/shanghai/source/precise/huangpu-cathay-mansions/source/build_model.py --out /tmp/cathay-build
python projects/shanghai/source/precise/huangpu-cathay-mansions/source/build_model.py --out /tmp/cathay-build --lod
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-cathay-mansions/source/build_native.py -- --raw /tmp/cathay-build/huangpu-cathay-mansions-raw.glb --out /tmp/cathay-build/huangpu-cathay-mansions.blend --previews /tmp/cathay-native --samples 16 --suffix=-v2
python projects/shanghai/source/precise/huangpu-cathay-mansions/source/package_assets.py --raw /tmp/cathay-build/huangpu-cathay-mansions-raw.glb --lod /tmp/cathay-build/huangpu-cathay-mansions-lod.glb --native /tmp/cathay-build/huangpu-cathay-mansions.blend --out /tmp/cathay-assets --gltfpack /path/to/gltfpack
python projects/shanghai/source/precise/huangpu-cathay-mansions/source/verify_geometry.py --assets /tmp/cathay-assets --out /tmp/cathay-packaged.json --gltfpack /path/to/gltfpack --blender /path/to/blender
python projects/shanghai/tools/build_candidate_city_integrations.py --check
python projects/shanghai/tools/build_model_todo.py --check
python projects/shanghai/tools/build_landmark_directory.py --check
python projects/shanghai/data/audit/cathay-mansions-v1/todo-directory-checks.py
```

真实页面脚本为[qa-browser.cjs](qa-browser.cjs)。设置 `NODE_PATH`、`MODEL_BASE_URL` 和 `CHROMIUM_PATH` 后执行 `node projects/shanghai/data/audit/cathay-mansions-v1/qa-browser.cjs --run`。只使用一个浏览器页面，窗口变化和城市加载完成后等待两次稳定渲染，再检查实际模型与相邻楼体。
