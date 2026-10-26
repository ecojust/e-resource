# 独立模型交付记录

本记录冻结于v2独立模型交付阶段。原生预览实际对照两原图通过；本阶段尚未进行HTML第三人称视角、目录发现、远近切换或遮罩生命周期验收。以后应用通过记录由项目另行增加，不能把这份阶段报告读成最终应用状态。

- [raw模型](../../../assets/models/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church-raw.glb)：27,113,064字节，SHA256 `f31ec44a361d58924bc3c7fa3298584b2df69c9791d910ad3025578933b39bd3`。
- [web模型](../../../assets/models/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church-web.glb)：10,619,436字节，SHA256 `d8007acbfe2344684e3e05c22cd9f35001b8d71e1833c2d06eeff62f75b11721`。
- [native模型](../../../assets/native/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church.blend)：39,953,968字节，SHA256 `e4b43f1c431cceb33b26974092879b6f5d4591de6a64cc3a91ff54ec52af619f`。
- [lod模型](../../../assets/models/precise/14-13720-6692/hongkou-hongde-church/hongkou-hongde-church-lod.glb)：5,212,724字节，SHA256 `c6d7af387f745102702bdf0f2349a2b26a0129d1cfab86ca49b2c455794e0a75`。

[原生预览](evidence/native-preview.png)及[root实际视觉记录](audit/root-native-visual-review.json)支持三项v2改正：低翼连续向后升的曲檐取代独立尖亭；整排砖色条纹改为低幅不规则色差；翼拱窗上部菱格、下部矩形格，圆窗以蓝色为主。塔内环鼓座和后脊做实心贴合封口。v1模型未重复打包。

[实际解码检查](evidence/decoded-package-check.json)绑定raw/web378,504有向位置和材质三角；法线最大0.023652°小于既有0.05°容差，LOD178,968三角且包围边界变化0.021613m。三档297个洞口内射线、实体墙负控及门内通道检查通过；这些是有限样本，不是全表面Hausdorff证明。[瓦搭接检查](audit/tile-lap-check.json)将真实Float32瓦三角逐一绑定原GLB，3,080对／27,720点净距4.219–10.619mm；不是只根据渲染图判断共面。所有GLB均0图片／0纹理。

[离线重建](audit/portable-rebuild.json)已在独立临时目录用当前源码生成相同raw SHA。轮廓来源、推定高度18.5–24m敏感范围及不确定后部见[calibration.json](calibration.json)。约21.55m名义顶高并非现场实测；既有17.25m是CNBH10m栅格估值，不是钟楼顶高。

打包使用项目source/precise/tooling/package_precise_building.py，显式传--shared-helper source/bund/photo-rebuild-v6/common/package_building.py及本目录packaging-input.json、raw、native、gltfpack、项目根和全新独立output。已安装资产受保护；重复打包可使用只含原tools/build_bund_lods.py的空白临时项目，不要删除现有资产绕过保护。check_decoded_package.mjs的三参数为PROJECT、PACKAGE_PARENT、MODEL_SOURCE，其中PACKAGE_PARENT/package为新压缩输出。源码不自动安装、登记或发布。

JSON审计保持产生时的原字节；其中绝对工作路径仅为历史定位。当前源副本、资产与照片SHA见[delivery-record.json](delivery-record.json)，全部文件白名单见[source-package-files.json](source-package-files.json)。当前报告中的原生数值构建阶段visual=false不否定其后独立root视觉证据；同样不能用原生通过推断浏览器通过。
