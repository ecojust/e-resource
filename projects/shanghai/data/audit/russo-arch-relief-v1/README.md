# 华俄道胜银行南樘拱窗浮雕复核

同一原生场景、照明、相机和取景下，原窗肩有斜线、圆卷与平券石，修订后可以看到两侧人物头部、背翼、屈腿、叠叶和拱顶兽面。近图的卷叶与原卷线相接，兽口与下巴间留空。石雕进深、面部表情与叶片弧面均按单幅近照估计。两幅照片的三窗匹配结果以南樘为最高，两幅相邻拱窗仍可见类似装饰。[三窗照片比对](arch-three-window-comparison.json) · [资料与源码](../../../source/precise/bund15/revisions/river-arch-relief/README.md)

| 机位 | 原件 | 修订 |
| --- | --- | --- |
| 南樘拱窗 | [原窗全图](before-whole-arch.png) | [新版全图](after-whole-arch.png) |
| 翼、叶与券石 | [原窗近景](before-wing-and-keystone.png) | [新版近景](after-wing-and-keystone.png) |

两档完整模型各新增36,636个三角面，合计129,484。远景新增9,716面，合计54,442。逐档检查保留原二进制数据、网格、节点、坐标和材质次序及外包框。每档17处人物、叶饰与兽首探针均命中新外表面，十个保留点逐一命中与旧版相同的位置与材质，覆盖全部三樘的玻璃、窗框与两樘原有券石、拱肩。每档新增三角面和保守计算的拱形开口重叠面积为0平方米。[逐面与可见面比对](geometry-comparison.json) · [项目LOD验证器实测](project-lod-verifier.json)

Blender重新打开原生工程后，原网格的位置、面和顶点次序、各面材质及UV均通过核对。五个新增物件可分别编辑。四幅Cycles渲染均采用相同8样本CPU参数，使用Open Image Denoise的CPU LDR sRGB模式去噪，原始渲染及对应图片的校验值均已记录。隔离登记副本原地更新五份元数据，重复执行结果一致。[原生重开](native-reopen.json) · [渲染签名](render-receipts.json) · [登记演练](registration-rehearsal.json)

## 147处真实主图的同镜对照

从登记前后的上海主地图两次选中华俄道胜银行，以同一经纬度、转角、视高和缩放拍摄南侧拱肩。桌面画面为1000×720，手机为390×844。左右对称的卷叶和有翼人像、中央兽首券石在两个实际页面间都产生了可测的图像变化。桌面右侧人像和中央券石较完整，左侧人像上方有地名贴条。手机可见兽首和两侧人像的内段，两翼外端受屏宽限制。[桌面修订前](main-map-before-desktop-detail.png) · [桌面修订后](main-map-after-desktop-detail.png) · [手机修订前](main-map-before-mobile-detail.png) · [手机修订后](main-map-after-mobile-detail.png)

每个新增物件都按真实网格投影到相同视口后核查形状内部的像素。桌面中央券石2228个投影像素中，2129个像素的最大通道变化至少为6。手机相同阈值下为2134个。桌面的两尊有翼人像分别变化4816与4975个像素。画面其他位置同时有阴影和地名变化，区域数据逐项列出。[两屏投影与像素统计](real-map-geometry-pixels.json) · [两个发布版本的文件签名](published-147-source-pair.json) · [实机脚本](check-published-arch.cjs)

最初两次后态运行遭软件渲染进程内存回收，已保留失败时间、传输与错误。恢复时逐图进入真实公开俯瞰链接，核实了登记号、加载的GLB、三角数及帧哈希。前态默认画面保留了从城市目录进入步行、随后选择俯瞰的操作记录。[分段恢复记录](software-renderer-retry.json)

两次登记的普通桌面、手机初选与同镜细节共八幅，原始分段记录包含每个视口的实际模型摘要。[登记前四图记录](main-map-before.json) · [登记后四图记录](main-map-after.json) · [独立实图目检](independent-main-map-review.json)

GitHub 公开固定版本中，地图、入口页、来源说明和四件下载文件等共 30 项均返回 HTTP 200，字节数和 SHA-256 与提交一致。[打开本次提交的地图](https://raw.githack.com/ecojust/e-resource/21dbf957f57704c51c676825c7c30d5812404ed6/projects/shanghai/index.html#landmark=bund15&mode=walk) · [固定版本逐文件核对](publication.json)

首次在 master 检查 30 项时，有 12 项仍是前一版本缓存。[首次 master 核验](publication-master-initial.json)
