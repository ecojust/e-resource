# 上海漫游启动包 · v13

[下载 shanghai-web-launcher.zip](shanghai-web-launcher.zip) · 75,198,283 字节，严格低于 100,000,000 字节。

SHA256：`409cf1070eb6625c9d2d5cb6c4929739bc2e0b925916de42a5463378274c8976`

完整解压，进入 `shanghai` 目录运行 `python -m http.server 8000`（macOS/Linux 可用 `python3`），然后访问 <http://localhost:8000/#landmark=yangpu-library&mode=walk>。请通过 HTTP 启动，不能直接双击 `index.html`。

本版导航 31 项，包含 14 项本地模型、17 项联网模型；新增杨浦区图书馆整馆。网页及联网资源固定到提交 `387561d8a7297eb7fc2a42907f0819fa1d61e958`。需要联网获取地图、城市分块和新增建筑；原始 GLB 与 Blender 文件在[项目模型目录](../source/precise/yangpu-library/CURRENT_STATE.md)，未打入启动包。

WASD/方向键行走，Shift 加速，拖动转向，滚轮调镜头；手机使用摇杆。若完整模型读取超时，请刷新页面重新加载，目前没有自动重试。

实际检查：307 件归档成员完整 CRC/SHA 校验通过；31 件运行时与 MAIN、V13 冻结基线一致。从实际 ZIP 按请求解压的目录启动，加载固定提交上的杨浦图书馆完整模型，核对 1 张截图；同时检查目录采用、源建筑替换及同块邻居。不据此声称包内所有地标、LOD、全城或硬件帧率已经重新验证。详见[归档与启动记录](../data/audit/launcher-v13/README.md)。

未进行现场测绘或摄影测量。西侧、北侧和内院部分窗跨、局部尺寸及饰纹按有限资料推估；屋脊总高不等同于审批图中的 18.49m 檐口高度。 全市底图仍含大量基于公开轮廓和高度推定的建筑。本包不是离线地图或测绘成果。
