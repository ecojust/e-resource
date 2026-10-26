# 普通小建筑逐栋复原源码

当前接入HTML的是[青浦朱家角北大街222号民宅前楼](qingpu-beidajie-222/DELIVERY.md)。它与15栋外滩、4栋陆家嘴合计20栋；并不把1,796,419个参数细化要素称为逐栋照片复原。[武康路129号独立下载包](xuhui-wukang-129/DELIVERY.md)已提供GLB与Blender及完整便携源码；它尚未加入HTML，也未通过网页场景验收，未计入本版20栋。

222仅覆盖两层三开间临街前楼，不含邻铺226号或未知后进。真实开口、开放木廊、木格、门叶、有限厚度灰瓦和简化石狮均为几何；中央草书匾保留原图，右门为统一估计玻璃材质。后部、精细雕刻、格数和高度仍有推定，模型不提供真实室内。

| 建筑 | 网页GLB | 原始GLB | Blender原生 | 远景GLB |
|---|---:|---:|---:|---:|
| 北大街222号 | [8,560,920](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/web.glb) | [18,154,244](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/raw.glb) | [29,405,268](../../assets/native/precise/14-13701-6700/qingpu-beidajie-222/model.blend) | [6,466,884](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/lod.glb) |

## 来源分支与许可

足迹来自Overture中的Zenodo／East Asian Buildings（Qian Shi等，2024-11-01；底层CC BY 4.0，DOI10.5281/zenodo.8174931），保留聚合数据的ODbL署名；它不是OSM building way。OSM只用于门牌与街桥身份核对。冻结原四点轮廓、地理锚点、macro14-13701-6700／localId502保持，同near其余27要素保留。

2022图为钉钉、CC BY-SA 4.0；2016结构参考为Fayhoo、CC BY-SA 3.0。带中央牌匾照片的raw、web与LOD模型按CC BY-SA 4.0发布，三者各保留一张原图；远景91,246三角形不能按“无图LOD”记账。源码MIT、字体OFL，原照片和轮廓继续保留各自许可，见[COPYRIGHT](qingpu-beidajie-222/COPYRIGHT.md)。

## 重建与验证范围

发布布局为`source/precise/{qingpu-beidajie-222,common}/`；保留白名单输入、原JPEG、字体与相邻common后，可离线运行该栋`build_model.py`和`validate_model.py`。不需重新查询地图或以POI代替真实轮廓。源码README保留生成阶段记录；当前交付状态以DELIVERY与本轮审计为准。

本轮三栋HTML技术检查通过，共15组采集、6份近／远景资产核验；root实际查看10张截图并接受有限接入表现。另有独立目录检查：生产20项静态记录复用，以及仅测试响应移除222后的19项动态加入／退出／返回和索引SHA失败保留基线。目录另经root实际图像复核，包含动态退出后返回的叠楼回归视图。三栋静态采集与运行时修复后的回归范围分别记录，不把旧图冒充全部修复后重跑；这不重跑全部20栋或全城逐栋核验。 见[本轮审计](../../data/audit/precise-buildings-v6/release-next/README.md)。

檐口7.54m、屋脊9.20m是条件照片比例推定；原GHSL8.579m为100m栅格均高，不是实测。尺寸小数、封闭网格与导出一致性不能证明现场测量精度。2016与2022不同门叶状态也不能证明某年永久改建。
