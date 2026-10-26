# 逐栋照片参照复原 · v6两批源码

本目录包含外滩5、6、7、9、14号的独立构建器及common。当前HTML共20栋：15栋外滩、4栋陆家嘴、1栋青浦普通小楼；[222源码](../../precise/README.md)单独采用普通楼来源分支。原10栋外滩仍按[上级源码链](../README.md)重建。各类细化范围不同，不能称全市同等照片精度。

## 五栋文件与入口

| 建筑 | 网页GLB | 原始GLB | Blender原生 | 远景GLB |
|---|---:|---:|---:|---:|
| 5号日清 | [8.73 MB](../../../assets/models/bund/web/bund05.glb) | [14.91 MB](../../../assets/models/bund/bund05.glb) | [24.07 MB](../../../assets/native/bund/bund05.blend) | [2.07 MB](../../../assets/models/bund/lod-v4/bund05.glb) |
| 6号中国通商 | [8.44 MB](../../../assets/models/bund/web/bund06.glb) | [13.01 MB](../../../assets/models/bund/bund06.glb) | [18.72 MB](../../../assets/native/bund/bund06.blend) | [0.96 MB](../../../assets/models/bund/lod-v4/bund06.glb) |
| 7号大北电报 | [14.59 MB](../../../assets/models/bund/web/bund07.glb) | [27.91 MB](../../../assets/models/bund/bund07.glb) | [43.87 MB](../../../assets/native/bund/bund07.blend) | [2.99 MB](../../../assets/models/bund/lod-v4/bund07.glb) |
| 9号轮船招商局 | [30.12 MB](../../../assets/models/bund/web/bund09.glb) | [76.88 MB](../../../assets/models/bund/bund09.glb) | [42.68 MB](../../../assets/native/bund/bund09.blend) | [8.43 MB](../../../assets/models/bund/lod-v4/bund09.glb) |
| 14号交通银行 | [6.73 MB](../../../assets/models/bund/web/bund14.glb) | [9.84 MB](../../../assets/models/bund/bund14.glb) | [15.05 MB](../../../assets/native/bund/bund14.blend) | [1.44 MB](../../../assets/models/bund/lod-v4/bund14.glb) |

表中单位为十进制MB，全部文件小于100,000,000字节。精确字节和本轮证据见[REALISM_V6_1](../../../data/bund/REALISM_V6_1.md)及各栋封装记录。07／09当前状态见各自DELIVERY，生成阶段README中的“待验”属于历史记录。

5号双山花与三面凸窗、6号五山墙四圆尖塔与三拱入口、14号八轴窗与阶梯塔冠保留首批成果；7号新增四层分组立面、金属顶帽与屋顶窗，9号新增通透外廊、不同柱式、石券缝和连续搭接瓦。所有楼体均有真实洞口、侧壁、独立框和构件；未见侧后、绝对高度与雕饰含推定。

照片玻璃范围为05的6窗112片、06的6窗127片、14的28窗137片、07的6窗18片、09南短翼2窗20片。原图只映射可靠的玻璃面，墙体和窗框不由整面照片平板代替。五栋原始／网页各保留一张原图，远景不带图；该策略不适用于222，它的中央匾在远景仍含照片。

玻璃嵌框约20mm前退距为构造估计，不是测量。明确标记的照片玻璃显示捕获光照，保留EXIF与色调映射，不叠加重复光照/HDR；普通材质和照片石墙保持各自路径。05／06／14首批844.5004㎡加07／09的317.9618㎡，v6铺装追加累计1,162.4622㎡；原v5成果另行保留，面积不代表实测。

本轮三栋HTML技术检查通过，共15组采集、6份近／远景资产核验；root实际查看10张截图并接受有限接入表现。另有独立目录检查：生产20项静态记录复用，以及仅测试响应移除222后的19项动态加入／退出／返回和索引SHA失败保留基线。目录另经root实际图像复核，包含动态退出后返回的叠楼回归视图。三栋静态采集与运行时修复后的回归范围分别记录，不把旧图冒充全部修复后重跑；这不重跑全部20栋或全城逐栋核验。 见[本轮审计](../../../data/audit/precise-buildings-v6/release-next/README.md)。

## 离线重建

单栋源码须保留相邻common、冻结JSON、引用的原照片与字体。各包的`build_model.py`、README和DELIVERY说明其实际输出命名及所需依赖；例如从项目根运行：

```sh
python source/bund/photo-rebuild-v6/bund07/build_model.py --output exported/bund07
python source/bund/photo-rebuild-v6/bund09/build_model.py --output exported/bund09
```

Python、NumPy、约束三角剖分Shapely及fontTools按包记录使用；相机研究可能另需Pillow/SciPy，读取冻结控制点不必重做相机拟合。原生转换使用Blender；预览地面、灯光和相机不属于源建筑GLB。原10栋v3/v4.4入口不能冒充这五栋当前源码。

## 来源与许可

五张2025主图均为Suicasmo、CC0-1.0；补充照片各自署名。7号另含Ferox Seneca2012 CC BY-SA 3.0、xiquinhosilva2016 CC BY 2.0、Chainwit.2024 CC BY 4.0与公版书页；9号2013两图为Legolas1024、CC BY-SA 4.0。首批05／06／14各年代照片与公版图页见原研究清单，不把整个目录统称CC0。

原创程序按MIT，地图轮廓和派生定位保留OpenStreetMap／Overture及ODbL署名，字体保留OFL。外部图像不因放入代码仓库变为MIT。首批三栋历史网页检查、旧启动包05冒烟和v5全城检查仍各自有效，但不冒充本轮07／09／222测试。
