# 克莱门公寓西前楼模型核验

原始及网页近档各有63,049面，远档27,763面。Blender重开了可编辑模型，核对物件、材质和三角面。初稿的内翼坡顶在檐下留下暗空；对照2013年的临街照片后，改作前端收坡和连续木檐口。三档各有52处实测射线，检查墙、亮暗钢窗、顶层弧窗、烟囱空口、私人庭门和沿街通道。[修改前预览](preflight/before-hipped-eaves.png) · [原生复核](geometry-native.json) · [三档实测](surface-probes.json) · [原照署名与许可](photo-credits.json)

已登记的西前楼在14-13719-6695内为1925，OSM独立轮廓为w1153659649。三顶点归属和独立远档ID均确认模型只覆盖这栋临街部分。城市近档保留其原屋面投影45.24%，远档保留45.25%。东前楼3746位于共用弄门另一边。八处相邻底模的裁切交叠均为零。沿街内凹庭院、共用弄门和外部通道通行。[城市几何与通行测试](footprint-review.json) · [配准合同](final-placement-contract.json) · [光线取景预检](../../../source/precise/xuhui-clements-apartments-west-front/camera-preflight.json)

正式24201与24202源站分别返回238、239处地标的目录。此前198处候选行逐字节对应。实取1417份文件，共1,222,259,185字节。运行时只对1925号西前楼临街段作局部裁切。地面见证覆盖两翼、私人凹院、共用弄门通道、保留的后段和同组邻楼。[两代目录](renderer-parent-controls.json) · [全量实取](renderer-release-http.json) · [运行时通行与邻楼](renderer-runtime-placement.json)

正式独立查看页在桌面与390像素宽手机上各留四张实图。沿街正面可辨两翼山墙和中央凹院，斜向视角显示临街进深，俯视角可对照两翼收坡及檐口。两种屏宽均从页面按钮切换近档的三个取景，再切换远档复看正立面。四个下载链接返回的文件与签名一致。[独立页面实测与下载](viewer.json) · [桌面斜向](viewer-desktop-full-oblique.png) · [手机俯视](viewer-mobile-full-above.png) · [实测脚本](check-viewer.cjs)

主图用238处的旧城和239处的新城分别打开实测。旧城的原始近档仍遮住同址矢量，西前楼所在分组新增裁片为零。加入新模型后，复兴中路临街两翼与中央退入的窗体连成一体，两侧瓦屋面、烟囱及砖色转角均可见。手机从建筑目录点入并放大，桌面目录与地图点选均实际触发。主图实测27个地面点，同时核对12户近邻，另在独立页保存并核验四种下载。246像素宽的远景窗口能显示地标簇，信息卡遮住下半幅，具体外观请看临街图。[旧城同址](city-31202/before/map-before.png) · [手机放大](city-31202/phone/map-mobile-zoom.png) · [临街全貌](city-31202/architecture/map-street-facade.png) · [瓦顶与烟囱](city-31202/architecture/map-roof.png)
