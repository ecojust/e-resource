# v9启动包：龙华塔单点运行记录

应用提交：`72f845db12482c0c7a3c1fccca3f2dd4fb4b8336`。启动包为75,099,231字节，SHA256 `5200a5e0dca61b709e766b9724f9c89d1757f4763654027a94642ffd88a8bcc0`，严格小于100 MB。全城、底图和流式模型需要联网，资源固定到这一提交；启动包不是全城离线包。

[归档检查](archive-check.json)验证实际ZIP的CRC、文件字节与解压结果。[公开应用资源记录](public-app-proof.json)验证同一提交及最终应用计划的实际HTTP响应字节；这项记录不等于公开ZIP下载校验。

[解压后运行报告](browser/browser.json)只做一次龙华塔完整模型加载及一张截图：实际导航25项、逐栋建筑6栋、目录4个宏块；实际完整GLB为19.74 MB，SHA256 `f1d6bb04a85cb0c9f63a45d7ad9a49a002553ed3e50fc4a764f1a25d557fa3ef`。13个源邻楼保持，截图前后OSM事务均已完成，原目标组件已隐藏且未残留在替代层。定向阻断已知Overture服务用于观察真实OSM回退，没有修改生产加载超时或浏览器缓存策略。

[Root视觉记录](browser/visual-review.json)绑定同一ZIP、应用提交及报告，实际查看[这一张截图](browser/longhua-extracted-smoke.png)。截图只说明记录的机位；模型的估计尺寸、未见背面及内部等限制见[模型与应用验收](../precise-buildings-v9/longhua/README.md)。

ZIP此次没有重复应用的目录生命周期或远景LOD切换测试，也未重测全部25项导航、16区建筑或用户设备帧率。应用本身的7张静态图和5张新宏目录图验收另见上述应用记录。

[模型包绑定](package-record.json) · [实际单点检查脚本](tools/launcher-smoke.py) · [实际OSM参考组件](tools/longhua-osm-target-evidence.json)。其余4个复用QA源文件同目录保留真实字节。此证据整理器只校验已有报告并生成安装清单，没有再次运行浏览器或网络。
