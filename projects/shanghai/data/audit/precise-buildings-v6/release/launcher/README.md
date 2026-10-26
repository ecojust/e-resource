# v6启动包与固定应用核验

应用固定提交：`ac388a7c598b81af3b6ac9fc79d4b63ee59a3ad4`。启动包为74,988,136字节（74.99 MB），SHA256 `20f028539f16406dbc8353cdb3d5558395c57095a53fd7db79792744ccadcde4`。[归档检查](archive-check.json)通过267个ZIP流CRC、266项清单SHA、路径安全与实际解压文件复核；原14栋核心模型在包内，新增三栋及其远景／照片从固定提交联网加载。每个文件均小于100,000,000字节。

[公开资产核验](public-assets.json)完整下载并逐字节核对7个固定提交文件，含三栋近景模型、样式、替换清单及两份运行代码。[预览响应](preview-response.json)记录固定CDN页面HTTP200并与HTML源字节一致；默认Python User-Agent曾被bot filter返回403，浏览器式请求成功，原证据保留。归档检查本身不声称下载验证远端内容，两类证据分开记录。

[实际解压包浏览器报告](browser.json)于2026-10-26 07:52:37–08:00:29 UTC运行，1040×760／DPR1，目标仅bund05，reset-only。05号近景加载、精确归属释放／重放、选定邻楼和城市清单reset通过，共2组采集；没有重复完整三栋远近LOD导航循环。此前三栋15组技术记录与10张视觉图仍见[上级审计](../README.md)，该轮发生在网络／样式补丁前。

[主审视觉记录](visual-review.json)逐张实际查看本轮[重置前](before-city-manifest-reset.png)与[重置后](after-city-manifest-reset.png)截图，确认立面、人物与楼前铺装仍可见。原browser报告中的visual pending保留技术采集时原值，后续视觉结论由独立记录提供；两者和PNG均按原字节保存并绑定SHA。

补丁后本轮没有number/null样式warning，仍有4条ReadPixels GPU stall warning与3条预期请求取消；没有将这些日志删去或声称warning归零。未做强制故障注入、低内存设备或用户硬件性能测试。此处只接受已声明的启动／reset冒烟范围，不声称上海全城达到逐栋照片精度。
