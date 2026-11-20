# 虹口救火会临街旧楼与瞭望塔

市房屋管理局第二批名录2F011记哈尔滨路2号。现场1994年市政府保护牌写吴淞路560号及1917年竣工。文献与三组独立照片用于辨出两端砖翼、四开间弧形门面、上下开敞廊、红砖方塔和六角小亭。门扇按2026年街景取红框蓝脚，现弧檐英文为 HONGKOU FIRE STATION，保护牌用历史英文 Hongkew Fire Station。塔顶构件、门窗和翼部屋面尺寸据公开照片估计。[现场牌、照片与年代](../../../source/precise/hongkou-hongkew-fire-station/reference-review.json) · [Blender街角视图](hongkou-hongkew-fire-station-preview.png)

近景及原始模型各35,454个三角面，远景27,046个。Blender 4.3.2重开169件可编辑网格，按材质的有向三角面与原始GLB对应。三档各47项独立检查覆盖四门、两层敞廊、砖翼各排窗、弧面字形、塔窗、开敞街角和继续保留的东段。[近远景与Blender文件散列](geometry-native.json) · [逐项网格复核](surface-probes.json)

城市基准中的3165号为建筑本体，另有全院用地对象。原城市近景与远景分别保留25.32%和25.23%的3165号投影面积。保留部分含武进路后续长翼，16件同瓦片建筑逐项按真实近、远源三角面核验，最小外部净距4.89米。截面只在长翼接合线闭合，长16.92米。开敞前场独立于建筑碰撞。[地块及城市源核验](footprint-review.json) · [配准与封口几何](final-placement-contract.json)

独立网页从项目工作区的真实静态地址打开，桌面和手机均通过完整近景、简化远景及四件实际下载校验。正式122处站点的静态网页、模块、样式、原生文件及三档GLB共16项，已与独立页实测输入逐字节吻合。[正式站单体页输入](viewer-production-inputs.json)。此前的121处主图与加入本项后的122处现状主图尚待实际测试。[独立页浏览器报告](viewer.json) · [网页及依赖输入](viewer-inputs.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

在122处冻结目录中直接调用网页的两种矢量底图裁剪和地面判断。32组要素与20处地面探针均符合预期，两个底图各自留下3165号东段长翼的原始几何，其余15个相邻要素保持完整。弧形前场、吴淞路和武进路的人行区域均可通行。旧诊断器只读取另一种地块字段，未能将本项的实际GeoJSON送入矢量裁剪。报告记录两种资料格式的前后结果与旧格式对照。[独立几何与地面检查](owner-vector-runtime-check.json) · [122处网站的343项实取文件](map-http-bindings.json)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有237组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了14个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收6,737,311字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

## 主图默认取景

正式121处对照采用原底图，122处新版由区目录选择后进入。模型位于吴淞路与武进路转角，以西南斜切凹弧门面和瞭望塔为取景中心。正式站342个冻结输入及4个城市源文件逐一匹配SHA-256，共200,945,062字节。阶段采集时街面、屋顶与远距地面复核仍在进行。[前态](map-before.png) · [手机](map-mobile.png) · [桌面](map-desktop.png) · [阶段收据](default-focus-verification.json)

## 121处至122处主图复核

14076上的121处目录和14077上的122处目录使用各自的实际资源。手机与桌面从普通目的地入口到达吴淞路与武进路口。街面视图能看到弧形开间、两侧砖墙和瞭望塔，俯视图能区分两处矮屋面和原底图保留的东段。远档实际使用27,046三角面的模型。共20处地面、后翼、街道和周边建筑探针通过，源站346份文件的SHA-256均吻合。[六图与输入核验](map-comparison-verification.json) · [主图报告](main-browser.json) · [街面](map-street-facade.png) · [屋面](map-roof.png) · [远档](map-distant.png)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 36 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/3feba51f2ea6f5a7733c37c58cc88be2ca90f640/projects/shanghai/index.html#landmark=hongkou-hongkew-fire-station&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 36 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
