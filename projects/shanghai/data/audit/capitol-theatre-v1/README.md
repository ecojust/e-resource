# 光陆大戏院 · 光陆大楼

上海市地方志记载，1928年2月25日落成的光陆大楼由鸿达洋行设计，西北部下层为原光陆大戏院及楼座，其余空间作公寓和办公室。原戏院入口朝向南苏州路与虎丘路近河转角。1928年照片已有不等高的两座屋顶构筑物，可与2019年航照及2025年街景逐一对正。不同文献记载八层或九层，模型采用现状可辨的八道主要洞口带和第四层附近的腰线。塔顶约41.75米、窗洞进深与背面均为估算。[建筑志、城市档案与实景照片](../../../source/precise/huangpu-capitol-theatre/reference-review.json)

## 模型与地面

原始及网页近景48,576面，远景25,616面。重开Blender工程，163个具名网格与原始模型按材质逐面一致。三个实际交付文件各70条射线，分别检验矩形钢窗凹槽、窗裙同层的腰线出挑、原戏院入户、厢房上方露台、大小两座塔的通风孔和顶帽。[四文件清单](../../../assets/models/candidates/huangpu-capitol-theatre/manifest.json) · [逐材质重开记录](geometry-native.json) · [210项射线结果](surface-checks.json)

[受保护旧楼全貌](huangpu-capitol-theatre-preview.png) · [原戏院入口和窗裙](theatre-door-and-relief.png) · [入口高塔](entrance-tower.png) · [原生视角核对](native-visual-review.json) · [独立查看器](../../../capitol-theatre.html)

## 共墙及邻楼

以具名OSM w293504471、虎丘路142–146号地址和城市源2457定位。西北弧面后东侧退台属独立单体2770，南面为虎丘路128号广学大楼3051。模型与两者分别有0.312和1.378米净距；地面保留门扇前凹入部分，雨篷在通行高度以上。[源面、照片和三期航片](../../../source/precise/huangpu-capitol-theatre/footprint-review.json) · [地图落位及地面](final-placement-contract.json)

近景同组69,510面，缺少逐面编号。检验了992个可能归属任一侧的共墙面，其距裁剪均超过0.324米。其中另有一个旧楼横向折返面，其外顶点超出相邻建筑的实际节点最大外伸距离，单独保留判读记录。远档按单体编号检验。保留沿旧楼后墙的源面窄条在近、远档分别约18.72、18.66平方米。[逐组几何和例外面坐标](placement-geometry.json) · [可复查程序](verify-placement.py)

独立页的正面按钮显示「虎丘路立面」。桌面和390像素手机实点真实按钮，近远景各留一图，同次请求验证全部四个下载的长度与SHA-256。[桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [浏览器操作与下载](viewer.json) · [修正前的按钮记录](preflight/front-view-label.json)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有228组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收7,788,495字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

## 119处正式主图的首次实测

从真实目录点开光陆大楼，390×844手机和870×660桌面的默认视图都显示弧形街面、分级塔顶和附近保留建筑。选中灯牌遮住部分底层门窗；收起列表进入虎丘路近景可看清弧面的外窗和入口。首次实测记录绑定119处目录及页面、脚本的实际SHA-256。当时仍在执行118处原城市同角度的对照实拍及最后远景和下载步骤。[手机默认](map-mobile.png) · [桌面默认](map-desktop.png) · [虎丘路近景](map-street-facade.png) · [状态与实际截图签名](main-map-first-views.json)
