# 黄家花园住宅的图像与几何复核

弧窗近照和花园全景分别用于校验。原始与网页近景在全景25个预先选点中有23束先击预期材质，远景为22束；三款在弧窗独立近照的11束均先击预期材质。主要偏差发生在窗边、窗台和石垛的交界。近照在389×585工作图上用八个窗角拟合，像素残差中位11.89。屋面另有每款23束的专项结果。[逐束原始记录](three-mesh-photo-checks.json) · [屋顶专题](roof/README.md)

原始和近景均有23,784个三角面，远景有14,940个。两次独立解码按顶点顺序、三角面方向和材质逐一比对。近景1,091个可编辑实体、远景776个实体通过开边、方向和正体积检查。[解码复核](mesh-decode-comparisons.json) · [可编辑部件](editable-solids.json)

桌面和手机分别实开九个机位、请求近远两档并实际保存三个模型。两台设备共18幅原图，下载按字节数和SHA-256核对。[桌面九视](ordinary-ui/desktop-nine-views.jpg) · [手机九视](ordinary-ui/phone-nine-views.jpg) · [浏览实录](ordinary-ui/report.json) · [逐图观察](ordinary-ui/visual-review.json)

[模型说明](../../../source/precise/changning-yuyuan-1055-huang-family-garden-residence/README.md)
