# 上海街道与建筑模型 TODO

根目录[README完整待办](../../../../README.md#模型-todo逐条制作与街道资料搜集)由`queue.json`、`discovered-buildings.json`与`discovered-streets.json`生成。当前收录1,058处历史建筑登记和1,038条道路名称线索，另列既有地图搜索快照中的1,036条具名源要素，待补建筑资料；这些集合会重叠，不能相加当作建筑总数。属于可继续扩展的资料发现快照，尚未穷尽上海所有街道或可查资料。

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

## 署名与许可

维基百科编者，《上海市优秀历史建筑》（版本95304946）及道路列表／分类；具体原文、取得日期、响应SHA256与字节数见各JSON的`sources`。基于维基百科整理的名录及其生成表格采用CC BY-SA 4.0（https://creativecommons.org/licenses/by-sa/4.0/），属于本目录与根README待办表格的许可说明；不改变其他原创代码和模型的MIT许可。官方名单保留机关署名和原始出处。本库不再分发整篇网页或第三方照片；照片许可须在制作前逐文件核验。

地图身份线索独立保存在`named-map-leads.json`，从已有`data/audit/landmark-candidate-features.geojson`的22,270条搜索要素提取1,036条具名记录，保留原UUID和逐条来源，不复制几何。OSM派生名称／元数据：© OpenStreetMap contributors，ODbL-1.0；其他来源按逐条元数据与项目来源声明处理。该索引只是地图身份，须补建筑照片／文字后才能进入制作队列。

崇明学宫追加资料见[chongming-archival-discovery.json](chongming-archival-discovery.json)：保存旧官网三页与2021区政府文字的哈希、已述尺寸、地址与方位，以及牌坊题名、明伦堂高度等冲突。中央棂星门与两侧门分开记录，照片未覆盖的范围不随中央候选自动完成。
