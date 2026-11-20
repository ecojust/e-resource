# 新老永安北侧天桥验收

原始 GLB、网页近景和远景均通过逐三角面检查。每个版本在北向窗洞的两排六跨中各取一个点，从街侧射入均先命中后退的玻璃，六处窗间墙探针均先命中砖面。近景 59,964 个三角面，远景 2,652 个，三个文件中的最低顶点距模型地面均为 13.0 米。这一净高是建模估计值。[几何与开口检查](geometry.json) · [检查脚本](../../../source/precise/huangpu-wing-on-skybridges/source/check_bridge.py) · [资产清单](../../../assets/models/candidates/huangpu-wing-on-skybridges/manifest.json)

Blender 重开了 87 组可编辑网格，按功能和开间保留砌体、窗框、玻璃、桥底及接头。北向渲染图中可见两层窗带、浅挑顶边和连续悬空底板。[Blender 复核](native-review.json) · [北向渲染](north-elevation.png)

北桥连接两座既有永安模型，南侧另一座桥仍待补证。背侧墙面与屋面细部含估计。[拍摄年代和模型范围](../../../source/precise/huangpu-wing-on-skybridges/README.md)

单体网页在桌面和窄屏分别加载近景与远景。Chromium 通过页面下载按钮取得四份文件，核对 SHA-256 后与清单一致。[网页检查](viewer.json)

主图外的旋转预览按天桥北立面设定正视方向。初次检查时侧向灯光在南面，街侧窗框和砖缝偏暗。调至街侧后，桌面近景和窄屏远景都能辨出上下两排六窗。四个下载按钮逐件核对大小与 SHA256。初版保留桌面近景示例及检查记录。[初次桌面预览](preflight/north-elevation-before-lighting/viewer-desktop-full.png) · [最终预览](viewer-desktop-full.png) · [窄屏远景](viewer-mobile-lod.png) · [下载实测](viewer.json)

天桥是悬空外景。地图登记按三档模型的真实最低顶点、比例和标高校验了 13.0 米净空，不生成桥墩或地面障碍。两栋既有主楼保留，浙江中路桥下五个取样点均无建筑碰撞。伸向老楼的接头在两档模型中均与实体墙面搭接；新楼一侧的实墙带和中央壁柱可见搭接，部分探针从原模型的窗洞穿过。这个结果只能定位外观接头，实际支承构造仍待原图。[原址及路面核验](footprint-review.json) · [接墙探针](attachment-check.json) · [窗洞与搭接范围](attachment-review.json) · [目录增量](catalog-preservation.json)

项目完整回归通过，含相机与地图碰撞、普通建筑模型目录和 20 项引用资料策略检查。[执行记录](package-regression.json)

87 处入口的主图上，桌面与 390 像素竖屏实载桥身，鼠标与触屏均选中北桥。320 像素全市视图的常规截图超时，随后保存了同一状态的诊断图，并在独立会话点选 87 号、返回近景、下载四件文件逐一核验。桥下五个路面点通行，两侧楼内对照点保持碰撞。[分次浏览器实测](main-map-closure.json) · [截图与几何目检](main-map-visual-review.json) · [触屏与下载](touch-return.json) · [地图输入记录](main-map-sources.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 26 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/0157505779cc4c95243ad88203b30ba9e297cfc8/projects/shanghai/index.html#landmark=huangpu-wing-on-skybridges&mode=overview) · [固定版本逐文件核对](publication.json)

首次读取 master 的 26 个链接时，12 项仍返回旧缓存。固定提交的链接已通过全部检查。[master 首次实测](publication-master-initial.json)
