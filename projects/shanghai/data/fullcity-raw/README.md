# 上海全域建筑轮廓提取

范围为提供的 `districts-display.geojson` 中上海 16 区可视化边界；包含海域，不能把瓦片覆盖面积当作城市陆域或已建成面积。

全域计划覆盖 **2,892** 个 z14 瓦片；其中 **1,734** 个存在 Overture 建筑源数据，已全部获取并解码。其余 **1,158** 个没有源瓦片，多数位于海域，也可能反映未开发区域或源数据空缺，不生成虚构建筑。

将瓦片边缘片段按 `(source_layer, Overture UUID)` 合并，随后裁剪到市界，得到 **1,796,667** 个唯一地上建筑或部件要素，分配到 **1,708** 个格网块。按真实部件存在情况排除重复父体后，可用于地上渲染的要素为 **1,796,116** 个。

## 数据文件

- `tiles/14/{x}/{y}.geojson.gz`：完整建筑几何，保留内院孔洞与源属性。每个 UUID 只分配到一个所属格网，不在相邻文件重复整个建筑。
- `manifest.json`：最终完整性、分区计数、文件列表及大小。
- `coverage.json`：全部计划源瓦片的处理状态。
- `coverage-gaps.geojson`：没有源建筑要素或处理失败的瓦片范围；具体原因见状态字段，不能一概理解为建筑漏测。
- `excluded-underground.geojson.gz`：源数据明确标为地下的 11 个建筑，原始几何单独保留，`renderable:false`，不会挤成地面楼房。
- `district-boundary.geojson`：本次提取使用的完整边界副本。
- `COMPLETE`：通过下载、解码、拼接及唯一性检查后生成。

## 分区计数

| 区 | 唯一地上建筑/部件 | 可渲染要素 | 有源高度或层数 |
|---|---:|---:|---:|
| 黄浦区 | 13,854 | 13,824 | 1,092 |
| 徐汇区 | 30,129 | 30,124 | 558 |
| 长宁区 | 17,954 | 17,863 | 2,583 |
| 静安区 | 22,915 | 22,895 | 255 |
| 普陀区 | 27,403 | 27,225 | 2,156 |
| 虹口区 | 15,395 | 15,384 | 402 |
| 杨浦区 | 32,622 | 32,593 | 916 |
| 闵行区 | 121,728 | 121,720 | 385 |
| 宝山区 | 106,543 | 106,520 | 364 |
| 嘉定区 | 131,113 | 131,032 | 444 |
| 浦东新区 | 416,516 | 416,470 | 1,436 |
| 金山区 | 120,473 | 120,473 | 250 |
| 松江区 | 139,361 | 139,347 | 132 |
| 青浦区 | 151,684 | 151,671 | 70 |
| 奉贤区 | 154,046 | 154,046 | 111 |
| 崇明区 | 294,931 | 294,929 | 156 |

## 属性与精度

- 真实轮廓来自 Overture Maps 2026-10-21.0 建筑主题，源最大缩放级别 14；MVT 轮廓存在量化与概化，不是测绘级矢量。
- `height`、`min_height`、`num_floors`、`sources` 等源属性原样保留；提取程序不臆造高度。
- `district_id` 与 `district_name` 按裁剪后几何所属区分配；几何跨区时采用内部代表点归属。
- 原始建筑与 `building_part` 均保留；有实际部件的父体标记 `renderable:false`，防止重复实体。
- 来源发布日期不是实测日期。缺高度的建筑如果在模型阶段使用遥感平均高度或默认高度，必须另标估算来源。

## 许可与署名

Overture 建筑主题采用 **ODbL 1.0**，保留 © OpenStreetMap contributors、© Overture Maps Foundation 署名。上海大量轮廓来自 Qian Shi 等的 East Asian Buildings，DOI:10.5281/zenodo.8174931，原数据采用 CC BY 4.0。逐要素来源保留在 `sources` 中。

官方说明：https://docs.overturemaps.org/attribution/#buildings

## 可持续重跑

提取脚本 `fetch_fullcity.py` 通过 HTTP Range 读取官方 PMTiles，只下载本区域所需瓦片。中间数据放在独立 cache 目录，记录已下载及已解码瓦片，失败后重跑可继续；中间 SQLite 不属于发布文件。

依赖：`pip install pmtiles mapbox-vector-tile shapely`。

```sh
python fetch_fullcity.py --boundary path/to/districts-display.geojson --output raw --cache cache --release 2026-10-21.0
```

官方旧发布版约保留 60 天，长期重抓应从 https://stac.overturemaps.org/catalog.json 选择仍可用版本，并使用新的 cache 目录。已发布的本地提取结果不依赖远端版本继续存在。
