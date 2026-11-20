# 国泰电影院西南街角模型核对

淮海中路870号，第二批优秀历史建筑2C004。以历史照片确认阶梯塔、街角和两侧竖窗，以2024年重开时的黄浦现场图及2025年5月4日正面照确定矩形门罩与两排字标。较早照片里装饰繁复的红金罩属于改造前的外观。[地址、照片与许可](../../../source/precise/huangpu-cathay-cinema/reference-review.json)

原始与网页模型各有54,410个三角面，远景26,710个。Blender重新打开后核验73个可编辑网格、14种材质。新版以两段长度不同的街墙合计范围为单体坐标中点，茂名南路与淮海中路两段都完整入镜。中央阶梯塔、纵向六个字母、横向字标和门罩上方的五个中文独立字均对应2024–25实照。独立解码的三份GLB中，78条材质与深度射线核验中文、横竖两组CATHAY、深入门廊的玻璃门、窗洞、面砖和塔身。字形来自随源分发的小型SIL OFL字体子集。[模型文件清单](../../../assets/models/candidates/huangpu-cathay-cinema/manifest.json) · [原生与GLB核验](geometry-native.json) · [预览](huangpu-cathay-cinema-preview.png) · [字样及窗洞实测](opening-rays.json) · [视觉记录](visual-review.json)

原生2706号来自同一实名OSM影院。保留近景投影的88.07%及远景的88.15%，裁剪限于西南入口尖角，后部观众厅仍由原生城市模型显示。相邻的十个共享文件所有者均无重叠，最近同瓦片源距裁剪边缘约8.84米。实查门廊下的公共路面、门槛、门扇和转角墙脚。源粗模9.6米依据层数估算，塔和旗杆约22米按照片比例估计；其余屋面、内部及舞台另计。[放置证据](footprint-review.json) · [合同](final-placement-contract.json) · [默认相机](overview-sightlines.json)

从上海项目目录运行，MACRO是14-13719-6695宏区目录，WORK为空目录。

    python -B data/audit/cathay-cinema-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/cathay-cinema-review
    python -B data/audit/cathay-cinema-v1/check-openings.py --work "$WORK" --report /tmp/cathay-cinema-review/opening-rays.json

在正式单体页面用 Chromium 156 分别打开桌面和手机视口，切换近景及远景。桌面与手机的两个层级均显示完整旗杆、中央阶梯塔和两段街墙。网页实际下载的三份 GLB 和 Blender 原文件逐一通过 SHA-256 核对。[浏览器记录](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机远景](viewer-mobile-lod.png)

以HTTP读取前序和当前两个冻结站的完整目录，核对前序模型条目逐项一致、本站仅新增本文模型及其裁剪合同。[前后两份目录的响应哈希](predecessor-controls.json)

两次场景之间，尚贤坊门楼、董家渡天主堂、原犹太人总会的默认镜头有调整。其余可拟合镜头的建筑在三种窗口尺寸下共有231组计算，取景参数一致。[场景输入及目录差异](camera-input-revision/input-difference.json) · [逐栋镜头核对](camera-input-revision/camera-arguments.json)

最终场景又通过HTTP逐项读取了13个文件，其中包括本次修改涉及的文件和这栋建筑的四种资产。实收8,164,807字节，均与冻结清单或原文件签名一致。[逐文件核对](revised-scene-http.json)

当前两站从页面入口读取实际主模块和登记表，另外逐一核对本站冻结清单的313个文件。[当前两站实际入口与登记表](current-predecessor-http.json)

正式120处地图从黄浦区目录进入，桌面使用点击，390×844手机使用触屏。两种首屏的街角、竖排CATHAY、阶梯塔和门罩都可辨。119处旧目录的79条候选逐条相同，三个GLB及原生文件均通过HTTP核对完整字节和SHA。两次默认均加载2706所属的真实11成员瓦片，首屏未触发粗略索引重试，记录中未见页面、请求或控制台错误。[手机与桌面的浏览器记录](default-views-browser.json) · [桌面](main-desktop.png) · [手机](main-mobile.png)
