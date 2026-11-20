# 当前建筑立面与地图灯牌

从入口选择汉弥登大楼，900 × 650 的桌面上可见七块全名牌。旧布局盖住该栋投影轮廓的 13,000 个像素。用相同的浏览器相机和同一份网页近景模型重测，轮廓共有 17,800 个像素，新布局的牌面覆盖 0 个。街角收分的两面墙、中央塔冠和门前路面可同时看见。[改前实拍](../hamilton-house-v1/main-desktop.png) · [改后实拍](desktop.png) · [逐面投影测量](mesh-and-labels.json)

七个地点保留各自的全名和点击区。逐牌检查中心、边与四角共 63 点。实际用鼠标点中移位的金城银行灯牌，再通过可见搜索结果返回汉弥登大楼，点击地图放大并复位。390 × 844 的触屏保留原有的一块汉弥登灯牌，矩形相对旧位置误差小于半像素，九点全部命中，实际轻触后路由仍指向该栋。两端视图及点击操作的记录对应各自截图的 SHA-256。[改前手机图](../hamilton-house-v1/main-mobile.png) · [改后手机图](mobile.png) · [浏览器记录](result.json) · [桌面灯牌实际像素位置](desktop-painted-labels.json)

## 复算

在 `projects/shanghai` 下运行下列命令。Python 需要 Pillow 和 NumPy。加入 `--verify-mesh` 时调用 Node 和仓库自带的 meshopt 解码器，从正式 GLB 重建点、面索引。

```sh
python data/audit/selected-facade-labels-v1/recompute-coverage.py --verify-mesh
node --test tests/building-beacons.test.mjs tests/building-beacon-groups.test.mjs
```

网页近景是 39,472 个三角面、19,984 个去重顶点。浏览器用两个视口各自的真实相机投影同一组顶点，逐三角绘制每 CSS 像素一格的轮廓掩膜，再与屏幕上真实灯牌矩形的并集求交。另有楼栋处在摄像机与目标建筑之间时，建筑遮挡以截图为准。归档中的投影和面索引采用 gzip 无损压缩。复算会核对其解压后 SHA、前后截图 SHA、实际模型 SHA、39,472 行索引，以及两次视口、相机和逐点点击记录。外部工作目录可用 `--project /path/to/projects/shanghai` 指定项目根。[原模型四件](../../../assets/models/candidates/huangpu-hamilton-house/manifest.json) · [源网格与输入签名](source-bindings.json) · [归档文件签名](evidence-manifest.json)

## 加入更多模型后的同一相机

另以首次采用新布局的 139 处目录、后续 164 处目录回放汉弥登相机。两个目录都通过真实 HTTP 取得并与冻结 SHA 对齐。139 处时桌面保留七块全名，原排布遮住 13,000 个轮廓像素，新排布为零。164 处时桌面出现八块全名，原排布为 13,717 个像素，新排布仍为零。390 像素手机上分别显示一块、两块全名，改前改后覆盖量分别保持在 330 和 3,950 个像素。以上两个较晚目录使用实际 MapLibre 投影变换进行离线排布，实际浏览器操作取自上面的 135 处实验。[两代目录与可点击牌数](catalog-density-replay.json) · [逐牌原始位置](projection/later-layouts.json.gz)

## 首次发布的文件

同一栋、同一模型、同一城市目录的实验使用 135 个地点。发布时只变更两个运行模块，并加入一份 135 处输入夹具和一处用例。每栋独有的 HTML 和 app 版本继续引用对应的 scene；scene 使用 `beacon-facade-clearance-v1` 引入新灯牌模块，分组模块沿用已有版本。39 条灯牌与分组回归全部通过。[实验站签名](experimental-site.json) · [四个发布文件](first-release-changes.json) · [实际首发版本导入路径](first-release-http-chain.json) · [回归输出](39-regression-tests.log) · [灯牌回归用例](../../../tests/building-beacons.test.mjs) · [汉弥登回归数据](../../../tests/fixtures/beacon-hamilton-focus.json)

`original/` 中保留本次原始浏览器、源网格绑定、站点绑定和覆盖测量脚本的字节与 SHA，所用原始工作路径载于脚本。上述便携复算直接使用相对项目路径。
