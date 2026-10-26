# v6.1 三栋HTML接入与目录验证

本目录报告对应外滩07／09与青浦222的当前应用接入，项目计数20＝15外滩＋4陆家嘴＋222；129另有独立下载资产，尚未加入HTML或通过网页场景验收，不计入20栋。本轮只验证报告中的建筑、位置、时刻和模式，不把全市179万要素称为同等照片复原。

- [三栋实际浏览器报告](../qingpu-beidajie-222/registration/browser/browser.json)：15组采集、6份实际资产核对；4条warning、3条预期取消、0条外部HTTP错误，page／shader／required-asset错误为0。
- [root最终视觉记录](../qingpu-beidajie-222/registration/browser/visual-review.json)：实际查看10张图，绑定浏览器报告及三栋web／LOD SHA；222远景仅能判断存在与场景延续，不能独立评判其立面细部。
- [独立目录实际浏览器报告](catalog/browser.json)：静态复用、受控动态加入、失败回退三个阶段。
- [root目录视觉与运行时回归说明](catalog/visual-review.json)：实际查看5张目录截图，绑定同一浏览器报告，包含动态返回场景；技术阶段通过不单独证明没有重复方盒。

运行时改动与回归范围（root记录）：三栋静态采集（07、09、222的15组记录／10张实际核图）发生于遮罩缓存修复之前。之后只修改了src/city-feature-mask.js的渲染缓存与uniform生命周期，package.json增加7项回归入口；16项候选源码在本轮实际浏览器运行前后逐SHA一致。模型几何、纹理、导航与accepted目录未改。本轮补验静态222复用、纯目录加载／卸载／返回及错误索引回退，并实际核对5张截图，未重新采集全部07／09近景LOD循环，不声称全城或硬件性能验收。

[16文件集成清单](validation/integration-files.json)与[运行前快照](catalog/runtime-snapshot-before.json)、[运行后快照](catalog/runtime-snapshot-after.json)按SHA绑定同一轮实际输入。

主体三栋浏览器报告采用静态候选导航；它本身没有运行按需目录流程。单独目录报告区分实际static20复用和Playwright仅在响应中移除静态222后的dynamic-only19→20加入，以及目录索引篡改后的拒绝路径。这些受控响应只用于测试，不是生产数据修改。不要将测试移除静态项写成正式应用只有19栋。

static_adoption实际读取20项导航，重复目录设置复用已加载对象，不发重复模型请求，卸载保留静态记录。dynamic_only仅在Playwright响应中去掉静态222及其顶层替换，读取19项，再由目录加载唯一222；离开清理动态记录、释放GPU几何并恢复owner，返回创建新对象，27邻要素保留。dynamic_hash_failure使用等长单字节破坏索引，明确SHA拒绝、零精细模型请求，完整28要素普通near继续可见。

技术报告与root实际图像审阅分别保存。root只对`actually_viewed`列出的图片作视觉判断，其他采集仅具技术记录；保留真实warning/取消/外部服务失败明细。通过范围限于载入、照片/LOD、唯一owner、邻楼保留和退出/返回/重置，以及目录报告明确测试的生命周期；不保证设备帧率、现场光学材质、未知背面或实测尺寸。

[首批v6历史审计](../release/README.md)与[v5历史审计](../../city-detail-v5/release/README.md)继续保留，不能代替本批。单体native历史见各自封装/DELIVERY。[本轮模型来源与限制](../../../bund/REALISM_V6_1.md)。

[上一版17栋在线预览](https://rawcdn.githack.com/ecojust/e-resource/ac388a7c598b81af3b6ac9fc79d4b63ee59a3ad4/projects/shanghai/index.html#mode=walk)（固定ac388…应用，尚不是本轮20栋页面）。[上一版v6启动包](../../../../downloads/shanghai-web-launcher.zip)为74.99 MB／74,988,136字节、按需联网；它在本地包含原14栋并联网加载首批3栋。**本轮20栋新预览与ZIP尚待发布，旧链接不能当作新增三栋已上线的证据。**
