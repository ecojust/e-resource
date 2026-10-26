# 武康路210号精细模型交付

这一模型保留真实照片中的拱形阳台、弧面入口、退进上层、上下三联窗、红檐齿饰与分层瓦屋面。原生有限范围外观复核、实际GLB开孔/玻璃嵌框校验、网页解码与LOD洞口抽查均通过。网页场景登记和浏览器验收由集成任务另行记录；本包没有修改导航。

| 文件 | 大小 | 用途 |
|---|---:|---|
| [原始GLB](../../../assets/models/precise/14-13718-6695/xuhui-wukang-210/raw.glb) | 5,785,688B | 完整未压缩几何 |
| [网页GLB](../../../assets/models/precise/14-13718-6695/xuhui-wukang-210/web.glb) | 2,393,848B | Meshopt压缩；84,670三角，位置精确保持 |
| [远景LOD](../../../assets/models/precise/14-13718-6695/xuhui-wukang-210/lod.glb) | 1,462,268B | 47,218三角；简化后洞口抽查通过 |
| [Blender源文件](../../../assets/native/precise/14-13718-6695/xuhui-wukang-210/model.blend) | 9,272,752B | 可编辑几何，预览相机/灯光在Preview_only集合 |

[原生预览](audits/native-v3-preview.png) · [重建说明](README.md) · [许可与照片署名](LICENSES.md) · [完整来源清单](SOURCE_FILES.json)

主体只对应原城市local563 / OSM w790826981@1。南侧982、后侧975与同微块另外23要素保持；地图主体匹配具有证据支持，但不是地籍边界/测绘定论。照片比例高度约8.9m，玻璃/灰浆色和不可见后侧推定均有明确记录，未把GHSL均高当实测。

web保留原始位置/材质/绕序/三角重数，法线最大角差0.01791°，在既有0.05°标准内；不宣称法线字节一致。raw/web/LOD共285个窗洞和拱门采样射线及邻墙负控通过，LOD边界差为0；采样不能代替所有曲线/全表面Hausdorff证明。三种GLB均0图像，照片仍作为有署名、CC BY-SA4的参考随源码保留。

独立目录重建raw逐字节一致；仅使用包内封装源码/测量helper和已声明gltfpack1.3.0重新生成四资产也逐字节一致。该次proof复制既有native，没有再运行Blender；重新保存.blend不承诺容器SHA相同。

审计：[实际解码](audits/decoded-package-check.json)、[实际原始GLB](audits/actual-glb-audit.json)、[模型便携重建](audits/portable-rebuild-proof.json)、[封装便携重建](audits/portable-full-package-proof.json)、[原生有限视觉复核](audits/native-v3-visual-review.json)、[root复核](audits/root-native-v3-visual-review.json)。

本包只提供该栋四资产及独立源码。注册器/街面/导航/全城宏数据不在安装范围内。
