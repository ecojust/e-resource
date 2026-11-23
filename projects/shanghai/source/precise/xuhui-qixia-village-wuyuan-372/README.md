# 栖霞村北排院向立面

上海市房屋管理局登记的5D071栖霞村位于徐汇区五原路372弄6–9号。历史街坊图将此排与1–5号金波邨分开。院面朝东南，从院中看，9号在左、6号在右。2016年1月20日连续四张照片拍到6号的土红披檐和白窗、7号绿色封廊、两者以西的成组钢窗以及9号敞开阳台。6、7、9有具名照片，中间一张没有可读的单户号码。

模型包括这四站可见的院向墙面、挑板、铁栏、钢窗、雨篷和院门。连续立面依据16处共见点、垂直和水平线配准。照片为650×487像素的网页版本，其中嵌入的原始图像尺寸记为500×375。逐处配准误差见 measurements/court-cameras.json。2010至2025年的四期影像为屋面走向和范围提供依据。不同图中可辨屋檐跨度约39–48米。院墙进深、遮挡处的栏杆间隔和楼层尺度具有估计误差，后排深处和室内尚缺资料。

图中左右近邻的归属可在 measurements/qixia-6-9-placement-and-sources.json 和 measurements/named-court-overlaps.json 核对。摄影站17、18、19、20分别对应游记中的照片42504417–42504420。模型单位为米，X沿这排住宅向东北、Y向西北进深、Z向上。

复算相机和重建模型的命令如下。

    python measurements/fit_court.py --output measurements/court-cameras.json
    python source/build_model.py --output full.glb
    python source/build_model.py --lod --output lod.glb
