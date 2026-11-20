# 大上海大戏院历史立面

1933年建成的Metropol Cinema位于西藏路。模型依据1934年日景、夜景和约1937年的近正面照片，表现八根分节玻璃灯柱、七组竖纹板、两翼横窗、双语挑牌、雨篷和门厅入口。地方志将原馆列为湮没建筑。上海市房屋管理局第一批优秀历史建筑名单1A023号记西藏中路520号，地方志、旧影像和新影院经营者记500号。[照片及地址核对](../../../source/precise/huangpu-metropol-cinema-historic-front/reference-review.json)

临街面宽约23.70米、柱顶约21.83米，雨篷、墙厚和截面均为比例估计。可见侧返及背面剖切用来展示模型的边界。原馆完整屋顶、后墙、后部观众厅及室内布置的资料不足，未纳入模型。

## 文件与几何

| 文件 | 字节 | SHA-256 |
| --- | ---: | --- |
| 原始 GLB | 862828 | `700210a2060459cd10f794e0f71a26dc80b51b1a353880231e00a18620d6e37e` |
| 网页 GLB | 350464 | `293a174697bd9ae1698aa301ce69f9480efc3ab859675be08cb5428a14e44402` |
| 远景 GLB | 240160 | `97ec19435e7751a792e91d60e75099d1a75c80c3ccd7447b03b78403789c8c17` |
| Blender | 228254 | `f22a1a5b9a1bcfa1a338cb4fe2e7e0c73d0f4eac648246e57f9765f489739100` |

原始与网页版本各12,808个三角面，远景版9,072个。逐材质比较了真实解码的两个网页网格与各自原始网格的顶点和有向三角面。Blender 4.3.2 重新打开交付文件后，122个可编辑网格与原始GLB逐材质匹配。[几何核验](geometry-native.json) · [正立面](huangpu-metropol-cinema-historic-front-preview.png) · [街面斜视](period-oblique-review.png)

## 历史观看

从黄浦区目录选择大上海大戏院，可在当代主图定位原址。点击「查看历史立面」打开独立三维面板，支持旋转、缩放、近远景切换和四种文件下载。点「返回地图」、面板内的「返回当代原址」或按 Escape 返回原来的地图视角。历史模型仅在用户打开面板后加载。它不占用当代商城的城市模型记录，也不参与街道碰撞。[按区目录](../../../landmarks.html#building-huangpu-metropol-cinema-historic-front) · [当代原址](../../../index.html#landmark=huangpu-metropol-cinema-historic-front&mode=overview) · [独立历史预览](../../../metropol-cinema-history.html) · [登记契约](final-placement-contract.json)

桌面和手机尺寸的独立页均已在Chromium打开，完整与远景版本各有截图；四种下载的字节数与SHA-256均已核对。[独立预览浏览器记录](viewer.json)

主图检查从真实黄浦区目录进入原址，分别检查商城和道路上的碰撞、面板前后的视角、键盘与触控返回方式。具备Playwright和Chromium的环境可从项目根目录运行下列命令，其中URL指向已接入该历史条目的上海站点。

```sh
python projects/shanghai/data/audit/metropol-cinema-history-v1/check-history-entry.py \
  --url http://127.0.0.1:8784/ --output /tmp/metropol-map-review
```

正式登记后，91 处地图目的地中有一处以原址打开独立历史模型。此次预发布检查的 117 个输入中，116 个正式文件字节完全一致；制作队列仅增加三个已核对的模型发布提交号。项目回归同时核对了不同尺寸的当代外观相机与历史原址定位。[正式输入](production-inputs.json) · [回归结果](package-regression.json)


## 91处地标站点阶段记录

在91处地标的预发布站，已从黄浦区目录到达当代原址。当时商城取样点有建筑碰撞，西藏中路取样点可通行，历史模型没有进入当代场景。手动打开后，桌面面板加载12,808个三角面的历史立面，鼠标拖动改变了画面。一次软件渲染检查在等待远景的25秒时限内未完成。91处站点的灯牌点击、手机和完整返回流程仍在复核。[阶段记录](main-map-phase.json) · [当代原址](phase91-desktop-site.png) · [历史面板](phase91-desktop-archive.png)

另一次88处地标的定向预检完成了桌面开关面板、旋转、远景、四种下载和返回。手机已核对旋转、远景及下载，在等待面板关闭的5秒内超时。独立历史页面的桌面、手机和下载记录见上方独立预览报告。
