# 上海屋顶几何科研数据：三项候选有界核查

日期：2026-10-25。只读查阅官方仓库、官方发布入口、API元数据及一篇1.27 MB论文，不下载城市数据包，不改仓库或模型。这里把“有屋顶类别”“有屋顶高度”“有真实三维屋顶坡面”分别处理。只深入核查下列三项；目录/搜索页只用来发现线索，不作为许可或精度证据。

## 结论

本轮找到一条比纯楼高更直接的新线索：**MT-BR上海约177万建筑的屋顶类别数据，明确有 flat / gable / hip / complex 四类**。它可为参数化屋顶选型提供依据，但本轮未核实数据再分发许可，未取得坡高、屋脊方向或屋顶平面几何；所以尚不能作为可直接上传GitHub的已授权LoD2模型库。GABLE也提供上海屋顶类别，但仍是“二维多边形+类别+高度”，外部数据许可和文件访问待解决。SAT2LoD2是一套依赖DSM及正射影像的生成方法，既未提供上海现成结果包，也有明确软件使用限制。

因此，三项均没有在本轮形成**同时满足上海16区几何覆盖、三维屋顶坡面、明确公开再分发权**的现成资产。此结论仅限本轮证据，不表示其他数据不存在。可以继续推进OSM有明确屋顶标签的局部建筑、或在取得数据包许可及属性样本后针对屋顶分类做有标注的参数化改善；不能将屋顶分类直接称为真实LoD2。

## 1. MT-BR / BuildingDetails-Multitask：最具体的新屋顶类别来源

官方资料：

- 仓库/说明：<https://github.com/ChanceQZ/BuildingDetails-Multitask>
- 直接README：<https://raw.githubusercontent.com/ChanceQZ/BuildingDetails-Multitask/main/README.md>
- 作者公开数据目录：<https://drive.google.com/drive/folders/1vlqWawFdINglfgIYS-KoOpiYP47THuf_>
- 目录内数据文件：<https://drive.google.com/file/d/1VSqa2xI5Lh1qSjrj0p-ekulLyTU5jWZR/view>
- 类别配置：<https://github.com/ChanceQZ/BuildingDetails-Multitask/blob/main/Code/configs/_base_/datasets/coco_instance_multitask.py>
- GitHub元数据：<https://api.github.com/repos/ChanceQZ/BuildingDetails-Multitask>

**上海覆盖证据：** README专节名为“The generated building detail dataset across Shanghai, China”，说明数据已向量化为GeoPackage，包含“1.77 million building entities”，每个实体有 urban functional type 和 roof architectural type。Google Drive目录本轮HTTP 200，公开页面实际列出 `SH_BuildingDetails.gpkg`，显示大小 **462.6 MB**、修改日期 Apr 21, 2024、Download 控件。此处确认的是官方发布和文件可见性，并非已下载和验证每区要素；没有把“across Shanghai”升级为16区逐栋完整覆盖认证。将来需对实际GeoPackage做坐标、16区覆盖、空值、唯一ID与空间错配检查，且源文件本身超过GitHub 100 MB限制，必须处理后分块。

**能增加什么：** 官方训练配置直接写 `auxiliary_classes = ('flat', 'gable', 'hip', 'complex')`，即平、双坡、四坡、复杂屋顶分类。对有足迹的建筑，这可使参数化选型从一律平顶变为有来源支持的类别；必须把自动分类误差及参数推定保留下来。README没有宣称提供每栋屋脊线、坡面高程、坡度、坡向、分体屋面或立面网格。本轮未下载GeoPackage，所以也没有推定它一定含有未说明的字段。

**许可实证：** 官方README没有数据许可声明；本轮GitHub metadata 的 `license` 为 `null`，完整仓库树（`truncated:false`）没有文件名含 `license` 的条目，Drive目录未显示单独数据许可文档。这里应写“本轮未确认公开再分发授权”，不能写成“数据明确禁止使用”，也不能由网页有Download按钮、MMDetection代码的上游许可或论文可下载推定GPKG可任意重分发。若后续获得作者对这份数据的许可证或包内许可，应重新评估。

证据：`academic-evidence/buildingdetails-readme.txt`、`buildingdetails-meta.txt`、`buildingdetails-tree.txt`、`buildingdetails-drive.txt`、`mtbr-config.txt`。本轮没有下载462.6 MB文件。

## 2. GABLE：上海已提供屋顶类型与估计高度，不是现成LoD2坡面

官方资料：

- 仓库：<https://github.com/AICyberTeam/GABLE>
- README：<https://raw.githubusercontent.com/AICyberTeam/GABLE/main/README.md>
- 作者上海下载入口：<https://pan.baidu.com/s/137_vIGuGn1YDtx7oUtm8_w>，README公开提取码 `u11u`。
- 作者读取脚本：<https://github.com/AICyberTeam/GABLE/blob/main/get_objects.py>
- 仓库许可：<https://github.com/AICyberTeam/GABLE/blob/main/LICENSE>
- 论文：<https://doi.org/10.1016/j.rse.2024.114057>

**上海覆盖证据：** README的2024-01-03公告明确发布 Beijing、Tianjin、Shanghai shapefile，下载表有Shanghai独立入口；2024-07-29公告说明曾补缺，应使用该日及以后的数据。说明称每个building instance有 compact rooftop polygon、category、height，分类总体系为12类 rooftop classes。本轮没有取得SHP，不报告上海建筑数量、不保证16区完整。

**实际几何：** 官方 `get_objects.py` 读取 `ogr.wkbPolygon` 几何，以及 `roof_type` 和 `height` 两个属性。README并未提供屋脊方向、坡高、屋顶平面Z坐标或立面细节。可以帮助区分屋顶类别和轮廓/高度，但不能因题目叫“3D building model”就认为包含真实三维坡面，也不把12种roof classes无证据映射成12种可还原的标准坡面。

**下载状态及许可边界：** GitHub资料HTTP 200；百度盘入口本轮连接返回 `Tunnel connection failed: 403 Forbidden`，这是本环境访问结果，不证明外部文件不存在或作者禁止下载。仓库根目录实际有MIT LICENSE，文字明确针对“this software and associated documentation files”。README没有另写外部百度盘SHP的许可证；本轮未取得包内说明或明确将该MIT扩展到外链数据的声明。因此可确认仓库软件/文档MIT，**外链SHP公开再分发权本轮尚未确立**。不把许可证的不确定性写成已知禁止，也不将论文版权自动套给数据。

证据：`academic-evidence/gable-readme.txt`、`gable-get_objects.txt`、`gable-license.txt`、`gable-meta.txt`、`gable-dir.txt`。未下载SHP。

## 3. SAT2LoD2：可生成坡面的方法，缺上海输入/输出数据且软件许可受限

官方资料：

- 仓库：<https://github.com/GDAOSU/LOD2BuildingModel>
- README：<https://raw.githubusercontent.com/GDAOSU/LOD2BuildingModel/main/README.md>
- 实际许可文件（小写）：<https://raw.githubusercontent.com/GDAOSU/LOD2BuildingModel/main/license>
- 论文全文：<https://isprs-archives.copernicus.org/articles/XLIII-B2-2022/379/2022/isprs-archives-XLIII-B2-2022-379-2022.pdf>
- 论文DOI：<https://doi.org/10.5194/isprs-archives-XLIII-B2-2022-379-2022>

**能力与覆盖：** 方法输入是卫星多视影像派生DSM和正射影像，通过建筑分解与模型拟合重建LoD2屋顶，的确超出了仅有高度的LoD1。但论文实验区明确是 Columbus、London、Trento；训练资料列 Jacksonville、Omaha、Austin、Chicago、Kitsap、Tyrol、Vienna。本轮官方README、论文没有提供上海现成结果数据包或已授权上海输入影像/DSM。算法可在别处使用不等于上海已被重建。

**实际许可而非“开源”标签：** README称open source，但根目录实际 `license` 是OSU EULA：第2节只允许“solely for Your internal, non-commercial purposes”；第3节不得向第三方distribute/transmit/display Works，且不得modify/translate/adapt/merge/make derivative works。本轮只阅读文件，没有安装运行软件或据其开发。论文页脚CC BY 4.0是论文许可，不代替软件/所附材料的EULA；也不直接推断用户独立输入数据产生的全部输出权利。现状下它不能作为本仓库随意改作与分发的软件/示例资产来源，更不能解决上海输入数据缺口。

证据：`academic-evidence/sat-readme.txt`、`sat-real-license.txt`、`sat-directory.txt`、`sat-paper.pdf`、`sat-paper.clean`。未下载软件包或示例城市数据。

## 后续最小验证顺序

1. 优先统计具有明确ODbL许可的OSM roof标签和building:part上海样本，按区报告覆盖，不扩大为全市精度保证。
2. MT-BR是值得保留的具体线索：先确认这份GPKG的数据许可；再有限读取schema、bbox和各区数量，核验四类字段编码及空值。只有完成这些，才适合把类别属性和现有建筑空间匹配，且坡高/屋脊方向仍要另找证据或标记推定。
3. 不需为了本轮审查继续下载数百MB数据或跑全市重建。即使分类获得许可，逐栋窗户、柱廊、外墙细部仍需单独来源。
