# 上海屋顶资料补充核查

日期：2026-10-25。本轮限定直接OSM标签/语义核验及三项新科研候选，不重复此前六类来源概览，不下载大型模型，不修改仓库或模型。

**可立即推进的是已有少量有来源参数的屋顶；尚未取得全16区真实屋顶坡面和立面且可公开再分发的现成数据包。** 这两点并不矛盾。已有缓存中的屋顶标签值得利用，不能继续将全城一律平顶当作数据能力的上限；但少量参数化屋顶也不能扩大宣传为全上海精细复刻。

## 1. 可直接利用的缓存数据和明确版本OSM证据

主任务对全部1,708个源块扫描得到1,796,667个唯一建筑/部件源要素。已有`roof_shape` 2,603条，非平1,118条；非平且`0<roof_height<height`的249条，其中同时有`roof_direction`或`roof_orientation`的161条，具备既有“可渲染”标记159条。这些是参数资格候选，不是已经核验完成的模型。各区分布见 [16区统计](CACHED_ROOF_COUNTS.md)，完整机器证据和精确交集在同目录。

这里可以补充有来源的双坡/单坡等几何、分段体量和屋顶颜色；仍需排除复杂足迹、孔洞、重叠parts和不完整参数。不从屋型或楼高推造真实窗位、坡面构造或实测精度。

原始OSM明确允许按ODbL条件复制、分发和改作，须署名且遵守派生数据库等相应义务：<https://www.openstreetmap.org/copyright>。保留Overture逐来源字段及OSM attribution，不将这些地理数据改标为无条件MIT。

三个原始版本API已实际HTTP 200，且与缓存源值逐项相同：

- <https://api.openstreetmap.org/api/0.6/way/1372574254/1.json>：skillion，方向347，坡高21.5，总高24.5。
- <https://api.openstreetmap.org/api/0.6/way/156346098/6.json>：skillion，方向54，坡高9.5，总高13。
- <https://api.openstreetmap.org/api/0.6/way/1371942058/2.json>：skillion，方向167，height=35，min_height=29.75，无roof:height。

**发现会影响模型正确性的语义差异：** OSM `roof:direction`是坡面下坡方向；Overture schema却写屋脊方位。这三个skillion样本的值未经旋转，故应按明确原始OSM语义处理。第三例顶是离地35m，不能因schema对height的措辞再加29.75m。具体文档URL、最低所需参数和推定边界见 [几何语义核查](ROOF_GEOMETRY_SEMANTICS.md)。不将三个样本推成全部ETL的保证。

## 2. 独立OSM全市计数：有界尝试的实际状态

- 黄浦区行政area `3600371650`（relation371650）直接查询ways/relations带`roof:shape`，kumi Overpass返回 **102个way、0 relation**；响应注明底库日期 **2026-07-28T02:16:18Z**。这是该镜像该时点的元素计数，不是当日全量OSM精度认证。查询和响应：`evidence/osm-probe.overpassql`、`evidence/osm-probe-kumi.json`。
- 随后一次16区8类键计数请求超时（`query_osm_counts.py`，115秒客户端限时）；最后一次简化为16区roof:shape/roof:height/building:part三类计数，官方overpass-api.de端点返回 **502 Bad Gateway**。相应查询文本、状态和脚本均保留。本轮到此停止重试，不为资料检查持续占用公共服务。
- 因而本轮**未取得独立OSM在线全16区完整计数，也未取得全市building:part数量**；不能把超时/502写成无标签或0。上面的16区缓存表明确标为已保存Overture源统计，没有伪装成OSM在线统计。
- 这些失败不妨碍利用已保存且有许可的候选和已核验单体版本；也不证明OSM之外无详细资料。

## 3. 三项具体新科研线索

完整下载入口、许可原文证据和覆盖边界见 [科研屋顶数据核查](academic-roofs.md)。摘要如下：

|来源|具体公开数据/方法|上海证据与可增加几何|本轮许可/访问结论|
|---|---|---|---|
|[MT-BR / BuildingDetails-Multitask](https://github.com/ChanceQZ/BuildingDetails-Multitask)|[SH_BuildingDetails.gpkg](https://drive.google.com/file/d/1VSqa2xI5Lh1qSjrj0p-ekulLyTU5jWZR/view)，公开目录显示462.6 MB，未下载|官方称上海177万实体；训练配置明确flat/gable/hip/complex四类，可给屋型选择依据；未核验16区逐栋覆盖及坡高/屋脊几何|README、完整仓库树与Drive未取得这份数据的再分发许可。不是已知禁止，也不能因Download按钮推定可分发|
|[GABLE](https://github.com/AICyberTeam/GABLE)|官方独立[Shanghai SHP入口](https://pan.baidu.com/s/137_vIGuGn1YDtx7oUtm8_w)，公开码u11u|读取脚本是2D polygon + roof_type + height，12类体系；未取得上海三维坡面与区级数量|本环境百度盘403；根MIT明确software/docs，未取得将其扩展到外链SHP的授权说明|
|[SAT2LoD2](https://github.com/GDAOSU/LOD2BuildingModel)|DSM和正射影像驱动LoD2生成方法|实验Columbus/London/Trento；未取得上海现成结果或上海已授权输入|实际EULA限内部非商业且禁软件再分发/改作；论文CC BY不等于软件/附带资产许可|

MT-BR是有实际价值的新线索，但当前既缺明确数据许可，也缺几何参数证据；即使后续允许使用，分类也不直接等于LoD2。其源GPKG超过GitHub单文件100 MB限制，未来经许可处理后需分块。此轮没有下载这些城市数据包。

## 4. 交付与范围

本目录提供计数表、参数交集、具体来源、HTTP记录和有限样本，供后续审阅和实现使用。没有启动浏览器、没有跑全城建模，也没有修改发布仓库。任何未来导出的屋顶模型仍应记录足迹来源、OSM版本、方向语义、参数实值、生成假设、跳过理由与独立验证结果；高程估计或屋顶分类不能被写成逐栋测绘精度。
