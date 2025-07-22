#!/usr/bin/env python3
"""
OpenAI Agent Tool Script
Configurable script for using OpenAI agents to interact with websites,
collect data, run tests, and maintain chat persistence.
"""

import os
import json
import logging
import asyncio
import argparse
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
from pathlib import Path
import aiohttp
from openai import AsyncOpenAI
from bs4 import BeautifulSoup
import pickle
from urllib.parse import urlparse, urljoin
from playwright.async_api import async_playwright, Browser, Page
import base64

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Configuration for the OpenAI agent"""
    api_key: str
    model: str = "gpt-4-turbo-preview"
    temperature: float = 0.7
    max_tokens: int = 4096
    max_retries: int = 3
    retry_delay: int = 2
    timeout: int = 30
    persist_chat: bool = True
    chat_history_file: str = "chat_history.pkl"
    system_prompt: str = "You are a helpful assistant that can analyze websites and collect data."
    project_root: str = "."  # Root directory for file access
    allowed_file_extensions: List[str] = field(default_factory=lambda: [".txt", ".json", ".csv", ".xml", ".html", ".log", ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".css", ".yml", ".yaml", ".toml", ".ini", ".conf"])
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    browser_headless: bool = True
    browser_timeout: int = 30000  # milliseconds
    # Screenshot optimization settings
    screenshot_save_to_file: bool = True  # Save screenshots to file instead of base64
    screenshot_max_width: int = 1280  # Max screenshot width
    screenshot_max_height: int = 720  # Max screenshot height
    screenshot_quality: int = 80  # JPEG quality (0-100)
    content_max_length: int = 50000  # Max HTML content length before truncation


@dataclass
class WebRequest:
    """Configuration for web requests"""
    url: str
    task: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    data: Optional[Dict[str, Any]] = None
    extract_fields: Optional[List[str]] = None
    follow_redirects: bool = True
    verify_ssl: bool = True
    user_agent: str = "Mozilla/5.0 (compatible; OpenAI-Agent/1.0)"


@dataclass
class TaskResult:
    """Structured result from agent task"""
    success: bool
    timestamp: str
    url: str
    task: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None
    agent_analysis: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


class ChatHistory:
    """Manages persistent chat history"""
    
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.messages: List[Dict[str, str]] = []
        self.load()
    
    def load(self):
        """Load chat history from file"""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'rb') as f:
                    self.messages = pickle.load(f)
                logger.info(f"Loaded {len(self.messages)} messages from history")
            except Exception as e:
                logger.error(f"Error loading chat history: {e}")
                self.messages = []
    
    def save(self):
        """Save chat history to file"""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, 'wb') as f:
                pickle.dump(self.messages, f)
            logger.info("Chat history saved")
        except Exception as e:
            logger.error(f"Error saving chat history: {e}")
    
    def add_message(self, role: str, content: str):
        """Add a message to history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.save()
    
    def get_context(self, max_messages: int = 10) -> List[Dict[str, str]]:
        """Get recent messages for context"""
        return [
            {"role": msg["role"], "content": msg["content"]}
            for msg in self.messages[-max_messages:]
        ]
    
    def clear(self):
        """Clear chat history"""
        self.messages = []
        self.save()


class OpenAIAgent:
    """OpenAI agent for web interaction and data collection"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self.client = AsyncOpenAI(api_key=config.api_key)
        self.chat_history = ChatHistory(config.chat_history_file) if config.persist_chat else None
        self.session: Optional[aiohttp.ClientSession] = None
        self.browser: Optional[Browser] = None
        self.playwright = None
        self.project_root = Path(config.project_root).resolve()
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        self.playwright = await async_playwright().start()
        
        # If we get here without DISPLAY and headless=False, it means xvfb-run failed
        if not self.config.browser_headless and not os.environ.get('DISPLAY'):
            logger.warning("No display found but continuing anyway. Browser may fail to start.")
            logger.warning("You can disable this automatic wrapper with --no-xvfb-wrapper")
        
        try:
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.browser_headless
            )
        except Exception as e:
            if "Missing X server or $DISPLAY" in str(e):
                if self.config.browser_headless:
                    logger.error("\nError: Unable to start browser even in headless mode.\n"
                               "This might be a Playwright/Chromium issue. Try:\n"
                               "  1. Reinstalling Playwright: pip install -U playwright\n"
                               "  2. Installing browser: playwright install chromium\n")
                else:
                    logger.error("\nError: Unable to start browser due to missing display.\n"
                               "Xvfb auto-start failed. Please either:\n"
                               "  1. Install Xvfb: sudo apt-get install xvfb\n"
                               "  2. Use xvfb-run: xvfb-run -a python openai_agent_tool.py [args]\n"
                               "  3. Set browser_headless=True in your config\n")
                raise RuntimeError("Display error. See instructions above.")
            raise
        
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
    
    async def fetch_webpage(self, request: WebRequest) -> Dict[str, Any]:
        """Fetch webpage content"""
        headers = request.headers or {}
        headers['User-Agent'] = request.user_agent
        
        try:
            async with self.session.request(
                method=request.method,
                url=request.url,
                headers=headers,
                data=request.data,
                allow_redirects=request.follow_redirects,
                ssl=request.verify_ssl,
                timeout=aiohttp.ClientTimeout(total=self.config.timeout)
            ) as response:
                content = await response.text()
                
                return {
                    'status': response.status,
                    'headers': dict(response.headers),
                    'content': content,
                    'url': str(response.url),
                    'cookies': [
                        {'name': c.key, 'value': c.value}
                        for c in response.cookies.values()
                    ]
                }
        except asyncio.TimeoutError:
            raise Exception(f"Request timed out after {self.config.timeout} seconds")
        except Exception as e:
            raise Exception(f"Failed to fetch webpage: {str(e)}")
    
    def extract_text_from_html(self, html: str) -> str:
        """Extract readable text from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Break into lines and remove leading/trailing space
        lines = (line.strip() for line in text.splitlines())
        
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        
        # Drop blank lines
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    async def playwright_navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to URL using Playwright with console logging"""
        page = await self.browser.new_page()
        
        # Collect console messages
        console_messages = []
        errors = []
        warnings = []
        
        def handle_console(msg):
            message_data = {
                "type": msg.type,
                "text": msg.text,
                "location": f"{msg.location.get('url', '')}:{msg.location.get('lineNumber', '')}:{msg.location.get('columnNumber', '')}" if msg.location else ""
            }
            console_messages.append(message_data)
            
            if msg.type == 'error':
                errors.append(message_data)
            elif msg.type == 'warning':
                warnings.append(message_data)
        
        def handle_page_error(error):
            errors.append({
                "type": "pageerror",
                "text": str(error),
                "location": ""
            })
        
        # Listen for console events
        page.on('console', handle_console)
        page.on('pageerror', handle_page_error)
        
        try:
            await page.goto(url, wait_until='networkidle', timeout=self.config.browser_timeout)
            title = await page.title()
            raw_content = await page.content()
            
            # Truncate content if too large (to avoid token limits)
            content = self._truncate_content(raw_content, max_length=50000)
            
            # Optimized screenshot handling
            screenshot_info = await self._handle_screenshot(page, url)
            
            # Get network errors from failed requests
            network_errors = []
            response_errors = await page.evaluate("""
                () => {
                    const errors = [];
                    // Check for failed network requests in performance entries
                    const entries = performance.getEntriesByType('navigation');
                    entries.forEach(entry => {
                        if (entry.type === 'navigate' && entry.responseStatus >= 400) {
                            errors.push({
                                type: 'network',
                                text: `HTTP ${entry.responseStatus} - ${entry.name}`,
                                location: entry.name
                            });
                        }
                    });
                    return errors;
                }
            """)
            network_errors.extend(response_errors)
            
            result = {
                "success": True,
                "title": title,
                "url": page.url,
                "content": content,
                "console_messages": console_messages,
                "errors": errors + network_errors,
                "warnings": warnings,
                "console_summary": {
                    "total_messages": len(console_messages),
                    "error_count": len(errors + network_errors),
                    "warning_count": len(warnings)
                }
            }
            
            # Add screenshot information
            result.update(screenshot_info)
            return result
        finally:
            await page.close()
    
    async def _handle_screenshot(self, page, url: str) -> Dict[str, Any]:
        """Handle screenshot capture with optimization options"""
        try:
            # Set viewport size for consistent screenshots
            await page.set_viewport_size({
                "width": self.config.screenshot_max_width,
                "height": self.config.screenshot_max_height
            })
            
            # Take screenshot with optimized settings
            screenshot_options = {
                "type": "jpeg" if self.config.screenshot_quality < 100 else "png",
                "quality": self.config.screenshot_quality if self.config.screenshot_quality < 100 else None
            }
            
            screenshot = await page.screenshot(**screenshot_options)
            screenshot_size = len(screenshot)
            
            # Generate filename from URL and timestamp
            import re
            from datetime import datetime
            safe_url = re.sub(r'[^\w\-_.]', '_', url.replace('http://', '').replace('https://', ''))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshot_{safe_url}_{timestamp}.jpg"
            
            if self.config.screenshot_save_to_file:
                # Save screenshot to file
                screenshot_path = os.path.join(os.path.dirname(__file__), "screenshots", filename)
                os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                
                with open(screenshot_path, "wb") as f:
                    f.write(screenshot)
                
                return {
                    "screenshot_saved": True,
                    "screenshot_path": screenshot_path,
                    "screenshot_filename": filename,
                    "screenshot_size_bytes": screenshot_size,
                    "screenshot_dimensions": f"{self.config.screenshot_max_width}x{self.config.screenshot_max_height}",
                    "screenshot_summary": f"Screenshot saved to {filename} ({screenshot_size} bytes)"
                }
            else:
                # Traditional base64 encoding (with size limit check)
                base64_size = (screenshot_size * 4) // 3  # Approximate base64 size
                if base64_size > 50000:  # ~50KB limit to avoid token issues
                    # Save anyway and provide path reference
                    screenshot_path = os.path.join(os.path.dirname(__file__), "screenshots", filename)
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    
                    with open(screenshot_path, "wb") as f:
                        f.write(screenshot)
                    
                    return {
                        "screenshot_saved": True,
                        "screenshot_path": screenshot_path,
                        "screenshot_too_large_for_base64": True,
                        "screenshot_size_bytes": screenshot_size,
                        "screenshot_summary": f"Screenshot too large for base64 ({screenshot_size} bytes), saved to {filename}"
                    }
                else:
                    return {
                        "screenshot_base64": base64.b64encode(screenshot).decode('utf-8'),
                        "screenshot_size_bytes": screenshot_size,
                        "screenshot_summary": f"Screenshot included as base64 ({screenshot_size} bytes)"
                    }
                    
        except Exception as e:
            logger.error(f"Screenshot capture failed: {e}")
            return {
                "screenshot_error": str(e),
                "screenshot_summary": f"Screenshot capture failed: {e}"
            }
    
    def _truncate_content(self, content: str, max_length: int = 50000) -> str:
        """Truncate HTML content to avoid token limits while preserving structure"""
        if len(content) <= max_length:
            return content
            
        # Try to truncate at a reasonable HTML boundary
        truncated = content[:max_length]
        
        # Find last complete tag
        last_tag_end = truncated.rfind('>')
        if last_tag_end != -1 and last_tag_end > max_length * 0.8:
            truncated = truncated[:last_tag_end + 1]
        
        # Add truncation notice
        truncated += f"\n<!-- Content truncated at {len(truncated)} characters (original: {len(content)}) -->"
        
        logger.info(f"Content truncated from {len(content)} to {len(truncated)} characters")
        return truncated
    
    async def playwright_click(self, selector: str, page_url: str) -> Dict[str, Any]:
        """Click element on page"""
        page = await self.browser.new_page()
        try:
            await page.goto(page_url, wait_until='networkidle', timeout=self.config.browser_timeout)
            await page.click(selector, timeout=self.config.browser_timeout)
            await page.wait_for_load_state('networkidle')
            
            return {
                "success": True,
                "clicked": selector,
                "new_url": page.url,
                "title": await page.title()
            }
        finally:
            await page.close()
    
    async def playwright_fill_form(self, page_url: str, form_data: Dict[str, str]) -> Dict[str, Any]:
        """Fill form fields"""
        page = await self.browser.new_page()
        try:
            await page.goto(page_url, wait_until='networkidle', timeout=self.config.browser_timeout)
            
            for selector, value in form_data.items():
                await page.fill(selector, value)
            
            return {
                "success": True,
                "filled_fields": list(form_data.keys()),
                "url": page.url
            }
        finally:
            await page.close()
    
    async def playwright_extract_data(self, page_url: str, selectors: Dict[str, str]) -> Dict[str, Any]:
        """Extract data from page using selectors"""
        page = await self.browser.new_page()
        try:
            await page.goto(page_url, wait_until='networkidle', timeout=self.config.browser_timeout)
            
            extracted = {}
            for name, selector in selectors.items():
                try:
                    element = await page.query_selector(selector)
                    if element:
                        extracted[name] = await element.text_content()
                    else:
                        extracted[name] = None
                except Exception as e:
                    extracted[name] = f"Error: {str(e)}"
            
            return {
                "success": True,
                "data": extracted,
                "url": page.url
            }
        finally:
            await page.close()
    
    async def playwright_get_console_logs(self, page_url: str) -> Dict[str, Any]:
        """Get comprehensive console logs and debugging info"""
        page = await self.browser.new_page()
        
        # Collect all console activity
        console_messages = []
        errors = []
        warnings = []
        network_failures = []
        
        def handle_console(msg):
            message_data = {
                "type": msg.type,
                "text": msg.text,
                "timestamp": datetime.now().isoformat(),
                "location": f"{msg.location.get('url', '')}:{msg.location.get('lineNumber', '')}:{msg.location.get('columnNumber', '')}" if msg.location else ""
            }
            console_messages.append(message_data)
            
            if msg.type == 'error':
                errors.append(message_data)
            elif msg.type == 'warning':
                warnings.append(message_data)
        
        def handle_page_error(error):
            errors.append({
                "type": "pageerror",
                "text": str(error),
                "timestamp": datetime.now().isoformat(),
                "location": "page"
            })
        
        def handle_response(response):
            if not response.ok:
                network_failures.append({
                    "type": "network_error",
                    "status": response.status,
                    "url": response.url,
                    "text": f"HTTP {response.status} - {response.status_text}",
                    "timestamp": datetime.now().isoformat()
                })
        
        # Set up listeners
        page.on('console', handle_console)
        page.on('pageerror', handle_page_error)
        page.on('response', handle_response)
        
        try:
            await page.goto(page_url, wait_until='networkidle', timeout=self.config.browser_timeout)
            
            # Execute JavaScript to get additional debugging info
            debug_info = await page.evaluate("""
                () => {
                    const result = {
                        userAgent: navigator.userAgent,
                        url: window.location.href,
                        title: document.title,
                        readyState: document.readyState,
                        errors: [],
                        performance: {},
                        localStorage: {},
                        sessionStorage: {}
                    };
                    
                    // Get performance data
                    if (window.performance) {
                        const navigation = performance.getEntriesByType('navigation')[0];
                        if (navigation) {
                            result.performance = {
                                loadTime: navigation.loadEventEnd - navigation.fetchStart,
                                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.fetchStart,
                                responseStatus: navigation.responseStatus
                            };
                        }
                    }
                    
                    // Try to get storage info (may fail due to permissions)
                    try {
                        for (let i = 0; i < localStorage.length; i++) {
                            const key = localStorage.key(i);
                            result.localStorage[key] = localStorage.getItem(key);
                        }
                    } catch (e) {
                        result.localStorage.error = e.toString();
                    }
                    
                    try {
                        for (let i = 0; i < sessionStorage.length; i++) {
                            const key = sessionStorage.key(i);
                            result.sessionStorage[key] = sessionStorage.getItem(key);
                        }
                    } catch (e) {
                        result.sessionStorage.error = e.toString();
                    }
                    
                    return result;
                }
            """)
            
            return {
                "success": True,
                "url": page.url,
                "console_messages": console_messages,
                "errors": errors + network_failures,
                "warnings": warnings,
                "debug_info": debug_info,
                "summary": {
                    "total_console_messages": len(console_messages),
                    "error_count": len(errors + network_failures),
                    "warning_count": len(warnings),
                    "page_loaded": debug_info.get('readyState') == 'complete'
                }
            }
        finally:
            await page.close()
    
    async def read_file(self, file_path: str) -> Dict[str, Any]:
        """Read file from project directory"""
        try:
            # Strip leading slashes to ensure relative path
            clean_path = file_path.lstrip('/')
            full_path = self.project_root / clean_path
            
            # Security check - ensure path is within project root
            resolved_path = full_path.resolve()
            if not str(resolved_path).startswith(str(self.project_root)):
                return {
                    "success": False,
                    "error": "Access denied: Path is outside project root"
                }
            
            # Check file extension
            if resolved_path.suffix not in self.config.allowed_file_extensions:
                return {
                    "success": False,
                    "error": f"File type not allowed: {resolved_path.suffix}"
                }
            
            # Check file size
            if resolved_path.stat().st_size > self.config.max_file_size:
                return {
                    "success": False,
                    "error": f"File too large: {resolved_path.stat().st_size} bytes"
                }
            
            # Read file
            with open(resolved_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return {
                "success": True,
                "path": str(resolved_path),
                "content": content,
                "size": len(content)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def list_files(self, directory: str = ".", pattern: str = "*") -> Dict[str, Any]:
        """List files in directory"""
        try:
            # Strip leading slashes to ensure relative path
            clean_directory = directory.lstrip('/') if directory != "." else "."
            dir_path = self.project_root / clean_directory
            
            # Security check
            resolved_path = dir_path.resolve()
            if not str(resolved_path).startswith(str(self.project_root)):
                return {
                    "success": False,
                    "error": "Access denied: Path is outside project root"
                }
            
            files = []
            for item in resolved_path.glob(pattern):
                if item.is_file() and item.suffix in self.config.allowed_file_extensions:
                    files.append({
                        "path": str(item.relative_to(self.project_root)),
                        "size": item.stat().st_size,
                        "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                    })
            
            return {
                "success": True,
                "directory": str(resolved_path.relative_to(self.project_root)),
                "files": files,
                "count": len(files)
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def create_tool_definitions(self) -> List[Dict[str, Any]]:
        """Create tool definitions for function calling"""
        return [
            {
                "type": "function",
                "function": {
                    "name": "navigate_to_url",
                    "description": "Navigate to a URL using browser automation",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "url": {
                                "type": "string",
                                "description": "The URL to navigate to"
                            }
                        },
                        "required": ["url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "click_element",
                    "description": "Click an element on the page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "selector": {
                                "type": "string",
                                "description": "CSS selector for the element to click"
                            },
                            "page_url": {
                                "type": "string",
                                "description": "The page URL to navigate to first"
                            }
                        },
                        "required": ["selector", "page_url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "fill_form",
                    "description": "Fill form fields on a page",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page_url": {
                                "type": "string",
                                "description": "The page URL to navigate to"
                            },
                            "form_data": {
                                "type": "object",
                                "description": "Object with selector:value pairs for form fields"
                            }
                        },
                        "required": ["page_url", "form_data"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "extract_data",
                    "description": "Extract data from page using CSS selectors",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page_url": {
                                "type": "string",
                                "description": "The page URL to navigate to"
                            },
                            "selectors": {
                                "type": "object",
                                "description": "Object with name:selector pairs for data extraction"
                            }
                        },
                        "required": ["page_url", "selectors"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "read_file",
                    "description": "Read a file from the project directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "file_path": {
                                "type": "string",
                                "description": "Path to the file relative to project root"
                            }
                        },
                        "required": ["file_path"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "list_files",
                    "description": "List files in a directory",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "directory": {
                                "type": "string",
                                "description": "Directory path relative to project root",
                                "default": "."
                            },
                            "pattern": {
                                "type": "string",
                                "description": "Glob pattern for filtering files",
                                "default": "*"
                            }
                        }
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_console_logs",
                    "description": "Get comprehensive developer console logs, errors, warnings and debugging info from a webpage",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "page_url": {
                                "type": "string",
                                "description": "The page URL to analyze"
                            }
                        },
                        "required": ["page_url"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_and_report",
                    "description": "Analyze data and create a structured report",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Report title"
                            },
                            "summary": {
                                "type": "string",
                                "description": "Executive summary"
                            },
                            "findings": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Key findings"
                            },
                            "data": {
                                "type": "object",
                                "description": "Structured data collected"
                            },
                            "errors": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Any errors encountered"
                            },
                            "recommendations": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Next steps or recommendations"
                            }
                        },
                        "required": ["title", "summary", "findings", "data"]
                    }
                }
            }
        ]
    
    async def process_task(self, request: WebRequest) -> TaskResult:
        """Process a web task with the agent"""
        start_time = datetime.now()
        
        try:
            # Prepare messages
            messages = []
            
            # Add system prompt with tool capabilities
            system_prompt = f"""{self.config.system_prompt}

You have access to the following tools:
- navigate_to_url: Navigate to any URL using a real browser
- click_element: Click elements on web pages using CSS selectors
- fill_form: Fill out forms on web pages
- extract_data: Extract specific data from pages using CSS selectors
- get_console_logs: Get comprehensive developer console logs, errors, warnings, and debugging info
- read_file: Read files from the project directory (root: {self.config.project_root})
- list_files: List files in the project directory
- analyze_and_report: Create structured reports from collected data

Use these tools to complete the requested task. Be thorough and handle errors gracefully. 
For debugging tasks, use get_console_logs to capture developer console information."""
            
            messages.append({
                "role": "system",
                "content": system_prompt
            })
            
            # Add chat history if available
            if self.chat_history:
                messages.extend(self.chat_history.get_context())
            
            # Add current task
            task_prompt = f"""
Task: {request.task}
Target URL: {request.url}

Please complete this task using the available tools. Be systematic and thorough in your approach.
"""
            
            if request.extract_fields:
                task_prompt += f"\n\nSpecifically extract these fields: {', '.join(request.extract_fields)}"
            
            messages.append({
                "role": "user",
                "content": task_prompt
            })
            
            # Call OpenAI with tools
            logger.info("Calling OpenAI API with function calling")
            
            collected_data = {}
            errors = []
            tool_calls_made = []
            
            # Allow multiple rounds of tool calls
            for _ in range(5):  # Max 5 rounds of tool calls
                response = await self.client.chat.completions.create(
                    model=self.config.model,
                    messages=messages,
                    temperature=self.config.temperature,
                    max_tokens=self.config.max_tokens,
                    tools=self.create_tool_definitions(),
                    tool_choice="auto"
                )
                
                assistant_message = response.choices[0].message
                messages.append({
                    "role": assistant_message.role,
                    "content": assistant_message.content,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "type": tc.type,
                            "function": {
                                "name": tc.function.name,
                                "arguments": tc.function.arguments
                            }
                        } for tc in (assistant_message.tool_calls or [])
                    ] if assistant_message.tool_calls else None
                })
                
                # If no tool calls, we're done
                if not assistant_message.tool_calls:
                    break
                
                # Process tool calls
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    tool_calls_made.append({"name": tool_name, "args": tool_args})
                    
                    logger.info(f"Executing tool: {tool_name}")
                    
                    try:
                        # Execute the appropriate tool
                        if tool_name == "navigate_to_url":
                            result = await self.playwright_navigate(tool_args["url"])
                        elif tool_name == "click_element":
                            result = await self.playwright_click(
                                tool_args["selector"],
                                tool_args["page_url"]
                            )
                        elif tool_name == "fill_form":
                            result = await self.playwright_fill_form(
                                tool_args["page_url"],
                                tool_args["form_data"]
                            )
                        elif tool_name == "extract_data":
                            result = await self.playwright_extract_data(
                                tool_args["page_url"],
                                tool_args["selectors"]
                            )
                        elif tool_name == "get_console_logs":
                            result = await self.playwright_get_console_logs(tool_args["page_url"])
                        elif tool_name == "read_file":
                            result = await self.read_file(tool_args["file_path"])
                        elif tool_name == "list_files":
                            result = await self.list_files(
                                tool_args.get("directory", "."),
                                tool_args.get("pattern", "*")
                            )
                        elif tool_name == "analyze_and_report":
                            result = {"success": True, "report": tool_args}
                            collected_data["report"] = tool_args
                        else:
                            result = {"success": False, "error": f"Unknown tool: {tool_name}"}
                        
                        # Store results
                        if result.get("success"):
                            if "data" in result:
                                collected_data[f"{tool_name}_{len(collected_data)}"] = result["data"]
                            elif "content" in result:
                                collected_data[f"file_content_{len(collected_data)}"] = result["content"]
                            elif "files" in result:
                                collected_data[f"file_list_{len(collected_data)}"] = result["files"]
                        else:
                            errors.append(result.get("error", "Unknown error"))
                        
                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps(result)
                        })
                        
                    except Exception as e:
                        error_msg = f"Tool execution error: {str(e)}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": json.dumps({"success": False, "error": error_msg})
                        })
            
            # Add to chat history
            if self.chat_history:
                self.chat_history.add_message("user", task_prompt)
                self.chat_history.add_message("assistant", assistant_message.content or "")
            
            # Calculate metrics
            end_time = datetime.now()
            metrics = {
                "processing_time": (end_time - start_time).total_seconds(),
                "tool_calls_made": len(tool_calls_made),
                "errors_encountered": len(errors)
            }
            
            return TaskResult(
                success=len(errors) == 0,
                timestamp=start_time.isoformat(),
                url=request.url,
                task=request.task,
                data=collected_data,
                error="; ".join(errors) if errors else None,
                agent_analysis=assistant_message.content,
                metrics=metrics
            )
            
        except Exception as e:
            logger.error(f"Error processing task: {e}")
            return TaskResult(
                success=False,
                timestamp=start_time.isoformat(),
                url=request.url,
                task=request.task,
                error=str(e)
            )
    
    async def process_with_retry(self, request: WebRequest) -> TaskResult:
        """Process task with retry logic"""
        last_error = None
        
        for attempt in range(self.config.max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{self.config.max_retries}")
                result = await self.process_task(request)
                
                if result.success:
                    return result
                
                last_error = result.error
                
                if attempt < self.config.max_retries - 1:
                    logger.warning(f"Retrying in {self.config.retry_delay} seconds...")
                    await asyncio.sleep(self.config.retry_delay)
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(self.config.retry_delay)
        
        return TaskResult(
            success=False,
            timestamp=datetime.now().isoformat(),
            url=request.url,
            task=request.task,
            error=f"Failed after {self.config.max_retries} attempts. Last error: {last_error}"
        )


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='OpenAI Agent Tool for Web Interaction')
    parser.add_argument('--config', type=str, help='Path to configuration file')
    parser.add_argument('--url', type=str, help='Target URL')
    parser.add_argument('--task', type=str, help='Task description')
    parser.add_argument('--api-key', type=str, help='OpenAI API key')
    parser.add_argument('--model', type=str, default='gpt-4-turbo-preview', help='OpenAI model')
    parser.add_argument('--output', type=str, help='Output file for results')
    parser.add_argument('--extract', type=str, nargs='+', help='Fields to extract')
    parser.add_argument('--clear-history', action='store_true', help='Clear chat history')
    parser.add_argument('--no-headless', action='store_true', help='Run browser with UI (requires display)')
    parser.add_argument('--no-xvfb-wrapper', action='store_true', help='Disable automatic xvfb-run wrapper')
    
    args = parser.parse_args()
    
    # Load configuration
    if args.config:
        with open(args.config, 'r') as f:
            config_data = json.load(f)
            agent_config = AgentConfig(**config_data['agent'])
            web_request = WebRequest(**config_data['request'])
    else:
        # Use command line arguments
        api_key = args.api_key or os.getenv('OPENAI_API_KEY')
        if not api_key:
            parser.error('OpenAI API key required (--api-key or OPENAI_API_KEY env var)')
        
        if not args.url or not args.task:
            parser.error('--url and --task are required when not using --config')
        
        agent_config = AgentConfig(
            api_key=api_key,
            model=args.model,
            browser_headless=not args.no_headless  # Default True unless --no-headless is used
        )
        
        web_request = WebRequest(
            url=args.url,
            task=args.task,
            extract_fields=args.extract
        )
    
    # Override browser_headless if --no-headless is specified
    if args.no_headless:
        agent_config.browser_headless = False
    
    # Create agent
    async with OpenAIAgent(agent_config) as agent:
        # Clear history if requested
        if args.clear_history and agent.chat_history:
            agent.chat_history.clear()
            logger.info("Chat history cleared")
        
        # Process task
        logger.info(f"Processing task: {web_request.task}")
        result = await agent.process_with_retry(web_request)
        
        # Output results
        result_dict = asdict(result)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result_dict, f, indent=2)
            logger.info(f"Results saved to {args.output}")
        else:
            print(json.dumps(result_dict, indent=2))
        
        # Log summary
        if result.success:
            logger.info("Task completed successfully")
            if result.data:
                logger.info(f"Extracted data: {json.dumps(result.data, indent=2)}")
        else:
            logger.error(f"Task failed: {result.error}")


if __name__ == "__main__":
    import sys
    import subprocess
    import shutil
    
    # Check if we need to wrap with xvfb-run
    # This happens before argparse to avoid parsing twice
    if '--no-xvfb-wrapper' not in sys.argv and not os.environ.get('DISPLAY'):
        # Check if we're already running under xvfb-run
        if 'xvfb-run' not in ' '.join(sys.argv):
            # Check if xvfb-run is available
            if shutil.which('xvfb-run'):
                # Need to check if browser_headless is false
                # Quick parse to check config
                needs_xvfb = False
                
                if '--config' in sys.argv:
                    try:
                        config_idx = sys.argv.index('--config')
                        if config_idx + 1 < len(sys.argv):
                            config_path = sys.argv[config_idx + 1]
                            with open(config_path, 'r') as f:
                                config_data = json.load(f)
                                if config_data.get('agent', {}).get('browser_headless', True) is False:
                                    needs_xvfb = True
                    except:
                        pass
                
                # Check for --no-headless flag
                if '--no-headless' in sys.argv:
                    needs_xvfb = True
                
                if needs_xvfb:
                    logger.info("No display found and browser_headless=False. Re-launching with xvfb-run...")
                    # Re-run ourselves with xvfb-run
                    cmd = ['xvfb-run', '-a', sys.executable] + sys.argv
                    sys.exit(subprocess.call(cmd))
    
    asyncio.run(main())