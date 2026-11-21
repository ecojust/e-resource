# 皇家公寓街面核验

三段街面沿两条道路收拢至1326号门。近景有139,692面，远景有93,616面。每个网格实测134条射线，检查五道横窗、两翼各两列圆窗、退进双门、两根圆柱、居中的三道竖肋与高一层的转角窗。Blender文件已重新打开并按材质核对有向三角面。[独立几何实测](surface-checks.json) · [原生工程复核](geometry-native.json)

底图5455仅替换临街折带。原主体近景保留76.74%，远景保留77.04%。室内庭院的5277近、远景距切面分别21.42米和21.51米。19个地面点覆盖双门前、柱脚、两街人行区域和商铺墙后，另测桌面、手机各七处构件视线。[落位](placement-geometry.json) · [默认视线](overview-sightlines.json) · [合同](final-placement-contract.json)

[模型与来源](../../../source/precise/xuhui-empire-mansions-street-front/README.md) · [单体预览](../../../empire-mansions.html) · [四份资产](../../../assets/models/candidates/xuhui-empire-mansions-street-front/manifest.json)

[桌面、手机及四次文件下载](viewer.json)

城市目录由248处增至249处。最终站的单体页、渲染模块、模型清单和四份资产已与实测单体页逐字节比对。三角面裁剪使用21张分区表，全城1,562个裁片，单表最多334片。源5455由六个三角形剔除临街旧立面，原有院落继续使用城市底图。[城市运行核验](runtime-placement.json) · [正式站与单体截图绑定](formal-viewer-http.json) · [最终目录登记](25k-compatibility.json)

三个服务版本分别完整读取并验证1,495、1,497和1,499个HTTP文件。最终服务共传输1,282,580,478字节。[三版完整读取记录](full-served-inputs.json)
