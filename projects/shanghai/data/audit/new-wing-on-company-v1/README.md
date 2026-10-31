# 新永安大楼：模型、主图接入与 TODO 清理

[主地图直接查看](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=huangpu-new-wing-on-company&mode=overview) · [建模来源与范围](../../../source/precise/huangpu-new-wing-on-company/README.md) · [四件资产清单](../../../assets/models/candidates/huangpu-new-wing-on-company/manifest.json)

本轮制作南京东路627号新永安公司／七重天大厦主楼与后部外观。北端高塔、低楔形楼体、圆端、连续东北立面、宽檐退台、阶梯顶冠与无读数温度计均由几何构成。南京东路635号老永安保留为另一栋模型；跨街桥、邻楼、室内和屋顶高天线不在本件范围内。

## 资料和估计

[文献复核](documentary-review.json)记录官方建筑志的前部22层、后部8层及72米约束；[照片复核](photo-review.json)记录实际查看的六张公开照片。照片不作为纹理，也不随资产发布。门牌627／727、1932／1933／1936年及文献1400平方米与地图约2016平方米的口径差异保留，未擅自统一。

模型选取实体顶冠72米为高度端点，用前部13层、上塔7层、顶部2级体量解释22层；这些分段、平面、退距、窗格和隐藏构造均为估计。实际几何外包为46.067×59.174×72米，不是现场测量。背面与屋面未达到逐面照片复原。

## 冻结资产与实际检查

| 资产 | 字节 | 三角面 |
|---|---:|---:|
| 原始 GLB | 7,669,016 | 137,148 |
| 网页 GLB | 2,433,676 | 137,148 |
| 远景 GLB | 781,548 | 38,500 |
| 可编辑 Blender | 4,046,931 | 137,148（建筑网格） |

四件合计14,931,171字节，每件均小于100 MB，完整SHA见清单。[几何检查](geometry.json)与[打包检查](packaged.json)验证实际顶点、分别闭合的作者构件、12处表面射线、压缩后有向三角面等价及无图片嵌入。[原生检查](native.json)实际重开Blender，核对建筑网格并排除摄影棚。[独立审查](independent-model-review.json)另行解码近远景，核对六个高度截面及来源与范围。

[正面](native-front-v3.png)、[斜面](native-oblique-v3.png)、[背面](native-rear-v3.png)与[东北细部](native-ne-detail-v3.png)四张最终原生图均已实际查看，[查看记录](native-visual-review.json)绑定图像哈希。连续立面没有被低裙楼檐带横切，温度计位于实墙柱面，未添加虚构读数。

## 主地图接入

[定位复核](footprint-review.json)将新楼绑定唯一源对象 `building / 708d0e95-d551-414d-a3be-897a9fe2fb6b`，宏块 `14-13720-6694`、localId1275。锚点约为121.47443219、31.23688690，方位−15.763307672°，均为近似配准。真实解码后的原始、网页、远景水平外包一致；仅对自身源足迹应用1米有界配准余量，不扩大到邻楼。新模型与老永安保守外包仍相隔约8.14米。

[增量接入检查](global-integration-checks.json)确认原30个候选记录、旧定位及裁剪实现不变；新替换增加6个三角形，总62／128。目录由原40项加31项候选组成，共71项、16区，黄浦23项。两份README的模型查看链接均进入 `projects/shanghai/index.html`；同一清单生成精灵灯牌。原40项保留既有室外漫游，新楼提供全局俯瞰。

33项灯牌／镜头测试、5项资产增量测试与5项接入检查通过。[生成及目录复核](root-checks.json)另含7项导航与5项实际目录测试。320像素窄屏在密集时采用22×20像素编号灯牌，数字字体仍为12像素；仅在原24×20尺寸放不下时使用。

[实际网页检查](browser.json)与[六张截图的实际查看记录](browser-visual-review.json)已通过。资产检查页真实加载近远景及四项下载；主图在桌面与390像素手机上完整取景，近远景SHA、位置和邻楼分离均核对。320×568全城视图中71个编号灯牌可见、无重叠或界面遮挡；真实触摸第71牌后，名称、URL片段和中心均从老永安切换到新永安。该密集灯牌检查关闭阴影并临时移除地图边界以固定zoom8，默认主图截图保留阴影。无控制台错误、警告或HTTP失败。

## TODO 清理

已交付的25项制作任务及46项已登记模型不再显示在活动TODO；原始记录继续保留。7条已完成主楼退出历史名录待建列表，剩余1051条；仅部分完成的对象改为明确未做范围，新永安所在条目只保留跨街桥。

具名地图线索按 `(source_layer, id)` 精确匹配，原1036条中16条已关联交付模型，剩1020条。没有按相似名称直接删除。[独立TODO与目录检查](todo-directory-checks.json)确认原1058条历史登记、1036条具名记录、1038条道路线索及旧审计保留。下一项为南京东路720号新新公司历史主楼；其参考仍须逐项核对。

## 重建与复核

以下在仓库根目录执行。先安装[source/requirements.txt](../../../source/precise/huangpu-new-wing-on-company/source/requirements.txt)，另备Blender与gltfpack；`--gltfpack`、`--blender`替换为本机可执行文件路径。

```sh
python projects/shanghai/source/precise/huangpu-new-wing-on-company/source/build_model.py --out /tmp/new-wing-build
python projects/shanghai/source/precise/huangpu-new-wing-on-company/source/build_model.py --out /tmp/new-wing-build --lod
blender -b -t 4 --python projects/shanghai/source/precise/huangpu-new-wing-on-company/source/build_native.py -- --raw /tmp/new-wing-build/huangpu-new-wing-on-company-raw.glb --out /tmp/new-wing-build/huangpu-new-wing-on-company.blend --previews /tmp/new-wing-native --samples 20 --suffix=-v3
python projects/shanghai/source/precise/huangpu-new-wing-on-company/source/package_assets.py --raw /tmp/new-wing-build/huangpu-new-wing-on-company-raw.glb --lod /tmp/new-wing-build/huangpu-new-wing-on-company-lod.glb --native /tmp/new-wing-build/huangpu-new-wing-on-company.blend --out /tmp/new-wing-assets --gltfpack /path/to/gltfpack
python projects/shanghai/source/precise/huangpu-new-wing-on-company/source/verify_geometry.py --assets /tmp/new-wing-assets --out /tmp/new-wing-packaged.json --gltfpack /path/to/gltfpack --blender /path/to/blender
python projects/shanghai/tools/build_candidate_city_integrations.py --check
python projects/shanghai/tools/build_model_todo.py --check
python projects/shanghai/tools/build_landmark_directory.py --check
```

真实浏览器检查：[qa-browser.cjs](qa-browser.cjs)，需要Playwright、Chromium与提供本项目及稀疏资产的HTTP服务。设置 `NODE_PATH`、`MODEL_BASE_URL`、`CHROMIUM_PATH` 后执行 `node projects/shanghai/data/audit/new-wing-on-company-v1/qa-browser.cjs --run`。检查使用一个浏览器页面依次加载资产检查页、目录和主图，不重跑旧30个模型矩阵。原生文件和渲染像素可能受Blender、硬件和压缩工具版本影响，更新资产必须同步新哈希及有界配准合同。
