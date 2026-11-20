# 正广和公司福州路历史街翼

1937年，正广和洋行在福州路44号建造上海总部。市第二批优秀历史建筑名录以2A029登记该处。2014年1月26日的街面正照显示一楼清水砖墙，上层红褐色木构件和浅色粉刷面，双山墙略向街上伸出。后侧另有建筑和院落。茂海路旧汽水厂、通北路400号的厂房和武康路99号的大班住宅各有自己的历史资料。[照片与历史资料](reference-review.json) · [街翼轮廓及按址匹配](footprint-review.json)

三维模型取照片可见的两组四窗山墙、中央窗带、临街大开口、砖砌烟囱和交接的瓦坡。屋高、各层进深及深色开口后的收口根据外观估计。照片仅供参照，模型的红瓦、木框、玻璃及砖材均由几何和独立颜色生成。[独立查看页](../../../caldbeck-macgregor.html) · [可编辑与网页成品](../../../assets/models/candidates/huangpu-caldbeck-macgregor-building/manifest.json) · [照片复核及模型检查](../../../data/audit/caldbeck-macgregor-v1/README.md)

在上海项目目录运行以下命令。构建使用Python、NumPy、Shapely、Blender、gltfpack、ImageMagick和Open Image Denoise。四种成品及原生重开渲染分别写到指定目录。

```sh
python source/precise/huangpu-caldbeck-macgregor-building/source/build_model.py \
  --out /tmp/caldbeck-assets --audit /tmp/caldbeck-audit --decoded /tmp/caldbeck-decoded \
  --gltfpack gltfpack --blender blender --oidn oidnDenoise
python data/audit/caldbeck-macgregor-v1/check-street.py --project . \
  --manifest /tmp/caldbeck-assets/manifest.json --decoded /tmp/caldbeck-decoded \
  --out /tmp/caldbeck-audit/street-checks.json
```
