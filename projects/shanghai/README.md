# 上海漫游 · Shanghai Explorer

独立的上海地图与第三人称漫游项目，覆盖 **全部 16 个区**，不包含其他项目的模型。使用真实行政区边界、道路、水系和建筑轮廓，结合可下载的街区 GLB 与主要地标模型。

![上海城市俯瞰](assets/previews/overview.png)

## 打开页面

[打开在线预览](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html)（第三方静态托管，首次出现提示时点击 **Open the page**）。

无需 npm 安装或构建。在本项目目录启动一个静态服务器：

```sh
python -m http.server 8000
```

然后打开 **http://localhost:8000**。页面入口是 [index.html](index.html)。ES 模块与 GLB 通过 HTTP 加载，请不要直接双击 HTML 使用 `file://` 打开。

页面需要联网请求公开地图瓦片；界面代码、地图引擎、地标和本地街区模型均随项目附带。支持桌面与移动端 WebGL 2 浏览器。

## 已包含的内容

| 内容 | 覆盖与细节 |
|---|---|
| 上海全域地图 | 黄浦、徐汇、长宁、静安、普陀、虹口、杨浦、闵行、宝山、嘉定、浦东新区、金山、松江、青浦、奉贤、崇明全部 16 区；真实道路、水系、区域边界和区级跳转 |
| 全市在线建筑 | Overture `building` / `building_part` 按视野加载真实轮廓，补充外围区域的建筑覆盖；有来源高度时使用其高度，缺失时估算 |
| 16 份本地街区模型 | 每区选择已核验道路起点附近约 **1 × 1 公里**，共 **8,294 个建筑或部件**；页面靠近街区时加载本地 GLB，远离时释放或隐藏 |
| 5 个独立地标 | 东方明珠、上海中心大厦、上海环球金融中心、金茂大厦、江海关大楼；米制、地理定位、幕墙/层叠结构/球体/钟面等可辨认细节 |
| 第三人称漫游 | 可见人物、步行动画、镜头跟随、键鼠/触屏、建筑与水面碰撞、位置跳转及安全落点检查 |
| 可复现源码 | Blender 地标生成脚本、PMTiles 真实轮廓提取脚本、街区 GLB 生成脚本、大小与格式检查脚本 |

**全市在线地图与本地街区样本是不同层次。** 16 份 GLB 并不声称离线保存了每个区的全部建筑；完整城市范围通过在线矢量地图按需浏览。本地样本依据真实轮廓制作，不是随机生成的城市方块。

## 操作

- **城市俯瞰**：拖动平移、滚轮缩放；导航面板可选择 16 个区或地标，“查看全市”返回全域。
- **第三人称**：`WASD` / 方向键行走，`Shift` 加速，拖动场景转向，滚轮调整镜头距离。
- `Q` / `E` 旋转镜头，`R` 重置镜头；手机使用左侧摇杆，按住“加速”，在地图上拖动转向。
- `/` 聚焦地点搜索；右上角可收起导航面板及查看数据说明。
- 建筑和水面会阻挡人物；跳转后会依据已加载的道路与建筑数据检查落点。地图瓦片尚未加载时，检查可能稍后完成。

## 下载模型

### 地标

- [东方明珠 GLB](assets/models/oriental-pearl.glb) · 468 m
- [上海中心 GLB](assets/models/shanghai-tower.glb) · 632 m
- [环球金融中心 GLB](assets/models/swfc.glb) · 492 m，顶部开口为实际贯通几何
- [金茂大厦 GLB](assets/models/jin-mao.glb) · 模型高度 420 m
- [江海关大楼 GLB](assets/models/customs-house.glb) · 90 m
- [陆家嘴四地标 Blender 场景](assets/native/shanghai-landmarks.blend)

### 16 区街区

见 [街区下载清单](assets/districts/README.md) 与 [逐模型元数据](assets/districts/metadata.json)。每个街区 GLB 都以自身经纬度锚点为原点，坐标为 **X 向东、Y 向上、Z 向南，单位为米**。

所有本地 GLB 均小于 **1 MB**，项目最大文件约 **5.1 MB**。采用比 GitHub 100 MiB 更保守的 **100,000,000 字节**单文件上限；没有依赖 Git LFS。

## 精度与数据来源

- 坐标统一为 **WGS84 / EPSG:4326**。地标位置核验自 OSM 对象，而非把不同坐标系混用；来源见 [地标锚点](data/landmark-anchors.json)。
- 行政区边界来自 OSM / Nominatim。保留[完整原始边界](data/districts.geojson)，另有[城市主体展示边界](data/districts-display.geojson)，避免 OSM 关系中远离上海的离散成员把全市视图拉至外省。处理范围与记录见 [数据说明](data/SOURCES.md)。
- 道路、水系和文字标注通过 OpenFreeMap / OpenMapTiles 获取；建筑主体来自 Overture Maps。核验的建筑版本为 **2026-10-21.0**。该服务历史版本保留时间有限，固定版本失效时页面尝试官方最新 STAC 版本，再回退 OSM 建筑数据。
- 建筑轮廓大量来自 Qian Shi 等的 **East Asian Buildings**（[DOI:10.5281/zenodo.8174931](https://doi.org/10.5281/zenodo.8174931)）。模型包含真实轮廓及孔洞，但不等同于摄影测量或建筑施工模型。
- 本地 8,294 个建筑/部件中，**91 个采用来源高度、271 个按楼层数 × 3.2 m 估算、7,932 个采用明确标注的 12 m 默认高度**。不可将缺失高度的街区视作实测天际线。
- 五个地标是根据公开外形资料制作的几何模型；幕墙、细部与裙房存在概括处理。页面不包含建筑内部、室内通行或精确道路高程，也不是测绘、导航或工程成果。

详见 [Overture 数据与覆盖说明](data/overture/README.md)、[原始样本与来源](data/neighborhoods/manifest.json)。

## 检查与重新生成

检查文件上限、GLB 结构和 16 区完整性：

```sh
python tools/check_assets.py
node tests/walk-controller.test.mjs
```

根据附带的真实轮廓重新生成街区模型：

```sh
python -m pip install numpy mapbox-earcut
python source/districts/build_district_models.py
```

重新提取官方最新建筑轮廓（需要联网）：

```sh
python -m pip install pmtiles mapbox-vector-tile shapely
python source/districts/fetch_overture_neighborhoods.py
```

重新生成地标（Blender 4.3 或兼容版本）：

```sh
SHANGHAI_OUTPUT_DIR=./generated blender --background --python source/landmarks/export_landmarks.py
CUSTOMS_OUTPUT_DIR=./generated/landmarks blender --background --python source/landmarks/customs_house.py
```

生成的 `generated/landmarks/*.glb` 可复制至 `assets/models/`。界面使用本地固定版本的 MapLibre GL JS 5.24.0、Three.js 0.180.0 与 PMTiles 4.3.0。

## 许可

- 本项目界面、控制器及原创地标生成代码采用 [MIT](LICENSE)。
- OSM、Overture 建筑与派生街区数据库/模型采用 **ODbL 1.0**，须保留相应来源署名；East Asian Buildings 原贡献源采用 **CC BY 4.0**。具体逐要素来源随 GeoJSON 保存。
- MapLibre、Three.js、PMTiles 的许可见 [licenses/](licenses/)。底图上的服务与数据署名保留在页面右下角。
- 地图、建筑数据、第三方库不因放入本仓库而改为 MIT；以上各类资源以各自许可为准。
