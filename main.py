"""
DeepFocus - 人脸识别与定位系统
主程序入口文件

Author: DeepFocus Team
Version: 1.0.0
GitHub: https://github.com/xiaowenhao404/DeepFocus
"""

import sys
import logging
from pathlib import Path

# 导入配置
import config


def setup_logging():
    """
    初始化日志系统
    
    配置日志格式、级别和输出位置
    """
    # 确保日志目录存在
    log_dir = Path(config.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 控制台输出
            logging.StreamHandler(sys.stdout),
            # 文件输出
            logging.FileHandler(
                log_dir / config.LOG_FILE,
                encoding='utf-8'
            )
        ]
    )
    
    # 配置错误日志（单独文件）
    error_handler = logging.FileHandler(
        log_dir / config.ERROR_LOG_FILE,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(log_format, datefmt=date_format)
    )
    logging.getLogger().addHandler(error_handler)
    
    logging.info(f"{config.APP_NAME} v{config.APP_VERSION} 启动")


def check_dependencies():
    """
    检查必要的依赖库是否已安装
    
    Returns:
        bool: 所有依赖都满足返回True，否则返回False
    """
    required_modules = [
        ('cv2', 'opencv-python'),
        ('numpy', 'numpy'),
        ('face_recognition', 'face-recognition'),
        ('PyQt5', 'PyQt5'),
    ]
    
    missing = []
    for module_name, package_name in required_modules:
        try:
            __import__(module_name)
            logging.info(f"[OK] 依赖检查通过: {package_name}")
        except ImportError:
            missing.append(package_name)
            logging.error(f"[MISSING] 依赖缺失: {package_name}")
    
    if missing:
        print("\n" + "="*50)
        print("错误：缺少必要的依赖库！")
        print("="*50)
        print("\n请运行以下命令安装依赖：")
        print(f"  pip install {' '.join(missing)}")
        print("\n或者安装所有依赖：")
        print("  pip install -r requirements.txt")
        print("="*50 + "\n")
        return False
    
    return True


def main():
    """
    主函数
    
    初始化系统并启动GUI应用
    """
    try:
        # 初始化日志
        setup_logging()
        
        # 检查依赖
        logging.info("正在检查依赖...")
        if not check_dependencies():
            sys.exit(1)
        
        # TODO: 启动GUI应用（TASK004 中实现）
        # from PyQt5.QtWidgets import QApplication
        # from gui.main_window import MainWindow
        # 
        # app = QApplication(sys.argv)
        # 
        # # 加载样式表
        # try:
        #     with open('gui/styles.qss', 'r', encoding='utf-8') as f:
        #         app.setStyleSheet(f.read())
        # except FileNotFoundError:
        #     logging.warning("未找到样式表文件 gui/styles.qss")
        # 
        # window = MainWindow()
        # window.show()
        # 
        # sys.exit(app.exec_())
        
        logging.info("项目基础架构搭建完成！")
        logging.info("GUI模块将在 TASK004 中实现")
        print("\n" + "="*60)
        print(f"  {config.APP_NAME} v{config.APP_VERSION}")
        print("  人脸识别与定位系统")
        print("="*60)
        print("\n[OK] 项目初始化成功！")
        print(f"[OK] 日志目录: {config.LOGS_DIR}")
        print(f"[OK] 输出目录: {config.OUTPUTS_DIR}")
        print("\n下一步：开始开发核心模块（TASK002）")
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        logging.info("用户中断程序")
        print("\n程序已终止")
        sys.exit(0)
        
    except Exception as e:
        logging.exception(f"程序运行出错: {e}")
        print(f"\n错误: {e}")
        print(f"详细信息请查看日志文件: {config.LOGS_DIR}{config.ERROR_LOG_FILE}")
        sys.exit(1)


if __name__ == "__main__":
    main()

