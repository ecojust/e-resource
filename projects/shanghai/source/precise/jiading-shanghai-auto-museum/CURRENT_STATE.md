# 上海汽车博物馆当前交付状态

已接入v11应用`d99e8c9f1665f65871cef730e74a86a48a3483b4`。[直接漫游](https://rawcdn.githack.com/ecojust/e-resource/d99e8c9f1665f65871cef730e74a86a48a3483b4/projects/shanghai/index.html#landmark=jiading-shanghai-auto-museum&mode=walk) · [项目当前状态](../../../CURRENT_STATE.md) · [实际模型与网页范围](../../../data/audit/precise-buildings-v11/two-modern-buildings/README.md)。

以2016年许可照片为主要外观依据，重建五层体量、连续银色曲面外壳、黄橙色折转饰带、分层玻璃幕墙、北侧五条沿外壳转弯的玻璃槽、独立百叶、入口和外部楼梯。整体尺度采用上海市绿化部门历史资料中的32.45米名义建筑高度。

[网页GLB](../../../assets/models/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum-web.glb)（10,347,300字节） · [原始GLB](../../../assets/models/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum-raw.glb)（31,951,432字节） · [远景LOD](../../../assets/models/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum-lod.glb)（10,347,300字节） · [Blender](../../../assets/native/precise/14-13706-6691/jiading-shanghai-auto-museum/jiading-shanghai-auto-museum.blend)（14,653,789字节）。每件严格小于100,000,000字节。

32.45米的历史资料没有说明测量基准，模型整体与局部尺寸不等于竣工实测。同济2006年采访和TJAD项目分别记载15米、17米最大结构悬挑，口径差异保留，未据此推断每处可见退距。曲率、层高、退台、板缝、隐藏屋面及内部支承均有估计。Web和LOD是相同压缩几何，各528396个三角形，没有减面收益承诺；标牌使用通用字体轮廓。有限接合与槽内射线检查不证明完整隐藏内景、结构安全或所有人物与相机运动无碰撞。

[原始来源、构造与许可](README.md) · [构建方法](CURRENT-BUILD.md) · [本版来源与限制](../../../data/bund/REALISM_V11.md)。原冻结文件与失败/修正历史保持，当前网页接入状态由本页和实际证据说明。

本版31件生产运行时文件与已发布v10阴影修复后的冻结字节相同；没有新增运行时修复。

启动包75,160,933字节，SHA256 `f2ff0d34d3ae27df73e2e678070cd600f77f162f9a785198d8761fd1f9594156`，严格小于100,000,000字节。包含14项本地导航模型和15项远程流式模型，底图、全城资源及远程模型需要联网，资源固定到应用提交`d99e8c9f1665f65871cef730e74a86a48a3483b4`。

本次启动包仅从实际解压目录加载**包玉刚图书馆**完整模型并由root查看1张图；不等于29项导航、另一栋新楼、LOD、目录生命周期、所有区或设备帧率均已在ZIP中验证。[启动包真实范围](../../../data/audit/launcher-v11/README.md) · [下载](https://github.com/ecojust/e-resource/raw/refs/heads/master/projects/shanghai/downloads/shanghai-web-launcher.zip)。
