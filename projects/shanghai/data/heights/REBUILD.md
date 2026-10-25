# 高度数据包的校验与重建

本页命令以项目根目录为当前目录。脚本也可从任意工作目录调用，默认输入均按脚本所在位置解析。需要 **Python 3.11+**；采样实现依赖 Shapely 2.1 的坐标转换接口。

```bash
python -m pip install -r data/heights/requirements-rebuild.txt
python data/heights/verify_release.py
```

`verify_release.py` 不需要GIS依赖，按 `height_sources_lock.json` 验证271个发布文件的长度和SHA-256，包括两个固定采样器。默认重建产物放在 `data/heights/rebuilt/`，原始下载放在 `data/heights/.cache/`；这两个目录都被本数据包的 `.gitignore` 忽略。原始CMAB、CNBH及GHSL西瓦片超过100MB，不能提交仓库。

## 下载原始数据

```bash
python data/heights/download_height_sources.py all
python data/heights/alternatives/download_cnbh_ranges.py
```

第一条下载CMAB上海ZIP及GHSL东西两个ZIP，逐个检查发布时记录的大小/校验和/ZIP CRC。已有正确缓存会复用。第二条使用公开HTTP分段下载CNBH并核验官方MD5。下载器不会在导入或运行 `--help` 时联网。由于上游服务可能改变访问策略，网络错误须依据实际错误处理，不能绕过许可或授权。

不必重下载：CMAB/GHSL下载器支持 `--cache-dir`；CNBH参数请运行 `--help`。裁剪脚本可直接接收已有原始文件。

## 重建三个高度来源

```bash
python data/heights/prepare_cmab.py --archive data/heights/.cache/height-sources/shanghai.zip
python data/heights/alternatives/clip_cnbh_shanghai.py
python data/heights/prepare_ghsl.py \
  --east data/heights/.cache/height-sources/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_4326_3ss_V1_0_R6_C31.zip \
  --west data/heights/.cache/height-sources/GHS_BUILT_H_ANBH_E2018_GLOBE_R2023A_4326_3ss_V1_0_R6_C30.zip
```

- CMAB可改用 `--raw 已解压shapefile目录`，可指定 `--boundaries`、`--output`。自动提取ZIP时检查成员路径，避免写出指定原始目录。默认输出 `rebuilt/cmab/shards/`。
- CNBH使用EPSG:32651原始Float32米值，裁剪后UInt16分米/scale=0.1。输入、边界、输出参数见该脚本 `--help`。默认输出在 `rebuilt/`。
- GHSL需要东西两个官方源，可为TIFF或ZIP。`prepare_ghsl.py` 是 `alternatives/extend_ghsl_west.py` 的统一入口；默认边界为项目 `data/districts.geojson`，输出为 `rebuilt/shanghai_ghsl_anbh_2018_3arcsec.tif`。`--previous` 可选，用来验证已有东瓦片裁剪像元未改变；首次重建无需已有裁剪。

全部使用**完整行政边界** `data/districts.geojson`，不能换成仅供地图简化展示的 `districts-display.geojson`。GHSL保持东瓦片格网，西瓦片按最近邻对齐；CNBH仍只覆盖主瓦片的有效范围。CMAB保留原始屋顶几何，单栋匹配阈值与估计质量标识由锁定采样器控制。

重建时GDAL/Parquet压缩库版本可能影响二进制文件哈希；不应为了使哈希相同而更改源高度或几何。先验证数值、格网、覆盖范围与统计，再由维护者明确更新新的来源锁。重建命令不会自动改动发布数据或现有锁文件。

## 重跑验证与高度一致性报告

```bash
python data/heights/test_cmab_matcher.py
python data/heights/alternatives/validate_sampler.py --help
python data/heights/compare_all_height_sources.py
```

比较脚本默认读取项目 `data/neighborhoods/manifest.json` 和本数据包的已发布高度来源，结果写到 `rebuilt/comparison/`。可通过 `--neighborhoods`、`--cmab`、`--cnbh`、`--ghsl`、`--output-dir` 改为新的输入。楼层换算固定为3.2m/层；缺失值不会变成零高度。它是跨来源一致性检查，不是现场实测精度测试。

`alternatives/validate_sampler.py` 提供不联网的像元缩放、足迹孔洞、窄足迹和缺失回退语义验证；原始/裁剪500点对比证据另见已附 `alternatives/raster_sampler_validation.json`。各参数以 `--help` 为准，原始大文件不是读取已发布数据的前提。

## 来源与许可文件

- 综合说明：[HEIGHT_SOURCES.md](HEIGHT_SOURCES.md)。
- CMAB官方数据许可元数据：[cmab-figshare.json](cmab-figshare.json)；原始说明：[cmab/README.txt](cmab/README.txt)、[字段文档](cmab/metadata.csv)。旧字段名 `pred_h_r` 与v2实际 `Height` 的差异已记录。
- CNBH下载/缩放/覆盖证据：[alternatives/HEIGHT_ALTERNATIVES.md](alternatives/HEIGHT_ALTERNATIVES.md)。
- GHSL官方许可：[ghsl-copyright.txt](ghsl-copyright.txt)；全行政范围复现证据：[ghsl_full_extent_validation.json](ghsl_full_extent_validation.json)。
- 原始现场查阅的论文HTML、第三方研究代码、全球索引与大下载包未附在本发行包；不影响使用已发布高度数据。
