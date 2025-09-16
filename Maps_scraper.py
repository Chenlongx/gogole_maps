
# 1. Python 标准库
import os
import sys
import csv
import re
import json
import asyncio
import platform
import uuid
import html
import time
import traceback
import base64
import chardet
import threading
import sqlite3
import random
from requests_html import HTMLSession
from fake_useragent import UserAgent
from urllib.parse import urljoin, urlparse, quote, parse_qs, unquote
from curl_cffi.requests import AsyncSession
from queue import Queue

# 2. 第三方库
import aiohttp
import requests
import pandas as pd
from bs4 import BeautifulSoup
from openpyxl.styles import Font
from playwright.async_api import async_playwright, Playwright, Browser

# 3. PyQt5 核心库 (已合并整理)
from PyQt5.QtCore import (QThread, pyqtSignal, QPoint, QSize, QThreadPool, pyqtSlot,
                          Qt, QUrl, QTimer, QPropertyAnimation, QEasingCurve, QRunnable,
                          QObject, QEvent, pyqtProperty)

from PyQt5.QtGui import (QIcon, QPixmap, QDesktopServices, QStandardItemModel,
                       QStandardItem, QCursor, QFontMetrics, QMovie, QColor, QPainter, QPen)

from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit,
                             QPushButton, QTableWidget, QTableWidgetItem, QLabel,
                             QFileDialog, QMessageBox, QComboBox, QDialog,
                             QGraphicsDropShadowEffect, QSizePolicy, QFrame,
                             QMenuBar, QAction, QCompleter, QListView, QCheckBox,
                             QFormLayout, QHeaderView, QProgressBar, QGroupBox, QRadioButton, QSlider, QSpinBox, QTabWidget,
                             QStackedLayout, QTabBar)
                             
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView, QWebEngineProfile, QWebEngineSettings, QWebEngineScript
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
from PyQt5.QtNetwork import QLocalServer, QLocalSocket, QNetworkAccessManager, QNetworkRequest



# 国家名称到两位ISO代码的映射字典 (更详尽版本)
COUNTRY_TO_CODE = {
    # 亚洲 (Asia)
    "中国": "CN", "日本": "JP", "韩国": "KR", "印度": "IN", "新加坡": "SG",
    "马来西亚": "MY", "泰国": "TH", "越南": "VN", "菲律宾": "PH", "印度尼西亚": "ID",
    "阿联酋": "AE", "沙特阿拉伯": "SA", "以色列": "IL", "土耳其": "TR", "卡塔尔": "QA",
    "巴基斯坦": "PK", "孟加ला国": "BD", "哈萨克斯坦": "KZ",

    # 欧洲 (Europe)
    "英国": "GB", "法国": "FR", "德国": "DE", "意大利": "IT", "西班牙": "ES",
    "俄罗斯": "RU", "荷兰": "NL", "瑞士": "CH", "瑞典": "SE", "挪威": "NO",
    "丹麦": "DK", "比利时": "BE", "奥地利": "AT", "爱尔兰": "IE", "葡萄牙": "PT",
    "波兰": "PL", "希腊": "GR", "芬兰": "FI", "捷克": "CZ", "匈牙利": "HU",

    # 北美洲 (North America)
    "美国": "US", "加拿大": "CA", "墨西哥": "MX",

    # 南美洲 (South America)
    "巴西": "BR", "阿根廷": "AR", "智利": "CL", "哥伦比亚": "CO", "秘鲁": "PE",

    # 大洋洲 (Oceania)
    "澳大利亚": "AU", "新西兰": "NZ",

    # 非洲 (Africa)
    "南非": "ZA", "埃及": "EG", "尼日利亚": "NG", "肯尼亚": "KE", "摩洛哥": "MA",
}



# 程序配置

CURRENT_APP_VERSION = "1.0.8" # 【重要】每次发布新版时，请更新此版本号
GITHUB_REPO_URL = "Chenlongx/gogole_maps" # 您的GitHub仓库路径 (格式: "用户名/仓库名")
GITHUB_API_PRIMARY = "https://api.github.com"
# 您可以选择一个稳定的镜像源，这里提供一个常用的作为示例
GITHUB_API_FALLBACK = "https://api.githubs.cn" 



def check_and_notify_dependencies():
    """
    检查关键依赖（如PyQt5）是否能加载。如果失败，则使用tkinter弹窗提示用户。
    这是为了处理因缺少VC++运行时库而导致的静默失败。
    """
    try:
        # 尝试导入PyQt5中最核心的模块，这是程序运行的先决条件
        from PyQt5.QtWidgets import QApplication
        # 如果导入成功，说明环境没问题，函数返回True
        return True
    except ImportError as e:
        # 如果导入失败，我们进入备用提示流程
        import tkinter as tk
        from tkinter import messagebox

        # 创建一个隐藏的tkinter根窗口，我们只需要它的弹窗功能
        root = tk.Tk()
        root.withdraw()

        # 准备给用户看的提示信息
        error_title = "缺少重要组件 (Missing Component)"
        error_message = (
            "应用程序启动失败！\n\n"
            "这很可能是因为您的系统缺少 'Microsoft Visual C++ Redistributable' 运行时库。\n\n"
            "请从微软官网搜索并安装【Visual C++ 2015-2022 Redistributable (x64)】后，再重新运行本程序。\n\n"
            "-------------------- English --------------------\n"
            "Application failed to start!\n\n"
            "This is likely because the 'Microsoft Visual C++ Redistributable' is missing on your system.\n\n"
            "Please search, download, and install 'Visual C++ 2015-2022 Redistributable (x64)' from the official Microsoft website, then run this application again."
        )

        # 使用tkinter的messagebox显示错误
        messagebox.showerror(error_title, error_message)
        
        # 销毁tkinter窗口并返回False，表示检查失败
        root.destroy()
        return False



def check_web_engine_component():
    """
    专门检查 QWebEngineView 核心浏览器组件是否能加载。
    这是比基础PyQt5检查更深层次的测试。
    """
    try:
        # 尝试导入最可能因为打包不完整而出错的模块
        from PyQt5.QtWebEngineWidgets import QWebEngineView
        
        # 为了更彻底地检查，我们甚至可以尝试创建一个虚拟实例
        # 注意：这需要一个 QApplication 实例，所以我们把它放在主逻辑块里
        # 暂时只检查导入，这已经能捕获99%的打包问题了。
        return True
    except ImportError as e:
        # 如果导入失败，说明打包不完整或环境有问题
        import tkinter as tk
        from tkinter import messagebox

        root = tk.Tk()
        root.withdraw()

        error_title = "缺少浏览器核心组件 (Browser Core Missing)"
        error_message = (
            "应用程序启动失败！\n\n"
            "无法加载内置的浏览器核心组件 (QWebEngineView)。\n\n"
            "这通常是由于以下原因造成的：\n"
            "1. 程序打包不完整，缺少了关键文件（如 QtWebEngineProcess.exe）。\n"
            "2. 杀毒软件错误地隔离了程序文件。\n\n"
            "请尝试将程序添加到杀毒软件的信任列表，或联系开发者获取完整的安装包。\n\n"
            "-------------------- English --------------------\n"
            "Application failed to start!\n\n"
            "Could not load the built-in browser core component (QWebEngineView).\n\n"
            "This is typically caused by:\n"
            "1. An incomplete application package missing critical files (e.g., QtWebEngineProcess.exe).\n"
            "2. Antivirus software has quarantined the program's files.\n\n"
            "Please try adding the application to your antivirus exclusion list or contact the developer for a complete package."
        )

        messagebox.showerror(error_title, error_message)
        
        root.destroy()
        return False



def get_performance_defaults():
    """
    【新增】检测系统性能 (CPU核心数和内存)，并返回推荐的并行设置。
    """
    defaults = {
        'parallel_tasks': 1,      # 默认值：1个地图采集页面
        'playwright_pool_size': 1 # 默认值：1个后台浏览器实例
    }
    
    try:
        import psutil # 尝试导入库
        
        cpu_cores = os.cpu_count() or 1
        total_ram_gb = psutil.virtual_memory().total / (1024**3) # 转换为GB
        
        print(f"💻 [性能检测] CPU核心数: {cpu_cores}, 总内存: {total_ram_gb:.2f} GB")
        
        # --- 推荐逻辑 ---
        
        # 【资源匹配修复】推荐后台浏览器 (Playwright) 的数量，与EmailWorker信号量匹配
        if total_ram_gb >= 12 and cpu_cores > 8:
            defaults['playwright_pool_size'] = 5 # 高性能：增加到5个页面，匹配EmailWorker需求
        elif total_ram_gb >= 6 and cpu_cores > 4:
            defaults['playwright_pool_size'] = 3 # 中等性能：保持3个页面
        else:
            defaults['playwright_pool_size'] = 2 # 低性能：至少2个页面避免阻塞
            
        # 2. 推荐地图采集页面 (QWebEngineView) 的数量 (相对较轻)
        if total_ram_gb < 6:
            defaults['parallel_tasks'] = 2 # 内存小于6G，最多开2个
        else:
            # 基本上是CPU核心数的一半，但最多不超过5个 (UI上限)
            defaults['parallel_tasks'] = min(5, max(1, cpu_cores // 2))

        print(f"  -> 根据性能，系统推荐设置 -> 地图页面: {defaults['parallel_tasks']}, Playwright实例: {defaults['playwright_pool_size']}")
        return defaults
        
    except (ImportError, Exception) as e:
        print(f"⚠️ [性能检测] 无法获取系统性能 ({e})，将使用最保守的默认设置。")
        # 如果 psutil 未安装或检测失败，返回最安全的值
        return defaults


def get_app_data_path(file_name):
    """获取应用程序数据目录中的文件路径，确保跨平台兼容"""
    # 应用程序的名称，用于创建专属文件夹
    APP_NAME = "GoogleMapsScraper"

    if sys.platform == "win32":
        # Windows: C:\Users\<Username>\AppData\Local\GoogleMapsScraper
        app_data_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", APP_NAME)
    elif sys.platform == "darwin":
        # macOS: ~/Library/Application Support/GoogleMapsScraper
        app_data_dir = os.path.join(os.path.expanduser("~"), "Library", "Application Support", APP_NAME)
    else: # Linux
        app_data_dir = os.path.join(os.path.expanduser("~"), ".config", APP_NAME)
    
    # 确保这个专属文件夹存在，如果不存在就创建它
    if not os.path.exists(app_data_dir):
        os.makedirs(app_data_dir)
    
    # 返回文件夹和文件名的完整路径
    return os.path.join(app_data_dir, file_name)



if getattr(sys, 'frozen', False):  # 判断是否在打包后的环境中运行
    try:
        # 确定应用程序的基础路径
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
        
        # 构造PyQt5核心库的路径
        qt_path = os.path.join(base_path, 'PyQt5', 'Qt5')
        
        if os.path.exists(qt_path):
            print(f"✅ [打包环境] 发现Qt核心路径: {qt_path}")
            
            # --- ▼▼▼ 【核心强化】开始 ▼▼▼ ---

            # 1. 准备好所有需要添加的路径
            qt_plugins_path = os.path.join(qt_path, 'plugins')
            qt_bin_path = os.path.join(qt_path, 'bin') # QtWebEngineProcess.exe 所在的路径
            
            # 2. 修改环境变量 (保留您原有的逻辑，作为通用后备方案)
            os.environ['QT_PLUGIN_PATH'] = qt_plugins_path
            if sys.platform == "win32":
                os.environ['PATH'] = qt_bin_path + os.pathsep + os.environ.get('PATH', '')
            
            # 3. 【最关键的一步】使用Qt的内置方法，在程序启动前直接添加库搜索路径
            #    这比修改环境变量更直接、更可靠。
            #    注意：这个导入和调用必须在 QApplication 实例创建之前。
            from PyQt5.QtCore import QCoreApplication
            QCoreApplication.addLibraryPath(qt_plugins_path)
            QCoreApplication.addLibraryPath(qt_bin_path)

            print(f"✅ [打包环境] 动态设置Qt环境变量并已通过内置方法添加核心库路径。")
            
            # --- ▲▲▲ 【核心强化】结束 ▲▲▲ ---

        else:
            print(f"⚠️ [打包环境] 警告: 未在预期位置找到Qt核心路径: {qt_path}")
            
    except Exception as e:
        print(f"❌ [打包环境] 动态设置Qt路径时发生严重错误: {e}")






class GenericSignals(QObject): # <--- 已重命名
    '''
    定义一个通用的信号类，可以从后台线程发射信号。
    '''
    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)



class GenericWorker(QRunnable): # <--- 已重命名
    '''
    一个通用的、可运行任何函数的QRunnable Worker。
    '''
    def __init__(self, fn, *args, **kwargs):
        super(GenericWorker, self).__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = GenericSignals() # <--- 使用重命名后的信号类

    @pyqtSlot()
    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
        except Exception as e:
            traceback.print_exc()
            exctype, value = sys.exc_info()[:2]
            self.signals.error.emit((exctype, value, traceback.format_exc()))
        else:
            self.signals.result.emit(result)
        finally:
            self.signals.finished.emit()



class WorkerSignals(QObject):
    """
    定义EmailFetcherWorker可以发出的所有信号。
    """
    # 信号格式: (找到的邮箱, 找到的官网URL, 表格行号)
    emailAndWebsiteFound = pyqtSignal(str, str, int)
    # 任务完成信号
    finished = pyqtSignal()



# (请用下面这个完整的类，替换掉您代码中旧的 class CircleOverlay)

class CircleOverlay(QWidget):
    """一个用于在父窗口上显示动态圆圈动画的透明叠加层。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)

        self._radius = 0
        self._opacity = 1.0
        self.center_pos = QPoint(0, 0)

        # --- 动画设置 (保持不变) ---
        self.radius_anim = QPropertyAnimation(self, b"circleRadius")
        self.radius_anim.setStartValue(0)
        self.radius_anim.setEndValue(150)
        self.radius_anim.setDuration(1200)
        self.radius_anim.setEasingCurve(QEasingCurve.OutQuad)

        self.opacity_anim = QPropertyAnimation(self, b"circleOpacity")
        self.opacity_anim.setStartValue(1.0)
        self.opacity_anim.setEndValue(0.0)
        self.opacity_anim.setDuration(1200)
        self.opacity_anim.setEasingCurve(QEasingCurve.InQuad)
        
        self.opacity_anim.finished.connect(self.hide)

    # --- 属性定义 (保持不变) ---
    @pyqtProperty(int)
    def circleRadius(self):
        return self._radius

    @circleRadius.setter
    def circleRadius(self, value):
        self._radius = value
        self.update()

    @pyqtProperty(float)
    def circleOpacity(self):
        return self._opacity

    @circleOpacity.setter
    def circleOpacity(self, value):
        self._opacity = value
        self.update()

    # --- 核心修改点 1: 修改绘图颜色 ---
    def paintEvent(self, event):
        """这是所有绘图操作发生的地方"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # --- ▼▼▼ 【颜色修复】将颜色从蓝色 (66, 133, 244) 修改为红色 (220, 53, 69) ▼▼▼ ---
        pen_color = QColor(220, 53, 69, int(self._opacity * 255)) # 使用醒目的红色
        # --- ▲▲▲ 修复结束 ▲▲▲ ---
        
        pen = QPen(pen_color, 3)
        painter.setPen(pen)
        
        painter.setBrush(Qt.NoBrush)
        
        painter.drawEllipse(self.center_pos, self._radius, self._radius)

    # --- 核心修改点 2: 移除位置偏移 ---
    def start_animation(self, center_pos):
        """外部调用的入口：在指定位置开始动画"""
        
        # --- ▼▼▼ 【位置修复】移除固定的偏移量，直接使用传入的 center_pos ▼▼▼ ---
        # 旧代码:
        # original_x = center_pos.x()
        # original_y = center_pos.y()
        # offset_pos = QPoint(original_x + 300, original_y - 150)
        # self.center_pos = offset_pos
        
        # 新代码 (正确):
        self.center_pos = center_pos
        # --- ▲▲▲ 修复结束 ▲▲▲ ---

        self.raise_()
        self.show()
        self.radius_anim.start()
        self.opacity_anim.start()




# (请用下面的整个类，替换掉您代码中旧的 class RegisterDialog)

class RegisterDialog(QDialog):
    def __init__(self, parent=None, device_id=None):
        super().__init__(parent)
        self.device_id = device_id

        self.registered_email = None
        self.registered_password = None
        self.registered_device_id = None

        self.setWindowTitle("创建新账号")
        # 优化尺寸，使其更适合新布局
        self.setFixedSize(420, 580) 
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint) # 设置为无边框

        # --- 整体布局与样式优化 ---
        # 1. 使用更现代、更柔和的样式表
        # 2. 区分主操作按钮（注册）和次要按钮（返回）的样式
        # 3. 为输入框添加更清晰的焦点效果
        self.setStyleSheet("""
            QDialog#mainDialog {
                background-color: #f4f6f9; /* 使用柔和的浅灰色背景 */
                border-radius: 8px;
            }
            /* 标题样式 */
            QLabel#titleLabel {
                font-size: 24px;
                font-weight: bold;
                color: #333;
                padding-top: 10px;
                padding-bottom: 20px;
            }
            /* 表单标签样式 */
            QLabel {
                font-size: 14px;
                font-weight: 500;
                color: #555;
            }
            QLineEdit {
                padding: 11px 15px;
                border: 1px solid #dcdcdc;
                border-radius: 5px;
                font-size: 14px;
                background-color: #ffffff;
            }
            QLineEdit:focus {
                border: 1px solid #4a90e2; /* 蓝色焦点边框 */
                box-shadow: 0 0 5px rgba(74, 144, 226, 0.5);
            }
            /* 主要操作按钮（注册） */
            QPushButton#registerButton {
                background-color: #4a90e2;
                color: white;
                padding: 12px;
                border-radius: 5px;
                font-size: 16px;
                font-weight: bold;
                border: none;
            }
            QPushButton#registerButton:hover {
                background-color: #357ABD;
            }
            /* 次要/文字按钮 */
            QPushButton {
                background-color: transparent;
                border: none;
                color: #4a90e2;
                font-size: 14px;
                text-decoration: none;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
            /* 发送验证码按钮的特殊样式 */
            QPushButton#sendOtpButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton#sendOtpButton:disabled {
                background-color: #e8e8e8;
                color: #999;
            }
        """)

        # --- 使用更合理的布局嵌套 ---
        self.setObjectName("mainDialog") # 为主对话框设置对象名以应用样式
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0) # 外部无边距
        
        # 自定义标题栏 (用于拖动和关闭)
        # 您可以复用之前的 CustomTitleBar 或创建一个简化的
        title_bar = QWidget(self)
        title_bar.setFixedHeight(40)
        title_bar_layout = QHBoxLayout(title_bar)
        title_bar_layout.addStretch()
        close_button = QPushButton("✕")
        close_button.setFixedSize(30, 30)
        close_button.setStyleSheet("border:none; font-size: 20px; color: #888;")
        close_button.clicked.connect(self.reject) # 关闭对话框
        title_bar_layout.addWidget(close_button)
        main_layout.addWidget(title_bar)
        
        self.draggable = True
        self.drag_pos = QPoint(0,0)

        def mousePressEvent(event):
            if event.button() == Qt.LeftButton:
                self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()
        def mouseMoveEvent(event):
            if event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.drag_pos)
                event.accept()

        title_bar.mousePressEvent = mousePressEvent
        title_bar.mouseMoveEvent = mouseMoveEvent

        # --- 表单内容容器 ---
        form_container = QWidget()
        container_layout = QVBoxLayout(form_container)
        container_layout.setContentsMargins(40, 0, 40, 40) # 设置舒适的内边距
        container_layout.setSpacing(18) # 增加控件垂直间距

        # 1. 增加一个醒目的标题
        title_label = QLabel("创建您的专属账号")
        title_label.setObjectName("titleLabel")
        title_label.setAlignment(Qt.AlignCenter)
        container_layout.addWidget(title_label)

        # 2. 使用 QFormLayout 替代 QVBoxLayout 来创建清晰的标签-输入框对
        #    这会自动将标签和输入框对齐，是专业表单设计的首选
        form_layout = QFormLayout()
        form_layout.setRowWrapPolicy(QFormLayout.WrapAllRows) # 确保在小屏幕上也能正常显示
        form_layout.setVerticalSpacing(15) # 行间距
        form_layout.setLabelAlignment(Qt.AlignLeft) # 标签左对齐

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("例如: yourname@example.com")
        form_layout.addRow(QLabel("邮箱地址:"), self.email_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("至少8位，建议包含字母和数字")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("设置密码:"), self.password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("请再次输入您的密码")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow(QLabel("确认密码:"), self.confirm_password_input)

        # 3. 将 QFormLayout 添加到容器中
        container_layout.addLayout(form_layout)

        # 4. 验证码部分保持水平布局，但样式统一
        code_layout = QHBoxLayout()
        self.otp_input = QLineEdit()
        self.otp_input.setPlaceholderText("6位验证码")
        self.send_otp_button = QPushButton("获取验证码")
        self.send_otp_button.setObjectName("sendOtpButton")
        self.send_otp_button.setCursor(Qt.PointingHandCursor)
        code_layout.addWidget(self.otp_input)
        code_layout.addWidget(self.send_otp_button)
        container_layout.addLayout(code_layout)

        # 5. 添加弹性空间，将按钮推向底部
        container_layout.addStretch()

        # 6. 放置操作按钮
        self.register_button = QPushButton("立即注册")
        self.register_button.setObjectName("registerButton") # 设置对象名以应用特殊样式
        self.register_button.setCursor(Qt.PointingHandCursor)
        container_layout.addWidget(self.register_button)
        
        self.back_to_login_button = QPushButton("已有账号？返回登录")
        self.back_to_login_button.setCursor(Qt.PointingHandCursor)
        container_layout.addWidget(self.back_to_login_button, alignment=Qt.AlignCenter)
        
        main_layout.addWidget(form_container)

        # 连接信号 (这部分逻辑不变)
        self.send_otp_button.clicked.connect(self.send_otp)
        self.register_button.clicked.connect(self.register_user)
        self.back_to_login_button.clicked.connect(self.accept)

        # 用于倒计时的定时器 (逻辑不变)
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown = 0

    # (send_otp, update_countdown, register_user 这三个方法不需要修改，保持原样即可)
    def send_otp(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "错误", "请输入邮箱地址！")
            return
            
        url = "https://mediamingle.cn/.netlify/functions/send-signup-otp"
        self.send_otp_button.setEnabled(False)
        self.send_otp_button.setText("发送中...")

        try:
            response = requests.post(url, json={"email": email}, timeout=15)
            data = response.json()

            if response.status_code == 200 and data.get("success"):
                QMessageBox.information(self, "成功", data.get("message", "验证码已发送"))
                self.countdown = 60
                self.update_countdown()
                self.countdown_timer.start(1000)
            else:
                QMessageBox.warning(self, "发送失败", data.get("message", "发送失败，请稍后再试"))
                self.send_otp_button.setEnabled(True)
                self.send_otp_button.setText("获取验证码")

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "网络错误", f"请求失败: {e}")
            self.send_otp_button.setEnabled(True)
            self.send_otp_button.setText("获取验证码")

    def update_countdown(self):
        if self.countdown > 0:
            self.send_otp_button.setText(f"{self.countdown}秒后重试")
            self.countdown -= 1
        else:
            self.countdown_timer.stop()
            self.send_otp_button.setEnabled(True)
            self.send_otp_button.setText("获取验证码")

    # (在 RegisterDialog 类中，用这个新方法替换旧的 register_user)
    def register_user(self):
        email = self.email_input.text().strip()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        token = self.otp_input.text().strip()

        # --- 后续的验证逻辑保持不变 ---
        if not email:
            QMessageBox.warning(self, "错误", "请输入邮箱地址！")
            return
        if not password:
            QMessageBox.warning(self, "错误", "请输入密码！")
            return
        if not confirm_password:
            QMessageBox.warning(self, "错误", "请再次输入密码进行确认！")
            return
        if not token:
            QMessageBox.warning(self, "错误", "请输入您邮箱中收到的6位验证码！")
            return

        if password != confirm_password:
            QMessageBox.warning(self, "错误", "两次输入的密码不一致！")
            return
        
        if not self.device_id:
            QMessageBox.critical(self, "致命错误", "无法获取设备ID，请重启程序。")
            return
        
        def get_os_type():
            os_name = platform.system()
            if os_name == "Windows": return "Windows"
            if os_name == "Darwin": return "macOS"
            if os_name == "Linux": return "Linux"
            return "Unknown"

        payload = {
            "email": email, 
            "password": password, 
            "token": token,
            "device_id": self.device_id,
            "os_type": get_os_type()
        }

        url = "https://mediamingle.cn/.netlify/functions/verify-and-register"
        self.register_button.setEnabled(False)
        self.register_button.setText("注册中...")

        try:
            response = requests.post(url, json=payload, timeout=15)
            data = response.json()

            if response.status_code == 201 and data.get("success"):
                self.registered_email = email
                self.registered_password = password
                self.registered_device_id = self.device_id

                QMessageBox.information(self, "注册成功", data.get("message", "注册成功！"))
                self.accept()
            else:
                QMessageBox.warning(self, "注册失败", data.get("message", "注册失败，请检查您的信息"))
                self.register_button.setEnabled(True)
                self.register_button.setText("立即注册")

        except requests.exceptions.RequestException as e:
            QMessageBox.critical(self, "网络错误", f"请求失败: {e}")
            self.register_button.setEnabled(True)
            self.register_button.setText("立即注册")





# (请用下面这个【【【完整的类】】】替换掉您代码中旧的 class EmailFetcherWorker)

class EmailFetcherWorker:
    """
    【速度与深度最终重构版】
    - 采用并行网络请求(asyncio.gather)大幅提升速度。
    - 严格限制Playwright的使用场景，仅在快速方法失败后介入。
    - 采集网站所有高价值页面的全部邮箱，而非找到一个就停止。
    """
    URL_BLOCKLIST = {
        'google.com/recaptcha', 'googletagmanager.com', 'google-analytics.com', 'doubleclick.net',
        'facebook.net', 'fbcdn.net', 'twitter.com/widgets.js', 'maps.googleapis.com',
        'maps.google.com'
    }

    BROWSER_PROFILES = {
        "chrome124_win": {
            "impersonate": "chrome124",
            "headers": {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'accept-language': 'en-US,en;q=0.9',
                'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Windows"',
                'sec-fetch-dest': 'document',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-site': 'none',
                'sec-fetch-user': '?1',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            }
        },
        "safari17_mac": {
            "impersonate": "safari17_0",
            "headers": {
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'accept-language': 'en-US,en;q=0.9',
                'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
            }
        }
    }

    class WorkerSignals(QObject):
        resultFound = pyqtSignal(dict, int)
        finished = pyqtSignal()

    def __init__(self, website, company_name, address, phone, row, playwright_manager, country, social_platforms_to_scrape, whatsapp_validation_mode, whatsapp_manager, is_speed_mode=False, collect_all_emails_mode=False, extreme_deep_scan_mode=False, enable_playwright_fallback=True, global_semaphore=None):
        # super().__init__()
        # --- 参数初始化 (保持不变) ---
        self.website = website
        self.company_name = company_name
        self.address = address
        self.phone = phone
        self.row = row
        self.playwright_manager = playwright_manager
        self.country = country
        self.is_speed_mode = is_speed_mode
        self.collect_all_emails_mode = collect_all_emails_mode
        self.extreme_deep_scan_mode = extreme_deep_scan_mode
        self.social_platforms_to_scrape = social_platforms_to_scrape
        self.whatsapp_validation_mode = whatsapp_validation_mode
        self.whatsapp_manager = whatsapp_manager
        self.enable_playwright_fallback = enable_playwright_fallback

        self.global_semaphore = global_semaphore # 保存从外部传入的全局总闸

        self.found_social_links = {p: None for p in ['facebook', 'instagram', 'linkedin', 'whatsapp']}

        self.profile_key = random.choice(list(self.BROWSER_PROFILES.keys()))
        self.browser_profile = self.BROWSER_PROFILES[self.profile_key]
        print(f"  -> Worker for '{self.company_name}' 已激活伪装身份: {self.profile_key}")


        self.initial_domain = urlparse(self.website).netloc if self.website else ""
        # self.signals = self.WorkerSignals()
        self.email_pattern = r"\b[a-zA-Z0-9._%+-]*[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+\b"
        self.excluded_domains = {"hotmail.com", "o405442.ingest.sentry.io"}
        self.temp_domains = {"tempmail.com", "mailinator.com", "guerrillamail.com"}
        self.HIGH_PRIORITY_KEYWORDS = [
            'contact', 'contact-us', 'contactus', 'get-in-touch', 'support',
            'about', 'about-us', 'team', 'staff', 'imprint', 'impressum', 'kontakt'
        ]
        self.LOW_PRIORITY_KEYWORDS = [
            'login', 'register', 'signin', 'signup', 'cart', 'checkout',
            'terms', 'privacy', 'legal', 'policy', 'sitemap', 'faq', 'blog', 
            'news', 'events', 'portfolio', 'gallery', 'projects', 'javascript:', 
            'tel:', 'mailto:', '.pdf', '.zip', '.jpg', '.png'
        ]
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'

    # --- 网络请求核心 (fetch_page, _fetch_with_requests_html_sync 保持不变) ---

    async def fetch_page(self, url, session, timeout=15):
        """
        【智能升级最终修复版】
        - 默认使用快速的 curl_cffi 尝试访问。
        - 如果且仅当收到 403/406 等反爬虫错误时，才自动、无条件地升级到 Playwright 进行强力突破。
        - 这将从根本上避免因低效的“Bing搜索兜底”策略被并发触发而导致的程序无响应。
        """
        # 1. 黑名单和请求头准备 (逻辑不变)
        if any(blocked_domain in url for blocked_domain in self.URL_BLOCKLIST):
            print(f"🚫 URL命中黑名单，已跳过: {url}")
            return None
        
        try:
            base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
        except Exception:
            base_url = url
            
        dynamic_headers = self.browser_profile["headers"].copy()
        dynamic_headers['referer'] = base_url
        
        # --- ▼▼▼ 【核心修复】在这里实现智能升级和重试逻辑 ▼▼▼ ---
        max_retries = 2
        for attempt in range(max_retries):
            try:
                # a. 第一次尝试 (或重试): 使用 curl_cffi (常规武器)
                response = await session.get(url, timeout=timeout, headers=dynamic_headers)
                
                # b. 成功获取响应，解码并返回
                if response.status_code == 200:
                    detected_encoding = chardet.detect(response.content)['encoding']
                    return response.content.decode(detected_encoding if detected_encoding else 'utf-8', errors='ignore')

                # c. 【关键修复】如果收到的是客户端错误（特别是403/406），则立即智能升级
                if 400 <= response.status_code < 500:
                    print(f"⚠️ curl_cffi 收到 HTTP {response.status_code} ({url})。自动升级至 Playwright 尝试直接绕过。")
                    
                    # d. 第二次尝试：使用 Playwright (终极武器)
                    if self.playwright_manager and self.playwright_manager.is_available():
                        # 这个函数会启动一个完整的后台浏览器来访问，成功率极高
                        return await self.playwright_manager.get_page_content(url)
                    else:
                        print("  -> Playwright 不可用，无法升级。")
                        return None # Playwright不可用，直接失败
                
                # e. 对于其他HTTP错误 (如服务器5xx错误)，直接失败
                print(f"❌ curl_cffi 获取页面失败 ({url}): HTTP {response.status_code}，不再重试。")
                return None

            except (aiohttp.client_exceptions.ClientConnectorError, asyncio.TimeoutError, Exception) as e:
                # f. 捕获网络层面的错误 (超时, 连接失败等)
                print(f"❌ curl_cffi 无法获取页面 ({url}): {type(e).__name__} (尝试 {attempt + 1}/{max_retries})")
                if attempt + 1 == max_retries:
                    print(f"  -> 已达到最大重试次数，快速失败。")
                    return None
                await asyncio.sleep(2) # 等待2秒再重试
        # --- ▲▲▲ 修复结束 ▲▲▲ ---
        
        return None # 理论上不会执行到这里

    # async def fetch_page(self, url, session, timeout=15):
    #     """
    #     【智能降级最终修复版】
    #     - 默认使用快速的 curl_cffi 尝试访问。
    #     - 如果且仅当收到 4xx/5xx (特别是 403) 这类反爬虫错误时，才自动降级到 Playwright 进行强力突破。
    #     - 对于常规网络错误（如超时），则继续快速失败，以保证程序整体效率和稳定性。
    #     """
    #     # 1. 黑名单和请求头准备 (逻辑不变)
    #     if any(blocked_domain in url for blocked_domain in self.URL_BLOCKLIST):
    #         print(f"🚫 URL命中黑名单，已跳过: {url}")
    #         return None
        
    #     try:
    #         base_url = f"{urlparse(url).scheme}://{urlparse(url).netloc}"
    #     except Exception:
    #         base_url = url
    #     enhanced_headers = {'User-Agent': self.user_agent, 'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8', 'Accept-Language': 'en-US,en;q=0.9', 'Accept-Encoding': 'gzip, deflate, br', 'Referer': base_url}
        
    #     # --- ▼▼▼ 【核心修复】在这里实现智能降级逻辑 ▼▼▼ ---

    #     # 2. 第一次尝试：使用 curl_cffi (常规武器)
    #     try:
    #         response = await session.get(url, timeout=timeout, headers=enhanced_headers)
    #         if response.status_code == 200:
    #             return response.text # 成功，直接返回网页内容
            
    #         # --- 3. 智能失败分析 ---
    #         # 如果是 4xx (客户端错误) 或 5xx (服务器错误)，特别是 403，就值得用 Playwright 尝试
    #         if 400 <= response.status_code < 600:
    #             print(f"⚠️ curl_cffi 收到 HTTP {response.status_code} ({url})。准备降级至 Playwright 尝试绕过。")
                
    #             # 4. 第二次尝试：使用 Playwright (终极武器)
    #             if self.playwright_manager and self.playwright_manager.is_available():
    #                 # 这个函数会启动一个完整的后台浏览器来访问，成功率极高
    #                 return await self.playwright_manager.get_page_content(url)
    #             else:
    #                 print("  -> Playwright 不可用，无法降级。")
    #                 return None
    #         else:
    #             # 对于其他状态码 (例如 3xx 重定向)，直接失败
    #             print(f"❌ curl_cffi 获取页面失败 ({url}): HTTP {response.status_code}，快速失败。")
    #             return None

    #     except Exception as e:
    #         # 对于网络层面的错误 (Timeout, ConnectionError)，我们仍然快速失败，
    #         # 因为 Playwright 也可能遇到同样问题，没必要降级。
    #         print(f"❌ curl_cffi 无法获取页面 ({url}): {type(e).__name__}，快速失败。")
    #         return None
    #     # --- ▲▲▲ 修复结束 ▲▲▲ ---



    async def _preflight_check_links(self, urls, session):
        """
        【性能优化版】使用HEAD请求对一组URL进行并行预检，并增加了对URL数量的硬性限制。
        """
        # ▼▼▼ 【核心修复】在这里添加一个硬性上限 ▼▼▼
        MAX_PREFLIGHT_URLS = 40 # 无论找到多少链接，一次最多只预检40个
        if len(urls) > MAX_PREFLIGHT_URLS:
            print(f"  -> 发现 {len(urls)} 个候选链接，为保证性能，仅预检前 {MAX_PREFLIGHT_URLS} 个。")
            urls = urls[:MAX_PREFLIGHT_URLS]
        # --- ▲▲▲ 优化代码添加完毕 ▲▲▲ ---

        async def check(url):
            """【修复版】确保 session.head 被显式 await，避免协程挂起"""
            response = None 
            try:
                response = await session.head(url, timeout=8, allow_redirects=True)
                content_type = response.headers.get('Content-Type', '').lower()
                if response.status_code == 200 and 'text/html' in content_type:
                    final_domain = urlparse(str(response.url)).netloc
                    if self.initial_domain in final_domain:
                        return url
            except Exception:
                pass
            finally:
                if response:
                    pass
            return None

        # 这里的 urls 已经是被“剪枝”过的版本了
        tasks = [check(url) for url in urls]
        results = await asyncio.gather(*tasks)

        valid_urls = [url for url in results if url]
        print(f"  -> 预检完成: {len(urls)} 个链接中，{len(valid_urls)} 个为有效HTML页面。")
        return valid_urls




    def _fetch_with_requests_html_sync(self, url, timeout=15):
        print(f"🔄 aiohttp 失败，正在切换至 requests-html 模式重试: {url}")
        try:
            session = HTMLSession()
            response = session.get(url, timeout=timeout, headers={'User-Agent': self.user_agent})
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ requests-html 模式请求失败 ({url}): {e}")
            return None
            
    # --- 邮件与链接提取 (大部分保持不变) ---
    def _check_and_store_social_link(self, url):
        # (此方法代码保持不变)
        if not url or url.strip().lower().startswith('javascript:'): return
        url_lower = url.lower()
        platforms = {'whatsapp': ['wa.me/', 'api.whatsapp.com'], 'facebook': 'facebook.com/', 'instagram': 'instagram.com/', 'linkedin': 'linkedin.com/'}
        for platform, keywords in platforms.items():
            if platform == 'whatsapp':
                existing_wa = self.found_social_links.get('whatsapp')
                if existing_wa and existing_wa.isdigit(): continue
            elif self.found_social_links.get(platform): continue
            if not self.social_platforms_to_scrape.get(platform): continue
            is_match = False
            keyword_list = keywords if isinstance(keywords, list) else [keywords]
            if any(keyword in url_lower for keyword in keyword_list): is_match = True
            if is_match:
                if platform == 'whatsapp':
                    phone_number = None
                    try:
                        if 'wa.me/' in url_lower: phone_number = url.split('wa.me/')[-1].split('/')[0].split('?')[0]
                        elif 'api.whatsapp.com' in url_lower:
                            query_params = parse_qs(urlparse(url).query)
                            if 'phone' in query_params: phone_number = query_params['phone'][0]
                        if phone_number:
                            cleaned_number = re.sub(r'\D', '', phone_number)
                            if cleaned_number: self.found_social_links[platform] = cleaned_number
                        else: self.found_social_links[platform] = url.split('#')[0].rstrip('/')
                    except Exception: self.found_social_links[platform] = url.split('#')[0].rstrip('/')
                else: self.found_social_links[platform] = url.split('#')[0].rstrip('/')
    
    async def extract_emails(self, text, source_url):
        """【优化版】优先使用正则直接提取，减少不必要的Soup解析"""
        
        # 1. 先用正则直接在原始文本上扫一遍，速度最快
        emails = re.findall(self.email_pattern, text)
        
        # 2. 对HTML进行反混淆和解码，再用正则扫一遍，捕获被隐藏的邮箱
        clean_text = deobfuscate_text(text)
        emails.extend(re.findall(self.email_pattern, clean_text))
        
        # 3. 最后才用Soup提取纯文本，作为补充
        try:
            soup = BeautifulSoup(clean_text, 'html.parser')
            normalized_text = ' '.join(soup.get_text(separator=' ').split())
            emails.extend(re.findall(self.email_pattern, normalized_text))
        except Exception:
            pass # soup解析可能失败，但不影响前面已找到的结果

        # 统一去重和过滤
        unique_emails = list(dict.fromkeys(emails))
        filtered_emails = self.filter_emails(unique_emails)
        
        page_has_phone = self.phone and (re.sub(r'\D', '', self.phone) in re.sub(r'\D', '', clean_text))
        return [(email, source_url, page_has_phone) for email in filtered_emails]
        
    def filter_emails(self, emails):
        BLOCKED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css', '.json', '.xml', '.woff', '.woff2', '.ttf', '.otf', '.eot'}
        BLOCKED_DOMAIN_KEYWORDS = {'sentry', 'wixpress'}

        filtered = []
        for email in emails:
            # 1. 基础格式和后缀名过滤 (保留不变)
            if any(email.lower().endswith(ext) for ext in BLOCKED_EXTENSIONS): continue
            if "@" not in email: continue
            
            local_part, domain = email.split("@", 1)
            domain = domain.lower()

            # 2. 域名关键词黑名单过滤 (上次的修复，保留)
            if any(keyword in domain for keyword in BLOCKED_DOMAIN_KEYWORDS):
                print(f"🚫 邮箱 {email} 因域名命中关键词黑名单而被过滤。")
                continue 

            # --- ▼▼▼ 【核心新增】随机长字符前缀过滤 ▼▼▼ ---
            # 3. 如果邮箱前缀长度超过20个字符...
            if len(local_part) > 20:
                # ...并且前缀只包含十六进制字符 (0-9, a-f)...
                # re.fullmatch 会确保整个字符串都符合这个模式
                import re
                if re.fullmatch(r'[0-9a-f]+', local_part, re.IGNORECASE):
                    # ...那么我们就认为它是一个机器生成的ID，予以过滤。
                    print(f"🚫 邮箱 {email} 因前缀疑似随机长字符而被过滤。")
                    continue
            # --- ▲▲▲ 新增结束 ▲▲▲ ---

            # 4. 其他原有的过滤规则 (保留不变)
            if domain in self.excluded_domains or domain in self.temp_domains: continue
            if self.country != "China" and (domain.endswith('.cn') or domain == '163.com'): continue
            
            letters = sum(c.isalpha() for c in local_part)
            if letters < 2 or (letters / len(local_part) < 0.4): continue
            
            filtered.append(email)
            
        return filtered

    # --- 【核心重构】并行爬取方法 ---
    # async def crawl_subpages(self, base_url, session):
    #     """
    #     【双模式重构版】
    #     - 增加了对 mailto 链接的提取。
    #     - 增加了对“极限深度扫描”模式的支持。
    #     """
    #     all_emails = []
    #     homepage_text = await self.fetch_page(base_url, session)
    #     if not homepage_text: return []

    #     emails_from_home = await self.extract_emails(homepage_text, base_url)
    #     if emails_from_home: all_emails.extend(emails_from_home)
        
    #     soup = BeautifulSoup(homepage_text, 'html.parser')
    #     links = soup.find_all('a', href=True)
    #     sub_urls_to_visit = set()
    #     visited = {base_url}

    #     for link in links:
    #         href = link.get('href', '').strip()

    #         # 1. 提取 mailto 邮箱 (我们上面添加的逻辑)
    #         if href.lower().startswith('mailto:'):
    #             email_match = re.search(self.email_pattern, href)
    #             if email_match:
    #                 email = email_match.group(0)
    #                 if self.filter_emails([email]):
    #                     all_emails.append((email, base_url, False))
    #                     print(f"✅ (mailto) 发现并提取了隐藏邮箱: {email}")
            
    #         # 2. 检查社交链接
    #         self._check_and_store_social_link(href)

    #         # 3. 根据模式筛选要访问的子页面
    #         if any(keyword in href.lower() for keyword in self.LOW_PRIORITY_KEYWORDS): continue
    #         absolute_url = urljoin(base_url, href)
    #         if not absolute_url.startswith(('http://', 'https://')): continue
    #         if urlparse(absolute_url).netloc == urlparse(base_url).netloc and absolute_url not in visited:
                
    #             # --- ▼▼▼ 【核心逻辑修改】 ▼▼▼ ---
    #             if self.extreme_deep_scan_mode:
    #                 # 极限模式：只要是同站链接，就加入待访问列表
    #                 sub_urls_to_visit.add(absolute_url)
    #             else:
    #                 # 普通模式：只访问包含高价值关键词的链接
    #                 link_text = link.get_text(strip=True).lower()
    #                 if any(kw in absolute_url.lower() for kw in self.HIGH_PRIORITY_KEYWORDS) or \
    #                    any(kw in link_text for kw in self.HIGH_PRIORITY_KEYWORDS):
    #                     sub_urls_to_visit.add(absolute_url)
    #             # --- ▲▲▲ 修改结束 ▲▲▲ ---

    #     if sub_urls_to_visit:
    #         # 根据模式设置不同的子页面访问上限
    #         # 1. 在真正下载前，先对所有候选链接进行并行预检
    #         urls_to_process = await self._preflight_check_links(list(sub_urls_to_visit), session)

    #         limit = 20 if self.extreme_deep_scan_mode else (3 if self.is_speed_mode else 5)
    #         # 【修改】我们现在只从“通过预检的”链接中选择
    #         urls_to_process = urls_to_process[:limit]
            
    #         if urls_to_process:
    #             print(f"  -> 智能筛选出 {len(urls_to_process)} 个链接进行并行抓取 (模式: {'极限' if self.extreme_deep_scan_mode else '常规'})...")
                
    #             async def fetch_and_extract(url):
    #                 page_text = await self.fetch_page(url, session)
    #                 if page_text: return await self.extract_emails(page_text, url)
    #                 return []

    #             tasks = [fetch_and_extract(url) for url in urls_to_process]
    #             results = await asyncio.gather(*tasks)
                
    #             for email_list in results:
    #                 if email_list: all_emails.extend(email_list)
        
    #     return all_emails

    # (在 EmailFetcherWorker 类中)

    async def crawl_subpages(self, base_url, session):
        """
        【最终限流修复版】
        - 增加了 asyncio.Semaphore 来限制深度扫描时的最大并发网络请求数量。
        - 从根本上解决了因“极限深度扫描”模式在不稳定网络下导致的资源耗尽和程序无响应问题。
        """
        all_emails = []
        homepage_text = await self.fetch_page(base_url, session)
        if not homepage_text: return []

        emails_from_home = await self.extract_emails(homepage_text, base_url)
        if emails_from_home: all_emails.extend(emails_from_home)
        
        soup = BeautifulSoup(homepage_text, 'html.parser')
        links = soup.find_all('a', href=True)
        sub_urls_to_visit = set()
        visited = {base_url}

        for link in links:
            # (这部分提取 mailto 和社交链接的逻辑保持不变)
            href = link.get('href', '').strip()
            if href.lower().startswith('mailto:'):
                email_match = re.search(self.email_pattern, href)
                if email_match:
                    email = email_match.group(0)
                    if self.filter_emails([email]):
                        all_emails.append((email, base_url, False))
                        print(f"✅ (mailto) 发现并提取了隐藏邮箱: {email}")
            self._check_and_store_social_link(href)
            
            # (这部分筛选子页面的逻辑也保持不变)
            if any(keyword in href.lower() for keyword in self.LOW_PRIORITY_KEYWORDS): continue
            absolute_url = urljoin(base_url, href)
            if not absolute_url.startswith(('http://', 'https://')): continue
            if urlparse(absolute_url).netloc == urlparse(base_url).netloc and absolute_url not in visited:
                if self.extreme_deep_scan_mode:
                    sub_urls_to_visit.add(absolute_url)
                else:
                    link_text = link.get_text(strip=True).lower()
                    if any(kw in absolute_url.lower() for kw in self.HIGH_PRIORITY_KEYWORDS) or \
                    any(kw in link_text for kw in self.HIGH_PRIORITY_KEYWORDS):
                        sub_urls_to_visit.add(absolute_url)

        if sub_urls_to_visit:
            urls_to_process = await self._preflight_check_links(list(sub_urls_to_visit), session)
            limit = 20 if self.extreme_deep_scan_mode else (3 if self.is_speed_mode else 5)
            urls_to_process = urls_to_process[:limit]
            
            if urls_to_process:
                print(f"  -> 智能筛选出 {len(urls_to_process)} 个链接进行并行抓取 (模式: {'极限' if self.extreme_deep_scan_mode else '常规'})...")
                
                # --- ▼▼▼ 【核心架构修复】在这里增加“限流阀” ▼▼▼ ---
                
                # 1. 创建一个信号量，我们设定一个合理值，比如允许最多同时有 5 个网络请求在运行。
                semaphore = self.global_semaphore if self.global_semaphore else asyncio.Semaphore(5)

                async def fetch_and_extract_throttled(url):
                    # 2. 在每个任务开始执行核心操作前，必须先“获取”一个信号量（通行证）。
                    #    如果通行证已发完，任务会在这里安全地异步等待，不会阻塞程序。
                    async with semaphore:
                        # 只有在获得“通行许可”后，才执行真正的耗时操作
                        page_text = await self.fetch_page(url, session)
                        if page_text: 
                            return await self.extract_emails(page_text, url)
                        return []

                # 3. 将我们的任务列表，全部指向这个带有限流器的新函数。
                #    asyncio.gather 仍然会一次性启动所有任务，但由于限流器的存在，
                #    实际上只有5个任务能同时进入工作状态。
                tasks = [fetch_and_extract_throttled(url) for url in urls_to_process]
                results = await asyncio.gather(*tasks)

                # --- ▲▲▲ 修复结束 ▲▲▲ ---
                
                for email_list in results:
                    if email_list: all_emails.extend(email_list)
        
        return all_emails
    
    # --- 评分与兜底搜索 (保持不变) ---
    def score_email(self, email, source_url, was_on_page_with_phone):
        # (此方法代码保持不变)
        score = 0
        try:
            local_part, domain = email.lower().split('@')
            website_domain = urlparse(self.website).netloc.replace('www.', '')
        except ValueError: return -999
        if was_on_page_with_phone: score += 100
        if domain == website_domain: score += 50
        elif website_domain in domain: score += 20
        good_keywords = ['info', 'contact', 'sales', 'support', 'hello', 'admin', 'service', 'enquiries', 'office', 'お問い合わせ']
        if any(keyword in local_part for keyword in good_keywords): score += 30
        if any(path_keyword in source_url.lower() for path_keyword in self.HIGH_PRIORITY_KEYWORDS): score += 20
        bad_keywords = ['noreply', 'privacy', 'abuse', 'no-reply', 'unsubscribe']
        if any(keyword in local_part for keyword in bad_keywords): score -= 60
        if any(k in email for k in ['example', 'test', 'spam', 'yourdomain', 'sentry.io']): return -999
        return score
    
    async def search_domain_specific_email(self, session):
        """【改造版】返回所有找到的邮箱列表"""
        if not self.playwright_manager or not self.playwright_manager.is_available(): return None
        try:
            domain = urlparse(self.website).netloc.replace('www.', '')
            if not domain: return None
        except Exception: return None

        query = f'site:{domain} "@{domain}"'
        search_url = f"https://www.bing.com/search?q={quote(query)}"
        try:
            page_content = await self.playwright_manager.get_page_content(search_url)
            if not page_content: return None
            
            soup = BeautifulSoup(page_content, 'html.parser')
            all_text_from_snippets = ' '.join([s.get_text() for s in soup.select(".b_lineclamp2, .b_algoSlug")])
            if not all_text_from_snippets: return None

            found_emails = re.findall(self.email_pattern, all_text_from_snippets)
            filtered_emails = self.filter_emails(found_emails)

            # --- ▼▼▼ 【核心修复】返回整个列表，而不是单个字符串 ▼▼▼ ---
            return filtered_emails if filtered_emails else None
            # --- ▲▲▲ 修复结束 ▲▲▲ ---
        except Exception: 
            return None

    async def search_with_bing_and_select(self, query, session, top_n_results=10, visit_best_n=3):
        """
        【最终性能优化版 - 智能降级兜底】
        - 兜底搜索现在也采用两阶段策略：
        1. 首先尝试使用快速的 curl_cffi 进行Bing搜索。
        2. 只有在快速方法失败（如遇到人机验证）时，才升级动用 Playwright。
        - 这将极大减少不必要的Playwright启动，从根本上解决并发调用导致的卡顿。
        """
        from difflib import SequenceMatcher
        def get_similarity(a, b): return SequenceMatcher(None, a, b).ratio()
        
        try:
            # --- 总开关判断 (保持不变) ---
            if not self.enable_playwright_fallback:
                print("ℹ️ Playwright 强力模式已关闭，跳过最终的Bing兜底搜索。")
                return None, None

            url = f"https://www.bing.com/search?q={quote(query)}&mkt=en-US"
            text = None
            soup = None

            # --- ▼▼▼ 【【【核心修复：为兜底搜索增加智能降级】】】 ▼▼▼ ---

            # 阶段一：尝试使用“侦察兵”(curl_cffi)进行快速搜索
            print(f" разведчик [快速兜底搜索] 正在尝试使用 curl_cffi 搜索: {query}...")
            try:
                # 直接复用我们强大的 fetch_page 方法，但强制它不要在失败时降级到Playwright
                # 注意：这里我们临时关闭了 enable_playwright_fallback
                original_fallback_state = self.enable_playwright_fallback
                self.enable_playwright_fallback = False
                fast_text = await self.fetch_page(url, session)
                self.enable_playwright_fallback = original_fallback_state # 立刻恢复原状

                if fast_text:
                    temp_soup = BeautifulSoup(fast_text, "html.parser")
                    # 检查是否能找到搜索结果的标志性容器
                    if temp_soup.find("li", class_="b_algo"):
                        print("  -> ✅ [快速兜底搜索] 成功！已获取到Bing搜索结果页面。")
                        text = fast_text
                        soup = temp_soup
            except Exception as e:
                print(f"  -> ⚠️ [快速兜底搜索] 发生错误: {e}")

            # 阶段二：如果快速方法失败，才出动“重型坦克”(Playwright)
            if not text:
                print(f"🐢 [Playwright兜底搜索] 快速搜索失败，正在升级至 Playwright 进行搜索: {query}...")
                
                if not self.playwright_manager or not self.playwright_manager.is_available():
                    print("❌ Playwright 不可用，Bing 兜底搜索中止。")
                    return None, None
                
                text = await self.playwright_manager.get_page_content(url)
                if not text:
                    print("❌ Playwright 未能获取Bing页面内容。")
                    return None, None
            
            # --- ▲▲▲ 修复结束 ▲▲▲ ---

            # 后续的解析和“精准打击”逻辑，现在可以安全地基于获取到的`text`执行
            if not soup: # 如果 soup 还没被创建 (说明走了Playwright路径)
                soup = BeautifulSoup(text, "html.parser")

            links = soup.find_all("li", class_="b_algo")
            if not links:
                print("ℹ️ Bing页面解析成功，但未找到任何搜索结果项。")
                return None, None
                
            # (后续的链接筛选和精准打击逻辑保持不变)
            candidate_links = []
            cleaned_company_name = re.sub(r'[^a-z0-9]', '', self.company_name.lower())
            for item in links[:top_n_results]:
                a = item.select_one("h2 a")
                if not a or not a.get('href'): continue
                
                real_link = deobfuscate_text(a['href'])
                if not real_link.startswith(('http', 'https')): continue
                
                parsed_url = urlparse(real_link)
                domain = parsed_url.netloc.replace('www.', '')
                if self.country != "China" and domain.endswith('.cn'): continue
                    
                excluded_link_domains = ['facebook.com', 'linkedin.com', 'yelp.com', 'instagram.com', 'twitter.com', 'youtube.com', 'zhihu.com', 'baidu.com', 'weibo.com', 'bilibili.com', 'sohu.com', '163.com']
                if any(excluded in domain for excluded in excluded_link_domains): continue
                    
                similarity_score = get_similarity(cleaned_company_name, re.sub(r'[^a-z0-9]', '', domain.split('.')[0]))
                candidate_links.append({"url": real_link, "score": similarity_score})
            
            if not candidate_links:
                return None, None
                
            candidate_links.sort(key=lambda x: x['score'], reverse=True)
            
            best_candidate_url = candidate_links[0]['url']
            print(f"  -> [精准兜底] 已锁定最佳候选网站: {best_candidate_url}")

            found_email = await self.quick_scan_homepage(session, url_override=best_candidate_url)

            if found_email:
                print(f"  -> ✅ [精准兜底] 成功在候选网站首页找到邮箱: {found_email}")
                return [found_email], best_candidate_url
            else:
                print(f"  -> ❌ [精准兜底] 未能在最佳候选网站首页找到邮箱。")
                return None, None

        except Exception as e:
            print(f"❌ Bing 搜索选择流程发生严重异常: {type(e).__name__} - {e}")
            traceback.print_exc()
            return None, None


    async def validate_phone_on_whatsapp(self, phone_number, session):
        """
        【逻辑重构最终版】
        - “标准模式”现在将只从网页文本中提取号码。
        - “高级模式”将采用三步验证流程：网页提取 -> 商家电话保底 -> 内部API验证。
        """
        # 模式为关闭则直接返回 (逻辑不变)
        if self.whatsapp_validation_mode == 'off':
            return None

        # --- ▼▼▼ 标准模式 (只从网页提取) ▼▼▼ ---
        elif self.whatsapp_validation_mode == 'standard':
            print(f"🔷 [标准模式] 正在从官网文本中提取WhatsApp号码...")
            
            if not self.website:
                print(f"  -> 无官网信息，无法执行网页提取。")
                return None

            try:
                homepage_text = await self.fetch_page(self.website, session)
                if not homepage_text:
                    return None
                
                # (此部分网页扫描和提取逻辑与之前版本相同)
                phone_pattern = re.compile(r'(\+\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4,}')
                soup = BeautifulSoup(homepage_text, 'html.parser')
                text_content = soup.get_text()
                potential_numbers = phone_pattern.findall(text_content)
                
                if not potential_numbers:
                    print(f"  -> 在 {self.website} 的文本中未发现任何电话号码格式。")
                    return None

                best_candidate = None
                for num_tuple in potential_numbers:
                    full_number_str = "".join(num_tuple).strip()
                    cleaned_number = re.sub(r'\D', '', full_number_str)

                    country_code_map = {"新加坡": "65", "马来西亚": "60", "中国": "86"}
                    country_code = country_code_map.get(self.country)

                    if country_code and cleaned_number.startswith(country_code) and len(cleaned_number) > len(best_candidate or ""):
                        best_candidate = cleaned_number
                    elif not best_candidate and len(cleaned_number) >= 8:
                        best_candidate = cleaned_number

                if best_candidate:
                    print(f"✅ [标准模式] 成功从网页文本中提取到WhatsApp候选号码: {best_candidate}")
                return best_candidate

            except Exception as e:
                print(f"❌ [标准模式] 网页文本提取过程中发生错误: {e}")
                return None
        
        # --- ▼▼▼ 高级模式 (网页提取 -> 商家电话 -> 内部验证) ▼▼▼ ---
        elif self.whatsapp_validation_mode == 'advanced':
            print(f"🔶 [高级模式] 正在执行多阶段WhatsApp号码验证...")
            candidate_number = None

            # 步骤 1: 首先尝试从网页中提取
            if self.website:
                try:
                    # (这里的网页提取逻辑与标准模式完全相同)
                    homepage_text = await self.fetch_page(self.website, session)
                    if homepage_text:
                        phone_pattern = re.compile(r'(\+\d{1,3}[-\.\s]?)?\(?\d{3}\)?[-\.\s]?\d{3}[-\.\s]?\d{4,}')
                        soup = BeautifulSoup(homepage_text, 'html.parser')
                        text_content = soup.get_text()
                        potential_numbers = phone_pattern.findall(text_content)
                        
                        if potential_numbers:
                            for num_tuple in potential_numbers:
                                full_number_str = "".join(num_tuple).strip()
                                cleaned_number = re.sub(r'\D', '', full_number_str)
                                if len(cleaned_number) >= 8:
                                    candidate_number = cleaned_number
                                    break # 找到第一个就用
                    if candidate_number:
                        print(f"  -> 步骤1: 成功从网页中提取到候选号码: {candidate_number}")

                except Exception as e:
                    print(f"  -> 步骤1: 网页提取过程中发生错误: {e}")

            # 步骤 2: 如果网页提取失败，则使用商家电话作为备选
            if not candidate_number:
                print("  -> 步骤1失败，正在使用商家自身电话作为备选...")
                cleaned_gmb_phone = re.sub(r'\D', '', phone_number or "")
                if len(cleaned_gmb_phone) >= 8:
                    candidate_number = cleaned_gmb_phone
                    print(f"  -> 步骤2: 成功采用商家电话: {candidate_number}")
            
            # 如果到这里还没有任何候选号码，则中止
            if not candidate_number:
                print("  -> 未找到任何有效的候选号码，高级验证中止。")
                return None

            # 步骤 3: 将最终的候选号码提交至内部API进行验证
            print(f"  -> 步骤3: 将候选号码 {candidate_number} 提交至内部API进行最终验证...")
            if not self.whatsapp_manager or not self.whatsapp_manager.initialization_successful:
                print("  -> 错误：WhatsApp管理器不可用或未初始化。")
                return None
            
            is_valid = self.whatsapp_manager.run_coroutine(
                self.whatsapp_manager.check_whatsapp_number_advanced(candidate_number)
            )
            
            if is_valid:
                print(f"✅ [高级模式] 验证成功！号码 {candidate_number} 是有效的WhatsApp号。")
                return candidate_number
            else:
                print(f"❌ [高级模式] 验证失败，号码 {candidate_number} 不是有效的WhatsApp号。")
                return None
        
        return None
        
    # --- 【核心重构】主调度方法 ---


    async def quick_scan_homepage(self, session):
        """
        【新增的辅助功能】
        对官网首页进行一次快速扫描。如果能找到与官网域名匹配的高质量邮箱，
        就直接返回该邮箱，作为最高优先级的结果，实现“早退”以提升速度。
        """
        if not self.website:
            return None
        
        try:
            # 使用较短的超时时间，因为我们追求速度
            text = await self.fetch_page(self.website, session, timeout=15)
            if not text:
                return None
            
            # 在快速扫描时，也顺便检查一下社交链接
            soup = BeautifulSoup(text, 'html.parser')
            for link in soup.find_all('a', href=True):
                self._check_and_store_social_link(link['href'])
            
            # 提取邮箱
            emails_with_context = await self.extract_emails(text, self.website)
            if not emails_with_context:
                return None
            
            # 对找到的邮箱进行评分
            scored_emails = []
            for email, source_url, has_phone in emails_with_context:
                score = self.score_email(email, source_url, has_phone)
                if score > -900: # 过滤掉垃圾邮箱
                    scored_emails.append((email, score))
            
            if not scored_emails:
                return None

            scored_emails.sort(key=lambda x: x[1], reverse=True)
            best_email, best_score = scored_emails[0]
            
            # 【快速模式的核心判断】检查最佳邮箱的域名是否与官网域名匹配
            try:
                email_domain = best_email.split('@')[1].lower()
                website_domain = urlparse(self.website).netloc.replace('www.', '').lower()
                if email_domain == website_domain:
                    print(f"⚡️ [快速扫描] 成功！在首页找到高质量匹配邮箱: {best_email}")
                    return best_email # 如果匹配，这被认为是一个高质量结果，直接返回
                else:
                    # 如果不匹配，说明可能是个通用邮箱(如gmail)，在快速模式下我们放弃这个结果
                    print(f"🤔 [快速扫描] 在首页找到邮箱 {best_email}，但域名不匹配官网，将继续深度扫描...")
                    return None
            except Exception:
                return None
                
        except Exception as e:
            print(f"❌ [快速扫描] 流程发生未知错误: {e}")
            return None



    # (在 EmailFetcherWorker 类中，用这个【【【完整的新方法】】】替换旧的 fetch_email 方法)
    async def fetch_email(self):
            """
            【社交媒体链接兜底修复版】
            增加了对初始官网链接的预检查。如果链接是社交媒体，则直接跳过并启动兜底搜索。
            同时确保此方法在所有代码路径下都能返回一个 (dict, int) 格式的元组。
            """
            final_result = {}
            try:
                self.final_email_output = "N/A"
                all_found_emails = []

                # --- ▼▼▼ 【核心修复】在这里增加前置检查逻辑 ▼▼▼ ---
                if self.website:
                    # 定义一个常见的社交媒体域名列表
                    social_domains = [
                        'facebook.com', 'instagram.com', 'linkedin.com', 
                        'twitter.com', 'youtube.com', 'tiktok.com', 'pinterest.com'
                    ]
                    try:
                        parsed_url = urlparse(self.website)
                        # 获取纯域名，例如 'www.facebook.com' -> 'facebook.com'
                        domain = '.'.join(parsed_url.netloc.lower().split('.')[-2:])
                        
                        if any(social_domain == domain for social_domain in social_domains):
                            print(f"⚠️ 初始官网链接为社交媒体 ({self.website})，将跳过直接扫描，启动兜底搜索。")
                            # 【关键】将官网链接置空，强制程序走兜底逻辑
                            self.website = "" 
                    except Exception:
                        # 如果URL解析失败，也当作无效链接处理
                        self.website = ""
                # --- ▲▲▲ 修复结束 ▲▲▲ ---

                async with AsyncSession(impersonate="chrome120", verify=False) as session:
                    # 后续的逻辑会因为 self.website 变为空而自动跳到正确的兜底流程
                    if self.website and not self.collect_all_emails_mode:
                        quick_scan_result = await self.quick_scan_homepage(session)
                        if quick_scan_result:
                            all_found_emails.append(quick_scan_result)

                    if not all_found_emails and self.website:
                        all_candidates = await self.crawl_subpages(self.website, session)
                        if all_candidates:
                            unique_emails_props = {email: props for email, *props in all_candidates}
                            scored_emails = []
                            for email, (source_url, has_phone) in unique_emails_props.items():
                                score = self.score_email(email, source_url, has_phone)
                                if score > -900:
                                    scored_emails.append((email, score))
                            
                            if scored_emails:
                                scored_emails.sort(key=lambda x: x[1], reverse=True)
                                all_found_emails.extend([email for email, score in scored_emails])

                    if not all_found_emails:
                        if self.website:
                            print(f"ℹ️ 官网 {self.website} 未找到邮箱，启动第一阶段兜底：域名限定搜索...")
                            emails_from_domain_search = await self.search_domain_specific_email(session)
                            if emails_from_domain_search:
                                all_found_emails.extend(emails_from_domain_search)
                        
                        if not all_found_emails:
                            # 因为我们在开头已经处理了社交媒体链接，所以这里的逻辑现在是正确的
                            if not self.website:
                                print(f"🚀 无有效官网，直接进入Bing搜索模式，目标: '{self.company_name}'")
                            else:
                                print(f"ℹ️ 域名限定搜索失败，启动最终阶段兜底：宽泛Bing搜索...")

                            query_parts = [self.company_name, self.address, self.phone]
                            query = " ".join(filter(None, query_parts))
                            
                            found_emails_list, found_website = await self.search_with_bing_and_select(query, session)
                            
                            if found_emails_list is None:
                                # 明确地将最终输出设置为“未找到”，因为搜索被跳过了
                                self.final_email_output = "N/A (Skipped)"
                            else:
                                # 只有在搜索真的执行了并且有结果时，才处理结果
                                if found_emails_list:
                                    all_found_emails.extend(found_emails_list)
                                if found_website and not self.website: 
                                    self.website = found_website
                    
                    if all_found_emails:
                        unique_emails_ordered = list(dict.fromkeys(all_found_emails))
                        if self.collect_all_emails_mode:
                            self.final_email_output = ";".join(unique_emails_ordered)
                            print(f"🐢 [全量扫描] 成功，共找到 {len(unique_emails_ordered)} 个高质量邮箱: {self.final_email_output}")
                        else:
                            self.final_email_output = unique_emails_ordered[0]
                            print(f"⚡️ [快速扫描] 成功，选用最佳邮箱: {self.final_email_output}")
                    elif self.final_email_output == "N/A":
                        self.final_email_output = "N/A (Searched)"
                    
                    if not self.found_social_links.get('whatsapp') and self.phone:
                        validated_number = await self.validate_phone_on_whatsapp(self.phone, session)
                        if validated_number:
                            self.found_social_links['whatsapp'] = validated_number

            except Exception as e:
                print(f"❌ 提取邮箱主流程失败 ({self.company_name}): {e}")
                traceback.print_exc()
                self.final_email_output = f"Error: {type(e).__name__}"
            
            finally:
                final_result = {
                    'email': self.final_email_output, 
                    'website': self.website or "", 
                    **self.found_social_links
                }
                # 确保始终返回一个元组
                return final_result, self.row
            


    # --- 线程入口 (保持不变) ---
    @pyqtSlot()
    def run(self):
        """
        【死锁修复版】此方法现在是一个简单的包装器，用于同步执行核心的异步任务。
        添加了更智能的超时和错误处理机制。
        """
        try:
            # 【超时保护】使用修复后的run_coroutine，添加更详细的错误处理
            print(f"🔄 Worker启动: {self.company_name} (行{self.row})")
            result = self.playwright_manager.run_coroutine(self.fetch_email())
            
            if result is None:
                # 如果超时或失败，返回一个标准格式的结果
                print(f"⚠️ Worker超时: {self.company_name} - 可能是页面池繁忙或网络问题")
                error_result = {'email': "Timeout: 页面池繁忙或网络超时"}
                return error_result, self.row
            
            print(f"✅ Worker完成: {self.company_name}")
            return result
        except Exception as e:
            print(f"❌ EmailFetcherWorker.run() 发生严重错误: {e}")
            traceback.print_exc()
            # 在出错时，也返回一个符合格式的元组
            error_result = {'email': f"Error: {type(e).__name__}"}
            return error_result, self.row

            




class DBManager:
    """
    一个用于管理SQLite数据库的单例类。
    负责数据库的连接、表的创建以及数据的增删改查。
    """
    _instance = None

    def __new__(cls): #【修复】移除了 db_name 参数，使其固定
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            
            # 【核心修复】使用 get_app_data_path 来获取数据库文件的标准路径
            # 这确保了数据库和JSON配置文件存储在同一个可靠的位置
            db_path = get_app_data_path("scraper_data.db")
            print(f"数据库文件将被存储在: {db_path}")
            
            cls._instance.db_name = db_path # 使用完整的、跨平台兼容的路径
            cls._instance.conn = None
            cls._instance.connect()
            cls._instance.create_table()
        return cls._instance

    def connect(self):
        """连接到SQLite数据库"""
        try:
            # 使用 check_same_thread=False 允许在多线程中使用此连接
            self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
            print(f"✅ 成功连接到数据库: {self.db_name}")
        except sqlite3.Error as e:
            print(f"❌ 连接数据库失败: {e}")

    def create_table(self):
        """【修改版】创建一个用于存储公司信息的数据表（如果不存在）"""
        if not self.conn:
            return
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    address TEXT,
                    phone TEXT,
                    image_url TEXT,
                    email TEXT,
                    website TEXT,
                    -- 【新增】为社交媒体链接添加新字段 --
                    facebook_url TEXT,
                    instagram_url TEXT,
                    linkedin_url TEXT,
                    whatsapp_url TEXT,
                    ------------------------------------
                    category TEXT,
                    hours TEXT,
                    rating REAL,
                    review_count INTEGER,
                    source_link TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, address)
                )
            """)
            self.conn.commit()
            print("✅ 数据表 'companies' 已准备就绪。")
        except sqlite3.Error as e:
            print(f"❌ 创建数据表失败: {e}")


    def insert_company(self, company_data):
        """
        向数据库中插入一条新的公司数据。
        如果公司已存在（基于名称和地址的唯一性约束），则不会插入。

        Args:
            company_data (dict): 包含公司信息的字典。

        Returns:
            int: 如果插入成功，返回新记录的ID；如果数据已存在或插入失败，返回None。
        """
        if not self.conn:
            return None
        
        # 准备SQL插入语句
        sql = ''' INSERT INTO companies(name, address, phone, image_url, email, website, facebook_url, instagram_url, linkedin_url, whatsapp_url, category, hours, rating, review_count, source_link)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) '''
        
        # 从字典中提取数据
        company = (
            company_data.get('name'),
            company_data.get('address'),
            company_data.get('phone'),
            company_data.get('image'),
            None,  # email 初始为空
            company_data.get('website'),
            None,  # facebook_url 初始为空
            None,  # instagram_url 初始为空
            None,  # linkedin_url 初始为空
            None,  # whatsapp_url 初始为空
            company_data.get('dkEaLTexts'), # category
            company_data.get('hours'),
            company_data.get('rating'),
            company_data.get('reviewCount'),
            company_data.get('link') # source_link
        )

        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, company)
            self.conn.commit()
            return cursor.lastrowid # 返回新插入行的ID
        except sqlite3.IntegrityError:
            # 这是一个预期的错误，表示数据重复（因为我们设置了UNIQUE约束）
            # print(f"🔵 重复数据，已跳过: {company_data.get('name')}")
            return None
        except sqlite3.Error as e:
            print(f"❌ 插入数据失败: {e}")
            return None

    def update_email_and_website(self, name, address, email, website):
        """根据公司名称和地址，更新其邮箱和官网信息"""
        if not self.conn:
            return False
        
        sql = ''' UPDATE companies
                  SET email = ?, website = ?
                  WHERE name = ? AND address = ? '''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (email, website, name, address))
            self.conn.commit()
            return cursor.rowcount > 0 # 如果有行被更新，返回True
        except sqlite3.Error as e:
            print(f"❌ 更新邮箱/官网失败: {e}")
            return False
        
    def update_social_media(self, name, address, social_links):
        if not self.conn:
            return False
        
        # social_links 是一个字典，例如 {'facebook': 'url', 'instagram': 'url'}
        sql = ''' UPDATE companies
                  SET facebook_url = ?, instagram_url = ?, linkedin_url = ?, whatsapp_url = ?
                  WHERE name = ? AND address = ? '''
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, (
                social_links.get('facebook'),
                social_links.get('instagram'),
                social_links.get('linkedin'),
                social_links.get('whatsapp'),
                name,
                address
            ))
            self.conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as e:
            print(f"❌ 更新社交媒体链接失败: {e}")
            return False
            
    def get_all_companies(self):
        """从数据库中查询所有公司的数据"""
        if not self.conn:
            return []
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT name, address, phone, email, website, category, hours, rating, review_count, source_link FROM companies")
            rows = cursor.fetchall()
            # 将查询结果转换为字典列表，以便于导出
            headers = ["名称", "地址", "电话", "邮箱", "官网","类别", "营业时间", "评分", "评价数", "来源链接"]
            return [dict(zip(headers, row)) for row in rows]
        except sqlite3.Error as e:
            print(f"❌ 查询所有数据失败: {e}")
            return []
        
    def get_all_companies_in_batches(self, batch_size=500):
        """
        【新增】
        使用生成器（generator）分批次从数据库中查询所有公司数据。
        这可以极大地减少内存占用。
        """
        if not self.conn:
            return

        offset = 0
        while True:
            try:
                cursor = self.conn.cursor()
                cursor.execute(f"SELECT name, address, phone, email, website, facebook_url, instagram_url, linkedin_url, whatsapp_url, category, hours, rating, review_count, source_link, image_url FROM companies LIMIT {batch_size} OFFSET {offset}")
                rows = cursor.fetchall()

                if not rows:
                    # 如果没有更多数据了，循环结束
                    break
                
                # 使用 yield 返回当前批次的数据
                yield rows
                
                offset += batch_size
            except sqlite3.Error as e:
                print(f"❌ 分批查询数据失败: {e}")
                break
                
    def clear_all_companies(self):
        """清空 companies 表中的所有数据"""
        if not self.conn:
            return False
        try:
            cursor = self.conn.cursor()
            # 使用 DELETE FROM 语句来清空表，比 DROP TABLE 更安全
            cursor.execute("DELETE FROM companies")
            self.conn.commit()
            print("🗑️ 数据库表 'companies' 已被清空。")
            return True
        except sqlite3.Error as e:
            print(f"❌ 清空数据表失败: {e}")
            return False



    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            print("ℹ️ 数据库连接已关闭。")


# 一个专门用于在后台执行数据库操作的线程
class DatabaseWorker(QThread):
    """一个专门用于在后台执行数据库操作的线程"""
    # 定义信号，用于从主线程接收任务
    insert_request = pyqtSignal(dict)
    update_request = pyqtSignal(str, str, str, str)
    update_social_media_request = pyqtSignal(str, str, dict)

    def __init__(self):
        super().__init__()
        self.db_manager = None

    def run(self):
        """线程启动后，创建DBManager实例并进入事件循环"""
        self.db_manager = DBManager()
        # connect signals to slots within this thread
        self.insert_request.connect(self.handle_insert)
        self.update_request.connect(self.handle_update)
        self.update_social_media_request.connect(self.handle_update_social_media)
        self.exec_() # 开启线程的事件循环，等待信号

    def handle_insert(self, data):
        if self.db_manager:
            self.db_manager.insert_company(data)

    def handle_update(self, name, address, email, website):
        if self.db_manager:
            self.db_manager.update_email_and_website(name, address, email, website)

    def handle_update_social_media(self, name, address, social_links):
        if self.db_manager:
            self.db_manager.update_social_media(name, address, social_links)

    def get_all_companies_blocking(self):
        """提供一个同步方法来获取数据，仅用于导出等非高频操作"""
        if self.db_manager:
            return self.db_manager.get_all_companies()
        return []
    
    def get_all_companies_in_batches_blocking(self, batch_size=500):
        """【新增】提供一个同步方法来分批获取数据"""
        if self.db_manager:
            # 返回生成器，让调用者去迭代
            return self.db_manager.get_all_companies_in_batches(batch_size)
        return iter([]) # 如果没有db_manager，返回一个空迭代器

    def clear_all_companies_blocking(self):
        """提供一个同步方法来清空数据"""
        if self.db_manager:
            return self.db_manager.clear_all_companies()
        return False

    def stop(self):
        """停止线程的事件循环"""
        if self.db_manager:
            self.db_manager.close()
        self.quit()
        # self.wait()


# 请使用这个新函数来替换上面的旧函数
def resource_path(relative_path):
    """
    获取资源的绝对路径，使其能够同时兼容开发模式、PyInstaller 和 Nuitka 的所有打包模式。
    """
    try:
        # PyInstaller 和 Nuitka 都会在打包后设置 sys.frozen 属性
        if getattr(sys, 'frozen', False):
            # 核心逻辑：
            # 1. 尝试获取 PyInstaller 单文件模式下的 _MEIPASS 临时路径。
            # 2. 如果获取不到（说明是 PyInstaller 文件夹模式 或 Nuitka 的任意模式），
            #    则使用可执行文件所在的目录作为基准路径。
            base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(sys.executable)))
        else:
            # 如果不是打包环境（即直接运行 .py 脚本），则使用当前工作目录
            base_path = os.path.abspath(".")

    except Exception:
        # 作为一个备用方案，如果上述逻辑出现任何意外，也回退到当前工作目录
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


class WhatsAppInitWorker(QObject):
    """
    一个专用于在后台线程中执行WhatsApp初始化任务的“工人”。
    它继承自QObject，以便可以移动到QThread中。
    """
    # 定义信号：
    # finished 信号将在任务完成后发射，并携带一个布尔值表示是否成功。
    finished = pyqtSignal(bool)

    def __init__(self, whatsapp_manager):
        super().__init__()
        self.whatsapp_manager = whatsapp_manager
        self._is_running = True

    @pyqtSlot()  # 明确这是一个槽函数
    def run(self):
        """
        这个方法将在新的后台线程中被执行。
        """
        if not self._is_running:
            return

        print("🚀 WhatsApp初始化Worker已在后台线程启动...")
        try:
            # 【核心】在这里，我们调用会阻塞的初始化流程。
            # 因为整个 run 方法已经在一个独立的线程里了，所以阻塞在这里是安全的，不会影响主UI。
            self.whatsapp_manager.run_coroutine(self.whatsapp_manager._initialize_browser_internal())
            
            # 检查初始化是否真的成功了
            success = self.whatsapp_manager.initialization_successful
            
            # 发射完成信号，并把成功与否的结果传递出去
            self.finished.emit(success)

        except Exception as e:
            print(f"❌ WhatsApp初始化Worker在执行时发生错误: {e}")
            self.finished.emit(False) # 发生异常，也发射一个失败信号

    def stop(self):
        self._is_running = False



# 【核心修改】不再使用 session.json，而是为浏览器创建一个完整的持久化配置文件夹
WHATSAPP_PROFILE_PATH = get_app_data_path("whatsapp_profile")
WPPCONNECT_API_PATH = resource_path("api.js") 

class WhatsAppManager(QObject):
    """
    【最终CSP修正版】
    使用自定义的、基于Promise的等待脚本来替代 wait_for_function，
    以彻底解决 'unsafe-eval' 内容安全策略问题。
    """
    login_success_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self._playwright: Playwright | None = None
        self._context: any = None 
        self._page: any = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._is_running = threading.Event()
        self._lock = threading.Lock() 
        self.initialization_successful = False
        self._thread.start()
        self._is_running.wait()

    def _run_loop(self):
        asyncio.run(self._main())

    async def _main(self):
        self._loop = asyncio.get_running_loop()
        self._is_running.set()
        await self._loop.create_future() 

    def run_coroutine(self, coro):
        with self._lock:
            if not self._loop: raise RuntimeError("WhatsAppManager event loop is not running.")
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            try:
                return future.result(timeout=320)
            except Exception as e:
                print(f"❌ WhatsAppManager 异步任务执行失败或超时: {e}")
                future.cancel()
                return None

    async def _initialize_browser_internal(self):
        if self._page and not self._page.is_closed():
            return

        print("🚀 [WhatsApp] 首次检测，正在后台启动持久化浏览器实例...")
        
        # 保持重试逻辑，以应对网络问题
        MAX_RETRIES = 2
        for attempt in range(MAX_RETRIES):
            try:
                if not os.path.exists(WPPCONNECT_API_PATH):
                    print(f"❌ [WhatsApp] 致命错误: 未找到 wppconnect API 文件: {WPPCONNECT_API_PATH}")
                    return

                if attempt > 0:
                    print(f"⚠️ 尝试 {attempt}/{MAX_RETRIES}: 正在清理旧的浏览器配置文件并重试...")
                    if self._context:
                        await self._context.close()
                        self._context = None
                    if self._playwright:
                        await self._playwright.stop()
                        self._playwright = None
                    import shutil
                    if os.path.exists(WHATSAPP_PROFILE_PATH):
                        shutil.rmtree(WHATSAPP_PROFILE_PATH, ignore_errors=True)
                    await asyncio.sleep(2)

                if not self._playwright:
                    self._playwright = await async_playwright().start()
                
                # self._context = await self._playwright.chromium.launch_persistent_context(
                #     user_data_dir=WHATSAPP_PROFILE_PATH,
                #     headless=False,
                #     user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                #     args=['--no-sandbox', '--disable-setuid-sandbox']
                # )

                launch_options = {
                    'user_data_dir': WHATSAPP_PROFILE_PATH,
                    'headless': True,
                    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                    'args': ['--no-sandbox', '--disable-setuid-sandbox']
                }

                if getattr(sys, 'frozen', False):
                    # 在打包后的环境中，构造捆绑的浏览器路径
                    # 注意：这里的 'chromium-1187' 必须和 .spec 文件中指定的版本号一致
                    executable_path = resource_path(os.path.join('ms-playwright', 'chromium-1187', 'chrome-win', 'chrome.exe'))
                    if os.path.exists(executable_path):
                        print(f"✅ [WhatsApp 后台] 发现捆绑的浏览器: {executable_path}")
                        launch_options['executable_path'] = executable_path
                    else:
                        print(f"❌ [WhatsApp 后台] 致命错误: 找不到捆绑的浏览器 {executable_path}")
                        # 可以选择在这里直接返回或抛出异常
                        return

                self._context = await self._playwright.chromium.launch_persistent_context(**launch_options)
                
                self._page = self._context.pages[0] if self._context.pages else await self._context.new_page()
                
                print("🕒 正在导航至 WhatsApp Web...")
                await self._page.goto("https://web.whatsapp.com", wait_until="domcontentloaded", timeout=60000)

                print("   -> 正在注入 API...")
                with open(WPPCONNECT_API_PATH, 'r', encoding='utf-8') as f:
                    wpp_script_content = f.read()
                await self._page.evaluate(wpp_script_content)

                # --- ▼▼▼【核心修复】使用基于Promise的自定义等待脚本 ▼▼▼ ---
                print("   -> 正在使用自定义 Promise 等待 WPP API 完全就绪...")
                
                js_wait_for_wpp = """
                () => {
                    return new Promise((resolve, reject) => {
                        const timeout = 60000; // 60秒超时
                        const interval = 500;   // 每500毫秒检查一次
                        let elapsedTime = 0;

                        const checkWpp = () => {
                            if (window.WPP && window.WPP.isFullReady) {
                                clearInterval(intervalId);
                                resolve(true);
                            } else {
                                elapsedTime += interval;
                                if (elapsedTime >= timeout) {
                                    clearInterval(intervalId);
                                    reject(new Error('WPP API 在60秒内未能准备就绪。'));
                                }
                            }
                        };
                        const intervalId = setInterval(checkWpp, interval);
                    });
                }
                """
                # page.evaluate 会自动等待 Promise 完成
                await self._page.evaluate(js_wait_for_wpp)
                # --- ▲▲▲ 修复结束 ▲▲▲ ---
                
                self.initialization_successful = True
                print("✅ [WhatsApp] 浏览器实例启动成功，WPP API已就绪。")
                return 

            except Exception as e:
                print(f"❌ [WhatsApp] 启动后台浏览器或注入API失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt >= MAX_RETRIES - 1:
                    self.initialization_successful = False
    
    # login_to_whatsapp 方法保持不变
    async def login_to_whatsapp(self):
        print("🚀 正在启动WhatsApp登录窗口...")
        playwright = await async_playwright().start()
        context = None
        try:
            launch_options = {
                'user_data_dir': WHATSAPP_PROFILE_PATH,
                'headless': False,
                'args': ['--no-sandbox']
            }

            if getattr(sys, 'frozen', False):
                # 在打包后的环境中，构造捆绑的浏览器路径
                # 再次确保这里的版本号与 .spec 文件中一致
                executable_path = resource_path(os.path.join('ms-playwright', 'chromium-1187', 'chrome-win', 'chrome.exe'))
                if os.path.exists(executable_path):
                    print(f"✅ [WhatsApp 登录] 发现捆绑的浏览器: {executable_path}")
                    launch_options['executable_path'] = executable_path
                else:
                    print(f"❌ [WhatsApp 登录] 致命错误: 找不到捆绑的浏览器 {executable_path}")
                    # 在用户交互场景下，可以弹窗提示
                    QMessageBox.critical(None, "启动失败", f"找不到必要的浏览器组件: {executable_path}")
                    if playwright: await playwright.stop()
                    return # 终止登录流程

            context = await playwright.chromium.launch_persistent_context(**launch_options)
            page = context.pages[0] if context.pages else await context.new_page()
            if "web.whatsapp.com" not in page.url:
                await page.goto("https://web.whatsapp.com", timeout=60000)
            print("⏳ 请在打开的浏览器窗口中扫描二维码登录WhatsApp...")
            await page.wait_for_selector("div#pane-side", timeout=300000)
            print("✅ 检测到WhatsApp登录成功！会话已自动保存。")
            self.login_success_signal.emit()
        except Exception as e:
            print(f"❌ WhatsApp登录失败或超时: {e}")
        finally:
            if context:
                await context.close()
            await playwright.stop()

    # check_whatsapp_number_advanced 方法保持不变
    async def check_whatsapp_number_advanced(self, phone_number) -> bool:
        if not self.initialization_successful or not self._page or self._page.is_closed():
            print("❌ [WhatsApp] 后台浏览器未就绪，检测中止。")
            print("   -> 尝试自动重新初始化...")
            await self._initialize_browser_internal()
            if not self.initialization_successful or not self._page or self._page.is_closed():
                print("❌ [WhatsApp] 自动重新初始化失败，检测彻底中止。")
                return False

        print(f"🕵️ [内部API验证] 正在检测号码: {phone_number}")
        
        try:
            js_code = f"window.WPP.contact.queryExists('{phone_number}@c.us');"
            result = await self._page.evaluate(js_code)
            is_valid = result is not None
            if is_valid:
                print(f"✅ [内部API验证] 成功！号码 {phone_number} 有效。")
            else:
                print(f"❌ [内部API验证] 号码 {phone_number} 无效或未注册。")
            return is_valid
        except Exception as e:
            print(f"❌ [内部API验证] 执行JS检查时发生严重错误: {e}")
            self.initialization_successful = False
            if self._context:
                await self._context.close()
                self._context = None
            self._page = None
            return False
    
    def run_coroutine_no_wait(self, coro):
        """
        【新增】一个非阻塞版本的 run_coroutine。
        它只负责将任务提交到事件循环，然后立即返回，不等待结果。
        专门用于处理需要用户长时间交互的任务，如扫码登录。
        """
        with self._lock:
            if not self._loop:
                raise RuntimeError("WhatsAppManager event loop is not running.")
            # 只提交任务，不调用 future.result()
            future = asyncio.run_coroutine_threadsafe(coro, self._loop)
            # 立即返回 future 对象，而不是等待它的结果
            return future

    # is_logged_in, _shutdown_internal, shutdown 方法保持不变
    def is_logged_in(self):
        return os.path.exists(WHATSAPP_PROFILE_PATH)

    async def _shutdown_internal(self):
        if self._context:
            print("🌙 [WhatsApp] 正在关闭持久化的浏览器上下文...")
            await self._context.close()
        if self._playwright:
            await self._playwright.stop()
        self._page = None
        self._context = None
        self._playwright = None
        self.initialization_successful = False
        print("✅ [WhatsApp] 浏览器已安全关闭。")

    def shutdown(self):
        if self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(self._shutdown_internal(), self._loop)


# 单例浏览器管理器
class PlaywrightManager:
    """
    一个线程安全的管理器，用于维护单个Playwright浏览器实例。
    该管理器在自己的后台线程中运行一个专用的asyncio事件循环。
    """
    # 定义浏览器在空闲多少秒后自动关闭
    SHUTDOWN_DELAY = 180  # 3分钟

    def __init__(self, pool_size=3): # 【新增】允许指定池的大小
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._context = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._is_running = threading.Event()
        self._lock = threading.Lock() # 这个锁仍然保留，用于保护初始化和关闭等关键操作
        
        self.initialization_successful = False
        self.shutdown_timer = None
        self._speed_mode_enabled = False

        # 【核心新增】页面池相关属性
        self.pool_size = max(1, pool_size) # 确保池大小至少为1
        self.page_pool: asyncio.Queue | None = None

        self._thread.start()
        self._is_running.wait()


    def set_speed_mode(self, enabled: bool):
        """
        从外部设置 Playwright 管理器的快速模式状态。
        """
        self._speed_mode_enabled = enabled
        if enabled:
            print("🔧 [Playwright Manager] 快速模式已开启。")
        else:
            print("🔧 [Playwright Manager] 快速模式已关闭。")

    def _run_loop(self):
        """后台线程的入口点，创建并运行事件循环。"""
        asyncio.run(self._main())

    async def _main(self):
        self._loop = asyncio.get_running_loop()
        self._is_running.set()
        
        # 将 future 保存为实例属性
        self._shutdown_future = self._loop.create_future()
        await self._shutdown_future

    def run_coroutine(self, coro):
        """
        【兼容性版本】保持原有同步接口，但使用较短超时避免长时间UI阻塞。
        """
        if not self._loop:
            raise RuntimeError("PlaywrightManager event loop is not running.")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        
        try:
            # 【UI响应性修复】使用较短超时时间，避免长时间UI阻塞
            return future.result(timeout=30)  # 从120秒减少到30秒
        except asyncio.TimeoutError:
            print(f"⚠️ 异步任务超时(30秒)，跳过以保持UI响应性")
            future.cancel()
            return None
        except Exception as e:
            print(f"❌ 异步任务执行失败: {e}")
            future.cancel()
            return None
    
    def run_coroutine_async(self, coro):
        """
        【新增】非阻塞版本，返回Future对象，不会阻塞UI线程。
        """
        if not self._loop:
            raise RuntimeError("PlaywrightManager event loop is not running.")
        
        return asyncio.run_coroutine_threadsafe(coro, self._loop)
        


    # 在 class PlaywrightManager 中，替换这个方法：
    async def _initialize_internal(self):
        """
        【死锁修复版】内部初始化方法。
        除了启动浏览器，还会创建N个浏览器页面并放入资源池。
        移除锁以避免死锁，使用状态检查来防止重复初始化。
        """
        if self.initialization_successful:
            return # 如果已经初始化成功，则直接返回，避免重复操作
            
        print("🚀 正在启动 Playwright 浏览器实例并创建页面资源池...")
        try:
            # 动态生成一个真实的Windows Chrome浏览器User-Agent
            ua = UserAgent(os='windows')
            ua_string = ua.chrome
            
            # 启动 Playwright 服务
            self._playwright = await async_playwright().start()

            # 准备浏览器启动选项
            launch_options = {
                'headless': True, 
                'args': ['--no-sandbox', '--disable-dev-shm-usage']
            }
            
            # 如果程序是在打包后（.exe）的环境中运行
            if getattr(sys, 'frozen', False):
                # 智能地寻找捆绑在程序包内的浏览器可执行文件
                executable_path = resource_path(os.path.join('ms-playwright', 'chromium-1187', 'chrome-win', 'chrome.exe'))
                if os.path.exists(executable_path):
                    launch_options['executable_path'] = executable_path
                else:
                    # 如果找不到，这是一个致命错误，无法继续
                    print(f"❌ [打包环境] 严重错误: 找不到捆绑的浏览器可执行文件！")
                    return

            # 启动Chromium浏览器实例
            self._browser = await self._playwright.chromium.launch(**launch_options)
            # 创建一个带有自定义User-Agent的、干净的浏览器上下文
            self._context = await self._browser.new_context(user_agent=ua_string)
            # 在上下文中注入反-反爬虫（stealth）脚本
            await self._apply_stealth_script()

            # --- 【核心新增】创建并填充页面池 ---
            # 创建一个异步队列作为我们的页面资源池，最大容量为 self.pool_size
            self.page_pool = asyncio.Queue(maxsize=self.pool_size)
            # 循环创建指定数量的浏览器页面，并逐个放入池中
            for i in range(self.pool_size):
                page = await self._context.new_page()
                await self.page_pool.put(page)
            print(f"  -> ✅ 已成功创建 {self.pool_size} 个浏览器页面的资源池。")
            # ------------------------------------
            
            # 标记初始化成功
            self.initialization_successful = True
            print("✅ Playwright 浏览器实例及页面池已准备就绪。")

        except Exception as e:
            # 如果在上述任何步骤中发生异常，打印详细错误并设置失败状态
            traceback.print_exc()
            print(f"❌ 启动 Playwright 失败: {e}")
            self._browser = None
            self.initialization_successful = False
    
    def is_available(self):
        """公开的检查方法，用于判断Playwright是否已成功初始化。"""
        return self.initialization_successful
    
    def _reset_shutdown_timer(self):
        """
        重置自动关闭的倒计时。
        每次浏览器被使用时都应该调用这个方法。
        """
        # 如果已经有一个关闭任务在计划中，先取消它
        if self.shutdown_timer:
            self.shutdown_timer.cancel()
        
        # 安排一个新的关闭任务
        self.shutdown_timer = self._loop.call_later(
            self.SHUTDOWN_DELAY,
            # call_later 不能直接调用协程，所以我们用 run_coroutine_threadsafe
            lambda: asyncio.run_coroutine_threadsafe(self._shutdown_internal(), self._loop)
        )
        print(f"ℹ️ Playwright 自动关闭倒计时已重置为 {self.SHUTDOWN_DELAY} 秒。")


    def initialize(self):
        if not self._loop or not self._loop.is_running():
            self._loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(target=self._start_event_loop, daemon=True)
            self._loop_thread.start()
        # 非阻塞提交，不等待结果
        asyncio.run_coroutine_threadsafe(self._initialize_internal(), self._loop)

    async def _shutdown_internal(self):
        """【并行修复版】关闭时需要清空并关闭池中的所有页面。"""
        print("🌙 正在关闭 Playwright 浏览器...")
        if self.shutdown_timer: self.shutdown_timer.cancel()
        
        # --- 【核心新增】关闭页面池中的所有页面 ---
        if self.page_pool:
            while not self.page_pool.empty():
                try:
                    page = self.page_pool.get_nowait()
                    await page.close()
                except (asyncio.QueueEmpty, Exception):
                    break
        # ------------------------------------

        if self._context: await self._context.close()
        if self._browser and self._browser.is_connected(): await self._browser.close()
        if self._playwright: await self._playwright.stop()
        
        self._browser = self._playwright = self._context = self.page_pool = None
        self.initialization_successful = False
        print("✅ Playwright 已安全关闭。")

    def shutdown(self):
        if self._loop and self._loop.is_running():
            async def shutdown_and_signal():
                # 1. 先执行原有的内部清理
                await self._shutdown_internal()
                # 2. 【核心】清理完毕后，设置 future 的结果来 unblock 后台线程
                if not self._shutdown_future.done():
                    self._shutdown_future.set_result(True)

            # 安排上面新定义的组合任务到后台循环中执行
            asyncio.run_coroutine_threadsafe(shutdown_and_signal(), self._loop)

    async def get_page_content(self, url: str) -> str | None:
        """
        【死锁修复版】从页面池中获取一个页面来执行抓取任务，用完后归还。
        添加了智能降级和资源监控机制。
        """
        if not self.is_available() or not self.page_pool:
            print("❌ Playwright 管理器或页面池未就绪，无法获取页面。")
            return None

        # 【智能资源管理】检查页面池可用性，如果没有空闲页面立即返回避免阻塞
        current_available = self.page_pool.qsize()
        if current_available == 0:
            print(f"⚠️ 页面池资源已满(0/{self.pool_size})，跳过请求: {url[:50]}...")
            print(f"💡 建议：如果频繁出现此消息，可考虑增加页面池大小或减少并发数")
            return None
        else:
            print(f"📊 页面池状态: {current_available}/{self.pool_size} 可用，处理: {url[:50]}...")

        self._reset_shutdown_timer()
        page = None
        try:
            # 【修复】从池中获取一个空闲页面，增加超时时间避免长时间等待
            page = await asyncio.wait_for(self.page_pool.get(), timeout=30.0)
            
            print(f"  -> [Playwright池] 页面已出队，正在访问: {url}")
            if self._speed_mode_enabled:
                await page.route("**/*", lambda route: route.abort() if route.request.resource_type in {"image", "stylesheet", "font", "media"} else route.continue_())

            await page.goto(url, timeout=20000, wait_until="domcontentloaded")
            content = await page.content()
            return content
        except asyncio.TimeoutError:
            print(f"⚠️ 页面池资源繁忙，获取页面超时 ({url})。跳过此请求以避免阻塞。")
            return None
        except Exception as e:
            print(f"❌ Playwright 访问页面时发生错误 ({url}): {e}")
            return None
        finally:
            if page:
                # 【修复】将页面归还到池中，供下一个任务使用
                if self._speed_mode_enabled:
                    await page.unroute("**/*") # 取消路由拦截
                await self.page_pool.put(page)
                print(f"  -> [Playwright池] 页面已归队，当前空闲: {self.page_pool.qsize()}/{self.pool_size}")


    # 浏览器伪装
    async def _apply_stealth_script(self):
        """
        一个自定义的、轻量级的stealth函数，用于覆盖常见的Playwright指纹特征。
        此方法将脚本注入到浏览器上下文中，后续所有新页面都会生效。
        """
        js_script = """
        (() => {
            // 1. 覆盖 navigator.webdriver 属性
            if (navigator.webdriver) {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            }

            // 2. 伪造 window.chrome 对象
            if (!window.chrome) {
                window.chrome = {};
            }
            if (window.chrome.runtime) {
                // 这是一个常见的检测标志
            }
            
            // 3. 伪造权限状态
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters)
            );

            // 4. 伪造插件信息
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
                ],
            });

            // 5. 伪造语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            // 6. 伪造 WebGL 指纹
            try {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    // UNMASKED_VENDOR_WEBGL 和 UNMASKED_RENDERER_WEBGL 是最常被查询的两个参数
                    if (parameter === 37445) { // UNMASKED_VENDOR_WEBGL
                        return 'Google Inc. (NVIDIA)'; // 伪装成NVIDIA显卡
                    }
                    if (parameter === 37446) { // UNMASKED_RENDERER_WEBGL
                        return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)';
                    }
                    return getParameter.apply(this, arguments);
                };
            } catch (e) {
                console.error('Failed to spoof WebGL:', e);
            }

            // 7. 保护函数 toString 方法
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === navigator.plugins.getter || this === navigator.languages.getter) {
                    return 'function get() { [native code] }';
                }
                if (this === WebGLRenderingContext.prototype.getParameter) {
                    return 'function getParameter() { [native code] }';
                }
                return originalToString.apply(this, arguments);
            };

            // 8.伪造 User-Agent Client Hints (品牌信息)
            if (navigator.userAgentData) {
                Object.defineProperty(navigator, 'userAgentData', {
                    get: () => ({
                        "brands": [
                            { "brand": "Google Chrome", "version": "124" },
                            { "brand": "Not-A.Brand", "version": "99" },
                            { "brand": "Chromium", "version": "124" }
                        ],
                        "mobile": false,
                        "platform": "Windows"
                    }),
                });
            }

            // 9. Canvas 指纹伪装
            try {
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {
                    // 在原始图像上添加微小的随机噪声
                    const ctx = this.getContext('2d');
                    if (ctx) {
                        // 随机选择一个角落
                        const shift = {
                            'r': Math.floor(Math.random() * 10) - 5,
                            'g': Math.floor(Math.random() * 10) - 5,
                            'b': Math.floor(Math.random() * 10) - 5,
                            'a': Math.floor(Math.random() * 10) - 5
                        };
                        const width = this.width;
                        const height = this.height;
                        const imageData = ctx.getImageData(0, 0, width, height);
                        for (let i = 0; i < height; i++) {
                            for (let j = 0; j < width; j++) {
                                const n = ((i * width) + j) * 4;
                                imageData.data[n + 0] = imageData.data[n + 0] + shift.r;
                                imageData.data[n + 1] = imageData.data[n + 1] + shift.g;
                                imageData.data[n + 2] = imageData.data[n + 2] + shift.b;
                                imageData.data[n + 3] = imageData.data[n + 3] + shift.a;
                            }
                        }
                        ctx.putImageData(imageData, 0, 0);
                    }
                    // 返回被修改后的图像数据
                    return originalToDataURL.apply(this, arguments);
                };
            } catch(e) {
                console.error('Failed to spoof Canvas fingerprint:', e);
            }

        })();
        """
        
        # 使用 add_init_script 将脚本注入到默认的浏览器上下文中
        # self._browser.contexts[0] 指的是浏览器启动时创建的第一个（也是默认的）上下文
        if self._context:
            await self._context.add_init_script(js_script)
            print("✅ 已成功应用自定义的 stealth 伪装脚本。")
        else:
            print("❌ 无法应用伪装脚本：浏览器或上下文不存在。")


    async def check_element_exists(self, url: str, selector: str) -> bool:
        """
        访问一个URL，并检查是否存在指定的CSS选择器对应的元素。
        返回: True (如果存在) 或 False (如果不存在或出错)。
        """
        if not self._context:
            print("❌ Playwright 上下文未初始化，无法检查元素。")
            return False

        # 这个方法不应该重置自动关闭计时器，因为它本身就是被其他任务调用的
        # self._reset_shutdown_timer() 

        try:
            async def perform_check():
                page = await self._context.new_page()
                print(f"🕵️ [Playwright] 正在检查元素 '{selector}' @ {url}")
                try:
                    # 使用 'load' 状态，等待页面资源（包括图片）加载
                    await page.goto(url, timeout=15000, wait_until="load")
                    
                    # 使用 locator().count() 来检查元素数量，这是检查存在性的推荐方法
                    count = await page.locator(selector).count()
                    return count > 0
                except Exception as e:
                    print(f"❌ Playwright 检查元素时出错: {e}")
                    return False
                finally:
                    await page.close()

            # 设置一个总的操作超时
            return await asyncio.wait_for(perform_check(), timeout=20.0)
        except asyncio.TimeoutError:
            print(f"❌ Playwright 检查元素总超时 ({url})")
            return False
        except Exception as e:
            print(f"❌ Playwright check_element_exists 发生未知错误: {e}")
            return False
class AIStatusChecker(QThread):
    """在后台检查AI状态的线程"""
    status_ready = pyqtSignal(dict) # 定义一个信号，完成后发射结果

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.api_url = "https://mediamingle.cn/.netlify/functions/check-ai-status"

    def run(self):
        result = {"success": False, "message": "未知错误"}
        if not self.user_id:
            result["message"] = "用户ID无效"
            self.status_ready.emit(result)
            return
        try:
            params = {"user_id": self.user_id}
            response = requests.get(self.api_url, params=params, timeout=10)
            if response.status_code == 200:
                result = response.json()
            else:
                result["message"] = f"服务器错误: HTTP {response.status_code}"
        except Exception as e:
            result["message"] = f"网络请求异常: {e}"

        self.status_ready.emit(result)


# =====================================================================
# 自定义标题栏 (保持功能不变，微调样式)
# =====================================================================
class CustomTitleBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_dialog = parent
        self.setFixedHeight(40) # 稍微增加标题栏高度

        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(15, 0, 15, 0) # 增加左右边距
        self.layout.setSpacing(10) # 增加按钮间距
        self.layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        # 窗口标题/图标
        self.title_label = QLabel("谷歌地图拓客") # 更专业的标题
        self.title_label.setStyleSheet("color: #ecf0f1; font-size: 15px; font-weight: bold; letter-spacing: 1px;") # 更亮的文字颜色
        self.layout.addWidget(self.title_label)
        self.layout.addStretch()

        # 帮助按钮
        self.help_button = QPushButton("?")
        self.help_button.setFixedSize(30, 30) # 增大按钮尺寸
        self.help_button.clicked.connect(self.show_help)
        self.help_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.2);
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.4);
            }
        """)
        self.layout.addWidget(self.help_button)

        # 关闭按钮
        self.close_button = QPushButton("X")
        self.close_button.setFixedSize(30, 30) # 增大按钮尺寸
        self.close_button.clicked.connect(self.close_parent_dialog)
        self.close_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                border-radius: 15px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.layout.addWidget(self.close_button)

        self.start_pos = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.globalPos() - self.parent_dialog.pos()

    def mouseMoveEvent(self, event):
        if self.start_pos is not None:
            self.parent_dialog.move(event.globalPos() - self.start_pos)

    def mouseReleaseEvent(self, event):
        self.start_pos = None

    def close_parent_dialog(self):
        if self.parent_dialog:
            self.parent_dialog.reject()

    def show_help(self):
        QMessageBox.information(self, "帮助", "如果您遇到登录问题，请联系管理员或查阅帮助文档。")


# 一个用于设置要抓取哪些社交媒体平台的对话框
# (请用下面的整个类，替换掉您代码中旧的 class SocialMediaDialog)
class SocialMediaDialog(QDialog):
    """一个用于设置要抓取哪些社交媒体平台的对话框"""
    # 定义一个新信号，用于在点击登录按钮时通知主窗口
    request_whatsapp_login = pyqtSignal()

    # def __init__(self, current_settings, parent=None):
    #     super().__init__(parent)
    #     self.setWindowTitle("拓客设置")
    #     self.setMinimumWidth(400)
    #     self.setModal(True)

    #     self.layout = QVBoxLayout(self)
    #     self.layout.setContentsMargins(20, 20, 20, 20)
    #     self.layout.setSpacing(15)

    #     # --- 社交媒体链接提取设置 ---
    #     social_group = QGroupBox("提取以下社交媒体链接")
    #     social_layout = QVBoxLayout()
    #     self.cb_facebook = QCheckBox("Facebook")
    #     self.cb_instagram = QCheckBox("Instagram")
    #     self.cb_linkedin = QCheckBox("LinkedIn")
    #     self.cb_facebook.setChecked(current_settings.get('social_platforms', {}).get('facebook', True))
    #     self.cb_instagram.setChecked(current_settings.get('social_platforms', {}).get('instagram', True))
    #     self.cb_linkedin.setChecked(current_settings.get('social_platforms', {}).get('linkedin', True))
    #     social_layout.addWidget(self.cb_facebook)
    #     social_layout.addWidget(self.cb_instagram)
    #     social_layout.addWidget(self.cb_linkedin)
    #     social_group.setLayout(social_layout)
    #     self.layout.addWidget(social_group)

    #     # --- WhatsApp 号码验证模式设置 ---
    #     whatsapp_group = QGroupBox("WhatsApp 号码验证模式")
    #     whatsapp_layout = QVBoxLayout()
    #     self.rb_wa_off = QRadioButton("关闭 (不验证)")
    #     self.rb_wa_standard = QRadioButton("标准验证 (快速, 成功率较低)")
    #     self.rb_wa_advanced = QRadioButton("高级验证 (需扫码登录, 成功率高)")
    #     self.login_wa_button = QPushButton("扫码登录 WhatsApp")
    #     self.login_wa_button.clicked.connect(self.request_whatsapp_login.emit)
    #     self.login_wa_button.setToolTip("点击后将打开浏览器，请使用手机WhatsApp扫码登录。\n登录状态会自动保存，只需操作一次。")
    #     whatsapp_layout.addWidget(self.rb_wa_off)
    #     whatsapp_layout.addWidget(self.rb_wa_standard)
    #     whatsapp_layout.addWidget(self.rb_wa_advanced)
    #     whatsapp_layout.addSpacing(10)
    #     whatsapp_layout.addWidget(self.login_wa_button)
    #     whatsapp_group.setLayout(whatsapp_layout)
    #     self.layout.addWidget(whatsapp_group)
    #     current_wa_mode = current_settings.get('whatsapp_mode', 'off')
    #     if current_wa_mode == 'standard': self.rb_wa_standard.setChecked(True)
    #     elif current_wa_mode == 'advanced': self.rb_wa_advanced.setChecked(True)
    #     else: self.rb_wa_off.setChecked(True)
    #     self.login_wa_button.setEnabled(self.rb_wa_advanced.isChecked())
    #     self.rb_wa_advanced.toggled.connect(self.login_wa_button.setEnabled)


    #     # --- 【【【新增功能】】】Playwright 强力模式设置 ---
    #     power_mode_group = QGroupBox("采集策略")
    #     power_mode_layout = QVBoxLayout()
    #     self.cb_playwright_fallback = QCheckBox("启用 Playwright 强力模式")
    #     self.cb_playwright_fallback.setToolTip(
    #         "勾选后，当遇到网站反爬虫(403错误)时，\n"
    #         "程序会自动调用后台浏览器(Playwright)进行强力重试。\n"
    #         "这会显著提高成功率，但也会消耗更多CPU和内存，可能导致卡顿。\n"
    #         "如果您的电脑性能较好，建议保持开启。"
    #     )
    #     # 从传入的设置中获取初始状态，如果没设置过，则默认为开启(True)
    #     self.cb_playwright_fallback.setChecked(current_settings.get('enable_playwright_fallback', True))
    #     power_mode_layout.addWidget(self.cb_playwright_fallback)
    #     power_mode_group.setLayout(power_mode_layout)
    #     self.layout.addWidget(power_mode_group)


    #     # --- 【【【新增功能】】】界面特效设置 ---
    #     effects_group = QGroupBox("界面特效")
    #     effects_layout = QVBoxLayout()
    #     self.cb_click_animation = QCheckBox("启用点击动画特效 (圈圈)")
    #     self.cb_click_animation.setToolTip(
    #         "勾选后，每次成功点击并提取商家信息时，\n"
    #         "会在详情面板区域播放一个扩散的圆圈动画。\n"
    #         "如果不喜欢这个特效，可以取消勾选。"
    #     )
    #     # 从传入的设置中获取初始状态，如果没设置过，则默认为开启(True)
    #     self.cb_click_animation.setChecked(current_settings.get('enable_click_animation', True))
    #     effects_layout.addWidget(self.cb_click_animation)
    #     effects_group.setLayout(effects_layout)
    #     self.layout.addWidget(effects_group)

    #     # --- 【新增功能】搜索精度设置 ---
    #     precision_group = QGroupBox("虚拟网格扫描精度 (值越小越精细，但越慢)")
    #     precision_layout = QHBoxLayout()
    #     self.precision_slider = QSlider(Qt.Horizontal)
    #     self.precision_slider.setRange(5, 50)  # 代表 0.5 到 5.0
    #     self.precision_slider.setSingleStep(1)
    #     self.precision_slider.setTickInterval(5)
    #     self.precision_slider.setTickPosition(QSlider.TicksBelow)
    #     self.precision_label = QLabel()
    #     self.precision_label.setFixedWidth(40)
    #     precision_layout.addWidget(self.precision_slider)
    #     precision_layout.addWidget(self.precision_label)
    #     precision_group.setLayout(precision_layout)
    #     self.layout.addWidget(precision_group)


    #     # 连接滑块信号并初始化
    #     self.precision_slider.valueChanged.connect(self.update_precision_label)
    #     current_precision = current_settings.get('grid_spacing', 1.0)
    #     self.precision_slider.setValue(int(current_precision * 10))
    #     self.update_precision_label(int(current_precision * 10))
    #     # --- 新增结束 ---


    #     # --- 【新增功能】并行采集设置 ---
    #     parallel_group = QGroupBox("并行采集设置 (实验性功能)")
    #     parallel_layout = QHBoxLayout()
    #     self.parallel_spinbox = QSpinBox()
    #     self.parallel_spinbox.setRange(1, 5) # 允许1-5个并行任务
    #     self.parallel_spinbox.setSuffix(" 个页面")
    #     self.parallel_spinbox.setToolTip("设置同时打开多少个谷歌地图页面进行采集。\n数量越多对网络和电脑性能要求越高。\n默认为1，即单页面模式。")
    #     parallel_layout.addWidget(QLabel("同时开启页面数量:"))
    #     parallel_layout.addWidget(self.parallel_spinbox)
    #     parallel_group.setLayout(parallel_layout)
    #     self.layout.addWidget(parallel_group)

    #     # 初始化
    #     current_parallel_count = current_settings.get('parallel_tasks', 1)
    #     self.parallel_spinbox.setValue(current_parallel_count)



    #     # --- 底部按钮 ---
    #     self.layout.addStretch()
    #     button_layout = QHBoxLayout()
    #     self.ok_button = QPushButton("确定")
    #     self.cancel_button = QPushButton("取消")
    #     button_layout.addStretch()
    #     button_layout.addWidget(self.ok_button)
    #     button_layout.addWidget(self.cancel_button)
    #     self.layout.addLayout(button_layout)
    #     self.ok_button.clicked.connect(self.accept)
    #     self.cancel_button.clicked.connect(self.reject)


    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("拓客设置")
        self.setMinimumWidth(400)
        self.setModal(True)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(20, 20, 20, 20)
        self.layout.setSpacing(15)

        # --- 社交媒体链接提取设置 (保持不变) ---
        social_group = QGroupBox("提取以下社交媒体链接")
        social_layout = QVBoxLayout()
        self.cb_facebook = QCheckBox("Facebook")
        self.cb_instagram = QCheckBox("Instagram")
        self.cb_linkedin = QCheckBox("LinkedIn")
        self.cb_facebook.setChecked(current_settings.get('social_platforms', {}).get('facebook', True))
        self.cb_instagram.setChecked(current_settings.get('social_platforms', {}).get('instagram', True))
        self.cb_linkedin.setChecked(current_settings.get('social_platforms', {}).get('linkedin', True))
        social_layout.addWidget(self.cb_facebook)
        social_layout.addWidget(self.cb_instagram)
        social_layout.addWidget(self.cb_linkedin)
        social_group.setLayout(social_layout)
        self.layout.addWidget(social_group)

        # --- WhatsApp 号码验证模式设置 (保持不变) ---
        whatsapp_group = QGroupBox("WhatsApp 号码验证模式")
        whatsapp_layout = QVBoxLayout()
        self.rb_wa_off = QRadioButton("关闭 (不验证)")
        self.rb_wa_standard = QRadioButton("标准验证 (快速, 成功率较低)")
        self.rb_wa_advanced = QRadioButton("高级验证 (需扫码登录, 成功率高)")
        self.login_wa_button = QPushButton("扫码登录 WhatsApp")
        self.login_wa_button.clicked.connect(self.request_whatsapp_login.emit)
        self.login_wa_button.setToolTip("点击后将打开浏览器，请使用手机WhatsApp扫码登录。\n登录状态会自动保存，只需操作一次。")
        whatsapp_layout.addWidget(self.rb_wa_off)
        whatsapp_layout.addWidget(self.rb_wa_standard)
        whatsapp_layout.addWidget(self.rb_wa_advanced)
        whatsapp_layout.addSpacing(10)
        whatsapp_layout.addWidget(self.login_wa_button)
        whatsapp_group.setLayout(whatsapp_layout)
        self.layout.addWidget(whatsapp_group)
        current_wa_mode = current_settings.get('whatsapp_mode', 'off')
        if current_wa_mode == 'standard': self.rb_wa_standard.setChecked(True)
        elif current_wa_mode == 'advanced': self.rb_wa_advanced.setChecked(True)
        else: self.rb_wa_off.setChecked(True)
        self.login_wa_button.setEnabled(self.rb_wa_advanced.isChecked())
        self.rb_wa_advanced.toggled.connect(self.login_wa_button.setEnabled)


        # --- 采集策略设置 (修改：增加推荐值标签) ---
        power_mode_group = QGroupBox("采集策略")
        power_mode_layout = QVBoxLayout()
        self.cb_playwright_fallback = QCheckBox("启用 Playwright 强力模式")
        self.cb_playwright_fallback.setToolTip("勾选后，当遇到网站反爬虫(403错误)时，\n程序会自动调用后台浏览器(Playwright)进行强力重试。\n这会显著提高成功率，但也会消耗更多CPU和内存，可能导致卡顿。\n如果您的电脑性能较好，建议保持开启。")
        self.cb_playwright_fallback.setChecked(current_settings.get('enable_playwright_fallback', True))
        power_mode_layout.addWidget(self.cb_playwright_fallback)

        parallel_pw_layout = QHBoxLayout()
        self.pw_pool_spinbox = QSpinBox()
        self.pw_pool_spinbox.setRange(1, 5)
        self.pw_pool_spinbox.setSuffix(" 个")
        self.pw_pool_spinbox.setToolTip("设置在“强力模式”下，最多同时运行多少个后台浏览器实例。\n数量越多速度越快，但对电脑性能要求越高。\n如果遇到卡顿，请将此值设为 1。")
        parallel_pw_layout.addWidget(QLabel("Playwright 并行数:"))
        parallel_pw_layout.addWidget(self.pw_pool_spinbox)
        
        # --- ▼▼▼ 【【【新增UI提示标签】】】 ▼▼▼ ---
        auto_pw_pool_size = current_settings.get('auto_playwright_pool_size', 1)
        recommend_pw_label = QLabel(f"（系统推荐: {auto_pw_pool_size}）")
        recommend_pw_label.setStyleSheet("color: #888; font-weight: normal;") # 设置为灰色普通字体
        parallel_pw_layout.addWidget(recommend_pw_label)
        parallel_pw_layout.addStretch()
        # --- ▲▲▲ 新增结束 ▲▲▲ ---

        power_mode_layout.addLayout(parallel_pw_layout)
        power_mode_group.setLayout(power_mode_layout)
        self.layout.addWidget(power_mode_group)
        current_pool_size = current_settings.get('playwright_pool_size', 1)
        self.pw_pool_spinbox.setValue(current_pool_size)


        # --- 界面特效设置 (保持不变) ---
        effects_group = QGroupBox("界面特效")
        effects_layout = QVBoxLayout()
        self.cb_click_animation = QCheckBox("启用点击动画特效 (圈圈)")
        self.cb_click_animation.setToolTip("勾选后，每次成功点击并提取商家信息时，\n会在详情面板区域播放一个扩散的圆圈动画。\n如果不喜欢这个特效，可以取消勾选。")
        self.cb_click_animation.setChecked(current_settings.get('enable_click_animation', True))
        effects_layout.addWidget(self.cb_click_animation)
        effects_group.setLayout(effects_layout)
        self.layout.addWidget(effects_group)

        # --- 搜索精度设置 (保持不变) ---
        precision_group = QGroupBox("虚拟网格扫描精度 (值越小越精细，但越慢)")
        precision_layout = QHBoxLayout()
        self.precision_slider = QSlider(Qt.Horizontal)
        self.precision_slider.setRange(5, 50)
        self.precision_slider.setSingleStep(1)
        self.precision_slider.setTickInterval(5)
        self.precision_slider.setTickPosition(QSlider.TicksBelow)
        self.precision_label = QLabel()
        self.precision_label.setFixedWidth(40)
        precision_layout.addWidget(self.precision_slider)
        precision_layout.addWidget(self.precision_label)
        precision_group.setLayout(precision_layout)
        self.layout.addWidget(precision_group)
        self.precision_slider.valueChanged.connect(self.update_precision_label)
        current_precision = current_settings.get('grid_spacing', 1.0)
        self.precision_slider.setValue(int(current_precision * 10))
        self.update_precision_label(int(current_precision * 10))

        # --- 并行采集设置 (修改：增加推荐值标签) ---
        parallel_group = QGroupBox("并行采集设置 (实验性功能)")
        parallel_layout = QHBoxLayout()
        self.parallel_spinbox = QSpinBox()
        self.parallel_spinbox.setRange(1, 5)
        self.parallel_spinbox.setSuffix(" 个页面")
        self.parallel_spinbox.setToolTip("设置同时打开多少个谷歌地图页面进行采集。\n数量越多对网络和电脑性能要求越高。")
        parallel_layout.addWidget(QLabel("同时开启页面数量:"))
        parallel_layout.addWidget(self.parallel_spinbox)
        
        # --- ▼▼▼ 【【【新增UI提示标签】】】 ▼▼▼ ---
        auto_parallel_tasks = current_settings.get('auto_parallel_tasks', 1)
        recommend_tasks_label = QLabel(f"（系统推荐: {auto_parallel_tasks}）")
        recommend_tasks_label.setStyleSheet("color: #888; font-weight: normal;")
        parallel_layout.addWidget(recommend_tasks_label)
        parallel_layout.addStretch()
        # --- ▲▲▲ 新增结束 ▲▲▲ ---

        parallel_group.setLayout(parallel_layout)
        self.layout.addWidget(parallel_group)
        current_parallel_count = current_settings.get('parallel_tasks', 1)
        self.parallel_spinbox.setValue(current_parallel_count)

        # --- 底部按钮 (保持不变) ---
        self.layout.addStretch()
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("确定")
        self.cancel_button = QPushButton("取消")
        button_layout.addStretch()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        self.layout.addLayout(button_layout)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def update_precision_label(self, value):
        """【新增】当滑块值改变时，更新右侧的文本标签"""
        float_value = value / 10.0
        self.precision_label.setText(f"{float_value:.1f}")

    def get_settings(self):
        """【修改】返回所有设置，包含新增的动画特效开关"""
        wa_mode = 'off'
        if self.rb_wa_standard.isChecked(): wa_mode = 'standard'
        elif self.rb_wa_advanced.isChecked(): wa_mode = 'advanced'
            
        return {
            'social_platforms': {
                'facebook': self.cb_facebook.isChecked(),
                'instagram': self.cb_instagram.isChecked(),
                'linkedin': self.cb_linkedin.isChecked(),
            },
            'whatsapp_mode': wa_mode,
            'grid_spacing': self.precision_slider.value() / 10.0,
            'parallel_tasks': self.parallel_spinbox.value(),
            'enable_playwright_fallback': self.cb_playwright_fallback.isChecked(),
            'enable_click_animation': self.cb_click_animation.isChecked() # 【新增】返回新复选框的状态
        }

# =====================================================================
# 登录对话框类 (美化版 - 更具艺术感)
# =====================================================================
class LoginDialog(QDialog):
    # 新增常量：设备码存储文件路径 和 后端API基地址
    USER_CONFIG_FILE = get_app_data_path("user_config.json")
    BACKEND_API_BASE_URL = "https://mediamingle.cn/.netlify/functions/receivingClient"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("安全登录") # 再次统一标题
        icon_path = resource_path(r"img/icon/谷歌地图.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(800, 480) # 进一步增大窗口尺寸，黄金比例感觉

        try:
            screen_center = QApplication.primaryScreen().availableGeometry().center()
            self.move(screen_center - self.rect().center())
        except Exception as e:
            # 这里的提示可以更具体一些
            print(f"登录窗口居中失败: {e}")

        self.setModal(True)
        self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
        self.device_data = self._load_config_data()
        self.logged_in_user_id = None
        # =====================================================================
        # 整体对话框样式 (背景渐变和圆角)
        # =====================================================================
        self.setStyleSheet("""
            LoginDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                            stop:0 #6a11cb, stop:1 #2575fc); /* 更有活力的紫蓝色渐变 */
                border-radius: 3px; /* 更大的圆角，更柔和 */
                border: 2px solid rgba(255, 255, 255, 0.2); /* 细微白色边框，增强玻璃感 */
            }
            /* 登录表单容器样式 */
            QWidget#loginFormContainer {
                background-color: rgba(255, 255, 255, 0.98); /* 几乎不透明的白色，略微磨砂感 */
                border-radius: 3px; /* 圆角略小于主窗口 */
                padding: 40px; /* 增加内边距，提供更多留白 */
                /* 可以尝试添加 QGraphicsDropShadowEffect 到这个容器来模拟内部阴影 */
            }
            QLabel#mainTitleLabel { /* 主标题，与CustomTitleBar里的区分开 */
                color: #2c3e50;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                font-size: 20px; /* 更大的主标题字号 */
                font-weight: bold;
                text-align: center;
                margin-bottom: 30px;
                letter-spacing: 1.5px; /* 增加字母间距 */
            }
            QLineEdit {
                padding: 18px 25px; /* 再次增加内边距 */
                border: 1px solid #e0e0e0; /* 更浅的边框 */
                border-radius: 3px; /* 更大的圆角 */
                font-size: 18px;
                background-color: #ffffff;
                color: #333333;
                font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                /* text-indent: 40px; /* 为图标预留空间，需要结合Python代码放置图标 */
            }
            QLineEdit:focus {
                border-color: #6a11cb; /* 与主背景渐变色呼应的焦点边框 */
            }
            QPushButton#loginButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #4a90e2, stop:1 #2575fc); /* 按钮使用主背景渐变色，呼应整体 */
                color: white;
                padding: 18px;
                border-radius: 3px;
                font-size: 22px; /* 更大的按钮文字 */
                font-weight: bold;
                border: none;
                margin-top: 30px; /* 增加按钮上方间距 */
                letter-spacing: 3px;
                outline: none;
            }
            QPushButton#loginButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #3b7ad6, stop:1 #1e5fc2); /* 悬停颜色稍深 */
            }
            QPushButton#loginButton:pressed {
                background-color: #1a4f9e;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                            stop:0 #2a6ecb, stop:1 #1551b8);
            }
            QLabel#errorLabel {
                color: #e74c3c;
                font-size: 16px;
                margin-top: 10px;
                margin-bottom: 10px;
                font-weight: bold;
                text-align: center;
            }
        """)

        main_v_layout = QVBoxLayout(self)
        main_v_layout.setContentsMargins(0, 0, 0, 0)
        main_v_layout.setSpacing(0)

        # 自定义标题栏
        self.title_bar = CustomTitleBar(self)
        self.title_bar.setStyleSheet("background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #6a11cb, stop:1 #2575fc); border-top-left-radius: 25px; border-top-right-radius: 25px;")
        main_v_layout.addWidget(self.title_bar)


        # 内容区域 (左右布局)
        content_h_layout = QHBoxLayout()
        content_h_layout.setContentsMargins(0, 0, 0, 0)
        content_h_layout.setSpacing(0)

        # 左侧图片区域
        self.image_label = QLabel(self)
        image_path = resource_path(r"img/background/starry_sky_background.jpg") # 假设您有这张图，请替换为您的实际图片路径
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # 缩放图片以适应窗口，保持长宽比
            # 这里使用 Qt.IgnoreAspectRatio 来让图片填充整个区域，可能会裁剪边缘
            scaled_pixmap = pixmap.scaled(self.size().width() // 2, self.height() - self.title_bar.height(),
                                          Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setScaledContents(True) # 确保图片内容能被缩放以填充 QLabel
            self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        else:
            self.image_label.setText("")
            self.image_label.setStyleSheet("background-color: #34495e; color: #ecf0f1; font-size: 20px; text-align: center;")
            self.image_label.setAlignment(Qt.AlignCenter)

        # 固定左侧宽度为总宽度的一半，并加入到布局
        self.image_label.setFixedWidth(self.width() // 2)
        content_h_layout.addWidget(self.image_label)

        # 右侧登录表单容器 (使用 QWidget 包装以便应用样式)
        login_form_container = QWidget(self)
        login_form_container.setObjectName("loginFormContainer")
        login_form_layout = QVBoxLayout(login_form_container)
        login_form_layout.setContentsMargins(40, 40, 40, 40) # 增加内部边距
        login_form_layout.setSpacing(25) # 增加控件间距

        # 标题
        self.main_title_label = QLabel("安全登录", login_form_container)
        self.main_title_label.setObjectName("mainTitleLabel") # 新的对象名，与CustomTitleBar里的区分开
        login_form_layout.addWidget(self.main_title_label, alignment=Qt.AlignCenter)

        # 用户名输入框 (带图标)
        self.username_input = QLineEdit(login_form_container)
        self.username_input.setPlaceholderText("请输入用户名")
        self.username_input.setText("")
        self.set_lineedit_icon(self.username_input, resource_path(r"img/icon/用户图标.png"))

        # 密码输入框 (带图标)
        self.password_input = QLineEdit(login_form_container)
        self.password_input.setPlaceholderText("请输入密码")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setText("")
        self.set_lineedit_icon(self.password_input, resource_path(r"img/icon/密码.png"))

        # 创建密码可见性切换按钮
        self.toggle_password_btn = QPushButton(self.password_input)
        self.toggle_password_btn.setCursor(Qt.PointingHandCursor)

        # 准备两种状态的图标
        show_icon_path = resource_path(r"img/icon/显示密码.png")
        hide_icon_path = resource_path(r"img/icon/不显示密码.png")

        if os.path.exists(show_icon_path) and os.path.exists(hide_icon_path):
            self.show_icon = QIcon(show_icon_path)
            self.hide_icon = QIcon(hide_icon_path)
            self.toggle_password_btn.setIcon(self.hide_icon)
            self.toggle_password_btn.setIconSize(QSize(22, 22)) # 设置图标大小
        else:
            # 如果图标文件不存在，使用文本代替
            self.toggle_password_btn.setText("👁")
            print("⚠️ 警告：密码可见性切换图标未找到，请检查路径。")

        self.toggle_password_btn.setFixedSize(30, 30) # 按钮大小
        self.toggle_password_btn.setStyleSheet("background: transparent; border: none;") # 透明无边框

        self.toggle_password_btn.clicked.connect(self.toggle_password_visibility)
        
        # 为右侧按钮留出空间
        # 原来 set_lineedit_icon 中设置了左边距，这里我们调整右边距
        left_margin, _, _, _ = self.password_input.getTextMargins()
        self.password_input.setTextMargins(left_margin, 0, 35, 0)

        # 错误信息标签
        self.error_label = QLabel("", login_form_container)
        self.error_label.setObjectName("errorLabel")
        self.error_label.setAlignment(Qt.AlignCenter)
        self.error_label.hide()

        # 登录按钮
        self.login_btn = QPushButton("登 录")
        self.login_btn.setObjectName("loginButton")
        self.login_btn.setCursor(Qt.PointingHandCursor)
        self.login_btn.clicked.connect(self.handle_login)

        login_form_layout.addWidget(self.username_input)
        login_form_layout.addWidget(self.password_input)
        login_form_layout.addWidget(self.error_label)
        login_form_layout.addWidget(self.login_btn)

        self.register_button = QPushButton("还没有账号？立即注册")
        self.register_button.setStyleSheet("background-color: transparent; border: none; color: #2563eb; text-decoration: underline;")
        self.register_button.clicked.connect(self.open_register_dialog)
        login_form_layout.addWidget(self.register_button)

        content_h_layout.addWidget(login_form_container, stretch=1)

        main_v_layout.addLayout(content_h_layout)

        self.setLayout(main_v_layout)

        

        # 为整个对话框添加阴影效果
        self.shadow = QGraphicsDropShadowEffect(self)
        self.shadow.setBlurRadius(40) # 更大的模糊半径
        self.shadow.setXOffset(0)
        self.shadow.setYOffset(15) # 更明显的下偏移，增强立体感
        self.shadow.setColor(Qt.black)
        self.setGraphicsEffect(self.shadow)
        
        # 在UI完全设置好后，尝试加载并填充已保存的用户信息
        self.load_and_fill_credentials()

    

    # 从本地文件加载最后一次登录的用户信息并填充输入框
    def load_and_fill_credentials(self):
        """从本地文件加载最后一次登录的用户信息并填充输入框"""
        config = self._load_config_data()
        last_user = config.get("last_login_user")
        
        if last_user and last_user in config.get("users", {}):
            user_data = config["users"][last_user]
            password_encoded = user_data.get("password")
            
            self.username_input.setText(last_user)
            
            if password_encoded:
                try:
                    # 使用 Base64 解码密码
                    password_decoded = base64.b64decode(password_encoded.encode('utf-8')).decode('utf-8')
                    self.password_input.setText(password_decoded)
                except (ValueError, TypeError, base64.binascii.Error) as e:
                    print(f"❌ 密码解码失败: {e}，密码框将留空。")
                    self.password_input.setText("")

    def set_lineedit_icon(self, line_edit, icon_path):
        """为 QLineEdit 设置左侧图标"""
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path)
            # 缩放图标以适应输入框高度
            scaled_icon = icon_pixmap.scaled(QSize(24, 24), Qt.KeepAspectRatio, Qt.SmoothTransformation)

            icon_label = QLabel(line_edit)
            icon_label.setPixmap(scaled_icon)
            icon_label.setStyleSheet("background-color: transparent;") # 确保背景透明

            # 将图标放置在输入框内部的左侧
            # 需要调整输入框的文本缩进，使其不与图标重叠
            line_edit.setTextMargins(35, 0, 0, 0) # 左侧留出图标空间

            # 计算图标位置
            # icon_label 的位置相对于 line_edit 的左上角
            # 这里简单的垂直居中，水平偏移 8 像素
            icon_label.setGeometry(8, (line_edit.height() - scaled_icon.height()) // 2,
                                   scaled_icon.width(), scaled_icon.height())
            line_edit.repaint() # 确保重绘以显示图标

            # 绑定 resizeEvent 确保图标在输入框大小变化时重新定位
            line_edit.installEventFilter(self) # 需要在 LoginDialog 类中实现 eventFilter

    # 切换密码可见性的槽函数
    def toggle_password_visibility(self):
        """切换密码输入框的显示模式 (文本/密码) 并更新图标"""
        if self.password_input.echoMode() == QLineEdit.Password:
            # 当前是隐藏状态，将要变为显示状态
            self.password_input.setEchoMode(QLineEdit.Normal)
            if hasattr(self, 'show_icon'):
                # 状态变为“显示”，图标也用“显示”图标
                self.toggle_password_btn.setIcon(self.show_icon) 
            else:
                self.toggle_password_btn.setText("🙈") # 无图标时的备用文本
        else:
            # 当前是显示状态，将要变为隐藏状态
            self.password_input.setEchoMode(QLineEdit.Password)
            if hasattr(self, 'hide_icon'):
                # 状态变为“隐藏”，图标也用“隐藏”图标
                self.toggle_password_btn.setIcon(self.hide_icon)
            else:
                self.toggle_password_btn.setText("👁") # 无图标时的备用文本

        

    def eventFilter(self, obj, event):
        """事件过滤器，用于处理 QLineEdit 的 resizeEvent 来更新图标和按钮位置"""
        if isinstance(obj, QLineEdit) and event.type() == event.Resize:
            # 找到并定位所有子控件
            for child in obj.children():
                if isinstance(child, QLabel) and child.pixmap():  # 左侧图标
                    scaled_icon_height = child.pixmap().height()
                    child.setGeometry(8, (obj.height() - scaled_icon_height) // 2,
                                      child.pixmap().width(), scaled_icon_height)
                elif isinstance(child, QPushButton):  # 右侧按钮
                    button_size = child.size()
                    obj_size = obj.size()
                    # 将按钮定位在输入框内部的右侧，并垂直居中
                    child.move(obj_size.width() - button_size.width() - 8,
                               (obj_size.height() - button_size.height()) // 2)
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 重新缩放图片以适应新的窗口尺寸
        image_path = r"img/login_art_bg.jpg" # 确保这个图片存在！
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # 根据 image_label 的实际尺寸进行缩放
            scaled_pixmap = pixmap.scaled(self.image_label.size(),
                                          Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
            self.image_label.setPixmap(scaled_pixmap)

        # 确保图片区域的宽度在窗口改变时也更新
        self.image_label.setFixedWidth(self.width() // 2)




    # 设备码管理相关方法
    def _load_config_data(self):
        """从本地文件加载完整的配置信息（包括设备和凭据）"""
        if os.path.exists(self.USER_CONFIG_FILE):
            try:
                # 必须显式指定 encoding='utf-8'
                with open(self.USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 配置文件 {self.USER_CONFIG_FILE} 格式错误，将创建新文件。")
                return {} 
        return {}
    
    def _save_config_data(self, data):
        """将完整的配置信息保存到本地文件"""
        try:
            # 写入时同样必须显式指定 encoding='utf-8'
            with open(self.USER_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"❌ 无法保存配置文件 {self.USER_CONFIG_FILE}: {e}")

    def _get_device_id_for_user(self, username):
        """获取指定用户的设备码"""
        config = self._load_config_data()
        return config.get("users", {}).get(username, {}).get("device_id")
    
    def _save_user_credentials_and_device_id(self, username, password, device_id):
        """保存或更新用户的凭据和设备ID，并将其设为最后登录用户"""
        config = self._load_config_data()
        
        # 对密码进行 Base64 编码
        password_encoded = base64.b64encode(password.encode('utf-8')).decode('utf-8')
        
        # 确保 "users" 键存在
        if "users" not in config:
            config["users"] = {}
        
        user_data = config["users"].get(username, {})
        
        # 更新或创建用户信息
        # config["users"][username] = {
        #     "password": password_encoded,
        #     "device_id": device_id
        # }

        user_data['password'] = password_encoded
        user_data['device_id'] = device_id

        # 3. 将更新后的数据写回配置中
        config["users"][username] = user_data
        
        # 设置为最后登录的用户
        config["last_login_user"] = username
        
        self._save_config_data(config)
        print(f"✅ 已保存用户 {username} 的凭据和设备ID。")


    def _generate_device_id(self):
        """生成一个唯一的设备码 (UUID)"""
        return str(uuid.uuid4()) 

    # 模拟向后端发送HTTP请求
    def _send_to_backend(self, data):
        """
        向后端发送HTTP请求，处理登录和设备码绑定/验证。

        参数:
            data (dict): 要发送的数据，包含用户名、密码、设备码等。

        返回:
            tuple: (bool success, str message, str user_id or None, str user_type or None)
        """
        url = self.BACKEND_API_BASE_URL
        print(f"发送请求到: {url}，数据: {data}")
        try:
            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                response_json = response.json()
                print(response_json)

                if response_json.get("success"):
                    user_info = response_json.get("user", {})
                    user_id = user_info.get("id")
                    user_type = user_info.get("userType") 

                    # --- 到期时间判断 ---
                    expiry_at_str = user_info.get("expiryAt")
                    trial_search_used = user_info.get("trial_search_used", False)
                    daily_export_count = user_info.get("daily_export_count", 0)

                    if expiry_at_str:
                        try:
                            from datetime import datetime, timezone
                            if expiry_at_str.endswith("Z"):
                                expiry_date = datetime.fromisoformat(expiry_at_str[:-1]).replace(tzinfo=timezone.utc)
                            else:
                                expiry_date = datetime.fromisoformat(expiry_at_str)

                            current_time = datetime.now(timezone.utc)
                            if current_time > expiry_date:
                                # 【修正】确保返回4个值
                                return False, "账号已过期，请联系管理员。", None, None, None, None, None
                        except ValueError as e:
                            print(f"日期解析错误: {e}")
                            # 【修正】确保返回4个值
                            return False, "账号到期时间格式不正确，请联系管理员。", None, None, None, None, None
                    else:
                        # 【修正】确保返回4个值
                        return False, "账号到期时间信息缺失，请联系管理员。", None, None, None, None, None

                    # --- 状态判断 ---
                    status = user_info.get("status")
                    if status != "active":
                        # 【修正】确保返回4个值
                        return False, f"账号状态为 '{status}'，无法登录，请联系管理员。", None, None, None, None, None

                    # 登录成功，返回4个值
                    return True, response_json.get("message", "登录成功。"), user_id, user_type, expiry_at_str, trial_search_used, daily_export_count
                else:
                    # 登录失败，也要返回4个值
                    return False, response_json.get("message", "登录失败。"), None, None, None, None, None
            else:
                # HTTP状态码非200，也要返回4个值
                error_response = response.json()
                return False, error_response.get("message", f"后端请求失败: HTTP {response.status_code}"), None, None, None, None, None

        except requests.exceptions.Timeout:
            print(f"❌ 后端请求超时: {url}")
            # 【修正】确保返回4个值
            return False, "网络请求超时，请检查网络连接。", None, None, None, None, None
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到后端: {url}")
            # 【修正】确保返回4个值
            return False, "无法连接到服务器，请检查后端服务是否运行。", None, None, None, None, None
        except requests.exceptions.RequestException as e:
            print(f"❌ 后端请求失败: {e}")
            # 【修正】确保返回4个值
            return False, f"网络错误或后端服务不可用: {e}", None, None, None, None, None
        except json.JSONDecodeError:
            print(f"❌ 后端返回非JSON格式响应: {response.text}")
            # 【修正】确保返回4个值
            return False, "服务器返回无效响应。", None, None, None, None, None
        except Exception as e:
            print(f"❌ 发送后端请求发生未知错误: {e}")
            # 【修正】确保返回4个值
            return False, f"发生内部错误: {e}", None, None, None, None, None

    


    # 登录逻辑
    def handle_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()

        if not username or not password:
            self.error_label.setText("用户名和密码不能为空！")
            self.error_label.show()
            self.shake_window()
            return


        # 获取当前操作系统的类型。
        def get_os_type():
            """
                获取当前操作系统的类型。
                返回 'Windows', 'macOS', 'Linux' 或 'Unknown'。
            """
            os_name = platform.system()
            if os_name == "Windows":
                return "Windows"
            elif os_name == "Darwin": # macOS 的系统名称是 Darwin
                return "macOS"
            elif os_name == "Linux":
                return "Linux"
            else:
                return "Unknown"
        
        # 检查是否是初次登录（本地是否有该用户的设备码记录）
        existing_device_id = self._get_device_id_for_user(username)

        device_id_to_send = existing_device_id or self._generate_device_id()
        # 统一生成或使用设备码，因为后端会判断是否是初次绑定
        if not existing_device_id:
            device_id_to_send = self._generate_device_id()
            print(f"本地无 {username} 的设备码记录，生成新设备码: {device_id_to_send}")
        else:
            device_id_to_send = existing_device_id
            print(f"本地发现 {username} 的设备码: {device_id_to_send}，将发送此码进行验证。")

        os_type = get_os_type() # 调用我们上面定义的函数
        print(f"当前设备操作系统类型: {os_type}")

        # 统一的请求负载，不再区分 endpoint
        payload = {
            "username": username,
            "password": password,
            "device_id": device_id_to_send,
            "os_type": os_type
        }

        # 调用真实的后端接口
        success, message, user_id, user_type, expiry_at, trial_search_used, daily_export_count = self._send_to_backend(payload)

        if success:
            if user_id:
                self.logged_in_user_id = user_id  # 保存 user_id
                self.user_type = user_type
                self.expiry_at = expiry_at
                self.trial_search_used = trial_search_used
                self.daily_export_count = daily_export_count
                self._save_user_credentials_and_device_id(username, password, device_id_to_send)
                # QMessageBox.information(self, "登录成功", message)
                self.accept()
            else:
                self.error_label.setText("无法获取用户ID，请联系管理员。")
                self.error_label.show()
                self.shake_window()
        else:
            # 检查返回的消息是否包含“过期”
            if "过期" in message:
                # --- ▼▼▼ 【核心修复】替换这里的逻辑 ▼▼▼ ---
                # 旧代码: QMessageBox.warning(self, "授权已过期", message)
                
                # 新代码：创建一个带“续费”按钮的自定义弹窗
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("授权已过期")
                msg_box.setText(f"<b>{message}</b>") # 例如: "账号已过期，请联系管理员。"
                msg_box.setInformativeText("您的账号授权已过期，请续费后重新登录。")

                renew_button = msg_box.addButton("立即续费", QMessageBox.ActionRole)
                close_button = msg_box.addButton("关闭", QMessageBox.RejectRole)
                
                msg_box.exec_()

                if msg_box.clickedButton() == renew_button:
                    # 在这里换上您的官网续费链接
                    QDesktopServices.openUrl(QUrl("https://mediamingle.cn/checkout.html"))
            else:
                # 其他错误，仍然在标签里显示
                self.error_label.setText(message)
                self.error_label.show()
                self.shake_window()


    def shake_window(self):
        animation = QPropertyAnimation(self, b"pos")
        animation.setDuration(250)
        animation.setLoopCount(2)
        initial_pos = self.pos()
        animation.setKeyValueAt(0, initial_pos)
        animation.setKeyValueAt(0.1, initial_pos + QPoint(10, 0)) # 增大抖动幅度
        animation.setKeyValueAt(0.2, initial_pos + QPoint(-10, 0))
        animation.setKeyValueAt(0.3, initial_pos + QPoint(10, 0))
        animation.setKeyValueAt(0.4, initial_pos + QPoint(-10, 0))
        animation.setKeyValueAt(0.5, initial_pos)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start()

    def open_register_dialog(self):
        # 为注册流程生成一个新的设备ID
        device_id_for_reg = self._generate_device_id()
        print(f"正在为注册流程准备设备ID: {device_id_for_reg}")

        # 创建注册窗口，并将 device_id 传递过去
        register_dialog = RegisterDialog(self, device_id=device_id_for_reg)
        
        # --- ▼▼▼ 【核心修复】检查注册窗口的返回状态 ▼▼▼ ---
        # .exec_() 会阻塞程序，直到窗口关闭。我们检查它是否是“成功”关闭的 (通过 self.accept())
        if register_dialog.exec_() == QDialog.Accepted:
            # 检查注册窗口是否真的返回了有效的注册信息
            if register_dialog.registered_email and register_dialog.registered_password:
                print("✅ 检测到新用户注册成功，正在将信息保存到本地配置...")
                
                # 1. 调用已有的保存方法，将新用户信息写入 user_config.json
                self._save_user_credentials_and_device_id(
                    username=register_dialog.registered_email,
                    password=register_dialog.registered_password,
                    device_id=register_dialog.registered_device_id
                )
                
                # 2. 为了提升用户体验，自动将新注册的账号密码填入登录框
                self.username_input.setText(register_dialog.registered_email)
                self.password_input.setText(register_dialog.registered_password)
                
                # 3. 弹窗提示用户现在可以登录了
                QMessageBox.information(self, "注册完成", "账号创建成功！已为您自动填写信息，请点击登录。")


# 屏蔽控制台输出
class SilentWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # 屏蔽输出，可自定义是否打印
        pass

def deobfuscate_text(text):
    """
    【Bing链接解密修复版】
    - 增加了对Bing搜索结果跳转链接的自动解析和Base64解码功能。
    - 保留了原有的文本和HTML实体反混淆能力。
    """
    # --- ▼▼▼ 【新增】Bing 链接解码逻辑 ▼▼▼ ---
    try:
        # 1. 检查这是否是一个Bing的跳转链接
        if text and "bing.com/ck/a" in text:
            # 2. 解析URL，获取所有查询参数
            parsed_url = urlparse(text)
            query_params = parse_qs(parsed_url.query)
            
            # 3. 检查是否存在 'u' 参数
            if 'u' in query_params:
                # 4. 获取 'u' 参数的值（它是一个列表，我们取第一个）
                encoded_url = query_params['u'][0]
                
                # 5. Bing有时会添加 'a1' 或 'r' 等前缀，我们需要移除它们
                if encoded_url.startswith('a1'):
                    encoded_url = encoded_url[2:]
                
                # 6. 【核心】进行 Base64 解码
                #    为了防止解码错误，我们需要确保填充正确
                padding = '=' * (4 - len(encoded_url) % 4)
                decoded_bytes = base64.b64decode(encoded_url + padding)
                
                # 7. 将解码后的字节转换为UTF-8字符串，并返回
                decoded_url = decoded_bytes.decode('utf-8')
                print(f"  -> [Bing链接解密] 成功解码: {decoded_url}")
                return decoded_url
    except Exception as e:
        print(f"  -> ⚠️ [Bing链接解密] 解码失败: {e}，将返回原始链接。")
        # 如果解码过程中出现任何意外，就返回原始的Bing链接，避免程序崩溃
        pass
    # --- ▲▲▲ 新增逻辑结束 ▲▲▲ ---

    # --- ▼▼▼ 保留原有的文本反混淆逻辑 ▼▼▼ ---
    # 1. 替换常见的混淆词
    text = text.replace('[at]', '@').replace('[dot]', '.')
    text = text.replace('(at)', '@').replace('(dot)', '.')
    
    # 2. 移除 "nospam" 或 "removethis" 等标记
    text = re.sub(r'(\.|\s)nospam(\.|\s)', '.', text, flags=re.IGNORECASE)
    text = re.sub(r'\.removethis', '', text, flags=re.IGNORECASE)
    
    # 3. 处理HTML实体编码 (例如 &amp; -> &)
    text = html.unescape(text)
    
    # 4. 处理空格和注释（更宽松的匹配）
    text = re.sub(r'\s*(@|\[at\])\s*', '@', text)
    text = re.sub(r'\s*(\.|\[dot\])\s*', '.', text)
    
    return text



# AI处理线程 (AIFetcher类)
class AIFetcher(QThread):
    # 定义信号: 
    dataEnriched = pyqtSignal(dict, list)
    errorOccurred = pyqtSignal(str)
    tokenUpdated = pyqtSignal(int)

    def __init__(self, companies_batch, user_id):
        super().__init__()
        self.companies_batch = companies_batch
        self.user_id = user_id
        # 您的Netlify后端AI接口地址
        self.api_url = "http://localhost:8888/.netlify/functions/gemini-enrich-data"


    def run(self):
        """线程主执行函数，负责调用后端AI接口"""
        try:
            # 从原始批次中提取纯数据，去掉附加的'row'信息
            payload_companies = [{"name": c.get("name"), "address": c.get("address"), "phone": c.get("phone"), "website": c.get("website")} for c in self.companies_batch]

            print(f"🤖 正在为 {len(payload_companies)} 家公司启动AI深度分析...")
            payload = {
                "user_id": self.user_id,
                "companies": payload_companies
            }
            
            # 使用 requests 发送同步请求，因为是在独立的线程中
            # AI处理可能耗时较长，超时时间设置得长一些，例如5分钟
            response = requests.post(self.api_url, json=payload, timeout=300) 

            if response.status_code == 200:
                response_data = response.json()
                if response_data.get("success"):
                    # 发射成功信号，把AI返回的数据和原始批次（含行号）都传回去
                    self.dataEnriched.emit(response_data.get("data", {}), self.companies_batch)
                    # 发射token更新信号
                    self.tokenUpdated.emit(response_data.get("tokens_remaining", 0))
                else:
                    self.errorOccurred.emit(response_data.get("message", "AI处理失败"))
            else:
                self.errorOccurred.emit(f"AI服务器错误: HTTP {response.status_code} - {response.text}")

        except requests.exceptions.Timeout:
            self.errorOccurred.emit("AI请求超时，服务器可能正在处理，请稍后在表格中查看结果。")
        except Exception as e:
            self.errorOccurred.emit(f"AI请求异常: {e}")


# 用于检查GitHub上的最新版本。
class UpdateChecker(QThread):
    """
    一个在后台运行的线程，用于检查GitHub上的最新版本。
    """
    # 定义一个信号，当发现新版本时发射
    # 参数: (新版本号, 下载页面URL)
    update_available = pyqtSignal(str, str)

    def __init__(self, current_version, repo_url):
        super().__init__()
        self.current_version = current_version
        self.repo_url = repo_url
        # 使用GitHub官方API获取最新release信息
        self.api_url = f"https://api.github.com/repos/{self.repo_url}/releases/latest"

    def run(self):
        """
        【修改版】线程的主执行函数。
        增加了自动回退逻辑，并能从Release中智能寻找.exe安装包的直接下载链接。
        """
        print(f"🚀 正在后台检查更新... 当前版本: {self.current_version}")
        
        api_endpoints = [GITHUB_API_PRIMARY, GITHUB_API_FALLBACK]
        success = False

        for base_url in api_endpoints:
            api_url = f"{base_url}/repos/{self.repo_url}/releases/latest"
            print(f"  -> 正在尝试API端点: {base_url}...")
            
            try:
                response = requests.get(api_url, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    latest_version = data.get("tag_name", "0.0.0")
                    
                    # --- ▼▼▼ 【核心修改点】从"assets"中寻找直接下载链接 ▼▼▼ ---
                    
                    # 1. 首先，设置一个默认的回退URL，即发布页面的地址
                    download_url = data.get("html_url") 
                    
                    # 2. 获取附件列表
                    assets = data.get("assets", [])
                    
                    # 3. 遍历所有上传的附件 (assets)，寻找安装包
                    for asset in assets:
                        asset_name = asset.get("name", "").lower()
                        # 您可以根据您打包的文件名来修改这里的判断条件
                        if asset_name.endswith(".exe") or asset_name.endswith(".zip"):
                            # 找到了！获取它的直接下载链接并跳出循环
                            download_url = asset.get("browser_download_url")
                            print(f"  ✅ 成功找到 .zip 压缩包的直接下载链接: {download_url}")
                            break # 找到第一个.exe就停止
                    
                    # --- ▲▲▲ 修改结束 ▲▲▲ ---

                    cleaned_latest = latest_version.lstrip('v')
                    cleaned_current = self.current_version.lstrip('v')
                    
                    print(f"  ✅ 成功从 {base_url} 获取到最新版本: {cleaned_latest}")

                    latest_parts = list(map(int, cleaned_latest.split('.')))
                    current_parts = list(map(int, cleaned_current.split('.')))
                    
                    if latest_parts > current_parts:
                        print(f"✅ 发现新版本！ {cleaned_current} -> {cleaned_latest}")
                        # 发射信号，将找到的URL（可能是直接下载链接，也可能是页面链接）传递出去
                        self.update_available.emit(latest_version, download_url)
                    else:
                        print("✅ 当前已是最新版本。")
                    
                    success = True
                    break

                else:
                    print(f"  ⚠️ 尝试 {base_url} 失败: GitHub API返回状态码 {response.status_code}")
            
            except requests.exceptions.RequestException as e:
                print(f"  ❌ 尝试 {base_url} 时发生网络错误: {e}")

        if not success:
            print("❌ 所有更新检查端点均尝试失败，请检查网络连接或稍后再试。")



class WhatsAppLoginWorker(QObject):
    """
    一个专用于在后台线程中执行WhatsApp登录的Worker。
    它继承自QObject，以便可以移动到QThread中。
    """
    # 定义一个信号，当登录流程结束后（无论成功失败）发射
    finished = pyqtSignal()

    def __init__(self, whatsapp_manager):
        super().__init__()
        self.whatsapp_manager = whatsapp_manager

    @pyqtSlot()  # 明确这是一个槽函数
    def run(self):
        """
        这个方法将在新的线程中被执行。
        我们在这里调用会阻塞的、完整的登录流程。
        """
        print("🚀 WhatsApp登录Worker已在后台线程启动...")
        try:
            # 【核心】在这里，我们调用的是会等待结果的、阻塞的 run_coroutine 方法
            # 因为整个 run 方法已经在一个独立的线程里了，所以阻塞在这里是安全的，不会影响主UI。
            self.whatsapp_manager.run_coroutine(self.whatsapp_manager.login_to_whatsapp())
        except Exception as e:
            print(f"❌ WhatsApp登录Worker在执行时发生错误: {e}")
        finally:
            # 确保在任务结束后发射 finished 信号，以便主线程可以进行清理
            print("✅ WhatsApp登录Worker任务执行完毕。")
            self.finished.emit()


class CompanyInfoTooltip(QWidget):
    """一个自定义的信息提示窗，用于在悬浮时显示公司详情。"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(300, 480)
        # 设置窗口属性：使其像一个工具提示，并且无边框
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground) # 支持半透明背景
        self.setAttribute(Qt.WA_ShowWithoutActivating) # 显示时不抢占主窗口焦点

        # 使用一个网络管理器来异步加载图片
        self.net_manager = QNetworkAccessManager(self)
        self.net_manager.finished.connect(self.on_image_loaded)

        # 设置基础样式
        self.setStyleSheet("""
            #mainFrame {
                background-color: rgba(30, 30, 30, 0.9); /* 半透明深色背景 */
                border-radius: 8px;
                border: 1px solid #555;
                padding: 12px;
            }
            QLabel {
                color: #f0f0f0;
                font-size: 13px;
                background-color: transparent;
            }
            #nameLabel {
                font-size: 16px;
                font-weight: bold;
                color: #ffffff;
            }
            #imageLabel {
                border: 1px solid #444;
                border-radius: 4px;
                background-color: #222;
                min-height: 150px; /* 图片最小高度 */
            }
        """)

        # 主框架和布局
        self.frame = QFrame(self)
        self.frame.setObjectName("mainFrame")
        main_layout = QVBoxLayout(self.frame)
        
        # 整体使用一个垂直布局
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.frame)
        self.layout.setContentsMargins(0,0,0,0)

        # 1. 图片标签
        self.image_label = QLabel("正在加载图片...")
        self.image_label.setObjectName("imageLabel")
        self.image_label.setFixedSize(250, 150)
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label)

        # 2. 公司名称
        self.name_label = QLabel("公司名")
        self.name_label.setObjectName("nameLabel")
        self.name_label.setWordWrap(True)
        main_layout.addWidget(self.name_label)
        
        # 使用 QFormLayout 来美观地展示键值对信息
        form_layout = QFormLayout()
        form_layout.setContentsMargins(0, 10, 0, 0)
        form_layout.setSpacing(8)
        
        self.address_label = QLabel()
        self.website_label = QLabel()
        self.email_label = QLabel()
        self.facebook_label = QLabel()
        self.linkedin_label = QLabel()
        self.whatsapp_label = QLabel()

        # 将标签添加到表单布局中
        form_layout.addRow("地址:", self.address_label)
        form_layout.addRow("官网:", self.website_label)
        form_layout.addRow("邮箱:", self.email_label)
        form_layout.addRow("Facebook:", self.facebook_label)
        form_layout.addRow("LinkedIn:", self.linkedin_label)
        form_layout.addRow("WhatsApp:", self.whatsapp_label)

        main_layout.addLayout(form_layout)



    def update_info(self, data):
        """
        【健壮性修复版】
        用传入的数据字典更新提示窗的内容。
        通过兼容多种可能的键名，使其能同时处理来自数据库和实时抓取的数据。
        """
        if not data:
            self.hide()
            return

        # --- ▼▼▼ 【核心修复逻辑】兼容多种键名 ▼▼▼ ---
        self.name_label.setText(data.get("名称") or data.get("name", "N/A"))
        self.address_label.setText(data.get("地址") or data.get("address", "N/A"))
        self.email_label.setText(data.get("邮箱") or data.get("email", "N/A"))
        
        # WhatsApp的键名在不同地方可能为 whatsapp (实时) 或 whatsapp_url (旧数据库) 或 WhatsApp (新数据库)
        self.whatsapp_label.setText(data.get("WhatsApp") or data.get("whatsapp_url") or data.get("whatsapp", "N/A"))
        
        self.address_label.setWordWrap(True)
        available_width = self.width() - 94 # 减去边距和标签宽度

        def create_elided_link(label, url_string):
            if not url_string or not isinstance(url_string, str): return "N/A"
            metrics = QFontMetrics(label.font())
            elided_text = metrics.elidedText(url_string, Qt.ElideRight, available_width)
            return f"<a href='{url_string}' style='color: #55aaff;'>{elided_text}</a>"
        
        # 兼容处理各种可能的链接键名
        self.website_label.setText(create_elided_link(self.website_label, data.get('官网') or data.get('website')))
        self.website_label.setOpenExternalLinks(True)
        
        self.facebook_label.setText(create_elided_link(self.facebook_label, data.get('Facebook') or data.get('facebook_url') or data.get('facebook')))
        self.facebook_label.setOpenExternalLinks(True)

        self.linkedin_label.setText(create_elided_link(self.linkedin_label, data.get('LinkedIn') or data.get('linkedin_url') or data.get('linkedin')))
        self.linkedin_label.setOpenExternalLinks(True)
        
        # 兼容处理图片链接键名
        image_url = data.get("image_url", "") or data.get("image", "")
        if image_url:
            self.image_label.setText("正在加载图片...")
            request = QNetworkRequest(QUrl(image_url))
            self.net_manager.get(request)
        else:
            self.image_label.setText("无可用图片")
            self.image_label.setPixmap(QPixmap()) # 清空旧图片


    def on_image_loaded(self, reply):
        """当网络请求完成时，此槽函数被调用"""
        if reply.error():
            print(f"❌ 图片加载失败: {reply.errorString()}")
            self.image_label.setText("图片加载失败")
            return
        
        image_data = reply.readAll()
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        
        # 缩放图片以适应标签大小，同时保持长宽比
        self.image_label.setPixmap(pixmap.scaled(
            self.image_label.size(), 
            Qt.KeepAspectRatioByExpanding, # <-- 【核心修复】修改为这个模式
            Qt.SmoothTransformation
        ))








class GoogleMapsApp(QWidget):
    session_expired = pyqtSignal()

    email_result_ready = pyqtSignal(dict, int) # (结果字典, 行号)
    email_worker_finished = pyqtSignal(int) # (行号)

    # 定义AI批处理大小
    AI_BATCH_SIZE = 1 

    # 脚本一：专门用于“列表详情”模式，它依赖于详情容器的存在
    JS_EXTRACT_DETAIL_INFO = r"""
    (function() {
        const container = document.querySelector('.bJzME.Hu9e2e.tTVLSc');
        if (!container) return null;
        const nameEl = container.querySelector(".DUwDvf.lfPIob");
        const name = nameEl ? nameEl.textContent.trim() : "";
        if (!name) return {"name": ""};


        const getHours = () => {
            // 优先尝试获取简短的营业状态摘要
            const summaryEl = container.querySelector('.OqCZI .o0Svhf');
            if (summaryEl) {
                return summaryEl.textContent.replace(/\s+/g, ' ').trim();
            }
            // 如果摘要不存在，则尝试解析详细的营业时间表格
            const tableEl = container.querySelector('table.eK4R0e');
            if (tableEl) {
                let hoursText = [];
                tableEl.querySelectorAll('tr.y0skZc').forEach(row => {
                    const day = row.querySelector('td.ylH6lf')?.textContent.trim();
                    const time = row.querySelector('td.mxowUb ul.fontTitleSmall li.G8aQO')?.textContent.trim();
                    if (day && time) {
                        hoursText.push(`${day}: ${time}`);
                    }
                });
                return hoursText.join(' | ');
            }
            return "";
        };

        const getText = (sel) => container.querySelector(sel)?.textContent.trim() || "";
        const getWebsite = () => container.querySelector('a.CsEnBe[data-item-id="authority"]')?.getAttribute("href") || "";
        const getPhone = () => container.querySelector('button.CsEnBe[data-item-id^="phone:tel:"] .Io6YTe')?.textContent.trim() || "";
        const getImage = () => {
            const selector = 'div.RZ66Rb button.aoRNLd img, button[jsaction$=".heroHeaderImage"] img, div[role="img"] img';
            const img = container.querySelector(selector);
            // 修改点：只要找到了 img 元素并且它有 src 属性，就直接返回这个 src
            return (img && img.src) ? img.src : '';
        };
        const getAddress = () => container.querySelector('button.CsEnBe[data-item-id="address"]')?.getAttribute('aria-label').replace('地址:', '').trim() || "";

        const getReviewCount = () => {
            const spans = container.querySelectorAll(".F7nice > span");
            if (spans.length < 2) return "";
            const secondSpan = spans[1];
            const text = secondSpan.textContent.trim();
            const match = text.match(/(\d+)/);
            return match ? match[1] : "";
        };

        return {
            "name": name, "address": getAddress(), "phone": getPhone(), "website": getWebsite(), "image": getImage(),
            "rating": getText(".F7nice span[aria-hidden='true']"),
            "reviewCount": getReviewCount(),
            "dkEaLTexts": getText(".DkEaL"), "email": "", "link": document.URL, "hours": getHours()
        };
    })();
    """

    # 脚本二：专门用于“单个商家页面”模式，它直接在整个文档中查找
    JS_EXTRACT_SINGLE_PAGE_DETAIL = r"""
    (function() {
        // 【优化】首先定位到包含所有核心信息的主容器 (role="main")
        const container = document.querySelector('[role="main"]');
        if (!container) {
            console.error("无法找到 role='main' 的主容器");
            // 如果连主容器都找不到，尝试直接从 document 级别找名字作为最后的补救
            const fallbackNameEl = document.querySelector("h1.DUwDvf.lfPIob");
            if (!fallbackNameEl) return null;
            // 即使只找到名字，也返回，避免流程完全中断
            return { "name": fallbackNameEl.textContent.trim() };
        }

        const nameEl = container.querySelector("h1.DUwDvf.lfPIob");
        const name = nameEl ? nameEl.textContent.trim() : "";
        if (!name) return null; // 在单个页面模式，如果连名字都找不到，就视为无效

        // 所有帮助函数都改为在新的、更精确的 `container` 内部查找
        const getHours = () => {
            const summaryEl = container.querySelector('.OqCZI .o0Svhf');
            if (summaryEl) return summaryEl.textContent.replace(/\s+/g, ' ').trim();
            const tableEl = container.querySelector('table.eK4R0e');
            if (tableEl) {
                let hoursText = [];
                tableEl.querySelectorAll('tr.y0skZc').forEach(row => {
                    const day = row.querySelector('td.ylH6lf')?.textContent.trim();
                    const time = row.querySelector('td.mxowUb ul.fontTitleSmall li.G8aQO')?.textContent.trim();
                    if (day && time) hoursText.push(`${day}: ${time}`);
                });
                return hoursText.join(' | ');
            }
            return "";
        };

        const getText = (sel) => container.querySelector(sel)?.textContent.trim() || "";
        const getWebsite = () => container.querySelector('a.CsEnBe[data-item-id="authority"]')?.getAttribute("href") || "";
        const getPhone = () => container.querySelector('button.CsEnBe[data-item-id^="phone:tel:"] .Io6YTe')?.textContent.trim() || "";
        const getImage = () => {
            const selector = 'div.RZ66Rb button.aoRNLd img, button[jsaction$=".heroHeaderImage"] img, div[role="img"] img';
            const img = container.querySelector(selector);
            return (img && img.src) ? img.src : '';
        };
        const getAddress = () => container.querySelector('button.CsEnBe[data-item-id="address"]')?.getAttribute('aria-label').replace('地址:', '').trim() || "";

        const getReviewCount = () => {
            // --- ▼▼▼ 【核心修复】将 container 变量修正 ▼▼▼ ---
            const spans = container.querySelectorAll(".F7nice > span");
            if (spans.length < 2) return "";
            const secondSpan = spans[1];
            const text = secondSpan.textContent.trim();
            // 正则表达式优化，以匹配带逗号的数字，例如 (1,234)
            const match = text.replace(/,/g, '').match(/(\d+)/);
            return match ? match[1] : "";
        };

        return {
            "name": name, "address": getAddress(), "phone": getPhone(), "website": getWebsite(), "image": getImage(),
            "rating": getText(".F7nice span[aria-hidden='true']"),
            "reviewCount": getReviewCount(),
            "dkEaLTexts": getText(".DkEaL"), "email": "", "link": document.URL, "hours": getHours()
        };
    })();
    """


    


    # ==================== 【新增】为QWebEngineView添加伪装的函数 ====================
    def setup_disguised_browser_for_view(self, browser_view):
        """
        【修改版】为指定的 QWebEngineView 实例配置独立的伪装身份。
        """
        print("🚀 [伪装] 正在为一个新的浏览器页面配置独立的伪装身份...")

        # 1. 创建一个全新的、临时的配置文件
        disguised_profile = QWebEngineProfile()

        # 2. 为这个配置文件设置随机User-Agent
        try:
            ua = UserAgent(os='windows')
            ua_string = ua.chrome
            
            disguised_profile.setHttpUserAgent(ua_string)
            print(f"  -> [伪装] 已应用随机Windows User-Agent: {ua_string}")
        except Exception as e:
            print(f"  -> [伪装] 警告：生成随机User-Agent失败: {e}")
            disguised_profile.setHttpUserAgent(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )

        # 3. 注入强大的伪装脚本 (反侦测的核心)
        stealth_script_js = """
        (() => {
            // 1. 覆盖 navigator.webdriver 属性
            if (navigator.webdriver) {
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => false,
                });
            }

            // 2. 伪造 window.chrome 对象
            if (!window.chrome) {
                window.chrome = {};
            }
            if (window.chrome.runtime) {
                // 这是一个常见的检测标志
            }
            
            // 3. 伪造权限状态
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications'
                    ? Promise.resolve({ state: Notification.permission })
                    : originalQuery(parameters)
            );

            // 4. 伪造插件信息
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: '' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin', description: '' },
                ],
            });

            // 5. 伪造语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });

            // 6. 伪造 WebGL 指纹
            try {
                const getParameter = WebGLRenderingContext.prototype.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) { return 'Google Inc. (NVIDIA)'; }
                    if (parameter === 37446) { return 'ANGLE (NVIDIA, NVIDIA GeForce GTX 1080 Ti Direct3D11 vs_5_0 ps_5_0, D3D11)'; }
                    return getParameter.apply(this, arguments);
                };
            } catch (e) {}

            // 7. 保护函数 toString 方法
            const originalToString = Function.prototype.toString;
            Function.prototype.toString = function() {
                if (this === navigator.plugins.getter || this === navigator.languages.getter) {
                    return 'function get() { [native code] }';
                }
                if (this === WebGLRenderingContext.prototype.getParameter) {
                    return 'function getParameter() { [native code] }';
                }
                return originalToString.apply(this, arguments);
            };

            // 8.伪造 User-Agent Client Hints (品牌信息)
            if (navigator.userAgentData) {
                Object.defineProperty(navigator, 'userAgentData', {
                    get: () => ({
                        "brands": [
                            { "brand": "Google Chrome", "version": "124" },
                            { "brand": "Not-A.Brand", "version": "99" },
                            { "brand": "Chromium", "version": "124" }
                        ],
                        "mobile": false,
                        "platform": "Windows"
                    }),
                });
            }

            // 9. Canvas 指纹伪装
            try {
                const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = function() {
                    const ctx = this.getContext('2d');
                    if (ctx) {
                        const shift = {
                            'r': Math.floor(Math.random() * 10) - 5,
                            'g': Math.floor(Math.random() * 10) - 5,
                            'b': Math.floor(Math.random() * 10) - 5,
                            'a': Math.floor(Math.random() * 10) - 5
                        };
                        const imageData = ctx.getImageData(0, 0, this.width, this.height);
                        for (let i = 0; i < this.height; i++) {
                            for (let j = 0; j < this.width; j++) {
                                const n = ((i * this.width) + j) * 4;
                                imageData.data[n + 0] = imageData.data[n + 0] + shift.r;
                                imageData.data[n + 1] = imageData.data[n + 1] + shift.g;
                                imageData.data[n + 2] = imageData.data[n + 2] + shift.b;
                                imageData.data[n + 3] = imageData.data[n + 3] + shift.a;
                            }
                        }
                        ctx.putImageData(imageData, 0, 0);
                    }
                    return originalToDataURL.apply(this, arguments);
                };
            } catch(e) {}
        })();
        """
        script = QWebEngineScript()
        script.setSourceCode(stealth_script_js)
        script.setName("stealth_script")
        # 这是最重要的！在文档创建时注入，早于页面自身的任何脚本
        script.setInjectionPoint(QWebEngineScript.DocumentCreation)
        script.setRunsOnSubFrames(True)
        script.setWorldId(QWebEngineScript.MainWorld)
        
        disguised_profile.scripts().insert(script)
        print("  -> [伪装] 已成功注入 Stealth 伪装脚本。")

        # 4. 【核心修改】创建一个使用此配置文件的页面，并应用到传入的 browser_view
        disguised_page = SilentWebEnginePage(disguised_profile, browser_view) 
        browser_view.setPage(disguised_page)
        print("✅ [伪装] 浏览器页面已应用全新的伪装配置。")

        return disguised_profile

    
    @property
    def browser(self):
        """【改造版】根据 QTabBar 的当前选中项，返回对应的浏览器页面。"""
        if not self.tabs:
            return None
        # --- ▼▼▼ 【核心修改】修改下面这行代码 ▼▼▼ ---
        current_index = self.tab_bar.currentIndex()
        if 0 <= current_index < len(self.tabs):
            return self.tabs[current_index]['view']
        return None




    def _create_new_tab(self, index):
        """
        【遮罩层修复版】
        - 为每个新的浏览器视图创建一个专属的、作为其子控件的加载遮罩层。
        - 为浏览器视图安装事件过滤器，以便能捕捉到它的尺寸变化事件。
        """
        self.tab_bar.addTab(f"采集任务-{index + 1}")
        browser_view = QWebEngineView(self.browser_container)
        profile = self.setup_disguised_browser_for_view(browser_view)
        
        # --- ▼▼▼ 【核心修复】在这里增加专属遮罩层的创建和绑定 ▼▼▼ ---
        
        # a. 创建一个加载提示层，并明确指定它的“父亲”是 browser_view
        loading_label = QLabel("正在加载页面，请稍候...", browser_view)
        loading_label.setAlignment(Qt.AlignCenter)
        loading_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 180); color: #4CAF50;
            font-size: 18px; font-weight: bold;
        """)
        loading_label.hide()
        # 立即设置其大小以铺满它的父亲
        loading_label.setGeometry(browser_view.rect())

        # b. 为这个浏览器视图安装事件过滤器，这样我们就能“监听”到它的尺寸变化
        browser_view.installEventFilter(self)

        # --- ▲▲▲ 修复结束 ▲▲▲ ---

        browser_view.loadStarted.connect(self.on_load_started)
        browser_view.loadFinished.connect(self.on_load_finished)
        
        self.user_triggered_navigation = True
        browser_view.load(QUrl("https://www.google.com/maps"))
        
        circle_overlay = CircleOverlay(browser_view)
        
        tab_info = {
            'view': browser_view,
            'profile': profile,
            'state': 'idle',
            'current_task': None,
            'overlay': circle_overlay,
            # --- ▼▼▼ 将专属的遮罩层和加载状态存入 tab_info 中 ▼▼▼ ---
            'loading_overlay': loading_label,
            'is_loading': False
            # --- ▲▲▲ 修复结束 ▲▲▲ ---
        }
        self.tabs.append(tab_info)
        
        browser_view.setGeometry(self.browser_container.rect())
        print(f"✅ 已成功创建并初始化采集页面: {index + 1}")


    def _update_tab_count(self, new_count):
        """
        【新】核心方法，用于动态调整采集页面的数量。
        """
        current_count = self.tab_bar.count()
        
        if new_count > current_count:
            # --- 需要增加页面 ---
            print(f"📈 检测到并行页面数量增加，正在从 {current_count} 增加到 {new_count}...")
            for i in range(current_count, new_count):
                self._create_new_tab(i)
            # 自动切换到最后一个新创建的页面
            self.tab_bar.setCurrentIndex(new_count - 1)

        elif new_count < current_count:
            # --- 需要减少页面 ---
            print(f"📉 检测到并行页面数量减少，正在从 {current_count} 减少到 {new_count}...")
            # 从后往前删除，避免索引错乱
            for i in range(current_count - 1, new_count - 1, -1):
                # 复用我们之前创建的关闭标签页的逻辑
                self._on_tab_close_requested(i)


    # 页面设计
    def __init__(self, user_id=None, credentials=None, user_type=None, expiry_at=None, trial_search_used=False, daily_export_count=0, width=1300, height=900):
        super().__init__()

        self.scraper_semaphore = threading.Semaphore(2)

        # 1. 首先，调用新函数获取系统推荐的默认值
        self.auto_detected_defaults = get_performance_defaults()
        



        # 2. 然后，从配置文件加载用户之前保存过的设置
        saved_user_settings = {}
        if credentials and 'username' in credentials:
            username = credentials['username']
            config = self._load_user_config()
            saved_user_settings = config.get("users", {}).get(username, {})

        # 3. 【关键】决定最终要使用的设置值
        #    逻辑：优先使用用户保存过的值，如果用户没保存过，就用系统推荐的值。
        self.parallel_tasks_count = saved_user_settings.get('parallel_tasks', self.auto_detected_defaults['parallel_tasks'])
        self.playwright_pool_size = saved_user_settings.get('playwright_pool_size', self.auto_detected_defaults['playwright_pool_size'])
    


        
        self.cache_lock = threading.Lock()

        self.task_queue = [] # 初始化并行任务队列

        self.extreme_deep_scan_mode = False # 初始化默认状态


        # 新增：初始化一个空的集合，用于在采集中存储已处理过的商家标识
        self.processed_items_cache = set()

        self._initial_show = True

        self._is_shutting_down = True 
        self.expiry_at = expiry_at # --- 新增：保存到期时间 ---

        # 标记是否为降级模式

        self.collect_all_emails_mode = True # 【修改】默认开启

        self.playwright_manager = None  # 主爬虫浏览器，按需创建
        self.whatsapp_manager = None         # WhatsApp专用浏览器，按需创建
        self.whatsapp_validation_mode = 'standard' # WhatsApp验证模式，默认为关闭
        
        self.is_degraded_mode = False
        print("Playwright 管理器初始化完成。")

        # 单个商家的最大处理时间（秒）
        self.ITEM_PROCESSING_TIMEOUT = 30

        self.is_paused_for_captcha = False # 用于标记是否因人机验证而暂停

        self.load_timeout_timer = QTimer(self)
        self.load_timeout_timer.setSingleShot(True)  # 设置为单次触发

        self.thread_pool = QThreadPool.globalInstance()

        # 设置一个合理的并发线程数，例如CPU核心数的2倍
        self.thread_pool.setMaxThreadCount(os.cpu_count() * 2) 

        print(f"全局线程池最大线程数: {self.thread_pool.maxThreadCount()}")

        self.active_worker_count = 0

        # 创建并启动数据库工作线程
        self.db_worker = DatabaseWorker()
        self.db_worker.start()



        # 1. 创建一个专属的、线程安全的【邮件任务队列】（生产者队列）
        self.email_task_queue = Queue()

        # 2. 创建一个专属的、线程安全的【邮件结果队列】（消费者->UI）
        self.email_result_queue = Queue()

        # 【资源匹配修复】创建信号量，数量与Playwright页面池大小匹配
        # 这确保EmailFetcherWorker数量不会超过可用的页面池资源，避免资源争抢
        self.email_worker_semaphore_count = min(self.playwright_pool_size, 5)  # 最多5个，避免过度并发
        self.email_worker_semaphore = threading.Semaphore(self.email_worker_semaphore_count)
        print(f"📊 [资源配置] EmailWorker信号量: {self.email_worker_semaphore_count}, Playwright页面池: {self.playwright_pool_size}")

        # 3. 创建并启动一个【独立的、单个的】后台线程，专门用于处理这个队列
        self.email_worker_thread = threading.Thread(target=self._email_worker_loop, daemon=True)
        self.email_worker_thread.start()

        # 4. 创建一个低频的 QTimer 作为"UI更新器"
        self.result_processor_timer = QTimer(self)
        self.result_processor_timer.timeout.connect(self._process_result_queue)
        self.result_processor_timer.start(500) # 每500毫秒检查一次结果队列
        
        # 【UI响应性监控】创建UI响应性监控定时器
        self.ui_responsiveness_timer = QTimer(self)
        self.ui_responsiveness_timer.timeout.connect(self._check_ui_responsiveness)
        self.ui_responsiveness_timer.start(5000)  # 每5秒检查一次UI响应性
        import time
        self._last_ui_check = time.time()
        print("🔧 [UI监控] UI响应性监控已启动，每5秒检查一次")


        # self.username = username
        self.user_id = user_id
        self.credentials = credentials # 保存凭据
        self.user_type = user_type

        self.trial_search_used = trial_search_used
        self.daily_export_count = daily_export_count



        self.is_loading = False
        self.user_triggered_navigation = False
        self.setWindowTitle("mediamingle.cn | Google Maps 自动采集器（增强版）")
        self.setWindowIcon(QIcon(resource_path("img/icon/谷歌地图.ico")))

        # 存储所有运行中的 EmailFetcher 线程
        self.email_fetchers = []
        
        # 存储AI线程
        self.ai_fetchers = [] 

        # 缓存待AI处理的公司信息
        self.ai_batch_queue = []



        # --- 【新增】初始化社媒抓取设置，默认全部开启 ---
        self.social_platforms_to_scrape = {
            'facebook': True,
            'instagram': True,
            'linkedin': True,
            'whatsapp': True
        }

        self.grid_spacing_degrees = 1.0
        self.enable_playwright_fallback = saved_user_settings.get('enable_playwright_fallback', True)

        self.enable_click_animation = saved_user_settings.get('enable_click_animation', True)



        if self.credentials: # 从文件加载社媒平台设置
            username = self.credentials.get('username')
            config = self._load_user_config()
            user_data = config.get("users", {}).get(username, {})
            self.social_platforms_to_scrape = user_data.get('social_platforms', self.social_platforms_to_scrape)
            self.grid_spacing_degrees = user_data.get('grid_spacing', 2.0)
            self.parallel_tasks_count = user_data.get('parallel_tasks', 1)
            self.collect_all_emails_mode = saved_user_settings.get('collect_all_emails_mode', True)
            self.extreme_deep_scan_mode = saved_user_settings.get('extreme_deep_scan_mode', False)
            
        self.resize(width, height)

        # 创建一个集合，用作缓存，快速检查数据是否已处理
        self.processed_items_cache = set()

        main_layout = QVBoxLayout(self)

        if self.user_type in ["standard", "trial"]:
            self.trial_label = QLabel("提示：当前为试用账号，仅允许导出一次数据。")
            self.trial_label.setStyleSheet("""
                QLabel {
                    background-color: #FFF3CD; /* 淡黄色背景 */
                    color: #856404; /* 暗黄色文字 */
                    border: 1px solid #FFEEBA;
                    border-radius: 4px;
                    padding: 8px;
                    font-weight: bold;
                    font-size: 14px;
                }
            """)
            self.trial_label.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(self.trial_label) # 将提示标签添加到主布局顶部

        menu_bar = QMenuBar(self)
        main_layout.setMenuBar(menu_bar) # 将菜单栏添加到主布局的顶部

        view_menu = menu_bar.addMenu("视图 (&V)") # &V 设置快捷键 Alt+V



        # --- 刷新页面 ---
        reload_action = QAction("刷新页面", self)
        reload_action.setShortcut("F5") # 设置 F5 快捷键
        reload_action.triggered.connect(self.reload_page)
        view_menu.addAction(reload_action)

        view_menu.addSeparator() # 添加分隔线

        # --- 缩放功能 ---
        zoom_in_action = QAction("放大", self)
        zoom_in_action.setShortcut("Ctrl++") # 设置 Ctrl+= (等同于Ctrl++) 快捷键
        zoom_in_action.triggered.connect(self.zoom_in)
        view_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("缩小", self)
        zoom_out_action.setShortcut("Ctrl+-") # 设置 Ctrl+- 快捷键
        zoom_out_action.triggered.connect(self.zoom_out)
        view_menu.addAction(zoom_out_action)

        reset_zoom_action = QAction("原始大小", self)
        reset_zoom_action.setShortcut("Ctrl+0") # 设置 Ctrl+0 快捷键
        reset_zoom_action.triggered.connect(self.reset_zoom)
        view_menu.addAction(reset_zoom_action)

        view_menu.addSeparator() # 添加分隔线

        # --- 全屏切换 ---
        self.fullscreen_action = QAction("切换全屏", self)
        self.fullscreen_action.setShortcut("F11")
        self.fullscreen_action.triggered.connect(self.toggle_full_screen)
        view_menu.addAction(self.fullscreen_action)

        # --- 【修改】菜单栏部分 ---
        tools_menu = menu_bar.addMenu("工具 (&T)")

        # --- 【新增】添加“社媒拓客设置”动作 ---
        social_media_action = QAction("社媒拓客设置...", self)
        social_media_action.triggered.connect(self.open_social_media_settings)
        tools_menu.addAction(social_media_action)
        tools_menu.addSeparator() # 添加分隔线

        self.speed_mode_action = QAction("快速抓取模式 (牺牲深度换取速度)", self, checkable=True)
        self.speed_mode_action.setChecked(False) # 默认不勾选
        self.speed_mode_action.toggled.connect(self.toggle_speed_mode) # 连接勾选状态变化的信号
        tools_menu.addAction(self.speed_mode_action)


        self.collect_all_emails_action = QAction("采集全部邮箱 (速度稍慢)", self, checkable=True)
        self.collect_all_emails_action.setChecked(self.collect_all_emails_mode) # 默认不勾选，即默认使用“找到一个最好”的快速模式
        self.collect_all_emails_action.toggled.connect(self.toggle_collect_all_emails_mode)
        tools_menu.addAction(self.collect_all_emails_action)

        self.extreme_deep_scan_action = QAction("极限深度扫描 (非常慢)", self, checkable=True)
        self.extreme_deep_scan_action.setChecked(self.extreme_deep_scan_mode)
        self.extreme_deep_scan_action.toggled.connect(self.toggle_extreme_deep_scan_mode)
        tools_menu.addAction(self.extreme_deep_scan_action)

        tools_menu.addSeparator() # 添加分隔线


        # --- 停止/暂停/继续 搜索 ---
        self.pause_search_action = QAction("暂停搜索", self)
        self.pause_search_action.triggered.connect(self.pause_search)
        self.pause_search_action.setEnabled(False) # 默认禁用
        tools_menu.addAction(self.pause_search_action)

        self.resume_search_action = QAction("继续搜索", self)
        self.resume_search_action.triggered.connect(self.resume_from_pause)
        self.resume_search_action.setVisible(False)
        tools_menu.addAction(self.resume_search_action)

        self.stop_search_action = QAction("中止任务", self) # 将“停止”改为“中止”
        self.stop_search_action.triggered.connect(self.stop_search)
        self.stop_search_action.setEnabled(False) # 默认禁用
        tools_menu.addAction(self.stop_search_action)


        tools_menu.addSeparator() 
        complete_emails_action = QAction("补全当前结果的邮箱/社媒信息", self)
        complete_emails_action.setToolTip("为表格中邮箱和社媒信息为空的条目，重新启动信息提取任务。")
        complete_emails_action.triggered.connect(self.start_completion_task)
        tools_menu.addAction(complete_emails_action)

        tools_menu.addSeparator() # 添加分隔线



        # --- 清除所有结果 ---
        clear_results_action = QAction("清除所有结果", self)
        clear_results_action.triggered.connect(self.clear_all_results)
        tools_menu.addAction(clear_results_action)


        # 创建“帮助”菜单
        help_menu = menu_bar.addMenu("帮助 (&H)") # &H 设置快捷键 Alt+H

        # 创建“访问官网”的动作
        website_action = QAction("访问官网", self)
        website_action.triggered.connect(self.open_website) # 连接点击事件到 open_website 方法
        help_menu.addAction(website_action)

        # 创建“联系我们”的动作
        contact_action = QAction("联系我们", self)
        contact_action.triggered.connect(self.open_contact_page) # 连接点击事件到 open_contact_page 方法
        help_menu.addAction(contact_action)

        # 创建“教程文档”的动作
        tutorial_action = QAction("教程文档", self)
        tutorial_action.triggered.connect(self.open_tutorial_page) # 连接点击事件到我们新加的方法
        help_menu.addAction(tutorial_action)

        # 添加一个分隔线
        help_menu.addSeparator()

        # 创建一个“关于”对话框的动作（推荐）
        about_action = QAction("关于...", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        self.ui_update_queue = []
        self.cell_update_queue = []
        # 用于缓存待更新的单元格信息
        self.ui_update_timer = QTimer(self)
        # 创建一个定时器，每500ms触发一次
        self.ui_update_timer.timeout.connect(self._process_ui_update_queue)
        self.ui_update_timer.start(1000) 

        down_arrow_path = resource_path("img/svg/下拉箭头.svg").replace('\\', '/')
        up_arrow_path = resource_path("img/svg/上箭头.svg").replace('\\', '/')


        # --- 统一样式 ---
        btn_style = """
        QPushButton {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #4CAF50, stop:1 #64B5F6);
            border-radius: 3px;
            color: white;
            padding: 8px 18px;
            font-weight: bold;
            font-family: '微软雅黑';
            font-size: 14px;
            border: none;
        }
        QPushButton:hover {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                                        stop:0 #388E3C, stop:1 #42A5F5);
        }
        QPushButton:pressed {
            background-color: #2E7D32;
        }
        """

        input_style = f"""
        QLineEdit, QComboBox, QTextEdit {{
            font-family: '微软雅黑';
            font-size: 13px;
            font-weight: bold;
            padding: 6px 10px;
            border: 2px solid #4CAF50;
            border-radius: 3px;
            background: #f9fff9;
            color: #222;
            selection-background-color: #81C784;
        }}
        QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
            border-color: #388E3C;
            background: #e6f4ea;
        }}
        QComboBox {{
            min-width: 120px;
            padding-right: 30px; /* 为箭头留出空间 */
            background: #f9fff9;
            border-radius: 3px;
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 24px;
            border-left: 1px solid #4CAF50;
            background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #A5D6A7, stop:1 #81C784);
        }}

        QComboBox::down-arrow {{
            image: url("{down_arrow_path}");
            width: 12px;
            height: 12px;
        }}
        QComboBox::down-arrow:on {{
            image: url("{up_arrow_path}");
        }}

        QComboBox QAbstractItemView {{
            font-family: '微软雅黑';
            font-size: 14px;
            font-weight: bold;
            background: white;
            border: 1px solid #4CAF50;
            selection-background-color: #A5D6A7;
            padding: 4px;
        }}
        QTextEdit {{
            min-height: 80px;
        }}
        QLabel {{
            font-family: '微软雅黑';
            font-size: 14px;
            font-weight: bold;
            color: #333;
            margin-right: 6px;
        }}
        """

        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # 顶部关键词输入 + 批量导入 + 地区+行业筛选
        search_layout = QHBoxLayout()
        search_layout.setSpacing(12)

        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入关键词")
        self.keyword_input.setStyleSheet(input_style)

        search_layout.addWidget(QLabel("关键词:"))
        search_layout.addWidget(self.keyword_input)

        self.import_btn = QPushButton("导入关键词")
        self.import_btn.clicked.connect(self.import_keywords)
        self.import_btn.setStyleSheet(btn_style)
        self.import_btn.setCursor(Qt.PointingHandCursor)
        search_layout.addWidget(self.import_btn)

        self.country_combo = QComboBox()
        self.country_combo.setEditable(True)  # 1. 设置为可编辑
        self.country_completer = QCompleter(self.country_combo.model(), self.country_combo) # 2. 创建补全器
        self.country_completer.setFilterMode(Qt.MatchContains) # 3. 设置模糊匹配
        self.country_completer.setCaseSensitivity(Qt.CaseInsensitive) # 4. 设置不区分大小写
        self.country_combo.setCompleter(self.country_completer) # 5. 应用补全器

        self.country_combo.setStyleSheet(input_style)
        search_layout.addWidget(QLabel("国家筛选:"))
        search_layout.addWidget(self.country_combo)

        # self.region_combo = QComboBox()
        # self.region_combo.setStyleSheet(input_style)
        # search_layout.addWidget(QLabel("地区筛选:"))
        # search_layout.addWidget(self.region_combo)

        # --- 新增：创建自定义的多选下拉框 ---
        self.region_combo = QComboBox()
        self.region_combo.setStyleSheet(input_style)
        
        # 1. 创建一个可以存放带复选框条目的数据模型
        self.region_model = QStandardItemModel(self)
        self.region_combo.setModel(self.region_model)
        
        # 2. 设置下拉列表的视图，使其能够正确显示复选框
        self.region_combo.setView(QListView(self))

        # 3. 连接信号：当模型中的任何条目（比如复选框状态）发生变化时，调用我们的处理函数
        self.region_model.itemChanged.connect(self.handle_region_item_changed)
        
        # 4. 一个临时标志，用于在程序更新文本时阻止信号的递归触发
        self._block_region_signals = False

        search_layout.addWidget(QLabel("地区筛选:"))
        search_layout.addWidget(self.region_combo)

        self.region_bounds = {}

        # 建议设置连接：国家下拉变化时更新地区下拉
        self.country_combo.currentTextChanged.connect(self.update_regions_for_country)

        self.load_regions_with_bounds()  # 加载外部地区列表

        self.industry_combo = QComboBox()
        self.industry_combo.addItem("全部行业")
        # self.industry_combo.addItems(["制造业", "批发", "零售", "服务"])
        self.industry_combo.setStyleSheet(input_style)
        search_layout.addWidget(QLabel("行业筛选:"))
        search_layout.addWidget(self.industry_combo)

        self.search_btn = QPushButton("开始搜索")
        self.search_btn.clicked.connect(self.start_search_batch)
        self.search_btn.setStyleSheet(btn_style)
        self.search_btn.setCursor(Qt.PointingHandCursor)
        search_layout.addWidget(self.search_btn)



        # 新增AI功能UI
        separator = QFrame()
        separator.setFrameShape(QFrame.VLine)
        separator.setFrameShadow(QFrame.Sunken)
        search_layout.addWidget(separator)

        # AI功能开启按钮
        self.ai_toggle_btn = QPushButton("深度获客 (关闭)")
        self.ai_toggle_btn.setCheckable(True)  # 设置为可选中/开关状态
        self.ai_toggle_btn.setChecked(False) # 默认关闭
        self.ai_toggle_btn.toggled.connect(self.on_ai_toggle) # 连接状态切换的信号
        self.ai_toggle_btn.setCursor(Qt.PointingHandCursor)
        self.ai_toggle_btn.setMinimumWidth(180) # 设置最小宽度
        # 为AI按钮设置一个独特的样式
        self.ai_toggle_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; /* 紫色 */
                border-radius: 3px; color: white; padding: 8px 18px;
                font-weight: bold; font-family: '微软雅黑'; font-size: 14px; border: none;
            }
            QPushButton:hover { background-color: #9b59b6; }
            QPushButton:checked { background-color: #27ae60; } /* 开启后的绿色 */
            QPushButton:checked:hover { background-color: #2ecc71; }
            QPushButton:disabled { background-color: #95a5a6; } /* 禁用状态的灰色 */
        """)
        search_layout.addWidget(self.ai_toggle_btn)

        # 显示Token余量的标签
        self.token_label = QLabel("剩余次数: -")
        self.token_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #8e44ad; margin-left: 10px;")
        search_layout.addWidget(self.token_label)

        self.expiry_label = QLabel("授权状态: -")
        self.expiry_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60; margin-left: 15px;")
        search_layout.addWidget(self.expiry_label)

        # 关键词输入框的索引是 1
        search_layout.setStretch(1, 3)  # 给关键词输入框设置一个较高的权重(例如3)
        
        # 国家筛选框的索引是 4
        search_layout.setStretch(4, 2)  # 给国家筛选框一个中等权重(例如2)
        
        # 地区筛选框的索引是 6
        search_layout.setStretch(6, 2)  # 给地区筛选框一个中等权重(例如2)
        
        # 行业筛选框的索引是 8
        search_layout.setStretch(8, 2)  # 给行业筛选框一个中等权重(例如2)

        main_layout.addLayout(search_layout)

        # 进度条
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #4CAF50;
                border-radius: 5px;
                text-align: center;
                font-family: '微软雅黑';
                font-weight: bold;
                color: #333;
                background-color: #E8F5E9;
            }
            QProgressBar::chunk {
                background-color: #66BB6A;
                width: 20px;
                margin: 0.5px;
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        # --- ▼▼▼ 【核心修改】从这里开始替换 ▼▼▼ ---

        # 1. 创建 QTabBar 作为用户可见的标签页切换栏
        self.tab_bar = QTabBar()
        self.tab_bar.setExpanding(False)
        self.tab_bar.setShape(QTabBar.RoundedNorth)
        self.tab_bar.currentChanged.connect(self._on_tab_changed)
        self.tab_bar.setTabsClosable(True) # 启用关闭按钮
        self.tab_bar.tabCloseRequested.connect(self._on_tab_close_requested) # 连接关闭信号
        main_layout.addWidget(self.tab_bar) # 将标签栏添加到主布局

        # 2. 创建一个简单的 QWidget 作为所有浏览器页面的“舞台”
        self.browser_container = QWidget()
        main_layout.addWidget(self.browser_container, stretch=3) # 将“舞台”添加到主布局

        # 3. 初始化状态管理列表
        self.tabs = [] 

        self.watchdog_timers = {}

        # 4. 根据用户设置，循环创建正确数量的页面
        if not hasattr(self, 'parallel_tasks_count'): self.parallel_tasks_count = 1

        for i in range(self.parallel_tasks_count):
            # 调用我们之前创建的、正确的辅助方法来创建页面
            self._create_new_tab(i)
        
        # 5. 默认将第一个页面置于顶层显示
        if self.tabs:
            self.tabs[0]['view'].raise_()

        # 6. 为了兼容旧代码，保留 self.circle_overlay 的赋值
        if self.tabs and 'overlay' in self.tabs[0]:
            self.circle_overlay = self.tabs[0]['overlay']
            


        # 8. 添加倒计时遮罩层
        self.countdown_label = QLabel(self)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 160); color: #FFC107;
            font-size: 24px; font-weight: bold; border-radius: 15px;
        """)
        self.countdown_label.hide()

        # --- ▲▲▲ 替换结束 ▲▲▲ ---

        # 结果表格 (这部分代码保持不变)
        self.table = QTableWidget()

        self.table.setColumnCount(14)
        self.table.setHorizontalHeaderLabels([
            "名称", "地址", "电话", "邮箱", "官网",
            "Facebook", "Instagram", "LinkedIn","WhatsApp", # 新增的列
            "类别", "营业时间", "评分", "评价数", "来源链接"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet("""
            QTableWidget {
                font-family: '微软雅黑';
                font-size: 13px;
                gridline-color: #ccc;
                background-color: #fff;
            }
            QHeaderView::section {
                background-color: #4CAF50;
                color: white;
                padding: 6px;
                font-weight: bold;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: #A5D6A7;
                color: #222;
            }
        """)

        # ==================== 悬浮提示窗逻辑初始化 开始 ====================
        self.info_tooltip = CompanyInfoTooltip(self)
        self.info_tooltip.hide()

        # 创建一个定时器，用于延迟显示提示窗，防止鼠标快速划过时闪烁
        self.hover_timer = QTimer(self)
        self.hover_timer.setSingleShot(True)
        self.hover_timer.timeout.connect(self.show_tooltip)

        self.current_hover_row = -1 # 用于记录当前悬浮的行号

        # 在表格上启用鼠标跟踪
        self.table.setMouseTracking(True)
        # 连接单元格进入信号到我们的处理函数
        self.table.cellEntered.connect(self.on_cell_hovered)
        # 在表格的视口上安装事件过滤器，以捕捉鼠标离开事件
        self.table.viewport().installEventFilter(self)


        main_layout.addWidget(self.table, stretch=2)

        # 导出按钮
        self.export_btn = QPushButton("导出结果 (XLSX/CSV)")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setStyleSheet(btn_style)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(self.export_btn)


        # 初始化变量
        self.keywords = []
        self.is_searching = False

        self.is_speed_mode = False


        # 初始化当前加载类型

        if self.browser is None:
            self.search_btn.setEnabled(False)
            self.keyword_input.setEnabled(False)
            self.region_combo.setEnabled(False)
            self.country_combo.setEnabled(False)
            self.industry_combo.setEnabled(False)
            self.import_btn.setEnabled(False)
            self.export_btn.setEnabled(False)
            self.ai_toggle_btn.setEnabled(False)
            
            error_message = (
                "严重错误：浏览器核心初始化失败！\n\n"
                "这可能是由以下原因造成的：\n"
                "1. 网络连接问题导致浏览器文件下载不完整。\n"
                "2. 杀毒软件或防火墙拦截了程序。\n"
                "3. 当前用户权限不足。\n\n"
                "请尝试以下解决方案：\n"
                "1. 检查网络连接。\n"
                "2. 暂时关闭杀毒软件后重试。\n"
                "3. 以管理员身份重新运行本程序。"
            )
            self.status_bar.showMessage("错误：浏览器核心初始化失败！搜索功能已禁用。")
            QMessageBox.critical(self, "初始化失败", error_message)

        # 【核心修复第一步】：在程序启动时，调用从数据库重新加载数据的方法
        self._reload_data_from_db_to_table()
        


        # 先打开Google Maps首页
        self.user_triggered_navigation = True
        # self.browser.load(QUrl("https://www.google.com/maps"))

        self.check_ai_status()
        self._update_expiry_display()
        self.setStyleSheet(input_style)

        self.check_license_status() # 启动时立即执行一次授权检查以触发弹窗

        self.license_check_timer = QTimer(self)
        self.license_check_timer.timeout.connect(self.check_license_status)
        # 设置为每小时检查一次 (3600 * 1000 毫秒)
        self.license_check_timer.start(7200000)




        if self.user_type in ["standard", "trial"]:
            if self.trial_search_used:
                self.search_btn.setEnabled(False)
                self.search_btn.setText("搜索权限已使用")

            # 【核心修复】在这里增加一个 is not None 的判断
            if self.daily_export_count is not None and self.daily_export_count > 0:
                self.export_btn.setEnabled(False)
                self.export_btn.setText("导出权限已使用")

        print("🚀 [架构] 正在主程序初始化时创建 Playwright 管理器单例...")
        self.playwright_manager = PlaywrightManager(pool_size=self.playwright_pool_size)
        pm_loop = self.playwright_manager._loop
        if pm_loop:
            # 将初始化任务非阻塞地提交到其自己的后台线程
            asyncio.run_coroutine_threadsafe(self.playwright_manager._initialize_internal(), pm_loop)
        else:
            print("❌ 严重错误: Playwright 管理器的事件循环未能启动！")


    def _on_email_task_completed(self, future):
        """
        【流量管制修复版】
        当一个邮件提取任务完成后，此回调函数被触发。
        它除了处理结果，还负责【归还通行令牌】。
        """
        try:
            final_result, row = future.result()
            if final_result:
                self.email_result_queue.put(('result', final_result, row))
            self.email_result_queue.put(('finished', row))
        except Exception as e:
            print(f"❌ 邮件提取的异步任务在后台执行失败: {e}")
            # 【重要】即使任务失败，也必须触发'finished'信号，以便能释放令牌！
            # 我们在这里无法直接获取row，所以发送一个特殊值-1来触发令牌释放
            self.email_result_queue.put(('finished', -1))
        finally:
            # --- ▼▼▼ 【核心修复第三步】归还令牌 ▼▼▼ ---
            # 无论任务成功还是失败，最终都必须释放一个令牌，
            # 这样等待中的“配菜师”才能继续工作。
            self.email_worker_semaphore.release()
            # --- ▲▲▲ 归还令牌结束 ▲▲▲ ---




# (在 GoogleMapsApp 类中，用这个新版本替换旧的 _email_worker_loop 方法)

    def _email_worker_loop(self):
        """
        【流量管制修复版】“配菜师”线程的主循环。
        在处理每个任务前，必须先获取一个“通行令牌”，从而实现对后台任务并发量的严格控制。
        """
        while True:
            try:
                # --- ▼▼▼ 【核心修复第二步】获取令牌 ▼▼▼ ---
                # 1. 在从队列取任务之前，先尝试获取一个令牌。
                #    如果令牌已发完，线程会在这里高效地阻塞等待，直到有任务完成并释放令牌。
                self.email_worker_semaphore.acquire()
                # --- ▲▲▲ 获取令牌结束 ▲▲▲ ---

                # 只有在获得令牌后，才从队列中取出任务来执行
                worker_args = self.email_task_queue.get()

                if worker_args is None:
                    self.email_worker_semaphore.release() # 退出前释放令牌
                    break
                
                # 【资源监控】周期性报告资源使用情况
                if not hasattr(self, '_last_resource_report'):
                    self._last_resource_report = 0
                import time
                current_time = time.time()
                if current_time - self._last_resource_report > 30:  # 每30秒报告一次
                    active_workers = self.email_worker_semaphore_count - self.email_worker_semaphore._value
                    queue_size = self.email_task_queue.qsize()
                    print(f"📊 [资源监控] 活跃Worker: {active_workers}/{self.email_worker_semaphore_count}, 队列任务: {queue_size}")
                    self._last_resource_report = current_time
                
                pm_loop = self.get_playwright_manager()._loop
                if pm_loop:
                    if not hasattr(self, 'global_network_semaphore'):
                        # 【智能限流】根据页面池大小动态调整网络并发数
                        import asyncio  # 【修复】确保asyncio模块在此作用域可用
                        max_concurrent = min(15, self.playwright_pool_size * 3)  # 每个页面最多3个并发请求
                        async def create_semaphore_coro(): return asyncio.Semaphore(max_concurrent)
                        future = asyncio.run_coroutine_threadsafe(create_semaphore_coro(), pm_loop)
                        try:
                            # 【UI响应性修复】使用短超时避免UI阻塞
                            self.global_network_semaphore = future.result(timeout=5)
                            print(f"✅ [架构] 全局网络请求限流阀已创建，最大并发数: {max_concurrent} (基于{self.playwright_pool_size}个页面池)")
                        except asyncio.TimeoutError:
                            print(f"⚠️ 创建网络限流阀超时，使用默认配置")
                            # 创建一个默认的信号量，避免程序崩溃
                            self.global_network_semaphore = asyncio.Semaphore(max_concurrent)

                    # 【UI响应性修复】直接异步执行fetch_email，避免创建Worker对象
                    # 这样可以完全避免UI线程阻塞问题
                    async def async_email_task():
                        worker = EmailFetcherWorker(
                            website=worker_args['website'],
                            company_name=worker_args.get('company_name', ""),
                            address=worker_args['address'],
                            phone=worker_args['phone'],
                            row=worker_args['row'],
                            playwright_manager=self.playwright_manager,
                            global_semaphore=self.global_network_semaphore,
                            country=self.country_combo.currentText(),
                            social_platforms_to_scrape=self.social_platforms_to_scrape,
                            whatsapp_validation_mode=self.whatsapp_validation_mode,
                            whatsapp_manager=self.whatsapp_manager,
                            is_speed_mode=self.is_speed_mode,
                            collect_all_emails_mode=self.collect_all_emails_mode,
                            extreme_deep_scan_mode=self.extreme_deep_scan_mode,
                            enable_playwright_fallback=worker_args.get('enable_playwright_fallback', True)
                        )
                        print(f"🔄 异步Worker启动: {worker.company_name} (行{worker.row})")
                        try:
                            result = await worker.fetch_email()
                            if result is None:
                                print(f"⚠️ 异步Worker超时: {worker.company_name}")
                                return {'email': "Timeout: 页面池繁忙或网络超时"}, worker.row
                            print(f"✅ 异步Worker完成: {worker.company_name}")
                            return result
                        except Exception as e:
                            print(f"❌ 异步Worker异常: {worker.company_name} - {e}")
                            return {'email': f"Error: {type(e).__name__}"}, worker.row
                    
                    future = asyncio.run_coroutine_threadsafe(async_email_task(), pm_loop)
                    future.add_done_callback(self._on_email_task_completed)
                else:
                    print("❌ 严重错误: Playwright 管理器的事件循环未运行！")
                    self.email_worker_semaphore.release() # 出错也要释放令牌

                self.email_task_queue.task_done()

            except Exception as e:
                print(f"❌ 邮件处理后台调度线程发生严重错误: {e}")
                traceback.print_exc()
                # 发生未知异常时，最好也释放一个令牌，防止死锁
                if 'email_worker_semaphore' in self.__dict__:
                    self.email_worker_semaphore.release()

    def _check_ui_responsiveness(self):
        """
        【UI响应性监控】检查UI线程是否响应正常
        """
        import time
        current_time = time.time()
        if hasattr(self, '_last_ui_check'):
            time_diff = current_time - self._last_ui_check
            if time_diff > 7:  # 如果超过7秒才被调用，说明UI可能卡顿
                print(f"⚠️ [UI监控] 检测到UI响应延迟 {time_diff:.1f}秒，可能存在阻塞")
                # 检查活跃的Worker数量
                if hasattr(self, 'email_worker_semaphore'):
                    active_workers = self.email_worker_semaphore_count - self.email_worker_semaphore._value
                    queue_size = self.email_task_queue.qsize() if hasattr(self, 'email_task_queue') else 0
                    print(f"📊 [UI监控] 当前状态 - 活跃Worker: {active_workers}/{self.email_worker_semaphore_count}, 队列: {queue_size}")
            else:
                print(f"✅ [UI监控] UI响应正常 ({time_diff:.1f}s)")
        self._last_ui_check = current_time

    def _process_result_queue(self):
        """
        【新】由 QTimer 在主UI线程中调用的方法。
        它安全地从结果队列中取出数据并更新UI。
        """
        # 为了避免一次处理过多导致UI卡顿，我们每次只处理一部分
        max_updates_per_cycle = 50 
        for _ in range(max_updates_per_cycle):
            if self.email_result_queue.empty():
                break # 队列空了，就停止本次处理
            
            try:
                data = self.email_result_queue.get_nowait()
                signal_type = data[0]
                
                if signal_type == 'result':
                    # 如果是结果消息，调用原来的结果处理器
                    _, result_dict, row = data
                    self.handle_worker_result(result_dict, row)
                elif signal_type == 'finished':
                    # 如果是完成消息，调用原来的完成处理器
                    _, row = data
                    self._on_worker_finished(row)
                    
            except Queue.Empty:
                break
            except Exception as e:
                print(f"❌ 处理结果队列时发生错误: {e}")



    def toggle_extreme_deep_scan_mode(self, checked):
        """处理“极限深度扫描”模式的开关"""
        self.extreme_deep_scan_mode = checked
        if checked:
            QMessageBox.warning(self, "模式切换", "极限深度扫描已开启。\n\n程序将尝试访问网站的所有内部链接（最多20个），\n这会【极大增加】采集耗时，请谨慎使用！")
        else:
            QMessageBox.information(self, "模式切换", "极限深度扫描已关闭。")
        self._update_user_settings({'extreme_deep_scan_mode': checked})


    def _on_tab_changed(self, index):
        """【改造版】当用户点击标签栏时，将被点击的页面提到最顶层显示"""
        if 0 <= index < len(self.tabs):
            # --- ▼▼▼ 【核心修改】使用 raise_() 方法 ▼▼▼ ---
            self.tabs[index]['view'].raise_()

    def _on_tab_close_requested(self, index):
        """
        【新功能】处理用户点击标签页关闭按钮的请求。
        """
        # 1. 安全检查：确保不会关闭最后一个页面
        if self.tab_bar.count() <= 1:
            QMessageBox.warning(self, "操作无效", "无法关闭最后一个采集页面。")
            return

        # 2. 弹窗确认，防止误操作
        reply = QMessageBox.question(self, '确认关闭', 
                                     f'您确定要关闭“采集任务-{index + 1}”吗？\n如果该页面正在执行任务，任务将被中止。',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            return
        
        print(f"🛑 用户请求关闭标签页 {index + 1}...")

        # 3. 在删除前，获取要关闭页面的所有信息
        tab_info_to_close = self.tabs[index]
        browser_view_to_close = tab_info_to_close['view']

        # 4. 停止该页面上可能正在进行的任何活动
        browser_view_to_close.stop() # 停止加载
        tab_info_to_close['state'] = 'closed' # 设置一个特殊状态，让所有回调函数都失效

        # 5. 从UI上移除标签页
        self.tab_bar.removeTab(index)
        
        # 6. 从我们的状态管理列表中移除对应项
        self.tabs.pop(index)
        
        # 7. 【关键】安全地销毁浏览器页面及其关联的资源，释放内存
        #    因为我们将 profile 保存在了 tab_info 中，它会随着 tab_info 被垃圾回收
        #    而 QWebEngineView 需要被显式地调度删除
        browser_view_to_close.deleteLater()
        
        # 8. 更新“同时开启页面数量”的设置
        self.parallel_tasks_count -= 1
        self._update_user_settings({'parallel_tasks': self.parallel_tasks_count})
        
        print(f"✅ 采集页面 {index + 1} 已被安全关闭。当前并行数量已更新为: {self.parallel_tasks_count}")

        # 9. (可选) 如果有任务因为页面关闭而中断，可以考虑将任务重新放回队列
        #    为简化，我们目前的设计是中止任务。
        #    如果需要重新调度，可以在这里将被中止的 task 重新 append 到 self.task_queue 中
        
        # 10. 呼叫一次调度员，看看有没有因为资源释放而可以启动的新任务
        self._dispatch_tasks()


    def toggle_collect_all_emails_mode(self, checked):
        """处理“采集全部邮箱”模式的开关"""
        self.collect_all_emails_mode = checked
        if checked:
            print("✅ [全量采集模式] 已开启。将尽可能多地获取所有高质量邮箱。")
            QMessageBox.information(self, "模式切换", "全量采集模式已开启。\n\n程序将完整扫描网站并返回所有找到的高质量邮箱，速度会稍慢。")
        else:
            print("❌ [快速采集模式] 已开启。将优先寻找一个最佳邮箱并快速返回。")
            QMessageBox.information(self, "模式切换", "快速采集模式已开启（默认）。\n\n程序会优先在首页寻找最佳邮箱，如果找到就立即返回，以获得最快速度。")
        
        # 将这个设置保存到用户的配置文件中
        self._update_user_settings({'collect_all_emails_mode': checked})


    # (在 GoogleMapsApp 类中)

    def showEvent(self, event):
        """
        重写 showEvent 方法。
        这个方法在窗口即将被显示时自动调用，是执行一次性初始定位的最佳时机。
        """
        super().showEvent(event)
        
        if self._initial_show:
            print("✨ 首次触发 showEvent，执行窗口居中操作。")
            try:
                screen_center = QApplication.primaryScreen().availableGeometry().center()
                window_center = self.rect().center()
                self.move(screen_center - window_center)
            except Exception as e:
                print(f"❌ 在 showEvent 中居中主窗口时发生错误: {e}")
            
            # --- ▼▼▼ 【核心修复】在这里添加“暖启动”代码 ▼▼▼ ---
            print("🚀 [预热启动] 主窗口已显示，正在后台悄默声地预热Playwright...")
            self.get_playwright_manager()
            # --- ▲▲▲ 修复结束 ▲▲▲ ---
            
            self._initial_show = False






    # 输入关键词
    def import_keywords(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "导入关键词文件", "",
                                                "CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;Text Files (*.txt)")
        if not file_path:
            return

        ext = os.path.splitext(file_path)[1].lower()
        self.keywords = []

        try:
            if ext == ".csv":
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    for row in reader:
                        for kw in row:
                            kw = kw.strip()
                            if kw:
                                self.keywords.append(kw)

            elif ext in [".xlsx", ".xls"]:
                # 用pandas读取Excel
                df = pd.read_excel(file_path, header=None)
                # 逐行逐列读取所有非空关键词
                for row in df.itertuples(index=False):
                    for kw in row:
                        if isinstance(kw, str):
                            kw = kw.strip()
                            if kw:
                                self.keywords.append(kw)
                        elif pd.notna(kw):
                            self.keywords.append(str(kw).strip())

            elif ext == ".txt":
                # 文本文件按行读取，每行可以包含多个逗号分隔关键词
                with open(file_path, encoding='utf-8') as f:
                    for line in f:
                        kws = line.strip().split(',')
                        for kw in kws:
                            kw = kw.strip()
                            if kw:
                                self.keywords.append(kw)
            else:
                QMessageBox.warning(self, "导入失败", "不支持的文件格式")
                return

            if self.keywords:
                QMessageBox.information(self, "导入成功", f"成功导入 {len(self.keywords)} 个关键词。")
            else:
                QMessageBox.warning(self, "导入失败", "未读取到任何关键词。")

        except Exception as e:
            QMessageBox.warning(self, "导入失败", str(e))

    # 判断是否在搜索(执行调用的首个方法)

    # def start_search_batch(self):

    #     # 在所有操作开始前，就提前调用一次get_playwright_manager。
    #     # 这个调用会非阻塞地在后台启动初始化流程，即“预先暖机”。
    #     self.get_playwright_manager()
    #     # --- 步骤 1: 所有前置检查 (此部分保持不变) ---
    #     if self.whatsapp_validation_mode == 'advanced':
    #         if not self.whatsapp_manager:
    #             print("ℹ️ 高级验证模式已开启，首次初始化WhatsApp管理器... (此过程可能需要一些时间)")
    #             self.whatsapp_manager = WhatsAppManager()
    #             self.whatsapp_manager.login_success_signal.connect(self.show_whatsapp_login_success_message)
    #         if not self.whatsapp_manager.initialization_successful:
    #             print("⏳ 正在等待WhatsApp管理器完成后台初始化...")
    #             self.whatsapp_manager.run_coroutine(self.whatsapp_manager._initialize_browser_internal())
    #             if not self.whatsapp_manager.initialization_successful:
    #                 QMessageBox.critical(self, "WhatsApp 初始化失败", "无法启动用于高级验证的浏览器实例。")
    #                 return

    #     if self.user_type in ["standard", "trial"]:
    #         if self.trial_search_used:
    #             msg_box = QMessageBox(self)
    #             msg_box.setIcon(QMessageBox.Warning)
    #             msg_box.setWindowTitle("搜索限制")
    #             msg_box.setText("<b>您的搜索次数已用尽！</b>")
    #             msg_box.setInformativeText("试用账号仅允许执行一次搜索。如需继续使用，请升级到正式版。")
    #             activate_button = msg_box.addButton("开通正式账号", QMessageBox.ActionRole)
    #             later_button = msg_box.addButton("稍后", QMessageBox.AcceptRole)
    #             msg_box.exec_()
    #             if msg_box.clickedButton() == activate_button:
    #                 print("用户点击“开通正式账号”，正在跳转到网站...")
    #                 url = QUrl("https://mediamingle.cn/checkout.html") 
    #                 QDesktopServices.openUrl(url)
    #             return
    #         self._send_action_to_backend("search")
    #         self.trial_search_used = True

    #     print("ℹ️ 启动搜索前，正在预检查深度采集环境 (Playwright)...")
    #     self.get_playwright_manager()
        
    #     # --- 步骤 2: 弹窗确认操作 (此部分保持不变) ---
    #     msg_box = QMessageBox(self)
    #     msg_box.setWindowTitle("开始新的搜索")
    #     msg_box.setText("您希望如何处理之前的结果？")
    #     msg_box.setIcon(QMessageBox.Question)
    #     append_button = msg_box.addButton("保留并追加", QMessageBox.AcceptRole)
    #     clear_button = msg_box.addButton("清除并开始新的", QMessageBox.DestructiveRole)
    #     cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
    #     msg_box.exec_()
    #     clicked_button = msg_box.clickedButton()

    #     if clicked_button == cancel_button:
    #         return
    #     if clicked_button == clear_button:
    #         print("用户选择清除旧数据...")
    #         self.db_worker.clear_all_companies_blocking()
    #         self.table.setRowCount(0)
    #         self.processed_items_cache.clear()
    #         QMessageBox.information(self, "操作完成", "所有旧数据已被清除。")

    #     # --- ▼▼▼ 【核心修改】从这里开始是全新的、简化的启动逻辑 ▼▼▼ ---
    #     # 准备一个临时的关键词列表，只用于本次即将开始的搜索
    #     current_search_keywords = []

    #     # 2. 优先从UI输入框获取关键词。
    #     kw_from_input = self.keyword_input.text().strip()
    #     if kw_from_input:
    #         # 如果输入框有内容，就把它作为本次搜索的关键词列表
    #         current_search_keywords = [kw_from_input]
    #         print(f"  -> 检测到输入框内容，将使用新关键词: {current_search_keywords}")
    #     else:
    #         # 如果输入框为空，则检查是否存在由“导入”功能填充的关键词列表
    #         # (self.keywords 在这里可能还保留着上一次搜索的值)
    #         if self.keywords:
    #             current_search_keywords.extend(self.keywords)
    #             print(f"  -> 输入框为空，将使用之前导入的 {len(self.keywords)} 个关键词。")

    #     # 3. 最终检查是否得到了任何关键词
    #     if not current_search_keywords:
    #         QMessageBox.warning(self, "提示", "请输入关键词或通过“导入关键词”按钮添加。")
    #         return

    #     # 4. 【关键】用本次搜索的关键词列表，彻底覆盖掉可能残留的旧列表
    #     self.keywords = current_search_keywords
    #     print(f"✅ 本次搜索已确认，将使用以下关键词: {self.keywords}")
                
    #     # 步骤 4: 生成任务队列
    #     self.task_queue = []
    #     self._generate_all_region_tasks() # 调用任务生成器，填充队列

    #     if not self.task_queue:
    #         QMessageBox.warning(self, "无任务", "未能根据您的设置生成任何搜索任务。")
    #         return
        
    #     # 步骤 5: 设置程序状态为“运行中”并更新UI
    #     self.is_searching = True
    #     self.stop_search_action.setEnabled(True)
    #     self.pause_search_action.setEnabled(True)
    #     self.pause_search_action.setVisible(True)
    #     self.resume_search_action.setVisible(False)
        
    #     # 初始化进度条
    #     self.progress_bar.setValue(0)
    #     # --- ▼▼▼ 【核心修复】修改此处的文本格式 ▼▼▼ ---
    #     self.progress_bar.setMaximum(len(self.task_queue))
    #     self.progress_bar.setFormat(f"准备开始... (共 {len(self.task_queue)} 个地区)")
    #     # --- ▲▲▲ 修复结束 ▲▲▲ ---
    #     self.progress_bar.show()

    #     # 步骤 6: 【关键】调用“任务调度员”来启动并行采集
    #     self._dispatch_tasks()



    def start_search_batch(self):
        """【最终异步修复版】启动批量搜索的总入口"""
        
        # 保留：提前“预热”Playwright管理器，此操作是非阻塞的
        self.get_playwright_manager()
        
        # 步骤 1: 检查是否需要进行耗时的WhatsApp初始化
        if self.whatsapp_validation_mode == 'advanced':
            # 懒加载WhatsAppManager
            if not self.whatsapp_manager:
                self.whatsapp_manager = WhatsAppManager()
                self.whatsapp_manager.login_success_signal.connect(self.show_whatsapp_login_success_message)
            
            # 【关键】如果后台浏览器还未初始化成功...
            if not self.whatsapp_manager.initialization_successful:
                print("⏳ 检测到WhatsApp高级模式开启且未初始化，正在启动后台初始化线程...")
                
                # --- ▼▼▼ 【核心修复】使用非阻塞的QThread方式启动初始化 ▼▼▼ ---
                self.wa_init_thread = QThread()
                self.wa_init_worker = WhatsAppInitWorker(self.whatsapp_manager)
                self.wa_init_worker.moveToThread(self.wa_init_thread)
                
                self.wa_init_thread.started.connect(self.wa_init_worker.run)
                self.wa_init_worker.finished.connect(self._on_whatsapp_init_finished)
                self.wa_init_thread.finished.connect(self.wa_init_thread.deleteLater)
                self.wa_init_worker.finished.connect(self.wa_init_worker.deleteLater)
                
                self.wa_init_thread.start()
                
                QMessageBox.information(self, "后台准备中", "WhatsApp高级验证功能正在后台初始化（首次启动约需30-60秒），\n初始化完成后搜索会自动开始。\n\n此过程不会影响您操作界面。")
                
                # 直接返回，不执行后续搜索逻辑。后续逻辑将由 _on_whatsapp_init_finished 触发
                return 
                # --- ▲▲▲ 修复结束 ▲▲▲ ---

        # 如果不需要初始化，或者初始化已完成，则直接执行搜索逻辑
        self._execute_search_logic()

    def _on_whatsapp_init_finished(self, success):
        """
        【新增】一个处理WhatsApp初始化完成信号的槽函数。
        这个函数在后台初始化完成后，在主UI线程中被安全地调用。
        """
        if success:
            print("✅ WhatsApp后台初始化成功！现在正式开始搜索任务...")
            self._execute_search_logic() # 初始化成功，执行真正的搜索逻辑
        else:
            QMessageBox.critical(self, "WhatsApp 初始化失败", "无法启动用于高级验证的浏览器实例，请检查网络或重启程序。")
            # 初始化失败，可以考虑重置UI状态
            self.is_searching = False
            self.stop_search_action.setEnabled(False)
            self.pause_search_action.setEnabled(False)

    def _execute_search_logic(self):
        """
        【新增】将原 start_search_batch 中所有与“开始一次新搜索”相关的逻辑，都移到这里。
        """
        # 包含了所有原 start_search_batch 方法中从“步骤2: 弹窗确认操作”开始的全部代码
        
        if self.user_type in ["standard", "trial"]:
            if self.trial_search_used:
                msg_box = QMessageBox(self)
                msg_box.setIcon(QMessageBox.Warning)
                msg_box.setWindowTitle("搜索限制")
                msg_box.setText("<b>您的搜索次数已用尽！</b>")
                msg_box.setInformativeText("试用账号仅允许执行一次搜索。如需继续使用，请升级到正式版。")
                activate_button = msg_box.addButton("开通正式账号", QMessageBox.ActionRole)
                later_button = msg_box.addButton("稍后", QMessageBox.AcceptRole)
                msg_box.exec_()
                if msg_box.clickedButton() == activate_button:
                    print("用户点击“开通正式账号”，正在跳转到网站...")
                    url = QUrl("https://mediamingle.cn/checkout.html") 
                    QDesktopServices.openUrl(url)
                return
            self._send_action_to_backend("search")
            self.trial_search_used = True
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("开始新的搜索")
        msg_box.setText("您希望如何处理之前的结果？")
        msg_box.setIcon(QMessageBox.Question)
        append_button = msg_box.addButton("保留并追加", QMessageBox.AcceptRole)
        clear_button = msg_box.addButton("清除并开始新的", QMessageBox.DestructiveRole)
        cancel_button = msg_box.addButton("取消", QMessageBox.RejectRole)
        msg_box.exec_()
        clicked_button = msg_box.clickedButton()

        if clicked_button == cancel_button:
            return
        if clicked_button == clear_button:
            print("用户选择清除旧数据...")
            self.db_worker.clear_all_companies_blocking()
            self.table.setRowCount(0)
            self.processed_items_cache.clear()
            QMessageBox.information(self, "操作完成", "所有旧数据已被清除。")

        # 重置状态并重新获取关键词 (这部分逻辑保持您之前修复后的版本)
        current_search_keywords = []
        kw_from_input = self.keyword_input.text().strip()
        if kw_from_input:
            current_search_keywords = [kw_from_input]
        elif self.keywords:
            current_search_keywords.extend(self.keywords)
        
        if not current_search_keywords:
            QMessageBox.warning(self, "提示", "请输入关键词或通过“导入关键词”按钮添加。")
            return

        self.keywords = current_search_keywords
        self.task_queue = []
        self._generate_all_region_tasks()
            
        if not self.task_queue:
            QMessageBox.warning(self, "无任务", "未能根据您的设置生成任何搜索任务。")
            return
        
        # 设置程序状态、UI和启动任务 (这部分逻辑也保持不变)
        self.is_searching = True
        self.stop_search_action.setEnabled(True)
        self.pause_search_action.setEnabled(True)
        self.pause_search_action.setVisible(True)
        self.resume_search_action.setVisible(False)
        
        self.progress_bar.setValue(0)
        self.progress_bar.setMaximum(len(self.task_queue))
        self.progress_bar.setFormat(f"准备开始... (共 {len(self.task_queue)} 个地区)")
        self.progress_bar.show()
        
        self._dispatch_tasks()



# 在 class GoogleMapsApp(QWidget): 中
    def _dispatch_tasks(self):
        """
        【并发渲染修复版】核心任务调度员
        - 增加了对 scraper_semaphore 的使用，限制同时活跃的地图采集页面数量。
        """
        # 1. 检查任务是否全部完成的逻辑（保持不变）
        is_fully_completed = (
            not self.task_queue and
            all(tab['state'] == 'idle' for tab in self.tabs) and
            self.active_worker_count == 0 and
            self.email_result_queue.empty()
        )

        if is_fully_completed:
            if not self.ui_update_queue and not self.cell_update_queue:
                print("✅✅✅ 所有并行任务及后台邮件提取均已完成！")
                self.is_searching = False
                self.stop_search_action.setEnabled(False)
                self.pause_search_action.setEnabled(False)
                
                self.progress_bar.setValue(self.progress_bar.maximum())
                self.progress_bar.setFormat("所有任务已完成！")

                QMessageBox.information(self, "任务完成", "所有地区的并行采集任务均已完成。")
            else:
                QTimer.singleShot(500, self._dispatch_tasks)
            return
        
        # --- ▼▼▼ 【核心修复】从这里开始是修改后的任务分配逻辑 ▼▼▼ ---

        # 2. 遍历所有空闲的标签页
        for i, tab_info in enumerate(self.tabs):
            # 检查条件：标签页空闲 并且 任务队列里有任务
            if tab_info['state'] == 'idle' and self.task_queue:
                
                # a. 【关键】在分配任务前，尝试获取一个“采集许可”。
                #    使用 non-blocking 模式，如果获取不到（说明活跃页面已达上限），
                #    就立即返回 false，我们则跳过这个标签页，等下次调度再试。
                if not self.scraper_semaphore.acquire(blocking=False):
                    # print(f"  -> (标签页 {i+1}) 采集限流阀已满，本轮调度跳过。")
                    continue # 跳到下一个空闲标签页

                # b. 如果成功获取到许可，说明可以开始工作了
                print(f"  -> ✅ (标签页 {i+1}) 已获取采集许可，准备分配任务...")
                
                # c. 从任务队列中取出一个任务 (这部分逻辑不变)
                task = self.task_queue.pop(0)
                tab_info['state'] = 'running'
                tab_info['current_task'] = task
                print(f"🚀 分配任务 [{task['keyword']} - {task['region_name']}] 给标签页 {i+1}")
                
                # d. 启动采集 (这部分逻辑不变)
                self._start_scraping_on_tab(i, task)
        # --- ▲▲▲ 修复结束 ▲▲▲ ---



    # 在 class GoogleMapsApp 中，用这个【修正版】函数完整替换旧的同名函数



    def _start_scraping_on_tab(self, tab_index, task):
        """【看门狗修复版 v3】让指定的标签页开始执行一个采集任务，并启动超时监控"""
        if not self.is_searching: return
        
        tab_info = self.tabs[tab_index]
        browser_view = tab_info['view']
        
        # --- 1. 更新总进度条 (逻辑不变) ---
        total_tasks = len(self.task_queue) + sum(1 for t in self.tabs if t['state'] == 'running')
        initial_total = self.progress_bar.maximum()
        completed_tasks = initial_total - total_tasks
        self.progress_bar.setValue(completed_tasks)
        current_keyword = task.get('keyword', '未知')
        self.progress_bar.setFormat(f"关键词: {current_keyword} | 总进度: {completed_tasks} / {initial_total} 个地区")
        
        print(f"  -> 标签页 {tab_index+1} 正在加载URL: {task['url']}")
        
        # --- 2. 【核心修复】大幅缩短看门狗定时器 ---
        # 将超时从 480000ms (8分钟) 调整为 90000ms (90秒)
        REGION_TASK_TIMEOUT = 90000 
        
        if tab_index in self.watchdog_timers:
            self.watchdog_timers[tab_index].stop()
            del self.watchdog_timers[tab_index]
            
        watchdog = QTimer(self)
        watchdog.setSingleShot(True)
        watchdog.timeout.connect(lambda: self.on_region_task_timeout(tab_index))
        watchdog.start(REGION_TASK_TIMEOUT)
        self.watchdog_timers[tab_index] = watchdog
        print(f"  -> ⏱️ (标签页 {tab_index+1}) 已启动 {REGION_TASK_TIMEOUT / 1000} 秒的看门狗定时器。")
        
        # --- 3. 设置页面模式并加载URL (逻辑不变) ---
        browser_view.settings().setAttribute(QWebEngineSettings.AutoLoadImages, not self.is_speed_mode)
        
        def connect_load_finished():
            def on_load_finished(ok):
                try: browser_view.loadFinished.disconnect(on_load_finished)
                except TypeError: pass
                
                if not ok:
                    print(f"❌ (标签页 {tab_index+1}) 页面加载失败，将由看门狗处理或手动跳过。")
                    self.finish_region_extraction(tab_index)
                    return
                
                self.wait_for_search_results(tab_index, task['zoom'])
            
            try: browser_view.loadFinished.disconnect()
            except TypeError: pass
            browser_view.loadFinished.connect(on_load_finished)

        connect_load_finished()
        browser_view.load(QUrl(task['url']))


    def on_poller_timeout(self, tab_index):
        """【新增】当哨兵轮询超时后，此函数被调用"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        
        # 检查定时器是否还存在，并确保页面仍在运行
        if '_poller_watchdog' in tab_info and tab_info['state'] == 'running':
            print(f"🚨 (标签页 {tab_index+1}) 哨兵轮询超时（15秒），强制跳过当前商家。")
            
            # 清理定时器
            del tab_info['_poller_watchdog']
            
            # 调用“完成并继续”的函数，让程序流程继续下去
            self.after_extraction_and_move_on(tab_index)


    def on_region_task_timeout(self, tab_index):
        """当某个地区的抓取任务总时长超时后，此函数被调用"""
        # 安全检查，防止窗口已关闭或任务已结束
        if tab_index >= len(self.tabs) or not self.is_searching:
            return
            
        tab_info = self.tabs[tab_index]
        
        # 再次确认这个标签页是否还在运行同一个任务 
        if tab_info['state'] == 'running':
            task_name = tab_info['current_task']['region_name'] if tab_info['current_task'] else "未知"
            print(f"🚨 【看门狗超时】(标签页 {tab_index+1}) 处理地区 '{task_name}' 超时！")
            print(f"  -> 强制中止当前任务，并准备处理下一个地区...")
            
            # 停止页面上的一切活动（加载、JS等）
            tab_info['view'].stop()
            
            # 直接调用任务结束函数，它会负责所有清理工作并调度新任务
            self.finish_region_extraction(tab_index)
        


    def _on_tab_load_timeout(self, tab_index, timer):
        """【新】处理单个标签页加载超时"""
        timer.stop()
        if tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] == 'running':
            print(f"❌ 标签页 {tab_index+1} 加载超时，强制结束当前任务。")
            tab_info['view'].stop()
            self.finish_region_extraction(tab_index)



    def wait_for_search_results(self, tab_index, current_zoom):
        """【改造版】等待指定标签页的搜索结果出现"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return
        
        browser_view = tab_info['view']
        tab_info['current_zoom'] = current_zoom
        
        check_js = "(function() { if (document.querySelector('h1.DUwDvf.lfPIob')) return 'single_result'; if (document.querySelector('iframe[src*=\"recaptcha\"]')) return 'captcha'; if (document.querySelector('a.hfpxzc')) return 'found'; if (document.querySelector('.jftiEf.fontBodyMedium') || document.querySelector('div.m6QErb.DxyBCb.kA9KIf.dS8AEf')) return 'no_results_page'; return 'not_found'; })();"

        def handle_check(result):
            if not self.is_searching or tab_index >= len(self.tabs) or self.tabs[tab_index]['state'] != 'running': return

            if result == 'found':
                print(f"✅ (标签页 {tab_index+1}) 检测到结果列表，开始提取。")
                self.tabs[tab_index]['current_item_index'] = 0
                self._scroll_and_extract_loop(tab_index, previous_count=0)
            elif result == 'single_result':
                print(f"✅ (标签页 {tab_index+1}) 检测到单个商家页面，开始提取。")
                self.extract_results_for_single_page(tab_index)
            else:
                print(f"❌ (标签页 {tab_index+1}) 未找到结果或超时，结束当前任务。")
                self.finish_region_extraction(tab_index)
        
        browser_view.page().runJavaScript(check_js, handle_check)


    def extract_results_for_single_page(self, tab_index):
        """【改造版】提取单个页面"""
        browser_view = self.tabs[tab_index]['view']
        browser_view.page().runJavaScript(self.JS_EXTRACT_SINGLE_PAGE_DETAIL, 
            lambda result, idx=tab_index: self.handle_single_result_data(result, idx))



    def handle_single_result_data(self, result, tab_index):
        """
        【新增】【改造版】处理单个商家页面的提取结果。
        此方法适配了并行化，能够进行线程安全的去重，并调用其他改造后的方法。
        """
        # --- 安全检查 ---
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        # --- 核心逻辑 ---
        try:
            if result:
                result['link'] = tab_info['view'].url().toString()
            
            if not result or not result.get('name'):
                print(f"🔵 (标签页 {tab_index+1}) 单个页面提取数据无效，结束任务。")
                self.finish_region_extraction(tab_index)
                return

            item_name = result.get('name', '').strip()
            item_address = result.get('address', '').strip()
            unique_key = f"{item_name}|{item_address}"

            is_duplicate = False
            with self.cache_lock:
                if unique_key in self.processed_items_cache:
                    is_duplicate = True
            
            if is_duplicate:
                print(f"🔵 (标签页 {tab_index+1}) 单个页面发现重复数据，准备降级重试: {item_name}")
                # 调用同样被改造过的“降级重试”方法
                self._retry_search_with_lower_zoom(tab_index)
                return
            
            # 如果不是重复数据，则交给最终处理器
            self._process_final_data(result, is_single_page=True, tab_index=tab_index)

        except Exception as e:
            print(f"❌ (标签页 {tab_index+1}) 处理单个商家页面结果时发生错误: {e}")
            traceback.print_exc()
            self.finish_region_extraction(tab_index)


    # MODIFIED: 替换此方法
    def _generate_all_region_tasks(self):
        """
        【新】任务生成器，取代旧的 search_next_keyword。
        它会遍历所有关键词和地区，生成完整的任务列表并放入 self.task_queue。
        """
        # 这个方法的主体就是原来 search_next_keyword 的逻辑
        # 但它现在会遍历所有关键词，而不是只处理当前的一个。
        
        for keyword in self.keywords:
            country = self.country_combo.currentText()
            
            # 1. 初始化当前关键词的坐标列表
            national_sweep_coords = []
            specific_coords = []
            
            # 2. 全国概览逻辑 (保持不变)
            for i in range(self.region_model.rowCount()):
                item = self.region_model.item(i)
                if item.checkState() == Qt.Checked and item.text() == '全国概览':
                    region_data = self.get_region_data_by_name(country, '全国概览')
                    if region_data and "coords" in region_data:
                        for coord in region_data["coords"]:
                            national_sweep_coords.append({
                                "lat": coord.get("latitude"), 
                                "lon": coord.get("longitude"),
                                "zoom": coord.get("zoom", 8),
                                "name": f"全国概览点 for {country}" # 添加名称以便调试
                            })
                    break
            
            # 3. 获取用户选择的地区列表 (保持不变)
            selected_regions = [self.region_model.item(i).text() for i in range(self.region_model.rowCount()) if self.region_model.item(i).checkState() == Qt.Checked and self.region_model.item(i).text() != '全国概览']

            # 4. 根据地区数量，智能选择“虚拟网格”或“逐个地区”扫描策略 (保持不变)
            total_regions_in_country = len(self.region_data_by_country.get(country, []))

            if total_regions_in_country > 50 and selected_regions:
                # --- 策略一：虚拟网格 ---
                print(f"✅ 关键词 '{keyword}' 在国家 '{country}' 启用“虚拟网格”策略。")
                # ... (此部分虚拟网格的计算逻辑保持原样) ...
                GRID_SPACING_DEGREES = self.grid_spacing_degrees
                min_lat, max_lat, min_lon, max_lon = 90, -90, 180, -180
                regions_to_process = selected_regions
                if "全部地区" in selected_regions:
                    regions_to_process = [r['name'] for r in self.region_data_by_country.get(country, []) if r['name'] not in ['全国概览', '全部地区']]
                
                for region_name in regions_to_process:
                    region_data = self.get_region_data_by_name(country, region_name)
                    if not region_data: continue
                    
                    # --- ▼▼▼ 【核心修复】用下面这个 if...elif... 结构替换旧的 if 结构 ▼▼▼ ---
                    
                    if "bounds" in region_data:
                        # 1. 优先处理有 "bounds" 的情况
                        b = region_data["bounds"]
                        min_lat = min(min_lat, b.get("latitude_min", 90))
                        max_lat = max(max_lat, b.get("latitude_max", -90))
                        min_lon = min(min_lon, b.get("longitude_min", 180))
                        max_lon = max(max_lon, b.get("longitude_max", -180))
                    elif "latitude" in region_data and "longitude" in region_data:
                        # 2. 【新增逻辑】如果没有 "bounds"，但有中心点坐标，也用它来更新范围
                        lat, lon = region_data["latitude"], region_data["longitude"]
                        min_lat = min(min_lat, lat)
                        max_lat = max(max_lat, lat)
                        min_lon = min(min_lon, lon)
                    max_lon = max(max_lon, lon)
                
                if min_lat <= max_lat and min_lon <= max_lon:
                    lat = min_lat
                    while lat <= max_lat:
                        lon = min_lon
                        while lon <= max_lon:
                            specific_coords.append({"lat": lat, "lon": lon, "zoom": 12, "name": f"网格点({lat:.2f}, {lon:.2f})"})
                            lon += GRID_SPACING_DEGREES
                        lat += GRID_SPACING_DEGREES
            
            elif selected_regions:
                # --- 策略二：逐个地区扫描 ---
                print(f"✅ 关键词 '{keyword}' 在国家 '{country}' 启用“逐个地区”精准扫描策略。")
                regions_to_process = selected_regions
                if "全部地区" in selected_regions:
                    regions_to_process = [r['name'] for r in self.region_data_by_country.get(country, []) if r['name'] not in ['全国概览', '全部地区']]
                for region_name in regions_to_process:
                    region_data = self.get_region_data_by_name(country, region_name)
                    if not region_data: continue
                    lat, lon, zoom = None, None, 12
                    if "latitude" in region_data and "longitude" in region_data:
                        lat, lon, zoom = region_data["latitude"], region_data["longitude"], region_data.get("zoom", 12)
                    elif "bounds" in region_data:
                        b = region_data["bounds"]
                        lat, lon, zoom = (b.get("latitude_min", 0) + b.get("latitude_max", 0)) / 2, (b.get("longitude_min", 0) + b.get("longitude_max", 0)) / 2, b.get("zoom", 10)
                    if lat is not None and lon is not None:
                        specific_coords.append({"lat": lat, "lon": lon, "zoom": zoom, "name": region_name})
            
            # 5. 组合当前关键词的所有坐标点
            search_coords_for_this_keyword = national_sweep_coords + specific_coords
            
            # 6. 【核心】为每个坐标点生成任务，并添加到总任务队列
            for coord_info in search_coords_for_this_keyword:
                latitude = coord_info['lat']
                longitude = coord_info['lon']
                zoom = coord_info['zoom']
                country_code = COUNTRY_TO_CODE.get(country)
                
                search_str = f"{keyword} in {country}" if country else keyword
                encoded = quote(search_str)
                
                url = f"https://www.google.com/maps/search/{encoded}/@{latitude},{longitude},{zoom}z"
                if country_code:
                    url += f"&gl={country_code}"

                task = {
                    'keyword': keyword,
                    'region_name': coord_info.get('name', f"坐标({latitude:.2f}, {longitude:.2f})"),
                    'url': url,
                    'zoom': zoom
                }
                self.task_queue.append(task)
                
        print(f"✅ 任务生成完毕，总计 {len(self.task_queue)} 个地区待采集。")


    def get_region_data_by_name(self, country, region_name):
        """根据国家和地区名，从已加载的数据中查找完整的地区信息字典"""
        if not hasattr(self, 'region_data_by_country'):
            return None
        country_regions = self.region_data_by_country.get(country, [])
        for region_data in country_regions:
            if region_data.get("name") == region_name:
                return region_data
        return None








    # 根据item是否被选中来更新其背景颜色
    def update_region_selection_style(self):
        """根据item是否被选中来更新其背景颜色"""
        for i in range(self.region_list_widget.count()):
            item = self.region_list_widget.item(i)
            if item.isSelected():
                # 设置为浅绿色背景
                item.setBackground(Qt.green) 
            else:
                # 恢复为透明背景
                item.setBackground(Qt.transparent)

    def handle_region_item_changed(self, item):
        """
        【交互优化版】当地区列表中的复选框状态改变时调用此函数。
        1. 实现“全部地区”与其他地区的互斥选择。
        2. 强制实时更新下拉框的显示文本。
        """
        if self._block_region_signals:
            return

        # 暂时阻止信号的递归触发
        self._block_region_signals = True
        
        # 判断被点击的条目是否是“全部地区”
        is_all_regions = (item.data(Qt.UserRole) == "all_regions_role")

        if item.checkState() == Qt.Checked:
            if is_all_regions:
                # 如果勾选了“全部地区”，则取消其他所有地区的勾选
                for i in range(self.region_model.rowCount()):
                    other_item = self.region_model.item(i)
                    if other_item is not item:
                        other_item.setCheckState(Qt.Unchecked)
            else:
                # 如果勾选了其他任何地区，则取消“全部地区”的勾选
                for i in range(self.region_model.rowCount()):
                    all_regions_candidate = self.region_model.item(i)
                    if all_regions_candidate.data(Qt.UserRole) == "all_regions_role":
                        all_regions_candidate.setCheckState(Qt.Unchecked)
                        break
        
        # 在所有逻辑处理完毕后，重新启用信号
        self._block_region_signals = False
        
        # 【核心】无论如何，都强制调用一次文本更新
        self.update_region_selection_text()

    def update_region_selection_text(self):
        """
        【修复版】根据当前勾选状态，更新地区下拉框的显示文本。
        该版本能正确处理“全部地区”的显示逻辑。
        """
        selected_regions = []
        is_all_regions_selected = False

        # 1. 遍历所有条目，区分“全部地区”和其他地区
        for i in range(self.region_model.rowCount()):
            item = self.region_model.item(i)
            if item.checkState() == Qt.Checked:
                if item.data(Qt.UserRole) == "all_regions_role":
                    is_all_regions_selected = True
                    # 找到了“全部地区”，就不需要再关心其他地区了
                    break 
                else:
                    selected_regions.append(item.text())
        
        # 2. 根据检查结果，更新显示文本
        if is_all_regions_selected:
            # 如果“全部地区”被勾选，直接显示它
            self.region_combo.setCurrentText("全部地区")
        elif not selected_regions:
            # 如果列表为空（且“全部地区”也没被选），显示提示
            self.region_combo.setCurrentText("请选择地区")
        elif len(selected_regions) <= 2:
            # 如果选择的地区不多，直接显示名称
            self.region_combo.setCurrentText(", ".join(selected_regions))
        else:
            # 如果选择的地区很多，显示数量
            self.region_combo.setCurrentText(f"已选择 {len(selected_regions)} 个地区")


    # 根据地区返回精度
    def get_region_bounds(self, country, area):
        if not hasattr(self, 'region_data_by_country'):
            self.load_regions_with_bounds()

        if country not in self.region_data_by_country:
            return None

        regions = self.region_data_by_country[country]

        # 选择“全部地区”时，返回所有地区的边界或坐标
        if area in (None, "", "全部地区"):
            all_coords = []
            for r in regions:
                if r.get("name") == "全部地区": continue
                
                if "bounds" in r:
                    # 计算边界中心点
                    lat = (r["bounds"].get("latitude_min", -90) + r["bounds"].get("latitude_max", 90)) / 2
                    lon = (r["bounds"].get("longitude_min", -180) + r["bounds"].get("longitude_max", 180)) / 2
                    all_coords.append({"latitude": lat, "longitude": lon})
                elif "latitude" in r and "longitude" in r:
                    # 直接使用具体坐标
                    all_coords.append({"latitude": r["latitude"], "longitude": r["longitude"]})
            return all_coords  # 返回所有地区的坐标列表

        # 查找具体地区的边界或坐标
        for r in regions:
            if r.get("name") == area:
                if "bounds" in r:
                    return [r["bounds"]]  # 返回单一边界
                elif "latitude" in r and "longitude" in r:
                    # 构造一个很小的边界框，附近0.01度范围
                    lat = r["latitude"]
                    lon = r["longitude"]
                    return [{
                        "latitude_min": lat - 0.005,
                        "latitude_max": lat + 0.005,
                        "longitude_min": lon - 0.005,
                        "longitude_max": lon + 0.005
                    }]
        return None




    # 在开始等待时，记录时间
    def start_search_for_region(self, region):
        # ...
        self.current_wait_start_time = time.time() # 记录开始等待的时间
        self.wait_for_search_results()



    # 等待元素出现


    




    def _scroll_and_extract_loop(self, tab_index, previous_count):
        """【改造版】滚动与提取的核心循环"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return
        
        browser_view = tab_info['view']
        js_get_count = "document.querySelectorAll('a.hfpxzc').length;"
        browser_view.page().runJavaScript(js_get_count, 
            lambda count, idx=tab_index, prev_c=previous_count: self._handle_count_check(count, prev_c, idx))



    def _handle_count_check(self, current_count, previous_count, tab_index):
        """【改造版】处理元素数量检查的结果"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        if current_count == previous_count and previous_count > 0:
            print(f"🛑 (标签页 {tab_index+1}) 滚动到底部，当前地区抓取完成。")
            self.finish_region_extraction(tab_index)
            return

        current_item_index = tab_info.get('current_item_index', 0)
        print(f"🔄 (标签页 {tab_index+1}) 列表有 {current_count} 个结果，上次处理到 {current_item_index}。")

        if current_item_index < current_count:
            self._process_next_item(tab_index)
        else:
            self._scroll_and_wait(tab_index, current_count)


    def _process_next_item(self, tab_index):
        """【改造版】处理列表中的下一个商家"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        current_item_index = tab_info.get('current_item_index', 0)
        browser_view = tab_info['view']
        
        js_pre_check = f"(function(index) {{ const elems = document.querySelectorAll('a.hfpxzc'); if (index >= elems.length) return {{ is_end: true }}; const container = elems[index].closest('.Nv2PK'); if (!container) return {{ name: null, address: null }}; const nameEl = container.querySelector('.qBF1Pd'); const addressEl = container.querySelectorAll('.W4Efsd > span > span')[1]; const name = nameEl ? nameEl.textContent.trim() : null; const address = addressEl ? addressEl.textContent.trim() : null; return {{ is_end: false, name: name, address: address }}; }})({current_item_index});"
        
        browser_view.page().runJavaScript(js_pre_check, 
            lambda result, idx=tab_index: self._handle_pre_check_result(result, idx))


    def _handle_pre_check_result(self, result, tab_index):
        """【改造版】处理预检查的结果"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        if result.get('is_end'):
            js_get_count = "document.querySelectorAll('a.hfpxzc').length;"
            tab_info['view'].page().runJavaScript(js_get_count, 
                lambda count, idx=tab_index: self._scroll_and_wait(idx, count))
            return

        name, address = result.get('name'), result.get('address')
        if name and address:
            unique_key = f"{name}|{address}"
            is_duplicate = False
            with self.cache_lock:
                if unique_key in self.processed_items_cache: is_duplicate = True
            
            if is_duplicate:
                print(f"🔵 (标签页 {tab_index+1}) 预检查发现重复商家: {name}，已跳过。")
                self.after_extraction_and_move_on(tab_index)
                return

        if name: print(f"▶️ (标签页 {tab_index+1}) 发现新商家: {name}，准备点击...")
        else: print(f"⚠️ (标签页 {tab_index+1}) 未能预读商家名，将按计划点击...")
        
        self._try_click_current_item(tab_index)

    def _try_click_current_item(self, tab_index):
        """【改造版】尝试点击指定标签页中的当前元素"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        browser_view = tab_info['view']
        current_item_index = tab_info.get('current_item_index', 0)
        
        browser_view.settings().setAttribute(QWebEngineSettings.AutoLoadImages, True)
        
        js_click = f"(function(index) {{ const elems = document.querySelectorAll('a.hfpxzc'); if (index >= elems.length) return false; elems[index].scrollIntoView({{behavior:'auto', block:'center'}}); elems[index].click(); return true; }})({current_item_index});"
        
        browser_view.page().runJavaScript(js_click, 
            lambda success, idx=tab_index: self._handle_click_result(success, idx))


    def _handle_click_result(self, success, tab_index):
        """【改造版】处理点击结果"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        if success:
            current_item_index = tab_info.get('current_item_index', 0)
            print(f"✅ (标签页 {tab_index+1}) 点击第 {current_item_index + 1} 个元素成功，启动哨兵...")
            tab_info['last_detail_title'] = tab_info.get('last_detail_title', '')
            self._start_detail_extraction_poller(tab_index)
        else:
            print(f"❌ (标签页 {tab_index+1}) 点击失败，跳过。")
            self.after_extraction_and_move_on(tab_index)

    
    def _start_detail_extraction_poller(self, tab_index):
        """【改造版】启动哨兵，并为其配备专属的超时定时器"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return
        
        tab_info['_poll_attempts'] = 0
        tab_info['_max_poll_attempts'] = 30 # 增加尝试次数以匹配15秒超时

        # 1. 创建一个专属的超时定时器
        POLLER_TIMEOUT_MS = 15000 # 15秒
        poller_watchdog = QTimer(self)
        poller_watchdog.setSingleShot(True)
        
        # 2. 【关键】如果超时，直接调用我们新增的 on_poller_timeout 函数
        poller_watchdog.timeout.connect(lambda: self.on_poller_timeout(tab_index))
        
        # 3. 将定时器存入 tab_info，以便后续可以取消它
        tab_info['_poller_watchdog'] = poller_watchdog
        
        poller_watchdog.start(POLLER_TIMEOUT_MS)
        
        # 4. 启动轮询 (这部分不变)
        self._poll_for_detail_data(tab_index)



    def _poll_for_detail_data(self, tab_index):
        """【改造版】哨兵轮询"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        if tab_info['_poll_attempts'] >= tab_info['_max_poll_attempts']:
            print(f"❌ (标签页 {tab_index+1}) 哨兵超时，跳过。")
            self.after_extraction_and_move_on(tab_index)
            return

        tab_info['_poll_attempts'] += 1
        browser_view = tab_info['view']
        browser_view.page().runJavaScript(self.JS_EXTRACT_DETAIL_INFO, 
            lambda result, idx=tab_index: self._handle_polled_detail_data(result, idx))




    def _handle_polled_detail_data(self, result, tab_index):
        """【改造版】处理哨兵返回的数据，并在成功时取消超时定时器"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        is_valid = result and result.get("name")
        is_new = is_valid and result.get("name") != tab_info.get('last_detail_title', '')
        image_url = result.get("image", "") if is_new else ""
        is_placeholder = "maps.gstatic.com/tactile/pane/default_geocode" in image_url
        is_fully_loaded = is_new and (bool(image_url) or is_placeholder)

        if is_fully_loaded:
            # 【核心修复】如果成功提取到数据，立即停止并清理超时定时器
            if '_poller_watchdog' in tab_info:
                tab_info['_poller_watchdog'].stop()
                del tab_info['_poller_watchdog']

            if is_placeholder: result["image"] = ""
            print(f"✅ (标签页 {tab_index+1}) 哨兵任务成功 (第 {tab_info['_poll_attempts']} 次)。")
            tab_info['last_detail_title'] = result.get("name")
            
            browser_rect = tab_info['view'].rect()
            new_center_x = int(browser_rect.width() * 0.75)
            new_center_y = int(browser_rect.height() * 0.5)
            new_center_pos = QPoint(new_center_x, new_center_y)
            
            if self.enable_click_animation:
                tab_info['overlay'].start_animation(new_center_pos)
            
            self._process_final_data(result, is_single_page=False, tab_index=tab_index)
        else:
            # 如果没加载完，就继续轮询，但要检查定时器是否还存在
            # （如果已超时，定时器会被删除，这个检查会失败，从而安全地停止轮询）
            if '_poller_watchdog' in tab_info:
                QTimer.singleShot(500, lambda: self._poll_for_detail_data(tab_index))



    def _process_final_data(self, result, is_single_page, tab_index):
        """
        【架构重构版】最终数据处理器。
        它的职责被极大简化：只负责准备任务参数，并将其放入后台队列。
        """
        try:
            # --- 数据准备和去重逻辑 (保持不变) ---
            item_name = result.get('name', '').strip()
            item_address = result.get('address', '').strip()
            unique_key = f"{item_name}|{item_address}"

            is_duplicate = False
            with self.cache_lock:
                if unique_key in self.processed_items_cache: is_duplicate = True
                else: self.processed_items_cache.add(unique_key)
            
            if is_duplicate:
                print(f"🔵 (标签页 {tab_index+1}) 最终处理发现重复数据: {item_name}")
                if is_single_page: self._retry_search_with_lower_zoom(tab_index)
                return

            print(f"📌 (标签页 {tab_index+1}) 提取到新信息: {item_name}")
            
            # --- UI和数据库更新准备 (保持不变) ---
            self.ui_update_queue.append(result)
            row = self.table.rowCount() + len(self.ui_update_queue) - 1
            self.db_worker.insert_request.emit(result)
            
            # --- ▼▼▼ 【【【核心修改：从创建Worker变为放入队列】】】 ▼▼▼ ---

            # 1. 准备好创建 EmailFetcherWorker 所需的所有参数
            worker_args = {
                'website': result.get('website', ""),
                'company_name': item_name,
                'address': item_address,
                'phone': result.get('phone'),
                'row': row,
                'playwright_manager': self.playwright_manager, # 传递管理器实例引用
                'country': self.country_combo.currentText(),
                'social_platforms_to_scrape': self.social_platforms_to_scrape,
                'whatsapp_validation_mode': self.whatsapp_validation_mode,
                'whatsapp_manager': self.whatsapp_manager,
                'is_speed_mode': self.is_speed_mode,
                'collect_all_emails_mode': self.collect_all_emails_mode,
                'extreme_deep_scan_mode': self.extreme_deep_scan_mode,
                'enable_playwright_fallback': self.enable_playwright_fallback
            }

            # 2. 【关键】将这个包含所有参数的字典，直接放入任务队列。
            #    这个操作是瞬间完成的，UI线程不会有任何卡顿。
            self.email_task_queue.put(worker_args)

            # 3. 增加活跃任务计数器，以便UI可以跟踪后台任务数量。
            self.active_worker_count += 1
            
            # --- ▲▲▲ 修改结束 ▲▲▲ ---

        finally:
            # 后续流程逻辑 (保持不变)
            if is_single_page:
                self.finish_region_extraction(tab_index)
            else:
                self.after_extraction_and_move_on(tab_index)






    def _scroll_and_wait(self, tab_index, current_count):
        """【改造版】滚动列表并等待新结果"""
        browser_view = self.tabs[tab_index]['view']
        js_scroll = "(function() { const feed = document.querySelector('div[role=\"feed\"]'); if (feed) { feed.scrollTop = feed.scrollHeight; return true; } return false; })();"
        browser_view.page().runJavaScript(js_scroll)
        QTimer.singleShot(500, lambda: self._wait_for_new_results_after_scroll(tab_index, current_count))


    def _wait_for_new_results_after_scroll(self, tab_index, previous_count, start_time=None):
        """【改造版】滚动后轮询检查新结果，并延长等待超时"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        # 【核心修改】将滚动等待的超时时间从10秒延长到25秒
        SCROLL_WAIT_TIMEOUT = 25 

        if start_time is None: start_time = time.time()
        if time.time() - start_time > SCROLL_WAIT_TIMEOUT:
            print(f"🛑 (标签页 {tab_index+1}) 等待新结果超时({SCROLL_WAIT_TIMEOUT}秒)，认为已到达列表底部。")
            self.finish_region_extraction(tab_index)
            return

        browser_view = tab_info['view']
        js_get_count = "document.querySelectorAll('a.hfpxzc').length;"
        
        def handle_check(current_count):
            if not self.is_searching or tab_index >= len(self.tabs) or self.tabs[tab_index]['state'] != 'running': return
            
            if current_count > previous_count:
                # 只要发现了新结果，就立刻回去继续主循环，不再等待
                print(f"  -> ✅ (标签页 {tab_index+1}) 新结果已加载。")
                QTimer.singleShot(500, lambda: self._scroll_and_extract_loop(tab_index, previous_count))
            else:
                # 如果没发现新结果，则在超时前继续等待
                QTimer.singleShot(1000, lambda: self._wait_for_new_results_after_scroll(tab_index, previous_count, start_time))

        browser_view.page().runJavaScript(js_get_count, handle_check)


    def after_extraction_and_move_on(self, tab_index):
        """【改造版】处理完一个商家后，继续处理下一个"""
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        tab_info['current_item_index'] = tab_info.get('current_item_index', 0) + 1
        tab_info['view'].settings().setAttribute(QWebEngineSettings.AutoLoadImages, not self.is_speed_mode)
        QTimer.singleShot(500, lambda: self._process_next_item(tab_index))

# 在 class GoogleMapsApp(QWidget): 中
    def finish_region_extraction(self, tab_index):
        """【并发渲染修复版】一个地区任务完成后的核心回调"""
        if tab_index >= len(self.tabs): return
        
        # 1. 停止看门狗定时器（保持不变）
        if tab_index in self.watchdog_timers:
            self.watchdog_timers[tab_index].stop()
            del self.watchdog_timers[tab_index]
            print(f"  -> ✓ (标签页 {tab_index+1}) 看门狗定时器已安全拆除。")
            
        tab_info = self.tabs[tab_index]
        
        # 只有当它确实处于 'running' 状态时，我们才执行清理和释放操作
        if tab_info['state'] == 'running':
            task_name = tab_info['current_task']['region_name'] if tab_info['current_task'] else "未知"
            print(f"✅ (标签页 {tab_index+1}) 任务 [{task_name}] 完成。")
            
            # --- ▼▼▼ 【核心修复】在这里添加下面这行代码 ▼▼▼ ---
            # 2. 【关键】归还“采集许可”，让等待的页面可以开始工作
            self.scraper_semaphore.release()
            print(f"  -> ✅ (标签页 {tab_index+1}) 已释放采集许可。")
            # --- ▲▲▲ 修复代码添加完毕 ▲▲▲ ---

            # 3. 更新状态并调用调度员（保持不变）
            tab_info['state'] = 'idle'
            tab_info['current_task'] = None
            
            QTimer.singleShot(100, self._dispatch_tasks)


    def _retry_search_with_lower_zoom(self, tab_index):
        """
        【改造版】一个辅助函数，用于在发现重复的单个商家后，
        为指定的标签页降低缩放级别并重新发起搜索。
        """
        if not self.is_searching or tab_index >= len(self.tabs): return
        tab_info = self.tabs[tab_index]
        if tab_info['state'] != 'running': return

        current_task = tab_info['current_task']
        browser_view = tab_info['view']
        
        current_zoom = current_task.get('zoom', 15)

        # 计算下一个缩放级别
        next_zoom = 0
        if current_zoom > 12: next_zoom = 12
        elif current_zoom > 10: next_zoom = 10
        else: next_zoom = 9

        if next_zoom < 10:
            print(f"❌ (标签页 {tab_index+1}) 因重复而降级，已达到最小缩放级别10z，放弃当前任务。")
            self.finish_region_extraction(tab_index) # 结束任务并呼叫调度员
            return

        print(f"⚠️ (标签页 {tab_index+1}) 因发现重复商家(Zoom: {current_zoom}z)，正在降低缩放级别至 {next_zoom}z 并重试...")

        # 更新当前任务的zoom
        current_task['zoom'] = next_zoom

        # 重新构建URL
        latitude = current_task['url'].split('@')[1].split(',')[0]
        longitude = current_task['url'].split('@')[1].split(',')[1]
        encoded_keywords = current_task['url'].split("search/")[1].split("/@")[0]
        
        new_url = f"https://www.google.com/maps/search/{encoded_keywords}/@{latitude},{longitude},{next_zoom}z"
        if "&gl=" in current_task['url']:
            new_url += "&gl=" + current_task['url'].split("&gl=")[-1]
        
        current_task['url'] = new_url
        print(f"🔄 (标签页 {tab_index+1}) 重试链接: {new_url}")
        self._start_scraping_on_tab(tab_index, current_task)















    # 清理已完成的线程
    def cleanup_fetcher(self, fetcher, fetcher_type="email"):
        """清理已完成的线程"""
        if fetcher_type == "email" and fetcher in self.email_fetchers:
            self.email_fetchers.remove(fetcher)
        elif fetcher_type == "ai" and fetcher in self.ai_fetchers:
            self.ai_fetchers.remove(fetcher)

        fetcher.deleteLater()

        self._dispatch_tasks()

    # 更新表格中的邮箱列
    def update_email_in_table(self, website, email, row):
        """更新表格中的邮箱列"""
        if row < self.table.rowCount():
            print(f"📧 为网站 {website} 提取到邮箱: {email}")
            item = QTableWidgetItem(email)
            self.table.setItem(row, 3, item)  # 第3列是邮箱列


    # 显示数据到页面上
    def show_result_single(self, item_data):
        row = self.table.rowCount()
        self.table.insertRow(row)

        name_item = QTableWidgetItem(item_data.get("name", ""))
        name_item.setData(Qt.UserRole, item_data)
        self.table.setItem(row, 0, name_item)

        # 填充已知的基本信息
        self.table.setItem(row, 1, QTableWidgetItem(item_data.get("address", "")))
        self.table.setItem(row, 2, QTableWidgetItem(item_data.get("phone", "")))
        self.table.setItem(row, 9, QTableWidgetItem(item_data.get("dkEaLTexts", "")))
        self.table.setItem(row, 10, QTableWidgetItem(item_data.get("hours", "")))
        self.table.setItem(row, 11, QTableWidgetItem(item_data.get("rating", "")))
        self.table.setItem(row, 12, QTableWidgetItem(str(item_data.get("reviewCount", ""))))
        self.table.setItem(row, 13, QTableWidgetItem(item_data.get("link", "")))

        # --- ▼▼▼ 【核心修复】智能判断是否应用骨架屏 ▼▼▼ ---
        
        # 1. 定义列索引到数据键名的映射
        col_to_key_map = {
            3: "email",
            4: "website",
            5: "facebook",
            6: "instagram",
            7: "linkedin",
            8: "whatsapp"
        }

        # 2. 准备“骨架”样式 (这部分不变)
        skeleton_bg_color = QColor(235, 235, 235)
        skeleton_fg_color = QColor(220, 220, 220)

        # 3. 遍历需要后台获取的列
        for col, key in col_to_key_map.items():
            # 关键判断：检查 item_data 中是否已存在该项数据
            if item_data.get(key):
                # 如果数据已存在 (例如官网链接)，直接显示
                self.table.setItem(row, col, QTableWidgetItem(item_data[key]))
            else:
                # 如果数据不存在，才显示骨架屏
                skeleton_item = QTableWidgetItem()
                skeleton_item.setBackground(skeleton_bg_color)
                skeleton_item.setForeground(skeleton_fg_color)
                skeleton_item.setText("██████████████")
                self.table.setItem(row, col, skeleton_item)

    def _add_full_company_row_to_table(self, company_data: dict):
        try:
            row = self.table.rowCount()
            self.table.insertRow(row)

            # 【核心修改】同样，在这里也绑定完整数据
            name_item = QTableWidgetItem(company_data.get("名称", ""))
            name_item.setData(Qt.UserRole, company_data)
            self.table.setItem(row, 0, name_item)

            # 其他列的显示逻辑不变
            self.table.setItem(row, 1, QTableWidgetItem(company_data.get("地址", "")))
            self.table.setItem(row, 2, QTableWidgetItem(company_data.get("电话", "")))
            self.table.setItem(row, 3, QTableWidgetItem(company_data.get("邮箱", "")))
            self.table.setItem(row, 4, QTableWidgetItem(company_data.get("官网", "")))
            self.table.setItem(row, 5, QTableWidgetItem(company_data.get("Facebook", "")))
            self.table.setItem(row, 6, QTableWidgetItem(company_data.get("Instagram", "")))
            self.table.setItem(row, 7, QTableWidgetItem(company_data.get("LinkedIn", "")))
            self.table.setItem(row, 8, QTableWidgetItem(company_data.get("WhatsApp", "")))
            self.table.setItem(row, 9, QTableWidgetItem(company_data.get("类别", "")))
            self.table.setItem(row, 10, QTableWidgetItem(company_data.get("营业时间", "")))
            self.table.setItem(row, 11, QTableWidgetItem(str(company_data.get("评分", ""))))
            self.table.setItem(row, 12, QTableWidgetItem(str(company_data.get("评价数", ""))))
            self.table.setItem(row, 13, QTableWidgetItem(company_data.get("来源链接", "")))
        except Exception as e:
            print(f"❌ 添加完整行到表格时出错: {e}")

    # 页面上显示数据
    def show_results(self, data, append=False):
        if not append:
            self.table.setRowCount(0)  # 清空表格

        for item in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
            self.table.setItem(row, 1, QTableWidgetItem(item.get("address", "")))
            self.table.setItem(row, 2, QTableWidgetItem(item.get("phone", "")))
            self.table.setItem(row, 3, QTableWidgetItem(item.get("email", "")))
            self.table.setItem(row, 4, QTableWidgetItem(item.get("website", "")))
            self.table.setItem(row, 5, QTableWidgetItem(item.get("dkEaLTexts", "")))
            self.table.setItem(row, 6, QTableWidgetItem(item.get("hours", "")))
            self.table.setItem(row, 7, QTableWidgetItem(item.get("rating", "")))
            self.table.setItem(row, 8, QTableWidgetItem(str(item.get("reviewCount", ""))))
            self.table.setItem(row, 9, QTableWidgetItem(item.get("link", "")))




    # (在 GoogleMapsApp 类中添加这两个新方法)

    def handle_whatsapp_login_request(self):
        """
        【修复版】处理来自设置对话框的WhatsApp登录请求。
        使用 QThread + QObject Worker 模式来彻底解决UI无响应问题。
        """
        QMessageBox.information(self, "准备登录", "即将打开一个新浏览器窗口进行WhatsApp扫码登录。此过程可能需要一些时间，请稍候...")
        
        # 懒加载WhatsAppManager，只在需要时创建
        if not self.whatsapp_manager:
            self.whatsapp_manager = WhatsAppManager()
        
        # 确保信号只连接一次
        try:
            self.whatsapp_manager.login_success_signal.disconnect(self.show_whatsapp_login_success_message)
        except TypeError:
            pass # 如果之前没连接过，会抛出TypeError，忽略即可
        self.whatsapp_manager.login_success_signal.connect(self.show_whatsapp_login_success_message)

        # --- ▼▼▼ 【核心修复逻辑】 ▼▼▼ ---

        # 1. 创建一个新的 QThread 实例
        self.login_thread = QThread()
        # 2. 创建我们的 Worker 实例
        self.login_worker = WhatsAppLoginWorker(self.whatsapp_manager)
        # 3. 【关键】将 Worker "移动" 到新创建的线程中
        self.login_worker.moveToThread(self.login_thread)

        # 4. 设置信号连接：
        #   - 当线程启动时，自动调用 Worker 的 run 方法
        self.login_thread.started.connect(self.login_worker.run)
        #   - 当 Worker 的任务完成后，让线程自己退出
        self.login_worker.finished.connect(self.login_thread.quit)
        #   - 在线程退出后，安全地删除 Worker 和 线程 对象，避免内存泄漏
        self.login_worker.finished.connect(self.login_worker.deleteLater)
        self.login_thread.finished.connect(self.login_thread.deleteLater)

        # 5. 启动线程，整个流程开始异步执行
        self.login_thread.start()
        
        print("✅ 已将WhatsApp登录任务分派到独立的后台线程。主UI将保持响应。")
        # --- ▲▲▲ 修复结束 ▲▲▲ ---

    def _update_user_settings(self, settings):
        """将用户的设置(社媒选择、WA模式)保存到 user_config.json"""
        if not self.credentials or 'username' not in self.credentials:
            return

        username = self.credentials['username']
        config = self._load_user_config()

        if "users" not in config: config["users"] = {}
        if username not in config["users"]: config["users"][username] = {}
        
        # 使用 update 方法，将新设置合并到用户的现有数据中
        config["users"][username].update(settings)
        
        # 复用已有的保存逻辑
        self._save_user_config(config) # 假设您有一个_save_user_config方法
        print(f"✅ 已为用户 {username} 保存新设置。")

    # 如果没有 _save_user_config, 请添加它:
    def _save_user_config(self, config_data):
        config_path = get_app_data_path("user_config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=4, ensure_ascii=False)
        except IOError as e:
            print(f"❌ 无法保存配置文件: {e}")


    def show_whatsapp_login_success_message(self):
        """显示WhatsApp登录成功的提示框"""
        QMessageBox.information(self, "登录成功", "WhatsApp登录状态已成功保存。您可以关闭此浏览器窗口了。")

    # 打开社媒拓客设置对话框，并更新配置
    def open_social_media_settings(self):
        """打开设置对话框，处理设置的保存和WhatsApp登录请求"""
        current_settings = {
            'social_platforms': self.social_platforms_to_scrape,
            'whatsapp_mode': self.whatsapp_validation_mode,
            'grid_spacing': self.grid_spacing_degrees,
            'parallel_tasks': self.parallel_tasks_count,
            'enable_playwright_fallback': self.enable_playwright_fallback, # 【新增】将当前设置传递给对话框
            'enable_click_animation': self.enable_click_animation,
            'auto_parallel_tasks': self.auto_detected_defaults['parallel_tasks'],
            'auto_playwright_pool_size': self.auto_detected_defaults['playwright_pool_size'],

        }
        dialog = SocialMediaDialog(current_settings, self)
        
        dialog.request_whatsapp_login.connect(self.handle_whatsapp_login_request)

        if dialog.exec_() == QDialog.Accepted:
            new_settings = dialog.get_settings()
            old_parallel_count = self.parallel_tasks_count
            
            self.social_platforms_to_scrape = new_settings['social_platforms']
            self.whatsapp_validation_mode = new_settings['whatsapp_mode']
            self.grid_spacing_degrees = new_settings['grid_spacing']
            self.parallel_tasks_count = new_settings['parallel_tasks'] 
            self.enable_playwright_fallback = new_settings['enable_playwright_fallback'] # 【新增】保存从对话框返回的新设置
            self.enable_click_animation = new_settings['enable_click_animation'] # 【新增】保存从对话框返回的新设置

            if self.parallel_tasks_count != old_parallel_count:
                self._update_tab_count(self.parallel_tasks_count)
            
            self._update_user_settings(new_settings)
            print("✅ 拓客设置已更新:", new_settings)
            QMessageBox.information(self, "设置已保存", "新的拓客设置将在下次搜索时生效。")

    def toggle_speed_mode(self, checked):
        """
        【修改版】
        处理“快速抓取模式”的开关，只更新状态标志。
        """
        self.is_speed_mode = checked
        if checked:
            print("✅ [快速模式] 已开启。在下次搜索时将禁用图片加载以提升滚动速度。")
            QMessageBox.information(self, "模式切换", "快速抓取模式已开启。\n\n在搜索列表滚动阶段将禁用图片加载以提升速度。")
        else:
            print("❌ [快速模式] 已关闭。将恢复正常图片加载。")
            QMessageBox.information(self, "模式切换", "快速抓取模式已关闭。")

        if self.playwright_manager:
            self.playwright_manager.set_speed_mode(self.is_speed_mode)
        


    # 导出的数据
    def export_results(self):
        """
        【内存优化版】
        使用批处理方式导出数据，避免一次性加载所有内容到内存。
        """
        if self.user_type in ["standard", "trial"]:
            if self.daily_export_count > 0:
                QMessageBox.warning(self, "导出限制", "试用账号仅允许导出一次，您已使用过该权限。")
                return # 直接返回，不执行后续导出代码
            
            # 如果是第一次导出，弹窗确认
            reply = QMessageBox.question(self, '确认导出',
                                         '您正在使用试用账号的唯一一次导出机会，确定要继续吗？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                return # 用户取消，不导出

        # 1. 检查数据库中是否有数据（可以先查总数）
        # (此步可选，但可以快速判断是否需要导出)
        # ...

        path, _ = QFileDialog.getSaveFileName(self, "保存数据", "",
                                            "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if not path:
            return

        headers = ["名称", "地址", "电话", "邮箱", "官网", "Facebook", "Instagram", "LinkedIn", "WhatsApp", "类别", "营业时间", "评分", "评价数", "来源链接"]
        total_exported = 0
        export_success = False

        try:
            # 获取批处理生成器
            batches = self.db_worker.get_all_companies_in_batches_blocking(batch_size=500)
            is_first_batch = True

            if path.lower().endswith('.xlsx'):
                with pd.ExcelWriter(path, engine='openpyxl') as writer:
                    start_row = 0
                    for batch_rows in batches:
                        if not batch_rows: continue
                        
                        batch_data = [dict(zip(headers, row)) for row in batch_rows]
                        df = pd.DataFrame(batch_data)
                        
                        df.to_excel(writer, index=False, sheet_name='地图数据', 
                                    header=is_first_batch, startrow=start_row)
                        
                        if is_first_batch:
                            # 自动调整列宽 (仅在第一批后执行一次)
                            worksheet = writer.sheets['地图数据']
                            for column in worksheet.columns:
                                # ... 调整列宽的代码保持不变 ...
                                max_length = 0
                                column_name = column[0].column_letter
                                if is_first_batch:
                                    max_length = len(str(worksheet[f'{column_name}1'].value))
                                for cell in column:
                                    if cell.value is not None:
                                        cell_len = len(str(cell.value))
                                        if cell_len > max_length:
                                            max_length = cell_len
                                adjusted_width = (max_length + 2)
                                worksheet.column_dimensions[column_name].width = adjusted_width

                        start_row += len(batch_rows)
                        total_exported += len(batch_rows)
                        is_first_batch = False
                export_success = True

            elif path.lower().endswith('.csv'):
                with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                    for batch_rows in batches:
                        if not batch_rows: continue
                        
                        batch_data = [dict(zip(headers, row)) for row in batch_rows]
                        df = pd.DataFrame(batch_data)
                        
                        df.to_csv(f, index=False, header=is_first_batch, mode='a')
                        
                        total_exported += len(batch_rows)
                        is_first_batch = False
                export_success = True

            # 导出成功后统一提示
            if export_success:
                if self.user_type in ["standard", "trial"]:
                    self._send_action_to_backend("export")
                    self.daily_export_count = 1 
                    self.export_btn.setEnabled(False)

                    # self.trial_export_used = True
                    # self._update_trial_status('trial_export_used', True) # <-- 【新增】调用保存方法
                    # self.export_btn.setEnabled(False)
                    self.export_btn.setText("导出权限已使用")
                    if hasattr(self, 'trial_label'):
                        self.trial_label.setText("提示：试用账号的导出权限已使用。")
                
                QMessageBox.information(self, "导出成功", f"成功导出 {total_exported} 条数据。")
                
                # if self.user_id:
                #     self.send_export_signal(self.user_id)
            
        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))
            export_success = False

        # 导出成功后通知后端的逻辑保持不变
        # if export_success and self.user_id:
        #     self.send_export_signal(self.user_id)




    def start_completion_task(self):
        """
        为表格中信息不完整的行启动邮件和社交媒体信息的补全任务。
        """
        if self.table.rowCount() == 0:
            QMessageBox.information(self, "提示", "表格中没有数据，无法执行补全任务。")
            return

        # 1. 扫描整个表格，找出所有需要补全信息的行
        tasks_to_create = []
        for row in range(self.table.rowCount()):
            email_item = self.table.item(row, 3)    # 第3列是邮箱
            website_item = self.table.item(row, 4)  # 第4列是官网

            # 定义需要补全的条件：
            # - 官网链接存在 (没有官网无法提取)
            # - 邮箱内容为空
            # - 并且当前不处于“正在提取”的状态（通过检查单元格文本是否为骨架屏来判断）
            if (website_item and website_item.text().strip() and
                (not email_item or not email_item.text().strip()) and
                (not email_item or "███" not in email_item.text())):
                
                # 从表格中收集创建任务所需的信息
                task_info = {
                    'name': self.table.item(row, 0).text(),
                    'address': self.table.item(row, 1).text(),
                    'phone': self.table.item(row, 2).text(),
                    'website': website_item.text(),
                    'row': row  # 关键：必须传递正确的行号，以便结果返回时能更新对应的行
                }
                tasks_to_create.append(task_info)

        if not tasks_to_create:
            QMessageBox.information(self, "操作完成", "未发现需要补全信息的条目。")
            return

        # 2. 在执行耗时操作前，弹窗与用户确认
        reply = QMessageBox.question(self, '确认操作',
                                    f'已扫描到 {len(tasks_to_create)} 条信息不完整的记录。\n\n'
                                    '是否要为这些记录启动邮箱和社交媒体信息提取？\n'
                                    '此过程将在后台进行，不会影响您操作界面。',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.No:
            return

        # 3. 遍历待办任务列表，创建并分派任务
        for task in tasks_to_create:
            row = task['row']
            
            # 为了提供即时反馈，先在UI上将这些行标记为“正在处理”（应用骨架屏样式）
            skeleton_bg_color = QColor(235, 235, 235)
            skeleton_fg_color = QColor(220, 220, 220)
            for col in range(3, 9): # 从邮箱列到WhatsApp列
                skeleton_item = QTableWidgetItem()
                skeleton_item.setBackground(skeleton_bg_color)
                skeleton_item.setForeground(skeleton_fg_color)
                skeleton_item.setText("██████████████")
                self.table.setItem(row, col, skeleton_item)

            # 构建与实时抓取时完全一致的后台任务参数
            worker_args = {
                'website': task.get('website', ""),
                'name': task.get('name'),
                'address': task.get('address'),
                'phone': task.get('phone'),
                'row': row,
                'playwright_manager': self.get_playwright_manager(),
                'country': self.country_combo.currentText(),
                'social_platforms_to_scrape': self.social_platforms_to_scrape,
                'whatsapp_validation_mode': self.whatsapp_validation_mode,
                'whatsapp_manager': self.whatsapp_manager,
                'is_speed_mode': self.is_speed_mode,
                'collect_all_emails_mode': self.collect_all_emails_mode,
                'extreme_deep_scan_mode': self.extreme_deep_scan_mode,
                'enable_playwright_fallback': self.enable_playwright_fallback
            }
            
            # 将任务放入后台处理队列，程序会自动开始处理
            self.email_task_queue.put(worker_args)
            self.active_worker_count += 1
        
        QMessageBox.information(self, "任务已启动", f"已成功为 {len(tasks_to_create)} 个条目启动信息补全任务。")



    def _send_action_to_backend(self, action_type):
        """【修正版】通知后端记录用户的操作，将 action_type 显式传递给线程"""
        if not self.user_id: return
        
        print(f"正在向后端上报操作: user_id={self.user_id}, action={action_type}")
        url = "https://mediamingle.cn/.netlify/functions/record-action"
        payload = {
            "user_id": self.user_id,
            "action_type": action_type
        }
        
        try:
            # --- ▼▼▼ 【核心修复】修改嵌套的线程类 ▼▼▼ ---
            class ActionReporter(QThread):
                def __init__(self, url, payload, action_type_arg): # 1. 增加一个参数
                    super().__init__()
                    self.url = url
                    self.payload = payload
                    self.action_type = action_type_arg # 2. 将参数保存到实例变量

                def run(self):
                    try:
                        requests.post(self.url, json=self.payload, timeout=10)
                        # 3. 使用实例变量 self.action_type
                        print(f"✅ 操作 '{self.action_type}' 上报成功。") 
                    except Exception as e:
                        print(f"❌ 上报操作 '{self.action_type}' 时发生网络错误: {e}")
            
            # 4. 创建实例时，传入 action_type
            self.reporter_thread = ActionReporter(url, payload, action_type)
            # --- ▲▲▲ 修复结束 ▲▲▲ ---

            self.reporter_thread.start()
        except Exception as e:
            print(f"❌ 启动上报线程失败: {e}")

    



    def eventFilter(self, source, event):
        """
        【AttributeError修复版】事件过滤器
        - 增加了对 self.table 是否已初始化的检查，防止在程序启动早期因访问不存在的控件而崩溃。
        - 保持了对浏览器视图尺寸变化和表格悬浮窗逻辑的监听。
        """
        # --- ▼▼▼ 【核心修复】在这里增加一个安全检查 ▼▼▼ ---
        # 检查 self.table 是否已经被创建。如果还没有，就跳过所有与表格相关的逻辑。
        if hasattr(self, 'table') and source is self.table.viewport() and event.type() == QEvent.Leave:
            self.hover_timer.stop()
            self.info_tooltip.hide()
            self.current_hover_row = -1
        # --- ▲▲▲ 修复结束 ▲▲▲ ---

        # 检查事件源是否是我们的浏览器视图，并且事件类型是“尺寸变化”
        if isinstance(source, QWebEngineView) and event.type() == QEvent.Resize:
            # 遍历所有标签页信息，找到这个事件源对应的那个
            for tab_info in self.tabs:
                if tab_info['view'] is source:
                    # 找到了！让它专属的遮罩层的大小自动调整为和它一样大
                    if 'loading_overlay' in tab_info: # 再次检查以确保安全
                        tab_info['loading_overlay'].setGeometry(source.rect())
                    break # 处理完毕，跳出循环

        # 调用父类的 eventFilter，确保其他事件能被正常处理
        return super().eventFilter(source, event)

    def on_cell_hovered(self, row, column):
        """当鼠标进入一个新的单元格时调用。"""
        if row != self.current_hover_row:
            # 鼠标移动到了新的一行
            self.current_hover_row = row
            # 隐藏旧的提示（如果有的话），并启动计时器
            self.info_tooltip.hide()
            self.hover_timer.start(500) # 延迟500毫秒显示

    def show_tooltip(self):
        """当悬浮计时器到期时，显示信息提示窗。"""
        if self.current_hover_row < 0:
            return

        # 从表格的第一列获取item
        item = self.table.item(self.current_hover_row, 0)
        if not item:
            return

        # 从item中提取我们之前绑定的完整数据字典
        row_data = item.data(Qt.UserRole)
        if not row_data:
            return

        # 更新提示窗内容
        self.info_tooltip.update_info(row_data)

        # 定位提示窗
        # 1. 获取鼠标当前在屏幕上的全局坐标
        cursor_pos = QCursor.pos()
        # 2. 将提示窗的左下角移动到鼠标位置
        #    x = 鼠标的x坐标
        #    y = 鼠标的y坐标 - 提示窗的高度
        tooltip_height = self.info_tooltip.height()
        self.info_tooltip.move(cursor_pos.x(), cursor_pos.y() - tooltip_height - 5) # 向上偏移5像素，避免遮挡鼠标

        # 显示提示窗
        self.info_tooltip.show()



    def _load_and_resume_progress(self):
        """加载并恢复之前的搜索进度"""
        try:
            progress_file_path = get_app_data_path("progress_state.json")
            if not os.path.exists(progress_file_path):
                return

            with open(progress_file_path, 'r', encoding='utf-8') as f:
                state = json.load(f)

            # 检查是否有正在运行或暂停的任务
            if not state.get("is_running"):
                return

            reply = QMessageBox.question(self, '发现未完成的任务',
                                        '检测到上次有一个搜索任务意外中断或被暂停，是否要继续？',
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            
            if reply == QMessageBox.Yes:
                print("👍 用户选择继续，正在恢复进度...")
                # 恢复所有状态变量
                self.current_keyword_index = state.get("current_keyword_index", 0)
                self.current_region_index = state.get("current_region_index", 0)
                self.keywords = state.get("keywords", [])
                self.search_coords = state.get("search_coords", [])
                self.processed_items_cache = set(state.get("processed_items_cache", []))
                
                # 根据上次是暂停还是中断，来决定UI和运行状态
                if state.get("is_paused"):
                    # 如果是暂停状态，只恢复UI，不自动开始
                    self.is_searching = False
                    self.pause_search_action.setVisible(False)
                    self.resume_search_action.setVisible(True)
                    self.stop_search_action.setEnabled(False)
                    QMessageBox.information(self, "任务已恢复", "任务已加载，请点击“继续搜索”开始。")
                else:
                    # 如果是意外中断状态，自动开始
                    self.is_searching = True
                    self.pause_search_action.setVisible(True)
                    self.resume_search_action.setVisible(False)
                    self.stop_search_action.setEnabled(True)
                    self.search_next_region() 

                
        except Exception as e:
            print(f"❌ 加载进度失败: {e}")



    def _reload_data_from_db_to_table(self):
        """
        【修改版】从数据库中重新加载所有已有数据并填充到UI表格中。
        """
        print("🔄 正在从数据库恢复已抓取的数据到表格中...")

        class DataLoader(QRunnable):
            def __init__(self, db_worker, ui_update_queue):
                super().__init__()
                self.db_worker = db_worker
                self.ui_update_queue = ui_update_queue

            def run(self):
                # 【修改】表头需要加入 image_url
                headers = ["名称", "地址", "电话", "邮箱", "官网", "Facebook", "Instagram", "LinkedIn", "WhatsApp", "类别", "营业时间", "评分", "评价数", "来源链接", "image_url"]
                batches = self.db_worker.get_all_companies_in_batches_blocking(batch_size=200)

                total_reloaded = 0
                for batch_rows in batches:
                    for row_tuple in batch_rows:
                        company_dict = dict(zip(headers, row_tuple))
                        company_dict['source'] = 'db_reload'
                        self.ui_update_queue.append(company_dict)
                        total_reloaded += 1
                print(f"✅ 成功从数据库加载 {total_reloaded} 条已有数据准备显示。")

        loader_task = DataLoader(self.db_worker, self.ui_update_queue)
        self.thread_pool.start(loader_task)

    def _update_expiry_display(self):
        """计算并更新界面上的会员到期时间显示"""
        if not self.expiry_at:
            self.expiry_label.setText("授权状态: 永久")
            self.expiry_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;")
            return

        try:
            from datetime import datetime, timezone
            # 解析后端返回的ISO 8601格式时间字符串
            if self.expiry_at.endswith("Z"):
                expiry_date = datetime.fromisoformat(self.expiry_at[:-1]).replace(tzinfo=timezone.utc)
            else:
                expiry_date = datetime.fromisoformat(self.expiry_at)

            # 计算剩余时间
            remaining = expiry_date - datetime.now(timezone.utc)
            remaining_days = remaining.days

            # 根据剩余天数更新显示和颜色
            if remaining_days < 0:
                self.expiry_label.setText("授权已过期")
                self.expiry_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #e74c3c;") # 红色
            elif remaining_days <= 7:
                self.expiry_label.setText(f"授权即将到期: 剩余 {remaining_days + 1} 天")
                self.expiry_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #f39c12;") # 橙色
            else:
                self.expiry_label.setText(f"授权剩余: {remaining_days + 1} 天")
                self.expiry_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #27ae60;") # 绿色

        except Exception as e:
            self.expiry_label.setText("授权状态: 未知")
            print(f"❌ 解析到期时间时出错: {e}")

    # 导出后通知后端记录次数
    def send_export_signal(self, user_id):
        """导出后通知后端记录次数"""
        if user_id is None:
            print("❌ user_id 为 None，无法发送导出记录。")
            QMessageBox.warning(self, "导出警告", "用户ID无效，无法记录导出次数。请重新登录。")
            return  # 不发送请求
    
        try:
            url = "https://mediamingle.cn/.netlify/functions/recordExport"  # 改成你的 Netlify API 地址
            payload = {
                "user_id": user_id,
                "data_to_export": "google_maps_data"
            }
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                print("✅ 导出次数已记录：", resp.json())
            else:
                print("❌ 后端返回错误：", resp.status_code, resp.text)
        except Exception as e:
            print("❌ 发送导出记录失败：", e)

    # loading 动画
    # 在 GoogleMapsApp 类中

    def on_load_started(self):
        """
        【遮罩层修复版】
        - 使用 self.sender() 来准确定位是哪个浏览器视图触发了加载。
        - 控制该视图专属的遮罩层和加载状态。
        """
        # 1. 获取发射此信号的浏览器视图对象
        browser_view = self.sender()
        if not isinstance(browser_view, QWebEngineView): return

        # 2. 找到这个视图对应的 tab_info
        target_tab_info = None
        for tab_info in self.tabs:
            if tab_info['view'] is browser_view:
                target_tab_info = tab_info
                break

        # 3. 只操作这个目标标签页的遮罩层和状态
        if target_tab_info and self.user_triggered_navigation and not target_tab_info['is_loading']:
            target_tab_info['is_loading'] = True
            overlay = target_tab_info['loading_overlay']
            overlay.raise_() # 确保遮罩层在最顶上
            overlay.show()




    def on_load_finished(self, ok):
        """
        【遮罩层修复版】
        - 同样使用 self.sender() 来准确定位是哪个浏览器视图完成了加载。
        """
        # 1. 获取发射此信号的浏览器视图对象
        browser_view = self.sender()
        if not isinstance(browser_view, QWebEngineView): return

        # 2. 找到这个视图对应的 tab_info
        target_tab_info = None
        for tab_info in self.tabs:
            if tab_info['view'] is browser_view:
                target_tab_info = tab_info
                break

        # 3. 只隐藏目标标签页的遮罩层
        if target_tab_info and target_tab_info['is_loading']:
            target_tab_info['is_loading'] = False
            target_tab_info['loading_overlay'].hide()
        
        # 4. 保留原有的全局逻辑
        self.user_triggered_navigation = False
        if not ok:
            print("一个页面加载失败或被用户停止。")

    # (在 GoogleMapsApp 类中, 替换这个方法)
    def resizeEvent(self, event):
        """【改造版】当窗口大小变化时，手动更新所有浏览器页面的大小和位置"""
        super().resizeEvent(event)
        
        # --- ▼▼▼ 【核心修复】删除下面这一行 ▼▼▼ ---
        # self._update_overlays_geometry()  <-- This line should be removed
        # --- ▲▲▲ 修复结束 ▲▲▲ ---

        # 【新】循环遍历所有浏览器页面，让它们的大小与容器保持一致
        if hasattr(self, 'browser_container') and hasattr(self, 'tabs'):
            container_rect = self.browser_container.rect()
            for tab_info in self.tabs:
                if tab_info.get('view'): # Safety check
                    tab_info['view'].setGeometry(container_rect)
                if 'overlay' in tab_info and tab_info.get('overlay'): # Safety check
                    # 动画层的大小也应与浏览器页面保持一致
                    tab_info['overlay'].setGeometry(container_rect)


    # 加载国家城市地区
    def load_regions_with_bounds(self, filepath="regions.json"):
        correct_filepath = resource_path(filepath)
        if not os.path.exists(correct_filepath):
            QMessageBox.critical(self, "错误", f"地区文件 '{correct_filepath}' 不存在！请确保它和程序在同一目录下。")
            return
            
        try:
            with open(correct_filepath, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
        except Exception as e:
            QMessageBox.warning(self, "加载地区失败", f"无法加载地区文件：{str(e)}")
            raw_data = []

        # 转为字典结构：{国家名: [地区列表]}
        self.region_data_by_country = {}
        for item in raw_data:
            country = item.get("country")
            regions = item.get("regions", [])
            if country and regions:
                # 确保每个地区列表都包含 "全部地区"
                if not any(r.get("name") == "全部地区" for r in regions):
                    regions.insert(0, {"name": "全部地区"})
                self.region_data_by_country[country] = regions

        self.country_combo.clear()
        if self.region_data_by_country:
            self.country_combo.addItems(self.region_data_by_country.keys())
            # 默认加载第一个国家的地区
            default_country = list(self.region_data_by_country.keys())[0]
            self.update_regions_for_country(default_country)
        else:
            self.region_combo.clear()


    def update_regions_for_country(self, country):
        """
        【交互优化版】
        1. 调整排序，确保“全部地区”在“全国概览”之前。
        2. 为“全部地区”和“全国概览”条目设置不同的用户角色，以便后续进行逻辑判断。
        """
        # 暂时阻止信号，因为我们要清空和重新填充模型
        self._block_region_signals = True

        self.region_model.clear()
        regions = self.region_data_by_country.get(country, [])
        
        # 1. 先将所有地区按名称分类
        all_regions_item = None
        national_overview_item = None
        other_regions = []

        for r_data in regions:
            name = r_data.get("name", "未知地区")
            item = QStandardItem(name)
            item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            item.setData(Qt.Unchecked, Qt.CheckStateRole)
            
            if name == "全部地区":
                all_regions_item = item
                # 为“全部地区”设置一个特殊的角色标记
                item.setData("all_regions_role", Qt.UserRole)
                # --- ▼▼▼ 【核心修复】在这里增加下面这行代码 ▼▼▼ ---
                item.setData(Qt.Checked, Qt.CheckStateRole)
                # --- ▲▲▲ 修复结束 ▲▲▲ ---
            elif name == "全国概览":
                national_overview_item = item
            else:
                other_regions.append(item)
        
        # 2. 按照“全部地区” -> “全国概览” -> “其他地区”的顺序重新插入模型
        if all_regions_item:
            self.region_model.appendRow(all_regions_item)
        if national_overview_item:
            self.region_model.appendRow(national_overview_item)
        for item in sorted(other_regions, key=lambda x: x.text()): # 其他地区按字母排序
            self.region_model.appendRow(item)
        
        # 填充完毕后，恢复信号并更新一次初始文本
        self._block_region_signals = False
        self.update_region_selection_text()


    # 新的槽函数，用于同时更新表格中的邮箱和官网列。
    def handle_worker_result(self, result_data, row):
        """处理来自Worker的所有结果（邮箱、官网、社媒），并更新UI和数据库"""

        # 如果用户已经点击了停止，则直接忽略所有后续返回的结果
        if not self.is_searching:
            return

        if row >= self.table.rowCount():
            return
        
        # 1. 找到第一列的单元格，那里藏着我们的“内口袋”
        name_item = self.table.item(row, 0)
        if name_item:
            # 2. 取出旧的“内口袋”数据
            existing_data = name_item.data(Qt.UserRole)
            if existing_data and isinstance(existing_data, dict):
                # 3. 将新找到的信息（邮箱、社交链接等）更新进去
                existing_data.update(result_data)
                # 4. 把更新后的、完整的“内口袋”数据再放回去！
                name_item.setData(Qt.UserRole, existing_data)
                print(f"✅ (行: {row}) 悬浮窗的“内口袋”数据已更新。")
        
        # 1. 准备UI更新指令
        # 使用 .get(key) or "" 来确保即使键不存在也不会出错
        email = result_data.get('email', "N/A")
        website = result_data.get('website', "")
        facebook = result_data.get('facebook', "")
        instagram = result_data.get('instagram', "")
        linkedin = result_data.get('linkedin', "")
        whatsapp = result_data.get('whatsapp', "")

        self.cell_update_queue.append((row, 3, email))
        self.cell_update_queue.append((row, 4, website))
        self.cell_update_queue.append((row, 5, facebook))
        self.cell_update_queue.append((row, 6, instagram))
        self.cell_update_queue.append((row, 7, linkedin))
        self.cell_update_queue.append((row, 8, whatsapp))
        
        # 2. 准备数据库更新指令
        # name_item = self.table.item(row, 0)
        address_item = self.table.item(row, 1)

        if name_item and address_item:
            name = name_item.text()
            address = address_item.text()
            # 更新邮箱和官网
            self.db_worker.update_request.emit(name, address, email, website)
            # 更新社交媒体
            self.db_worker.update_social_media_request.emit(name, address, {
                'facebook': facebook,
                'instagram': instagram,
                'linkedin': linkedin,
                'whatsapp': whatsapp
            })


    def check_ai_status(self):
        """向后端异步查询AI权限和Token余量，不会阻塞UI"""
        if not self.user_id:
            self.ai_toggle_btn.setEnabled(False)
            self.ai_toggle_btn.setText("AI功能 (未登录)")
            self.token_label.setText("剩余次数: -")
            return

        print("🚀 正在后台异步检查AI状态...")
        # 创建并启动检查器线程
        self.status_checker = AIStatusChecker(self.user_id)
        # 将线程完成后的信号连接到我们新加的处理函数
        self.status_checker.status_ready.connect(self.handle_ai_status_result)
        # 线程任务完成后，自动调度删除，避免内存泄漏
        self.status_checker.finished.connect(self.status_checker.deleteLater)
        self.status_checker.start()

    def on_ai_toggle(self, checked):
        """处理AI按钮的点击事件"""
        if checked:
            # 用户尝试开启AI，再次检查状态
            self.check_ai_status() 
            if self.ai_toggle_btn.isEnabled():
                self.ai_toggle_btn.setText("深度获客 (开启)")
            else:
                # 如果检查后发现无权限，则自动弹回
                self.ai_toggle_btn.setChecked(False)
        else:
            self.ai_toggle_btn.setText("深度获客 (关闭)")

    def start_ai_enrichment(self):
        """取出队列中的公司，并启动AIFetcher线程"""
        if len(self.ai_batch_queue) < self.AI_BATCH_SIZE:
            return

        print(f"📦 AI队列已满，打包 {self.AI_BATCH_SIZE} 个公司开始深度信息提取...")

        # 取出指定数量的批次
        batch_to_process = self.ai_batch_queue[:self.AI_BATCH_SIZE]
        # 从队列中移除已取出的
        self.ai_batch_queue = self.ai_batch_queue[self.AI_BATCH_SIZE:]

        # 创建AI处理线程
        ai_fetcher = AIFetcher(batch_to_process, self.user_id)

        # 连接信号与槽
        ai_fetcher.dataEnriched.connect(self.update_table_with_ai_data)
        ai_fetcher.errorOccurred.connect(self.on_ai_error)
        ai_fetcher.tokenUpdated.connect(lambda tokens: self.token_label.setText(f"AI Tokens: {tokens}"))

        # 复用原有的线程清理逻辑
        # 注意：需要修改cleanup_fetcher以支持多种线程
        ai_fetcher.finished.connect(lambda f=ai_fetcher: self.cleanup_fetcher(f, "ai"))

        self.ai_fetchers.append(ai_fetcher) # 保存线程引用，防止被回收
        ai_fetcher.start()

    def update_table_with_ai_data(self, ai_data, original_batch):
        """用AI返回的数据更新表格"""
        print("✅ 收到AI处理结果，正在更新表格...")
        if "公司" not in ai_data:
            print("❌ AI返回数据格式不正确，缺少'公司'键。")
            return

        ai_company_list = ai_data["公司"]

        # 使用原始批次中的公司名和行号来匹配更新
        for original_company in original_batch:
            original_name = original_company.get("name")
            row_to_update = original_company.get("row")

            # 在AI返回结果中找到对应的公司
            for ai_company in ai_company_list:
                if ai_company.get("name") == original_name:
                    print(f"   -> 正在更新: {original_name} (行: {row_to_update})")
                    # 更新表格项 (假设列号: 3-邮箱, 4-官网)
                    self.table.setItem(row_to_update, 3, QTableWidgetItem(ai_company.get("email", "")))
                    self.table.setItem(row_to_update, 4, QTableWidgetItem(ai_company.get("website", "")))
                    # 提示：您可以在表格中新增列来显示更多AI获取的信息，如社交链接、贸易数据等
                    break 

    def on_ai_error(self, message):
        """处理AI错误"""
        print(f"❌ AI 处理出错: {message}")
        QMessageBox.warning(self, "AI错误", message)

    # 重写窗口关闭事件，以确保Playwright被安全关闭。
    def closeEvent(self, event):
        """
        【安全修复版】
        重写窗口关闭事件，使用正确的顺序安全地关闭所有后台服务和线程。
        """
        # 1. 弹窗确认退出 (这部分逻辑保持不变)
        reply = QMessageBox.question(self, '确认退出', '确定要退出程序吗？',
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.No:
            event.ignore() # 用户选择不退出，忽略关闭事件
            return

        print("程序即将关闭，开始执行清理工作...")

        # --- ▼▼▼ 【核心修复】调整资源关闭的顺序 ▼▼▼ ---

        # 2. 首先，设置停止标志，并保存最终进度
        if self.is_searching:
            print("...检测到任务正在运行，设置停止标志并保存最终进度...")
            self.is_searching = False # 告诉所有循环立即停止

        
        # 3. 然后，等待 QThreadPool 中的所有 EmailFetcherWorker 任务执行完毕
        #    这是最关键的一步，确保“工人们”先下班
        print("...正在等待所有后台数据提取任务完成...")
        self.thread_pool.waitForDone(5000) # 等待最多5秒
        print("...所有后台数据提取任务已结束。")

        # 4. 在确保没有任务再使用它们之后，再安全地关闭后台服务
        if self.playwright_manager is not None:
            print("...正在关闭 Playwright 管理器...")
            self.playwright_manager.shutdown()
        
        if self.whatsapp_manager is not None:
            print("...正在关闭 WhatsApp 管理器...")
            self.whatsapp_manager.shutdown()

        # 5. 最后关闭数据库连接线程
        print("...正在关闭数据库管理器...")
        self.db_worker.stop()
        # --- ▲▲▲ 修复结束 ▲▲▲ ---

        print("清理工作完成，程序将安全退出。")
        event.accept() # 接受关闭事件，允许窗口关闭
        sys.exit(0)


    # 检查是否所有任务（地图抓取 + 所有后台邮箱抓取）都已完成。

    def handle_ai_status_result(self, data):
        """处理从AIStatusChecker线程返回的状态结果"""
        if data.get("success") and "authorized" in data and "tokens_remaining" in data:
            is_authorized = data.get("authorized")
            tokens = data.get("tokens_remaining", 0)

            if is_authorized:
                self.ai_toggle_btn.setEnabled(True)
                self.token_label.setText(f"剩余次数: {tokens}")
                if not self.ai_toggle_btn.isChecked():
                    self.ai_toggle_btn.setText("深度获客 (关闭)")
                else:
                    self.ai_toggle_btn.setText("深度获客 (开启)")
            else:
                self.ai_toggle_btn.setEnabled(False)
                self.ai_toggle_btn.setChecked(False)
                self.ai_toggle_btn.setText("AI功能 (未授权)")
                self.token_label.setText("剩余次数: -")
        else:
            error_message = data.get("message", "未知后端错误")
            self.ai_toggle_btn.setEnabled(False)
            self.token_label.setText("剩余次数: 查询失败")
            print(f"❌ AI状态检查失败: {error_message}")

    def _on_worker_finished(self, row):
        """
        【改造版】当一个后台邮件任务完成时，这个槽函数会被调用。
        """
        # 1. 减少活跃任务计数 (这部分不变)
        self.active_worker_count -= 1

        # 2. 检查并清理残留的骨架屏 (这部分逻辑不变)
        try:
            item_to_check = self.table.item(row, 3)
            if item_to_check and item_to_check.text() == "██████████████":
                print(f"🧹 (行: {row}) 清理小队发现残留的骨架屏，正在进行清理...")
                for col in range(3, 9):
                    self.table.setItem(row, col, QTableWidgetItem(""))
        except Exception as e:
            print(f"❌ 清理骨架屏时发生意外错误: {e}")

        # --- ▼▼▼ 【核心修复】用调用调度员替换旧的检查方法 ▼▼▼ ---
        # 当一个邮件任务完成，我们呼叫调度员。
        # 调度员会检查所有条件（任务队列、标签页、邮件任务），
        # 并决定是继续分配地图采集任务，还是宣布全部工作完成。
        self._dispatch_tasks()
        # --- ▲▲▲ 修复结束 ▲▲▲ ---

    def _process_ui_update_queue(self):
        """
        【UI更新平滑化修复版】
        通过分批处理UI更新队列，避免因数据瞬间涌入导致的“更新风暴”和界面卡顿。
        """
        # 如果两个队列都是空的，就直接返回，不执行任何操作
        if not self.ui_update_queue and not self.cell_update_queue:
            return

        # 1. 定义每个周期（即每次定时器触发）最大处理的任务数量
        MAX_UPDATES_PER_CYCLE = 50 

        # 关键性能优化：在所有操作开始前禁用UI更新，防止每一步都重绘
        self.table.setUpdatesEnabled(False)
        try:
            # 2. 循环处理，直到达到最大处理数或两个队列都为空
            for _ in range(MAX_UPDATES_PER_CYCLE):
                # 3. 优先处理“新增行”的队列，因为这比更新单元格更重要
                if self.ui_update_queue:
                    # 从队列头部取出一个任务并处理
                    item = self.ui_update_queue.pop(0) 
                    
                    # 判断数据来源，调用不同的行添加方法
                    if item.get('source') == 'db_reload':
                        self._add_full_company_row_to_table(item)
                    else:
                        self.show_result_single(item)

                # 4. 如果“新增行”队列空了，再处理“更新单元格”的队列
                elif self.cell_update_queue:
                    # 从队列头部取出一个任务并处理
                    row, col, text = self.cell_update_queue.pop(0)
                    if row < self.table.rowCount(): # 安全检查，防止行号越界
                        self.table.setItem(row, col, QTableWidgetItem(text))
                
                # 5. 如果两个队列都处理完了，就提前结束本周期的循环
                else:
                    break
        finally:
            # 关键性能优化：所有批处理操作完成后，一次性启用更新，让所有变化同时高效地显示出来
            self.table.setUpdatesEnabled(True)

    def pause_for_captcha(self):
        """
        当检测到人机验证时，调用此方法来暂停程序。
        """
        # 1. 设置暂停状态
        self.is_paused_for_captcha = True
        print("⏸️ 程序已暂停，等待用户处理人机验证...")

        # 2. 修改“开始搜索”按钮，使其变为“恢复任务”按钮
        self.search_btn.setText("恢复任务")
        
        # 3. 解绑旧的点击事件，绑定新的“恢复”事件
        try:
            self.search_btn.clicked.disconnect(self.start_search_batch)
        except TypeError:
            # 如果之前没有连接过，disconnect会抛出TypeError，可以安全地忽略
            pass
        self.search_btn.clicked.connect(self.resume_from_captcha)

        # 4. 弹窗提示用户
        QMessageBox.warning(self, "需要您操作",
                            "检测到Google人机验证，自动抓取已暂停。\n\n"
                            "请在下方的内置浏览器中手动完成验证后，点击“恢复任务”按钮继续。")

    def resume_from_captcha(self):
        """
        用户点击“恢复任务”按钮后，调用此方法来继续执行。
        """
        # 1. 恢复状态
        self.is_paused_for_captcha = False
        print("▶️ 用户已操作，正在恢复任务...")

        # 2. 将按钮改回“开始搜索”
        self.search_btn.setText("开始搜索")

        # 3. 再次解绑“恢复”事件，重新绑定回“开始”事件
        try:
            self.search_btn.clicked.disconnect(self.resume_from_captcha)
        except TypeError:
            pass
        self.search_btn.clicked.connect(self.start_search_batch)

        # 4. 【关键】从中断的地方继续：重新调用等待函数
        #    此时页面上的人机验证应该已经解决了
        self.wait_for_search_results()


    def on_item_processing_timeout(self):
        """
        独立的“看门狗”定时器触发时调用的方法。
        """
        # 检查是否真的有一个任务卡住了
        if self.is_currently_processing_item:
            print(f"🚨 【看门狗超时】处理第 {self.current_index + 1} 个商家超过 {self.ITEM_PROCESSING_TIMEOUT} 秒，判定为卡死。")
            print("➡️ 强制放弃当前项，继续处理下一个...")
            
            # 调用我们统一的“完成并继续”的函数
            self.after_extraction_and_move_on()




    # ==================== 新增的槽函数（处理菜单点击） 开始 ====================
    def open_website(self):
        """打开公司官网"""
        # 请将这里的链接替换成您真实的官网地址
        url = QUrl("https://mediamingle.cn") # 示例链接
        QDesktopServices.openUrl(url)

    # 打开教程文档页面
    def open_tutorial_page(self):
        """打开教程文档页面"""
        # 这里是您提供的教程文档链接
        url = QUrl("https://mediamingle.cn/product.html?id=maps-scraper")
        QDesktopServices.openUrl(url)


    def open_contact_page(self):
        """打开联系我们页面"""
        # 请将这里的链接替换成您真实的联系页面地址
        url = QUrl("https://mediamingle.cn/contact.html") # 示例链接
        QDesktopServices.openUrl(url)

    def show_about_dialog(self):
        """显示一个简单的“关于”对话框"""
        QMessageBox.about(self, "关于 GoogleMapsScraper",
                          "<b>GoogleMapsScraper v1.0.7</b><br>"
                          "一款强大的自动化拓客工具。<br><br>"
                          "版权所有 © 2025 龄龙科技有限公司")
        
    def reload_page(self):
        """重新加载内置浏览器页面"""
        self.browser.reload()

    def zoom_in(self):
        """放大浏览器视图"""
        current_zoom = self.browser.zoomFactor()
        self.browser.setZoomFactor(current_zoom + 0.1)

    def zoom_out(self):
        """缩小浏览器视图"""
        current_zoom = self.browser.zoomFactor()
        self.browser.setZoomFactor(current_zoom - 0.1)

    def reset_zoom(self):
        """重置浏览器视图为100%"""
        self.browser.setZoomFactor(1.0)

    def toggle_full_screen(self):
        """切换窗口全屏状态"""
        if self.isFullScreen():
            # 当前是全屏，所以要退出全屏
            self.showNormal()
            # 【核心修复】将菜单文本改回“切换全屏”
            self.fullscreen_action.setText("切换全屏")
        else:
            # 当前是普通窗口，所以要进入全屏
            self.showFullScreen()
            # 【核心修复】将菜单文本改为“退出全屏”
            self.fullscreen_action.setText("退出全屏")


    def pause_search(self):
        """【改造版】暂停当前的搜索任务"""
        if not self.is_searching: return
        
        self.is_searching = False # 【关键】设置全局停止标志，所有循环都会因此而暂停
        # 更新UI
        self.pause_search_action.setVisible(False)
        self.resume_search_action.setVisible(True)
        self.stop_search_action.setEnabled(True)
        
        # 停止所有标签页的当前加载（如果有的话）
        for tab_info in self.tabs:
            if tab_info['state'] == 'running':
                tab_info['view'].stop()
                # 将状态改为 'idle'，这样“继续”时调度员会自动重新分配任务
                tab_info['state'] = 'idle' 

        print("⏸️ 搜索已暂停。所有页面已停止，任务队列被保留。")
        QMessageBox.information(self, "任务已暂停", "搜索已暂停，您可以随时点击“继续搜索”恢复。")

    def resume_from_pause(self):
        """【改造版】从暂停状态恢复搜索"""
        if self.is_searching: return # 防止重复点击
        
        self.is_searching = True
        # 更新UI
        self.pause_search_action.setVisible(True)
        self.resume_search_action.setVisible(False)
        self.stop_search_action.setEnabled(True)

        print("▶️ 正在从暂停中恢复...")
        
        # 【关键】恢复任务不再是调用旧方法，而是直接呼叫“任务调度员”，
        # 它会根据当前的任务队列和空闲页面，自动开始或继续工作。
        self._dispatch_tasks()

    def stop_search(self): # 这个方法现在是“中止”
        if self.is_searching: # 只有在运行时才能中止
            print("🛑 用户请求中止任务...")
            self.is_searching = False

            # 恢复UI初始状态
            self.progress_bar.hide()
            self.stop_search_action.setEnabled(False)
            self.pause_search_action.setEnabled(False)
            self.pause_search_action.setVisible(True)
            self.resume_search_action.setVisible(False)
            QMessageBox.information(self, "操作完成", "搜索任务已中止。")

    def clear_all_results(self):
        """清除表格和数据库中的所有结果"""
        reply = QMessageBox.question(self, '确认操作', 
                                     '您确定要清除表格和数据库中的所有结果吗？\n此操作将永久删除所有已保存的数据，不可撤销。',
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            # 1. 清空UI表格
            self.table.setRowCount(0)
            # 2. 清空内存缓存
            self.processed_items_cache.clear()
            
            # --- ▼▼▼ 【【【在这里补上这句关键代码】】】 ▼▼▼ ---
            # 3. 调用后台数据库工作线程，执行清空数据库的操作
            success = self.db_worker.clear_all_companies_blocking()
            # --- ▲▲▲ 【【【代码补充完毕】】】 ▲▲▲ ---

            if success:
                print("🗑️ 表格、缓存和数据库均已清空。")
                QMessageBox.information(self, "操作成功", "所有本地数据均已清除。")
            else:
                print("❌ 清除数据库时发生错误。")
                QMessageBox.warning(self, "操作失败", "清除数据库时发生错误，请检查日志。")

    def check_license_status(self):
        """【修改版】定时检查授权，并处理即将到期的情况"""
        if not self.credentials:
            return

        print("🕒 正在执行定期的授权状态检查...")
        # ... (LicenseCheckWorker 的定义保持不变) ...
        # 在 LicenseCheckWorker 的 run 方法中，需要让它返回剩余天数
        # 为了简化，我们直接在主线程处理
        self._update_expiry_display() # 每次检查时，先更新一次UI显示

        try:
            from datetime import datetime, timezone
            if not self.expiry_at: return # 永久授权，无需检查

            if self.expiry_at.endswith("Z"):
                expiry_date = datetime.fromisoformat(self.expiry_at[:-1]).replace(tzinfo=timezone.utc)
            else:
                expiry_date = datetime.fromisoformat(self.expiry_at)

            remaining_days = (expiry_date - datetime.now(timezone.utc)).days

            if remaining_days < 0:
                self.on_license_check_complete(False, "您的账号已过期，请立即续费。")
            elif remaining_days <= 7:
                self.on_license_check_complete(True, f"您的账号即将到期（剩余 {remaining_days + 1} 天），建议您及时续费。")
            else:
                print("✅ 定期授权检查通过。")

        except Exception as e:
            print(f"❌ 定期授权检查时发生错误: {e}")

    def on_license_check_complete(self, is_valid, message):
        """【修改版】处理授权检查结果，并弹出续费提示"""
        # 如果授权有效，但属于“即将到期”的提醒，也需要弹窗
        if is_valid and "即将到期" in message:
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Warning)
            msg_box.setWindowTitle("授权即将到期提醒")
            msg_box.setText(f"<b>{message}</b>")
            msg_box.setInformativeText("为避免服务中断，请考虑续费。")

            renew_button = msg_box.addButton("立即续费", QMessageBox.ActionRole)
            later_button = msg_box.addButton("稍后提醒", QMessageBox.RejectRole)

            # 1. 获取当前窗口已有的标志
            flags = msg_box.windowFlags()
            # 2. 在原有标志的基础上，通过“按位或”操作，添加“保持在最顶层”的提示
            msg_box.setWindowFlags(flags | Qt.WindowStaysOnTopHint)

            msg_box.exec_()

            if msg_box.clickedButton() == renew_button:
                # --- 在这里换上您的官网续费链接 ---
                QDesktopServices.openUrl(QUrl("https://mediamingle.cn/checkout.html"))

        # 如果授权已确定无效（过期）
        elif not is_valid:
            self.license_check_timer.stop()
            msg_box = QMessageBox(self)
            msg_box.setIcon(QMessageBox.Critical)
            msg_box.setWindowTitle("授权已过期")
            msg_box.setText(f"<b>{message}</b>")
            msg_box.setInformativeText("您的所有功能已被限制，请续费以恢复使用。")

            renew_button = msg_box.addButton("立即续费", QMessageBox.ActionRole)
            exit_button = msg_box.addButton("退出程序", QMessageBox.RejectRole)

            flags = msg_box.windowFlags()
            msg_box.setWindowFlags(flags | Qt.WindowStaysOnTopHint)

            msg_box.exec_()

            if msg_box.clickedButton() == renew_button:
                QDesktopServices.openUrl(QUrl("https://mediamingle.cn")) # --- 同样换成您的链接 ---

            # 无论用户点击“续费”还是“退出”，最终都会触发会话过期，返回登录界面
            self.session_expired.emit()

    # 在 GoogleMapsApp 类中添加这个方法
    # def get_playwright_manager(self):
    #     """
    #     【死锁修复版】
    #     首次调用时，将Playwright的初始化任务提交到后台执行，
    #     但绝不阻塞主UI线程。
    #     """
    #     # 检查实例是否还不存在
    #     if self.playwright_manager is None:
    #         print("首次调用，正在初始化 Playwright 管理器... (这可能需要一些时间)")
            
    #         # 步骤1: 创建管理器实例 (这会启动后台事件循环)
    #         self.playwright_manager = PlaywrightManager()

    #         # --- ▼▼▼ 核心修复代码 ▼▼▼ ---
    #         # 步骤2: 将耗时的、异步的初始化方法安全地提交到它自己的后台事件循环中去执行。
    #         #        这个调用是“发射后不管”的，它会立即返回，不会阻塞当前的主UI线程。
    #         #        后台的 Playwright 线程会自己负责完成浏览器的启动。
    #         pm_loop = self.playwright_manager._loop
    #         if pm_loop:
    #             asyncio.run_coroutine_threadsafe(self.playwright_manager._initialize_internal(), pm_loop)
    #         else:
    #             print("❌ 严重错误: Playwright 管理器的事件循环未能启动！")
    #             # 在这种极端情况下，可以考虑禁用相关功能或提示用户
    #             self.is_degraded_mode = True
    #             QMessageBox.critical(self, "初始化失败", "后台浏览器服务未能启动，深度信息采集功能将不可用。")
    #             return self.playwright_manager # 仍然返回实例，但它是未初始化状态
    #         # --- ▲▲▲ 修复代码结束 ▲▲▲ ---

    #         # 步骤3: 立即设置快速模式，这不依赖于浏览器是否已启动
    #         self.playwright_manager.set_speed_mode(self.is_speed_mode)
    #         print("Playwright 初始化任务已提交到后台，主程序继续执行。")

    #     # 立即返回实例。
    #     # 后续的邮件提取任务在需要使用Playwright时，会自然地等待其初始化完成。
    #     return self.playwright_manager

    def get_playwright_manager(self):
        """【健壮性修复版】此方法现在只负责返回已在__init__中创建的单例"""
        return self.playwright_manager

    # 从本地文件加载完整的配置信息
    def _load_user_config(self):
        """从本地文件加载完整的配置信息"""
        config_path = get_app_data_path("user_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                return {}
        return {}

# (在文件中找到 AppManager 类，并用下面的代码完整替换它)

class AppManager(QObject):
    """一个用于管理登录窗口和主窗口生命周期的类"""
    def __init__(self):
        super().__init__()
        self.login_dialog = None
        self.main_window = None
        self.update_checker = None # 添加一个引用来管理更新线程

    def start(self):
        if self.main_window:
            self.main_window.close()
            self.main_window = None

        # --- 1. 计算尺寸 ---
        screen = QApplication.primaryScreen()
        if screen is None: screen = QApplication.screens()[0]
        available_geometry = screen.availableGeometry()
        screen_width = available_geometry.width()
        screen_height = available_geometry.height()

        # 1. 根据您指定的新比例计算主窗口的目标尺寸
        self.main_app_width = int(screen_width * 3 / 10)  # 宽度为十分之三
        self.main_app_height = int(screen_height * 4 / 5) # 高度为五分之四
        
        # 确保尺寸不会过小
        self.main_app_width = max(self.main_app_width, 1024) # 最小宽度
        self.main_app_height = max(self.main_app_height, 768)  # 最小高度
        
        print(f"屏幕可用尺寸: {available_geometry.width()}x{available_geometry.height()}, 程序目标尺寸: {self.main_app_width}x{self.main_app_height}")

        # --- 2. 启动更新检查 ---
        self.update_checker = UpdateChecker(
            current_version=CURRENT_APP_VERSION, 
            repo_url=GITHUB_REPO_URL
        )
        self.update_checker.update_available.connect(self.handle_update_available)
        self.update_checker.finished.connect(self.update_checker.deleteLater)
        self.update_checker.start()

        # --- 3. 创建并显示登录窗口 ---
        self.login_dialog = LoginDialog()
        result = self.login_dialog.exec_()

        # --- 4. 处理登录结果 ---
        if result == QDialog.Accepted:
            user_id = getattr(self.login_dialog, "logged_in_user_id", None)
            user_type = getattr(self.login_dialog, "user_type", None)
            expiry_at = getattr(self.login_dialog, "expiry_at", None)
            trial_search_used = getattr(self.login_dialog, "trial_search_used", False)
            daily_export_count = getattr(self.login_dialog, "daily_export_count", 0)

            config = self.login_dialog._load_config_data()
            username = config.get("last_login_user")
            credentials = None
            if username and "users" in config and username in config["users"]:
                credentials = {
                    "username": username,
                    "password": base64.b64decode(config["users"][username]["password"].encode('utf-8')).decode('utf-8'),
                    "device_id": config["users"][username]["device_id"],
                    "os_type": platform.system()
                }

            if user_id and credentials:
                self.show_main_window(user_id, credentials, user_type, expiry_at, trial_search_used, daily_export_count)
            else:
                sys.exit(0)
        else:
            sys.exit(0)


    def show_main_window(self, user_id, credentials, user_type, expiry_at, trial_search_used, daily_export_count):
        # 这个方法现在只负责创建主窗口
        self.main_window = GoogleMapsApp(
            user_id=user_id, credentials=credentials, user_type=user_type, expiry_at=expiry_at, 
            trial_search_used=trial_search_used, daily_export_count=daily_export_count,
            # --- ▼▼▼ 【核心修复】将新计算的尺寸传递过去 ▼▼▼ ---
            width=self.main_app_width, height=self.main_app_height 
        )
        self.main_window.session_expired.connect(self.start)
        self.main_window.show()

    # --- ▼▼▼ 【新增】处理更新信号的槽函数 ▼▼▼ ---
    def handle_update_available(self, new_version, url):
        """
        当后台线程发现新版本时，此方法被调用以显示弹窗。
        """
        # 获取当前活动的窗口作为父窗口，确保弹窗在最前面
        parent_window = QApplication.activeWindow()
        
        msg_box = QMessageBox(parent_window)
        msg_box.setIcon(QMessageBox.Information)
        msg_box.setWindowTitle("发现新版本！")
        
        msg_box.setText(
            f"<b>发现新版本 {new_version}！</b><br><br>"
            "建议您更新到最新版本以获取最佳体验和新功能。"
        )
        msg_box.setInformativeText(
            f'您可以从以下地址下载：<br><a href="{url}">{url}</a>'
        )
        msg_box.setTextFormat(Qt.RichText)
        
        download_button = msg_box.addButton("立即下载", QMessageBox.ActionRole)
        later_button = msg_box.addButton("稍后提醒", QMessageBox.RejectRole)

        msg_box.exec_()

        # 如果用户点击了“立即下载”，则自动打开链接（会触发浏览器下载）
        if msg_box.clickedButton() == download_button:
            QDesktopServices.openUrl(QUrl(url))



if __name__ == "__main__":
    # 第一次检查：基础依赖（如VC++运行库）
    if check_and_notify_dependencies():
        
        if check_web_engine_component():
            # 只有在两次检查都通过后，才继续执行程序的正常逻辑
            
            QApplication.setAttribute(Qt.AA_UseSoftwareOpenGL)

            app = QApplication(sys.argv)
            
            # --- ▼▼▼ 新增的单例应用程序逻辑 ▼▼▼ ---

            # 1. 定义一个唯一的服务器名称，防止和其他应用冲突
            #    可以使用UUID或者一个独特的字符串
            server_name = "GoogleMapsScraper-Instance-Lock"

            # 2. 尝试连接到本地服务器
            #    这是一个“试探”动作，看看是不是已经有实例在运行了
            socket = QLocalSocket()
            socket.connectToServer(server_name)

            # 3. 判断连接结果
            if socket.waitForConnected(500): # 等待500毫秒
                # 如果能连上，说明服务器已存在，即已有实例在运行
                QMessageBox.warning(None, "程序已在运行", 
                                    "Google Maps 采集器已经有一个实例在运行了。\n请检查您的任务栏或系统托盘。")
                # 提示后直接退出
                sys.exit(0) 
            else:
                # 如果连不上，说明自己是第一个实例
                # a. 创建一个 QLocalServer
                local_server = QLocalServer()
                # b. 监听上面定义的唯一名称
                local_server.listen(server_name)

                # --- ▲▲▲ 单例逻辑结束，开始正常的程序启动流程 ▲▲▲ ---
                
                print("✅ 依赖检查通过，正在启动应用程序...")
                
                app.setQuitOnLastWindowClosed(False)

                manager = AppManager()
                manager.start()

                sys.exit(app.exec_())
        else:
            # 如果浏览器核心组件检查失败
            print("❌ 浏览器核心组件检查失败，程序已终止。")
            sys.exit(1)

    else:
        # 如果基础依赖检查失败
        print("❌ 基础依赖检查失败，程序已终止。请根据弹窗提示解决问题。")
        sys.exit(1)
