# 新乐路55号圣母大堂

模型取新乐路、襄阳北路转角的五穹顶主堂。上海地方志记1936年2月落成，中央穹顶高35米。北面正门和东面窄窗按2011年两组实照分别制作，两条街的2013年、2020年全景用于核对开口位置。南侧主教公馆另留调查。[建筑范围与来源](../../../source/precise/xuhui-xinle-orthodox-cathedral/README.md) · [北门照片比例](../../../source/precise/xuhui-xinle-orthodox-cathedral/entrance-photo-study.json)

## 原生模型和表面细节

Blender重新打开后可编辑114个网格，使用13种材质。原始和网页近景各98,800个三角面，远景56,736面。每档都用98条射线核对可见的首个表面，覆盖弧顶、鼓座深窗、双扇门、门扇圆饰、扇形窗和石级。原生转角图中，中央穹顶后方的一座次顶被挡住。桌面和390像素宽手机的实际单体页均已切换近远档并核对四个下载文件。[重新打开的 Blender 场景](geometry-native.json) · [转角渲染](xuhui-xinle-orthodox-cathedral-preview.png) · [294项表面检验](surface-checks.json) · [实页与下载](viewer.json) · [图像核对](visual-review.json)

## 与西邻矮墙的交界

原有教堂轮廓与西侧楼体有1.00平方米交叠。按两者屋面高度和14.54米交界线单独处理共墙，保留西楼29.10米屋面。近、远两套原始建筑网格均未损失西邻的整高投影面积，同一矢量要素内的另外两个相邻分块也完整保留。新模型的地面投影为547.45平方米，街墙、台阶与上部檐口分别核对。[网格、矢量分块与地面](placement-geometry.json) · [落位与分段高度](final-placement-contract.json) · [两个屏宽的街面视线](overview-sightlines.json)

最终城市服务从182处增至183处，之前142条候选记录逐字段一致。正式地址下的957个签名文件合计942,964,833字节，均已实际读取并核对SHA-256。新乐路圣母大堂所在近景源新增8个裁剪面，整城共984个；慈修庵所在高密度分区保留322条记录。整城检查还核对了本项目21处地面和16项矢量结果。[实际前后目录](renderer-parent-controls.json) · [957项HTTP核验](renderer-release-http.json) · [实际整城运行检查](renderer-runtime-placement.json)

同一发布脚本尾段也在独立工作树按第145、146项的真实先后顺序重放，新的共享模块得以继承。整份957项签名通过正式快照检查，改写地图模块、整城检查器、标签模块或目录内容的四种反例均被拒绝。[签名快照](renderer-release-snapshot.json) · [实际发布脚本重放](renderer-integration-rehearsal.json)

## 最终城市实景

在182处版本的同一街角，北门位置仍是一片高楼窗墙。183处版本中，从390像素宽的目录点入即可看到大堂的中央穹顶、两侧窗和北门。靠近新乐路，深绿色双扇门、扇形窗和石阶可辨，门牌小字在这个尺度难以读清。斜俯视屋顶时，三座次顶露出完整轮廓，第四座在中央大顶后方只露出一段弧边。缩至街区后，名称灯牌可见，浏览器已切换到56,736面的远景资产。[替换前](city-24146/map-before.png) · [手机目录入口](city-24146/map-mobile-settled.png) · [北门](city-24146/map-north-portal.png) · [穹顶](city-24146/map-five-domes.png) · [街区远景](city-24146/map-distant.png)

最终站点的962件签名输入共943,012,158字节。前态实测曾遇五片邻区网格返回502，逐片取回相符的原始Git对象并复读两份站点后，对照机位通过。西墙剖面是一条带三个顶点的折线，渲染器生成两段墙面。原测试误填一段而超时，根据签名几何另存了两段的测试用例。手机实测完成后，第一次桌面过程在屋面截屏之前中止；另开桌面浏览器完成全部七张图、近远两档资产和21处地面检查。独立页原有四帧及四次下载也与最终站点逐件相符。[两站输入](city-24146/two-served-sites.json) · [全部HTTP核验](city-24146/146-all-http.json) · [邻区恢复](city-24146/preliminary/cache-restored-http.json) · [剖面段数](city-24146/preliminary/segment-count.json) · [逐图核对](city-24146/visual-review.json) · [独立页与实际下载](city-24146/individual-downloads-rebound.json)
