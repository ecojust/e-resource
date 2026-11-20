# 汉弥登大楼的凹角、塔冠与门廊

1930年10月的施工照片已分别注明前景170号公寓和后景的都城饭店。2021年《新民晚报》的外景及采访与2007、2013、2017年的独立照片相互补充。门廊上制作四个单独的“福州大楼”立体字、三幅券窗和入口雨篷。凹角两侧配有住宅窗、遮阳篷及局部空调，退阶肩部设透空双券。模型限于街角及两端短翼。[门牌和照片](../../../source/precise/huangpu-hamilton-house/reference-review.json) · [建模范围](../../../source/precise/huangpu-hamilton-house/README.md)

照片中能辨出凹弧和直翼相交的两个路面控制点，结合2017年相机焦距与地块估算，冠顶约60.5米。测试像点选择、拍摄者眼高和近似像主点后，屋顶可能位于54.9至67.2米。底图的十四层估高为44.8米，两种来源分别记录。[相机估算](../../../source/precise/huangpu-hamilton-house/elevation-estimate.json)

原始模型与网页近景均为39,472个三角面，远景24,136个。Blender重新打开后核对234个可编辑网格和11种材质。实际解码的三份模型均通过29次第一交点或透空检验，包括两侧肩部的天空、门楣四字、门玻璃、住宅窗框和塔尖石槽。[四件模型](../../../assets/models/candidates/huangpu-hamilton-house/manifest.json) · [原生比对](geometry-native.json) · [87条表面检验](opening-rays.json) · [重新打开后渲染](huangpu-hamilton-house-preview.png)

固定底图1844号覆盖实名门牌地块的98.13%。两条长翼和后部保持原生，近景保留其屋顶投影的51.04%，远景保留50.91%。近景中61片三角形既与1844相容，又贴合邻楼边线，全部当作受保护的相邻来源检查。新增裁剪距同瓦片其余近景至少4.24米，远景至少4.31米。六个实物地面点、两种视高下的街面及塔冠视线均有独立记录。[邻楼与原生范围](footprint-review.json) · [接入合同](final-placement-contract.json) · [视线估算](overview-sightlines.json)

第135处城市场景通过实际HTTP与第134处对照，旧候选逐条一致；完整输入收据包含501个文件。[前后HTTP实取](predecessor-controls.json) · [发布快照](production-snapshot.json)

独立页在桌面及390×844手机分别显示近景和远景，并通过四个下载链接验签。[浏览器报告](viewer.json) · [桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png)

从上海项目目录复核，其中MACRO指向四个固定底图原件，WORK为新的解码目录。

    python -B data/audit/hamilton-house-v1/verify-placement.py --macro "$MACRO" --work "$WORK" --out /tmp/hamilton-review
    python -B data/audit/hamilton-house-v1/check-openings.py --work "$WORK" --report /tmp/hamilton-review/opening-rays.json

整楼尺度下，手机仍能看见两边逐级后退的肩部、主门上方三券和塔冠。门楣细字宜放大查看。另有深度射线确认两边肩部在三档模型中都保留透空。[对图记录](visual-review.json)

第135处主地图从目录实点打开这栋建筑。390×844手机可见凹入的沿街正面、两翼和中央塔身，顶部灯牌贴近塔冠。900×650桌面默认展开导航，密集的邻楼灯牌和底部位置卡遮住了大半模型。两端均实际装入39,472面的网页近景，选中本楼，且五栋共用的近景分组只对1844使用11个裁片。对照的第134处目录有94条既有候选记录，逐条一致，四件模型均已实取验签。[手机原帧](main-mobile.png) · [桌面原帧](main-desktop.png) · [当时的选中、瓦片和实取记录](main-map-browser-progress.json)

同一浏览器收起导航后拍下街面、塔冠肩部和原生两翼。街面图能辨凹入的外墙、门洞与门楣，选中灯牌仍遮住部分券窗。塔冠图显示中央塔身两侧的退台，标签压到中央上缘。六处地面点分别核对雨篷下、人行道、入口和主墙。缩到15.45级时，实景切到24,136面的远景模型。目标近瓦片和远瓦片的HTTP字节均与冻结原件相同，179个实际请求文件与4条目录生成记录完成复核。第134处版本另外对91、92两处地点完成15次公开下载，共8,760,779字节。[街面](three-arched-entrance.png) · [肩部与塔冠](paired-open-shoulders.png) · [保留的两侧](retained-source.png) · [远景](distant.png) · [六图与检测结果](main-map-browser.json) · [179个输入核验](main-map-inputs-verified.json) · [前一公开版本下载](predecessor-public-downloads-134.json)

900×650桌面从默认视角收起导航，再点一次页面右侧的加号，缩放从18.074升至19.074，画面里的已绘制建筑灯牌由七块减到两块。此时可辨中央塔身、两级退台和左右两翼。再点一次加号，在缩放20.074时将鼠标从画面坐标（420，365）向左上拖至约（345，148），门楣上方的三扇拱头窗和金色字牌就离开底部位置卡；前景名牌仍遮住门扇下缘。两处放大与这一次拖动都保留123°方向、41°俯角和近景模型的同一SHA-256。[一次放大的全楼](public-zoom-one.png) · [两次放大的初始位置](public-zoom-two.png) · [拖动后的三券窗与门楣](public-dragged-street.png) · [五步控件、相机和SHA记录](public-zoom-steps.json)
