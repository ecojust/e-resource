# 上海建筑高度来源、许可与验证记录

检查日期：2026-10-25。此目录提供可复现的**建筑高度估计**，不能视为逐栋实测高度。模型先保留原数据 `height`，其次用 `num_floors × 3.2 m`，再尝试严格匹配 CMAB 屋顶、CNBH 10 m 像元、GHSL 2018 像元；全部缺失才由上层明确标记 12 m 默认值。栅格均值不能覆盖原始单栋高度。

## 可再分发来源

|来源|实际取得的数据|许可|坐标与单位|主要限制|
|---|---|---|---|---|
|CMAB v2|上海 ZIP 335,640,089 B，21 组 shapefile；行政区内保留 583,980 个屋顶|CC BY 4.0|实际 `.prj` 全为 EPSG:3857；`Height` 为米|机器学习预测；影像屋顶不等于地面足迹；存在分割、投影位移与年代差异|
|CNBH-10m 2020|原始 X121Y31 TIFF 335,234,763 B；上海裁剪 24,314,417 B|CC BY 4.0|原始 EPSG:32651、Float32 米；裁剪 UInt16，元数据 scale=0.1，即分米|上海正值仅 8.5–41.7 m；高楼明显平滑；主体覆盖全部16区中心，远端飞地不完整|
|GHS-BUILT-H ANBH E2018 R2023A|下载东西两瓦片后按16区完整边界裁剪，2,685,448 B|CC BY 4.0|EPSG:4326、3角秒、Float32 米|每个像元内建成区平均净高度，上海约80×93m；不是楼顶高度|
|Microsoft 2023Q4 高度/密度|已下载并裁剪，高度文件 2,609,062 B|CDLA-Permissive-2.0|EPSG:3857，原始第二波段归一化高度×100米，裁剪已转米|约65m地面像元、区域平均值；仅作独立比较，不进入正式优先级|

CMAB 数据引用：Zhang, Yecheng; Zhao, Huimin; Long, Ying (2025), *CMAB-The World's First National-Scale Multi-Attribute Building Dataset*, [Figshare v2, DOI 10.6084/m9.figshare.27992417.v2](https://doi.org/10.6084/m9.figshare.27992417.v2)。[官方 API](https://api.figshare.com/v2/articles/27992417/versions/2) 明确标示数据 **CC BY 4.0**；元数据保存在 `cmab-figshare.json`。上海下载地址为 https://ndownloader.figshare.com/files/51075296 ，官方及本地 MD5 均为 `8e821a251f97e1de78511a5934e9c964`。注意[论文](https://www.nature.com/articles/s41597-025-04730-5)自身许可为 CC BY-NC-ND，和 Figshare 数据许可不同；不再分发论文全文或图像。

论文说明：高度是 Bootstrap Aggregated XGBoost 的100次模型估计均值，训练标签来自百度2023建筑楼层数据；不是激光扫描或逐栋现场测量。旧字段说明写 `pred_h_r`，实际下载 v2 字段已改为 `merged_id, Height, Function, Age, Quality`。`Quality` 是建筑外观质量属性，**不是高度置信度**。图像年份由文件名可见2020–2024，不能统一称为2025年现状。论文描述地理坐标WGS1984，而实际提供数据为WGS84 Web Mercator EPSG:3857，本实现依实际 `.prj` 解读。

CNBH引用：Wu, Wanben; Ma, Jun; Banzhaf, Ellen; et al. (2023), *A first Chinese building height estimate at 10 m resolution (CNBH-10m) using multisource earth observations and machine learning*, Remote Sensing of Environment 291,113578，[DOI 10.1016/j.rse.2023.113578](https://doi.org/10.1016/j.rse.2023.113578)。[Zenodo 数据](https://zenodo.org/records/7827315)，下载 https://zenodo.org/api/records/7827315/files/CNBH10m_X121Y31.tif/content ，MD5 `72fccc03160010daeb697220e2c0db1b`。已比对500个原始/裁剪有效像元，最大量化误差0.04996m。原始浮点值已经是米，**不能除以10**；只有发布的UInt16裁剪需读取其scale=0.1。全国文献RMSE6.1m、MAE5.2m不能当作上海本项目的验证精度。

GHSL引用：European Commission, Joint Research Centre, *GHS-BUILT-H R2023A*，[数据引用](http://data.europa.eu/89h/85005901-3a49-48dd-9d19-6261354f56fe)，[产品说明](https://human-settlement.emergency.copernicus.eu/ghs_buH2023.php)。[官方版权文件](https://jeodpp.jrc.ec.europa.eu/ftp/jrc-opendata/GHSL/GHS_BUILT_H_GLOBE_R2023A/copyright.txt) 明确 CC BY 4.0。输入含2000年SRTM、2006–2011年AW3D30以及2018年Sentinel-2阴影信息，不能解释为所有建筑2018年直接实测。采用 **ANBH平均净建筑高度**，不是AGBH面积稀释的体积平均。零值视为无可用高度。东西瓦片R6_C30+C31覆盖16区完整行政几何（包括远端飞地），但无建筑的像元仍可为零。扩展前12,923,730个像元逐值不变，西部新增1,927个有效像元。最终SHA-256 `3d4fe310d0c159e19ac847fe51bc7e14316877b8662ea0bc7cc2d75db9c73535`，详见 `ghsl_full_extent_validation.json`。

Microsoft来源、许可原文、实际下载与验证参见 `alternatives/HEIGHT_ALTERNATIVES.md`。**GlobalBuildingAtlas高度/LoD1为CC BY-NC 4.0**，只有分离的GBA.ODbLPolygon轮廓为ODbL；本项目没有复制GBA的单栋高度或几何。不将“开放下载”等同于“无限制商用”。

## 固定接口与转移规则

```python
from building_height_sampler import BuildingHeightSampler
sampler = BuildingHeightSampler(
    cnbh_path='alternatives/cnbh_2020_shanghai_core_dm.tif',
    ghsl_path='shanghai_ghsl_anbh_2018_3arcsec.tif',
    cmab_path='cmab/shards',
)
result = sampler.sample_geometry(feature['geometry'])  # 输入GeoJSON EPSG:4326
```

每个worker缓存一个实例；不要为每栋楼重复加载栅格。需要 `building_height_sampler.py`、`raster_height_sampler.py`、上述数据和 Python numpy/rasterio/pyproj/shapely>=2.1/pyarrow。`None` 表示此估计链没有可用高度；调用方优先保留源height和楼层估计。

返回 `height_m, height_source, height_quality, height_estimated, height_license, height_method, height_sample_count, height_sampler_version`；CMAB另有源ID、IoU、双方覆盖率。质量键分别为 `cmab_estimate_matched_rooftop`、`cnbh_estimate_10m`、`raster_estimate_2018`。这些名称均明确为估计，不能显示成“实测”。

CMAB在5000投影米网格存储，266片合计314,271,565 B，最大4,873,520 B。文件保留原始屋顶轮廓；没有坐标偏移、简化或最近邻转移。只有 **IoU≥0.60且双方覆盖率均≥0.70** 才接受；第二候选IoU与最佳相差≤0.10且高度差>10%则拒绝。建筑分裂/合并不满足双边覆盖时拒绝。六项几何语义测试通过，见 `test_cmab_matcher.py`。583,980个屋顶的实际预测高度为3–135.98m，中位18.07m，仅27个超过100m；因此CMAB也显著平滑超高层，不能补全真实高层天际线。数值分布见 `cmab/height_distribution.json`。所有16区都有CMAB屋顶，逐区计数见 `cmab/shards/manifest.json`；这不代表覆盖每栋建筑或全部农村区域。

CNBH优先取足迹内部像元中心的有效正值中位数；狭小足迹无内部像元中心时取足迹内representative point。孔洞排除，不取邻楼像元填洞；内部像元存在但皆无效则进入GHSL。GHSL取同一足迹内部代表点所在像元。栅格采样器六项语义测试、500点缩放验证与680栋性能测试见 `alternatives/raster_sampler_validation.json`。

## 对齐与高度一致性检查

独立对齐审计对16区各80个、共1280个参考轮廓抽样：直接EPSG3857位置有246个IoU≥0.5；假设GCJ偏移(-500,+250m)仅2个、反向偏移3个、100m对照偏移4个。因此没有整体GCJ错位证据，禁止擅自移动数据。这只排除明显统一偏移，不证明单栋地面与屋顶精确重合。详见 `../audit/cmab-alignment.json`。

现有16区500m邻域共8,322栋，严格CMAB匹配663栋（7.97%）；CNBH可采样7,677栋，其余645栋回退GHSL。该邻域不是全市随机样本，不能外推全市匹配率。

其中375栋具有可比较的源数据：93个明确height、282个num_floors×3.2m。下列为两类数据的**一致性**，不是对独立地面真值的准确率验证：

|估计来源|可比较样本|中位绝对差|P90绝对差|
|---|---:|---:|---:|
|严格匹配CMAB|29（仅2个明确height，其余楼层估计）|16.692m|47.006m|
|CNBH足迹采样|370|16.450m|124.470m|
|GHSL代表点像元|375|17.724m|132.173m|

三列样本不同，不能据此直接排名数据精度。93个明确height中，GHSL中位绝对差达71.669m；上海中心所在GHSL像元只有约23.96m，而地标实际632m，直接展示了用像元高度替换单栋高度的错误。逐区、按高度级、按height/楼层来源拆分统计和逐样本CSV均在 `height_source_comparison.json`、`height_source_comparison.csv`；可用 `compare_all_height_sources.py` 重跑。

## 五个地标高度的独立核实

|地标|采用高度|可靠来源|
|---|---:|---|
|东方明珠|468m|[东方明珠官方](https://www.opg.cn/)|
|上海中心|632m|[CTBUH/CVU Skyscraper Center](https://www.skyscrapercenter.com/building/shanghai-tower/56)|
|上海环球金融中心|492m|[森大厦项目官网](https://www.mori.co.jp/en/projects/swfc/)|
|金茂大厦|420.5m|[CTBUH/CVU Skyscraper Center](https://www.skyscrapercenter.com/building/jin-mao-tower/189)|
|江海关大楼|79.2m|[上海海关原文存档](https://web.archive.org/web/20100610110157/http://shanghai.customs.gov.cn/publish/portal27/tab8419/module26899/info82241.htm)：主楼36.2m+钟楼43m|

英文维基曾写江海关90m，与官方原文冲突，本项目采用79.2m并记录更正。地标高精模型覆盖其通用轮廓；OSM锚点是轮廓/定位基准，不宣称亚米级测量。

## 发布与复现

原始CMAB335MB ZIP、429MB主shp、CNBH335MB TIFF、Microsoft全球索引等**不得上传到要求单文件<100MB的仓库**。发布小型栅格、CMAB分片、采样源码、许可/出处与验证报告即可；也可只发布重建下载脚本与最终分片模型。原始论文HTML只用于本地查阅，不再分发。

完整可移植重建入口和命令见 [REBUILD.md](REBUILD.md)。`prepare_cmab.py` 从原始shapefile或Shanghai ZIP重建CMAB分片；`prepare_ghsl.py` 调用已附的东西瓦片合并脚本，支持首次完整重建；CNBH公开分段下载、裁剪和语义验证脚本在 `alternatives/`。默认输入相对项目目录解析，均可用CLI参数覆盖；重建结果写入忽略目录 `rebuilt/`，不自动修改锁定发行文件。几何裁剪使用OSM行政区边界，边界许可ODbL-1.0单独保留；来源高度仍须署名原CC BY作者，派生数据库的发布许可由项目总体许可证说明。
