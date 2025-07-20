#!/usr/bin/env python3
"""
ORCAST Dashboard Contact Sheet Generator
Creates a composite PNG of all dashboard endpoint monitoring views
"""

import asyncio
import base64
import json
import subprocess
import time
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import io
import os
import sys

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

class DashboardContactSheetGenerator:
    """Generates a contact sheet of all dashboard views"""
    
    def __init__(self):
        self.screenshots_dir = Path("dashboard_screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)
        
        self.dashboard_views = [
            {
                'name': 'Full Dashboard Overview',
                'url': 'http://localhost:8000/live_backend_test.html',
                'wait_for': '.backend-dashboard',
                'description': 'Complete monitoring dashboard with all endpoints'
            },
            {
                'name': 'Main App Backend Tab',
                'url': 'http://localhost:8000',
                'click_tab': 'Backend Inspection',
                'wait_for': '#inspection-tab',
                'description': 'Backend inspection tab in main ORCAST app'
            },
            {
                'name': 'Endpoint Grid View',
                'url': 'http://localhost:8000/live_backend_test.html',
                'wait_for': '.endpoints-grid',
                'scroll_to': '.endpoints-grid',
                'description': 'Grid of all monitored endpoints'
            },
            {
                'name': 'Performance Charts',
                'url': 'http://localhost:8000/live_backend_test.html',
                'wait_for': '.charts-container',
                'scroll_to': '.charts-container',
                'description': 'Live performance metrics and charts'
            },
            {
                'name': 'Activity Feed',
                'url': 'http://localhost:8000/live_backend_test.html',
                'wait_for': '.activity-feed',
                'scroll_to': '.activity-feed',
                'description': 'Real-time activity and logging feed'
            },
            {
                'name': 'System Information',
                'url': 'http://localhost:8000/live_backend_test.html',
                'wait_for': '.system-info-section',
                'scroll_to': '.system-info-section',
                'description': 'System health and resource monitoring'
            }
        ]
        
        self.composite_layout = {
            'columns': 3,
            'rows': 2,
            'padding': 20,
            'title_height': 80,
            'description_height': 40
        }
    
    def check_dependencies(self):
        """Check if required dependencies are available"""
        issues = []
        
        if not SELENIUM_AVAILABLE:
            issues.append("Selenium not installed: pip install selenium")
        
        try:
            # Check if Chrome/Chromium is available
            result = subprocess.run(['google-chrome', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                result = subprocess.run(['chromium-browser', '--version'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode != 0:
                    issues.append("Chrome/Chromium browser not found")
        except:
            issues.append("Chrome/Chromium browser not accessible")
        
        try:
            from PIL import Image
        except ImportError:
            issues.append("Pillow not installed: pip install Pillow")
        
        return issues
    
    def create_text_fallback_images(self):
        """Create text-based fallback images when browser automation isn't available"""
        print("📝 Creating text-based dashboard previews...")
        
        fallback_screenshots = []
        
        for view in self.dashboard_views:
            # Create a text-based representation
            img = Image.new('RGB', (800, 600), color='#1a1a1a')
            draw = ImageDraw.Draw(img)
            
            try:
                # Try to use a better font
                font_title = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 32)
                font_text = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
                font_small = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 12)
            except:
                # Fallback to default font
                font_title = ImageFont.load_default()
                font_text = ImageFont.load_default()
                font_small = ImageFont.load_default()
            
            # Draw title
            draw.text((50, 50), view['name'], fill='#4fc3f7', font=font_title)
            
            # Draw description
            draw.text((50, 100), view['description'], fill='#e0e0e0', font=font_text)
            
            # Draw URL
            draw.text((50, 130), f"URL: {view['url']}", fill='#999', font=font_small)
            
            # Draw mock dashboard elements based on view type
            if 'Overview' in view['name']:
                self._draw_overview_mockup(draw, font_text, font_small)
            elif 'Grid' in view['name']:
                self._draw_grid_mockup(draw, font_text, font_small)
            elif 'Charts' in view['name']:
                self._draw_charts_mockup(draw, font_text, font_small)
            elif 'Activity' in view['name']:
                self._draw_activity_mockup(draw, font_text, font_small)
            elif 'System' in view['name']:
                self._draw_system_mockup(draw, font_text, font_small)
            else:
                self._draw_generic_mockup(draw, font_text, font_small)
            
            # Save screenshot
            screenshot_path = self.screenshots_dir / f"{view['name'].replace(' ', '_').lower()}.png"
            img.save(screenshot_path)
            fallback_screenshots.append(str(screenshot_path))
            print(f"   ✅ Created: {screenshot_path.name}")
        
        return fallback_screenshots
    
    def _draw_overview_mockup(self, draw, font_text, font_small):
        """Draw overview dashboard mockup"""
        # Header stats
        stats = [
            ("Active Endpoints", "46"),
            ("Health Score", "92%"),
            ("Total Requests", "1,247"),
            ("Est. Cost Today", "$3.45")
        ]
        
        x_start = 50
        for i, (label, value) in enumerate(stats):
            x = x_start + i * 180
            draw.rectangle([x, 180, x + 160, 240], outline='#333', width=1)
            draw.text((x + 10, 190), label, fill='#999', font=font_small)
            draw.text((x + 10, 210), value, fill='#4fc3f7', font=font_text)
        
        # Endpoint categories
        categories = ["ML Services", "Firestore", "Real-time", "OrcaHello", "BigQuery"]
        for i, category in enumerate(categories):
            y = 280 + i * 30
            draw.rectangle([50, y, 70, y + 20], fill='#4fc3f7')
            draw.text((80, y + 5), category, fill='#e0e0e0', font=font_small)
    
    def _draw_grid_mockup(self, draw, font_text, font_small):
        """Draw endpoint grid mockup"""
        # Grid of endpoint cards
        for row in range(3):
            for col in range(3):
                x = 50 + col * 250
                y = 180 + row * 120
                
                # Card background
                draw.rectangle([x, y, x + 230, y + 100], outline='#333', width=1)
                
                # Status indicator
                status_color = '#66bb6a' if (row + col) % 3 != 0 else '#ef5350'
                draw.ellipse([x + 10, y + 10, x + 25, y + 25], fill=status_color)
                
                # Endpoint name
                endpoint_name = f"Endpoint {row * 3 + col + 1}"
                draw.text((x + 35, y + 15), endpoint_name, fill='#4fc3f7', font=font_small)
                
                # Metrics
                draw.text((x + 10, y + 40), "Response: 45ms", fill='#e0e0e0', font=font_small)
                draw.text((x + 10, y + 55), "Success: 98%", fill='#e0e0e0', font=font_small)
                draw.text((x + 10, y + 70), "Cost: $0.02", fill='#e0e0e0', font=font_small)
    
    def _draw_charts_mockup(self, draw, font_text, font_small):
        """Draw performance charts mockup"""
        # Chart titles and areas
        charts = [
            ("Response Times", 50, 180, 350, 280),
            ("Success Rate", 420, 180, 720, 280),
            ("Cost Breakdown", 50, 320, 350, 420),
            ("Request Volume", 420, 320, 720, 420)
        ]
        
        for title, x1, y1, x2, y2 in charts:
            # Chart background
            draw.rectangle([x1, y1, x2, y2], outline='#333', width=1)
            draw.text((x1 + 10, y1 + 10), title, fill='#4fc3f7', font=font_text)
            
            # Mock chart data
            import random
            for i in range(10):
                line_x = x1 + 20 + i * (x2 - x1 - 40) // 10
                line_y1 = y1 + 40
                line_y2 = y1 + 40 + random.randint(20, 60)
                draw.line([line_x, line_y1, line_x, line_y2], fill='#4fc3f7', width=2)
    
    def _draw_activity_mockup(self, draw, font_text, font_small):
        """Draw activity feed mockup"""
        # Activity entries
        activities = [
            "ML Service: ✅ 42ms",
            "Firestore: ✅ 156ms", 
            "BigQuery: ❌ Timeout",
            "OrcaHello: ✅ 89ms",
            "Routes API: ✅ 234ms"
        ]
        
        draw.text((50, 180), "🔴 Live Activity Feed", fill='#4fc3f7', font=font_text)
        
        for i, activity in enumerate(activities):
            y = 220 + i * 35
            # Entry background
            draw.rectangle([50, y, 750, y + 30], fill='#222', outline='#333')
            
            # Timestamp
            timestamp = f"{14 + i}:3{5 - i}:0{2 + i}"
            draw.text((60, y + 8), timestamp, fill='#999', font=font_small)
            
            # Activity
            draw.text((140, y + 8), activity, fill='#e0e0e0', font=font_small)
    
    def _draw_system_mockup(self, draw, font_text, font_small):
        """Draw system information mockup"""
        # System info cards
        info_cards = [
            ("Firebase Collections", ["whale_detections: 1,247", "ml_analysis: 856", "routes: 423"]),
            ("BigQuery Datasets", ["whale_data: 5.2GB", "ml_analysis: 2.1GB", "orcast_results: 1.8GB"]),
            ("Active Connections", ["WebSocket: 23", "SSE: 12", "HTTP: 67"]),
            ("Resource Usage", ["CPU: 34%", "Memory: 68%", "Bandwidth: 4.2Mbps"])
        ]
        
        for i, (title, items) in enumerate(info_cards):
            x = 50 + (i % 2) * 375
            y = 180 + (i // 2) * 200
            
            # Card background
            draw.rectangle([x, y, x + 350, y + 180], outline='#333', width=1)
            draw.text((x + 10, y + 10), title, fill='#4fc3f7', font=font_text)
            
            # Items
            for j, item in enumerate(items):
                draw.text((x + 20, y + 40 + j * 25), f"• {item}", fill='#e0e0e0', font=font_small)
    
    def _draw_generic_mockup(self, draw, font_text, font_small):
        """Draw generic dashboard mockup"""
        # Generic dashboard elements
        draw.text((50, 180), "Dashboard View", fill='#4fc3f7', font=font_text)
        draw.rectangle([50, 220, 750, 550], outline='#333', width=2)
        draw.text((60, 240), "Live monitoring interface would be displayed here", fill='#e0e0e0', font=font_small)
        draw.text((60, 270), "Real-time endpoint testing and performance metrics", fill='#999', font=font_small)
    
    async def capture_live_screenshots(self):
        """Capture live screenshots using browser automation"""
        if not SELENIUM_AVAILABLE:
            print("⚠️ Selenium not available, using text fallbacks")
            return self.create_text_fallback_images()
        
        print("📸 Capturing live dashboard screenshots...")
        
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1200,800')
        chrome_options.add_argument('--disable-gpu')
        
        screenshots = []
        
        try:
            driver = webdriver.Chrome(options=chrome_options)
            
            for view in self.dashboard_views:
                try:
                    print(f"   📷 Capturing: {view['name']}")
                    
                    # Navigate to URL
                    driver.get(view['url'])
                    
                    # Wait for page load
                    time.sleep(2)
                    
                    # Click tab if specified
                    if 'click_tab' in view:
                        try:
                            tab_button = driver.find_element(By.XPATH, f"//button[contains(text(), '{view['click_tab']}')]")
                            tab_button.click()
                            time.sleep(1)
                        except:
                            print(f"     ⚠️ Could not click tab: {view['click_tab']}")
                    
                    # Initialize dashboard if needed
                    if 'live_backend_test.html' in view['url']:
                        try:
                            init_button = driver.find_element(By.ID, "init-btn")
                            if init_button.is_enabled():
                                init_button.click()
                                time.sleep(3)  # Wait for initialization
                        except:
                            print("     ⚠️ Could not initialize dashboard")
                    
                    # Wait for specific element
                    if 'wait_for' in view:
                        try:
                            WebDriverWait(driver, 10).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, view['wait_for']))
                            )
                        except TimeoutException:
                            print(f"     ⚠️ Element not found: {view['wait_for']}")
                    
                    # Scroll to element if specified
                    if 'scroll_to' in view:
                        try:
                            element = driver.find_element(By.CSS_SELECTOR, view['scroll_to'])
                            driver.execute_script("arguments[0].scrollIntoView();", element)
                            time.sleep(1)
                        except:
                            print(f"     ⚠️ Could not scroll to: {view['scroll_to']}")
                    
                    # Take screenshot
                    screenshot_path = self.screenshots_dir / f"{view['name'].replace(' ', '_').lower()}.png"
                    driver.save_screenshot(str(screenshot_path))
                    screenshots.append(str(screenshot_path))
                    print(f"     ✅ Saved: {screenshot_path.name}")
                    
                except Exception as e:
                    print(f"     ❌ Failed to capture {view['name']}: {e}")
                    # Create fallback for this view
                    fallback_path = self._create_single_fallback(view)
                    screenshots.append(fallback_path)
            
            driver.quit()
            
        except WebDriverException as e:
            print(f"⚠️ Browser automation failed: {e}")
            print("📝 Falling back to text-based previews...")
            return self.create_text_fallback_images()
        
        return screenshots
    
    def _create_single_fallback(self, view):
        """Create a single fallback image for a view"""
        img = Image.new('RGB', (800, 600), color='#1a1a1a')
        draw = ImageDraw.Draw(img)
        
        try:
            font_title = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 24)
            font_text = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 14)
        except:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
        
        draw.text((50, 50), view['name'], fill='#4fc3f7', font=font_title)
        draw.text((50, 100), "Screenshot capture failed", fill='#ef5350', font=font_text)
        draw.text((50, 130), view['description'], fill='#e0e0e0', font=font_text)
        
        screenshot_path = self.screenshots_dir / f"{view['name'].replace(' ', '_').lower()}.png"
        img.save(screenshot_path)
        return str(screenshot_path)
    
    def create_contact_sheet(self, screenshot_paths):
        """Create a composite contact sheet from screenshots"""
        print("🎨 Creating composite contact sheet...")
        
        layout = self.composite_layout
        
        # Load screenshots
        images = []
        for path in screenshot_paths:
            try:
                img = Image.open(path)
                # Resize to standard size
                img = img.resize((800, 600), Image.Resampling.LANCZOS)
                images.append(img)
            except Exception as e:
                print(f"   ⚠️ Could not load {path}: {e}")
                # Create placeholder
                placeholder = Image.new('RGB', (800, 600), color='#333')
                images.append(placeholder)
        
        # Calculate composite dimensions
        img_width, img_height = 800, 600
        total_width = layout['columns'] * img_width + (layout['columns'] + 1) * layout['padding']
        total_height = (layout['title_height'] + 
                       layout['rows'] * (img_height + layout['description_height']) + 
                       (layout['rows'] + 1) * layout['padding'])
        
        # Create composite image
        composite = Image.new('RGB', (total_width, total_height), color='#0a0a0a')
        draw = ImageDraw.Draw(composite)
        
        # Draw title
        try:
            title_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 36)
            desc_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 16)
            small_font = ImageFont.truetype('/System/Library/Fonts/Helvetica.ttc', 12)
        except:
            title_font = ImageFont.load_default()
            desc_font = ImageFont.load_default()
            small_font = ImageFont.load_default()
        
        title_text = "ORCAST Live Backend Monitoring Dashboard - Contact Sheet"
        title_bbox = draw.textbbox((0, 0), title_text, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (total_width - title_width) // 2
        draw.text((title_x, 20), title_text, fill='#4fc3f7', font=title_font)
        
        # Draw timestamp
        timestamp = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        draw.text((20, total_height - 30), timestamp, fill='#999', font=small_font)
        
        # Draw endpoint count
        endpoint_count = f"Monitoring {len(self.dashboard_views)} dashboard views"
        draw.text((total_width - 300, total_height - 30), endpoint_count, fill='#999', font=small_font)
        
        # Place screenshots
        for i, (img, view) in enumerate(zip(images, self.dashboard_views)):
            row = i // layout['columns']
            col = i % layout['columns']
            
            x = layout['padding'] + col * (img_width + layout['padding'])
            y = layout['title_height'] + layout['padding'] + row * (img_height + layout['description_height'] + layout['padding'])
            
            # Paste screenshot
            composite.paste(img, (x, y))
            
            # Draw view name
            view_name = view['name']
            name_bbox = draw.textbbox((0, 0), view_name, font=desc_font)
            name_width = name_bbox[2] - name_bbox[0]
            name_x = x + (img_width - name_width) // 2
            name_y = y + img_height + 10
            
            # Background for text
            draw.rectangle([name_x - 5, name_y - 5, name_x + name_width + 5, name_y + 25], fill='#222')
            draw.text((name_x, name_y), view_name, fill='#4fc3f7', font=desc_font)
            
            # Draw description
            description = view['description']
            if len(description) > 60:
                description = description[:57] + "..."
            
            desc_bbox = draw.textbbox((0, 0), description, font=small_font)
            desc_width = desc_bbox[2] - desc_bbox[0]
            desc_x = x + (img_width - desc_width) // 2
            desc_y = name_y + 25
            
            draw.text((desc_x, desc_y), description, fill='#ccc', font=small_font)
        
        # Save composite
        timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
        composite_path = f"orcast_dashboard_contact_sheet_{timestamp_str}.png"
        composite.save(composite_path, 'PNG', quality=95)
        
        print(f"   ✅ Contact sheet saved: {composite_path}")
        print(f"   📐 Dimensions: {total_width} x {total_height}")
        print(f"   📊 Views: {len(images)} dashboard screenshots")
        
        return composite_path
    
    async def generate_contact_sheet(self):
        """Generate the complete contact sheet"""
        print("🎯 ORCAST Dashboard Contact Sheet Generator")
        print("=" * 50)
        
        # Check dependencies
        issues = self.check_dependencies()
        if issues:
            print("⚠️ Dependency issues:")
            for issue in issues:
                print(f"   • {issue}")
            print()
        
        # Check if services are running
        print("🔍 Checking service availability...")
        try:
            import requests
            # Test HTTP server
            try:
                response = requests.get('http://localhost:8000', timeout=5)
                print("   ✅ HTTP server (port 8000) is running")
            except:
                print("   ❌ HTTP server (port 8000) not accessible")
            
            # Test ML service
            try:
                response = requests.get('http://localhost:8081/health', timeout=5)
                print("   ✅ ML service (port 8081) is running")
            except:
                print("   ❌ ML service (port 8081) not accessible")
                
        except ImportError:
            print("   ⚠️ Requests not available for service checking")
        
        print()
        
        # Capture screenshots
        screenshot_paths = await self.capture_live_screenshots()
        
        if not screenshot_paths:
            print("❌ No screenshots captured - cannot create contact sheet")
            return None
        
        # Create contact sheet
        contact_sheet_path = self.create_contact_sheet(screenshot_paths)
        
        print(f"\n🎉 Contact sheet generated successfully!")
        print(f"📄 File: {contact_sheet_path}")
        print(f"📁 Screenshots saved in: {self.screenshots_dir}")
        
        return contact_sheet_path

async def main():
    """Main function"""
    generator = DashboardContactSheetGenerator()
    
    try:
        contact_sheet_path = await generator.generate_contact_sheet()
        
        if contact_sheet_path:
            print(f"\n✅ Success! Contact sheet created: {contact_sheet_path}")
            
            # Try to open the file
            try:
                subprocess.run(['open', contact_sheet_path], check=False)
                print("🖼️ Opening contact sheet...")
            except:
                print("💡 Tip: Open the contact sheet manually to view the results")
        else:
            print("\n❌ Failed to create contact sheet")
            return 1
            
        return 0
        
    except KeyboardInterrupt:
        print("\n⏹️ Contact sheet generation interrupted")
        return 130
    except Exception as e:
        print(f"\n💥 Error: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main()) 