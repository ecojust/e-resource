# 岳阳路145号花园住宅南立面与折檐红瓦屋顶

穿过岳阳路的院门，草坪北侧可以看到这座红瓦住宅。2021年刊载的庭园照片从南面拍到一楼玻璃廊、通长露台和两侧成对的山墙。2023年刊载的两幅俯拍补充了中央老虎窗、上缓下陡的折檐、人字坡面交接及五组烟囱。主屋和东邻永嘉路501号圆塔住宅分别建模。[本栋三维预览](../../../yueyang-road-145-residence.html) · [2023年照片及1948年街坊图](https://www.thepaper.cn/newsDetail_forward_23188382) · [花园正面与院门](https://www.oldkids.cn/blog/view.php?bid=1596614)

《上海名建筑志》记载，主宅建于1928年，原有三开间，南面临花园。后来重做了南侧外廊、阳台和外墙开窗，东侧开间也有改动。本次依据2021年和2023年刊载的外观制作，保留了照片中可辨的绿色遮阳篷、临花园玻璃窗带、屋顶鱼鳞瓦和中央三角窗额。绿化挡住的窗扇分隔、廊深、屋脊及烟囱高度均为估算。建筑背面和侧面主要采用檐下的简化墙面，北侧服务用房、整个大花园和室内另待测绘。[来源、影像指纹与年代分歧](reference-review.json)

市房管局名录的2D024、2D028两行均写「花园住宅／老干部局／岳阳路145号」。工作名录103指永嘉路501号，104指岳阳路145号。《上海名建筑志》分述两栋。园内的机构地址点位于主宅以南，地图定位采用房屋实际轮廓、1948年街坊图和两期航片。花园北侧的源面2048东西约22.1米，东侧340为永嘉路501号，北面4888为独立建筑。2023年的花园上空照片中可在145号的右侧树后看到501号的尖塔。[地块与相对方位](footprint-review.json) · [名录异文](../../../data/audit/municipal-heritage-register-2026-11-20/README.md)

几何按照项目MIT许可发行。第三方照片、地方志及影像服务的权利归其作者或提供方。成品以原创三维网格表现窗扇、山墙、瓦行与烟囱。[模型文件清单](../../../assets/models/candidates/xuhui-yueyang-road-145-residence/manifest.json) · [专项审计](../../../data/audit/yueyang-road-145-residence-v1/README.md)

在项目的 projects/shanghai 目录运行。环境需要项目使用的Python、Shapely、NumPy、Blender、Node.js、ImageMagick、gltfpack及Open Image Denoise。

~~~bash
python source/precise/xuhui-yueyang-road-145-residence/source/build_model.py --out /tmp/yueyang-145-assets --audit /tmp/yueyang-145-native --gltfpack /path/to/gltfpack --oidn /path/to/oidnDenoise
python source/precise/xuhui-yueyang-road-145-residence/source/check_surfaces.py --manifest /tmp/yueyang-145-assets/manifest.json --out /tmp/yueyang-145-surfaces.json
~~~
