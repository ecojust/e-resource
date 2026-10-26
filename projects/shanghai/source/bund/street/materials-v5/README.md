# 街道材质 v4.5：只读审计与限定补丁

本包只在 staging 写文件。没有修改主项目、模型、建筑材质、照片资产或 Git；没有启动浏览器。补丁只修复 `BundRoadSurface` 沥青全幅纹理被误用石材裁片消隐阈值的问题。效果应是克制的中距离色差恢复，不承诺凭此解决整条街的真实感。

## 具体发现与照片依据

| 对象 | 当前原因 | 有依据的处理 |
| --- | --- | --- |
| 楼前亮白带 | 公开截图第 257/258/259 行有 335/492/473 个像素精确为 RGB(205,210,208)，等于底图 `#cdd2d0`；另有大片 `#d9ddd8` 背景色。Three 铺装约为灰色，两个不同渲染体系的亮度没有统一。 | 根代理的几何补齐应优先解决。`road_area_pattern` 和 pedestrian line 同色，离线证据不足以区分具体 layer；不能因此全局调暗 `BundStonePaving` 或删除底图。 |
| 沥青过于纯色 | 全幅 2.1×2.1m 实拍扫描仍被当作“需避开砖缝的石材裁片”，在 0.14m/pixel 时完全退出，路面回到纯底色。 | 独立全幅消隐 0.20→0.90m/pixel，保留硬件 mip 过滤色差；微法线仍在 0.055m/pixel 时归零，远处仍不采样。已给可套用补丁。 |
| 铺装像统一网格 | `BundStonePaving` 一种材质覆盖滨江步道、路边肩带与连接补片；统一东西/南北世界坐标下 1.20×0.60m running-bond，没有照片里的横向深色铺带与区域差异。当前缝宽 4mm、缝色压暗 14%，都是推定。 | 2011 实拍确有灰色宽石板、较深横带与窄缝，但没有可校准的条带坐标。先保留现尺寸和颜色；后续按已定位铺装区域/路向分组，不能通过全局放大纹理或随机画横带冒充复刻。 |
| 草带像平毯 | 两个床只有水平土面/草面：土顶 .080m、草顶 .090m，石边顶 .215m；扫描图本身是混合裸土与稀草的通用材质，斜视下 mip 平均后自然近似纯色。照片所见疏树及其阴影、草丛轮廓尚无可信三维对应。 | 保留 2.51×2.51m 物理扫描尺度。增加法线/放大草纹不会产生草叶轮廓；不要用随机斑块、乱放树或更饱和绿色替代定位证据。绿化代理应在其证据范围内补体积。 |
| 浅色石边 | `BundGraniteCurb` 还共用于栏杆柱/灯基座；并非截图整段白带的唯一或主要来源。路缘真实宽度当前估计 .12m，绿化边宽 .18m。 | 2010 高角照片支持浅灰低边，2025 汇丰照片支持楼侧黄色路缘和灰色人行道。保留现几何边界与整体亮度，勿把共享石边统一刷成道路黄漆。 |

`src/paving-material.js` 是旧版脚本；当前 `map-scene.js` 只导入 `architectural-material.js`，没有运行旧 .80×.42m 网格。此次诊断没有把旧脚本误当作当前效果。`realism-v5` 的上海滨江 HDR 仅用于建筑玻璃，本任务未改变它。

## 参考与年代限制

- `source/bund/street/references/promenade-day.jpg`：Bohao Zhao，2011-08-01，**CC BY 3.0**；[Commons 原页面](https://commons.wikimedia.org/wiki/File:外灘步行道_Bund_Promenade_-_panoramio.jpg)，[许可](https://creativecommons.org/licenses/by/3.0/)。观察灰色宽石板、深色横带、窄缝、栏杆/台阶；未把照片作为地面贴图。
- `source/bund/street/references/bund17-18-19-aerial-2010-original.jpg`：Gary Lee Todd, Ph.D.，2010-09-18，**CC0-1.0**；[Commons 原页面](https://commons.wikimedia.org/wiki/File:2010_Shanghai_Bund,_Viewed_from_Oriental_Pearl_Tower_02.jpg)，[许可](https://creativecommons.org/publicdomain/zero/1.0/)。支持长条绿化床、浅石边、道路与植被的形态关系，不能证明 2026 年每棵树的位置/物种。
- `assets/references/bund/hsbc-20250501-original.jpg`：Suicasmo，2025-05-01，**CC0-1.0**；[Commons 原页面](https://commons.wikimedia.org/wiki/File:HSBC_Building,_Shanghai_20250501-1.jpg)，[许可](https://creativecommons.org/publicdomain/zero/1.0/)。观察暗沥青、黄色楼侧路缘、排水缝和灰石人行道。照片中的花箱/临时设施不能任意复制到 17–19 号楼前。

三张照片光照、白平衡、拍摄年份不同，未做光度标定；没有把照片 RGB 当作真实材质反射率。所有输入 SHA、大小和截图像素证据在 `evidence.json`。没有新下载或修改图像。

## 参数建议

下表的数字是渲染工作值，尺寸均非现场测量。**本补丁仅应用沥青消隐一项**。

| 材质 | 保留当前底色（线性 RGB）与物理尺度 | 合理的后续微调范围 / 限制 |
| --- | --- | --- |
| 铺装 | (.36,.38,.39)，granite 无缝采样片约 .514×.813m；估计板块 1.20×.60m、缝 4mm | 干燥灰石 roughness .78–.90、metalness 0；当前未改。不要把采样片扩大成板块，也不要让纹理砖缝叠加几何/程序缝。 |
| 沥青 | (.065,.075,.080)，完整 2.1×2.1m | 保留 base roughness .94、normal 强度 .25 及现有近距离消隐；颜色/粗糙度覆盖改为 .20–.90m/pixel。 |
| 草带 | (.10,.13,.055)，完整 2.51×2.51m | 干草/土 roughness .90–1.00、metalness 0；先保持颜色，避免因 2010 照片色差强行换季。 |
| 石边 | (.48,.49,.46)，绿化石边 (.46,.47,.44) | 灰石 roughness .78–.90、metalness 0；现有近距离纹理尺度合理，先解决真实边界与形体。 |

## 交付与套用

- `street-asphalt-v4.5.patch`：相对 `src/architectural-material.js` 的最小 unified diff，可由根代理套用。
- `architectural-material.street-v4.5.mjs`：同补丁结果的审阅副本，不要求新增第二套 runtime 模块。
- `patch-input.json`：基线/候选 SHA。基线应为 `866e426810f80a7fcee0154a004d61284034127fce056156625eab4d439073ed`；若其他代理改动了该文件，应重新对齐差异。
- `validate_proposal.mjs`、`validation.json`：9 项实际检查，包括旧 profile uniform/顶点变换不变、photo/glass 排除、12 纹理共享、配置约束、正常/失败路径释放。没有声称 GPU shader 编译或浏览器视觉通过。
- `audit_evidence.py`、`evidence.json`：12 张现有贴图共 7,413,517B 的 SHA/大小复核与截图色值计数。

在项目目录先执行：

```sh
patch --dry-run -p1 -i /workspace/shanghai_expansion/street-v4.5/materials/street-asphalt-v4.5.patch
node /workspace/shanghai_expansion/street-v4.5/materials/validate_proposal.mjs "$PWD"
```

根代理可随后执行同一 `patch -p1` 去掉 `--dry-run`，再以相同机位/光照做近路面和中距离 A/B。检查沥青没有重复棋盘、高光闪烁或放大颗粒；楼前白带必须单独核验几何覆盖。材质 patch 不增加图片、全场反射、额外 draw call 或常驻 GPU 纹理；仅中距离沥青保留两次颜色/粗糙度贴图采样，微法线与远景成本边界不变。
