# OpenCV Zoo 模型文件

本目录存放 OpenCV DNN 引擎所需的 ONNX 模型文件。

## 所需模型

1. **YuNet 人脸检测模型**: `face_detection_yunet_2023mar.onnx`
2. **SFace 人脸识别模型**: `face_recognition_sface_2021dec.onnx`

## 自动下载

运行以下命令自动下载模型：

```bash
python models/download_models.py
```

## 手动下载

如果自动下载失败，请从以下地址手动下载：

- YuNet: https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx
- SFace: https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx

下载后将文件放置到本目录 (`models/`) 下。

