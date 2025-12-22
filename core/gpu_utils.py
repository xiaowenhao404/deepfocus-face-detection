"""
DeepFocus GPU 工具模块 v2.1

提供GPU/CUDA检测、显存管理、性能监控等功能
"""

import logging
from typing import Dict, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)


# ==================== CUDA/GPU 检测 ====================

def check_cuda_available() -> Dict[str, any]:
    """
    检测CUDA是否可用及GPU设备信息
    
    Returns:
        {
            "cuda_available": bool,
            "gpu_count": int,
            "gpu_info": str,
            "dlib_cuda_compiled": bool
        }
    """
    result = {
        "cuda_available": False,
        "gpu_count": 0,
        "gpu_info": "未检测到CUDA支持",
        "dlib_cuda_compiled": False
    }
    
    try:
        import dlib
        
        # 检查dlib是否使用CUDA编译
        if hasattr(dlib, 'DLIB_USE_CUDA') and dlib.DLIB_USE_CUDA:
            result["dlib_cuda_compiled"] = True
            result["cuda_available"] = True
            
            # 获取GPU数量
            if hasattr(dlib, 'cuda') and hasattr(dlib.cuda, 'get_num_devices'):
                gpu_count = dlib.cuda.get_num_devices()
                result["gpu_count"] = gpu_count
                result["gpu_info"] = f"CUDA可用，检测到 {gpu_count} 个GPU设备"
            else:
                result["gpu_info"] = "CUDA可用（dlib已编译CUDA支持）"
        else:
            result["gpu_info"] = "dlib未编译CUDA支持，使用CPU模式"
    except ImportError:
        result["gpu_info"] = "dlib未安装"
    except Exception as e:
        result["gpu_info"] = f"CUDA检测失败: {str(e)}"
    
    return result


# 模块加载时检测一次CUDA（缓存结果）
_CUDA_INFO: Optional[Dict] = None


def get_cuda_info() -> Dict[str, any]:
    """获取CUDA检测结果（使用缓存）"""
    global _CUDA_INFO
    if _CUDA_INFO is None:
        _CUDA_INFO = check_cuda_available()
        logger.info(f"GPU状态: {_CUDA_INFO['gpu_info']}")
    return _CUDA_INFO


def is_cuda_available() -> bool:
    """快速检查CUDA是否可用"""
    return get_cuda_info().get("cuda_available", False)


# ==================== 显存管理 ====================

# 估算的GPU显存限制（根据常见配置）
# 4GB显存大约可以处理 4000x3000 像素的图像
DEFAULT_GPU_MAX_PIXELS = 12_000_000  # 12MP, 约4K分辨率
DEFAULT_CPU_MAX_PIXELS = 25_000_000  # CPU可以处理更大的图像


def estimate_safe_image_size(use_gpu: bool = False) -> int:
    """
    估算安全的最大图像像素数
    
    Args:
        use_gpu: 是否使用GPU处理
        
    Returns:
        最大像素数
    """
    if use_gpu and is_cuda_available():
        return DEFAULT_GPU_MAX_PIXELS
    return DEFAULT_CPU_MAX_PIXELS


def should_resize_for_processing(
    image: np.ndarray,
    use_gpu: bool = False,
    safety_factor: float = 0.8
) -> Tuple[bool, float]:
    """
    判断图像是否需要缩放以安全处理
    
    Args:
        image: 输入图像 (H, W, C) 或 (H, W)
        use_gpu: 是否使用GPU
        safety_factor: 安全系数（0.8表示使用80%的安全限制）
        
    Returns:
        (是否需要缩放, 建议缩放比例)
    """
    if image is None:
        return False, 1.0
    
    h, w = image.shape[:2]
    current_pixels = h * w
    max_pixels = int(estimate_safe_image_size(use_gpu) * safety_factor)
    
    if current_pixels <= max_pixels:
        return False, 1.0
    
    # 计算缩放比例
    scale = np.sqrt(max_pixels / current_pixels)
    return True, scale


def resize_for_processing(
    image: np.ndarray,
    use_gpu: bool = False,
    safety_factor: float = 0.8
) -> Tuple[np.ndarray, float]:
    """
    如果图像太大，缩放到安全尺寸
    
    Args:
        image: 输入图像
        use_gpu: 是否使用GPU
        safety_factor: 安全系数
        
    Returns:
        (处理后的图像, 实际使用的缩放比例)
    """
    import cv2
    
    needs_resize, scale = should_resize_for_processing(image, use_gpu, safety_factor)
    
    if not needs_resize:
        return image, 1.0
    
    h, w = image.shape[:2]
    new_h = int(h * scale)
    new_w = int(w * scale)
    
    logger.info(f"图像过大，缩放处理: {w}x{h} -> {new_w}x{new_h} (比例: {scale:.2f})")
    
    resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def scale_face_locations(
    face_locations: list,
    scale: float
) -> list:
    """
    将人脸位置坐标按比例缩放回原图尺寸
    
    Args:
        face_locations: 人脸位置列表 [(top, right, bottom, left), ...]
        scale: 之前缩放使用的比例
        
    Returns:
        缩放回原图的人脸位置列表
    """
    if abs(scale - 1.0) < 0.001:
        return face_locations
    
    inv_scale = 1.0 / scale
    scaled_locations = []
    
    for (top, right, bottom, left) in face_locations:
        scaled_locations.append((
            int(top * inv_scale),
            int(right * inv_scale),
            int(bottom * inv_scale),
            int(left * inv_scale)
        ))
    
    return scaled_locations


# ==================== 性能计时器 ====================

class PerformanceTimer:
    """
    性能计时器，用于统计处理各阶段耗时
    
    用法:
        timer = PerformanceTimer()
        timer.start("detection")
        # ... 执行检测 ...
        timer.stop("detection")
        
        timer.start("encoding")
        # ... 执行编码 ...
        timer.stop("encoding")
        
        stats = timer.get_stats()
    """
    
    def __init__(self):
        import time
        self._time = time
        self._start_times: Dict[str, float] = {}
        self._durations: Dict[str, float] = {}
        self._total_start: Optional[float] = None
    
    def start_total(self):
        """开始总计时"""
        self._total_start = self._time.time()
    
    def start(self, name: str):
        """开始某阶段计时"""
        self._start_times[name] = self._time.time()
    
    def stop(self, name: str) -> float:
        """停止某阶段计时，返回耗时（秒）"""
        if name not in self._start_times:
            return 0.0
        duration = self._time.time() - self._start_times[name]
        self._durations[name] = duration
        del self._start_times[name]
        return duration
    
    def get_duration(self, name: str) -> float:
        """获取某阶段耗时"""
        return self._durations.get(name, 0.0)
    
    def get_total_time(self) -> float:
        """获取总耗时"""
        if self._total_start is None:
            return sum(self._durations.values())
        return self._time.time() - self._total_start
    
    def get_stats(self) -> Dict[str, float]:
        """获取所有统计数据"""
        stats = dict(self._durations)
        stats["total_time"] = self.get_total_time()
        return stats
    
    def log_summary(self, prefix: str = ""):
        """输出耗时摘要到日志"""
        total = self.get_total_time()
        parts = [f"{k}: {v:.2f}s" for k, v in self._durations.items()]
        summary = f"{prefix}总耗时: {total:.2f}s ({', '.join(parts)})"
        logger.info(summary)

