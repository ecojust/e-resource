# 武康路129号：独立下载与HTML接入状态（v7）

徐汇武康路129号的GLB、可编辑Blender及完整源码已独立发布。本次已通过**21项静态导航候选中的单栋网页验收**：近景、斜视、LOD、返回、替换对象释放/恢复和城市清单重置；root实际查看7张记录。源对象及17个同近景块邻楼保持。该早期单栋证明不包含动态目录；后续武康两楼目录另验通过，新ZIP仅以青浦代表宏作实际解压运行，未对129重跑ZIP浏览器。

本栋本轮使用既有v2模型，原始GLB 15,002,212字节、网页GLB 4,759,104字节、LOD 2,751,684字节、Blender 21,341,124字节，均小于100,000,000字节。下载、照片许可、可移植源码和历史原生审计继续沿用本页原条目；[普通小楼索引](../README.md)列出四栋的直接下载与各自状态。[v7本次接入范围](../../../data/audit/precise-buildings-v7/release/README.md)记录实际报告；本批应用固定到`53ee12a60fcd613d82f73cb50cdf0b36436052eb`。

当前网页证据：[129静态浏览器](../../../data/audit/precise-buildings-v7/xuhui-wukang-129/acceptance/browser.json)及[129实际图像复核](../../../data/audit/precise-buildings-v7/xuhui-wukang-129/acceptance/visual-review.json)。单栋候选成功不修改原JSON或历史REBUILD中的生成阶段记录；本段补充其后发生的验收。后立面、隐藏屋顶、绝对尺度、材料和门叶状态仍有原说明中的推定或简化，不能称为全楼实测或完整街道复原。

129号这份静态候选证据早于A/B接入时的相机修复。后者前两轮技术通过、整组视觉未接受，修正后的A/B v3静态复验现已通过；129所属武康两楼目录生命周期已另行记录通过，不把A/B静态采集写作129已在新运行时重复全部视角检查。

## 下载

| 文件 | 用途 | 字节数 |
|---|---|---:|
| [原始 GLB](../../../assets/models/precise/14-13718-6695/xuhui-wukang-129/raw.glb) | 完整几何，190,926个三角形 | 15,002,212 |
| [网页压缩 GLB](../../../assets/models/precise/14-13718-6695/xuhui-wukang-129/web.glb) | 完整几何的 Meshopt 压缩版本 | 4,759,104 |
| [远景 LOD GLB](../../../assets/models/precise/14-13718-6695/xuhui-wukang-129/lod.glb) | 远景简化，83,716个三角形 | 2,751,684 |
| [可编辑 Blender](../../../assets/native/precise/14-13718-6695/xuhui-wukang-129/model.blend) | Blender 4.3.2 原生文件 | 21,341,124 |

所有单个文件均小于 **100,000,000字节**。完整 SHA256、模型与原生校准/视觉/几何/压缩审计的相对位置见 [delivery-record.json](delivery-record.json)。[原生校准视角预览](evidence/photo-perspective-v2.png)是已实际查看的渲染，不是HTML运行截图。

## 已完成的检查与范围

- 已对照Windmemories的2026年原图、Antigng的2017年原图及首版/修正版渲染，接受本轮三处修正：中央后退墙上方坡屋面、圆端侧后连接、相邻前墙连续处理。
- raw与网页GLB的三角形位置、材质、绕序和重数精确对应；最大法线角差约0.01530°，低于项目既有0.05°界限，法线不宣称逐字节相同。raw/web/LOD共270条记录窗口内部射线与30条相邻墙负控通过；这不是全部曲面或孔边的全量距离证明。
- 完整源码在临时安装布局中独立重建，阻断原staging/主项目读取与网络后仍得到相同raw，并重新封装得到四件资产相同SHA。native使用已核验原件复制；这次便携检查没有再次运行Blender。

后立面、隐藏屋顶深度、圆端半径与绝对尺度仍有推定；玻璃、瓦片、栏杆、门饰和设备细节存在简化。二楼圆端门扇的关闭模型状态与照片中的开门状态也不相同。不得把本包描述为全楼实测或光学材质复刻；原始单体检查记录对应当时范围；本次网页与目录验收范围见本页顶部v7状态。

## 来源与许可

模型几何按 **CC BY-SA 4.0** 声明；两张许可原图分别为 **Antigng（2017）** 与 **Windmemories（2026）**，均为 **CC BY-SA 4.0**。照片原字节保留在 `references/`，仅作几何/身份参考：raw、web、LOD和native的照片内嵌数量均为 **0**，没有强贴照片掩盖细节缺失。

原地图轮廓来自OpenStreetMap贡献者，经Overture Maps Foundation汇编，保留 **ODbL 1.0** 归属。原`w582319150@1`轮廓与源要素映射不因照片推定的曲面造型而改称精测数据。照片、地图、模型和代码许可分别见 [LICENSES.md](LICENSES.md)，不能混称CC0或套用代码许可。

## 源码和审计

[REBUILD_STANDALONE.md](REBUILD_STANDALONE.md)提供模型、相机、native与压缩封装的完整命令。`common/`为本栋冻结的本地副本；`native-wrapper/finish_native.py`只将`Preview_only`展示平面设为−0.01m，并要求显式指定`--candidate-root`，建筑地坪和几何不随之移动。原始单体 [SOURCE_FILES.json](SOURCE_FILES.json)保持原字节；新的 [source-package-files.json](source-package-files.json)列出这份完整交付源码和证据。

主要检查：[独立有限视觉复核](evidence/visual-review-v2.json)、[root视觉复核](evidence/root-v2-visual-review.json)、[原生几何绑定](evidence/native-build-report.json)、[校准相机运行](evidence/photo-camera-native-run.json)、[真实GLB洞口与位置检查](evidence/raw-independent-model-check.json)、[实际Three压缩对照](evidence/compression-geometry-check.json)、[raw/web/LOD解码与孔内采样](evidence/decoded-package-check.json)、[便携源与封装复建](evidence/portable-source-package-proof.json)、[封装记录](evidence/packaging-record.json)。

历史审计JSON中的原staging绝对路径和旧`output/`、`native/`文件名保留作来源记录；`delivery-record.json`给出本交付的相对定位，不要求读者拥有原工作目录。历史“等待验收”的字段保留原记录；后续实际网页证据由本页当前状态单独说明，不回写历史证明。
