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


## 91处地标站点浏览器核验

在黄浦区目录点大上海大戏院可到达当代原址。桌面上先选大光明大戏院，再俯瞰全市，91枚灯牌中心全部命中各自地标。点击第91号灯牌会显示大上海大戏院的位置卡和「查看历史立面」。打开面板前，浏览器对档案模型的请求数为零。手机上的当代城市块加载了53,852个三角面的原始地图文件。商城取样点仍有建筑碰撞，西藏中路取样点可通行。[主图浏览器记录](main-map-browser.json) · [117份HTTP输入](main-map-inputs.json) · [桌面原址](main-map-desktop-site.png) · [手机原址](main-map-mobile-site.png)

1160×790桌面与390×844手机均在主图打开档案面板，显示12,808面的近景和9,072面的远景。鼠标和触屏拖动改变了模型画面，四种下载各自与交付清单的SHA-256相符。桌面在面板内按Escape、手机轻触「返回当代原址」均恢复原视角、碰撞与按钮焦点；外层「返回地图」也已检验。两端均可改选大光明大戏院，再从搜索返回大上海大戏院，期间没有档案模型请求。[桌面历史面板](main-map-desktop-archive.png) · [手机历史面板](main-map-mobile-archive.png)

早期预检保留了88处站点的手机返回等待超时，以及91处站点首次切换远景后25秒等待超时的记录。上述双端完整复核使用91处站点。[早期阶段记录](main-map-phase.json)
