# 屋顶补充 v4.1

126个屋顶已接入6个城市分块：双坡29、单坡97，涉及嘉定、普陀、长宁、黄浦。每个采用的参数均核对了原始OSM历史版本；总高度与足迹保留，双坡屋脊居中对称，仍是公开参数的几何解释。

全市1,708分块及1,796,419个普通建筑/部件计数不变；其余1,702个模型与状态字节不变。这一补充不代表全城精细模型或摄影测量成果。完整来源核查见 [ROOF_DATA_AUDIT.md](ROOF_DATA_AUDIT.md)，生成与复核命令见 [SOURCE_ROOF_PATCHES.md](../../source/city/SOURCE_ROOF_PATCHES.md)。

[单坡更新前](../../assets/previews/roofs/jiading-roof-before.png) · [单坡更新后](../../assets/previews/roofs/jiading-roof-after.png)· [双坡更新前](../../assets/previews/roofs/changning-roofs-before.png) · [双坡更新后](../../assets/previews/roofs/changning-roofs-after.png)（两组均为同机位网页截屏；双坡样本为屋顶小部件）

[备用楼块遮挡修复](OSM_FALLBACK_FIX.md) · [几何检查](geometry-validation.json) · [实际分块检查](roof-validation.json) · [全市对账](fullcity-validation.json) · [合并检查](merge-report.json)

# Bounded roof qualification

126 of 1,118 cached non-flat roof candidates passed: 29 gabled and 97 skillion roofs. The accepted records occur in 6 original owner tiles across 嘉定 (3), 普陀 (79), 长宁 (27), 黄浦 (17). This is a bounded source-supported improvement, not citywide LoD2 coverage.

All 132 prefiltered unique OSM way/version requests succeeded. Six skillion candidates had both orientation and direction tags and were conservatively excluded. The remaining 992 candidates are enumerated in skipped-roofs.json; reason counts overlap because a record may fail several checks. Of 345 hipped candidates, 11 have usable positive height/roof-height arithmetic; hipped roofs are report-only and none are qualified.

The 126 accepted source polygons and property objects equal their immutable fullcity raw records exactly. Qualification does not repair geometry or replace outlines with a minimum rotated rectangle. The rectangle is only used to measure aspect/alignment and determine the explicit gabled ridge direction. Near-rectangular gables require aspect ≥1.20, rectangularity ≥0.95, convexity ≥0.98, and every nonzero edge within 8° of an axis. Footprints must be valid single polygons without holes, area ≥1 m², short span ≥0.25 m. Detailed building replacement IDs, linked parts, and whole parents with parts/residual geometry are excluded.

Height is OSM absolute top above ground. Eave height = height − roof_height; base = max(0,min_height). No fallback height, extra wall height, or epsilon inflation is applied. 22 accepted records have height == roof_height; 30 have eave == base, including 8 elevated roof-only parts. 22 records have a nonzero min_height; none have a negative min_height. All satisfy strict roof_height <= height − base. Roof-only cases need zero wall height supported by the generator.

For skillion roofs, the exact historical OSM roof:direction is interpreted as downslope clockwise from north: [east,south] = [sin θ,−cos θ]. Overture's generic direction wording must not be substituted. Gabled ridges use explicit verified along/across relative to the long footprint axis. All required original OSM shape, height, roof:height and orientation/direction tags agree with the cached source; min_height agrees when explicit and defaults to zero only when absent.

Exact historical way tags and closed node sequences are archived in source-evidence. Historical node coordinates were not reconstructed: geometry remains the cached Overture polygon (some footprints were assembled from source tile fragments). The result is a parametric interpretation of public source data, not a surveyed roof mesh. Two near-coincident gabled parts around 121.403645,31.230159 already overlap in the source; qualification preserves both existing source records rather than merging or inventing geometry.

Rebuild without network from a project checkout:

```sh
python source/city/qualify_roofs.py --offline
```

Optional --project, --input, --output and --evidence paths are supported. Omit --offline to fetch missing exact-version evidence, bounded to two concurrent requests. Requires Python, Shapely, NumPy and mapbox-earcut (the project's coordinate helper dependencies). No model export is performed.

Source footprints: Overture Maps buildings release 2026-10-21.0, OSM-derived candidates. Historical tags: © OpenStreetMap contributors, ODbL-1.0; https://www.openstreetmap.org/copyright . Responses retain their original attribution/license fields.
