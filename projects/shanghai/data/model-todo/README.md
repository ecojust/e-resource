# 上海街道与建筑模型 TODO

根目录[README完整待办](../../../../README.md#模型-todo逐条制作与街道资料搜集)由`queue.json`、`discovered-buildings.json`与`discovered-streets.json`生成。当前收录1,058处历史建筑登记和1,038条道路名称线索，另列既有地图搜索快照中的1,036条具名源要素，待补建筑资料；这些集合会重叠，不能相加当作建筑总数。属于可继续扩展的资料发现快照，尚未穷尽上海所有街道或可查资料。

[官方道路补充资料](official-road-leads.json)另保留186条专题原表记录：2022年主要道路范围170条，以及2023年绿化特色道路16个路段。101条与既有名称初步匹配，42条为新名称候选，43条为组合名称待拆分；这些是原表行数，不是新增独立道路数，尚未并入1,038名称快照。README与街道索引逐行展示待办，来源URL、文号、日期及响应哈希一并保留。

[名称复核](official-road-reconciliation.json)继续检查42个新名称候选与43个组合源行：32个源行可关联已有名称，另提出52个待查名称字符串，不等于新增52条实体道路。蕴川／蕰川及环城路／嘉定环城路保留为别名待核；高架、环线原表所述地面道路不并入高架实体，国道上海段未擅自拆分。README逐行呈现复核建议，原始1,038条快照、源表范围和原任务状态均保留。

[第一批前20条库存复核](heritage-first20-model-reconciliation.json)将6条名录与既有模型关联，包括名称匹配漏掉的中国银行大楼。海关后翼未建、中国银行西翼高度冲突等范围缺口仍保留；老永安与新永安需拆成两栋，峻岭／茂名公寓先核实体。该报告按所列仓库提交核对源码、清单和资产路径，没有重新验收照片或几何，也不把任何整处名录判为全部完成。

[局部地图标签资料](bund-map-road-label-leads.json)来自仓库已冻结的4个外滩及周边完整PBF，源版本`20261018_080001_pt`。实际核对输入哈希并提取`transportation_name`：746个标签要素中排除6个渡轮和1个没有选定名称字段的要素，739次出现按精确名称字符串组成411组；221组与既有名称索引匹配，190组未匹配。README与街道索引只逐行展示这190组待核标签，JSON保留全部411组及所有原feature ID、class/subclass、语言字段、瓦片来源和出现次数。它们包含桥隧、出入口、服务通道、步道、广场等，**不是190条新道路**，不增加已确认道路实体数、不改动1,038条名称快照。

瓦片覆盖约东经121.46484–121.50879、北纬31.22220–31.25977，仅为中心城区局部。跨瓦片和同名分段尚未按实体去重；缓冲区标签可能超出名义瓦片边界，几何尚未裁切或配准到区属。MVT feature ID没有被认定为OSM way ID。标签与官方原名及52个待查名称的交叉匹配仅提示文字相同，不证明道路实体相同或沿街建筑已获得可建模资料。全市水面冻结包仅保留`water`层，不能据其覆盖范围推称全市路名已经取得。

## 来源与口径

- 建筑登记覆盖现今16区，前四批632处采用维基百科《上海市优秀历史建筑》固定版本95304946，第五批426处直接解析上海市规划和国土资源管理局名单的互联网存档正文。前四批官方存档的访问失败／挑战页状态保留在数据中，不称已核验官方原文。
- 859处登记包含照片文件页链接，状态为`indexed-not-reviewed`。照片身份、年代、视角、许可及是否可用作建模参考需要逐条核查；没有下载或随库再分发照片。
- 一处登记可能是里弄、建筑群、多栋院落或多地址，必须拆栋后再建模。名录中的旧称、现称、历史区名和拆除提示保留。街道分类只给出区属线索；跨区、旧路名、同名路及繁简别名仍须核对。
- 1,038条道路来自道路列表及20个道路分类；该列表自行注明不完整。覆盖各区的历史建筑登记，不等于各区全部道路已完成搜集。具体“区属待核”数量以生成街道索引为准，不据此推算全市缺失街道数量。
- 街道与建筑的`address_match_building_ids`只是名称子串匹配，尚未核对区属、地理位置或具体楼栋；`possible_existing_models`也只是查重提示。已有模型必须比对范围，不能重复计数或自动验收。
- 40个城市入口和6个既有独立候选记录在制作队列的基线清单中。普通精模目录21条是城市入口子集。新候选在执行队列单独记载；与全市1,796,419个基线渲染要素不可直接相减计算完成率。

## 执行规则

1. 按`production_queue.order`逐栋执行；当前条目标记`in_progress`。每条先明确单体身份与参考范围，再生成模型。
2. 制作近景、远景及可编辑文件，记录可核实尺寸、估计项、来源和许可证。完成几何、原生重开、预览及网页检查后才标记`candidate_delivered`；候选不等于照片精确复原或原址配准完成。
3. 每完成一栋立即提交主分支，只暂存明确的新增／修改文件，检查没有`D`或重命名删除。清理已提交的本地模型可以采用稀疏检出；保留源码、来源、状态及检查记录。
4. 当前制作队列之后，按建筑名录批次和编号顺序核对身份、已有模型、照片和楼栋拆分，形成新的制作项。遇到资料不足就记录缺口，推进下一条有依据的建筑。
5. 道路线索按现有索引逐条读取原文，寻找沿街具体建筑与照片／文字，追加新条目。对16区继续补充权威道路清单并对账，不能把本次列表称作“全市全部”。

README 中的模型文件大小统一使用十进制 MB；通常保留两位小数，小于 0.1 MB 时保留三位。资产清单 JSON 的 `bytes` 字段保留精确值，用于校验；更新 README 时从该字段换算。

## 更新与复验

```sh
python projects/shanghai/tools/build_model_todo.py
python projects/shanghai/tools/build_model_todo.py --check
```

抓取工具在`tooling/`，固定依赖见`requirements.txt`。使用`--cache`将响应存入仓库外，使用`--output /tmp/new-*.json`写新快照；`--offline`重放缓存。抓取结果须逐ID合并，保留任务状态、拆分关系和既有模型关联，不可直接覆盖正在执行的队列。

```sh
python projects/shanghai/data/model-todo/tooling/discover_heritage.py --cache /tmp/shanghai-heritage --output /tmp/new-buildings.json
python projects/shanghai/data/model-todo/tooling/discover_streets.py --cache /tmp/shanghai-streets --output /tmp/new-streets.json
```

局部地图标签的复验脚本位于[../../tools/extract_bund_road_labels.py](../../tools/extract_bund_road_labels.py)，依赖Python标准库及`opencc-python-reimplemented==0.1.7`；提取时Python版本和全部输入SHA256见JSON。脚本不请求网络：先读工作文件，否则读取已有Git对象，并禁用Git延迟抓取。所需原始瓦片不在本地对象库时会报错，不会在线补取。仅输出新提案快照，不覆盖道路基线或执行队列。

从仓库根目录复验，先确保8项冻结输入已在本地：

```sh
python -m pip install -r projects/shanghai/data/model-todo/tooling/requirements.txt
python projects/shanghai/tools/extract_bund_road_labels.py --repo . --output /tmp/bund-label-recheck.json
```

`/tmp/bund-label-recheck.json`是复验输出位置；正式记录仍为本目录的`bund-map-road-label-leads.json`。复验后应比较输入哈希、411组稳定ID和逐次出现记录；生成时间、依赖环境和输入读取方式可能不同。JSON内标记待核，不把重跑结果直接合并为新街道实体。

## 署名与许可

维基百科编者，《上海市优秀历史建筑》（版本95304946）及道路列表／分类；具体原文、取得日期、响应SHA256与字节数见各JSON的`sources`。基于维基百科整理的名录及其生成表格采用CC BY-SA 4.0（https://creativecommons.org/licenses/by-sa/4.0/），属于本目录与根README待办表格的许可说明；不改变其他原创代码和模型的MIT许可。官方名单保留机关署名和原始出处。本库不再分发整篇网页或第三方照片；照片许可须在制作前逐文件核验。

官方道路事实索引来自上海市绿化和市容管理局《上海市主要道路（河道）和景观区域范围界定》（沪绿容〔2022〕104号）及《2023年上海市绿化特色道路名录》（沪绿容〔2023〕483号）。仅整理名称、范围、明确区属等事实及原文链接，未发现开放许可声明，不将维基百科表格许可扩展至官方原文。主要道路表无区属列；绿化名录仅覆盖15区的16个路段，不能据此推断完整道路覆盖或逐栋建模依据。

地图身份线索独立保存在`named-map-leads.json`，从已有`data/audit/landmark-candidate-features.geojson`的22,270条搜索要素提取1,036条具名记录，保留原UUID和逐条来源，不复制几何。OSM派生名称／元数据：© OpenStreetMap contributors，ODbL-1.0；其他来源按逐条元数据与项目来源声明处理。该索引只是地图身份，须补建筑照片／文字后才能进入制作队列。

崇明学宫追加资料见[chongming-archival-discovery.json](chongming-archival-discovery.json)：保存旧官网三页与2021区政府文字的哈希、已述尺寸、地址与方位，以及牌坊题名、明伦堂高度等冲突。中央棂星门与两侧门分开记录，照片未覆盖的范围不随中央候选自动完成。

局部道路标签的OSM派生数据：© OpenStreetMap contributors，OpenFreeMap / OpenMapTiles，ODbL-1.0；来源版次、原瓦片URL、边界及响应哈希见`bund-map-road-label-leads.json`。这部分数据不套用维基百科表格的CC BY-SA许可。提取代码采用项目MIT许可，未再分发参考照片，未使用建筑地址字段生成道路列表。

[上海大厦与俄罗斯领事馆地图轮廓复核](heritage-next-footprint-review.json)保留4个OSM源要素、原始身份与米制计算。大厦两个具名要素共享外包，另一个无名内凹部件明确关联同一主楼；部件所在层级和历史墙线未确认。领事馆的碎片数不是楼栋数，地图楼层与文献冲突继续保留。目标[GeoJSON](heritage-next-source-features.geojson)按ODbL标注；邻域混合来源几何及图只留本地研究。离线复验用[提取脚本](../../tools/extract_heritage_footprints.py)，依赖和固定提交见报告。

[第一批第21–40条库存复核](heritage-next20-model-reconciliation.json)按固定提交核对49项元数据；20条均未在已登记精模中找到确切对应，仍待身份、拆栋与来源核对。徐家汇天主堂与藏书楼南楼、沙逊别墅与沙逊大厦、旧海关官邸与江海关楼等同名近名对象分别记录，未新增几何验收。

[国际饭店、跑马总会与大光明参考](heritage-following-building-references.json)已按原名录顺序加入队列19–21，保存官方／地方志及署名转刊的事实、照片与历史平面来源、拍摄时点和使用条件。国际饭店83.8／83.6米、跑马钟塔次级53米、大光明16／30.5米与楼层口径均保留未解，历史面积与现状加建范围分别列出；照片和图纸仅供参考，不随库再分发。

[后续三栋的冻结地图轮廓](heritage-following-footprint-review.json)保留国际饭店、跑马总会和大光明的3个OSM源要素与[原始目标几何](heritage-following-source-features.geojson)。三者均无可用高度、层数或子部件分段；外框不是已确认历史墙线。跑马总会地图长轴约98.45米与次级文字“长逾100米”未调和，不能缩放凑值。来源ODbL及离线[复验脚本](../../tools/extract_following_footprints.py)见报告；混合来源邻域图不随库发布。
