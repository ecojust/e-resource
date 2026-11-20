# 衡山路10号美童公学主教学楼

1922年主教学楼朝向东南草坪，立面有两层，阁楼的五扇中央老虎窗各有尖山花和半圆拱窗。2017年原片可辨正门石门楣、浅色钟亭的拱窗窗格与角饰，以及东侧一件有四柱和小锥顶的屋面构筑。其原用途尚缺记载。后窗排列、钟亭标高和侧翼细部按照片比例估计。[原始资料](../../../source/precise/xuhui-shanghai-american-school-main/reference-review.json) · [可编辑几何](../../../source/precise/xuhui-shanghai-american-school-main/source/american_school_geometry.py)

航片与街面实照把教学长翼定位在原始L形粗楼东侧。东翼的地块投影约1444平方米，北向延伸段约867平方米。原始底图17.9米高度取自10米格网估算。屋顶和窗门依实照建模，真实单元组中的另外六栋使用各自原有的网格。164处登记前目录中，最近的既有地标与该地块相距580米。[原始地块分界](footprint-partition.json) · [既有覆盖核对](existing-map-coverage-164.json) · [建筑和底图来源](../../../source/precise/xuhui-shanghai-american-school-main/footprint-review.json)

使用项目根目录下的 `source/precise/xuhui-shanghai-american-school-main/source/build_model.py` 可以重建三个GLB、可编辑Blender工程与默认预览。脚本接受 `--out`、`--audit`、`--blender`、`--gltfpack` 和 `--oidn`。地块分界与保留建筑另由实际发布网格核对。[重建脚本](../../../source/precise/xuhui-shanghai-american-school-main/source/build_model.py) · [落位与近远几何验证](verify-placement.py)

最终完整模型有32,755个三角面，远景19,147面，Blender源中有91个可编辑网格。原始、网页和远景分别完成67项射线检查，包括中央七个上层窗洞、五扇拱形阁窗、钟亭窗格、屋坡与塔座的连续接合。两张完整矢量瓦片分别含2426和3535个合并组成面；同处跨瓦片范围分别计算。原生北翼近景保留878.38平方米，远景保留866.85平方米，近远接缝偏差约7厘米。[三档射线](surface-probes.json) · [可编辑网格核对](geometry-native.json) · [原生预览](xuhui-shanghai-american-school-main-preview.png) · [相机与取景](native-camera.json) · [原生落位](placement-geometry.json) · [矢量去重](vector-source-checks.json)

在164处与165处正式页面中，项目目录分别止于科学会堂和衡山路校舍。新版独立页、资源清单及四种下载从同一公开路由实取，共核对十份输入。[前后两个入口及资源字节](public-entry-bytes.json)

桌面独立页面完整显示衡山路主楼，两翼、正门、五扇中央阁窗和钟亭都在画面内。本次查看器复查完成一幅近景后释放显存，其余视角另行复查。[首幅网页近景](first-desktop-viewer.png) · [首轮操作记录](first-desktop-viewer.json)

登记后的单体页面已在1250×820和390×844实测，两个视口均成功切换完整近景和简化远景，桌面实际下载的原始、网页、远景及Blender四件逐项通过文件名、大小与SHA-256核对。[桌面近景](viewer-desktop-full.png) · [手机近景](viewer-mobile-full.png) · [浏览器与下载数据](viewer.json)

### 城市地图实测

在164处的原场景和165处的登记后场景拍摄同一个校园。手机从徐汇区目录点入，桌面重载同一链接。登记后能看清正门、五扇中央阁窗、钟亭和边上的小顶。两幅默认图和正面近景中，前景原有建筑遮住左翼低层的一部分。[登记前](map-before.png) · [手机默认](map-mobile.png) · [桌面默认](map-desktop.png) · [临街正面](map-street-facade.png) · [屋顶](map-roof.png) · [城区远景](map-distant.png)

两个近机位都载入了实地七栋建筑的原生组。仅3093号原楼的东翼被替换，北翼接缝有两段封口。12项实际地面检查包括主楼教室、保留北翼、另外六栋原楼、东南草坪和北翼旁院道。拉远至15.5级后，场景切换并验明远景GLB。两版浏览器均正常退出，作对照的旧场景保留了一条未带详情的地图控制台警告。[逐图观察和限制](main-map-visual-review.json) · [旧场景数据](control-browser.json) · [新场景数据与四件下载](main-browser.json) · [两版文件签名和HTTP读取](map-release-bindings.json)
