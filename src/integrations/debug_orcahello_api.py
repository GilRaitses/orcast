"""
Debug OrcaHello API to understand actual endpoint structure
"""

import asyncio
import aiohttp
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_orcahello_api():
    """Debug the actual OrcaHello API responses"""
    
    base_url = "https://aifororcas.azurewebsites.net"
    
    async with aiohttp.ClientSession() as session:
        
        print("🔍 Debugging OrcaHello API Structure...")
        
        # Test 1: Root endpoint
        print("\n1. Testing root endpoint...")
        try:
            async with session.get(base_url) as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                text = await response.text()
                print(f"Response length: {len(text)} chars")
                if 'api' in text.lower():
                    print("✅ Contains 'api' references")
                if 'swagger' in text.lower():
                    print("✅ Contains 'swagger' references")
                if 'detections' in text.lower():
                    print("✅ Contains 'detections' references")
                print(f"First 500 chars:\n{text[:500]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 2: Try /api endpoint
        print("\n2. Testing /api endpoint...")
        try:
            async with session.get(f"{base_url}/api") as response:
                print(f"Status: {response.status}")
                print(f"Content-Type: {response.headers.get('content-type')}")
                text = await response.text()
                print(f"Response length: {len(text)} chars")
                print(f"First 500 chars:\n{text[:500]}...")
        except Exception as e:
            print(f"Error: {e}")
        
        # Test 3: Try swagger endpoint
        print("\n3. Testing swagger endpoint...")
        swagger_endpoints = [
            "/swagger",
            "/swagger/index.html",
            "/api/swagger",
            "/swagger/v1/swagger.json"
        ]
        
        for endpoint in swagger_endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    print(f"\n{endpoint}: Status {response.status}")
                    if response.status == 200:
                        content_type = response.headers.get('content-type', '')
                        print(f"Content-Type: {content_type}")
                        
                        if 'application/json' in content_type:
                            data = await response.json()
                            print(f"✅ JSON response with keys: {list(data.keys())}")
                            
                            # Look for API paths
                            if 'paths' in data:
                                paths = list(data['paths'].keys())
                                print(f"Available API paths: {paths[:10]}...")  # First 10
                        else:
                            text = await response.text()
                            print(f"Response length: {len(text)} chars")
                            if len(text) < 1000:
                                print(f"Response: {text}")
            except Exception as e:
                print(f"{endpoint}: Error - {e}")
        
        # Test 4: Try common API endpoints
        print("\n4. Testing common endpoints...")
        test_endpoints = [
            "/api/detections",
            "/api/hydrophones", 
            "/api/metrics",
            "/detections",
            "/hydrophones"
        ]
        
        for endpoint in test_endpoints:
            try:
                async with session.get(f"{base_url}{endpoint}") as response:
                    print(f"\n{endpoint}: Status {response.status}")
                    content_type = response.headers.get('content-type', '')
                    print(f"Content-Type: {content_type}")
                    
                    if response.status == 200:
                        if 'application/json' in content_type:
                            try:
                                data = await response.json()
                                print(f"✅ JSON response with keys: {list(data.keys()) if isinstance(data, dict) else f'Array with {len(data)} items'}")
                            except:
                                text = await response.text()
                                print(f"Failed to parse JSON, got: {text[:200]}...")
                        else:
                            text = await response.text()
                            print(f"HTML/Text response length: {len(text)}")
                            if 'detections' in text.lower() or 'api' in text.lower():
                                print("✅ Contains API-related content")
            except Exception as e:
                print(f"{endpoint}: Error - {e}")
        
        # Test 5: Check if it's a single-page app
        print("\n5. Checking for SPA structure...")
        try:
            async with session.get(base_url) as response:
                text = await response.text()
                
                # Look for common SPA patterns
                if 'react' in text.lower():
                    print("✅ Appears to be a React app")
                if 'angular' in text.lower():
                    print("✅ Appears to be an Angular app")
                if 'vue' in text.lower():
                    print("✅ Appears to be a Vue app")
                if 'api/' in text:
                    print("✅ Contains API path references")
                
                # Look for API base URLs in the HTML
                import re
                api_patterns = [
                    r'api["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'baseURL["\']?\s*:\s*["\']([^"\']+)["\']',
                    r'https?://[^"\']+/api[^"\']*'
                ]
                
                for pattern in api_patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        print(f"Found API references: {matches}")
        
        except Exception as e:
            print(f"Error checking SPA: {e}")

async def main():
    await debug_orcahello_api()

if __name__ == "__main__":
    asyncio.run(main()) 