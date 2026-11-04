# 上海建模接续入口

本页帮助新会话找到可执行的下一步，不代替实际队列和资产验收。先读 [协作规范](../AGENTS.md)、[工作索引](INDEX.md) 和最新任务，再核对当前 Git 状态。仓库有大量资产，按任务恢复所需文件；不要全量扫描或重新下载全市模型。

## 已核对的起点快照

以下状态于 **2026-11-04** 按 `82eff72291b2529d433217fd72773617c8bde494` 核对；后续模型交付后更新此节，并在任务历史中保留旧快照。

| 项目 | 状态与依据 |
| --- | --- |
| 最近模型 | 大世界历史主楼与街角塔，ID `huangpu-great-world`，队列第 37 项已交付 |
| 模型提交 | [`215d582eefeb9f584b60f4c5625b283bb1dd374e`](https://github.com/ecojust/e-resource/commit/215d582eefeb9f584b60f4c5625b283bb1dd374e) |
| 发布记录提交 | [`82eff72291b2529d433217fd72773617c8bde494`](https://github.com/ecojust/e-resource/commit/82eff72291b2529d433217fd72773617c8bde494) |
| 按区入口 | 16 区、83 处建筑与构件入口＝40 处既有＋43 处新增接入；黄浦 29 处 |
| 执行队列 | 37 项制作任务已交付；下一项第 38 项尚未制作，不计入完成数 |
| 下一模型 | `hongkou-general-post-office`，上海邮政总局历史主楼与钟塔，虹口区北苏州路 276 号，名录 `sh-historic-b1-023`，状态 `identity_review` |

数字来自 [queue.json](../projects/shanghai/data/model-todo/queue.json)、[接入登记](../projects/shanghai/data/candidate-city-integrations.json) 和两份 README 的生成目录，属于不同口径。`CURRENT_STATE.md` 下部和资料说明中的旧数字、旧“下一栋”只反映当时状态。

## 下一次收到“继续建模”时

1. 核对 [队列](../projects/shanghai/data/model-todo/queue.json) 当前最早未完成项。若仍是第 38 项，先读 [邮政总局身份预研](../projects/shanghai/data/model-todo/postal-preflight.json)，已有文字与 2010 外观照核对只是预研，不是模型验收。
2. 补现状多向、院落与屋顶资料，确认修缮后外观；核对主楼、钟塔、附属体与地图源身份、边界、高度和柱式细部，再确定有依据的制作范围。
3. 按现有模型目录约定制作源文件、四类资产、manifest 与专项证据；地图定位与模型制作可分工，最终按同一范围和坐标合同核对。
4. 接入主 `index.html`，核对原源替换、邻楼、碰撞、灯牌、目录与名称。同步两份 README、活动 TODO 和状态，完成相关验收后按规则提交与核对公开版本。

当前用户请求是建立开发规则与历史，此次不启动第 38 项制作。

## 大世界的交付边界

已完成沿街四层 U 形主体、街角塔和可见屋顶亭；中庭屋盖现状及完整内院仍待核，独立共舞台／ET 聚场保持独立。2014 照片中的白钢屋盖不能直接当作修缮后现状依据。已建主体不重复列入活动 TODO，具体剩余任务见 [完成范围记录](../projects/shanghai/data/model-todo/completed-model-scope-review.json)。

[来源与限制](../projects/shanghai/source/precise/huangpu-great-world/README.md) · [模型及发布验收](../projects/shanghai/data/audit/great-world-v1/README.md) · [主图直达](https://raw.githack.com/ecojust/e-resource/master/projects/shanghai/index.html#landmark=huangpu-great-world&mode=overview)

大世界公开 `master` 文件曾短暂返回旧版本，随后复查通过。该轮 19 项不可变提交 HTTP 核对见 [publication.json](../projects/shanghai/data/audit/great-world-v1/publication.json)；最终 master 重试只保存在当时仓库外临时记录，不当作本次重新运行的证据。后续发布仍须核对字节和缓存链，不能只看 HTTP 状态。

## 文件与环境恢复

- 从仓库根目录执行维护命令；通用检查见 [AGENTS.md](../AGENTS.md)。Python、Node、Blender 与建模压缩工具按具体源码和验收脚本确认依赖，不假定临时工具安装永久存在。
- 稀疏检出时先用 `git show HEAD:<准确路径>` 或 `git ls-tree HEAD <具体目录>` 核实；按需要增加检出范围或恢复对应文件。不要把本地缺文件计为删除，提交使用明确路径。
- `projects/shanghai/data/model-todo/README.md` 提供来源、许可和采集方法，但其中历史批次说明不是当前执行队列。抓取新资料须逐 ID 合并，保留当前状态及拆分关系。
- 模型的专项脚本可能固定 ID、提交、地图宏块或容量；复用前逐项适配。旧全局布局生成器含固定基线，不能用来覆盖当前登记或旧审计。
- 工作缓存与重型过程输出置于仓库外；最终必需的源码、来源摘要、脚本和验收结果保存在仓库相应目录，日志使用持久链接。无需为纯文档任务重开所有模型或重跑浏览器。

## 用户反复强调的要求

以下摘录来自当前可见对话，按其出现顺序保留关键要求；没有为早期消息补写日期，也不声称覆盖全部历史：

> 稍等已经做好的建筑都要归纳到 按区查看主要建筑下面，按区来；并且像之前的那样提供直接查看的连接；也就是需要把他们接入到全局模型里面去；现在都是独立的模型

> 所有的细节化的建筑，都需要在地图上用精灵图做一个灯牌；无论如何缩放都要能看到；所以你要检查目前已经独立建模的建筑汇总，并在按区查看主要建筑里标注出来数量

> 你新增的这些模型，点击全局查看之后，跟之前的查看网页不一样啊；原因在于你没有将他们接入/projects/shanghai/index.html；readme中所有模型连接都要接入/projects/shanghai/index.html的

> todo里面的如果已经做好了可以移除；然后继续后续模型制作

> 你需要自己逐个实现模型的制作，不要总是我来教

> 你看一下，readme中有的建筑的 “查看网页”显示的模型不一致
