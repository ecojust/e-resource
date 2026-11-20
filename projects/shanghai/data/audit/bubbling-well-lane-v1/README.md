# 涌泉坊中央过街楼核验

与 2007、2009 年实拍逐项比对后，第二版增加了上层双拱窗中间的扭纹石柱和统一窗台、扇光、成对方窗的波浪檐，并将底层小拱内的店窗向后移至侧室前部。临街面砖、拱石、牌匾文字、柱头及折向两侧的活动门扇均有实体几何。[照片与建筑志](../../../source/precise/jingan-bubbling-well-lane-gate/reference-review.json) · [初版原生渲染](preflight/initial-gatehouse.png) · [修正后原生渲染](jingan-bubbling-well-lane-gate-preview.png)

四件资产合计 5,798,302 字节。原始及网页近景分别为 55,868 个三角面，远景为 26,420 个。Blender 4.3.2 重开原生后核对了 54 个按材质与部位命名的可编辑网格。三种 GLB 各做 26 次射线检测，覆盖贯通的门洞、侧面石柱、商铺窗和上层玻璃，在中心线三个位置均测得从地面起约 4.11 米的顶棚净高。[原生工程与有向三角面](geometry-native.json) · [三版本射线、地面和底图](placement-geometry.json)

原始城市矢量中最近建筑距门楼约 15.38 米。对可能靠近门楼的两组近景 GLB 解压并展开实例，逐三角形计算保守平面包围框，最近下界为 12.96 米；远景下界为 13.05 米。OpenFreeMap 的 17 个建筑聚合要素中，最近者相距 39.64 米。登记不指定原建筑、切面或需要隐藏的对象。[原始城市面、19 级影像和各组近景](../../../source/precise/jingan-bubbling-well-lane-gate/footprint-review.json) · [放置契约](final-placement-contract.json)

地面障碍由全部三份实际模型在地面上方 0.13、0.98 与 1.70 米处的截面合并得到，包含八块侧室、门柱及墙体。中轴线离最近实体约 1.66 米，步行者半径 0.38 米有净空。街面、门槛、通道、院内、两侧房间和石柱分别设置了探针。[计算程序](verify-placement.py)

同一份 Blender 工程另设街边斜视与行人高度两个机位。斜视图可辨三拱、中央牌匾和门楼侧深。行人图中可看见院端的开口，两侧折叠门扇收在拱脚后。[街侧斜视](street-oblique.png) · [通道入口](passage.png) · [原生工程、相机与图片指纹](native-views.json)

第 104 处整合沿用前 103 条目录记录。新版发布候选站的 182 个真实 HTTP 响应合计 68,489,794 字节，目录、程序、模型清单、四件成品、相邻两组底模与独立网页的 SHA-256 均相符。早期目录的 181 项 HTTP 记录另存于 [第一轮绑定](preflight/initial-map-http-bindings.json)。[目录冻结清单](production-snapshot.json) · [HTTP 检查](map-http-bindings.json)

第一轮 104 处主图在手机与桌面目录中选中门楼，取得近景、门洞内的跟随镜头并核对 12 个地面点。宏块邻楼的 `localModel` 表示对应原始城市三维建筑已接管该矢量，检查按宏块来源和 `candidateModel` 判定。一次加载返回较旧的城市父块，重新调用地图的 `setCityManifest` 后，原版块号、两组近景和邻楼碰撞均可检查。原生城市目录请求的代码时限为 25 秒，本次初检没有保留该请求报错的原文。精细地标 GLB 的 35 秒传输时限属于另一请求。[初检报告](preflight/initial-walk-time-budget.json) · [原生目录重新加载记录](preflight/detail-retry.json)

初检中，真实键盘行走从街侧局部 y=–3.10 米到达洞内 y=5.39 米。软件渲染下每秒推进的帧数很少，该轮在院端见证点前达到测试时限。新版检查在较小的步行视口记录每段按键的实际位置，并延长每段行走的实时时限。[早期门洞内地图画面](preflight/map-walk-inside.png)

新版 104 处整合已从静安区目录实点进入。手机首访在加载原生城市目录时产生 `signal timed out`，门楼本身的已校验近景仍正常显示。桌面重新加载同一页面后，拉近门楼可见六个原生细节组，切远后加载 26,420 面远景。12 个现场地面点分别核对街面、门柱、通道、院内及三处原有邻楼。第三人称人物从街侧 –3.10 米一直用 Shift+W 走至院内 +9.21 米，962 个位置样本均可通行，门楼本体深约 7.25 米。[主图实测、请求告警与采样](main-browser.json) · [桌面](map-desktop.png) · [手机](map-mobile.png) · [门楼近视](map-gate-front.png) · [远景](map-distant.png)

侧向按键的首轮记录只证明人物从通道中心分别接近左、右墙至 x=–1.274 米、+1.274 米。键仍按下时，读取的瞬时速度为 8.5 米/秒；多个轮询样本可能处于同一动画帧。这组记录不足以判定人物已经撞墙。现有侧向实体的直接证据是两侧房间和门柱共四个 `collisionAt` 实点。持续按键和桌面宽度补图采用单独页面实测，结果见下。原来的窄步行画面下方由位置卡覆盖。[首轮原始数据](preflight/104-unreviewed-primary-browser.json) · [已注明采样限制的主报告](main-browser.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 35 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/fa20616fb91626953c40d8ea5209f3610a636f86/projects/shanghai/index.html#landmark=jingan-bubbling-well-lane-gate&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 35 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

820×580 的桌面复查分别从通道内与院侧重新按键前行。洞内 y=3.049 米的画面可见牌匾、石柱和人物；院内 y=9.299 米的画面从门拱下向院内看，拱缘占据前景。第一次完整穿门记录的 962 个轮询样本中，有 28 个不同的纵向位置。[拱内近照](map-passage-desktop.png) · [院侧随行镜头](map-courtyard-desktop.png)

从通道中心线左右各 0.80 米处分别持续按 Shift+A、Shift+D，实测人物在 x=−1.567 米和 +1.567 米停下，两次末速度均为零，按键仍处于按下状态。每一侧均核对四个不同的生产动画帧，下一步扫掠均返回建筑；人物中心仍处在可通行空间内。此次院侧截图时的背景宏块为实际 1,296,608 字节远景父块，六组近景的外观与切换另见主报告。[侧墙独立碰撞实测](passage-browser.json) · [检查程序](check-passage-details.cjs) · [同期背景块](supplemental-background.json)
