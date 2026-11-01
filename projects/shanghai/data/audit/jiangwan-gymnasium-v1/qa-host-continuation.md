# 单宿主网页验收的续段与取景修正

本轮只启动一个Node／Playwright宿主和一个Chrome，辅助页、目录和主图按顺序使用同一页面。没有重新开浏览器重跑来掩盖失败。

首次主图默认视角在截图前触发QA断言：把全目录202行错误地要求为当前视口活跃行。实际主图按附近模型惰性加载，当时主场45行加体育馆10行，共55行；生产纹理容量为224行。这个错误属于QA断言口径，生产模型与脚本均未修改。失败栈保留在browser.json的failures中。

原宿主通过SHA绑定的qa-resume-active-clips.cjs续段继续。续段使用当前页面已装载的THREE三角化工具，单纯计算最终目录几何的202行，不加载旧模型资产，也不创建第二个WebGL上下文。每份实际资产状态再按其活跃clip IDs累加核对真实shader.triangles；224行纹理与near源由实际主图渲染验证；颜色／深度／距离钩子的构造覆盖由另列运行时检查记录，不把未使用的距离通道冒称实际绘制。202是全目录总数，不声称截图视口同时加载全部202行。

首张入口近景被保留的前方独立建筑遮住，仅作为不充分过程图保留。相机从zoom20.2调整到21.8，保持门口目标、65度俯仰和90度朝向，进入门前空地；没有隐藏邻楼。调整后的三拱凹进、两侧格门孔、中央有界暗止挡、浅门槛和挑台孔清楚可见。

默认小比例图可见细屋缝／石缝的像素取样纹及西立面背光表现。侧、门、屋面近图分开核对几何。细部路径实际调用setVisualQuality({shadows:false})并等待渲染，但原capture state未采样getRealismState().lighting.enabled，所以不把调用描述为独立读到阴影状态，更不将其冒称默认阴影质量完全通过。当前近图和源／几何证据支持没有粗模平顶或前立面叠盖。

最终宿主关闭、控制归档、截图实看和输入散列以qa-host-completion.json、qa-visual-review.json及browser.json为准。根代理对所有截图的实际复核另列。

本轮私有HTTP服务最初在读取基线相邻宏 `14-13723-6690/online-ids.json.gz` 的promisor对象时，遇到已失效GitHub凭据，并错误返回404；目录中的该文件并未缺失。服务改用不可变基线版本的公开HTTP回退，下载后按基线git tree的blob SHA1（含Git blob头）核实，再缓存与提供。原404、浏览器console错误和分块保留在线建筑警告完整留在报告，不能称首次运行零错误。

此前另有一次Playwright响应体读取协议失败；旧监听器没有记录其URL，因此不把它推定为上述404。第二个SHA绑定续段 `qa-resume-environment.cjs` 在原宿主和原页面中，对该监听器覆盖宏全部已服务路径（包括预检请求的保守超集）逐个重新fetch、读ArrayBuffer并计算SHA256；再重回原LOD场景，使此前失败的相邻宏通过实际streamer重新加载并显示。初始错误不删除，后续出现任何新增同类或应用错误均不能通过。恢复输入、请求集合、逐资源实际重试及实际场景分别绑定到 `env-recovery-input.json`、`env-recovery-served-source-trace.json` 和 `env-recovery.json`。这支持恢复后的完整验收，并不声称找回了未知失败响应的URL。

恢复后的LOD→手机转换时，相同旧监听器又出现一次未知URL的响应体协议取读失败。严格门禁保留了第二次失败并再次停止。第三个SHA绑定续段 `qa-resume-observer.cjs` 仅从当前手机阶段继续：将城市响应监听改为带URL的状态与响应头记录，不再把易失的CDP响应体接口作为唯一证据；在稳定的原页面中同步重新fetch所有已观察源文件并核对实际字节，同时保留页面、console及HTTP错误监听。两次未知URL观察器失败仍作为有限QA证据缺口保留，不推定其原因、不改称应用错误、不声称找回未知响应。此前已经得到的12项字节校验、相邻宏实际visible与LOD/近景接受保持可追溯。最终恢复输入由 `env-recovery-final-input.json` 绑定。

恢复输入沿用的 `bodyObserverLimitation` 中“one”是首次响应观察器失败的历史描述；最终以 `original.responseCheckFailures` 实际保留的两条记录和 `observer_policy` 的“both”为准。两条都属于未能追溯具体URL的历史观察器证据缺口。
