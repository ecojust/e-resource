# 武康路210号二层住宅：照片依据候选

本包重建照片可见的南侧拱窗铁艺阳台、中央凹进上层与弧面入口、北侧上下三联窗、分层红檐和坡瓦屋面。它是可独立重建的建筑模型，尚未登记到HTML导航，原生渲染与网页验收由集成任务另行记录；这里不把几何检查等同于视觉验收。

主体对应既有 Overture / OpenStreetMap `w790826981@1`，城市 macro `14-13718-6695`、local ID `563`。来源轮廓完全保存在 `geometry-input.json`。官方名录、两期照片中的210门牌、临街朝向和南侧院墙/后屋关系共同支持这个**有条件的主楼匹配**，不是地籍地址连接或外墙实测。南接982、后侧975及同微块另外23个要素保持原状，不能按院落或半径一起删除。

## 离线重建

使用 Python3.12、`requirements.txt` 中的 NumPy/Shapely。下面的两个命令从本目录执行；输出目录可换到任意可写路径。

```sh
python build_model.py --output output
python check_model.py --output output
```

几何构建只读取本目录下的 `geometry-input.json`、`calibration-model.json` 和 `common/`，不访问网络、原主项目、全城瓦片或照片。照片是人工几何参考，未作为贴图嵌入，不需要下载纹理。`freeze_source.py` 是最初来源冻结的可追溯工具，重新执行它需要完整原城市数据与匹配清单；它不是重建本模型的前置步骤。冻结器要求在主项目之外的独立源码副本运行，以免重写已安装的来源记录；常规重建只运行上面的build/check两步。

## Blender输入

原始输出为 `output/xuhui-wukang-210-raw.glb`。坐标为glTF `[east,up,-north]`，米制，地面 **0m**，基础最低点约-0.12m。附带脚本的预览地面固定在-0.01m，不把基础底面误认为街道地面。

```sh
blender -b --python-exit-code 1 --python common/blender_finish.py -- \
  --glb output/xuhui-wukang-210-raw.glb --output native --render \
  --view-azimuth 129.5 --view-elevation 11 --width 1400 --height 1100
```

正面方位104.5348°；129.5°斜视可见南侧阳台体与中央凹进。另可采用79.5°反向斜视查看北侧。脚本生成可编辑 `.blend`、预览PNG和绑定输入SHA的JSON；这些命令说明不代表本包作者已运行Blender或验收渲染。

## 精度与细节范围

- 映射正面宽14.245051m，但原地图可能沿屋檐描绘，不能当现场测量值。
- 高度、退进、窗宽和瓦片尺寸来自照片比例推定。结构屋脊基准约8.77m，包含瓦盖/脊盖的实际模型最高点约8.89m；整体高度不确定量约1m，未使用GHSL100m栅格均高19.848m作为这栋房屋高度。
- 窗是墙面的真开孔，有连续洞口返回面。玻璃厚20mm，前面退离框前22mm，位于80mm框厚内。弧面门厅也是真拱孔。
- 瓦片长向随坡度，坡向搭接60mm；相邻排实体高差17.1mm、瓦身厚12mm，避免把重叠区域放在同一平面。侧折边和独立脊盖均有实体。
- 铁艺腹部弯杆、卷饰、碗形托底和三只多边形壁挂花盆有据简化。窗格细节部分受树和反射遮挡，仍是近似。
- 后立面无清楚照片，采用闭合的简单墙体和推定屋面连接，不凭空增加装饰窗。材料为估计PBR色/粗糙度，不宣称照片级表面、真实光学玻璃或测绘模型。

`evidence/photo-observations.json` 标记原图像素观察区域；它们不是相机标定矩阵，也不作为整面贴图UV。2026 Commons文件实际1800×1200，EXIF保留6000×4000相机声明，不能将两者混用。2017原图保留EXIF6。

## 审计和文件范围

构建输出含每个实体的FLOAT32闭合边配对/正体积检查、实际GLB窗洞射线与邻墙负控、实际玻璃嵌框深度、有限值/法线和单文件100,000,000B门槛。发布白名单见 `SOURCE_FILES.json`，原图字节不变。目录外 `research/`、`reference-only/`、历史输出和缓存不属于可公开源码包；尤其不发布私有航拍，也没有据它描线或制贴图。

## v3屋面交接修正

主任务实际渲染发现北侧高翼与中屋面之间敞口，v3补齐两翼可见前return之后的无窗内侧墙与红檐连续段。原4,937个部件的顶点、三角、材质、标签完整digest不变，只增加10个闭合实体；没有移动照片可见窗洞、屋面、檐高或源轮廓，也没有推造后段窗位。新增红檐避开旧梁50mm外延，从1.17m深度接续并采用精确长度，避免正面积共面重叠。修正的实际GLB与实体检查再次通过，旧模型/原生预览保留于研究历史。视觉复验单独记录，不能用这段几何说明代替。

## 封装与当前交付

当前v3原生有限复核已通过；查看 [DELIVERY.md](DELIVERY.md) 获取四资产下载、原生预览和审计链接。完整封装工具及测量helper包含在 `packaging/`，无需外滩共享目录；额外依赖与WASM哈希见 `packaging/dependencies.json`。以下输出必须尚不存在，`.blend` 使用前述native步骤生成或下载交付的源文件。

```sh
python packaging/package_precise_building.py \
  --spec packaging/package-input.json \
  --raw output/xuhui-wukang-210-raw.glb \
  --native /absolute/path/to/model.blend \
  --project packaging/measurement-project \
  --shared-helper packaging/package_building.py \
  --gltfpack /absolute/path/to/gltfpack \
  --output /absolute/path/to/new-plan/package
node packaging/check_decoded_package.mjs \
  /absolute/path/to/shanghai-project /absolute/path/to/new-plan /absolute/path/to/this-source
```

最后一条使用公开项目随附的Three/GLTFLoader/Meshopt CPU解码，不启动浏览器。运行几何与封装重建无需这些JS依赖。Python封装的zstandard用于读取压缩Blender文件头。
