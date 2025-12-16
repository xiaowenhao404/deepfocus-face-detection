"""
DeepFocus 图像预处理模块

实现CLAHE自适应直方图均衡化等图像增强算法
"""

import cv2
import numpy as np
from typing import Optional
import logging


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_size: int = 8
) -> np.ndarray:
    """
    应用CLAHE（Contrast Limited Adaptive Histogram Equalization）
    限制对比度自适应直方图均衡化
    
    CLAHE是传统直方图均衡化的改进版本，能够有效增强局部对比度，
    同时避免噪声放大。特别适合处理光照不均的图像。
    
    算法原理：
        1. 将图像分成若干小块（tiles），例如8x8
        2. 每个小块独立进行直方图均衡化
        3. 使用clip_limit限制对比度，防止噪声放大
        4. 使用双线性插值平滑块边界
    
    Args:
        image: 输入图像（BGR格式或灰度图）
        clip_limit: 对比度限制阈值，范围通常为1.0-4.0
            - 值越大，对比度增强越明显
            - 值越小，噪声放大越少
            - 默认2.0为经验最优值
        tile_size: 分块大小（像素），默认8x8
            - 值越小，局部增强越细致
            - 值越大，处理速度越快
            
    Returns:
        np.ndarray: 增强后的图像，格式与输入相同
        
    Examples:
        >>> img = cv2.imread("dark_image.jpg")
        >>> enhanced = apply_clahe(img, clip_limit=2.0, tile_size=8)
        >>> cv2.imwrite("enhanced.jpg", enhanced)
        
    References:
        Zuiderveld, Karel. "Contrast limited adaptive histogram equalization."
        Graphics gems (1994): 474-485.
    """
    logger = logging.getLogger(__name__)
    
    # 如果是彩色图，转换到LAB色彩空间
    # LAB空间将亮度（L）和色度（A, B）分离
    # 只对亮度通道进行增强，保持颜色不变
    if len(image.shape) == 3:
        logger.debug("彩色图像，转换到LAB空间处理")
        
        # BGR转LAB
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        
        # 分离通道
        l_channel, a_channel, b_channel = cv2.split(lab)
        
        # 创建CLAHE对象
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=(tile_size, tile_size)
        )
        
        # 只对L（亮度）通道应用CLAHE
        l_channel = clahe.apply(l_channel)
        
        # 合并通道
        lab = cv2.merge([l_channel, a_channel, b_channel])
        
        # LAB转回BGR
        enhanced = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
        
        logger.debug("CLAHE增强完成（彩色图）")
        return enhanced
        
    else:
        # 灰度图直接处理
        logger.debug("灰度图像，直接应用CLAHE")
        
        clahe = cv2.createCLAHE(
            clipLimit=clip_limit,
            tileGridSize=(tile_size, tile_size)
        )
        
        enhanced = clahe.apply(image)
        
        logger.debug("CLAHE增强完成（灰度图）")
        return enhanced


def histogram_equalization(image: np.ndarray) -> np.ndarray:
    """
    传统全局直方图均衡化
    
    相比CLAHE，全局直方图均衡化速度更快，但可能导致噪声放大。
    适合整体偏暗或偏亮的图像。
    
    Args:
        image: 输入图像（BGR格式或灰度图）
        
    Returns:
        np.ndarray: 均衡化后的图像
    """
    if len(image.shape) == 3:
        # 彩色图：在LAB空间的L通道处理
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        l = cv2.equalizeHist(l)
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
    else:
        # 灰度图：直接均衡化
        return cv2.equalizeHist(image)


def gamma_correction(image: np.ndarray, gamma: float = 1.0) -> np.ndarray:
    """
    伽马校正
    
    调整图像的整体亮度，适合处理过曝或欠曝的图像。
    
    Args:
        image: 输入图像
        gamma: 伽马值
            - gamma < 1: 增亮图像
            - gamma = 1: 不变
            - gamma > 1: 变暗图像
            
    Returns:
        np.ndarray: 校正后的图像
        
    Examples:
        >>> # 增亮暗图
        >>> bright_img = gamma_correction(dark_img, gamma=0.5)
        >>> # 变暗亮图
        >>> dark_img = gamma_correction(bright_img, gamma=2.0)
    """
    # 构建查找表
    inv_gamma = 1.0 / gamma
    table = np.array([
        ((i / 255.0) ** inv_gamma) * 255
        for i in np.arange(0, 256)
    ]).astype("uint8")
    
    # 应用查找表
    return cv2.LUT(image, table)


def denoise_image(
    image: np.ndarray,
    method: str = 'bilateral',
    strength: int = 10
) -> np.ndarray:
    """
    图像去噪
    
    Args:
        image: 输入图像
        method: 去噪方法
            - 'bilateral': 双边滤波（保边去噪）
            - 'gaussian': 高斯滤波
            - 'median': 中值滤波
        strength: 去噪强度（1-30）
            
    Returns:
        np.ndarray: 去噪后的图像
    """
    if method == 'bilateral':
        # 双边滤波：保持边缘的同时去噪
        return cv2.bilateralFilter(image, strength, strength*2, strength*2)
    elif method == 'gaussian':
        # 高斯滤波
        kernel_size = strength * 2 + 1  # 必须为奇数
        return cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
    elif method == 'median':
        # 中值滤波：对椒盐噪声效果好
        kernel_size = strength * 2 + 1
        return cv2.medianBlur(image, kernel_size)
    else:
        raise ValueError(f"不支持的去噪方法: {method}")


def enhance_image_quality(
    image: np.ndarray,
    apply_clahe_flag: bool = True,
    denoise_flag: bool = False
) -> np.ndarray:
    """
    综合图像质量增强
    
    整合多种预处理技术，一站式提升图像质量。
    
    Args:
        image: 输入图像
        apply_clahe_flag: 是否应用CLAHE增强
        denoise_flag: 是否去噪
        
    Returns:
        np.ndarray: 增强后的图像
    """
    result = image.copy()
    
    # 去噪（如果需要）
    if denoise_flag:
        result = denoise_image(result, method='bilateral', strength=5)
    
    # CLAHE增强（如果需要）
    if apply_clahe_flag:
        result = apply_clahe(result, clip_limit=2.0, tile_size=8)
    
    return result

