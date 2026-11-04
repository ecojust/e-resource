# e-resource 协作规范

本文件适用于整个仓库。用户当前指令优先；在已授权范围内持续完成工作，不重复请求确认。本规范不新增普通修改、提交或发布的审批步骤。文件采用工具可识别的 `AGENTS.md` 名称。

## 接手任务

1. 先读 [工作记录索引](history/INDEX.md)、最新任务及相关未完成记录；上海建模同时读 [接续入口](history/CONTINUE-SHANGHAI.md) 和实际制作队列。
2. 执行 `git status --short`、`git branch --show-current`、`git log -5 --oneline`，核对分支、提交和未提交修改。日志中的数字、提交与“下一项”只是带日期的记录，需与当前文件核对。
3. 用户说“继续／下一个模型”时，按 `production_queue.order` 自主推进下一项，完成资料核对、制作、接入、验收和交付。收到明确修复或文档请求时先完成该请求，不擅自切回建模。
4. 保留用户及其他 agent 的修改，不擅自重置、覆盖、清理或强推。可并行分派资料、建模、定位、集成和复核；先划分文件范围，主 agent 负责汇总与最终记录。
5. 仓库包含大量地图资源，优先用 `rg` 在相关目录中查找，避免无范围地列出全部资产或解码全市数据。稀疏检出缺文件时先核对 Git 中的具体路径，按需恢复，不把本地缺失当作仓库删除。

## 项目入口与状态依据

| 路径 | 用途 |
| --- | --- |
| [根 README](README.md) | 资源入口、生成的活动 TODO、按区建筑目录 |
| [上海项目说明](projects/shanghai/README.md) | 网页入口、按区目录与模型说明 |
| [当前交付记录](projects/shanghai/CURRENT_STATE.md) | 最新模型、范围与限制；下方保留的旧轮次不是当前计数 |
| [历史交付](projects/shanghai/DELIVERY_HISTORY.md) | 更早版本的交付原文与证据入口 |
| [制作队列](projects/shanghai/data/model-todo/queue.json) | 执行顺序、单体状态、已有库存与发布提交 |
| [候选接入登记](projects/shanghai/data/candidate-city-integrations.json)、[既有地标](projects/shanghai/data/landmarks.json) | 主图定位、模型 ID、导航与目录的数据依据 |
| `projects/shanghai/source/precise/<id>/` | 单体建模源码、来源、估计项与许可 |
| `projects/shanghai/assets/models/` | 模型资产；具体文件以该模型 manifest 为准 |
| `projects/shanghai/data/audit/<delivery>/` | 对应版本的几何、原生文件、浏览器与发布证据 |
| `projects/shanghai/src/`、`projects/shanghai/tools/`、`projects/shanghai/tests/` | 页面运行代码、生成维护工具、回归检查 |
| `models/` | 上海项目以外的独立模型；遵循各自说明，不强套上海接入规则 |

## 逐栋建模与来源

- 制作前确认名称、地址、行政区、具体楼栋与参考年代，实际阅读文字并查看照片。照片链接、搜索结果和名录名称只是线索，不能直接记为已核验。
- 区分主楼、后翼、独立邻楼、塔、门、院落和建筑组。同名或同一名录下的多个实体须拆分；保留地址、年代、高度及层数异文，不为凑数合并或重复制作。
- 明确本轮有依据的建模边界，记录实据与估计。未见屋顶、隐面、尺寸和装饰不能表述为测绘成果；局部立面交付不能标成整栋或整组完成。
- 交付原始 GLB、网页 GLB、远景 LOD 和可编辑 Blender 文件，保留可重建源码、参数、manifest、来源与许可证。资产逐件严格小于 **100,000,000 字节**；manifest 记录精确 bytes 与 SHA256，README 大小使用十进制 MB。
- 保留原文来源、版本／取得日期、实际核对范围及必要哈希。第三方照片和网页默认仅供研究；要公开再分发或作为贴图，先核实具体授权。维基百科派生表格、OSM 派生数据与原创代码／模型的许可分别维护，不能统一改写为 MIT。
- 资料不足时写清具体缺口，保留未完成状态，再推进有依据的任务；不通过臆造细节或虚报检查来关闭条目。

## 全局地图、目录与灯牌

- 所有已交付的精细建筑和构件都要接入 `projects/shanghai/index.html`。独立预览页可保留作辅助检查与下载，不能代替全局接入。
- 两份 README 的“按区查看主要建筑”收录全部已交付入口，标明总数、各区数量及直接链接。建筑“查看网页”统一为主图 `index.html#landmark=<id>&mode=overview`，或已经验收开放的 `mode=walk`；名称、ID、资产、区属和实际定位必须一致。
- 精细模型从同一登记生成地图精灵灯牌，在视野内各种缩放下持续可见；密集时可用编号，仍应独立点选并显示名称。检查桌面、窄屏、鼠标与触摸，不能只看单体预览页。
- 先核对地图源身份、坐标、朝向、单位及范围，再替换已建部分对应的 owner。近景、远景、阴影和返回场景均须保留独立邻楼及未建范围；不能靠遮掉整组源或扩大模型来掩盖配准问题。
- 模型显示几何、源裁剪范围和地面碰撞分别核对；保留庭院、桥下与合理通道。只有通过相应检查才开放漫游、室内或登楼。
- 修改公共导航、缓存链、裁剪容量或材质时运行相关回归。不能仅放宽校验器来接受错误几何，也不能用单元检查冒充真实 GPU 或浏览器结果。

## TODO、计数与文档同步

- `queue.json` 保留已完成历史；活动 TODO 移除确已完成的范围，未建后翼、院落、连接等改列具体剩余任务。保留原始发现数据、源 ID、拆分关系与旧审计，不整表覆盖已有执行状态。
- 模型入口／构件数、manifest 数、资产文件数、名录条目数、道路名称数和地图要素数是不同口径。按登记去重统计；不能直接相加，不能用入口数减全市源要素数计算完成率。
- 先更新结构化记录，再使用现有生成器同步两份 README、地标目录和 TODO。不要只手改生成表格，下一次生成会覆盖手改内容。
- 模型时间来自该模型资产版本的真实 Git 提交，README 按上海时区 UTC+8 显示；文档修改日期不能冒充模型制作时间。历史数量、固定版本链接与审计原文保留在其版本范围内。

## 验收、维护与发布

- 检查实际输出的完整与 LOD 几何、材料、门窗和屋顶，重开可编辑原生文件，实际查看预览及主图画面。记录通过范围与未验证事项；截图生成不等于已经目视查看。
- 验收记录绑定实际脚本版本、输入与最终资产哈希。生产资产变更后重跑受影响检查；保留失败记录与修复后结果，不能复制上一轮结论或覆盖旧审计。
- 以下命令从仓库根目录执行，按本次变更选择；依赖和稀疏检出输入缺失应先补齐。纯文档修改只做链接、格式及受影响目录检查，不重跑无关模型／浏览器验收。

```sh
python -B projects/shanghai/tools/build_candidate_city_integrations.py --catalog-only --check
python -B projects/shanghai/tools/update_global_model_metadata.py --check
python -B projects/shanghai/tools/build_model_todo.py --check
python -B projects/shanghai/tools/build_landmark_directory.py --check
python -B projects/shanghai/tools/restoration_progress.py --check
python -B projects/shanghai/tools/sync_readme_districts.py --check
git diff --check
```

`--catalog-only` 复用已验收库存，不能代替新增资产核验。新增模型先按生成器 `--help` 使用显式 `--append-manifest` 和新的 `--audit-directory`，避免改写旧交付。各生成器移除 `--check` 后可能写文件，先确认输出范围；旧版 `check_global_model_placements.py` 与 `build_global_urban_placements.py` 有固定历史基线，不作为当前通用检查。

导航、目录、灯牌或俯瞰相机变更时，可运行相关已有检查；模型专项与浏览器检查沿用对应交付脚本并核对其适用 ID，不能直接把大世界等旧脚本当成新模型验收。

```sh
node --test projects/shanghai/tests/landmark-navigation.test.mjs projects/shanghai/tests/landmark-directory.test.mjs projects/shanghai/tests/building-beacons.test.mjs projects/shanghai/tests/candidate-overview-camera.test.mjs
```

- 按既有流程，每栋完成后独立提交主分支；用户另有分支或发布指令时遵从。只暂存本轮明确文件，稀疏检出按需用 `git add --sparse -- <paths>`，检查暂存 diff，避免把清理本地文件变成历史资产删除。
- 明确区分本地完成、检查通过、已提交、已推送和公开文件已核对。公开 HTTP 200 不代表版本正确，应对照确切提交校验关键页面、模块、清单与下载字节；缓存过期时保留失败与重试范围，必要时提供已验证的不可变提交主图链接。
- 更新模型提交时间时可以追加元数据提交，不回写不存在的自引用提交号。检查通过且资产未再变化时，不反复重跑相同重型任务。

## 持续记录与交接

从本规范启用起，每次用户 prompt 在 `history/` 当前任务中保留原话和顺序；新独立任务建 `YYYY-MM-DD-NNN.md`，同一任务的补充继续追加。先前不可得的原话明确注明，历史摘要不冒充完整对话。

每个有意义阶段后，以及暂停、阻塞、交接和最终回复前，更新任务记录与 [索引](history/INDEX.md)。记录实际改动、必要命令／提交、决策依据摘要、结果、持久证据链接、限制和可执行的下一步；详细模型报告继续放各自 audit 目录。规则改变时同步本文件；当前建模顺序或状态改变时同步接续入口，旧快照保留日期。

不记录 token、密码、密钥、敏感环境变量或私有推理过程。用户原话中的秘密用 `[已脱敏：类型]` 替换并说明；只记录可复查结论和简短理由。临时 workspace 路径标明可能丢失，不能成为唯一交接依据。记录格式见 [history/README.md](history/README.md)。

本规范于 2026-11-04 建立，结构参考用户指定的 [pureTV 协作规范](https://github.com/ecojust/pureTV/blob/0a9ca2afd80c48750ed74546dcd984df27308949/AGENTS.md)，内容按本仓库实际流程整理；不引入其 Android、签名或游戏交付规则。
