# 华山路823、825、827号院临街住宅三山墙与明梯

2018年2月10日，Antigng在华山路拍到院门后的三山墙住宅。右门柱同时可见823号和825、827号门牌。2015年与2020年的街景还能辨认中央开敞拱厅和楼梯。上海市第五批优秀历史建筑名录以5D051登记整组住宅，此模型取其中临街可辨的一栋。院内深处各栋的逐号归属待核。[照片原页](https://commons.wikimedia.org/wiki/File:华山路823号住宅.jpg) · [市级名录](https://fgj.sh.gov.cn/yxlsjz/20200414/b9946bf8508e4b9689671fcd4146bb86.html) · [位置与分栋依据](measurements/placement-identity.json)

中央拱厅下方可见混凝土栏板，先沿左侧平台平伸，再顺楼梯向右侧低平台下降。楼梯模型包含踏面与底板，遮挡处的步数采用估算。2018年原片缩至1300像素宽后，沿券口87个方向中的76处仍能辨认明暗界线，椭圆拟合误差中位数为0.64像素。[原片拱边读数](measurements/loggia-arch-control.json) · [检查成品网格的拱边](measurements/check_arch_profile.py)

两翼分别保留扇光钢窗、上层罩篷、下层遮阳篷，以及菱形和横长花孔。左端另有四个长方形通气孔。透过拱口可见楼梯的斜底板及两端平台。树枝挡住的细窗棂和最靠右的收边主要依据邻近可见边缘。按街景中南翼山墙尖到檐角白落水管的距离校正后，模型这段墙的水平跨度为2.81米。[翼面可见点与遮挡](measurements/wing-photo-readings.json) · [建模参数](source/wing_layout.json)

两翼山墙尖的模型间距约15.71米。分两批处理街景后，八视图解与十二视图解分别给出15.61米和15.15米。中央山墙至翼部墙面的前出量，对拍摄机位和树后檐角的辨识更敏感。最初八个视图把两处檐角误读成翼脊尖，算得3.81米。十二个视图校正后为2.57米，单独用2015年和2020年影像分别为3.42米和2.61米。模型采用约3.76米，处在这些估计的上端。局部高度以模型底部的水平截面为起点，街道路面与该截面之间的高差仍有不确定性。[八视图原记录](measurements/street-front-triangulation.json) · [十二视图重算](measurements/twelve-view-front-and-side-adjustment.json) · [坐标与高程对齐](measurements/model-to-street-datum.json)

在此目录运行 `python -B measurements/check_mesh.py output` 可分别重建近景和远景，输出三角网与逐构件闭合检查。运行 `python -B measurements/render_loggia.py output/full-source.glb output/render` 可从2018年的拍摄位置查看整面山墙、中央拱厅和近处梯段。[照片使用许可](SOURCES-LICENSE.md)

南侧能辨认高墙的两处上窗、落水管和两段突出窗间。模型中两段分别向外伸出约3.05米和3.77米，后段下窗台及室内被绿篱遮挡。侧檐前后跨度约11.53米，烟囱有三枚菱形孔。俯拍与两年的侧向街照可读出沿主屋脊交合的三个短坡顶，北端和屋后隐面保留简化边界。[南侧量读与不确定度](measurements/side-and-roof-observations.json)

对照右翼墙尖与瓦面时，原模型漏掉一段平檐，造成约0.52米高差。补回平檐后，两档模型均以5,138道向下的射线复核屋面覆盖，并在墙角六处量取瓦面高度。最终近景有427个闭合构件、38,708个三角面，远景有404个闭合构件、30,968个三角面。[实测屋面闭合](measurements/side-roof-seam-check.json) · [六点量测程序](measurements/check_roof_verge.py) · [2018年原照片与模型对照](../../../data/audit/huashan-823-827-stair-loggia-v1/registration/2018-frontage-comparison.jpg)

独立页有九个观察位置，包括可同时看到烟囱、瓦坡及两段凸窗的南向侧视。四种下载分别为原始GLB、网页近景、网页远景和可编辑Blender文件。Blender重新打开后含182组可编辑网格、17种材质和九台相机。近景有10,248个纹理面角，保存重开后与作者网格的UV坐标最大偏差约为0.00000024。
