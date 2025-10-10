#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vercel 入口文件
专门为Vercel部署优化的Flask应用入口
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入主应用
from app import app

# Vercel WSGI 处理器
def handler(request):
    """Vercel WSGI 处理器"""
    return app(request)

# 导出应用实例
application = app
