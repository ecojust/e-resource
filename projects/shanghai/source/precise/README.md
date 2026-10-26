# 街区建筑逐栋复原源码（v8）

新增第5栋：虹口多伦路59号鸿德堂。已完成本版原生、网页及目录生命周期的有限验证；[当前应用范围](../../data/audit/precise-buildings-v8/hongde/README.md)，与下方保留的v7历史记录分开。

| 建筑 | 网页GLB | 原始GLB | 远景LOD | Blender |
|---|---|---|---|---|
| [鸿德堂](hongkou-hongde-church/CURRENT_STATE.md) | [10,619,436字节](../../assets/models/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church-web.glb) | [27,113,064字节](../../assets/models/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church-raw.glb) | [5,212,724字节](../../assets/models/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church-lod.glb) | [39,953,968字节](../../assets/native/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church.blend) |

四件文件均低于100,000,000字节。2024年可见配置结合2014年白天结构参考，原照片均为CC BY-SA 4.0；图像未嵌入模型。保留原OSM/Overture四角轮廓与唯一源对象，10个本地邻楼保留。后部、绝对高度和细小构造仍有推定。[独立交付记录](hongkou-hongde-church/DELIVERY.md)保留制作阶段的历史状态，当前接入状态以上述应用证明为准。

## v7四栋记录（历史保留）

以下“本批”“当前”等词对应v7；各项原模型下载与历史证明保持。

本批将武康路129号、210号和北大街208–212号茶楼接入HTML，与已发布的北大街222号组成4栋普通小楼。129号已有单栋静态候选网页验收；210号与茶楼v3的实际原生斜视图已由root复核接受，两栋v3静态网页及全部11张root图像复核也已通过。候选两宏普通目录均有本批实际验证；新启动包完成归档及青浦代表宏实际解压运行，未重跑武康ZIP浏览器，也未沿用上一版20项报告。

| 建筑 | 当前可确认状态 | 下载与完整来源 |
|---|---|---|
| 青浦北大街222号民宅前楼 | 已在v6.1接入；本批保留 | [DELIVERY](qingpu-beidajie-222/DELIVERY.md) |
| 徐汇武康路129号住宅 | 独立GLB/Blender已发布；21项候选中的单栋静态网页验收通过，本批已接入，后续武康整宏目录另验通过 | [DELIVERY](xuhui-wukang-129/DELIVERY.md) |
| 徐汇武康路210号住宅 | v3原生、静态网页及所属整宏目录生命周期通过 | [DELIVERY](xuhui-wukang-210/DELIVERY.md) |
| 青浦北大街208–212号茶楼前楼 | v3原生、静态网页及所属整宏目录生命周期通过 | [DELIVERY](qingpu-beidajie-208-212/DELIVERY.md) |

下表为实际封装文件，链接采用最终项目相对位置；资产已随第一应用提交发布。16件模型文件均严格小于100,000,000字节。

| 建筑 | 网页GLB（字节） | 原始GLB（字节） | 远景LOD（字节） | Blender（字节） |
|---|---:|---:|---:|---:|
| 北大街222号 | [8,560,920](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/web.glb) | [18,154,244](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/raw.glb) | [6,466,884](../../assets/models/precise/14-13701-6700/qingpu-beidajie-222/lod.glb) | [29,405,268](../../assets/native/precise/14-13701-6700/qingpu-beidajie-222/model.blend) |
| 武康路129号 | [4,759,104](../../assets/models/precise/14-13718-6695/xuhui-wukang-129/web.glb) | [15,002,212](../../assets/models/precise/14-13718-6695/xuhui-wukang-129/raw.glb) | [2,751,684](../../assets/models/precise/14-13718-6695/xuhui-wukang-129/lod.glb) | [21,341,124](../../assets/native/precise/14-13718-6695/xuhui-wukang-129/model.blend) |
| 武康路210号 | [2,393,848](../../assets/models/precise/14-13718-6695/xuhui-wukang-210/web.glb) | [5,785,688](../../assets/models/precise/14-13718-6695/xuhui-wukang-210/raw.glb) | [1,462,268](../../assets/models/precise/14-13718-6695/xuhui-wukang-210/lod.glb) | [9,272,752](../../assets/native/precise/14-13718-6695/xuhui-wukang-210/model.blend) |
| 北大街208–212号茶楼 | [4,593,804](../../assets/models/precise/14-13701-6700/qingpu-beidajie-208-212/qingpu-beidajie-208-212-web.glb) | [13,863,092](../../assets/models/precise/14-13701-6700/qingpu-beidajie-208-212/qingpu-beidajie-208-212-raw.glb) | [2,669,664](../../assets/models/precise/14-13701-6700/qingpu-beidajie-208-212/qingpu-beidajie-208-212-lod.glb) | [21,180,492](../../assets/native/precise/14-13701-6700/qingpu-beidajie-208-212/qingpu-beidajie-208-212.blend) |

210保留南侧弯曲铁栏阳台、中部凹门厅、北侧三联窗和红檐瓦顶，v3补闭高低屋面交接；茶楼保留三砖拱、开放木廊、实体栏杆与灯笼，v3修正竖牌位置、字形比例和屋面搭接。两栋各完成一张原生斜视图复核；后续v3网页覆盖近景、斜视、LOD、返回及替换状态，共11张root实际核图。它不是全方向外观或全城逐栋验收。

前两轮A/B网页技术通过但整组视觉未接受，失败报告保留。相机缓存/近距限制与普通楼水平投影修正后的v3正式复验通过；不删除对街邻楼，也不把旧技术通过改写为旧视觉成功。

129与210保留Overture收录的OSM来源轮廓；222和茶楼的轮廓来自East Asian Buildings／Zenodo，不能标作OSM建筑way。每栋只替换明确的源对象，不按地址院落或半径删除邻楼。129、210两期照片均为Antigng与Windmemories的CC BY-SA 4.0参考；222使用钉钉2022年CC BY-SA 4.0和Fayhoo2016年CC BY-SA 3.0资料；茶楼使用Fayhoo的CC BY-SA 3.0历史照片，EXIF与页面拍摄日期冲突保留说明。各自模型、数据、代码和字体许可依交付声明分别保留，不能统称CC0。

新增210参考：[Antigng 2017](https://commons.wikimedia.org/wiki/File:%E6%AD%A6%E5%BA%B7%E8%B7%AF210%E5%8F%B7%E4%BD%8F%E5%AE%85.jpg)、[Windmemories 2026](https://commons.wikimedia.org/wiki/File:20260209_210_Wukang_Road.jpg)；茶楼参考：[Fayhoo原图](https://commons.wikimedia.org/wiki/File:Zhujiajiaojulebuchalou.jpg)。茶楼原图EXIF为2016-02-07，页面描述为2013-09-07，未强行统一，也不据此声称2026现状。

222中央牌匾保留原照片；129、210与茶楼当前候选未嵌入照片纹理。后部、绝对高度、雕饰、材料及部分门窗状态仍为推定或简化，不提供经过核验的真实室内。每栋依各自REBUILD保留冻结本地依赖；历史源码中的候选状态由当前DELIVERY说明补充，不改写历史审计。

全城1,796,419个建筑及部件要素未逐栋完成照片核对。历史v6.1验证见[上一版审计](../../data/audit/precise-buildings-v6/release-next/README.md)；本批范围见[v7审计](../../data/audit/precise-buildings-v7/release/README.md)。
