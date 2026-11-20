# 震旦大学图书馆教学大楼球场侧立面

2020年9月13日的球场侧全景与斜视照片可辨十三组窗。两端各有三联窗，中央为跨层钢窗，两翼各有五组单窗。完成首轮照片配准后，调整了两端窗组的宽度、层高和女儿墙。中央窗最低一段受树木遮挡，模型沿用有照片可见的钢框形式。59.70米总宽按原地块北边估算，层高4.50米采用两张照片的窗头取点。屋面、短侧墙和后部截面为估算。[照片、年代与两栋门牌](../../../source/precise/huangpu-aurora-university-library/reference-review.json) · [同角度几何小图与复算](preflight/README.md)

原始和网页近景均为131,624面，简化远景26,104面。原生工程中有108个独立网格、13种材质，网格与原始GLB按材质逐面核对。重新打开工程后渲染正面，并对照现场照片检查窗组、楼号和窗楣。三档各检查99项，包括弧形窗头、三联窗、红砖竖墩、中央长窗和屋面位置。[原生渲染](huangpu-aurora-university-library-preview.png) · [原生及解码校验](geometry-native.json) · [297项逐件射线](field-checks.json) · [模型下载](../../../aurora-university-library.html)

重庆南路280号的原十二号楼对应底图1079，球场侧以外的原体在近、远档中分别保留70.99%和71.15%。西侧25.8米高的校舍1536距新模型裁切边界约8米，重庆南路225号的博物馆1360距边界约122米。两个原体的近、远景均从对应城市源逐档提取，重合面积为零。15个地面取样覆盖球场、五段略有退进的墙脚、保留后部及两栋邻楼。桌面与手机按预设160°朝向和48°俯角计算遮挡，球场侧10,063个取样点中，从模型自身可见的部分均可从现有城市面前看到。[两栋遗产及有关原体](../../../source/precise/huangpu-aurora-university-library/footprint-review.json) · [近远档与地面取样](placement-geometry.json) · [地图放置](final-placement-contract.json) · [相机视线计算](camera-preflight.json)

正式173处站点由172处版本生成。855项实际HTTP读取核对了823,728,471字节，包括四种模型、原城市近远景来源及此前所有冻结网页输入。逐条比对保留此前所有候选地标，使用该站实际模块复算全城934片裁切、17个宏区、单个宏区最大316片。[逐个文件的网络收据](frozen-http.json) · [地图运行配置与地面检查](runtime-placement.json)

173处冻结站的独立页已在桌面和手机切换近景、远景。完整球场立面在两端的视框内，中央长窗与两侧窗带连续可辨。四件文件均由页面实际下载，逐件核对字节与SHA256。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [桌面远景](viewer-desktop-lod.png) · [手机远景](viewer-mobile-lod.png) · [浏览器收据](viewer.json)

### 全城实景复核

在相同机位打开 172 处和 173 处两个版本，原先一整块灰色校舍的球场侧换成红砖壁柱、连续窗列及中央纵向楼梯窗。高位图能看到立面背后保留的原建筑屋顶。桌面和手机首次成图都与稳定后的同机位截图逐字节相同。楼梯窗近景有地名标签遮住部分右侧窗列，远景下已无法分辨单个窗格。[改前](city-24135/map-before.png) · [手机](city-24135/map-mobile.png) · [桌面](city-24135/map-desktop.png) · [楼梯窗](city-24135/map-central-stair-window.png) · [屋面](city-24135/map-roof.png) · [街区远景](city-24135/map-distant.png)

实测 18 处地面及相邻楼体位置，包含原震旦博物馆与两处邻校舍底图编号。用最终站点重新读取页面、浏览器模块、资源清单和四件下载，逐项对照最初浏览器验收和冻结源文件。[两代全城站点](city-24135/two-served-sites.json) · [原城市场景](city-24135/control-browser.json) · [细化后场景](city-24135/main-browser.json) · [独立页文件核对](independent-viewer-24135.json) · [逐图记录](city-24135/visual-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/c8b1fc328cb0342a7572c70bc25e1e2184ea36d4/projects/shanghai/index.html#landmark=huangpu-aurora-university-library&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 10 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
