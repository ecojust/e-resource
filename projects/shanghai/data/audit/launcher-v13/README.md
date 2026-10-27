# V13 启动包实际验证

应用提交 `387561d8a7297eb7fc2a42907f0819fa1d61e958`；ZIP 75,198,283 字节，SHA256 `409cf1070eb6625c9d2d5cb6c4929739bc2e0b925916de42a5463378274c8976`。

- [archive-check.json](archive-check.json)：实际读取 307 件成员，检查 CRC、清单 SHA、路径、固定提交链接和 31/14/17 导航数量。未进行联网下载或浏览器验证。
- [runtime-target-check.json](runtime-target-check.json)：实际 ZIP 的 31 件运行时与 MAIN、冻结基线逐字节一致；杨浦图书馆四件本地资产与归档指向一致。
- [extraction.json](extraction.json)：只从该 ZIP 按浏览器请求实际解压 77 件文件、45,163,203 字节，逐件 SHA 验证；无 MAIN 回退。没有声称全部成员落盘。
- [smoke/browser.json](smoke/browser.json)：固定提交上的新目标完整模型实际加载，单次 full 视图、静态目录采用、源/near/far owner、邻居、实际资产与运行时核验。没有重新执行 LOD/W 或动态目录生命周期。
- [smoke/root-visual-review.json](smoke/root-visual-review.json)：root 实际看过[本次截图](smoke/east-entry-walk.png)，绑定浏览器报告和图像 SHA。

从实际 ZIP 按请求解压的目录启动，加载固定提交上的杨浦图书馆完整模型，核对 1 张截图；同时检查目录采用、源建筑替换及同块邻居。 此处只记录一个新目标的启动冒烟，软件渲染不代表硬件 FPS。未进行现场测绘或摄影测量。西侧、北侧和内院部分窗跨、局部尺寸及饰纹按有限资料推估；屋脊总高不等同于审批图中的 18.49m 檐口高度。 需要联网；读取超时仍需刷新。
