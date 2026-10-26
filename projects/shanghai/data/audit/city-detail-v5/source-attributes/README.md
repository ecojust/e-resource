# Full Overture GeoParquet：上海属性补充核验

版本 `2026-10-21.0`；直接访问官方 S3 GeoParquet，以完整 raw 档案的 `source_layer:UUID` 作同集合比较。

全球 513 个文件共 277,560,947,087 B。只读文件尾 bbox 和候选 footer，定位 4 个文件、104 个 row groups；属性 Range 载荷 95,083,821 B，几何列读取 0 B，整文件下载 0。

宽 bbox 返回 2,433,147 个要素；与行政边界裁剪后的 raw 逐键匹配 1,796,667/1,796,667。多出的 bbox 要素不能计作上海市区覆盖。

| 字段 | MVT 非空 | Full GeoParquet 非空 | Full 新增 | 值不同 |
|---|---:|---:|---:|---:|
| height | 2,637 | 2,637 | 0 | 0 |
| num_floors | 9,665 | 9,665 | 0 | 0 |
| class | 89,761 | 89,761 | 0 | 0 |
| subtype | 90,779 | 90,779 | 0 | 0 |
| roof_shape | 2,603 | 2,603 | 0 | 0 |
| roof_height | 313 | 313 | 0 | 0 |
| roof_orientation | 383 | 383 | 0 | 0 |
| roof_direction | 130 | 130 | 0 | 0 |
| facade_material | 458 | 458 | 0 | 0 |
| facade_color | 1,434 | 1,434 | 0 | 0 |
| roof_material | 250 | 250 | 0 | 0 |
| roof_color | 1,215 | 1,215 | 0 | 0 |

上海候选文件的 full schema 未见窗/门/入口字段：True。缺属性表示未知，不能推出建筑没有窗门。

126 个已验证屋顶的关键属性与完整源匹配：True。逐字段差异及原始证据索引见 `full-source-coverage.json`。

本次是原 MVT 审计的补充：使用完整源核查是否丢失属性，没有重新下载全球几何，也没有把 bbox 统计冒充行政边界统计。稀疏缓存文件仅含指定列块，不能作为完整 Parquet 传播或发布；工作项目和 Git 均未修改。
