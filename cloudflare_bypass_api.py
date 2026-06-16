"""
Cloudflare Bypass API - Sellable service
Run as: python services/cloudflare_bypass_api.py
Then clients POST to http://localhost:8888/bypass with {"url": "https://example.com"}
Payment: Crypto to 0xD0366D78055b8c637c44d769D1A1371106d13552
"""
import asyncio, json, hmac, hashlib, time
from http.server import HTTPServer, BaseHTTPRequestHandler
from playwright.async_api import async_playwright

API_KEY = 'cf_bypass_pro_2026'
WALLET = '0xD0366D78055b8c637c44d769D1A1371106d13552'
PRICE_USD = 2  # $2 per bypass

class BypassHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                'service': 'Cloudflare Bypass API',
                'price': f'${PRICE_USD}/bypass',
                'wallet': WALLET,
                'usage': 'POST /bypass with {"url": "https://target.com"}',
                'auth': 'Header X-API-Key: cf_bypass_pro_2026',
                'example': 'curl -X POST http://localhost:8888/bypass -H "X-API-Key: cf_bypass_pro_2026" -d \'{"url":"https://example.com"}\''
            }, indent=2).encode())
            return
        
        self.send_error(404)

    def do_POST(self):
        if self.path != '/bypass':
            self.send_error(404)
            return
        
        # Auth check
        key = self.headers.get('X-API-Key', '')
        if key != API_KEY:
            self.send_error(401, json.dumps({'error': 'Invalid API key. Pay to: ' + WALLET}))
            return
        
        # Get URL
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length) if length else b'{}'
        try:
            data = json.loads(body)
            url = data.get('url', '')
        except:
            self.send_error(400, json.dumps({'error': 'Invalid JSON'}))
            return
        
        if not url:
            self.send_error(400, json.dumps({'error': 'Missing url field'}))
            return
        
        # Process bypass asynchronously
        result = asyncio.run(self.bypass_cloudflare(url))
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(result, indent=2).encode())
    
    async def bypass_cloudflare(self, url):
        print(f'[BYPASS] Processing: {url[:60]}')
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                ctx = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                )
                page = await ctx.new_page()
                await page.goto(url, timeout=30000, wait_until='networkidle')
                await page.wait_for_timeout(3000)
                
                cookies = await ctx.cookies()
                cf_cookies = [c for c in cookies if 'cf_clearance' in c['name'].lower()]
                
                await browser.close()
                
                if cf_cookies:
                    return {
                        'success': True,
                        'cf_clearance': cf_cookies[0]['value'],
                        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'cookies': {c['name']: c['value'] for c in cookies},
                        'price': PRICE_USD,
                        'wallet': WALLET,
                    }
                else:
                    return {
                        'success': True,
                        'note': 'No cf_clearance cookie found (site might not use Cloudflare)',
                        'cookies': {c['name']: c['value'] for c in cookies},
                    }
        except Exception as e:
            return {'success': False, 'error': str(e)}

def run():
    port = 8888
    server = HTTPServer(('0.0.0.0', port), BypassHandler)
    print(f'Cloudflare Bypass API running on http://localhost:{port}')
    print(f'Wallet for payments: {WALLET}')
    print(f'Price: ${PRICE_USD}/bypass')
    print(f'Example: curl -X POST http://localhost:{port}/bypass -H "X-API-Key: {API_KEY}" -d \'{{"url":"https://example.com"}}\'')
    server.serve_forever()

if __name__ == '__main__':
    run()
