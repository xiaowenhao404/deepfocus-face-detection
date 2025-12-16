"""
DeepFocus 全局配置文件

包含项目的默认参数设置、路径配置等
"""

# ==================== 人脸识别参数配置 ====================

# 默认检测模型方法
# 'hog': HOG (Histogram of Oriented Gradients) - 速度快，适合CPU
# 'cnn': CNN (Convolutional Neural Network) - 精度高，需要GPU
DEFAULT_MODEL_METHOD = 'hog'

# 默认匹配容忍度（欧氏距离阈值）
# 范围: 0.0 ~ 1.0
# 值越小越严格，越大越宽松
# 针对亚洲人脸，推荐值: 0.40 ~ 0.45
DEFAULT_TOLERANCE = 0.45

# 默认上采样次数
# 0: 不上采样，速度最快
# 1: 标准模式（默认）
# 2: 检测小人脸，适合教室等远距离场景
DEFAULT_UPSAMPLE = 1


# ==================== 路径配置 ====================

# 测试图像目录
IMAGES_DIR = 'Images/'

# 识别结果输出目录
OUTPUTS_DIR = 'outputs/results/'

# 日志文件目录
LOGS_DIR = 'outputs/logs/'


# ==================== CLAHE 图像增强参数 ====================

# 对比度限制阈值
CLAHE_CLIP_LIMIT = 2.0

# 分块大小（tile grid size）
CLAHE_TILE_SIZE = 8


# ==================== GUI 配置 ====================

# 主窗口默认尺寸
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800

# 图像显示区域最小尺寸
IMAGE_DISPLAY_MIN_WIDTH = 800
IMAGE_DISPLAY_MIN_HEIGHT = 600


# ==================== 图像处理配置 ====================

# 图像最大尺寸限制（用于内存优化）
# 超过此尺寸的图像会先缩放再处理
MAX_IMAGE_DIMENSION = 1920

# 图像保存质量（JPEG）
IMAGE_SAVE_QUALITY = 95


# ==================== 日志配置 ====================

# 日志级别
# DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = 'INFO'

# 日志文件名
LOG_FILE = 'app.log'

# 错误日志文件名
ERROR_LOG_FILE = 'error.log'


# ==================== 其他配置 ====================

# 应用程序名称
APP_NAME = 'DeepFocus'

# 应用程序版本
APP_VERSION = '1.0.0'

# 作者信息
AUTHOR = 'DeepFocus Team'

# GitHub仓库地址
GITHUB_URL = 'https://github.com/xiaowenhao404/DeepFocus'

