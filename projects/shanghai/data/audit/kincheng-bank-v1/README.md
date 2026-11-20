# 金城银行大楼 · 江西中路200号临街主楼

## 外观与工程

模型覆盖江西中路一侧的西立面和对应主楼。2015年整体照片和2021年发布的入口近照可辨双圆柱门廊、额枋与徽章、中轴券窗、小阳台和两侧窗列。三期正射影像用于比较屋顶位置，未能确定东侧院内各栋的历史归属。冻结地图的临街边长约35.52米、主楼进深约20.41米。成品高度29.75米，楼层、屋面退台、檐线、石材和被遮挡部位均按照片比例估计。当前门头采用后期的“交通银行”字样。[来源、图像日期及许可](../../../source/precise/huangpu-kincheng-bank/reference-review.json) · [照片与建模说明](../../../source/precise/huangpu-kincheng-bank/README.md) · [地图配准](../../../source/precise/huangpu-kincheng-bank/footprint-review.json)

原始和网页模型各有35,368个三角面，远景模型22,680个。重新打开交付的 Blender 文件后，155个可编辑网格按材质的有向面记录与原始模型相符。三份 GLB 各通过35个表面探测，合计105处，核对窗、门廊、中央券、上部退台和侧墙。[原生工程及导出对比](geometry-native.json) · [105处表面检查](surface-checks.json) · [模型清单及下载哈希](../../../assets/models/candidates/huangpu-kincheng-bank/manifest.json)

首轮预览后修整了近景入口。首次复制的入口图有损坏的 PNG 数据块，现有图片取自同一次重开最终工程的完整渲染，已检查所有 PNG 块的 CRC、文件结尾和完整解码，并与参考照片目视核对。[初版预览](preflight/draft-front.png) · [最终整体](huangpu-kincheng-bank-preview.png) · [修正后的入口图](entrance.png) · [作者目视记录](author-visual-review.json)

## 预览和地图

独立页在1250×820桌面及390×844窄屏上分别打开网页、远景两档，四个下载按钮实际取得的文件均符合清单。[独立预览](../../../kincheng-bank.html) · [浏览器记录与下载收据](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

临街模型按西边线中点配准，向内朝77.56°。源1708属于宏块14-13720-6694，绘图时只裁其原建筑。四边向外平移0.55米，可盖住近景26,272个源三角面及远景12个源三角面；近景包其余76,520个三角面距裁剪区最近约2.05米。地面碰撞由交付模型两米以下的真实几何生成，约702.65平方米。底图中东侧院楼、都城饭店和北邻各自保留。[实解码几何比较](placement-geometry.json) · [定位合同](final-placement-contract.json) · [同源复核脚本](verify-placement.py)

加入金城银行后，全市源建筑需要 321 个三角面来限定替换范围。地图按分块选择裁剪数据，并继续限制单次绘制最多读取 320 个三角面。正式数据共 7 张表，最大一张 141 面。实际 WebGL 测试绘制跨分块的 322 面样例，核对移除、恢复时的像素。正式地图的 104 项输入中，103 项字节完全一致；制作队列仅多出三个已公开并已核对的模型提交号。[正式数据运行检查](runtime-placement.json) · [实际 GPU 像素验证](macro-textures-gpu.json) · [输入核对](production-inputs.json)

完整项目回归通过。320 像素宽的手机测试对 89 个入口逐个点击，并检查每个编号的像素尺寸、间距及与地点卡的边界。[完整测试记录](package-regression.json)

主图89处目录中的江西中路入口已在390×844手机与870×660桌面打开。近景实际显示35,368面，远景实际显示22,680面，两档哈希均相符。7处地面探测分别核对楼内、路边、东侧小巷和四栋邻楼。四个交付文件和两份原地图 GLB 的 HTTP 字节均已回读。全市321个裁剪三角面分入7张宏块纹理，单张最多141面，每次绘制上限320。[合并检查记录](main-browser.json) · [实际文件输入](map-input-fingerprints.json) · [GPU及矢量运行检查](runtime-placement.json) · [视图观察](map-visual-review.json)

街对面的屋顶和常驻灯牌遮住入口下部，主图西立面处于街谷阴影，入口饰件另有无遮挡的独立渲染。首轮远景的模型状态已核实，软件截图超过120秒。随后在正式站520×410窗口核对22,680面模型并单独保存远景图，六份HTTP文件均再次校验。冻结原城市建筑近景对照继续补取。[正式远景](map-distant.png) · [远景及文件复核](supplement.json)[手机入口](map-mobile.png) · [桌面入口](map-desktop.png) · [江西中路近景](map-street-facade.png) · [屋顶](map-roof.png) · [截图超时及当时的模型状态](preflight/distant-screenshot-timeout.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 26 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/ca4ed85996ef187b08827807d1ae9661ddf625a3/projects/shanghai/index.html#landmark=huangpu-kincheng-bank&mode=overview) · [固定版本逐文件核对](publication.json)

首次读取 master 的 26 个链接时，有 12 项仍返回旧版本。[首次 master 核验](publication-master-initial.json)

[上海市房屋管理局首批保护编号及门牌核对](../first-batch-register-2026-11-20/README.md)
