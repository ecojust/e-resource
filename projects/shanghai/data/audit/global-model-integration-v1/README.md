# 已完成模型接入全局场景与按区目录

本轮将30件已交付的单体模型接入上海地图，与原有40处入口合为70处建筑与构件模型入口，覆盖16区。原始单体网页、GLB、Blender和来源说明继续保留。全局模型按距离加载近景／远景，目录中的“全局查看”直接定位对应模型。

这70处是可查看的模型入口数，包含学宫内分开的殿堂、门、牌坊、池桥和碑廊，不能当作70栋独立楼宇或全市复原完成率。新增30处采用近似定位，提供全局俯瞰；原有40处室外漫游继续保留。新增模型没有被改称测绘级复原或全部通过原址漫游验收。

| 区 | 已独立建模的建筑／构件入口 |
|---|---:|
| 黄浦区 | 22 |
| 徐汇区 | 7 |
| 长宁区 | 2 |
| 静安区 | 1 |
| 普陀区 | 1 |
| 虹口区 | 4 |
| 杨浦区 | 1 |
| 闵行区 | 1 |
| 宝山区 | 1 |
| 嘉定区 | 1 |
| 浦东新区 | 4 |
| 金山区 | 1 |
| 松江区 | 1 |
| 青浦区 | 2 |
| 奉贤区 | 1 |
| 崇明区 | 20 |
| **合计** | **70** |

## 定位与底图处理

- [接入清单](../../candidate-city-integrations.json)与原有 `landmarks.json` 共用一套ID供地图、灯牌、按区目录使用，不另造一份模型数量。
- [城市位置核验](urban-placement-review.json)及[场址和近邻复核](urban-site-review.json)记录黄浦6件、虹口3件、徐汇1件。8件有明确地图源身份；底图只在已验证可见模型的有界范围内裁剪。大光明保留后部影厅，宋庆龄与鲁迅源楼身份不充分，保留其全部底图。鲁迅正立面以已核POI附近位置示意，仍有定位及遮挡限制。
- [崇明说明](chongming-placement.md)与[原创布局图](chongming-layout.png)记录20件的近似院落关系。整园错误拉高的源块仅在主轴／东轴已建区域及庭院内修正；西侧、东北合院余体与周边67个源要素保留。模型原有尺寸、朝向、隐面及历史时期限制继续适用。
- 碑廊全局派生版本只改变两个节点的刚性变换，将两条长廊分置东西侧；压缩几何二进制、索引、材质和面数不变。18米间距是近似布局。原Blender仍保留单体展示布局。
- 泮池整体显示抬升0.85米，使原模型水面位于地图零高程平面之上；这不是实测标高，也没有新增地形或挖池模型。源模型水位、池床和桥体几何均保留。
- 裁剪依赖当前场景中可见且SHA校验成功的模型，模型隐藏或卸载后恢复底图。源文件没有被删除或改写。在线矢量底图先准备范围外余体，再隐藏对应源显示。

## 检查范围

[资产清单](inventory.json)实际读取32份候选交付中的128件资产，共469,145,558字节，核对每件字节数、SHA与原始GLB真实坐标；其中2件早已属于原40入口，本轮只新增其余30件。[接入生成检查](catalog-checks.json)核对ID、资产和位置合同。[独立摆放检查](placement-independent.json)采用运行时坐标与旋转公式检查实际外包，碑廊使用原网格位置与派生节点变换分别检查两廊。

浏览器、运行时、灯牌和目录的最终结果由本目录相应JSON记录；资产解码、几何可见性、灯牌显示及页面目录分别核验，不能相互替代。软件GPU与本地HTTP测试不代表真实手机GPU或CDN性能。几何检查没有重新认定历史尺寸、照片复原精度或未经验证的院内通行。

[全局浏览器记录](browser.json)覆盖新增30件模型的实际加载、位置变换及近远景切换；[资产浏览器记录](browser-assets.json)核对全部60件网页／远景资产的HTTP字节、解码和几何外包。[目录检查](directory.json)覆盖桌面、手机、搜索、键盘和直接链接；[README与灯牌身份核对](readme-beacons.json)确认两份README、16区数量和地图70个登记ID一致。登记数量与某一视口实际可见牌数分别记录。

## 重建

在仓库根目录执行以下工具。缺失的历史资产可从记录的Git版本读取，无需取消全仓库稀疏检出。

```sh
python projects/shanghai/tools/build_global_urban_placements.py
python projects/shanghai/tools/build_chongming_global_placements.py
python projects/shanghai/tools/build_candidate_city_integrations.py
python projects/shanghai/tools/check_global_model_placements.py
python projects/shanghai/tools/update_global_model_metadata.py
python projects/shanghai/tools/build_model_todo.py
python projects/shanghai/tools/sync_readme_districts.py
python projects/shanghai/tools/build_landmark_directory.py
python projects/shanghai/tools/restoration_progress.py
```

灯牌以同一70条记录生成原创精灵图与名称牌，和模型LOD／加载距离独立；视野内标记保持固定屏幕尺寸。密集时每个模型保留独立编号，以引线连接原址，不合并成簇；点选后显示名称并定位模型。布局避开侧栏、底部信息卡和地图按钮。缩放及点击结果见[实际浏览器记录](browser-beacons.json)。

名称牌和编号牌的点击、悬停使用绘制布局的屏幕矩形，原址灯点保留独立命中；不依赖地图引擎对动态文字偏移的旧命中索引。视野外名称牌由明确过滤器隐藏，70条源记录与原址灯点仍保留。候选默认镜头按模型外包和界面留白取景，并保持目标高程；切回既有入口时恢复其原有镜头规则。

[运行时回归记录](runtime-regressions.json)区分初次全套与后续针对性检查，逐项记录通过结果及文件版本。[独立代码复核](runtime-independent-review.json)、[灯牌独立检查](beacon-checks.json)及[窄屏间距增量检查](beacon-compact-delta-checks.json)另行记录范围和文件指纹。原生命中查询、对象的`visible`状态或资产解码成功均不单独作为像素验收依据；涉及源建筑修正的截图需等待残余建筑准备完成及后续实际绘制。

名称牌采用五种固定尺寸的原创精灵背景，文字与背景共享偏移；地面锚点投影和透视补偿使实际屏幕尺寸、排布矩形及点击区域一致。[最终灯牌代码复核](beacon-ground-perspective-review.json)单独记录这次修正，保留先前缩放、编号和窄屏报告所检查的原版本。

[名称牌最终浏览器检查](browser-nameplates.json)实际重载最终脚本，核验960×720碑廊视角中的12块完整名称牌，以及390×844手机视图中的7块名称牌；实际鼠标点击明伦堂、触控大光明均切换至不同目的地，名称、地址片段和地图中心同步更新。[图像复核](browser-visual-review.json)记录最终五处全局几何视图，包含完整泮池水面、桥体和两条碑廊；旧场景证据保留各自运行时指纹，没有重写成最终脚本测试结果。

## 已发布版本

应用提交为 `961148cdb24f882dbffe91b96ee0646eb0d76e5a`。[全局地图](https://raw.githack.com/ecojust/e-resource/961148cdb24f882dbffe91b96ee0646eb0d76e5a/projects/shanghai/index.html#mode=overview)与[按区目录](https://raw.githack.com/ecojust/e-resource/961148cdb24f882dbffe91b96ee0646eb0d76e5a/projects/shanghai/landmarks.html)固定到同一版本。

[发布字节检查](publication-bytes.json)实际读取85个公开HTTP文件，共97,330,571字节，包含30件新增模型的全部60个近远景文件、两份README、目录、清单及本轮运行时／依赖文件；均逐字节匹配该提交。[预览地址检查](publication-preview.json)确认地图、目录与灯牌模块的固定版本地址返回HTTP 200、正确内容类型及相同字节。此项是发布内容核对，真实浏览器渲染和交互范围见前述本地浏览器证据。
