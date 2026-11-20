# 九江路36号原三菱银行的四柱门廊

市房管局第二批2A044著录中华邮政储金汇业局。2024年市住建委、市历保中心报道了原三菱银行的门廊、高窗与沿革。2015年正面照片、带36号门牌的实名地块和政府报道共同确定街面。西邻九江路50号对应原三井银行，独立门牌点落在重合的88和2301号源内。[市政资料、图片、日期与题名异文](../../../source/precise/huangpu-former-mitsubishi-bank/reference-review.json) · [地块与门牌](../../../source/precise/huangpu-former-mitsubishi-bank/footprint-review.json)

模型按2024年报道所见的金色行名制作。南立面覆盖约28.39米，表现四根通高花岗岩柱、涡卷叶饰柱头、三组后退高窗、两端长窗、五级台阶与成对卧狮。1934年始建，1936年竣工是文献记载的两个不同节点。政府介绍地上五层含夹层，现行OSM标签写六层。模型采用有日期照片和街墙长度推算檐口标高，卧狮与柱头细节为据照片制作的近似。[造型边界](../../../source/precise/huangpu-former-mitsubishi-bank/README.md) · [相机与标高估计](../../../source/precise/huangpu-former-mitsubishi-bank/elevation-estimate.json)

原始和网页GLB各有58,600个三角面，远景有23,464个。Blender重新打开并逐组比对109个网格。每档GLB各测24处材料和实际深度，覆盖后退的门窗、四柱、柱顶、狮身、台阶和檐线。[四种交付文件](../../../assets/models/candidates/huangpu-former-mitsubishi-bank/manifest.json) · [原生重开及材料核对](geometry-native.json) · [72条检测射线](opening-rays.json) · [原生文件渲染](huangpu-former-mitsubishi-bank-preview.png)

在固定宏区14-13720-6694中，1993号源仅替换南面临街段，近景保留原生投影90.12%，远景保留90.30%。六个同组源中其他五个与裁剪区交叠面积均为零。地面的七个探针分别覆盖台阶前人行道、踏步、实柱、铜狮台座、西门前凹入处及两处门扇。对周围源轮廓与标高的视线计算显示，最初49°俯角会被对街楼体挡住，选定−32°方位和40°俯角后，两个视口高度下的六个目标点均可见。[近远源与地面核验](footprint-review.json) · [接入合同](final-placement-contract.json) · [源几何视线测试](overview-sightlines.json)

上海项目内可用固定宏区和空目录复核。

    python -B data/audit/former-mitsubishi-bank-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/mitsubishi-review
    python -B data/audit/former-mitsubishi-bank-v1/check-openings.py --work "$WORK" --report /tmp/mitsubishi-review/opening-rays.json
    python -B data/audit/former-mitsubishi-bank-v1/check-overview-sightlines.py --feature-table "$MACRO/feature-table.json.gz" --contract /tmp/mitsubishi-review/final-placement-contract.json --report /tmp/mitsubishi-review/overview-sightlines.json

独立页已实际打开桌面及390×844手机的近远两档，并在界面中逐项下载核验四种文件。两侧卧狮、底层中央石阶及后退高窗在桌面近景可辨，窄屏远景保留四柱与上方两排窗。[桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png) · [浏览器校验](viewer.json) · [画面核对](visual-review.json)

前一版154处与本版155处的正式目录已经通过实际HTTP请求逐字节验证。原有候选行全部保留，本次增加九江路36号的街面模型；生产签名记录705项输入。[前后版本HTTP核对](predecessor-controls.json) · [生产输入签名](production-snapshot.json)

## 实际城市地图

从前一版154处的按区目录进入浙江第一商业银行，再查看九江路36号。原生近景组有六栋，三菱街面还呈现为统一灰窗墙，台湾银行的228号裁剪已在本组生效。[前态街面](predecessor-street.png) · [前态相机及7份实取文件](predecessor-map-browser.json)

本版155处从目录实点三菱银行。900×650桌面和390×844触屏均能看到四柱和两翼高窗，牌面在屋顶上方，发光点会遮住一小块台阶。贴近街面的补图可辨柱础和两侧狮座；自牌覆盖中央门的部分窗格。两种尺寸的选中灯牌均命中本栋。[桌面默认](main-desktop.png) · [手机默认](main-mobile.png) · [门前台阶](central-double-door.png) · [四柱柱头](portico-capitals.png)

实测近景58,600面，远景23,464面，七个人行道、台阶、柱脚和门扇探针全部与模型合同相合。原生近景仍含228、807、1993、2095、2206、2688六栋。三菱合同作用于1993，台湾银行既有合同作用于228，其余四栋保留各自的原生表面。三菱交界处的实际截面是一段，初版检验曾误将该组的有效裁剪预设为仅1993，第一次运行保留在案。前态用例中未参与断言的段数也已按正式几何订正。[保留的相邻原楼](retained-source.png) · [远档](distant.png) · [六图、两档与四份实际下载](main-map-browser.json) · [原始假设与失败记录](earlier-shared-group-assumption/assumption-browser.json) · [初次前态用例](earlier-shared-group-assumption/before-map-case.json)

本次实景来自21116与21117。213个浏览或下载资源经再次实际请求并核验完整字节，共287,707,826字节，另有六项生成资料独立核对。下一套23116、23117加入台湾银行专项聚焦，分别签入705项与713项。跨版本62次HTTP核对确认三菱登记、各档文件及源合同相同，上一段的照片记录21k两端的实景。[实际输入](main-map-inputs.json) · [两代焦点版本的HTTP对照](focus-23116-23117-http.json)

以155处全量目录重放23117的正式布局，两个视口均只有三菱这一枚可见名称牌，其中心和矩形与21117实际截图逐像素相同。四根石柱每根2,212个真实三角面，中央铜门72个三角面，各自投影均与名称牌零像素交叠。灯点地面位置沿用21117，实拍中仍可见台阶上的发光效果。[23k正式布局与门柱投影](focus-23117-occlusion.json)
