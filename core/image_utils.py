"""
DeepFocus 图像工具模块

提供图像读取、保存、转换、缩放等通用工具函数
"""

import cv2
import numpy as np
from typing import Optional, Tuple
import logging
import os


def safe_imread(file_path: str) -> Optional[np.ndarray]:
    """
    安全读取图像，支持中文路径
    
    OpenCV的cv2.imread不支持包含中文的文件路径，
    本函数使用numpy读取二进制数据，再用cv2解码的方式解决此问题。
    
    Args:
        file_path: 图像文件路径（支持中文）
        
    Returns:
        Optional[np.ndarray]: 图像数组（BGR格式），失败返回None
        
    Examples:
        >>> img = safe_imread("Images/目标脸.jpg")
        >>> if img is not None:
        ...     print(f"图像尺寸: {img.shape}")
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            logger.error(f"文件不存在: {file_path}")
            return None
        
        # 使用numpy读取二进制数据
        img_data = np.fromfile(file_path, dtype=np.uint8)
        
        # 使用cv2解码图像
        img = cv2.imdecode(img_data, cv2.IMREAD_COLOR)
        
        if img is None:
            logger.error(f"图像解码失败: {file_path}")
            return None
        
        logger.debug(f"成功读取图像: {file_path}, 尺寸: {img.shape}")
        return img
        
    except Exception as e:
        logger.exception(f"读取图像时发生错误 {file_path}: {e}")
        return None


def save_image(image: np.ndarray, file_path: str, quality: int = 95) -> bool:
    """
    保存图像，支持中文路径
    
    使用cv2.imencode编码后写入文件的方式，支持中文路径。
    
    Args:
        image: 图像数组（BGR格式）
        file_path: 保存路径（支持中文）
        quality: JPEG质量（1-100），默认95
            
    Returns:
        bool: 成功返回True，失败返回False
        
    Examples:
        >>> img = cv2.imread("input.jpg")
        >>> success = save_image(img, "输出/结果.jpg", quality=95)
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.debug(f"创建目录: {dir_path}")
        
        # 根据文件扩展名选择编码格式
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.jpg', '.jpeg']:
            # JPEG格式，可设置质量
            encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
            success, img_encode = cv2.imencode('.jpg', image, encode_param)
        elif ext == '.png':
            # PNG格式
            success, img_encode = cv2.imencode('.png', image)
        else:
            # 默认使用JPEG
            success, img_encode = cv2.imencode('.jpg', image)
        
        if not success:
            logger.error(f"图像编码失败: {file_path}")
            return False
        
        # 写入文件
        img_encode.tofile(file_path)
        
        logger.debug(f"成功保存图像: {file_path}")
        return True
        
    except Exception as e:
        logger.exception(f"保存图像时发生错误 {file_path}: {e}")
        return False


def resize_image(
    image: np.ndarray,
    max_dimension: int = 1920
) -> Tuple[np.ndarray, float]:
    """
    等比例缩放图像到指定最大尺寸
    
    保持图像宽高比不变，将图像缩放到指定的最大边长。
    适用于处理超大图像以节省内存和计算时间。
    
    Args:
        image: 输入图像
        max_dimension: 最大边长（像素），默认1920
            
    Returns:
        Tuple[np.ndarray, float]: (缩放后的图像, 缩放比例)
            - 缩放比例 < 1.0 表示缩小
            - 缩放比例 = 1.0 表示未缩放
            - 缩放比例 > 1.0 表示放大（通常不推荐）
            
    Examples:
        >>> img = cv2.imread("large_image.jpg")  # 3000x2000
        >>> resized, scale = resize_image(img, max_dimension=1920)
        >>> print(f"缩放比例: {scale}, 新尺寸: {resized.shape}")
        缩放比例: 0.64, 新尺寸: (1280, 1920, 3)
    """
    logger = logging.getLogger(__name__)
    
    height, width = image.shape[:2]
    max_dim = max(height, width)
    
    # 如果图像不超过最大尺寸，直接返回
    if max_dim <= max_dimension:
        logger.debug(f"图像无需缩放: {width}x{height}")
        return image, 1.0
    
    # 计算缩放比例
    scale = max_dimension / max_dim
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    logger.info(f"缩放图像: {width}x{height} -> {new_width}x{new_height} (scale={scale:.3f})")
    
    # 缩小图像使用INTER_AREA插值（效果最好）
    # 放大图像使用INTER_CUBIC插值
    interpolation = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_CUBIC
    
    resized = cv2.resize(
        image,
        (new_width, new_height),
        interpolation=interpolation
    )
    
    return resized, scale


def convert_color_space(
    image: np.ndarray,
    target: str = 'RGB'
) -> np.ndarray:
    """
    色彩空间转换
    
    支持常见色彩空间之间的转换。
    假设输入图像为BGR格式（OpenCV默认）。
    
    Args:
        image: 输入图像（BGR格式）
        target: 目标色彩空间
            - 'RGB': RGB色彩空间（face_recognition需要）
            - 'GRAY': 灰度图
            - 'HSV': HSV色彩空间（色调、饱和度、明度）
            - 'LAB': LAB色彩空间（亮度、A通道、B通道）
            
    Returns:
        np.ndarray: 转换后的图像
        
    Raises:
        ValueError: 如果目标色彩空间不支持
        
    Examples:
        >>> bgr_img = cv2.imread("image.jpg")
        >>> rgb_img = convert_color_space(bgr_img, 'RGB')
        >>> gray_img = convert_color_space(bgr_img, 'GRAY')
    """
    logger = logging.getLogger(__name__)
    
    # 色彩空间转换映射
    conversions = {
        'RGB': cv2.COLOR_BGR2RGB,
        'GRAY': cv2.COLOR_BGR2GRAY,
        'HSV': cv2.COLOR_BGR2HSV,
        'LAB': cv2.COLOR_BGR2LAB
    }
    
    if target not in conversions:
        raise ValueError(
            f"不支持的色彩空间: {target}。"
            f"支持的选项: {', '.join(conversions.keys())}"
        )
    
    logger.debug(f"色彩空间转换: BGR -> {target}")
    converted = cv2.cvtColor(image, conversions[target])
    
    return converted


def crop_image(
    image: np.ndarray,
    x: int,
    y: int,
    width: int,
    height: int
) -> np.ndarray:
    """
    裁剪图像区域
    
    Args:
        image: 输入图像
        x: 左上角x坐标
        y: 左上角y坐标
        width: 裁剪宽度
        height: 裁剪高度
        
    Returns:
        np.ndarray: 裁剪后的图像
        
    Examples:
        >>> img = cv2.imread("image.jpg")
        >>> face_region = crop_image(img, 100, 100, 200, 200)
    """
    # 确保坐标在有效范围内
    h, w = image.shape[:2]
    x = max(0, min(x, w))
    y = max(0, min(y, h))
    x2 = min(x + width, w)
    y2 = min(y + height, h)
    
    return image[y:y2, x:x2].copy()


def get_image_info(image: np.ndarray) -> dict:
    """
    获取图像信息
    
    Args:
        image: 输入图像
        
    Returns:
        dict: 包含图像信息的字典
            - shape: 图像形状 (height, width, channels)
            - dtype: 数据类型
            - size: 总像素数
            - channels: 通道数
            - memory: 内存占用（MB）
    """
    info = {
        'shape': image.shape,
        'dtype': str(image.dtype),
        'size': image.size,
        'channels': 1 if len(image.shape) == 2 else image.shape[2],
        'memory_mb': image.nbytes / (1024 * 1024)
    }
    
    return info


def validate_image(image: Optional[np.ndarray]) -> bool:
    """
    验证图像是否有效
    
    Args:
        image: 图像数组
        
    Returns:
        bool: 有效返回True，否则返回False
    """
    if image is None:
        return False
    
    if not isinstance(image, np.ndarray):
        return False
    
    if image.size == 0:
        return False
    
    if len(image.shape) not in [2, 3]:
        return False
    
    return True


# 图像格式转换常量
IMAGE_FORMATS = {
    'JPEG': ['.jpg', '.jpeg'],
    'PNG': ['.png'],
    'BMP': ['.bmp'],
    'TIFF': ['.tif', '.tiff']
}


def get_supported_formats() -> list:
    """
    获取支持的图像格式列表
    
    Returns:
        list: 支持的文件扩展名列表
    """
    formats = []
    for exts in IMAGE_FORMATS.values():
        formats.extend(exts)
    return formats


def is_supported_format(file_path: str) -> bool:
    """
    检查文件格式是否支持
    
    Args:
        file_path: 文件路径
        
    Returns:
        bool: 支持返回True，否则返回False
    """
    ext = os.path.splitext(file_path)[1].lower()
    return ext in get_supported_formats()

