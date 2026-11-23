# 宛平路42号住宅双色砖墙与卷叶凸窗

宛平路42号在上海市第五批优秀历史建筑名录中登记为住宅，编号5D055。2015年12月门边可直接读到42号牌。Livelikerw于2019年2月23日拍摄的照片，可同时看到双色砖墙、中央入口、临街折面凸窗和北侧巷口。2020年2月同街实拍可辨同一组门窗与浮雕。[名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [2019年原片](https://commons.wikimedia.org/wiki/File:42_Wanping_Road.jpg) · [各机位资料](measurements/sources.json)

临街两层黄砖之上另有两层红砖。四座外挑窗湾各有中央宽面和两道斜返，每个宽面窗下并列两件浅色卷叶板，两侧斜返分别有一件。窗间是竖砌红砖。最靠南的一轴窗仍在墙面内。中央楼梯间的双列窄窗由浅色浮雕相隔，入口上方有双波形挑线、分格过梁和跨过线缆仍可辨认的花形凸框。[门楣轮廓](measurements/portal-profile.json) · [楼梯窗裙取点](measurements/central-cast-panels.json)

制作初稿用22米作为临街宽度的工作尺度。依据2019年原照的镜头信息及多段水平砖缝、竖向窗边配准。模型的进深、被树木和架线遮住的装饰以及门楣浮雕的真实凸出厚度仍有估计。原始照片的3968×2976像素画幅用于读砖缝与门窗。程序生成红砖、黄砖和竖砌砖的彩色纹理及法线纹理，均可从源参数重建。[镜头与立面基准](measurements/registered-street-camera.json) · [砖纹周期与取样](measurements/brick-finish-photo-control.json)

运行 `python -B measurements/check_mesh.py output` 可重建两档封闭构件及其GLB。运行 `python -B measurements/render_street.py output/full-source.glb output/renders` 可查看原拍摄机位下的模型。街面以外的体量及上层格窗另行核实。[来源和许可](SOURCES-LICENSE.md)
