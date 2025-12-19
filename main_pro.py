"""
DeepFocus Pro v2.0 - 增强版主程序入口

使用FaceEnginePro和macOS风格界面
支持多目标照片、批量处理、可缩放查看、处理过程可视化
"""

import sys
import logging
from pathlib import Path

# 导入配置
import config


def setup_logging():
    """初始化日志系统"""
    log_dir = Path(config.LOGS_DIR)
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=log_format,
        datefmt=date_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                log_dir / config.LOG_FILE,
                encoding='utf-8'
            )
        ]
    )
    
    error_handler = logging.FileHandler(
        log_dir / config.ERROR_LOG_FILE,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(
        logging.Formatter(log_format, datefmt=date_format)
    )
    logging.getLogger().addHandler(error_handler)
    
    logging.info(f"{config.APP_NAME} Pro v{config.APP_VERSION} 启动")


def check_dependencies():
    """检查必要的依赖库"""
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
    """主函数"""
    try:
        # 初始化日志
        setup_logging()
        
        # 检查依赖
        logging.info("正在检查依赖...")
        if not check_dependencies():
            sys.exit(1)
        
        # 启动GUI应用
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import Qt
        from gui.main_window_pro import MainWindowPro
        
        logging.info("启动增强版GUI应用...")
        app = QApplication(sys.argv)
        
        # 高分屏适配
        if hasattr(Qt, 'AA_EnableHighDpiScaling'):
            QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
            QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
        # 设置应用程序信息
        app.setApplicationName(config.APP_NAME + " Pro")
        app.setApplicationVersion(config.APP_VERSION)
        
        # 创建并显示主窗口（样式表在窗口内部加载）
        window = MainWindowPro()
        window.show()
        
        logging.info("GUI界面已显示")
        
        # 进入事件循环
        sys.exit(app.exec_())
        
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

