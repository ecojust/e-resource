# 上海全域高细节资料可行性核查（有界检查）

核查日期：2026-10-25。范围限定为六类相关来源，不下载大数据、不修改既有模型。以下“未取得/未核实”只描述本轮检查结果，不表示相关数据在全球不存在，也不把网页可浏览等同于模型包可公开再分发。

## 结论

本轮没有取得一个**覆盖上海全部16区、包含可核验的真实屋顶/立面细节，并且可按明确条件公开再分发**的LoD2/LoD3或摄影测量网格包。已经取得的轮廓和楼高资料仍可改进LoD1城市背景，但不能单靠增加挤出高度、通用窗格或更换引擎恢复真实窗位、柱廊和屋顶结构。

这不是停止所有建模的理由：有明确照片/建筑资料的单体仍可继续人工重建并逐栋备份，或在取得测绘图、授权mesh后分批替换。只是不能把这些局部成果或推定细节扩大宣称为“全城逐栋真实精细复原”。现有外滩模型的照片依据和推定标注应保留。Godot/Unreal可改善某些运行与打包方式，但不会自动补齐缺失的城市几何或再分发许可。

## 来源1：GlobalBuildingAtlas（GBA）

主要来源：
- [作者官方仓库与说明](https://github.com/zhu-xlab/GlobalBuildingAtlas)
- [GBA.LoD1 数据发布](https://huggingface.co/datasets/zhu-xlab/GBA.LoD1)
- [论文：GlobalBuildingAtlas: an open global and complete dataset of building polygons, heights and LoD1 3D models](https://essd.copernicus.org/articles/17/6647/2025/)

本次直接获取官方README，开头明确写："we provide the level of detail 1 (LoD1) data of buildings across the globe"。FAQ明确：目标为全球覆盖，但因数据质量，部分地区可能缺失或缺高度；高度是机器学习派生结果，会有错误。因此上海属于其全球设计范围，但本次没有下载上海瓦片核验每栋完整度，也不宣称其已覆盖上海所有建筑。

实际内容是建筑多边形、估计高度与高度方差等属性，经脚本生成LoD1。它不能提供真实屋顶坡面、老虎窗、窗洞、门厅、柱廊或照片纹理。换用GBA不能单独解决用户反映的“小方块”问题。

官方许可证明确分产品，而非一律开放商用：
- `GBA.ODbLPolygon`：来源于ODbL数据的纯轮廓，ODbL。
- `GBA.Polygon`、`GBA.LoD1`、`GBA.Height`：CC BY-NC 4.0。
- 仓库代码：MIT with Commons Clause，README明确注明 no commercial use allowed。

CC BY-NC不等于“禁止任何下载/再分发”；可以在其非商业、署名等条件下使用和分享，但不能把这些数据或组合成果无条件标为MIT/可商用。即便接受该条件，它仍只有LoD1。作者还明确其Web Viewer只供交互查看，要求数据访问使用正式发布，不能拿WFS做自动查询或批量提取。本次未调用WFS。

证据来自上述官方README和产品发布页；本轮没有复制其三维数据。

## 来源2：Overture Buildings

主要来源：
- [官方Buildings Guide](https://docs.overturemaps.org/guides/buildings/)
- [Building schema](https://docs.overturemaps.org/schema/reference/buildings/building/)
- [官方许可与署名](https://docs.overturemaps.org/attribution/)

官方用途说明明确3D/2.5D显示是按建筑高度或楼层挤出。Schema对geometry的定义是俯视的二维足迹，`height`、`num_floors`用于近似三维形状；`building_part`可改善分体体量。可选字段包括 `facade_color`、`facade_material`、`roof_material`、`roof_shape`、`roof_direction`、`roof_orientation`、`roof_color`、`roof_height`。

**有这些schema字段，不代表上海数据实际全部有值，更不代表数据包含真实屋顶三角面或立面网格。** 有可靠且完整的屋顶参数时可以进一步构造参数化屋顶；数据结构没有提供全楼窗洞、门廊、墙面雕刻等几何。现有项目的外滩500m历史源样本341个要素中，仅1个有`roof_shape`；这只说明该局部样本稀疏，不能外推为全市统计。证据：已发布 `data/bund/geometric-detail-statistics.json`，其中城市总量属于V2历史分析，不是最新V3计数。

上海覆盖有现有工程的实际获取和审计支持，而不只依赖“全球”宣传：2026-10-21.0源在16区保留1,796,667个唯一地上建筑/部件；当前V3已导出1,708个通用模型分块。原始源、唯一ID和全部分块校验随项目发布。

官方许可：Buildings主题为ODbL；须保留Overture及OSM和逐来源署名。官方许可页列East Asian Buildings为CC BY 4.0。可下载及依法再分发，许可足够支持目前的分块数据库；它缺的是全市近景几何细节，不能靠更换引擎补出。

官方证据链接如上。项目覆盖审计见 [全域核验](fullcity-models-validation.json)；来源与许可见 [SOURCES.md](../SOURCES.md)。

## 来源3：CNBH / CMAB楼高来源家族

主要来源：
- [CMAB Figshare v2官方API](https://api.figshare.com/v2/articles/27992417/versions/2)
- [CNBH Zenodo DOI](https://doi.org/10.5281/zenodo.7827315)
- [CNBH DataCite官方元数据](https://api.datacite.org/dois/10.5281/zenodo.7827315)

**CMAB：** 官方API仍列`shanghai.zip`，文件ID51075296，335,640,089字节；本次仅查看元数据，没有重下载。数据许可对象明确为CC BY 4.0。API介绍其通过机器学习/多模态模型估计屋顶、楼高、功能、年代、外观质量等属性；现有项目实读V2的字段为`merged_id, Height, Function, Age, Quality`，几何是屋顶二维轮廓，并非建筑密集网格。数据说明引用街景作为训练/属性推断来源，不等于提供了可再分发的全部街景照片、纹理或窗洞几何。

既有上海数据实查：行政区内583,980个屋顶，16区都有记录；这不表示每栋建筑全覆盖。上海预测高度3–135.98m，仅27个超过100m，不能准确恢复真实超高层天际线。`Quality`是外观质量，不能误用成高度置信度。屋顶投影也不能无条件当成地面足迹。官方数据CC BY 4.0与论文自身更严格的文章许可应分别处理；已发布项目采用的是数据许可。

**CNBH：** 官方元数据明确为中国2020年10m分辨率的Random Forest楼高估计。DataCite的`rightsList`明确CC BY 4.0。它是栅格高度估计，不包含单栋真实屋顶坡面、立面或纹理；全国RMSE 6.1m/MAE 5.2m不能当成上海逐栋误差保证。既有上海裁剪覆盖16区中心但远端飞地不完整，正值8.5–41.7m，显著平滑高楼。

这些数据已被当前项目用于有标注的高度估算，重新获取或换引擎不会改变其语义。CMAB属性可帮助挑选建筑类别、制作有依据的风格分类；用其自动生成具体窗户和装饰仍属于程序推测，不能标为逐栋验证后的复刻。

本次重新读取了上述官方API元数据。既有处理、许可和对齐/精度限制见 [高度来源审计](../heights/HEIGHT_SOURCES.md)、[CMAB元数据](../heights/cmab-figshare.json)、[CNBH元数据](../heights/alternatives/datacite-7827315.json)；大数据复用已有审计，没有重新下载。


## 来源4：上海公共数据开放门户 / 地方CIM线索

- 直接检查入口：<https://data.sh.gov.cn/>。
- 本次使用公开HTTP请求返回 **412 Precondition Failed**，没有取得可审阅的数据目录或具体3D模型数据条目。
- 针对上海CIM/实景三维的有限检索只返回了泛化搜索结果，未用这些结果充当具体数据证据。未绕过访问限制。
- 因此，本轮**没有确认**其是否提供覆盖16区的可下载LoD2/LoD3数据；也**没有取得再分发许可**。不能把访问失败写成“该门户没有高精度数据”或“政府数据禁止使用”。若能正常访问，应继续核查具体数据集的下载范围、坐标、年份、精度报告和许可正文，而非只引用“建成数字孪生平台”的宣传描述。

## 来源5：Google Maps Platform Photorealistic 3D Tiles

- 服务文档：<https://developers.google.com/maps/documentation/tile/3d-tiles>（本轮HTTP 200）。
- 官方使用政策：<https://developers.google.com/maps/documentation/tile/policies>（本轮HTTP 200）。
- 覆盖页面：<https://developers.google.com/maps/coverage>（本轮HTTP 200）。该页是一般Maps覆盖表，本轮没有在其中核实上海Photorealistic 3D Tiles覆盖；不能根据一般2D地图的China行推断三维mesh覆盖。
- 能力：服务可向兼容的3D Tiles渲染器传输摄影级三维瓦片；文档说明需支持版权署名，列有CesiumJS与Cesium for Unreal。**这是在线服务接口，不是本次已下载的开放上海模型包。** 本轮未创建API密钥、未调用收费瓦片服务、未取得上海mesh。
- 许可/使用证据：官方政策“Pre-fetching, caching, or storage of content”明确写明，除协议规定的有限条件外，不得“pre-fetch, index, store, or cache any Content”；并列出Geodata extraction/resale和offline用途限制。因此，不能把服务中的瓦片抓取后当作已获开放再分发授权的GLB上传本仓库。
- 文档页页脚的CC BY 4.0是**文档内容**许可，不是3D瓦片的开放数据许可。若另行采用该在线服务，必须单独确认地区覆盖、账号/费用和服务条款；本轮不把它作为公开模型资源的替代品。

## 来源6：Sketchfab现有上海建筑局部候选

- 模型页：<https://sketchfab.com/3d-models/east-gate-of-broadway-mansions-6229b42dd6334965b15fb10128c86a6e>。
- 元数据：<https://api.sketchfab.com/v3/models/6229b42dd6334965b15fb10128c86a6e>（本轮HTTP 200）。
- 名称为 **East gate of Broadway Mansions**，即上海大厦/百老汇大厦东门局部；API记录214,698顶点、357,022面。不能据此推断其为整栋或全上海数据。
- API许可字段为 **CC Attribution-NonCommercial-NoDerivs 4.0**；原文要求署名、非商业用途，且“Modified versions can not be distributed”。许可URL：<https://creativecommons.org/licenses/by-nc-nd/4.0/>。这不等于完全不能分享未修改原件，但不能把它改标MIT，也不能把修改后版本的公开再分发当作已被允许。
- `isDownloadable:true` 仅为元数据标记。下载接口 <https://api.sketchfab.com/v3/models/6229b42dd6334965b15fb10128c86a6e/download> 本轮实际返回 **401**，正文为 `Authentication credentials were not provided.`。未取得模型包，未绕过认证抓取viewer资源。
- 结论：即使未来取得符合许可的下载，也只是一个局部候选，不能解决全市逐栋细节或本轮10栋外滩建筑的覆盖问题。

## 本轮证据保存与边界

上述HTTP状态记录的是本轮访问结果，后续服务状态可能变化。没有下载或上传大型3D资产，也不转载查阅网页全文；新增分发资源仅为这份核查说明。可复现高度资料的官方元数据与许可仍以 [高度来源](../heights/HEIGHT_SOURCES.md)、[数据来源](../SOURCES.md)及逐文件来源记录为准。

继续推进时，可按单体保留“足迹来源、尺寸证据、照片方位、已知/推定部位、独立验证、许可证据、GLB/.blend哈希”清单；缺少来源的部分应标记为推定。公开数据的年代差异和栅格高度误差不能通过增加模型小数位或三角形数消除。
