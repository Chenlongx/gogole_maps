
import os
import sys
import csv
import re
import json
import aiohttp
import asyncio
import platform
import uuid
import html
import time
import traceback
import requests
import pandas as pd
from PyQt5.QtGui import QIcon, QPixmap
from openpyxl.styles import Font
from PyQt5.QtCore import QThread, pyqtSignal, QPoint, QSize, QThreadPool, pyqtSlot
from urllib.parse import urljoin, urlparse, quote, parse_qs, unquote
from bs4 import BeautifulSoup
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
                             QTableWidget, QTableWidgetItem, QLabel, QFileDialog, QMessageBox, QComboBox, QDialog, QGraphicsDropShadowEffect, QSizePolicy, QFrame)
from PyQt5.QtCore import Qt, QUrl, QTimer, QPropertyAnimation, QEasingCurve, QRunnable, QObject
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtWidgets import QTableWidget, QHeaderView
from PyQt5.QtWebEngineWidgets import QWebEnginePage, QWebEngineView, QWebEnginePage
from PyQt5.QtWidgets import QProgressBar
import base64
import chardet
from playwright.async_api import async_playwright, Playwright, Browser
import threading
import sqlite3



class WorkerSignals(QObject):
    """
    定义EmailFetcherWorker可以发出的所有信号。
    """
    # 信号格式: (找到的邮箱, 找到的官网URL, 表格行号)
    emailAndWebsiteFound = pyqtSignal(str, str, int)
    # 任务完成信号
    finished = pyqtSignal()




class EmailFetcherWorker(QRunnable):
    """
    一个可被QThreadPool执行的任务单元，包含了所有抓取邮箱的逻辑。
    """
    URL_BLOCKLIST = {
        'google.com/recaptcha',
        'googletagmanager.com',
        'google-analytics.com',
        'doubleclick.net',
        'facebook.net',
        'fbcdn.net',
        'twitter.com/widgets.js',
        'maps.google.com',
        'maps.googleapis.com'
    }

    def __init__(self, website, company_name, address, phone, row, playwright_manager, country):
        super().__init__()
        # 接收所有必要的参数
        self.website = website
        self.company_name = company_name
        self.address = address
        self.phone = phone
        self.row = row
        self.playwright_manager = playwright_manager

        self.country = country

        # 从官网URL中提取并存储初始域名，用于后续判断
        if self.website:
            self.initial_domain = urlparse(self.website).netloc
        else:
            self.initial_domain = "" # 如果没有官网，则设置为空字符串


        # 实例化信号容器
        self.signals = WorkerSignals()

        # ---------------------------------------------------------------
        # 【重要】: 将原来 EmailFetcher 类中所有的逻辑代码(除了__init__和run)
        #           原封不动地复制到这里。
        # ---------------------------------------------------------------
        self.email_pattern = r"\b[a-zA-Z0-9._%+-]*[a-zA-Z][a-zA-Z0-9._%+-]*@[a-zA-Z0-9-]+(?:\.[a-zA-Z]{2,})+\b"
        self.excluded_domains = {"hotmail.com", "o405442.ingest.sentry.io"}
        self.temp_domains = {"tempmail.com", "mailinator.com", "guerrillamail.com"}
        self.target_paths = [
            'contact', 'about', 'team', 'support', 'careers', 
            'contact-us', 'about-us', 'get-in-touch', 'info',
            'контакти', 'privacy', 'terms'
        ]
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        self.found_emails_on_page_with_phone = []



    def score_email(self, email, source_url, was_on_page_with_phone):
        """
        为找到的邮箱打分，以决定其优先级。

        Args:
            email (str): 候选邮箱地址。
            source_url (str): 发现该邮箱的页面URL。
            was_on_page_with_phone (bool): 是否与电话号码在同一页面找到。

        Returns:
            int: 该邮箱的得分。
        """
        score = 0
        try:
            local_part, domain = email.lower().split('@')
            website_domain = urlparse(self.website).netloc.replace('www.', '')
        except ValueError:
            return -999 # 格式不正确的邮箱，直接淘汰

        # 1. 最高优先级：与电话号码共现 (这是最强的相关性信号)
        if was_on_page_with_phone:
            score += 100

        # 2. 域名匹配
        if domain == website_domain:
            score += 50  # 与官网主域名完全匹配，加高分
        elif website_domain in domain:
            score += 20  # 是官网的子域名，加分

        # 3. 关键词匹配 (local_part, 即@前面的部分)
        good_keywords = ['info', 'contact', 'sales', 'support', 'hello', 'admin', 'service', 'enquiries', 'office', 'お問い合わせ']
        if any(keyword in local_part for keyword in good_keywords):
            score += 30

        # 4. 页面来源URL匹配
        if any(path_keyword in source_url.lower() for path_keyword in self.target_paths):
            score += 20 # 如果来自 "contact", "about" 等页面，加分

        # 5. 惩罚项：通用公共邮箱 (如非必要，我们不想要这个)
        # public_domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'aol.com']
        # if any(public_domain in domain for public_domain in public_domains):
        #     score -= 40

        # 6. 惩罚项：不希望的邮箱类型
        bad_keywords = ['noreply', 'privacy', 'abuse', 'no-reply', 'unsubscribe']
        if any(keyword in local_part for keyword in bad_keywords):
            score -= 60
            
        # 7. 惩罚项：垃圾/示例邮箱
        if any(k in email for k in ['example', 'test', 'spam', 'yourdomain', 'sentry.io']):
            return -999 # 直接淘汰

        return score


    def filter_emails(self, emails):
        """
        邮箱过滤规则：
        1. 域名黑名单
        2. 临时邮箱域名
        3. 本地部分必须包含至少两个字母
        4. 字母比例不能太低（防止纯数字/随机ID）
        """
        filtered = []
        for email in emails:
            # 拆分邮箱
            if "@" not in email:
                continue
            local_part, domain = email.split("@", 1)
            domain = domain.lower()

            # 1. 域名黑名单
            if domain in self.excluded_domains:
                continue

            # 2. 临时邮箱域名
            if domain in self.temp_domains:
                continue

            if self.country != "China":
                if domain.endswith('.cn') or domain == '163.com':
                    # 打印一条日志，方便调试（可选）
                    # print(f"🚫 已根据国家 '{self.country}' 过滤邮箱: {email}")
                    continue # 跳过当前循环，处理下一个邮箱

            # 3. 至少两个字母
            letters = sum(c.isalpha() for c in local_part)
            if letters < 2:
                continue

            # 4. 字母比例要求
            if letters / len(local_part) < 0.4:
                continue

            filtered.append(email)

        return filtered
    

    # (在 EmailFetcher 类中，替换旧的 fetch_page 方法)
    async def fetch_page(self, url, session, timeout=10, max_bytes=None):
        """
        优化版 fetch_page：
        1. 捕获 403 和超时错误并直接使用 Playwright 重试。
        2. 保留原有的限时、编码检测等功能。
        """
        if any(blocked_domain in url for blocked_domain in self.URL_BLOCKLIST):
            print(f"🚫 URL命中黑名单，已跳过: {url}")
            return None # 直接返回，不进行任何网络请求

        is_asset_file = any(url.lower().endswith(ext) for ext in [
            '.js', '.css', '.json', '.xml', 
            '.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp',
            '.woff', '.woff2', '.ttf', '.otf', '.eot'
        ])
        
        try:
            async with session.get(url, timeout=timeout, ssl=False, headers={'User-Agent': self.user_agent}) as response:
                if response.status == 403:
                    # 如果是资源文件，就不要重试了
                    if is_asset_file or urlparse(url).netloc != self.initial_domain:
                        print(f"🚫 aiohttp 访问资源文件被拒绝 (403): {url}，已跳过。")
                        return None
                    
                    print(f"🚫 aiohttp 访问被拒绝 (403): {url}。正在切换至浏览器模式重试...")
                    return await self.playwright_manager.get_page_content(url)

                if response.status == 200:
                    # ... (此处的成功逻辑保持不变) ...
                    raw_bytes = await response.read()

                    if max_bytes and len(raw_bytes) > max_bytes:
                        print(f"⚠️ 页面过大已跳过: {url}")
                        return None

                    charset = None
                    content_type = response.headers.get('Content-Type', '')
                    if 'charset=' in content_type:
                        charset = content_type.split('charset=')[-1].strip()

                    if charset:
                        try:
                            return raw_bytes.decode(charset, errors='replace')
                        except (UnicodeDecodeError, LookupError):
                            print(f"⚠️ 指定编码解码失败，进入自动检测: {url}")
                            charset = None

                    sample = raw_bytes[:4096]
                    result = chardet.detect(sample)
                    detected_encoding = result['encoding']
                    confidence = result['confidence']
                    if detected_encoding and confidence > 0.8:
                        try:
                            return raw_bytes.decode(detected_encoding, errors='replace')
                        except UnicodeDecodeError:
                            pass

                    for enc in ['utf-8', 'gbk', 'latin-1']:
                        try:
                            return raw_bytes.decode(enc, errors='replace')
                        except UnicodeDecodeError:
                            continue
                    return None
                else:
                    print(f"❌ 获取页面失败 ({url}): HTTP {response.status}")
                    return None
        except asyncio.TimeoutError:
            # 如果是资源文件，超时后也不要重试
            if is_asset_file or urlparse(url).netloc != self.initial_domain:
                print(f"⏳ aiohttp 请求资源文件超时: {url}，已跳过。")
                return None

            print(f"⏳ aiohttp 请求超时: {url}。正在切换至浏览器模式重试...")
            # =======================================================
            # 【修改点】同样，直接 await playwright_manager 的方法
            # =======================================================
            return await self.playwright_manager.get_page_content(url)
        except aiohttp.ClientSSLError as ssl_err:
            print(f"❌ SSL 错误 ({url}): {ssl_err}")
            return None
        except Exception as e:
            print(f"❌ 无法获取页面 ({url}): {type(e).__name__} - {e}")
            return None






    async def extract_emails(self, text, source_url):
        """
        从页面文本中提取邮箱，并检查是否存在电话号码。
        如果存在电话号码，将该页面的邮箱标记为更相关的邮箱。
        """
        # 首先进行反混淆
        clean_text = deobfuscate_text(text)

        soup = BeautifulSoup(clean_text, 'html.parser')
        normalized_text = ' '.join(soup.get_text(separator=' ').split())
        emails = re.findall(self.email_pattern, normalized_text)

        # 第二步：调用过滤器
        filtered_emails = self.filter_emails(emails)

        # filtered_emails = [email for email in emails if not email.endswith(self.excluded_domains)]
        
        # # 检查页面文本中是否包含电话号码
        # if self.phone and self.check_phone_in_text(normalized_text, self.phone):
        #     print(f"✅ 在包含电话号码的页面发现邮箱: {filtered_emails}")
        #     self.found_emails_on_page_with_phone.extend(filtered_emails)

        # return filtered_emails

        # 检查页面是否包含电话号码
        page_has_phone = self.phone and self.check_phone_in_text(normalized_text, self.phone)
        
        # 将找到的邮箱与它们的来源URL和电话共现信息打包
        results = []
        for email in filtered_emails:
            results.append((email, source_url, page_has_phone))
            # 如果电话共现，我们依然要立刻记录下来，因为它有最高优先级
            if page_has_phone:
                print(f"✅ 在包含电话号码的页面 {source_url} 发现邮箱: {email}")
                self.found_emails_on_page_with_phone.append(email)

        return results
    
    def check_phone_in_text(self, text, phone):
        """检查文本中是否包含给定电话号码的变体"""
        # 移除电话号码中的非数字字符进行宽松匹配
        cleaned_phone = re.sub(r'\D', '', phone)
        # 尝试匹配电话号码的不同格式，例如带空格、破折号、括号等
        # 这是一个简化的匹配，更精确的匹配可能需要更多正则
        return cleaned_phone in re.sub(r'\D', '', text) # 匹配纯数字部分

    async def crawl_subpages(self, base_url, session, depth=0, max_depth=2, visited=None, all_emails=None):
        """
        修改版: 
        1. 收集所有子页面找到的邮箱，而不是找到第一个就返回。
        2. 将当前页面的 URL 作为 source_url 传给 extract_emails。
        3. 【【【新增】】】 使用任务包装器增强 gather 的稳定性。
        """
        if visited is None:
            visited = set()
        if all_emails is None:
            all_emails = []

        if depth > max_depth or base_url in visited:
            return all_emails

        visited.add(base_url)
        text = await self.fetch_page(base_url, session)
        if not text:
            return all_emails

        emails_with_context = await self.extract_emails(text, base_url)
        if emails_with_context:
            all_emails.extend(emails_with_context)

        if depth < max_depth:
            soup = BeautifulSoup(text, 'html.parser')
            links = soup.find_all('a', href=True)
            sub_urls_to_visit = set()

            for link in links:
                href = link['href']
                absolute_url = urljoin(base_url, href)
                parsed_url = urlparse(absolute_url)
                
                if parsed_url.netloc == urlparse(base_url).netloc and absolute_url not in visited:
                    path = parsed_url.path.lower().strip('/')
                    if any(target_path in path for target_path in self.target_paths):
                        sub_urls_to_visit.add(absolute_url)

            sub_urls_to_visit = list(sub_urls_to_visit)[:10] 

            # 【【【修改点】】】
            # 1. 定义一个安全的任务包装器协程
            async def safe_crawl_wrapper(url):
                try:
                    # 注意这里递归调用 crawl_subpages 时，all_emails 列表是共享的
                    # 它会直接修改外部的 all_emails 列表，所以这里不需要接收返回值
                    await self.crawl_subpages(url, session, depth + 1, max_depth, visited, all_emails)
                except Exception as e:
                    print(f"❌ 爬取子页面 {url} 时发生内部错误: {e}")
                # 因为是直接修改列表，所以不需要返回
            
            # 2. 使用包装器创建任务
            tasks = [safe_crawl_wrapper(sub_url) for sub_url in sub_urls_to_visit]
            if tasks:
                await asyncio.gather(*tasks)
            
        return all_emails

    async def fetch_js_for_emails(self, url, session):
        """
        修改版:
        1. 收集所有 JS 文件中找到的邮箱。
        2. 将 JS 文件的 URL 作为 source_url 传入。
        """
        try:
            text = await self.fetch_page(url, session)
            if not text:
                return []
            
            soup = BeautifulSoup(text, 'html.parser')
            script_tags = soup.find_all('script', src=True)
            all_js_emails = []

            # 【【【修改点】】】 为并发任务增加更强的保护
            async def safe_fetch_js_content(js_url):
                try:
                    # print(f"⚡ 尝试从 JS 文件提取: {js_url}") # 调试信息
                    js_content = await self.fetch_page(js_url, session)
                    if js_content:
                        return await self.extract_emails(js_content, js_url)
                except Exception as e:
                    print(f"❌ 处理单个JS文件失败 ({js_url}): {e}")
                return [] # 确保即使出错也返回一个空列表

            tasks = [safe_fetch_js_content(urljoin(url, tag['src'])) for tag in script_tags if tag.get('src')]
            results = await asyncio.gather(*tasks)
            
            for email_list in results:
                all_js_emails.extend(email_list)
                
            return all_js_emails
        except Exception as e:
            print(f"❌ 提取 JS 邮箱主流程失败 ({url}): {e}")
            return []

    async def fetch_json_for_emails(self, url, session):
        """
        修改版: 将 JSON 文件的 URL 作为 source_url 传入。
        """
        possible_json_paths = [
            '/api/contact', '/contact.json', '/data.json', '/info.json', '聯絡我們',
            '/wp-json/wp/v2/users', '/assets/data/contact.json'
        ]

        async def fetch_single_json(path):
            json_url = urljoin(url, path)
            try:
                # ... (内部的 get 请求和 try-except 保持不变) ...
                async with session.get(json_url, timeout=3, ssl=False, headers={'User-Agent': self.user_agent}) as response:
                    if response.status == 200 and 'application/json' in response.headers.get('Content-Type', ''):
                        raw_bytes = await response.read()
                        if len(raw_bytes) > 500 * 1024:
                            return []
                        json_data = await response.json(content_type=None)
                        # 之前: return await self.extract_emails(json.dumps(json_data))
                        # 修改后: 将 json_url 作为 source_url 传入
                        return await self.extract_emails(json.dumps(json_data), json_url)
            except asyncio.TimeoutError:
                pass # print(f"⏳ JSON 请求超时: {json_url}")
            except Exception:
                pass
            return []

        results = await asyncio.gather(*(fetch_single_json(path) for path in possible_json_paths))

        all_json_emails = []
        for r in results:
            if r:
                all_json_emails.extend(r)
        
        return all_json_emails


    # 🔁 从 Bing 搜索结果链接中解析真实 URL（不依赖跳转）
    # 这个函数是同步的，可以在异步方法中直接调用
    def extract_url_from_bing_redirect(self, bing_redirect_url):
        try:
            parsed = urlparse(bing_redirect_url)
            query = parse_qs(parsed.query)
            if 'u' in query:
                encoded_str = query['u'][0]
                # 检查是否为 Base64 + 前缀形式
                if encoded_str.startswith("a1") or encoded_str.startswith("a0"):
                    b64_part = encoded_str[2:]  # 去掉前缀 a1 或 a0
                    # Base64 字符串长度必须是4的倍数，否则需要填充
                    padded = b64_part + "=" * (-len(b64_part) % 4) 
                    try:
                        decoded = base64.b64decode(padded).decode("utf-8")
                        return decoded
                    except Exception as e:
                        # 如果Base64解码失败，可能是普通URL
                        print(f"⚠️ Base64解码失败，尝试URL解码: {e}")
                        return unquote(encoded_str)  # 普通 URL 解码
                else:
                    return unquote(encoded_str)  # 普通 URL 解码
            else:
                return bing_redirect_url
        except Exception as e:
            print(f"⚠️ 解析 Bing 跳转 URL 错误: {e}")
            return bing_redirect_url

    # 通过 Bing 搜索引擎进行搜索
    async def search_with_bing(self, query, session, max_results_to_visit=3):
        """
        【【【修改版】】】
        使用 Playwright 浏览器访问 Bing 搜索，以模拟真人行为，提高成功率。
        """
        try:
            url = f"https://www.bing.com/search?q={quote(query)}&mkt=en-US"
            print(f"🔍 [浏览器模式] 使用 Bing 搜索: {query}")

            # 【【【核心修改点】】】
            # 移除 aiohttp 的 session.get(...) 调用
            # 直接使用封装好的 Playwright 管理器来获取页面内容
            text = await self.playwright_manager.get_page_content(url)

            # 检查 Playwright 是否成功获取到页面内容
            if not text:
                print(f"❌ Bing 搜索失败：浏览器未能获取页面内容 (URL: {url})")
                return [] # 【优化】: 统一返回空列表

            soup = BeautifulSoup(text, "html.parser")

            # Bing 的搜索结果链接通常在 <li class="b_algo"> 下的 <a> 标签
            links = soup.find_all("li", class_="b_algo")
            if not links:
                print("❌ 未找到任何 Bing 搜索结果链接，可能是页面结构变化或无结果")
                return [] # 【优化】: 统一返回空列表

            all_bing_emails = []
            visited_count = 0
            for item in links:
                if visited_count >= max_results_to_visit:
                    break # 只访问前 max_results_to_visit 个结果

                a = item.select_one("h2 a")
                if not a or not a.get('href'):
                    continue

                raw_link = a['href']
                real_link = self.extract_url_from_bing_redirect(raw_link)
                
                if not real_link.startswith(('http://', 'https://')):
                    continue 

                print(f"🌐 访问 Bing 搜索结果真实链接: {real_link}")
                
                # 注意：这里仍然使用 fetch_page，因为它内部已经包含了 aiohttp + Playwright 的双重保障
                page_text = await self.fetch_page(real_link, session)
                if not page_text:
                    continue

                emails_with_context = await self.extract_emails(page_text, real_link)
                if emails_with_context:
                    all_bing_emails.extend(emails_with_context)

                visited_count += 1

            return all_bing_emails

        except Exception as e:
            print(f"❌ Bing 浏览器搜索模式发生未知异常: {type(e).__name__} - {e}")
            return [] # 【优化】: 统一返回空列表


    # 在 EmailFetcher 类中，添加这个新方法
    async def search_with_bing_and_select(self, query, session, top_n_results=10, visit_best_n=3):
        """
        专为无官网情况设计：搜索、筛选最相关的链接、访问并提取邮箱。
        返回 (found_email, found_website_url)
        """
        from difflib import SequenceMatcher # 导入用于计算相似度的库

        def get_similarity(a, b):
            return SequenceMatcher(None, a, b).ratio()

        try:
            url = f"https://www.bing.com/search?q={quote(query)}&mkt=en-US"
            print(f"🔍 使用 Bing 搜索 (en-US Market): {query} (URL: {url})")

            request_headers = {
                'User-Agent': self.user_agent,
                'Accept-Language': 'en-US,en;q=0.9'
            }

            async with session.get(url, timeout=15, ssl=False, headers=request_headers) as response:
                if response.status != 200: return None, None
                text = await response.text()
                soup = BeautifulSoup(text, "html.parser")
                links = soup.find_all("li", class_="b_algo")
                if not links: return None, None

                # 1. 筛选和评分搜索结果链接
                candidate_links = []
                cleaned_company_name = re.sub(r'[^a-z0-9]', '', self.company_name.lower())
                
                for item in links[:top_n_results]:
                    a = item.select_one("h2 a")
                    if not a or not a.get('href'): continue
                    
                    real_link = self.extract_url_from_bing_redirect(a['href'])
                    if not real_link.startswith(('http', 'https')): continue

                    parsed_url = urlparse(real_link)
                    domain = parsed_url.netloc.replace('www.', '')

                    # 如果UI选择的国家不是 "中国", 并且链接域名以 .cn 结尾，则跳过
                    if self.country != "中国" and domain.endswith('.cn'):
                        print(f"🚫 已跳过 .cn 链接 (当前国家: {self.country}): {real_link}")
                        continue
                    
                    # 排除已知的社交媒体或目录网站
                    excluded_link_domains = ['facebook.com', 'linkedin.com', 'yelp.com', 'instagram.com', 'twitter.com', 'youtube.com',
                                            'zhihu.com', 
                                            'baidu.com',
                                            'weibo.com',
                                            'bilibili.com',
                                            'sohu.com',
                                            '163.com'
                                             ]
                    if any(excluded in domain for excluded in excluded_link_domains):
                        continue

                    # 计算相似度分数
                    similarity_score = get_similarity(cleaned_company_name, re.sub(r'[^a-z0-9]', '', domain.split('.')[0]))
                    candidate_links.append({"url": real_link, "score": similarity_score})
                
                if not candidate_links:
                    print("... Bing 搜索结果中未找到合适的非社交媒体链接。")
                    return None, None

                # 2. 按相似度排序，选出最好的几个
                candidate_links.sort(key=lambda x: x['score'], reverse=True)
                print(f"... 候选官网链接排序: {candidate_links}")
                
                # 3. 依次访问最相关的链接，直到找到邮箱
                for link_info in candidate_links[:visit_best_n]:
                    target_url = link_info['url']
                    print(f"  -> 正在访问最相关的链接 (相似度: {link_info['score']:.2f}): {target_url}")
                    
                    # 使用 crawl_subpages 及其评分机制来找这个网站的最佳邮箱
                    # 注意：这里我们只关心这个网站本身，所以不递归太深
                    all_emails_from_site = await self.crawl_subpages(target_url, session, max_depth=1)
                    if not all_emails_from_site:
                        continue
                    
                    # 对找到的邮箱进行评分，选出最好的那个
                    scored_emails = []
                    for email, source_url, has_phone in all_emails_from_site:
                        score = self.score_email(email, source_url, has_phone)
                        if score > -900:
                            scored_emails.append((email, score))
                    
                    if scored_emails:
                        scored_emails.sort(key=lambda x: x[1], reverse=True)
                        best_email, _ = scored_emails[0]
                        # 找到了！返回邮箱和这个链接作为官网
                        return best_email, target_url
            
            return None, None # 遍历完所有最佳链接都没找到

        except Exception as e:
            print(f"❌ Bing 搜索选择流程异常: {type(e).__name__} - {e}")
            return None, None


    # 在 EmailFetcher 类中，替换此方法
    async def fetch_email(self):
        """
        完整版 fetch_email 流程:
        根据是否存在 self.website，自动选择执行路径。

        路径一 (有官网):
        1. 并发执行所有常规抓取策略 (网页、JS、JSON、Sitemap)。
        2. 如果常规策略找不到，则启动智能搜索 (search_with_bing_and_select) 作为最终兜底。
        3. 对所有收集到的候选邮箱进行去重、评分和排序。
        4. 选择分数最高的邮箱，并通过 emailAndWebsiteFound 信号发送结果。

        路径二 (无官网):
        1. 直接进入“仅搜索”模式。
        2. 使用公司名和地址构造精确查询。
        3. 调用智能搜索方法 (search_with_bing_and_select) 寻找最佳官网和邮箱。
        4. 通过 emailAndWebsiteFound 信号发送结果。
        """
        try:
            # ===================================================================
            # 路径一：有明确官网，执行常规流程 + 智能搜索兜底
            # ===================================================================
            if self.website:
                all_candidates = [] # 用于存储所有找到的 (email, source_url, has_phone) 元组
                async with aiohttp.ClientSession() as session:
                    loop = asyncio.get_event_loop()

                    async def task_wrapper(coro):
                        try:
                            return await coro
                        except Exception as e:
                            # print(f"❌ 任务异常: {type(e).__name__} - {e}")
                            return []

                    # 1. 并发执行所有主要任务
                    tasks = [
                        loop.create_task(task_wrapper(self.crawl_subpages(self.website, session))),
                        loop.create_task(task_wrapper(self.fetch_js_for_emails(self.website, session))),
                        loop.create_task(task_wrapper(self.fetch_json_for_emails(self.website, session))),
                        # loop.create_task(task_wrapper(self.fetch_sitemap_for_emails(self.website, session))),
                    ]
                    
                    results = await asyncio.gather(*tasks)

                    # 2. 收集所有常规任务的结果
                    for result_list in results:
                        if result_list:
                            all_candidates.extend(result_list)
                    
                    # 3. 如果常规方法没找到，也用 Bing 智能搜索作为最终兜底
                    if not all_candidates:
                        print(f"ℹ️ 官网 {self.website} 未直接找到邮箱，启动 Bing 搜索兜底...")
                        
                        # --- 【修改点 1】构造更精确的兜底搜索查询 ---
                        query_parts = []
                        if self.company_name:
                            # query_parts.append(f'"{self.company_name}"') # 使用引号进行精确匹配
                            query_parts.append(self.company_name) 
                        if self.address:
                            # query_parts.append(f'"{self.address}"') # 包含完整地址
                            query_parts.append(self.address) 
                        if self.phone:
                            # query_parts.append(f'"{self.phone}"') # 如果有电话，也加上
                            query_parts.append(self.phone)
                        # query_parts.append("email")
                        query = " ".join(query_parts)
                        # --- 查询构造结束 ---
                        
                        found_email, found_website = await self.search_with_bing_and_select(query, session)
                        if found_email and found_website:
                            print(f"🏆 [兜底搜索] 成功找到: {found_email} @ {found_website}")
                            # 直接发射信号并返回，因为这是最高精度的兜底结果
                            self.signals.emailAndWebsiteFound.emit(found_email, found_website, self.row)
                            return
                        else:
                             print(f"❌ [兜底搜索] 未能通过搜索找到邮箱")
                
                # 4. 对常规方法找到的候选邮箱进行去重与评分
                if not all_candidates:
                    print(f"❌ 未在官网 {self.website} 及所有方法中找到邮箱")
                    self.signals.emailAndWebsiteFound.emit("N/A", self.website, self.row) # 【【【 修改这里 】】】
                    return

                # 对候选邮箱去重 (基于邮箱地址本身)
                unique_emails = {}
                for email, source_url, has_phone in all_candidates:
                    if email not in unique_emails:
                        unique_emails[email] = {"source_urls": [source_url], "has_phone": has_phone}
                    else:
                        unique_emails[email]["source_urls"].append(source_url)
                        if has_phone:
                            unique_emails[email]["has_phone"] = True

                # 为每个独立邮箱评分
                scored_emails = []
                for email, properties in unique_emails.items():
                    score = self.score_email(email, properties["source_urls"][0], properties["has_phone"])
                    if score > -900: # 过滤掉被直接淘汰的
                        scored_emails.append((email, score))
                
                # 5. 排序并选择最优结果
                if not scored_emails:
                    print(f"❌ 所有候选邮箱评分过低或无效: {self.website}")
                    self.emailAndWebsiteFound.emit("N/A", self.website, self.row)
                    return

                scored_emails.sort(key=lambda x: x[1], reverse=True)
                best_email, best_score = scored_emails[0]
                
                print(f"🏆 [常规流程] 最终选择: {best_email} (分数: {best_score})")
                self.signals.emailAndWebsiteFound.emit(best_email, self.website, self.row)
                return

            # ===================================================================
            # 路径二：没有官网，直接执行“仅搜索”流程
            # ===================================================================
            else:
                print(f"🚀 进入仅搜索模式，目标: '{self.company_name}'")
                async with aiohttp.ClientSession() as session:
                    
                    # --- 【修改点 2】构造更精确的“仅搜索”模式查询 ---
                    query_parts = []
                    if self.company_name:
                        # query_parts.append(f'"{self.company_name}"') # 使用引号进行精确匹配
                        query_parts.append(self.company_name) # 去掉引号
                    if self.address:
                        # query_parts.append(f'"{self.address}"') # 包含完整地址
                        query_parts.append(self.address) # 去掉引号
                    if self.phone:
                        # query_parts.append(f'"{self.phone}"') # 如果有电话，也加上
                        query_parts.append(self.phone) # 去掉引号
                    # query_parts.append("email") # 保留关键词以提高找到邮箱的概率
                    query = " ".join(query_parts)
                    # --- 查询构造结束 ---
                    
                    # 2. 调用增强版的 Bing 搜索，它会返回(邮箱, 官网URL)
                    found_email, found_website = await self.search_with_bing_and_select(query, session)

                    # 3. 发射信号
                    if found_email and found_website:
                        print(f"🏆 [搜索模式] 成功找到: {found_email} @ {found_website}")
                        self.signals.emailAndWebsiteFound.emit(found_email, found_website, self.row)
                    else:
                        print(f"❌ [搜索模式] 未能通过搜索找到邮箱")
                        self.signals.emailAndWebsiteFound.emit("N/A (Searched)", "", self.row)
        
        except Exception as e:
            print(f"❌ 提取邮箱主流程失败 ({self.company_name}): {e}")
            self.signals.emailAndWebsiteFound.emit(f"Error: {e}", "", self.row)



    @pyqtSlot() # 明确这是一个槽函数
    def run(self):
        """
        线程池会调用这个run方法来执行任务。
        """
        try:
            # 这里的逻辑和原来 EmailFetcher.run() 的一样
            self.playwright_manager.run_coroutine(self.fetch_email())
        except Exception as e:
            print(f"❌ EmailFetcherWorker 运行时发生错误: {e}")
            traceback.print_exc()
        finally:
            # 任务完成后，必须发射 finished 信号
            self.signals.finished.emit()
            




class DBManager:
    """
    一个用于管理SQLite数据库的单例类。
    负责数据库的连接、表的创建以及数据的增删改查。
    """
    _instance = None

    def __new__(cls, db_name="scraper_data.db"):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance.db_name = db_name
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
        """创建一个用于存储公司信息的数据表（如果不存在）"""
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
                    email TEXT,
                    website TEXT,
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
        sql = ''' INSERT INTO companies(name, address, phone, website, category, hours, rating, review_count, source_link)
                  VALUES(?,?,?,?,?,?,?,?,?) '''
        
        # 从字典中提取数据
        company = (
            company_data.get('name'),
            company_data.get('address'),
            company_data.get('phone'),
            company_data.get('website'),
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

    def __init__(self):
        super().__init__()
        self.db_manager = None

    def run(self):
        """线程启动后，创建DBManager实例并进入事件循环"""
        self.db_manager = DBManager()
        # connect signals to slots within this thread
        self.insert_request.connect(self.handle_insert)
        self.update_request.connect(self.handle_update)
        self.exec_() # 开启线程的事件循环，等待信号

    def handle_insert(self, data):
        if self.db_manager:
            self.db_manager.insert_company(data)

    def handle_update(self, name, address, email, website):
        if self.db_manager:
            self.db_manager.update_email_and_website(name, address, email, website)

    def get_all_companies_blocking(self):
        """提供一个同步方法来获取数据，仅用于导出等非高频操作"""
        if self.db_manager:
            return self.db_manager.get_all_companies()
        return []

    def stop(self):
        """停止线程的事件循环"""
        if self.db_manager:
            self.db_manager.close()
        self.quit()
        self.wait()



def resource_path(relative_path):
    """
    获取资源的绝对路径，兼容开发模式和 PyInstaller 打包后的模式。
    """
    try:
        # PyInstaller 创建的临时文件夹路径
        base_path = sys._MEIPASS
    except Exception:
        # 不在 PyInstaller 打包程序中，正常运行
        base_path = os.path.abspath(".") # 获取当前工作目录

    return os.path.join(base_path, relative_path)




# 单例浏览器管理器
class PlaywrightManager:
    """
    一个线程安全的管理器，用于维护单个Playwright浏览器实例。
    该管理器在自己的后台线程中运行一个专用的asyncio事件循环。
    """
    def __init__(self):
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None
        self._loop: asyncio.AbstractEventLoop | None = None
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._is_running = threading.Event() # 用于确认后台循环是否已启动

        self._thread.start()
        self._is_running.wait() # 等待后台线程和事件循环准备就绪

    def _run_loop(self):
        """后台线程的入口点，创建并运行事件循环。"""
        asyncio.run(self._main())

    async def _main(self):
        """设置事件循环并保持运行。"""
        self._loop = asyncio.get_running_loop()
        self._is_running.set() # 通知主线程，循环已启动
        
        # 保持事件循环持续运行，直到shutdown被调用
        shutdown_future = self._loop.create_future()
        await shutdown_future

    def run_coroutine(self, coro):
        """
        在管理器的事件循环中安全地运行一个协程，并阻塞等待结果。
        这是从其他线程（如QThread）与Playwright交互的唯一方式。
        """
        if not self._loop:
            raise RuntimeError("PlaywrightManager event loop is not running.")
        
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        
        try:
            # 【【【修改点】】】 为 result() 调用添加超时（例如60秒）
            # 如果异步任务在60秒内没有完成，它将引发 TimeoutError 异常
            return future.result(timeout=60)
        except Exception as e:
            # 捕获超时或其他从异步任务传来的异常
            print(f"❌ 异步任务执行失败或超时: {e}")
            # 取消任务，防止它继续在后台运行
            future.cancel()
            return None # 返回一个默认值，避免上层代码出错
        

    async def _initialize_internal(self):
        """内部初始化方法，必须在管理器的事件循环中调用。"""
        if self._browser and self._browser.is_connected():
            return # 如果已经初始化，则不执行任何操作

        print("🚀 正在启动 Playwright 浏览器实例...")
        try:
            self._playwright = await async_playwright().start()
            self._browser = await self._playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            print("✅ Playwright 浏览器实例启动成功。")
        except Exception as e:
            print(f"❌ 启动 Playwright 失败: {e}")
            # 可以在这里处理初始化失败的情况
            self._browser = None

    def initialize(self):
        if not self._loop or not self._loop.is_running():
            self._loop = asyncio.new_event_loop()
            self._loop_thread = threading.Thread(target=self._start_event_loop, daemon=True)
            self._loop_thread.start()
        # 非阻塞提交，不等待结果
        asyncio.run_coroutine_threadsafe(self._initialize_internal(), self._loop)

    async def _shutdown_internal(self):
        """内部关闭方法，必须在管理器的事件循环中调用。"""
        if self._browser and self._browser.is_connected():
            print("🌙 正在关闭 Playwright 浏览器实例...")
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        print("✅ Playwright 已安全关闭。")
        
        # 停止事件循环
        for task in asyncio.all_tasks(self._loop):
            if task.get_coro().__name__ == '_main':
                task.get_coro().send(None) # 结束 _main 协程中的等待
                break

    def shutdown(self):
        """公开的关闭方法，从任何线程调用。"""
        if self._loop and self._loop.is_running():
            # 提交关闭任务，但不等待结果，因为循环即将停止
            asyncio.run_coroutine_threadsafe(self._shutdown_internal(), self._loop)

    async def get_page_content(self, url: str) -> str | None:
        """
        获取单个页面的内容。这个方法本身就是协程，需要通过 run_coroutine 调用。
        【【【新增】】】 使用 asyncio.wait_for 增加内部超时保护。
        """
        if not self._browser or not self._browser.is_connected():
            print("⚠️ Playwright 未初始化，无法获取页面。")
            await self._initialize_internal()
            if not self._browser:
                 return None

        # 【【【修改点】】】
        try:
            # 将核心逻辑包裹在 asyncio.wait_for 中，设置一个比外部调用更短的超时
            async def perform_get_content():
                page = await self._browser.new_page()
                print(f" puppeteer 正在通过浏览器访问: {url}")
                try:
                    # 页面导航和内容获取的总时间不应超过30秒
                    await page.goto(url, timeout=20000, wait_until="domcontentloaded") # 导航超时20秒
                    content = await page.content() # 获取内容
                    return content
                except Exception as e:
                    print(f"❌ Playwright 访问页面失败 ({url}): {e}")
                    return None
                finally:
                    await page.close()

            # 为整个操作设置一个30秒的超时
            return await asyncio.wait_for(perform_get_content(), timeout=30.0)

        except asyncio.TimeoutError:
            print(f"❌ Playwright 操作总超时 ({url})")
            return None
        except Exception as e:
            # 捕获其他可能的异常
            print(f"❌ Playwright get_page_content 发生未知错误: {e}")
            return None


class AIStatusChecker(QThread):
    """在后台检查AI状态的线程"""
    status_ready = pyqtSignal(dict) # 定义一个信号，完成后发射结果

    def __init__(self, user_id):
        super().__init__()
        self.user_id = user_id
        self.api_url = "https://google-maps-backend-master.netlify.app/.netlify/functions/check-ai-status"

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


# =====================================================================
# 登录对话框类 (美化版 - 更具艺术感)
# =====================================================================
class LoginDialog(QDialog):
    # 新增常量：设备码存储文件路径 和 后端API基地址
    USER_CONFIG_FILE = "user_config.json"
    BACKEND_API_BASE_URL = "https://google-maps-backend-master.netlify.app/.netlify/functions/receivingClient"
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("安全登录") # 再次统一标题
        icon_path = resource_path(r"img/icon/谷歌地图.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.resize(800, 480) # 进一步增大窗口尺寸，黄金比例感觉
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
                with open(self.USER_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"⚠️ 配置文件 {self.USER_CONFIG_FILE} 格式错误，将创建新文件。")
                return {} # 返回一个空的配置字典
        return {}
    
    def _save_config_data(self, data):
        """将完整的配置信息保存到本地文件"""
        try:
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
        
        # 更新或创建用户信息
        config["users"][username] = {
            "password": password_encoded,
            "device_id": device_id
        }
        
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
            tuple: (bool success, str message, str user_id or None)
        """
        url = self.BACKEND_API_BASE_URL
        print(f"发送请求到: {url}，数据: {data}")
        try:
            response = requests.post(url, json=data, timeout=10)

            if response.status_code == 200:
                response_json = response.json()
                print(response_json)  # 调试用，可以看到完整的响应

                if response_json.get("success"):
                    user_info = response_json.get("user", {})
                    backend_device_code = user_info.get("deviceCode")
                    username = data.get("username")
                    user_id = user_info.get("id")  # 新增：提取 user_id（假设后端返回 id）

                    # if username and backend_device_code:
                    #     self._set_device_id_for_user(username, backend_device_code)
                    
                    # --- 新增到期时间判断 ---
                    expiry_at_str = user_info.get("expiryAt")
                    if expiry_at_str:
                        try:
                            # 将ISO 8601字符串转换为datetime对象
                            # 注意：Python 3.7+ 支持 fromisoformat
                            # 对于较旧版本，可能需要使用 datetime.strptime(expiry_at_str, "%Y-%m-%dT%H:%M:%S%z")
                            from datetime import datetime, timezone
                            
                            # 解析时区信息，如果时区是+00:00，则可以转换为UTC aware datetime
                            if expiry_at_str.endswith("Z"):  # 处理Z结尾的UTC时间
                                expiry_date = datetime.fromisoformat(expiry_at_str[:-1]).replace(tzinfo=timezone.utc)
                            else:  # 处理带偏移量的ISO时间
                                expiry_date = datetime.fromisoformat(expiry_at_str)

                            current_time = datetime.now(timezone.utc)  # 获取当前UTC时间

                            if current_time > expiry_date:
                                return False, "账号已过期，请联系管理员。", None
                        except ValueError as e:
                            print(f"日期解析错误: {e}")
                            return False, "账号到期时间格式不正确，请联系管理员。", None
                    else:
                        return False, "账号到期时间信息缺失，请联系管理员。", None
                    # --- 结束到期时间判断 ---

                    # --- 新增状态判断 ---
                    status = user_info.get("status")
                    if status != "active":
                        return False, f"账号状态为 '{status}'，无法登录，请联系管理员。", None
                    # --- 结束状态判断 ---

                    # 如果登录成功，并且后端返回了新的设备码（初次登录），则更新本地存储
                    if "user" in response_json and "deviceCode" in response_json["user"]:
                        backend_device_code = response_json["user"]["deviceCode"]
                        username = data.get("username")
                        # if username and self._get_device_id_for_user(username) != backend_device_code:
                        #     self._set_device_id_for_user(username, backend_device_code)
                        #     print(f"本地设备码已更新为后端返回的: {backend_device_code}")

                    return True, response_json.get("message", "登录成功。"), user_id  # 新增 user_id
                else:
                    return False, response_json.get("message", "登录失败。"), None  # 返回 None 作为 user_id
            else:
                # 处理非200状态码的错误
                error_response = response.json()
                return False, error_response.get("message", f"后端请求失败: HTTP {response.status_code}"), None

        except requests.exceptions.Timeout:
            print(f"❌ 后端请求超时: {url}")
            return False, "网络请求超时，请检查网络连接。", None
        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到后端: {url}")
            return False, "无法连接到服务器，请检查后端服务是否运行。", None
        except requests.exceptions.RequestException as e:
            print(f"❌ 后端请求失败: {e}")
            return False, f"网络错误或后端服务不可用: {e}", None
        except json.JSONDecodeError:
            print(f"❌ 后端返回非JSON格式响应: {response.text}")
            return False, "服务器返回无效响应。", None
        except Exception as e:
            print(f"❌ 发送后端请求发生未知错误: {e}")
            return False, f"发生内部错误: {e}", None

    


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
        success, message, user_id = self._send_to_backend(payload)

        if success:
            if user_id:
                self.logged_in_user_id = user_id  # 保存 user_id
                self._save_user_credentials_and_device_id(username, password, device_id_to_send)
                # QMessageBox.information(self, "登录成功", message)
                self.accept()
            else:
                self.error_label.setText("无法获取用户ID，请联系管理员。")
                self.error_label.show()
                self.shake_window()
        else:
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


# 屏蔽控制台输出
class SilentWebEnginePage(QWebEnginePage):
    def javaScriptConsoleMessage(self, level, message, lineNumber, sourceID):
        # 屏蔽输出，可自定义是否打印
        pass

def deobfuscate_text(text):
    # 1. 替换常见的混淆词
    text = text.replace('[at]', '@').replace('[dot]', '.')
    text = text.replace('(at)', '@').replace('(dot)', '.')
    
    # 2. 移除 "nospam" 或 "removethis" 等标记
    text = re.sub(r'(\.|\s)nospam(\.|\s)', '.', text, flags=re.IGNORECASE)
    text = re.sub(r'\.removethis', '', text, flags=re.IGNORECASE)
    
    # 3. 处理HTML实体编码 (例如 &#64; -> @)
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
        # self.api_url = "https://google-maps-backend-master.netlify.app/.netlify/functions/gemini-enrich-data"
        # self.api_url = "https://google-maps-backend-master.netlify.app/.netlify/functions/gemini-enrich-data"
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



class GoogleMapsApp(QWidget):
    # 定义AI批处理大小
    AI_BATCH_SIZE = 1 

    # 页面设计
    def __init__(self, user_id=None):
        super().__init__()
        self.playwright_manager = PlaywrightManager()
        print("正在初始化 Playwright 管理器...")
        # self.browser = self.playwright_manager.initialize()
        print("Playwright 管理器初始化完成。")
        
        self.wait_start_time = None

        # 用于记录单个商家处理的开始时间
        self.item_processing_start_time = None
        # 单个商家的最大处理时间（秒）
        self.ITEM_PROCESSING_TIMEOUT = 30
        # 标记当前是否有商家正在处理中
        self.is_currently_processing_item = False

        self.last_detail_title = ""

        self.is_paused_for_captcha = False # 用于标记是否因人机验证而暂停

        self.load_timeout_timer = QTimer(self)
        self.load_timeout_timer.setSingleShot(True)  # 设置为单次触发
        self.load_timeout_timer.timeout.connect(self.on_load_timeout)

        # self.db_manager = DBManager()

        self.thread_pool = QThreadPool.globalInstance()
        # 设置一个合理的并发线程数，例如CPU核心数的2倍
        self.thread_pool.setMaxThreadCount(os.cpu_count() * 2) 

        print(f"全局线程池最大线程数: {self.thread_pool.maxThreadCount()}")

        self.active_worker_count = 0

        # 创建并启动数据库工作线程
        self.db_worker = DatabaseWorker()
        self.db_worker.start()

        # self.username = username
        self.user_id = user_id
        self.is_loading = False
        self.user_triggered_navigation = False
        self.setWindowTitle("QWebEngineView Google Maps 自动采集（增强版）")
        self.setWindowIcon(QIcon(resource_path("img/icon/谷歌地图.ico")))

        # 存储所有运行中的 EmailFetcher 线程
        self.email_fetchers = []
        
        # 存储AI线程
        self.ai_fetchers = [] 

        # 缓存待AI处理的公司信息
        self.ai_batch_queue = []

        # 提取状态次数
        self.hrefs_last_count = 0

        # 跟踪地图抓取是否完成
        self.map_scraping_finished = False

        self.resize(1300, 900)

        # 创建一个集合，用作缓存，快速检查数据是否已处理
        self.processed_items_cache = set()

        main_layout = QVBoxLayout(self)

        self.ui_update_queue = []
        self.cell_update_queue = []
        # 用于缓存待更新的单元格信息
        self.ui_update_timer = QTimer(self)
        # 创建一个定时器，每500ms触发一次
        self.ui_update_timer.timeout.connect(self._process_ui_update_queue)
        self.ui_update_timer.start(800) 

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
            font-size: 13px;
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
            font-size: 16px;
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
        self.country_combo.setStyleSheet(input_style)
        search_layout.addWidget(QLabel("国家筛选:"))
        search_layout.addWidget(self.country_combo)

        self.region_combo = QComboBox()
        self.region_combo.setStyleSheet(input_style)
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
        self.progress_bar.hide() # 默认隐藏
        main_layout.addWidget(self.progress_bar)

        # 浏览器区域
        self.browser = QWebEngineView()
        self.browser.setPage(SilentWebEnginePage(self.browser))
        main_layout.addWidget(self.browser, stretch=3)


        # 🔧 启用开发者工具
        # self.devtools = QWebEngineView()
        # self.browser.page().setDevToolsPage(self.devtools.page())
        # self.devtools.setWindowTitle("开发者工具")
        # self.devtools.resize(1200, 800)
        # self.devtools.show()

        # 添加loading遮罩层
        self.loading_label = QLabel("正在加载页面，请稍候...", self)
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("""
            background-color: rgba(255, 255, 255, 180);
            color: #4CAF50;
            font-size: 18px;
            font-weight: bold;
        """)
        self.loading_label.resize(self.browser.size())
        self.loading_label.hide()  # 默认隐藏


        # 添加倒计时遮罩层
        self.countdown_label = QLabel(self)
        self.countdown_label.setAlignment(Qt.AlignCenter)
        self.countdown_label.setStyleSheet("""
            background-color: rgba(0, 0, 0, 160);
            color: #FFC107;
            font-size: 24px;
            font-weight: bold;
            border-radius: 15px;
        """)
        self.countdown_label.hide()  # 默认隐藏

        # 用于倒计时的计时器和变量
        # self.countdown_timer = QTimer(self)
        # self.countdown_timer.timeout.connect(self.update_countdown)
        # self.countdown_seconds = 0

        # 绑定加载开始和结束信号
        self.browser.loadStarted.connect(self.on_load_started)
        self.browser.loadFinished.connect(self.on_load_finished)


        # 结果表格
        self.table = QTableWidget()
        self.table.setColumnCount(10)
        self.table.setHorizontalHeaderLabels([
            "名称", "地址", "电话", "邮箱", "官网","类别", "营业时间", "评分", "评价数", "来源链接"
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
        main_layout.addWidget(self.table, stretch=2)

        # 导出按钮
        self.export_btn = QPushButton("导出结果 (CSV)")
        self.export_btn.clicked.connect(self.export_results)
        self.export_btn.setStyleSheet(btn_style)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        main_layout.addWidget(self.export_btn)

        # 初始化变量
        self.keywords = []
        self.current_keyword_index = 0
        self.is_searching = False

        # 初始化当前加载类型
        self._current_load_type = "initial_map_load"

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

        # 先打开Google Maps首页
        self.user_triggered_navigation = True
        self.browser.load(QUrl("https://www.google.com/maps"))

        self.check_ai_status()

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
    def start_search_batch(self):
        if self.is_paused_for_captcha:
            QMessageBox.information(self, "提示", "程序当前已暂停，请先恢复任务。")
            return


        if self.is_searching:
            QMessageBox.warning(self, "提示", "当前正在搜索，请稍候。")
            return
        
        self.map_scraping_finished = False

        # 每次开始新的搜索时，清空去重缓存
        self.processed_items_cache.clear()

        # 先清空表格
        self.table.setRowCount(0)

        # 如果没有导入关键词，则使用输入框中的
        if not self.keywords:
            kw = self.keyword_input.text().strip()
            if kw:
                self.keywords = [kw]
            else:
                QMessageBox.warning(self, "提示", "请输入关键词或导入关键词文件。")
                return
        
        # ===== 新增代码：重置并显示进度条 =====
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("准备开始...")
        self.progress_bar.show()
        # ====================================


        self.current_keyword_index = 0
        self.search_next_keyword()


    # MODIFIED: 替换此方法
    def search_next_keyword(self):
        if self.current_keyword_index >= len(self.keywords):
            # self.is_searching = False
            # self.load_all_saved_results()
            # QMessageBox.information(self, "完成", "所有关键词搜索完成。")

            # ===== 新增代码：所有任务完成，隐藏进度条 =====
            # self.progress_bar.hide()
            # ======================================== 

            print("🏁 所有关键词的地图抓取流程已完成，等待后台邮箱任务结束...")
            self.map_scraping_finished = True
            self._check_if_all_work_is_done() # 检查是否可以立即结束

            return

        self.is_searching = True
        self.current_keyword = self.keywords[self.current_keyword_index] # 保存当前关键词
        country = self.country_combo.currentText()
        region = self.region_combo.currentText()
        
        # 准备当前关键词需要搜索的所有地区坐标
        self.search_coords = []
        if region == "全部地区":
            coords_list = self.get_region_bounds(country, region)
            if coords_list:
                for coord in coords_list:
                    lat = coord.get("latitude")
                    lon = coord.get("longitude")
                    if lat is not None and lon is not None:
                        self.search_coords.append((lat, lon))
        else:
            bounds_list = self.get_region_bounds(country, region)
            if bounds_list:
                for bounds in bounds_list:
                    lat = (bounds.get("latitude_min", -90) + bounds.get("latitude_max", 90)) / 2
                    lon = (bounds.get("longitude_min", -180) + bounds.get("longitude_max", 180)) / 2
                    self.search_coords.append((lat, lon))


        # ===== 新增代码：设置进度条最大值和初始值 =====
        total_regions = len(self.search_coords)
        if total_regions > 0:
            self.progress_bar.setMaximum(total_regions)
            self.progress_bar.setValue(0)
            self.progress_bar.setFormat(f"关键词: {self.current_keyword} - %v / %m 个地区（数据已去重）")
        else:
            # 如果没有地区，也要更新提示
            self.progress_bar.setFormat(f"关键词: {self.current_keyword} - 无有效地区")
        # ==========================================


        if not self.search_coords:
            QMessageBox.warning(self, "错误", f"关键词 '{self.current_keyword}' 无法获取任何地区经纬度，已跳过。")
            # 移动到下一个关键词
            self.current_keyword_index += 1
            QTimer.singleShot(100, self.search_next_keyword)
            return

        # 初始化当前关键词的地区索引和结果存储
        self.current_region_index = 0
        # self.current_results = []
        
        # 开始搜索这个关键词下的第一个地区
        self.search_next_region()

    # ADDED: 添加此新方法
    def search_next_region(self):
        # 检查当前关键词的所有地区是否已搜索完毕
        if self.current_region_index >= len(self.search_coords):
            # 所有地区搜索完成，保存当前关键词的结果
            # if self.current_results:
            #     self.save_results_to_json(self.current_results, self.current_keyword)
            
            # 清空当前结果并准备下一个关键词
            self.current_results = []
            self.current_keyword_index += 1
            self.search_next_keyword() # 开始下一个关键词
            return
        

        # ===== 新增代码：更新进度条的值 =====
        # 使用 current_region_index 作为当前进度（0-based）
        # 显示时可以用 %v 来表示当前值
        self.progress_bar.setValue(self.current_region_index)



        # 获取当前要搜索的地区坐标
        latitude, longitude = self.search_coords[self.current_region_index]
        
        # 获取其他参数
        kw = self.current_keyword
        country = self.country_combo.currentText()
        region = self.region_combo.currentText() # 这里是 "全部地区" 或具体地区
        industry = self.industry_combo.currentText()

        print(f"\n🚀 开始搜索: [关键词: {kw}] -> [地区 {self.current_region_index + 1}/{len(self.search_coords)}] at ({latitude}, {longitude})")


        # 记录当前加载类型，以便在 on_load_finished 中正确分发
        self._current_load_type = "batch_search"
        self._batch_search_info = {
            "keyword": kw,
            "country": country,
            "region": region,
            "industry": industry,
            "latitude": latitude,
            "longitude": longitude
        }

        # 构造搜索字符串
        search_parts = [kw]
        if industry and industry != "全部行业":
            search_parts.append(industry)

        if country and country != "全部国家":  # 防止用户选择“全部国家”
            search_parts.append(country)
        
        search_str = " ".join(search_parts).strip()
        encoded = quote(search_str)
        url = f"https://www.google.com/maps/search/{encoded}/@{latitude},{longitude},15z"
        print(f"搜索链接: {url}")

        LOAD_TIMEOUT_MS = 45000 
        self.load_timeout_timer.start(LOAD_TIMEOUT_MS)
        
        self.user_triggered_navigation = True # 触发 loading 动画
        self.browser.load(QUrl(url))




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



    # 输入关键词进行搜索
    def on_load_finished_for_batch(self, ok, keyword, country, region, industry, latitude, longitude):
        """
        修改后的函数，实现了“或者”判断逻辑。
        """
        # 根据您的“或者”逻辑，无论ok是True还是False，我们都必须进入下一步——检查元素。
        # 因为只有当两个条件（浏览器加载失败 AND 页面元素找不到）都失败时，整个流程才算失败。
        # 因此，wait_for_search_results 函数将成为唯一的失败判断点。

        if ok:
            # 这是“或者”逻辑的第一部分：浏览器报告成功。
            # 我们打印一条日志，然后继续去检查元素。
            print("浏览器报告加载成功(ok=True)，进入元素检查阶段...")
        else:
            # 这是“或者”逻辑的第二部分的前奏：浏览器报告失败。
            # 但我们不立即放弃，而是打印提示，然后继续去检查元素，作为最后的补救措施。
            print("浏览器报告加载失败(ok=False)，但仍将尝试检查页面元素...")

        # 无论ok为何值，我们都调用 wait_for_search_results。
        # 这个函数内部有自己的超时失败逻辑，它将成为最终的、唯一的“审判官”。
        # 如果它找到了 hfpxzc 元素（即使 ok 是 False），流程也会继续。
        # 只有当它超时后也找不到元素，才会触发“跳到下一个地区”的操作。
        self.wait_for_search_results()

    # 在开始等待时，记录时间
    def start_search_for_region(self, region):
        # ...
        self.current_wait_start_time = time.time() # 记录开始等待的时间
        self.wait_for_search_results()



    # 等待元素出现
    def wait_for_search_results(self, retries=0, max_retries=10):
        # 【修改点1: 将最大等待时间与重试次数解耦】
        MAX_WAIT_SECONDS = 15 # 定义一个总的超时秒数
        CHECK_INTERVAL_MS = 1500  # 每次检测间隔

        # 如果是第一次重试，就记录开始时间并设置UI
        if retries == 0:
            self.wait_start_time = time.time()
            
            # 设置并显示倒计时遮罩
            self.countdown_label.setText(f"等待搜索结果... ({MAX_WAIT_SECONDS}s)")
            browser_pos = self.browser.mapTo(self, self.browser.rect().topLeft())
            self.countdown_label.setGeometry(browser_pos.x(), browser_pos.y(), self.browser.width(), self.browser.height())
            self.countdown_label.raise_()
            self.countdown_label.show()

        # 检查总等待时间是否超过了硬性上限
        elapsed_time = time.time() - self.wait_start_time
        if elapsed_time > MAX_WAIT_SECONDS:
            print(f"❌ 等待超时（超过 {MAX_WAIT_SECONDS} 秒），跳到下一个地区")
            self.countdown_label.hide()
            self.current_region_index += 1
            QTimer.singleShot(1000, self.search_next_region)
            return

        # 【修改点2: 合并倒计时UI更新到主循环中】
        remaining_seconds = int(MAX_WAIT_SECONDS - elapsed_time)
        self.countdown_label.setText(f"等待搜索结果... ({remaining_seconds}s)")

        # JavaScript检测逻辑保持不变
        check_js = """
        (function() {
            if (document.querySelector('iframe[src*="recaptcha"]')) { return 'captcha'; }
            if (document.querySelector('a.hfpxzc, a[href^="/maps/place/"], div[role="article"]')) { return 'found'; }
            return 'not_found';
        })();
        """

        def handle_check(result):
            if result == 'found':
                print("✅ 检测到搜索结果元素，开始提取。")
                self.countdown_label.hide()
                QTimer.singleShot(2000, self.extract_results_for_batch)

            elif result == 'captcha':
                print("🚨 检测到人机验证！已暂停自动抓取。")
                self.countdown_label.hide()
                self.pause_for_captcha() 

            # 检查是否还有重试机会（这里只是为了打印日志，真正的超时判断在上面）
            elif retries < max_retries:
                print(f"⌛ 未找到结果，继续等待... (已等待 {int(elapsed_time)}s / {MAX_WAIT_SECONDS}s)")
                # 【修改点3: 延长重试间隔】
                # 将间隔从1000ms延长到1500ms，给UI线程更多喘息时间
                QTimer.singleShot(1500, lambda: self.wait_for_search_results(retries + 1, max_retries))
                
            else: # 如果是重试次数用尽（作为备用超时机制）
                print(f"❌ 达到最大重试次数({max_retries})，跳到下一个地区")
                self.countdown_label.hide()
                self.current_region_index += 1
                QTimer.singleShot(1000, self.search_next_region)

        self.browser.page().runJavaScript(check_js, handle_check)


    def extract_results_for_batch(self):
        print("✅ 检测到结果项，开始滚动并实时提取链接")
        # self.current_results_batch = []  # 存储当前地区的搜索结果
        self.start_scroll_and_extract()

    # =====================================================================
    # 【全新】滚动与提取逻辑 (替换旧的 start_scroll_and_extract 到 after_detail_wait)
    # =====================================================================
    def start_scroll_and_extract(self):
        """
        启动新的、更健壮的滚动提取流程。
        """
        print("✅ 检测到结果项，启动新版滚动提取流程...")
        self.current_index = 0  # 当前要处理的元素索引
        self._scroll_and_extract_loop(previous_count=0)

    def _scroll_and_extract_loop(self, previous_count):
        """
        滚动和提取的核心循环。
        """
        js_get_count = "document.querySelectorAll('a.hfpxzc').length;"
        self.browser.page().runJavaScript(js_get_count, 
            lambda count: self._handle_count_check(count, previous_count))

    def _handle_count_check(self, current_count, previous_count):
        """处理元素数量检查的结果。"""
        if current_count == previous_count and previous_count > 0:
            print("🛑 滚动到底部后未发现新结果，当前地区抓取完成。")
            self.finish_region_extraction()
            return

        print(f"🔄 当前列表有 {current_count} 个结果，上次处理到 {self.current_index}。")
        if self.current_index < current_count:
            self._process_next_item()
        else:
            self._scroll_and_wait(current_count)

    def _process_next_item(self):
        """
        处理下一个商家，并启动“看门狗”定时器。
        【【【修改版】】】
        """
        js_get_count = "document.querySelectorAll('a.hfpxzc').length;"
        
        def on_count_received(count):
            if self.current_index < count:
                print(f"▶️ 开始处理第 {self.current_index + 1} 个商家...")
                # 【关键】设置状态
                self.is_currently_processing_item = True
                
                # 【【【核心修改】】】
                # 不再使用匿名的 singleShot，而是创建一个我们可以控制的实例
                self.item_timeout_timer = QTimer(self)
                self.item_timeout_timer.setSingleShot(True)
                self.item_timeout_timer.timeout.connect(self.on_item_processing_timeout)
                self.item_timeout_timer.start(self.ITEM_PROCESSING_TIMEOUT * 1000)
                
                self._try_click_current_item()
            else:
                print("...本轮已处理完毕，开始滚动加载更多...")
                self._scroll_and_wait(count)

        self.browser.page().runJavaScript(js_get_count, on_count_received)
            
    def _try_click_current_item(self):
        """尝试点击当前索引处的元素。"""
        js_click = f"""
        (function(index) {{
            const elems = document.querySelectorAll('a.hfpxzc');
            if (index >= elems.length) return false;
            elems[index].scrollIntoView({{behavior:'auto', block:'center'}});
            elems[index].click();
            return true;
        }})({self.current_index});
        """
        self.browser.page().runJavaScript(js_click, self._handle_click_result)

    def _handle_click_result(self, success):
        """处理点击操作的结果。"""
        if success:
            print(f"✅ 点击第 {self.current_index + 1} 个元素成功，等待详情页标题变化")
            self.last_detail_title_before_click = self.last_detail_title # 记录点击前的标题
            self._wait_for_new_detail_title()
        else:
            print(f"❌ 点击第 {self.current_index + 1} 个元素失败，跳过。")
            self.after_extraction_and_move_on()

    def _wait_for_new_detail_title(self, retries=0, max_retries=15): # 可以适当增加重试次数
        """等待右侧详情面板的内容更新。"""
        # 【移除旧的超时检查】这里的超时由外部看门狗负责
        js_get_title = "document.querySelector('h1.DUwDvf.lfPIob')?.textContent.trim() || '';"
        
        def handle_title(title):
            # 如果还没被看门狗中断，才继续执行
            if not self.is_currently_processing_item:
                return

            if title and title != self.last_detail_title_before_click:
                print(f"✅ 详情页标题已更新为: {title}")
                self.last_detail_title = title
                QTimer.singleShot(500, self.extract_detail_info)
            elif retries < max_retries:
                QTimer.singleShot(1000, lambda: self._wait_for_new_detail_title(retries + 1, max_retries))
            else:
                print(f"❌ 等待详情标题变化重试次数已用尽，跳过...")
                self.after_extraction_and_move_on()

        self.browser.page().runJavaScript(js_get_title, handle_title)


    def _scroll_and_wait(self, current_count):
        """
        【修改版】
        滚动列表到底部，然后调用新的轮询函数来等待结果。
        """
        print("📜 正在滚动结果列表以加载更多数据...")
        js_scroll = """
        (function() {
            const feed = document.querySelector('div[role="feed"]');
            if (feed) { feed.scrollTop = feed.scrollHeight; return true; }
            return false;
        })();
        """
        # 执行滚动
        self.browser.page().runJavaScript(js_scroll)
        
        # 【【【核心修改】】】
        # 不再使用 QTimer.singleShot(3000, ...)，而是调用新的智能等待函数
        # 等待500ms让滚动动画生效，然后开始检查
        QTimer.singleShot(500, lambda: self._wait_for_new_results_after_scroll(previous_count=current_count))

    def finish_region_extraction(self):
        """一个地区的所有数据都抓取完毕后，调用此函数来处理后续逻辑。"""
        self.current_region_index += 1 
        QTimer.singleShot(1000, self.search_next_region)

    def after_extraction_and_move_on(self):
        """
        在提取信息后（无论成功、失败还是超时），调用此方法来处理下一个商家。
        【【【修改版】】】
        """
        # 【关键】如果这个函数被调用，说明当前商家处理已结束，需要“喂狗”
        if self.is_currently_processing_item:
            # 【【【核心修改】】】
            # 在继续下一步之前，先停止为当前商家设置的看门狗定时器
            if hasattr(self, 'item_timeout_timer'):
                self.item_timeout_timer.stop()

            self.is_currently_processing_item = False # 解除锁定状态
            self.current_index += 1
            QTimer.singleShot(500, self._process_next_item)

    def handle_result(self, result):
        """
        【修正版】
        处理从JS提取的单条数据。
        修正了UI不更新的逻辑错误。
        """
        try:
            # 1. 检查数据有效性
            if not result or not result.get('name'):
                print("🔵 提取到的数据无效或名称为空，已跳过。")
                return # 直接返回，不执行后续操作

            # 2. 创建一个唯一的标识符（例如：公司名 + 地址）
            item_name = result.get('name', '').strip()
            item_address = result.get('address', '').strip()
            unique_key = f"{item_name}|{item_address}"

            # 3. 检查这个标识符是否已经在我们的缓存中
            if unique_key in self.processed_items_cache:
                print(f"🔵 UI层面发现重复数据，已跳过: {item_name}")
                self.after_extraction_and_move_on() # 跳过重复项，但要继续处理下一个
                return
            
            # 4. 如果是新数据，将其添加到缓存中，防止后续重复
            self.processed_items_cache.add(unique_key)
            # ^^^^^^ 【核心修改点结束】 ^^^^^^

            print(f"📌 提取到新信息: {result.get('name')}")
            # 数据库的 UNIQUE 约束会自动处理重复数据，我们无需在UI层面等待。

            print(f"📌 提取到新信息: {result.get('name')}")

            # 2. 立即更新UI表格，让用户能实时看到新数据
            # self.show_result_single(result)
            self.ui_update_queue.append(result)
            # 获取刚刚添加的行号，用于后续的后台任务
            row = self.table.rowCount() + len(self.ui_update_queue) - 1

            # 3. 异步地将数据发送到后台数据库线程进行存储
            self.db_worker.insert_request.emit(result)

            # 4. 启动后台的AI和邮箱抓取任务（逻辑保持不变）
            if self.ai_toggle_btn.isChecked() and self.ai_toggle_btn.isEnabled():
                company_info = {
                    "name": result.get("name"), "address": result.get("address"),
                    "phone": result.get("phone"), "website": result.get("website"),
                    "row": row
                }
                self.ai_batch_queue.append(company_info)
                if len(self.ai_batch_queue) >= self.AI_BATCH_SIZE:
                    self.start_ai_enrichment()

            website_url = result.get('website')
            # 1. 创建任务单元 (Worker)
            selected_country = self.country_combo.currentText()
            worker = EmailFetcherWorker(
                website=website_url if website_url else "",
                company_name=result.get('name'), 
                address=result.get('address'),
                phone=result.get('phone'), 
                row=row,
                playwright_manager=self.playwright_manager,
                country=selected_country
            )
            # 2. 连接 Worker 的信号到主窗口的槽函数
            worker.signals.emailAndWebsiteFound.connect(self.update_email_and_website)
            # 【重要】连接任务完成信号到我们的新槽函数
            worker.signals.finished.connect(self._on_worker_finished)
            self.thread_pool.start(worker)
            self.active_worker_count += 1

        except Exception as e:
            # 异常捕获逻辑保持不变，确保程序健壮性
            print(f"🔥🔥🔥 [严重错误] 处理数据时发生未知异常: {e}")
            print(f"    - 问题数据: {result}")
            traceback.print_exc()
        
        finally:
            # 保证流程能够继续下去
            self.after_extraction_and_move_on()


    # =====================================================================
    # 【重要】修改 extract_detail_info 的最后一行
    # =====================================================================
    def extract_detail_info(self):
        """
        【修改后的方法】
        此方法现在只负责准备并执行JS脚本，将后续处理完全交给 self.handle_result。
        """
        js_extract = r"""
        (function() {
            // ... (您的JS提取代码保持不变) ...
            const container = document.querySelector('.bJzME.Hu9e2e.tTVLSc');
            if (!container) return null;

            const getText = (selector) => {
                const el = container.querySelector(selector);
                return el ? el.textContent.trim() : "";
            };

            const getMultipleTextByClass = (className) => {
                return Array.from(container.querySelectorAll("." + className.split(" ").join(".")))
                    .map(e => e.innerText.trim());
            };

            const getHours = () => {
                const el = container.querySelector(".ZDu9vd");
                if (!el) return "";
                const spans = Array.from(el.querySelectorAll(":scope > span > span"));
                const texts = spans.map(s => s.innerText.trim());
                return texts.join("");
            };

            const getReviewCount = () => {
                const spans = container.querySelectorAll(".F7nice > span");
                if (spans.length < 2) return "";
                const secondSpan = spans[1];
                const text = secondSpan.textContent.trim();
                const match = text.match(/(\d+)/);
                return match ? match[1] : "";
            };

            const getWebsite = () => {
                const link = container.querySelector('a.CsEnBe[data-item-id="authority"]');
                return link ? link.getAttribute("href") || "" : "";
            };

            const getDkEaLText = () => {
                const el = container.querySelector('.DkEaL');
                return el ? el.textContent.trim() : "";
            };

            const getPhone = () => {
                const details = getMultipleTextByClass("Io6YTe fontBodyMedium kR99db fdkmkc");
                for (let item of details) {
                    let text = item.trim().replace(/\n/g, " ");
                    if (/^\+?\d{1,4}([\s-]?\d{1,5}){2,6}$/.test(text)) {
                        return text;
                    }
                }
                return "";
            };

            const getLink = () => {
                const link = document.querySelector('a.hfpxzc');
                return link ? link.getAttribute("href") || "" : "";
            };

            const name = getText(".DUwDvf.lfPIob");
            const details = getMultipleTextByClass("Io6YTe fontBodyMedium kR99db fdkmkc");
            const rating = getText(".F7nice span[aria-hidden='true']");
            const reviewCount = getReviewCount();
            const website = getWebsite();
            const dkEaLTexts = getDkEaLText();
            const phone = getPhone();
            const link = getLink();
            let address = details[0] || "";
            let hours = getHours();

            return {
                "name": name, "rating": rating, "address": address, "hours": hours,
                "website": website, "dkEaLTexts": dkEaLTexts, "phone": phone,
                "email": "", "reviewCount": reviewCount, "link": link,
            };
        })();
        """
        # 将回调函数指定为我们新创建的、更健壮的 self.handle_result 方法
        self.browser.page().runJavaScript(js_extract, self.handle_result)


    # 清理已完成的线程
    def cleanup_fetcher(self, fetcher, fetcher_type="email"):
        """清理已完成的线程"""
        if fetcher_type == "email" and fetcher in self.email_fetchers:
            self.email_fetchers.remove(fetcher)
        elif fetcher_type == "ai" and fetcher in self.ai_fetchers:
            self.ai_fetchers.remove(fetcher)

        fetcher.deleteLater()

        self._check_if_all_work_is_done()

    # 更新表格中的邮箱列
    def update_email_in_table(self, website, email, row):
        """更新表格中的邮箱列"""
        if row < self.table.rowCount():
            print(f"📧 为网站 {website} 提取到邮箱: {email}")
            item = QTableWidgetItem(email)
            self.table.setItem(row, 3, item)  # 第3列是邮箱列


    # 显示数据到页面上
    def show_result_single(self, item):
        # 追加一行，而不是重置表格
        row = self.table.rowCount()
        self.table.insertRow(row)

        self.table.setItem(row, 0, QTableWidgetItem(item.get("name", "")))
        self.table.setItem(row, 1, QTableWidgetItem(item.get("address", "")))
        self.table.setItem(row, 2, QTableWidgetItem(item.get("phone", "")))
        self.table.setItem(row, 3, QTableWidgetItem(""))
        self.table.setItem(row, 4, QTableWidgetItem(item.get("website", "")))
        self.table.setItem(row, 5, QTableWidgetItem(item.get("dkEaLTexts", "")))
        self.table.setItem(row, 6, QTableWidgetItem(item.get("hours", "")))
        self.table.setItem(row, 7, QTableWidgetItem(item.get("rating", "")))
        self.table.setItem(row, 8, QTableWidgetItem(str(item.get("reviewCount", ""))))
        self.table.setItem(row, 9, QTableWidgetItem(item.get("link", "")))

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


    # 导出的数据
    def export_results(self):
        # 1. 从数据库获取所有数据
        all_data = self.db_worker.get_all_companies_blocking()

        if not all_data:
            QMessageBox.information(self, "提示", "数据库中没有可导出的数据。")
            return

        path, _ = QFileDialog.getSaveFileName(self, "保存数据", "",
                                            "Excel Files (*.xlsx);;CSV Files (*.csv)")
        if not path:
            return

        # 2. 将字典列表转换为DataFrame
        df = pd.DataFrame(all_data)

        # 【修正点】在这里初始化 export_success 变量
        export_success = False 

        try:
            if path.lower().endswith('.xlsx'):
                # (您的 Excel 导出代码... 保持不变)
                writer = pd.ExcelWriter(path, engine='openpyxl')
                df.to_excel(writer, index=False, sheet_name='地图数据')
                worksheet = writer.sheets['地图数据']
                default_font = Font(name='Microsoft YaHei', size=11)
                for column in worksheet.columns:
                    max_length = 0
                    column_name = column[0].column_letter
                    for cell in column:
                        if cell.value is not None: # 只处理非空单元格
                            cell_len = len(str(cell.value))
                            if cell_len > max_length:
                                max_length = cell_len
                    adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column_name].width = adjusted_width
                writer.close()
                QMessageBox.information(self, "导出成功", f"成功导出 {len(all_data)} 条数据到 Excel 文件。")
                export_success = True # <--- 导出成功后，设置为 True

            elif path.lower().endswith('.csv'):
                # (您的 CSV 导出代码... 保持不变)
                df.to_csv(path, index=False, encoding='utf-8-sig')
                QMessageBox.information(self, "导出成功",
                                        f"成功导出 {len(all_data)} 条数据到 CSV 文件。\n\n"
                                        "建议使用 Microsoft Excel, WPS 表格 或 LibreOffice Calc 等电子表格软件打开此文件，"
                                        "以获得最佳的表格排版和网格线效果。")
                export_success = True # <--- 导出成功后，设置为 True
            

        except Exception as e:
            QMessageBox.warning(self, "导出失败", str(e))
            export_success = False # 发生异常时，确保是 False

        # 导出成功后将消息发送到后端
        if export_success:
            if self.user_id:
                self.send_export_signal(self.user_id)
            else:
                print("❌ user_id 未设置，无法记录导出次数。")
                QMessageBox.warning(self, "导出警告", "用户ID无效，无法记录导出次数。请重新登录。")



    # 导出后通知后端记录次数
    def send_export_signal(self, user_id):
        """导出后通知后端记录次数"""
        if user_id is None:
            print("❌ user_id 为 None，无法发送导出记录。")
            QMessageBox.warning(self, "导出警告", "用户ID无效，无法记录导出次数。请重新登录。")
            return  # 不发送请求
    
        try:
            url = "https://google-maps-backend-master.netlify.app/.netlify/functions/recordExport"  # 改成你的 Netlify API 地址
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
    def on_load_started(self):
        # 只在用户主动发起导航时才显示 loading 动画
        if self.user_triggered_navigation and not self.is_loading:
            self.is_loading = True
            # 获取 browser 组件在父窗口中的绝对位置（左上角）
            browser_pos = self.browser.mapTo(self, self.browser.rect().topLeft())

            # 设置 loading_label 的位置和大小，使其覆盖整个浏览器区域
            self.loading_label.setGeometry(browser_pos.x(), browser_pos.y(),
                                        self.browser.width(), self.browser.height())
            # 将 loading 动画置于最前面
            self.loading_label.raise_()

             # 显示 loading 动画
            self.loading_label.show()

    # ✅ 页面加载结束时触发（成功或失败都会触发）
    def on_load_finished(self, ok):
        self.load_timeout_timer.stop()
        if self.is_loading:

            # 重置 loading 状态
            self.is_loading = False

            # 隐藏 loading 动画
            self.loading_label.hide()

        # 无论加载是否成功都要重置导航状态
        self.user_triggered_navigation = False
        if not ok:
            print("页面加载失败")

        # 根据加载类型分发处理
        if hasattr(self, '_current_load_type'):
            if self._current_load_type == "initial_map_load":
                # 初始地图加载，无需额外处理，loading 动画已隐藏
                print("初始地图加载完成。")
            elif self._current_load_type == "batch_search":
                # 批次搜索加载，调用相应的批次处理方法
                if hasattr(self, '_batch_search_info'):
                    info = self._batch_search_info
                    self.on_load_finished_for_batch(
                        ok=ok,
                        keyword=info["keyword"],
                        country=info["country"],
                        region=info["region"],
                        industry=info["industry"],
                        latitude=info["latitude"],
                        longitude=info["longitude"]
                    )
                self._current_load_type = None # 处理完后重置
                self._batch_search_info = None # 清理信息
        else:
            print("未知页面加载完成。")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # 调整 loading 遮罩
        if self.loading_label.isVisible():
            browser_pos = self.browser.mapTo(self, self.browser.rect().topLeft())
            self.loading_label.setGeometry(browser_pos.x(), browser_pos.y(),
                                        self.browser.width(), self.browser.height())
        # 调整倒计时遮罩
        if self.countdown_label.isVisible():
            browser_pos = self.browser.mapTo(self, self.browser.rect().topLeft())
            self.countdown_label.setGeometry(browser_pos.x(), browser_pos.y(),
                                        self.browser.width(), self.browser.height())


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
        self.region_combo.clear()
        regions = self.region_data_by_country.get(country, [])
        region_names = [r.get("name", "未知地区") for r in regions]
        self.region_combo.addItems(region_names)



    # 新的槽函数，用于同时更新表格中的邮箱和官网列。
    def update_email_and_website(self, email, found_website, row):
        # 1. 将UI更新指令放入队列
        # 指令格式: (行, 列, 文本)
        self.cell_update_queue.append((row, 3, email)) # 邮箱更新指令

        # 官网也一样处理
        # 注意：这里我们不再从UI读取官网，因为可能还没来得及更新
        # 而是直接使用信号传过来的 found_website
        self.cell_update_queue.append((row, 4, found_website))

        # 2. 数据库更新逻辑保持不变，它已经是异步的了
        # 从UI表格中获取name和address作为更新数据库的键
        name_item = self.table.item(row, 0)
        address_item = self.table.item(row, 1)

        if name_item and address_item:
            name = name_item.text()
            address = address_item.text()
            self.db_worker.update_request.emit(name, address, email, found_website)

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
        重写窗口关闭事件，确保所有后台服务被安全关闭。
        结合了对AI队列的检查、通用的退出确认以及对后台线程池的等待。
        """
        # 1. 检查是否有未完成的AI任务，并提示用户
        if self.ai_batch_queue:
            reply = QMessageBox.question(self, '确认退出',
                                        'AI处理队列中仍有待处理项目，确定要退出吗？',
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore() # 用户选择不退出，忽略关闭事件
                return
        else:
            # 2. 如果没有AI任务，则进行通用退出确认
            reply = QMessageBox.question(self, '确认退出', '确定要退出程序吗？',
                                         QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.No:
                event.ignore()
                return

        # 3. 执行清理工作
        print("程序即将关闭，开始执行清理工作...")

        # 依次关闭后台服务
        self.playwright_manager.shutdown()
        self.db_worker.stop()

        # 等待线程池中的所有任务完成，最长等待5秒
        print("等待后台任务完成...")
        self.thread_pool.waitForDone(5000)

        print("清理工作完成，程序将退出。")
        event.accept() # 接受关闭事件，允许窗口关闭


    # 检查是否所有任务（地图抓取 + 所有后台邮箱抓取）都已完成。
    def _check_if_all_work_is_done(self):
        """
        【修改版】
        检查是否所有任务（地图抓取 + 所有后台任务）都已完成。
        """
        # 只有当地图抓取完成，并且没有任何正在运行的后台任务时，才算真正完成
        if self.map_scraping_finished and self.active_worker_count == 0:
            print("✅✅✅ 所有地图抓取和后台邮箱任务均已完成！")
            self.is_searching = False
            self.progress_bar.hide()
            QMessageBox.information(self, "任务完成", "所有关键词的地图数据和邮箱抓取任务均已完成。")


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

    def _on_worker_finished(self):
        """当一个后台任务完成时，这个槽函数会被调用。"""
        self.active_worker_count -= 1
        # 每次有任务完成时，都检查一下是否所有工作都结束了
        self._check_if_all_work_is_done()

    def _process_ui_update_queue(self):
        # 如果两个队列都是空的，就什么都不做
        if not self.ui_update_queue and not self.cell_update_queue:
            return

        # 复制并清空两个队列
        items_to_add = self.ui_update_queue[:]
        self.ui_update_queue.clear()

        cells_to_update = self.cell_update_queue[:]
        self.cell_update_queue.clear()

        # 关键性能优化：在所有操作开始前禁用UI更新
        self.table.setUpdatesEnabled(False)
        try:
            # 第一步：先处理所有要新增的行
            if items_to_add:
                for item in items_to_add:
                    self.show_result_single(item)

            # 第二步：再处理所有要更新的单元格
            if cells_to_update:
                for row, col, text in cells_to_update:
                    # 在这里，我们只更新那些UI上还没有值的单元格，或者强制更新邮箱
                    # 官网只有在为空时才更新
                    if col == 3: # 邮箱列，总是更新
                        self.table.setItem(row, col, QTableWidgetItem(text))
                    elif col == 4: # 官网列
                        current_item = self.table.item(row, col)
                        if not current_item or not current_item.text():
                            self.table.setItem(row, col, QTableWidgetItem(text))
        finally:
            # 关键性能优化：所有操作完成后，一次性启用更新，让所有变化同时显示出来
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
        self.search_btn.clicked.connect(self.resume_search)

        # 4. 弹窗提示用户
        QMessageBox.warning(self, "需要您操作",
                            "检测到Google人机验证，自动抓取已暂停。\n\n"
                            "请在下方的内置浏览器中手动完成验证后，点击“恢复任务”按钮继续。")

    def resume_search(self):
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
            self.search_btn.clicked.disconnect(self.resume_search)
        except TypeError:
            pass
        self.search_btn.clicked.connect(self.start_search_batch)

        # 4. 【关键】从中断的地方继续：重新调用等待函数
        #    此时页面上的人机验证应该已经解决了
        self.wait_for_search_results()

    # 当页面加载时间超过我们设定的硬性上限时，此方法被调用。
    def on_load_timeout(self):
        """
        当页面加载时间超过我们设定的硬性上限时，此方法被调用。
        """
        print("❌ 页面加载硬性超时！QWebEngineView可能已卡死，正在强制停止并跳过当前地区...")
        
        # 1. 强制停止 QWebEngineView 当前的所有加载活动
        self.browser.stop()
        
        # 2. 手动处理UI状态，因为 on_load_finished 不会被调用了
        if self.is_loading:
            self.is_loading = False
            self.loading_label.hide()
        self.user_triggered_navigation = False

        # 3. 手动推进到下一个任务
        self.current_region_index += 1
        self.search_next_region()


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


    def _wait_for_new_results_after_scroll(self, previous_count, start_time=None, max_wait_sec=10):
        """
        在滚动后，主动轮询检查新结果是否出现，带有超时机制。
        这取代了旧的固定3秒等待。
        """
        if start_time is None:
            start_time = time.time()
            print(f"  -> 等待新结果加载... (超时: {max_wait_sec}s)")

        # 检查是否超时
        if time.time() - start_time > max_wait_sec:
            print(f"🛑 等待新结果超时({max_wait_sec}s)，认为已到达列表底部。")
            self.finish_region_extraction()
            return

        # 检查当前元素数量
        js_get_count = "document.querySelectorAll('a.hfpxzc').length;"
        
        def handle_check(current_count):
            if current_count > previous_count:
                # 成功！发现了新结果
                print(f"  -> ✅ 新结果已加载 (数量从 {previous_count} -> {current_count})。")
                # 等待500ms让DOM稳定，然后开始下一轮提取
                QTimer.singleShot(500, lambda: self._scroll_and_extract_loop(previous_count=previous_count))
            else:
                # 还没有新结果，继续等待并轮询
                QTimer.singleShot(1000, lambda: self._wait_for_new_results_after_scroll(previous_count, start_time, max_wait_sec))

        self.browser.page().runJavaScript(js_get_count, handle_check)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # --- 修改后的启动流程 ---

    # 1. 创建并显示登录对话框
    login_dialog = LoginDialog()

    # 2. 调用 exec_() 会以模态方式显示对话框，并阻塞程序直到对话框关闭。
    #    - 如果在对话框中调用了 self.accept() (登录成功时), exec_() 返回 QDialog.Accepted。
    #    - 如果调用了 self.reject() 或用户点击了窗口的关闭按钮, exec_() 返回 QDialog.Rejected。
    result = login_dialog.exec_()

    # 3. 根据登录对话框返回的结果，决定是否启动主程序
    if result == QDialog.Accepted:
        # 如果登录成功 (result is QDialog.Accepted)
        print("✅ 登录成功，正在启动主应用程序...")
        user_id = getattr(login_dialog, "logged_in_user_id", None)
        if user_id:
            main_app_window = GoogleMapsApp(user_id=user_id)  # 传递 user_id
            main_app_window.show()
            sys.exit(app.exec_())
        else:
            print("❌ 未获取到 user_id，程序将退出。")
            sys.exit()
    else:
        # 如果登录失败或用户取消登录 (result is QDialog.Rejected)
        print("❌ 登录已取消或失败，程序将退出。")
        # 直接退出程序
        sys.exit()