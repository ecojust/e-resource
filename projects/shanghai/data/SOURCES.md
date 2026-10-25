# 上海公共地理数据来源

本数据使用 WGS84 经纬度（EPSG:4326），与 OpenStreetMap / MapLibre 的地理坐标一致。未将高德等 GCJ-02 坐标直接用作地标定位。

## 16 区边界

- `districts.geojson`：通过 Nominatim 查询获得的 16 个 OpenStreetMap 行政区关系多边形，保留完整来源几何。每区附 OSM 关系编号、链接与范围。
- `districts-display.geojson`：上述几何与上海城市展示范围 `[120.8, 30.6, 122.25, 31.95]` 相交后的展示版本，仍包含全部 16 区。用于城市概览，避免远离上海主体的来源成员或宽阔海域使镜头缩小到全国尺度。
- `boundary-processing.json`：处理方法和受影响区的记录。静安、宝山来源关系含远离主体的独立多边形，浦东、崇明含较宽海域；本项目不额外断言这些成员的行政真实性，不将裁切称作官方边界修正。
- 这套边界来自开放社区地图，不是官方测绘或法律边界。原始关系与城市展示版本分开保留。

接口：`https://nominatim.openstreetmap.org/search`。查询时按每秒至多一次请求，使用可识别的应用 User-Agent。来源许可：OpenStreetMap 数据库 **ODbL 1.0**，署名 **© OpenStreetMap contributors**。许可说明：https://www.openstreetmap.org/copyright 。边界及其加工数据不受仓库代码 MIT 许可替代。

曾对阿里云 DataV 公开 GeoJSON 进行可用性调查，但其响应未明确标注独立再分发许可和坐标基准，因此最终交付没有使用或转载该几何数据。

## 街道、水体和建筑

浏览器地图来自 **OpenFreeMap / OpenMapTiles / OpenStreetMap**：

- 样式：`https://tiles.openfreemap.org/styles/liberty`
- 向量 TileJSON：`https://tiles.openfreemap.org/planet`
- 此次核对瓦片版本：`20261018_080001_pt`，源最大缩放级别 14，可由 MapLibre 在更高缩放下显示。
- 道路：`transportation` / `transportation_name` 图层；水体：`water` / `waterway`；建筑：`building`。
- 建筑立体高度字段：`render_height`、`render_min_height`；这些渲染高度可能由地图标签估算或使用缺省值，不代表每栋楼的实测高度。

OpenFreeMap 项目代码采用 MIT，但其地图数据库来自 OpenStreetMap，仍需按来源保持归属信息。建议保留 TileJSON 自带的标准署名：**OpenFreeMap · © OpenMapTiles · Data from OpenStreetMap**。服务条款与说明：https://openfreemap.org/ 及 https://openfreemap.org/tos 。地图在运行时联网加载，不是随仓库离线复制的全市瓦片包。

本次只下载 16 个缩放 14 的样本瓦片用于验证，总量约 1.45 MB，并限制至多 4 个并发请求。样本不是全市统计。数据中各区 `sampleCoverage` 记录的是入场点对应样本瓦片的要素数量。

**建筑覆盖有明显差异**：中心区域有较多建筑轮廓；部分郊区和农村样本仅含少量建筑。项目不会用虚构楼宇填补这些空白，也不声称提供全市每栋建筑的完整实景模型。

## 漫游起点

`districts.json` 的 `walkStart` 为对应行政区内、距离参考中心较近的真实向量道路几何点。优先选择步道，未取得步道时选择可见的服务道路或普通道路；已排除瓦片中标注为禁止步行、私有、隧道或非地面层的候选。

- 起点含瓦片编号、道路分类与匹配距离，可以复核。
- 浦东起点选在陆家嘴；崇明起点选在通过 OSM 验证的城桥镇附近，避免落在全区几何中心的偏远地带。
- 起点用于虚拟场景初始化，不是现实世界步行安全或通行许可的保证。

## 地标定位

`landmark-anchors.json` 的经纬度来自实时 Overpass 查询的 OSM 建筑轮廓中心；江海关大楼使用同名景点节点。均附 OSM 对象编号及链接。

同时查询了 Wikipedia 坐标进行交叉核对；最终以 OSM 对象位置对齐同源地图。模型外形为程序化近似，定位依据与建筑外形精度分开记录。

查询端点：`https://overpass-api.de/api/interpreter`。OpenStreetMap 数据仍适用 ODbL 1.0；地标名称、高度及来源链接在锚点文件中记录。

## 全市建筑补充：Overture Maps

为避免仅使用 OSM 时上海郊区建筑稀疏的问题，页面还加载 Overture Maps 官方建筑 PMTiles。该来源整合了真实的 OpenStreetMap 和 East Asian buildings 建筑轮廓，城区及郊区密度显著高于单独的 OSM 样本。

- 2026-10-21.0 版本：`https://tiles.overturemaps.org/2026-10-21.0/buildings.pmtiles`。
- 来源建筑图层：`building`、`building_part`。
- 全市数据由页面在线按需读取；本地另提供每区漫游起点周围约 1 km² 的 GeoJSON 和 GLB 样本，包含全部 16 区。
- 本地 16 个模型共表示 8,294 个建筑/分部：91 个有来源高度，271 个有楼层数并按 3.2 米/层估算，其余 7,932 个采用统一 12 米可视化默认高度。这一高度不是实测值。
- Overture 建筑主题及其衍生数据遵循 ODbL 1.0；需要保留 © Overture Maps Foundation、© OpenStreetMap contributors 和逐要素原始数据归属。East Asian buildings 数据由 Qian Shi 等发布（2023），原始许可为 CC BY 4.0： https://doi.org/10.5281/zenodo.8174931 。
- 许可总览：https://docs.overturemaps.org/attribution/ 。

正式重建应从最新 STAC 版本选择数据，因为旧版公共 PMTiles 可能在保留期后过期；本地 GeoJSON 和 GLB 样本已保存，不依赖旧版服务。
