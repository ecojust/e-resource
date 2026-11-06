# 上海建模接续入口

本页帮助新会话找到可执行的下一步，不代替实际队列和资产验收。先读 [协作规范](../AGENTS.md)、[工作索引](INDEX.md) 和最新任务，再核对当前 Git 状态。仓库有大量资产，按任务恢复所需文件；不要全量扫描或重新下载全市模型。

## 当前先做什么（2026-11-06接续）

先完成第38项上海邮政总局 `hongkou-general-post-office` 的最终验收与发布收尾，再制作第39项宏恩医院。用户本轮要求完善规则与历史，并把全部未提交改动保存为提交；这不等于邮政总局已通过最终验收或已推送。详见[本次请求](2026-11-06-001.md)与[模型过程](2026-11-04-002.md)。

| 状态口径 | 实际情况 |
| --- | --- |
| 已有公开基线 | 大世界交付时为83处入口、黄浦29处；模型提交 `215d582eefeb9f584b60f4c5625b283bb1dd374e`，发布记录 `82eff72291b2529d433217fd72773617c8bde494` |
| 本次接手的Git起点 | `c59174528765c104f09295ef10132b4bb4f63ce5`，master；此前规范和历史已经提交，本栋代码与资产当时仍在工作区 |
| 当前开发目录 | 84处＝40处既有＋44处候选，虹口5处；46份资产清单／184件资产是另一个统计口径，不代表84处已公开验收 |
| 邮政总局候选状态 | `candidate_delivered`，四资产、源码、定位与候选画面已有证据；本栋没有 `published_commit`，最终浏览器与发布报告待生成 |
| 已完成的候选检查 | 5图及模型HTTP字节通过有限接受；原执行因外部PMTiles CORS错误保留 `completed:false`，另有2条同源取数警告 |
| 原生与几何 | 最终3图和实际Blender重开通过；修正前8图单独绑定旧raw，不能当最终资产截图 |
| 后续新模型 | 第39项 `jingan-country-hospital`，宏恩医院历史主楼（华东医院干部病房楼），静安延安西路221号；仅预研，未制作 |

本轮提交是保存全部本地进度，公开文件未重新核对；准确提交号以 `git log -1 --format=%H -- history/2026-11-06-001.md` 为准。不要把旧日志中的83处、当前README中的84处或队列里的候选状态混为同一发布结论。

## 恢复邮政总局的操作顺序

1. 先核对Git及[清单](../projects/shanghai/assets/models/candidates/hongkou-general-post-office/manifest.json)。本次接续记录的manifest SHA256为 `83715c205b4f083524dc977e218fdc3abdc63204bb400bb9ea558d83a6bcafb8`，四资产合计35,665,440字节；变化时重新判断受影响证据，未变时不重复重建模型。
2. 阅读[候选接受](../projects/shanghai/data/audit/postal-office-v1/candidate-acceptance.json)、[原执行](../projects/shanghai/data/audit/postal-office-v1/candidate-stage.json)、[独立候选画面复核](../projects/shanghai/data/audit/postal-office-v1/independent-candidate-visual-review.json)和[地图合同](../projects/shanghai/data/audit/postal-office-v1/footprint-review.json)。默认候选主图是在后台仍加载时拍摄，只证明定位与灯牌；最终街墙替换以目标owner和clip已就绪后的画面核验。
3. 完成最终84处目录下的实际浏览器检查：主图、完整／LOD切换、近景源替换和邻楼、整塔与屋顶、桌面和窄屏、灯牌缩放、真实鼠标／触摸、四项下载。`browser.json`、`qa-contract.json`、最终元数据／独立浏览器／Root复核及`publication.json`目前均待生成，不能链接成已有通过证据。
4. 外部PMTiles CORS异常仍是已知限制。透明网络代理只讨论过方案，没有最终执行报告；若用于测试，须保留同一URL与Range、206响应范围、源与转交字节哈希及仅补响应头的说明，不能用空瓦片，也不能据此宣称线上CORS已修复。
5. 浏览器通过后更新实际状态，运行仓库内本轮 `check-metadata.py`、`check-preservation.py` 及适用检查，再提交验收收尾。源脚本中的固定历史基线有其用途；仓库外临时提交脚本若硬编码HEAD为 `c591745...`，本次提交后已经过期，不可直接执行。
6. 真正发布时推送并对照确切模型提交核对公开字节，之后写入本栋 `published_commit`，生成真实模型时间。当前只是中途保存进度，README的“未记录”不应自动填入文档提交时间。

必需源码与现有证据均随本次提交保存。上轮 `/workspace/shanghai-postal-*` 是临时缓存，可能在后续环境消失；其中未发布的最终QA脚本只能作为可选参考，须从仓库内已有候选脚本和同类已验收流程重建并重新绑定输入，不作为唯一接续入口。上一轮子agent不一定仍存在，应重新核对活跃任务和文件分工。

## 邮政总局完成后再做宏恩医院

读取[有限预研](../projects/shanghai/data/model-todo/country-hospital-preflight.json)，区分1926历史主楼与1951成立的华东医院机构、现代院区；补侧后面、屋顶与地图身份，不用约1.1万平方米建筑面积直接缩放足迹。下栋接入还需检查 `build_candidate_city_integrations.py` 的 `DISTRICTS` 和 `sync_readme_districts.py` 的 `PREFIX_DISTRICT`，目前没有 `jingan` 支持。本轮不开始这栋模型。

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
