# 外滩17/18号对面绿化候选 · v4.5

本包保留绿化来源版本 v4.5，已通过统一的 `bund-streets` owner 接入主项目 v5 街景。这是一组有照片依据的近景绿化：两条既有草带内的 **南4、北3棵稀疏乔木序列**、斜撑和短草叶。依据是 Gary Lee Todd, Ph.D. 于 **2010-09-18** 拍摄的 CC0 航拍；不代表2026年精测现状。南床后三棵根部不同程度遮挡，尤其最后两棵树位为树干延长线推定，必须连同证据标记审阅。未补种无定位依据的额外树列或灌木墙，不断言树种。

- `data/photo-controls-overlay.svg` 将草带四角与7个根点作为独立矢量图层叠在原图上。绿点为清楚根部；黄点为被遮挡的估计位置。原JPEG字节未改。
- `source/photo-controls.json` 给出原图像素、可见程度、估计尺寸和误差输入；`data/greenery-v4.5.json` 给出地理位置、局部坐标和两床单应矩阵。四个控制角点的精确拟合只说明算法一致，**不是独立相机标定**。3像素角点及2–5像素纵向根点扰动，在狭窄床的透视下可产生约0.8–1.9m的位置敏感度；这不是实测置信区间。
- 草带平面严格复用冻结的OSM外边界，源关系2142077、外圈way160033684。现有2026 OSM bbox没有自然树点，但这不等于没有树。
- 2019年 Balon Greyjoy 的两张 CC0 高空照片只显示附近仍有道路侧树冠；不足以确认同7棵树的存续或2026形态。2016隧道图为室内，已明确排除。完整来源、许可和SHA见 `references/SOURCES.json`。

## 候选与性能

网页生成器 `source/street-greenery.js` 只有8个 InstancedMesh 批次，7,135个实例，329,862个渲染三角，几何与实例缓冲合计744,708字节。叶片是弯折几何轮廓，树冠由分枝和不规则疏密叶簇组成；无下载树模型、无透明贴片、无外部贴图、无额外光源或独立动画循环。6,575组短草叶在原有草面上补充近景轮廓，约2.5–7.5cm高，不替换已有草坪材质。

`output/bund17-18-greenery-candidate.glb` 是同一生成器烘焙出的独立自包含下载模型（35.63MB）；`output/bund17-18-greenery-web.glb` 为保留全部三角和位置的 Meshopt 版本（约13.56MB）。两个文件均严格低于100,000,000字节。网页优先采用实例模块，不再额外加载这两个下载模型。最终字节和SHA见 `output/asset-files.json`。

运行 `source/render_preview.py` 可生成 `output/greenery-overview.png` 和 `output/north-near.png` 的 Blender 形态预览；它们为重建产物，不随当前模型包提供。预览地面、石边是简单参照物，不在 GLB 内。主项目集成状态与浏览器验收记录见 [`data/bund/REALISM_V5.md`](../../../../data/bund/REALISM_V5.md)。

## 统一归属 bund-streets

`createStreetGreenery({ THREE, data, origin: [121.4862,31.2385], bedGroundHeights })` 返回 `{group,stats,setActive,updateDistance,dispose}`。`group` 是 **bund-streets 模型局部米制坐标**，位置0、缩放1，X东/Y上/Z南；附加到已成功加载的街景模型Group后继承其地理变换，不要再独立放进全局scene，也不要重复应用Mercator缩放。

```js
const vegetation = await createStreetGreenery({THREE, data:greeneryData});
streetObject.add(vegetation.group);
```

安装路径建议：模块放 `src/street-greenery.js`，数据放 `data/bund/greenery-v4.5.json`。若未显式传data，模块在该路径加载。由街景owner统一控制显示、缓存、光照、资源释放；不要再注册独立model记录。实例网格可被现有 `disposeModel` 正常释放；如果使用返回的`dispose()`，它幂等，不要另让owner重复释放同一资源。

当前基准为既有平面草顶Y=.09m。`bedGroundHeights:{south:height,north:height}` 可整体调整相应床的树、支撑、草叶高度，值是**新的局部绝对Y**，不是增量。整个床必须随同地形一致调整。`data/greenery-ground-sidecar.geojson` 给出树根地理点、0.16m树干半径、0.90m支撑包络、2.25m支撑连接高度，供漫游碰撞与地面接触复核。默认位置下，CPU已检查每个草叶与支撑的实际变换顶点位于草床内部；树冠允许自然外伸。没有生成浮空树或改动原道路/草床。

`updateDistance(distanceMetres)` 在65m外只隐藏短草实例；不隐藏树干或换成不同轮廓的树冠。可不调用它，由owner只在步行近景可见时启用整组。

## 离线重建与核验

需Python/numpy/shapely、Node、现有项目的vendored Three/GLTFLoader/Meshopt，以及gltfpack。原始2010 JPEG仅供校验和证据查看，不用于材质。所有源文件均只写本包data/output，不访问或更改主项目数据。

```sh
python source/generate_greenery.py
node source/validate_export.mjs /path/to/shanghai_project
python source/compress_candidate.py --project /path/to/shanghai_project --gltfpack /path/to/gltfpack
blender -b -t 4 --python source/render_preview.py
```

`output/greenery-validation.json` 包含有限顶点、实际草/支撑顶点落床、内存、资源幂等释放检查；`greenery-compression-validation.json` 使用项目真实GLTFLoader/Meshopt解码验证压缩后全部329,862个有向三角位置严格一致。树根定位仍只有上述照片估计精度，不能拿几何软件通过当作真实地理精度证明。

## 许可

原创代码、枝叶/支撑几何MIT；由OSM草床导出的定位数据按ODbL-1.0并注明© OpenStreetMap contributors。2010和2019原参考照片分别保留作者与CC0来源；被排除的2016照片为Anagoria、CC BY 3.0。未将任何照片裁剪图用于纹理。GLB内嵌相应来源、年代和copyright，压缩后恢复这些字段。`inspection/` 中的局部放大仅用于判读，不作为改写后的原图发布。
