# 小桃园清真寺主礼拜殿

小桃园街52号的主寺与24号清真女寺各有门牌。主寺院内东立面有三扇双开木门、两根独立圆柱和两端壁柱，二层三个圆券窗下悬“顯揚正教”匾。2014年远照、2015及2025年的院内照片和两期航空影像共同定位主殿。市级保护牌记1930年竣工，寺内沿革记1925年动工后两年余建成，两种记载均保留出处。街门、院附翼和净身堂单列。[保护牌与复建日期](../../../source/precise/huangpu-xiaotaoyuan-mosque-prayer-hall/reference-review.json) · [资料、照片和本次范围](../../../source/precise/huangpu-xiaotaoyuan-mosque-prayer-hall/README.md)

原始及网页近景各56,708面，远景32,332面，Blender复开后确认190个可编辑网格。三档各作35次射线检查，核实三扇底层木门、扇形上亮、二层弧窗的石套和钢框、两侧圆窗、两根门廊柱、四座绿穹顶、中央金色亭顶与月牙，并穿过亭柱间的敞口。主殿基座约24.9×18.8米，金杆上端的月牙约23.34米；侧后开窗与垂直尺寸按公开照片比例估算。[三档实测](opening-rays.json) · [原生复开](geometry-native.json) · [原生预览](huangpu-xiaotaoyuan-mosque-prayer-hall-preview.png) · [文件与SHA-256](../../../assets/models/candidates/huangpu-xiaotaoyuan-mosque-prayer-hall/manifest.json)

原生实名地块1550涵盖52号院落中多幢建筑。沿主殿在东侧门阶外和南边界设置一个折线截面，近景保留928.45平方米（62.08%），远景保留920.41平方米（62.03%）。近、远原生接缝上缘均为6.40米，其中近景全组存在投影中心等距的面，均在裁区两米之外，改变其归属对裁去面积的影响低于0.0001平方米。另六个同组源在两档均无裁切，和全部附近地块的最小间距约0.52米。10处地面检查包含院前、台阶平台、主楼、西侧转折以及保留的南、东两处。[地块、接缝及地面](footprint-review.json) · [放置合同](final-placement-contract.json) · [桌面与手机高度下的六个目标](overview-sightlines.json)

在上海项目目录中，按原生底图绑定表提供本地宏区与空的核验目录。

    python -B data/audit/xiaotaoyuan-prayer-hall-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/xiaotaoyuan-audit
    python -B data/audit/xiaotaoyuan-prayer-hall-v1/check-openings.py --work "$WORK" --report /tmp/xiaotaoyuan-audit/opening-rays.json
    python -B data/audit/xiaotaoyuan-prayer-hall-v1/check-overview-sightlines.py --feature-table "$MACRO/feature-table.json.gz" --contract /tmp/xiaotaoyuan-audit/final-placement-contract.json --report /tmp/xiaotaoyuan-audit/overview-sightlines.json

桌面与390像素手机的独立查看器分别加载了近景和远景，四张实际画面均保留从月牙至石阶的完整轮廓。四座绿穹顶、中央金色望月亭及其开敞柱间都可从院侧辨认，四种下载文件SHA-256均与模型清单一致。[独立页](../../../xiaotaoyuan-prayer-hall.html) · [实际浏览器及下载记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

正式城市目录从179处增至180处。两个实际HTTP服务返回的目录字节与各自冻结树一致，原有139个候选记录保持相同。[正式输入及SHA-256](production-snapshot.json) · [前后目录HTTP核对](predecessor-controls.json)

主图的两版已用 Chromium 在同一院侧机位对照。旧版可见连续灰色体块，接入后能辨出两侧圆窗、中央匾额和门柱。保留的院翼仍挡住底层门阶，近拍时名称框覆盖部分二层窗，中央亭顶超出画面上缘。另一个屋面视角能辨出中央金亭及四座绿顶。桌面用鼠标、390 像素手机用触摸从黄浦目录进入主图，两处画面上的名称均能命中主殿。缩至街区尺度后仍可看到标记。十处地面结果均与放置记录一致。两次浏览器运行分别结束，页面、控制台和请求均无报错。[同机位旧图](city-24143/map-before.png) · [同机位新图](city-24143/court-arcade.png) · [手机](city-24143/main-mobile.png) · [屋顶](city-24143/gold-cupola-and-four-domes.png) · [主图记录](city-24143/main-map-browser.json) · [逐图复核](city-24143/visual-review.json)

两个本地冻结版分别有 179 和 180 处入口。24143 端口提供的 935 个文件共 920,442,083 字节，与本轮签名逐件相符。独立查看器原有四张画面和四件实际保存文件的哈希均已复核。[旧版浏览器](city-24143/control.json) · [两版输入及下载复核](city-24142-24143-preflight.json) · [935 个文件的传输记录](city-24143/143-all-http.json)
