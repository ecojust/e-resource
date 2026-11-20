# 卜内门大楼四川中路东立面

房管局第二批2A047、1937年5月12日的历史照片题注和今天的门牌都指向四川中路133号。《上海名建筑志》记其1922年底落成，原有雕塑有部分散佚。模型按2009、2013和2020年的正面与斜照制作现存五开间街墙。中央阳台下方可辨光面支座，山花中央仍可辨扇贝和侧卷。杨浦区图书馆历史斜照中的扛柱力士单独记入史料。[门牌、照片与来源](../../../source/precise/huangpu-brunner-mond-building/reference-review.json) · [制作边界](../../../source/precise/huangpu-brunner-mond-building/README.md)

五个券洞内分别设置橱窗和内退的中央双扇门。两根带凹槽的巨柱、柱头的正面与侧部叶饰、三角山花、五个开间的大窗与中间楼板带均可单独编辑。六七层的窗洞缩在上部实墙内，两侧和中部的窗墙退距不同。室内、侧后楼面和深处屋顶留待后续取证。[四件模型](../../../assets/models/candidates/huangpu-brunner-mond-building/manifest.json) · [窗墙几何](../../../source/precise/huangpu-brunner-mond-building/source/street_elevation.py) · [山花与叶饰](../../../source/precise/huangpu-brunner-mond-building/source/ornament.py)

原始与网页近景各有43,600个三角面，简化模型19,104个。Blender重新打开87个可编辑网格并比对材质、三角面与轴向。逐份解码实际交付的三份GLB，取得84条表面材质和第一交点深度记录。中央顶层窗的横梃和横梃上方玻璃在三份交付件中都有独立检验。[原生文件与GLB核验](geometry-native.json) · [材质及深度检验](opening-rays.json) · [正立面渲染](huangpu-brunner-mond-building-preview.png)

固定底图14-13720-6694中，1600号轮廓与实名OSM重合97.86%，东侧临街边长约24.62米。近景保留原生屋顶投影的86.47%，远景保留86.72%。同瓦片另四个所有者与本次裁剪无重叠，近景最近相距20.56米。实物三角面校验了六处地面点，固定周边楼体用于检查两种屏幕视高下的默认视线。[底图归属](../../../source/precise/huangpu-brunner-mond-building/footprint-review.json) · [配准检验](footprint-review.json) · [接入合同](final-placement-contract.json) · [默认视线](overview-sightlines.json)

初轮软件渲染在首张桌面截图等待30秒后超时。预加载器把等待时间延长到300秒，随后的完整独立页检查实测桌面及390×844手机的近景和远景，并下载核对三份GLB和Blender原生文件。[独立页浏览器报告](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [画面观察](visual-review.json) · [软件渲染等待设置](viewer-timeout.cjs)

从上海项目目录复核，令 MACRO 指向含固定宏块原件的目录，WORK 使用空目录。

    python -B data/audit/brunner-mond-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/brunner-review
    python -B data/audit/brunner-mond-v1/check-openings.py --work "$WORK" --report /tmp/brunner-review/opening-rays.json


从130处的四行储蓄会大楼版本进入本版，原有90行模型记录逐项保留。向旧版实际请求目录、宏区索引、要素表及近远两份原生模型，核对五份文件的完整散列。130处目录尚无卜内门记录，原有候选也未占用源体1600及其建筑UUID。旧版可读的近景瓦片包含五个独立源。这里的前态证据来自HTTP文件和原生几何。[前版真实文件](predecessor-source-http.json) · [前后目录](predecessor-controls.json) · [467项生产输入](production-snapshot.json)

131处主图已从建筑目录在桌面及390×844触屏分别进入。默认视角可辨五开间和底层正门，山花近景能看到现状贝壳纹饰和支座。两次点击定位均命中卜内门大楼，实测当前近景组只裁剪1600号源，另外四栋保留。六张截图覆盖默认桌面、手机、入口、山花、后方保留面和远景；远景实际加载19,104个三角面的简化文件。[桌面主图](main-desktop.png) · [手机主图](main-mobile.png) · [贝壳山花](shell-pediment.png) · [原生保留面](retained-source.png) · [远景](distant.png)

地图内执行的六个地面查询中，门前街道、挑阳台下的门槛外及南端窗前街道可以通行，凹入的花岗岩踏步、铜门和石墩均返回建筑碰撞。原始GLB、网页近景、远景和Blender文件均实际下载且SHA-256一致。验收同时核对175份浏览器实取资源和四项目录生成记录，包括新版分组灯牌的三个模块；记录中页面、控制台和请求错误均为零。[入口近景](five-arch-entrance.png) · [浏览器实测与四件下载](main-map-browser.json) · [实取文件签名](main-map-inputs.json)

前一版主图的七处近期交付也在同一 GitHub 提交逐件下载复核。130 个入口中，七处均指向各自的模型清单，40 个公开文件合计 89,172,995 字节。[七处入口及下载收据](predecessor-public-downloads-130.json)
