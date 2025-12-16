"""
DeepFocus 特征匹配模块

提供人脸特征向量的距离计算、批量比对和置信度评分功能
"""

import numpy as np
from typing import List, Tuple
import logging


def euclidean_distance(feat1: np.ndarray, feat2: np.ndarray) -> float:
    """
    计算两个特征向量的欧氏距离
    
    欧氏距离是特征空间中两点之间的直线距离。
    在人脸识别中，距离越小表示两张脸越相似。
    
    公式: d = ||feat1 - feat2|| = sqrt(sum((feat1_i - feat2_i)^2))
    
    Args:
        feat1: 特征向量1 (通常为128维)
        feat2: 特征向量2 (通常为128维)
        
    Returns:
        float: 欧氏距离，范围通常在 0.0 ~ 1.5
            - 0.0: 完全相同
            - < 0.6: 很可能是同一人
            - 0.6 ~ 1.0: 可能相似
            - > 1.0: 不同的人
            
    Examples:
        >>> feat1 = np.random.rand(128)
        >>> feat2 = np.random.rand(128)
        >>> dist = euclidean_distance(feat1, feat2)
        >>> print(f"距离: {dist:.3f}")
        
    References:
        - Schroff, Florian, et al. "FaceNet: A unified embedding for face 
          recognition and clustering." CVPR 2015.
    """
    return np.linalg.norm(feat1 - feat2)


def cosine_similarity(feat1: np.ndarray, feat2: np.ndarray) -> float:
    """
    计算两个特征向量的余弦相似度
    
    余弦相似度衡量两个向量的方向相似程度，不考虑长度。
    
    公式: cos(θ) = (feat1 · feat2) / (||feat1|| * ||feat2||)
    
    Args:
        feat1: 特征向量1
        feat2: 特征向量2
        
    Returns:
        float: 余弦相似度，范围 -1.0 ~ 1.0
            - 1.0: 方向完全相同
            - 0.0: 正交
            - -1.0: 方向完全相反
    """
    # 归一化
    norm1 = np.linalg.norm(feat1)
    norm2 = np.linalg.norm(feat2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    # 点积除以长度积
    return np.dot(feat1, feat2) / (norm1 * norm2)


def batch_compare(
    target_encoding: np.ndarray,
    face_encodings: List[np.ndarray],
    tolerance: float = 0.45,
    method: str = 'euclidean'
) -> List[Tuple[bool, float]]:
    """
    批量比对特征向量
    
    将目标特征与多个候选特征进行比对，返回匹配结果和距离。
    
    Args:
        target_encoding: 目标特征向量
        face_encodings: 待比对的特征向量列表
        tolerance: 匹配阈值（仅对欧氏距离有效）
        method: 距离计算方法
            - 'euclidean': 欧氏距离（默认）
            - 'cosine': 余弦相似度
            
    Returns:
        List[Tuple[bool, float]]: [(是否匹配, 距离/相似度), ...]
        
    Examples:
        >>> target = np.random.rand(128)
        >>> candidates = [np.random.rand(128) for _ in range(10)]
        >>> results = batch_compare(target, candidates, tolerance=0.45)
        >>> matches = [r for r in results if r[0]]
        >>> print(f"找到 {len(matches)} 个匹配")
    """
    logger = logging.getLogger(__name__)
    results = []
    
    for i, encoding in enumerate(face_encodings):
        if method == 'euclidean':
            # 欧氏距离
            distance = euclidean_distance(target_encoding, encoding)
            is_match = distance <= tolerance
            metric = distance
        elif method == 'cosine':
            # 余弦相似度（转换为距离）
            similarity = cosine_similarity(target_encoding, encoding)
            distance = 1 - similarity  # 转换为距离（0=相同，2=完全不同）
            is_match = distance <= (1 - tolerance)
            metric = distance
        else:
            raise ValueError(f"不支持的距离方法: {method}")
        
        results.append((is_match, metric))
        
        if is_match:
            logger.debug(f"候选#{i} 匹配成功，距离: {metric:.4f}")
    
    return results


def compute_confidence(distance: float, tolerance: float = 0.45) -> float:
    """
    将欧氏距离转换为置信度百分比
    
    置信度表示匹配的可信程度，值越大表示越确信是同一人。
    
    计算方法:
        - 当 distance >= tolerance 时，置信度为 0%
        - 当 distance = 0 时，置信度为 100%
        - 线性插值中间值
    
    公式: confidence = (1 - distance / tolerance) × 100
    
    Args:
        distance: 欧氏距离
        tolerance: 匹配阈值
        
    Returns:
        float: 置信度百分比，范围 0.0 ~ 100.0
        
    Examples:
        >>> # 完美匹配
        >>> conf = compute_confidence(0.0, 0.45)
        >>> print(f"{conf:.1f}%")  # 100.0%
        
        >>> # 中等匹配
        >>> conf = compute_confidence(0.30, 0.45)
        >>> print(f"{conf:.1f}%")  # 33.3%
        
        >>> # 不匹配
        >>> conf = compute_confidence(0.60, 0.45)
        >>> print(f"{conf:.1f}%")  # 0.0%
    """
    if distance >= tolerance:
        return 0.0
    
    # 距离越小，置信度越高
    # distance=0 -> confidence=100
    # distance=tolerance -> confidence=0
    confidence = (1 - distance / tolerance) * 100
    
    # 限制范围 [0, 100]
    return min(100.0, max(0.0, confidence))


def find_best_match(
    target_encoding: np.ndarray,
    face_encodings: List[np.ndarray],
    tolerance: float = 0.45
) -> Tuple[int, float, bool]:
    """
    找到最佳匹配的人脸
    
    在候选列表中找到与目标最相似的人脸。
    
    Args:
        target_encoding: 目标特征向量
        face_encodings: 候选特征向量列表
        tolerance: 匹配阈值
        
    Returns:
        Tuple[int, float, bool]: (最佳匹配索引, 距离, 是否匹配)
            - 如果没有候选，返回 (-1, 1.0, False)
            
    Examples:
        >>> target = np.random.rand(128)
        >>> candidates = [np.random.rand(128) for _ in range(5)]
        >>> idx, dist, matched = find_best_match(target, candidates)
        >>> if matched:
        ...     print(f"最佳匹配: 候选#{idx}, 距离: {dist:.3f}")
    """
    if not face_encodings:
        return -1, 1.0, False
    
    # 计算所有距离
    distances = [
        euclidean_distance(target_encoding, encoding)
        for encoding in face_encodings
    ]
    
    # 找到最小距离
    best_idx = int(np.argmin(distances))
    best_distance = distances[best_idx]
    is_match = best_distance <= tolerance
    
    return best_idx, best_distance, is_match


def calculate_match_statistics(
    target_encoding: np.ndarray,
    face_encodings: List[np.ndarray],
    tolerance: float = 0.45
) -> dict:
    """
    计算匹配统计信息
    
    Args:
        target_encoding: 目标特征向量
        face_encodings: 候选特征向量列表
        tolerance: 匹配阈值
        
    Returns:
        dict: 统计信息字典
            - total: 总人脸数
            - matched: 匹配数
            - unmatched: 未匹配数
            - min_distance: 最小距离
            - max_distance: 最大距离
            - avg_distance: 平均距离
            - match_rate: 匹配率 (%)
    """
    if not face_encodings:
        return {
            'total': 0,
            'matched': 0,
            'unmatched': 0,
            'min_distance': 0.0,
            'max_distance': 0.0,
            'avg_distance': 0.0,
            'match_rate': 0.0
        }
    
    # 计算所有距离
    distances = [
        euclidean_distance(target_encoding, encoding)
        for encoding in face_encodings
    ]
    
    # 统计匹配数
    matches = [d for d in distances if d <= tolerance]
    
    return {
        'total': len(face_encodings),
        'matched': len(matches),
        'unmatched': len(face_encodings) - len(matches),
        'min_distance': float(np.min(distances)),
        'max_distance': float(np.max(distances)),
        'avg_distance': float(np.mean(distances)),
        'match_rate': (len(matches) / len(face_encodings)) * 100
    }


# 常用阈值配置
TOLERANCE_PRESETS = {
    'strict': 0.35,      # 严格模式：减少误报
    'normal': 0.45,      # 正常模式：推荐用于亚洲人脸
    'loose': 0.55,       # 宽松模式：提高召回率
    'very_loose': 0.65   # 非常宽松：最大召回率
}


def get_recommended_tolerance(scenario: str = 'normal') -> float:
    """
    获取推荐的匹配阈值
    
    Args:
        scenario: 应用场景
            - 'strict': 严格模式，适合安全场景
            - 'normal': 正常模式，适合一般应用
            - 'loose': 宽松模式，适合查找场景
            - 'very_loose': 非常宽松，最大化召回
            
    Returns:
        float: 推荐阈值
    """
    return TOLERANCE_PRESETS.get(scenario, 0.45)

