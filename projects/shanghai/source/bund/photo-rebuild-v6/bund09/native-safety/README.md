# 09原生文件压缩与核验预案

本目录只准备脚本与普通Python验证，**尚未运行Blender，也没有生成09原生工程**。公共helper未修改。

09旧候选raw（SHA `bc95e772312de70f289ad170bf1d6814a469ac9650ac3834e7dcb591c1fa77a3`）含1,792,010顶点、735,922三角、1,999,948条唯一索引边。按当前实际4.3.2、source SHA匹配的06/14未压缩native块布局估计，09未压缩文件约100.63–100.72MB，略超过100 MB。此为估计，不是已经测得的09native大小；玻璃嵌框调整后应重新确认顶点数，三角数不变。

估算方法是`13V + 9E + 70T + packedJPEG + 固定开销`。06/14实际DATA块分别支持位置12V、布尔V、边8E与布尔E、每三角3个corner共60T、面索引／材料／布尔共10T；非网格开销约0.70–0.80MB。05现raw与旧native报告source SHA不匹配，因此未用于估算。

建议root直接保存压缩原生文件。从本栋目录运行：

```sh
blender -b --python native-safety/blender_finish_compressed.py -- \
  --glb output/bund09-raw.glb --output native-compressed --render \
  --view-azimuth 72.05 --view-elevation 0 --width 1300 --height 950
python native-safety/validate_native_storage.py \
  --input native-compressed/bund09-raw.blend \
  --report native-compressed/storage-check.json
blender -b --python native-safety/blender_reopen_verify.py -- \
  --native native-compressed/bund09-raw.blend --raw output/bund09-raw.glb \
  --report native-compressed/reopen-check.json
```

`blender_finish_compressed.py`锁定公共finisher SHA `d0859e6692b7a603872c14897876f3f021017f90e4938bcd3dc0eb3083cc03d1`，只在内存中将唯一保存调用增加`compress=True`，并记录原helper、wrapper哈希。导入、几何、原JPEG、相机和普通报告逻辑保持原样；若公共文件变动，脚本拒绝继续，要求重新审阅。实际存储格式以文件头核验，不按后缀猜测。

如果已经正常保存了未压缩文件，即使其略大于100MB，也可以**不启动Blender**进行无损封装，保留旧文件：

```sh
python native-safety/compress_existing_blend.py \
  --input native-uncompressed/bund09-raw.blend \
  --output native-compressed/bund09-raw.blend \
  --report native-compressed/compression-check.json
```

该脚本使用带校验和的Zstandard，把原文件字节完整压缩；流式解压SHA必须等于原native SHA，源文件SHA必须未变，最终物理文件必须小于100 MB，才原子落到新路径。随后仍需root用Blender重开检查，不能把压缩往返等同于场景已验收。

存储校验识别`BLENDER`原始头、gzip `1f8b`、Zstandard `28b52ffd`，完整流式遍历BHead到SDNA/ENDB、检查流结束/CRC、统计解码SHA，拒绝截断、负长度和尾随数据。默认解压总量上限512MiB，Zstandard窗口上限128MiB；不把解码内容写出第二份文件。已通过plain/gzip/zstd/多frame、超限、CRC与截断fixture，并只读验证现有06真native，见`python-validation.json`。fixture只验证文件读取逻辑，不是假装真实Blender场景。

当前冻结的`common/package_building.py`已原生识别plain/gzip/zstd头（`blender_header`函数），且环境已安装`zstandard`，因此**不需要改打包helper或绕开其100MB核验**：将通过检查的压缩`.blend`作为原有`--native`输入即可，仍字节相同复制并记录其实际压缩文件SHA。现helper只解码12字节识别头，完整有界存储核验由本目录补充。native场景重开另检查建筑collection的三角数、转换轴后的边界和packed JPEG原字节，视觉效果仍由root渲染／浏览器单独验收。
