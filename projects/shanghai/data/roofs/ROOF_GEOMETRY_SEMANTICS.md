# 屋顶参数的几何含义及最小可靠输入

核查日期：2026-10-25。此文件只解释本轮取得的官方文档；不构造模型，也不宣称字段值已逐栋测量验证。

## 特别需要避免的方向混用

- Overture Building schema 当前 v2.0.0：`roof_direction` = **“Bearing of the roof ridge line in degrees”**（屋脊线方位，0≤值<360）。来源：<https://docs.overturemaps.org/schema/reference/buildings/building/>。
- OSM `roof:direction`：明确 **“direction of the roof surface(s), not the roof ridge”**，从高处屋脊往低处屋檐的下坡方向，可为0–360度或N/S/NW等罗盘文字。来源：<https://wiki.openstreetmap.org/wiki/Key:roof:direction>。
- 两份文档存在实质语义差异。不能将两种字段不经核验直接送入同一个“屋脊方位”参数。对标准双坡屋面，原始OSM下坡方位对应屋脊轴线±90°；屋脊方向本身按180°等价。对于单坡屋顶，下坡方向直接决定高低檐，不能随意把它改成屋脊方向。应保留字段出处，并用样本OSM原始标签核查实际ETL是否转换；本轮尚未证明Overture转换的实现。
- Overture `roof_orientation` 明确沿用OSM语义：`along` 为屋脊平行较长建筑边，`across` 为屋脊垂直较长边。来源：<https://docs.overturemaps.org/schema/reference/buildings/types/roof_orientation/>。这里不是绝对北向；近正方形、复杂多边形和多部分屋顶往往无法仅凭“较长边”唯一确定实际屋脊。OSM文档也指出正方形和单坡不能依赖这种检测：<https://wiki.openstreetmap.org/wiki/Key:roof:orientation>。

## 高度和分体

- OSM `height` 是地面至屋顶最高点的总高，屋顶坡高 `roof:height` 包含在内；对接地的常规建筑，檐口/墙顶高度 = `height − roof:height`。不能先把整栋挤出到height，再额外叠加同样的roof:height。OSM `min_height` 是悬空部分底部的离地高，`height`仍是到顶的总高。来源：<https://wiki.openstreetmap.org/wiki/Simple_3D_Buildings>。
- Overture 当前schema将 `height` 描述为建筑或部件最低点至最高点距离，`min_height`为底部离地高；这与OSM文档的总高措辞也不同。接地建筑无此差别，非零min_height的部件须在转换前核验源字段处理，不能无条件套用OSM公式。
- `roof_height` / `roof:height`是屋顶底部至最高点的距离，单位米。`roof:angle`是坡面角度，只有明确屋型、坡向和水平跨度后才能推得坡高；`roof:levels`是屋顶内楼层数，不能自动等同测量的米数。
- `building:part`是具有独立高度/层数/形状/材质的建筑部分，可改善裙房、塔楼、悬挑等体量；不是窗户、门厅或装饰几何。建筑轮廓和parts需要匹配与去重，不能把二者都完整重叠渲染。来源：<https://wiki.openstreetmap.org/wiki/Key:building:part>。

## 能增加哪些几何，以及仍需标记哪些推定

|输入|可有据增加的部分|不能由字段唯一恢复的部分|
|---|---|---|
|二维足迹+总高|有高度的体量|任何非平屋面；仅高度不是LoD2|
|上述+`roof_shape=flat`|有来源的平顶类别|女儿墙、机房、排水坡度及设备|
|简单矩形足迹+明确gable类+正值坡高+无歧义屋脊轴/朝向|标准双坡屋面的参数化几何；保留参数来源|不对称坡、屋脊偏心、老虎窗、屋檐外挑；默认对称仍需注明|
|简单足迹+hip类+坡高+方向|标准四坡近似|屋脊长度、端部坡角、非对称坡面；等坡度假设不是实测|
|skillion类+坡高+明确下坡方向|高低檐与单个斜面近似|屋檐外挑、实际坡面的细分、天窗；方向缺失不可随意替代|
|pyramidal/dome/onion/complex类|类别依据或待处理队列|仅类别不能确定顶点位置/曲面截面/复杂屋脊拓扑；不应强制编成同一种通用模型|
|`building:part`足迹+各自高度/min_height|有来源的分段体量|窗位、柱廊、雕刻和真实表面材质|
|roof/facade material或colour|表面颜色/材质类别|真实照片纹理、开窗位置或凹凸几何|

屋型加参数能支持“依据来源参数生成的屋顶”，不等于取得测绘认证的LoD2/LoD3。只存在屋型而缺坡高/朝向时，可以在明确标记推定的前提下做视觉改善，但不能把默认值称作逐栋精度证据。对自交多边形、孔洞、复杂屋型、不合理负值/单位、坡高大于总高等应记录并跳过或另行审核。

文档原始小文件、抓取HTTP状态存于同目录 `evidence/`；文档许可不替代具体数据的许可证。

## 与缓存来源版本一致的OSM样本核验

为避免“当前way”与缓存planet快照版本不一致，直接请求以下3个已记录版本，均HTTP 200：

|来源版本API|原始OSM标签|缓存Overture值比对|
|---|---|---|
|<https://api.openstreetmap.org/api/0.6/way/1372574254/1.json>|skillion; roof:direction=347; roof:height=21.5; height=24.5|逐项相同|
|<https://api.openstreetmap.org/api/0.6/way/156346098/6.json>|skillion; roof:direction=54; roof:height=9.5; height=13|逐项相同|
|<https://api.openstreetmap.org/api/0.6/way/1371942058/2.json>|building:part=roof; skillion; roof:direction=167; height=35; min_height=29.75; 无roof:height|逐项相同|

这证明**这三个样本**中方位角未做旋转，height也未改为height−min_height。应按原始OSM下坡方位解释这些skillion；第三例顶点高度是离地35m，不能因Overture文字描述而加29.75m变成64.75m。缺roof:height不能无标记地认为35−29.75必然是实际坡高。

以上是有限样本证据，不能据此断言所有来源、所有字段或未来ETL都相同。当前完整缓存非平屋顶候选中带`roof_direction`的128条均为skillion，因此本轮没有可做同样精确版本比较的gabled/hipped方向样本。保留来源属性、按数据源区分语义仍有必要。证据为 `evidence/osm-direction-sample-check.json` 和对应历史way JSON。OSM API自身明确返回ODbL许可链接。
