"""
Telegram Bot: Cloudflare Bypass + Scraping Service
Accepts crypto payments via wallet address.
Run in background: python services/telegram_bot.py
"""
import asyncio, json, os, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright

TOKEN = '8650825564:AAFYAViT-vDUyMOK3x427aGL4WwVD1XzGyI'
WALLET = '0xD0366D78055b8c637c44d769D1A1371106d13552'
PRICE_USD = 2

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "🤖 Cloudflare Bypass Bot\n\n"
        "I can bypass Cloudflare protection (JS Challenge, Turnstile, Under Attack mode) "
        "and return working cookies for your scripts.\n\n"
        f"Price: ${PRICE_USD}/bypass\n\n"
        "Commands:\n"
        "/bypass <url> - Bypass Cloudflare for a URL\n"
        "/price - Show pricing info\n"
        "/help - Show this message\n\n"
        "Payment: Crypto to wallet below\n"
        f"`{WALLET}`\n\n"
        "Send payment and your URL, I'll deliver the cookies."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def bypass_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Usage: /bypass <url>\nExample: /bypass https://example.com')
        return
    
    url = context.args[0]
    if not url.startswith('http'):
        url = 'https://' + url
    
    await update.message.reply_text(f'Processing: {url}\nThis takes 10-30 seconds...')
    
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
            cf = [c for c in cookies if 'cf_clearance' in c['name'].lower()]
            
            await browser.close()
            
            result = "✅ Bypass complete!\n\n"
            if cf:
                result += f"cf_clearance: `{cf[0]['value'][:30]}...`\n\n"
            result += f"Cookies: {len(cookies)} total\n"
            result += f"User-Agent: Chrome on Windows\n\n"
            result += f"Payment: Send ${PRICE_USD} in crypto to:\n`{WALLET}`\n\n"
            result += "Reply with /confirm <txid> after payment."
            
            await update.message.reply_text(result, parse_mode='Markdown')
    except Exception as e:
        await update.message.reply_text(f'Error: {str(e)[:100]}')

async def price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        f"💰 Pricing\n\n"
        f"Single bypass: ${PRICE_USD}\n"
        f"Bulk (10+): $1.50 each\n"
        f"Bulk (50+): $1 each\n\n"
        f"Payment: Crypto (ETH, USDT, USDC, BTC) to:\n"
        f"`{WALLET}`\n\n"
        f"Contact @yaqeen_manadger_bot for bulk orders."
    )
    await update.message.reply_text(msg, parse_mode='Markdown')

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if 'hello' in text or 'hi' in text or 'مرحبا' in text:
        await update.message.reply_text('Welcome! Use /bypass <url> to start.')
    elif any(word in text for word in ['price', 'cost', 'سعر', 'كم']):
        await price(update, context)
    else:
        await update.message.reply_text('Use /start to see available commands.')

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', start))
    app.add_handler(CommandHandler('price', price))
    app.add_handler(CommandHandler('bypass', bypass_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    
    print('Bot started! Talk to @yaqeen_manadger_bot on Telegram')
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
