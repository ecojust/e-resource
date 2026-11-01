# 江湾游泳馆实际网页验收

唯一Chrome／Node host完成桌面和手机辅助页、实际主图全景、侧面／北主门／屋顶、full/LOD、72项真实碰撞、80灯牌独立拾取与原生CDP触屏体育馆→游泳馆。触屏后hash、标题、位置改变，目标资产实际loaded visible。10张截图均已由pool_qa实际打开，Root另有独立查看记录。

最初屋顶相机pitch20使固定屋顶检查点落在自己的常驻灯牌内，QA visibility门禁在capture前停下；不是模型或网络加载失败，没有生成不充分截图。保留初始failures，通过SHA绑定qa-resume-roof.cjs在同一host将相机pitch调55，原probe、灯牌、模型和生产输入不改；该probe随后无UI/灯牌遮挡，实际屋顶图通过。只这一条continuation，无失败续段。

HTTP监听只记录URL/status/headers；在稳定页面同步fetch已请求的关键文档、代码和城市资源完整字节，算SHA256，城市资源另算Git blob SHA1与225af1b冻结树比较。不再使用会因导航失效的Playwright异步response.body观察器，不把重取字节冒称原响应体。初始与最终HTTP、console及warning错误均零，同步字节验证无失败；异步body观察器已移除。

地图原5-owner近组只裁泳馆1666的16行，另外4邻体保留；全目录218行和当前实际clip集合分别核对，GPU容量224。既有体育馆与主场保持独立。南端两侧局部在全景中被独立粗邻体挡住，未通过隐藏邻体改善画面；北主门与西侧有单独近景证据。

北入口图中央窗下、拱右上少量细竖虚线如实保留。独立平面检查未发现对应缺面或共面重叠，但确切像素原因尚未证明，不能当石缝装饰或宣称无痕。每张细部状态实际采样lighting.enabled=false，入口activeCasterModels=0；没有另做receiveShadow-only试验，不据此宣称已证明阴影因果。尺寸、隐面、后止挡仍为估计，室内通行不在验收范围。

80灯牌在320×568及缩短至320×548的真实视口均可独立拾取，文字12px。后者用于保守模拟实际CSS测得的最长标题净区，画面当前卡片仍为体育馆；没有声称截图实际显示最长标题。原生touch后游泳馆长标题的净区和目标visible另实测。

Node正常exit0，Chrome已关闭，私server由其所属PID受控SIGTERM终止（exit143）；8782／9223无监听。活动control已先按SHA归档，再移除活动名称，原失败记录和续段代码保留。详见browser.json、qa-visual-review.json、qa-host-completion.json。
