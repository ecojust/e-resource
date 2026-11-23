# 宛平路42号住宅双色砖墙与卷叶凸窗

宛平路42号在上海市第五批优秀历史建筑名录中登记为住宅，编号5D055。2015年12月门边可直接读到42号牌。Livelikerw于2019年2月23日拍摄的照片，可同时看到双色砖墙、中央入口、临街折面凸窗和北侧巷口。2020年2月同街实拍可辨同一组门窗与浮雕。[名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [2019年原片](https://commons.wikimedia.org/wiki/File:42_Wanping_Road.jpg) · [各机位资料](measurements/sources.json)

临街两层黄砖之上另有两层红砖。四座外挑窗湾各有中央宽面和两道斜返，每个宽面窗下并列两件浅色卷叶板，两侧斜返分别有一件。窗间是竖砌红砖。最靠南的一轴窗仍在墙面内。中央楼梯间的双列窄窗由浅色浮雕相隔，入口上方有双波形挑线、分格过梁和跨过线缆仍可辨认的花形凸框。[门楣轮廓](measurements/portal-profile.json) · [楼梯窗裙取点](measurements/central-cast-panels.json)

制作初稿用22米作为临街宽度的工作尺度。依据2019年原照的镜头信息及多段水平砖缝、竖向窗边配准。模型的进深、被树木和架线遮住的装饰以及门楣浮雕的真实凸出厚度仍有估计。原始照片的3968×2976像素画幅用于读砖缝与门窗。程序生成红砖、黄砖和竖砌砖的彩色纹理及法线纹理，均可从源参数重建。[镜头与立面基准](measurements/registered-street-camera.json) · [砖纹周期与取样](measurements/brick-finish-photo-control.json)

运行 `python -B measurements/check_mesh.py output` 可重建两档网格及逐构件闭合检查。运行 `python -B measurements/render_street.py output/full-source.glb output/renders` 可从原拍摄机位查看模型。[来源和许可](SOURCES-LICENSE.md)

街景中南北两端的外墙，在地面、白腰线和红黄砖交界三个高度量得约21.54至21.62米。成品取其中位数约21.59米。南北两端的红黄砖界线分别高出墙脚约6.19和6.24米。以墙段宽度校准水平尺度、砖界高度校准竖直尺度后，再拿八条窗轴及中央门楣复核，平面差值中位数约0.44米，高程差值中位数约0.13米。[两期街景测点与残差](measurements/front-street-intersections.json) · [制作尺度核对](measurements/model-to-street-control.json)

顶层格窗包括八组带窗芯的窗和两端的斜格。南段个别窗后来封闭，原片还能辨认玻璃和实墙之间的差别。前檐十六根外挑构件均按2019年实拍的根部与端部取点，北段另用2020年的斜向街景复核。两端高处墙面的进深从数个街景机位量得约4.76至5.41米，模型取5.10米。南侧三层小窗、偏后两处开口和灰色缓坡屋面可从独立页侧面查看。西侧较低的红瓦院屋各有边界，后墙遮挡处采用简化处理。[顶层格窗与檐椽](measurements/lattice-registration.json) · [端墙街景与四期屋顶资料](measurements/street-and-end-wall-survey.json)

红黄平砖与凸窗竖砌砖各由独立的色彩图和法线图表现。在四座窗湾的八个前转角、每角四个标高复查，修订前的纹理接缝最大错开约0.49个周期，沿折面展开后两档网格的最大差小于0.00000012个周期。八块照片留出样片中六块砖缝相关性有所改善，黄砖低段和模糊的第二窗湾仍有差异。[成品纹理与照片](measurements/fold-and-phase-photo-verification.json)

2015年和2020年街景都可辨入口的双波形挑线、花形凸框和分格过梁。先只用门窗和腰线给两期照片配准，再沿浮雕外缘比较。避开明显架线后，43个方向中有36处存在清楚的边缘峰，偏移中位数为2.25像素。浮雕凸出的厚度为估算。近景有1,109个闭合构件、71,308个三角面。远景有1,027个闭合构件、39,820个三角面。[两期门楣实拍复核](measurements/portal-two-epochs.json) · [独立首击检查](measurements/check_portal.py) · [2019年原照与模型对照](../../../data/audit/wanping-42-brick-window-bays-v1/registration/2019-frontage-comparison.jpg)

四种成品分别是原始GLB、网页近景、网页远景和可编辑Blender工程。Blender重开后含666组可编辑网格、13种材质、九台相机，以及三套不同砖面的颜色和法线图。颜色图与法线图按其各自的颜色空间读取，六张图片均打包于工程内。
