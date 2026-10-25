# 地标排除审计输入

这些文件用于离线复核精细地标替换的 Overture UUID，均低于 100 MB。

- `landmark-candidate-features.geojson`：五处地标附近 9 个原始瓦片中的 22,270 个要素；仅用于查找 OSM way 对应的主楼及记录海关附近保留对象。
- `customs-osm-footprints.geojson`：海关周边 OSM 建筑足迹，替换范围限定在 way `178407318` 的临江前楼。
- `landmark-osm/*.json`：上海中心、东方明珠、环球金融中心、金茂大厦的 OSM way/full API 快照，含引用节点坐标。
- `portable-exclusions-validation.json`：发行版脚本从完整 raw 快照重建并与原排除配置比较的结果。
- `parent-residual-examples.json`：独立审计的 12 个父体剩余足迹样例，含米制面积与全部关联部件 UUID。

从项目根目录重建（无需联网或私人 SQLite 缓存）：

```sh
python -m pip install shapely pyproj
python source/city/build_landmark_exclusions.py
```

默认读取 `data/fullcity-raw/manifest.json` 及其中全部 1,708 个 gzip 瓦片，验证 1,796,667 个源要素的完整性，输出 `data/landmark-exclusions.json`。可用 `--project`、`--raw`、`--audit` 和 `--output` 指定其他路径。只有确定的主楼 OSM record_id 和显式关联 building_id 会被排除；不使用半径删除。

原始数据来源为 Overture Maps buildings `2026-10-21.0`、© OpenStreetMap contributors。OSM 与 Overture buildings 主题适用 ODbL 1.0；相关 East Asian Buildings 源数据适用 CC BY 4.0。源记录和提供方保留在各要素 properties 中。

## 父体剩余足迹

只删除“有部件”的完整父体会漏掉部件覆盖范围之外的裙房。以下脚本用完整城市的显式 `building_id` 关系计算 `parent − union(parts)`，不修改原始 raw 数据：

```sh
python source/city/build_parent_residual_overrides.py
```

默认输出 `data/parent-residual-overrides.json`，恢复 402 个父体的剩余足迹，总面积 953,690.012 平方米。另 103 个父体已被部件完全覆盖、4 个由精细地标替换。42 个总残差面积不超过 1 平方米的父体合计 22.635866 平方米，作为明确记录的网格阈值不输出；不使用宽度或覆盖率过滤，孔洞完整保留。

父体的 `height` / `num_floors` 可能指整栋楼的最高塔楼，不能直接用于裙房。配置保留其原值供审计，剩余足迹高度须独立通过 CMAB/CNBH/GHSL 等估计并明确标记估计来源。
