# 中山医院3号楼中央主楼

复旦校史明确指出，1994年登记的优秀历史建筑为西院区3号楼。1936年北向正面与2019年院区反向实拍出自同一份建设成果展，可分别核对正门、两端墙垛、上层廊柱、石栏平台、歇山顶及南坡五座老虎窗。[原始出处及两张原片的哈希](../../../source/precise/xuhui-zhongshan-hospital-main-building/reference-review.json)

| 输入 | 结果 |
| --- | --- |
| 原始和网页完整GLB | 56,912个三角面，两档独立解码后逐面一致 |
| 远景GLB | 29,464个三角面，保留五座老虎窗、长脊和檐角 |
| 可编辑源 | Blender重开后校验82个网格，与原始GLB的表面一致 |
| 三档可见表面 | 156次射线核验窗洞、门廊、窗廊、石栏、老虎窗、屋脊、接墙和空地，并核对山花及窗侧面的朝向、屋檐底面 |

[几何核验](geometry-native.json) · [射线与材质距离](surface-probes.json)

城市底图将这栋163米长的楼整体记为14-13719-6696/2186，来源是名字为“3号楼”的OSM建筑w298235024@3。实测近景源的中央替换面积为1,000.44平方米，两侧保留856.03和1,345.94平方米。远景源对应保留847.82和1,334.02平方米。两个剖面使用远景原有的23.5米高度。近远景剖面的最大位置差约7厘米。同组1132与裁切边界的距离超过26.9米。[原生网格及剖面校验](placement-geometry.json) · [模型放置合同](final-placement-contract.json)

真实OpenMapTiles底图将多个院楼归于同一矢量ID。采用生产裁切程序处理后，3号楼原矢量投影中的2,181.79平方米继续保留。其余相交源、相邻院楼和80米门诊楼保留。[底图实测](vector-source-checks.json)

四层病房之上的石栏、柱廊与黄色屋顶相互独立，可在编辑文件中选取。两翼、另址院楼和室内留待新的实测、分期及影像资料。[编辑源及建模边界](../../../source/precise/xuhui-zhongshan-hospital-main-building/README.md)

两次场景之间，董家渡天主堂的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有252组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了14个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收8,712,277字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

发布候选的125处站点已从桌面和手机分别加载单体近、远两档并核对四项下载。正立面截图可辨檐端、五处屋顶窗、中央窗带与屋檐下的退台。院区前、后不同时期的两翼继续沿用原生楼体。[单体记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [全部386项HTTP输入](final-snapshot-http.json)

在125处入口的地图上，通过 HTTP 实取带版本号的三份地图登记表，以及按 SHA-256 寻址的普通建筑总表、分区索引和替换表。共核对14个请求，返回字节与冻结清单一致。[逐次请求](metadata-cache-http.json) · [本次调整涉及的文件](runtime-input-changes.json)

最终125处站点从目录分别在1280×800与390×844点入中山医院3号楼。六次取景中的北廊、南坡和两翼画面都加载了真实2186/1132组，并读取主楼接两侧翼楼的两段23.5米截面。南坡西端被既有翼楼部分遮挡；北侧近景可见多层病房窗及出挑栏杆。远近GLB、四件下载、周边院内通路与五座邻楼已实测。另核对135份真实HTTP资源和4份目录输入。[主图记录](main-map-browser.json) · [六图目检](map-visual-review.json) · [输入复核](main-map-input-verification.json)

前一版124处的地图从原目录进入院区，2186和1132仍使用同一原生近景，替换与裁切列表为空。[登记前地图](map-before.png) · [124处前态核对](before-browser.json) · [最终125处全量HTTP](ordinary-final-snapshot-http.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/ac8b08c0feaca1fc83683b061a5e03442b785725/projects/shanghai/index.html#landmark=xuhui-zhongshan-hospital-main-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

## 125处入口版本的公开下载复查

在同一份公开城市版本上重新下载了任务62至81的20份清单，以及每个模型的原生文件、原始网格、近景和远景模型。连同5个主图启动文件，共105个文件、184,650,902字节。每项都已核对长度和SHA-256。[公开下载记录](public-city-downloads-125.json) · [本次复查的固定版本](https://github.com/ecojust/e-resource/tree/ee95eabf4850d9c62de7078009f85d81ad813eda)
