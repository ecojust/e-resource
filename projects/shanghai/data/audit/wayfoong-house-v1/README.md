# 新汇丰大楼 · 汇丰银行职员宿舍

四川中路的这座八层住宅由公和洋行设计，1928年建成，最初供汇丰银行经理和职员居住。2021年起，上海市留学人员之家使用其中二层。市房管局2A048登记地址为四川中路210–220号双号，上海市欧美同学会使用四川中路220号。外滩12号总行另行登记。[挂牌地址、使用单位及影像](../../../source/precise/huangpu-wayfoong-house/reference-review.json)

临街面在二层底座上设四层通贯壁柱，托檐以上另有两层，两端各设方顶端亭。中段各层有五组三联窗。首层两个入口后退，玻璃窗和入口门扇均位于实体洞口后。深色铁窗裙和石面分开建模；后座和中央连接翼围出两处下沉的采光井。2013年的街面照片、2023年三处街景及三个版本的航片提供外观与屋面依据。层高、后座、采光井深度和装饰尺寸为估计。[建模范围](../../../source/precise/huangpu-wayfoong-house/README.md) · [独立模型页](../../../wayfoong-house.html)

旧城市源419与南邻1787的面界有7.86平方米交叠。南邻实际近、远模型的屋面均为22.40米，独立高度裁剪从22.55米起处理419的上段。验证保留了近景所有23,899个可能属于南邻的面，其中261个面在平面和高度上可归到任一方。两栋间的源截面用两段封闭。独立的北侧、后侧建筑沿用其原始几何。[地址与源面](../../../source/precise/huangpu-wayfoong-house/footprint-review.json)


近景和原始模型各49,168面，远景16,644面。原生文件重开后有37个可编辑网格，各材质的面与原始模型逐一比对。三份GLB各检验138个独立射线点，覆盖90道中部窗、两处后退门扇、两处透至低屋面的采光井、檐下窗裙及地块外空域，共414项通过。[三档表面实测](surface-checks.json) · [原生文件及材质核验](geometry-native.json) · [原生总览](huangpu-wayfoong-house-preview.png)

两档模型的实际落位各自对比近远城市几何，两处门槛可从街边走向门扇。邻楼在近景与模型最近相距0.347米，在远景相距0.425米。桌面与390像素手机均点选了「四川中路立面」，实测两档并逐件下载四个文件校验签名。[地图落位](final-placement-contract.json) · [源面和地面见证点](placement-geometry.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [实际下载与加载](viewer.json)

原生文件还重新渲染了入口和两处采光井。前一张能辨门框后退和铸铁窗裙，后一张可辨前后翼之间的两处低屋面。[入口与窗裙](west-door-and-ironwork.png) · [采光井俯视](double-court-roof.png) · [三张图的像素复核](native-visual-review.json)

132处的真实地图已从模型目录打开四川中路220号小汇丰大楼。此前131处场景在同一街段显示原城市建筑，十个对照文件均核过SHA-256。新增后390×844手机和870×660桌面各装入完整近景，实取两段邻楼截面。手机可辨上层窗带和两处低屋面，选中灯牌遮住首层下缘。桌面默认展开导航，同街与外滩的多个灯牌遮挡了部分正面和屋顶，两端默认图均保留这个初始状态。[131处原街景](map-before.png) · [原态和十个文件](control-browser.json) · [132处手机](map-mobile.png) · [132处桌面](map-desktop.png) · [两端载入记录](main-browser-progress.json)

正式地图其余三张实拍分别记录同机位的四川中路街面、上方两处采光井及缩放15.5的远景。街面与屋面实际装入419所属的近瓦片并使用六个裁剪三角形，邻楼低段共墙的两个截面可见。十八处步行见证全部通过，包括两处门口、现街、隔墙保留下段和邻楼。实际场景分别下载网页近景及远景，并读取城市近、远两份瓦片。四个模型文件及两份瓦片的HTTP复取结果与冻结清单相符。[街面](map-street-facade.png) · [屋面](map-roof.png) · [远景](map-distant.png) · [完整浏览器结果](main-map-browser.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 39 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/a58fb5460faddaf61a17e5bf1bf0342e42995b73/projects/shanghai/index.html#landmark=huangpu-wayfoong-house&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 39 项时，有 9 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)

320×568触屏在全城缩放8显示9个可点分组。逐个实点开关后，共读到132个互不重复的建筑名。各按钮的九个位置另用DOM命中测试核对，81处全部落在目标按钮上；随后在分组内输入“汇丰”，实际触选小汇丰大楼并确认名称与地图地址。[分组全景](map-320-groups.png) · [实点前的建筑列表](map-320-selection.png) · [触控与命中记录](groups320.json)
