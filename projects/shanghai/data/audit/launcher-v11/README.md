# v11启动包单点实跑记录

启动包75,160,933字节，SHA256 `f2ff0d34d3ae27df73e2e678070cd600f77f162f9a785198d8761fd1f9594156`，严格小于100,000,000字节。包含14项本地导航模型和15项远程流式模型，底图、全城资源及远程模型需要联网，资源固定到应用提交`d99e8c9f1665f65871cef730e74a86a48a3483b4`。

本次启动包仅从实际解压目录加载**包玉刚图书馆**完整模型并由root查看1张图；不等于29项导航、另一栋新楼、LOD、目录生命周期、所有区或设备帧率均已在ZIP中验证。

本版31件生产运行时文件与已发布v10阴影修复后的冻结字节相同；没有新增运行时修复。[31件运行时清单](runtime-baseline.json)。

[实际归档与解压](archive-check.json) · [解压目录浏览器报告](browser/browser.json) · [root真实图像审阅](browser/visual-review.json) · [实际截图](browser/minhang-baoyugang-library-extracted-smoke.png)。截图前后实际目标组件、保留邻楼和残余层均由绑定脚本检查；源ID下其他组件完整保留。

[应用公开字节](public-app-proof.json)与两栋[汽车博物馆](public-models/jiading-shanghai-auto-museum.json)、[图书馆](public-models/minhang-baoyugang-library.json)独立公开四资产记录分别保留，各自提交不相互冒充。应用共享11图及两份各5图范围见[应用记录](../precise-buildings-v11/two-modern-buildings/README.md)。

CDP仅阻断已知Overture主机以检查真实OSM回退；缓存与生产超时不改。该证据整理未重新运行浏览器或网络，尚不替代最终公开ZIP响应下载核验。
