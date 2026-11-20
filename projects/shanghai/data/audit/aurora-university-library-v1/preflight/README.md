# 1936年西一号楼北面取形

这张小图使用单线程深度缓冲，将原模型投到2020年9月13日球场侧照片的视角。西楼以实际地块宽59.70米为标尺。两张照片各选取30个上层窗头位置，反求平面投影；斜向照片给出的层高约4.47米，本次采用4.50米。视角近于水平的另一张照片较难确定焦距，用于检验范围。坡度、窗台、壁厚及地面均为估值。[模型小图](field-photograph-view.png) · [来源、取点及限度](../../../../source/precise/huangpu-aurora-university-library/reference-review.json)

左右各五列单窗与中央连续窄窗对齐后，按同一方向复看三联窗，收窄两端窗组并向中央略移，增加了女儿墙的浅色面层厚度。原图中的现代高楼、树木、岗亭和校园告示继续保留为外部照片证据。[原摄影文章](https://www.meipian.cn/35orsqs7)

可在本目录复算。`python check_window_pitch.py` 从照片取点恢复斜向与近水平视图的层高。`OPENBLAS_NUM_THREADS=1 python render_field_preview.py /tmp/aurora-field-view.png` 从同一取点重新生成568×316像素的模型小图，复算PNG的SHA256为 `6d3e984f0758af412e93683cb54ad2126ba21a6dfa70fd80df383e0f43bee7db`。脚本需要仓库的建筑几何工具、NumPy、SciPy、Pillow、Shapely和字体工具。[层高复算](check_window_pitch.py) · [小图渲染](render_field_preview.py)
