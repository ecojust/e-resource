# 亚细亚大楼 · 外滩1号

依据中山东一路、延安东路两面分期照片制作现存外观。两面各有七开间，中央三开间逐层形成深廊，地面有双柱门廊，顶部柱廊前设弯曲栏杆。东南转角后退，屋顶四隅有角亭，中央有低位采光顶。后墙窗位、屋顶构件与尺度按影像估计。[模型范围与来源](../../../source/precise/huangpu-asia-building/README.md)

## 编辑与几何

近景和原始 GLB 各 91,276 个三角面，远景 44,952 个。Blender 原生文件重新打开后有 116 个可编辑网格。按材质比较原始与解压后的实际三角面，面向、位置和材质分配一致。每档独立检查59条射线，覆盖两面退廊深处的玻璃、门扇、门廊与上层柱列、转角窗、屋顶及街道留空。[原生校验](geometry-native.json) · [Blender 渲染](huangpu-asia-building-preview.png) · [共177条射线](surface-probes.json)

## 单体查看

桌面和390像素宽手机的真实查看页均能完成近远档切换、正面和俯视操作，四次实际下载的字节和清单相符。初始东南斜视同时看见两面门廊与中央转角。桌面旧取景的对照图主要看见延安东路一面。上方视角可见四角亭与中央分格采光顶。[查看器与下载校验](viewer.json) · [新取景](viewer-desktop-initial.png) · [旧取景对照](viewer-previous-framing-comparison-initial.png) · [手机斜视](viewer-mobile-initial.png) · [屋顶](viewer-desktop-roof.png)

## 地图位置与邻栋

原始 Overture 建筑对象为 14-13720-6694 宏中的 2141。近远两档原楼投影均由替换范围完整覆盖。把北邻外滩2号上海总会的近远两个真实 GLB 展开并放回共同坐标后，两栋最近仍有至少1.865米，旧楼裁剪掩膜距上海总会也有至少1.393米。按低于两米的模型表面另算地面障碍。[场地输入](../../../source/precise/huangpu-asia-building/footprint-review.json) · [几何及距离](placement-geometry.json) · [登记契约](final-placement-contract.json)

OpenMapTiles 的同一个备用底图要素覆盖两栋建筑。使用交付的矢量裁剪模块处理真实图块后，外滩1号地面范围内的1,587.97平方米已完整剔除，外滩2号原有1,914.15平方米保留。[备用底图核验](vector-source-checks.json) · [99处发布输入](production-snapshot.json)

## 主图与交互

99处目录可用鼠标或触控打开外滩1号。840像素宽桌面自动取景的下部双柱门廊与上部退廊均可辨；收起侧栏后可同时看到两面七开间及东南转角。俯视能看见四角亭、采光顶及北侧上海总会。远景实际切换到44,952面资源。六个地面采样分别验证楼体、两处保留建筑和三处人行空间。四件下载、近远玻璃模型及近远粗楼源均有实际 HTTP 字节校验，浏览器没有记录页面和请求错误。[浏览器记录](main-map-browser.json) · [157份运行资源及4份生成输入](main-map-inputs.json) · [逐图核对](main-map-visual-review.json)

手机390×844从目录实际触控进入。初始17.947级视图有一次粗楼仍遮住下部的过渡帧；同页加载近景源组后，19.15级视图能从地面门廊一直看到采光顶。桌面一次早期加载也观察到叠显，稍后同一自动机位已完整可见。[手机自动取景](overview-settled-mobile.png) · [手机源组就绪](main-mobile.png) · [桌面自动取景](overview-settled-desktop.png) · [两机位状态记录](settled-overview.json)

运行复核脚本时，外滩2号的已有近景及远景 GLB 应分别放入一个临时目录并命名为 `web.glb`、`lod.glb`；精确路径和校验值见场地输入。Python 需 NumPy、Shapely 2；备用底图解码另需 mapbox-vector-tile。浏览器测试使用 Playwright、Chromium 和运行中的上海站点。

```bash
cd projects/shanghai
python data/audit/asia-building-v1/verify-placement.py --macro /tmp/macro-14-13720-6694 --work /tmp/asia-verify --bund02 /tmp/bund02 --out /tmp/asia-verify
python data/audit/asia-building-v1/check-surfaces.py --out /tmp/asia-surfaces.json
python data/audit/asia-building-v1/prepare-vector.py --out /tmp/asia-vector-input.json
node data/audit/asia-building-v1/check-vector.mjs /tmp/asia-vector-input.json /tmp/asia-vector-result.json
MODEL_BASE_URL=http://127.0.0.1:8784/ QA_OUTPUT_DIR=/tmp/asia-viewer node data/audit/asia-building-v1/check-viewer.cjs
MODEL_BASE_URL=http://127.0.0.1:8784/ QA_OUTPUT_DIR=/tmp/asia-map node data/audit/asia-building-v1/check-main-map.cjs
```

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 32 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/fb605b73b3f9761a81f7e4cd890efdd5c839ee15/projects/shanghai/index.html#landmark=huangpu-asia-building&mode=overview) · [固定版本逐文件核对](publication.json)

首次在 master 检查 32 项时，有 11 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
