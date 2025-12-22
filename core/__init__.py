"""
DeepFocus 核心算法模块

包含人脸检测、特征提取、图像预处理等核心功能
"""

__version__ = '2.1.0'

# 导出核心引擎
from core.face_engine_pro import FaceEnginePro, get_cuda_info
from core.opencv_dnn_engine import (
    OpenCVDNNEngine,
    is_opencv_dnn_available,
    get_opencv_dnn_error,
    check_models_exist
)

__all__ = [
    'FaceEnginePro',
    'get_cuda_info',
    'OpenCVDNNEngine',
    'is_opencv_dnn_available',
    'get_opencv_dnn_error',
    'check_models_exist',
]

