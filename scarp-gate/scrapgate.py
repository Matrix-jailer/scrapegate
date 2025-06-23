# @Gen666Z

import sys
import os
import re
import time
import logging
import telegram
import random
import socket
import aiohttp
import tldextract
import asyncio
import json
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest, NetworkError, TimedOut
from tqdm import tqdm
from colorama import Fore, Style
import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy_splash import SplashRequest

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Remove Playwright lock file as it's no longer needed
LOCK_FILE = ".playwright_installed.lock"
if os.path.exists(LOCK_FILE):
    os.remove(LOCK_FILE)

# Color definitions
merah = Fore.LIGHTRED_EX
putih = Fore.LIGHTWHITE_EX
hijau = Fore.LIGHTGREEN_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
reset = Style.RESET_ALL

# Telegram Bot Configurations
BOT_TOKEN = os.getenv("BOT_TOKEN", "1416628944:AAFeWmd-vRW-B4rft_zznoNcX26j6gei_Ys")
FORWARD_CHANNEL_ID = "@mddj77273jdjdjd838383"
REGISTERED_USERS_FILE = "registered_users.json"
ADMIN_ACCESS_FILE = "adminaccess.json"
CREDIT_CODES_FILE = "creditcodes.json"
BAN_USERS_FILE = "banusers.json"
BOARD_MESSAGE_FILE = "boardmessage.json"

# Extended Lists
RELATED_PAGES = [
    "/", "/checkout", "/buynow", "/cart", "/payment", "/order",
    "/purchase", "/subscribe", "/confirm", "/billing", "/pay",
    "/transactions", "/order-summary", "/complete", "/shop", "/buy",
    "/proceed-to-checkout", "/payment-gateway", "/secure-checkout",
    "/order-confirmation", "/payment-processing", "/finalize-order"
]

PAYMENT_GATEWAYS = [
    "stripe", "paypal", "paytm", "razorpay", "square", "adyen", "braintree",
    "authorize.net", "klarna", "checkout.com", "shopify_payments", "worldpay",
    "2checkout", "amazon_pay", "apple_pay", "google_pay", "mollie", "opayo", "paddle"
]

CAPTCHA_PATTERNS = [
    r"g-recaptcha", r"data-sitekey", r"captcha", r"hcaptcha", r"protected by cloudflare",
    r"turnstile", r"arkose-labs", r"funcaptcha", r"geetest", r"recaptcha/api.js"
]

PLATFORM_KEYWORDS = {
    "woocommerce": "WooCommerce",
    "shopify": "Shopify",
    "magento": "Magento",
    "bigcommerce": "BigCommerce",
    "prestashop": "PrestaShop",
    "opencart": "OpenCart",
    "wix": "Wix",
    "squarespace": "Squarespace"
}

CARD_KEYWORDS = [
    "visa", "mastercard", "amex", "discover", "diners", "jcb", "unionpay",
    "maestro", "mir", "rupay", "cartasi", "hipercard"
]

THREE_D_SECURE_KEYWORDS = [
    "three_d_secure", "3dsecure", "acs", "acs_url", "acsurl", "redirect",
    "secure-auth", "challenge", "3ds", "3ds1", "3ds2", "tds", "tdsecure",
    "3d-secure", "three-d", "3dcheck", "3d-auth", "three-ds",
    "stripe.com/3ds", "m.stripe.network", "hooks.stripe.com/3ds",
    "paddle_frame", "paddlejs", "secure.paddle.com", "buy.paddle.com",
    "idcheck", "garanti.com.tr", "adyen.com/hpp", "adyen.com/checkout",
    "adyenpayments.com/3ds", "auth.razorpay.com", "razorpay.com/3ds",
    "secure.razorpay.com", "3ds.braintreegateway.com", "verify.3ds",
    "checkout.com/3ds", "checkout.com/challenge", "3ds.paypal.com",
    "authentication.klarna.com", "secure.klarna.com/3ds"
]

GATEWAY_KEYWORDS = {
    "stripe": ["stripe.com", "api.stripe.com/v1", "client_secret", "pi_", "stripe.js", "three_d_secure"],
    "paypal": ["paypal.com", "www.paypal.com", "paypal-sdk", "three_d_secure"],
    "braintree": ["braintreepayments.com", "client_token", "braintree.js", "three_d_secure"],
    "adyen": ["checkoutshopper-live.adyen.com", "adyen.js", "three_d_secure"],
    "authorize.net": ["authorize.net/gateway/transact.dll", "anet.js", "three_d_secure"],
    "square": ["squareup.com", "square.js", "three_d_secure"],
    "klarna": ["klarna.com", "klarna_checkout", "three_d_secure"],
    "checkout.com": ["checkout.com", "cko.js", "three_d_secure"],
    "razorpay": ["checkout.razorpay.com", "razorpay.js", "three_d_secure"],
    "paytm": ["securegw.paytm.in", "paytm.js", "three_d_secure"],
    "shopify_payments": ["shopify_payments", "checkout.shopify.com", "three_d_secure"],
    "worldpay": ["worldpay.com", "worldpay.js", "three_d_secure"],
    "2checkout": ["2checkout.com", "2co.js", "three_d_secure"],
    "amazon_pay": ["amazonpay.com", "amazonpay.js", "three_d_secure"],
    "apple_pay": ["apple.com", "apple-pay.js", "three_d_secure"],
    "google_pay": ["google.com", "googlepay.js", "three_d_secure"],
    "mollie": ["mollie.com", "mollie.js", "three_d_secure"],
    "opayo": ["opayo.com", "opayo.js", "three_d_secure"],
    "paddle": ["checkout.paddle.com", "checkout-service.paddle.com", "paddle.com/checkout", "paddle_button.js", "paddle.js"]
}

# Time conversion dictionary
TIME_CONVERSIONS = {
    "minute": 60,
    "hour": 3600,
    "day": 86400,
    "week": 604800,
    "year": 31536000
}

# JSON Utilities
def load_json(file_path):
    if not os.path.exists(file_path):
        logger.warning(f"File {file_path} does not exist, returning empty dict")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File {file_path} is empty, returning empty dict")
                return {}
            data = json.loads(content)
            if not isinstance(data, dict):
                logger.error(f"Invalid JSON in {file_path}, expected dict but got {type(data)}")
                return {}
            return data
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}

def save_json(file_path, data):
    with open(file_path, "w") as f:
        json.dump(data, f)

def load_registered_users():
    return load_json(REGISTERED_USERS_FILE)

def save_registered_users(users_data):
    save_json(REGISTERED_USERS_FILE, users_data)

def is_user_registered(user_id):
    registered = load_registered_users()
    return str(user_id) in registered

def register_user(user_id, update):
    registered = load_registered_users()
    if str(user_id) not in registered:
        registered[str(user_id)] = {
            "credits": 10,
            "join_date": time.time(),
            "username": f"@{update.effective_user.username}" if update.effective_user.username else f"User_{user_id}"
        }
        save_registered_users(registered)

def get_user_credits(user_id):
    registered = load_registered_users()
    return registered.get(str(user_id), {}).get("credits", 0)

def deduct_credit(user_id):
    registered = load_registered_users()
    if str(user_id) in registered and registered[str(user_id)]["credits"] > 0:
        registered[str(user_id)]["credits"] -= 1
        save_registered_users(registered)
        return True
    return False

def add_credit(user_id, amount, update):
    registered = load_registered_users()
    if str(user_id) in registered:
        registered[str(user_id)]["credits"] += amount
        save_registered_users(registered)
    else:
        registered[str(user_id)] = {
            "credits": amount,
            "join_date": time.time(),
            "username": f"@{update.effective_user.username}" if update.effective_user.username else f"User_{user_id}"
        }
        save_registered_users(registered)

def load_admin_access():
    return load_json(ADMIN_ACCESS_FILE)

def save_admin_access(data):
    save_json(ADMIN_ACCESS_FILE, data)

def is_admin(user_id):
    admin_access = load_admin_access()
    current_time = time.time()
    if str(user_id) in admin_access and admin_access[str(user_id)] > current_time:
        return True
    if str(user_id) in admin_access and admin_access[str(user_id)] <= current_time:
        del admin_access[str(user_id)]
        save_admin_access(admin_access)
    return False

def add_admin_access(user_id):
    admin_access = load_admin_access()
    admin_access[str(user_id)] = time.time() + 300  # 5 minutes expiration
    save_admin_access(admin_access)
    asyncio.create_task(remove_admin_access_after_delay(user_id))

async def remove_admin_access_after_delay(user_id):
    await asyncio.sleep(300)  # 5 minutes
    admin_access = load_admin_access()
    if str(user_id) in admin_access:
        del admin_access[str(user_id)]
        save_admin_access(admin_access)

def load_credit_codes():
    return load_json(CREDIT_CODES_FILE)

def save_credit_codes(data):
    save_json(CREDIT_CODES_FILE, data)

def load_ban_users():
    return load_json(BAN_USERS_FILE)

def save_ban_users(data):
    save_json(BAN_USERS_FILE, data)

def is_user_banned(user_id):
    ban_users = load_ban_users()
    current_time = time.time()
    if str(user_id) in ban_users:
        ban_info = ban_users[str(user_id)]
        if ban_info.get("expires", 0) > current_time or ban_info.get("expires") == "permanent":
            return True
        del ban_users[str(user_id)]
        save_ban_users(ban_users)
    return False

def ban_user(user_id, reason, time_period):
    ban_users = load_ban_users()
    credits = get_user_credits(user_id)
    if time_period == "permanent":
        expires = "permanent"
    else:
        try:
            time_value, time_unit = int(time_period[:-len(time_period.partition(time_period[-1])[0]) - 1]), time_period[-1]
            expires = time.time() + (time_value * TIME_CONVERSIONS.get(time_unit, 0))
        except (ValueError, IndexError):
            expires = time.time() + 86400  # Default to 1 day if invalid format
    ban_users[str(user_id)] = {
        "id": str(user_id),
        "date": time.strftime("%Y-%m-%d %H:%M:%S"),
        "reason": reason,
        "credits_last_time": credits,
        "expires": expires
    }
    save_ban_users(ban_users)

def unban_user(user_id):
    ban_users = load_ban_users()
    if str(user_id) in ban_users:
        del ban_users[str(user_id)]
        save_ban_users(ban_users)

def load_board_message():
    data = load_json(BOARD_MESSAGE_FILE)
    return data.get("message", "🌟 *No message set!*").strip() if data.get("message") else "🌟 *No message set!*"

# URL Validation
async def validate_url(url):
    domain = tldextract.extract(url).top_domain_under_public_suffix
    if not domain:
        return False, "Invalid URL: No valid domain found."

    try:
        socket.gethostbyname(domain)
    except socket.gaierror:
        return False, "Unresolvable DNS: Cannot connect to host."

    try:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, allow_redirects=True, timeout=5) as resp:
                if resp.status == 429:
                    return False, "Rate limited (429). Try again later."
                if resp.status >= 400:
                    return False, f"HTTP Error: Status {resp.status}."
                cloudflare = "cloudflare" in dict(resp.headers).get("server", "").lower()
                if cloudflare:
                    return False, "Cloudflare protection detected. May not be bypassable."
                return True, "URL is accessible."
    except aiohttp.ClientError as e:
        return False, f"Connection error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

# Scrapy Spider for Scanning
class PaymentGatewaySpider(scrapy.Spider):
    name = 'payment_gateway_spider'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'SPLASH_URL': 'https://splash-service-yz8h.onrender.com:8050',
        'DOWNLOADER_MIDDLEWARES': {
            'scrapy_splash.SplashCookiesMiddleware': 723,
            'scrapy_splash.SplashMiddleware': 725,
            'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
        },
        'SPIDER_MIDDLEWARES': {
            'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
        },
        'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],
        'DOWNLOAD_TIMEOUT': 20,
        'LOG_LEVEL': 'INFO',
    }

    def __init__(self, base_url, progress_callback=None, total_pages=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [base_url.rstrip("/") + page for page in RELATED_PAGES]
        self.results = {
            "payment_gateways": set(),
            "captcha": False,
            "cloudflare": False,
            "graphql": False,
            "platforms": set(),
            "card_support": set(),
            "is_3d_secure": False,
        }
        self.progress_callback = progress_callback
        self.total_pages = total_pages
        self.completed_pages = 0

    def start_requests(self):
        for url in self.start_urls:
            yield SplashRequest(
                url,
                self.parse,
                args={'wait': 2.0},
                headers={'Accept-Language': 'en-US,en;q=0.9'},
            )

    def parse(self, response):
        self.completed_pages += 1
        if self.progress_callback:
            self.progress_callback(self.completed_pages, self.total_pages)

        self.results["cloudflare"] = self.results["cloudflare"] or (
            "cloudflare" in response.headers.get("server", "").lower()
        )

        soup = BeautifulSoup(response.text, 'html.parser')
        html_content = response.text.lower()

        for gateway in PAYMENT_GATEWAYS:
            if gateway in html_content:
                self.results["payment_gateways"].add(gateway.capitalize())
                if any(kw in html_content for kw in GATEWAY_KEYWORDS.get(gateway, []) if kw in THREE_D_SECURE_KEYWORDS):
                    self.results["is_3d_secure"] = True

        if any(re.search(pattern, html_content, re.IGNORECASE) for pattern in CAPTCHA_PATTERNS):
            self.results["captcha"] = True

        self.results["graphql"] = self.results["graphql"] or ("graphql" in html_content)

        for keyword, name in PLATFORM_KEYWORDS.items():
            if keyword in html_content:
                self.results["platforms"].add(name)

        for card in CARD_KEYWORDS:
            if card in html_content:
                self.results["card_support"].add(card.capitalize())

        iframes = soup.find_all('iframe')
        for iframe in iframes:
            frame_url = iframe.get('src', '').lower()
            if any(kw in frame_url for kw in THREE_D_SECURE_KEYWORDS):
                self.results["is_3d_secure"] = True
            if frame_url:
                yield SplashRequest(
                    frame_url,
                    self.parse_iframe,
                    args={'wait': 2.0},
                    meta={'dont_merge_cookies': True},
                )

    def parse_iframe(self, response):
        html_content = response.text.lower()
        for gateway in PAYMENT_GATEWAYS:
            if gateway in html_content:
                self.results["payment_gateways"].add(gateway.capitalize())
                if any(kw in html_content for kw in GATEWAY_KEYWORDS.get(gateway, []) if kw in THREE_D_SECURE_KEYWORDS):
                    self.results["is_3d_secure"] = True
        if any(re.search(pattern, html_content, re.IGNORECASE) for pattern in CAPTCHA_PATTERNS):
            self.results["captcha"] = True
        self.results["graphql"] = self.results["graphql"] or ("graphql" in html_content)
        for keyword, name in PLATFORM_KEYWORDS.items():
            if keyword in html_content:
                self.results["platforms"].add(name)
        for card in CARD_KEYWORDS:
            if card in html_content:
                self.results["card_support"].add(card.capitalize())

# Scan Site Function
async def scan_site_parallel(base_url, progress_callback=None):
    results_container = {}
    process = CrawlerProcess({
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36',
        'SPLASH_URL': 'https://splash-service-yz8h.onrender.com',
        'LOG_LEVEL': 'INFO',
    })

    class WrappedSpider(PaymentGatewaySpider):
        def closed(self, reason):
            results_container["results"] = self.results
            logger.info(f"Spider closed with reason: {reason}")

    try:
        process.crawl(
            WrappedSpider,
            base_url=base_url,
            progress_callback=progress_callback,
            total_pages=len(RELATED_PAGES)
        )
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, process.start)
    except Exception as e:
        logger.error(f"Error running spider: {e}")
    return results_container.get("results", {
        "payment_gateways": set(),
        "captcha": False,
        "cloudflare": False,
        "graphql": False,
        "platforms": set(),
        "card_support": set(),
        "is_3d_secure": False,
    })

async def show_progress_bar(update: Update, context: ContextTypes.DEFAULT_TYPE, total_pages):
    message = await update.message.reply_text("**🌐 Checking website... [⬜⬜⬜⬜⬜] 0%**", parse_mode=ParseMode.MARKDOWN)
    bar_length = 5
    last_percent = -1

    def update_progress(current, total):
        nonlocal last_percent
        current_percent = min(int((current / total) * 100), 100)
        if current_percent > last_percent:
            filled = int((current_percent / 100) * bar_length)
            progress = "🟧" * filled + "⬜" * (bar_length - filled) if current_percent < 100 else "🟩" * bar_length
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(message.edit_text(
                    f"**🌐 Checking website... [{progress}] {current_percent}%**",
                    parse_mode=ParseMode.MARKDOWN
                ))
            except telegram.error.BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Failed to update progress bar: {e}")
            except telegram.error.TimedOut:
                logger.warning("Telegram API timed out during progress update")
            last_percent = current_percent

    return message, update_progress

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_link = f"[@{user.username}](tg://user?id={user.id})" if user.username else f"User_{user.id}"
    keyboard = [
        [{"text": "📝 Register", "callback_data": "register"}, {"text": "🔍 Check URL", "callback_data": "checkurl"}],
        [{"text": "💰 Credits", "callback_data": "credits"}, {"text": "👨‍💼 Admin", "callback_data": "admin"}]
    ]
    reply_markup = create_inline_keyboard(keyboard)
    is_registered = is_user_registered(user.id)
    features = (
        "  - ✅ *Registered Successfully*\n"
        if is_registered else "  - ✅ *Register to get started*\n"
    ) + "  - 🔍 *Check URLs (1 credit per check)*\n  - 💰 *View your credits*"
    welcome_text = (
        f"🌟 **Welcome to Payment Gateway Scanner, {user_link}!** 🌟\n"
        f"🔧 **Analyze websites with ease!** Check payment gateways, platforms, 3D Secure, and more.\n"
        f"💡 **Features:**\n{features}\n"
        f"👉 **Click a button below to begin!** ⚡\n\n"
        f"⚡ **Contact: @Gen666Z** ⚡\n"
    )
    if update.message:
        message = await update.message.reply_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
        context.user_data["message_id"] = message.message_id
    else:
        await update.callback_query.edit_message_text(welcome_text, parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    keyboard = [
        [{"text": "📝 Register", "callback_data": "register"}, {"text": "🔍 Check URL", "callback_data": "checkurl"}],
        [{"text": "💰 Credits", "callback_data": "credits"}, {"text": "👨‍💼 Admin", "callback_data": "admin"}],
        [{"text": "🔙 Back", "callback_data": "back"}]
    ]
    reply_markup = create_inline_keyboard(keyboard)

    if action := query.data:
        if action == "register":
            if is_user_banned(user_id):
                await query.edit_message_text(
                    "**🚫 You are banned!**\n"
                    "📩 *Try to contact Owner to get Unban: @Gen666Z*\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=create_inline_keyboard([[{"text": "👨‍💼 Admin", "callback_data": "admin"}]])
                )
            elif is_user_registered(user_id):
                await query.edit_message_text(
                    "**🚫 You are already registered!**\n"
                    f"💰 **Credits: {get_user_credits(user_id)}**\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                register_user(user_id, update)
                await query.edit_message_text(
                    "**✅ Registration Successful!**\n"
                    f"💰 **You received 10 credits! Current: 10**\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        elif action == "checkurl":
            credits = get_user_credits(user_id)
            if is_user_banned(user_id):
                await query.edit_message_text(
                    "**🚫 You are banned!**\n"
                    "📩 *Try to contact Owner to get Unban: @Gen666Z*\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=create_inline_keyboard([[{"text": "👨‍💼 Admin", "callback_data": "admin"}]])
                )
            elif not is_user_registered(user_id):
                await query.edit_message_text(
                    "**🚫 Please register first!**\n"
                    "📝 **Click 'Register' to get started.**\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            elif credits <= 0:
                await query.edit_message_text(
                    "**💸 Out of Credits!**\n"
                    "🔴 **Your credits have run out!**\n"
                    "📩 **Contact Admin to recharge: @Gen666Z**\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    "**🔍 Enter URL to Check**\n"
                    f"💰 **Credits: {credits} (1 credit will be deducted)**\n"
                    "📝 **Send /url <url> (e.g., /url https://example.com)**\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
                context.user_data["awaiting_url"] = True
        elif action == "credits":
            credits = get_user_credits(user_id)
            if is_user_banned(user_id):
                await query.edit_message_text(
                    "**🚫 You are banned!**\n"
                    "📩 *Try to contact Owner to get Unban: @Gen666Z*\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=create_inline_keyboard([[{"text": "👨‍💼 Admin", "callback_data": "admin"}]])
                )
            elif not is_user_registered(user_id):
                await query.edit_message_text(
                    "**🚫 Please register first!**\n"
                    "📝 **Click 'Register' to get started.**\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
            else:
                await query.edit_message_text(
                    f"**💰 Your Credits**\n"
                    f"🔢 **Available: {credits} credits**\n"
                    f"🔄 **1 credit per URL check**\n"
                    f"🔧 **Contact admin to recharge if needed!**\n\n",
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=reply_markup
                )
        elif action == "admin":
            await query.edit_message_text(
                "**👨‍💼 Contact Admin**\n"
                "📩 **Reach out to @Gen666Z for support or recharges!**\n\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif action == "back":
            await start(update, context)

async def url_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.user_data.get("awaiting_url", False):
        return
    context.user_data["awaiting_url"] = False

    raw_text = update.message.text.strip()
    just_args = raw_text[len("/url"):].strip()
    if not just_args:
        await update.message.reply_text("**🚫 Usage: /url <url> (e.g., /url https://example.com)**", parse_mode=ParseMode.MARKDOWN)
        return

    url = just_args
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    if is_user_banned(user_id):
        await update.message.reply_text(
            "**🚫 You are banned!**\n"
            "📩 **Try to contact Owner to get Unban: @Gen666Z**\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_inline_keyboard([[{"text": "👨‍💼 Admin", "callback_data": "admin"}]])
        )
        return
    if not is_user_registered(user_id):
        await update.message.reply_text(
            "**🚫 Please register first!**\n"
            "📝 **Click 'Register' in the menu to get started.**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    if not deduct_credit(user_id):
        await update.message.reply_text(
            "**💸 Out of Credits!**\n"
            "🔴 **Your credits have run out!**\n"
            "📩 **Contact Admin to recharge: @Gen666Z**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    is_valid, message = await validate_url(url)
    if not is_valid:
        await update.message.reply_text(
            f"**❌ Invalid URL!**\n{message}\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_inline_keyboard([[{"text": "🔙 Back", "callback_data": "back"}]])
        )
        return

    max_attempts = 3
    attempt = 0

    while attempt < max_attempts:
        try:
            start_time = time.time()
            progress_message, update_progress = await show_progress_bar(update, context, len(RELATED_PAGES))
            results = await scan_site_parallel(url, progress_callback=update_progress)
            processing_time = time.time() - start_time

            user = update.effective_user
            user_link = f"[@{user.username}](tg://user?id={user.id})" if user.username else f"User_{user.id}"
            credits_left = get_user_credits(user_id)
            gateways = ', '.join(sorted(results['payment_gateways'])) if results['payment_gateways'] else 'None found'
            platforms = ', '.join(sorted(results['platforms'])) if results['platforms'] else 'Unknown'
            cards = ', '.join(sorted(results['card_support'])) if results['card_support'] else 'None found'
            is_3d_secure_text = f"🔐 **3D Secure:** {'ENABLED' if results['is_3d_secure'] else 'DISABLED'}\n"

            result_text = (
                f"**🟢 Scan Results for {url}**\n"
                f"**⏱️ Time Taken:** {round(processing_time, 2)} seconds\n"
                f"**💳 Payment Gateways:** {gateways.replace('<', '<').replace('>', '>')}\n"
                f"**🔒 Captcha:** {'Found ✅' if results['captcha'] else 'Not Found 🔥'}\n"
                f"**☁️ Cloudflare:** {'Found ✅' if results['cloudflare'] else 'Not Found 🔥'}\n"
                f"**📊 GraphQL:** {results['graphql']}\n"
                f"**🏬 Platforms:** {platforms.replace('<', '<').replace('>', '>')}\n"
                f"**💵 Card Support:** {cards.replace('<', '<').replace('>', '>')}\n"
                f"{is_3d_secure_text}"
                f"**💰 Credit Left:** {credits_left}\n"
                f"**🆔 Scanned by:** {user_link}\n"
            )
            try:
                await progress_message.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
            except telegram.error.BadRequest as e:
                if "Message is not modified" not in str(e):
                    logger.error(f"Failed to edit final message: {e}")
            except telegram.error.TimedOut:
                logger.warning("Telegram API timed out during final message update")
                await update.message.reply_text(result_text, parse_mode=ParseMode.MARKDOWN)
            try:
                await context.bot.send_message(
                    chat_id=FORWARD_CHANNEL_ID,
                    text=result_text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_notification=True
                )
            except BadRequest as e:
                logger.debug(f"Could not forward to channel {FORWARD_CHANNEL_ID}: {e}")
            except Exception as e:
                logger.debug(f"Error forwarding to channel: {e}")
            break
        except Exception as e:
            logger.error(f"Error checking URL {url}: {e}")
            attempt += 1
            if attempt == max_attempts:
                try:
                    await progress_message.edit_text(
                        f"**❌ Error checking URL: {e}**\n\n",
                        parse_mode=ParseMode.MARKDOWN
                    )
                except telegram.error.BadRequest as e:
                    if "Message is not modified" not in str(e):
                        logger.error(f"Failed to edit error message: {e}")
                except telegram.error.TimedOut:
                    logger.warning("Telegram API timed out during error message update")
                    await update.message.reply_text(
                        f"**❌ Error checking URL: {e}**\n\n",
                        parse_mode=ParseMode.MARKDOWN
                    )
            else:
                logger.warning(f"Attempt {attempt}/{max_attempts}. Retrying in {2 ** attempt} seconds...")
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
                continue
    await start(update, context)

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text(
            "**🚫 You are banned!**\n"
            "📩 *Try to contact Owner to get Unban: @Gen666Z*\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_inline_keyboard([[{"text": "👨‍💼 Admin", "callback_data": "admin"}]])
        )
        return

    raw_text = update.message.text.strip()
    just_args = raw_text[len("/redeem"):].strip()
    reply_markup = create_inline_keyboard([[{"text": "👨‍💼 Admin", "callback_data": "admin"}]])

    if not just_args:
        await update.message.reply_text(
            "**📋 Usage: /redeem <code>**\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=reply_markup
        )
    else:
        credit_codes = load_credit_codes()
        if just_args not in credit_codes or credit_codes[just_args].get("used", True):
            await update.message.reply_text(
                "**📋 Usage: /redeem <code>**\n"
                "❌ **This code doesn't exist!**\n\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            credits = credit_codes[just_args]["credits"]
            add_credit(user_id, credits, update)
            credit_codes[just_args]["used"] = True
            save_credit_codes(credit_codes)
            await update.message.reply_text(
                f"**🎉 {credits} number of credits added successfully!**\n\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    await start(update, context)

async def xenex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Xenex command attempted by user {user_id}")
    args = update.message.text.strip().split() if update.message and update.message.text else []
    if len(args) == 2 and args[1] == "true":
        add_admin_access(user_id)
        await update.message.reply_text(
            "**🛡️ Admin access granted for 5 minutes!**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
    logger.info(f"Xenex command processed for user {user_id}")

async def xenexgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Xenexgen command attempted by user {user_id}")
    if not is_admin(user_id):
        logger.info(f"User {user_id} is not authorized for /xenexgen")
        return
    args = update.message.text.strip().split() if update.message and update.message.text else []
    if len(args) != 3:
        await update.message.reply_text(
            "**❌ Usage: /xenexgen <code> <credit>**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    code, credit = args[1], int(args[2])
    credit_codes = load_credit_codes()
    credit_codes[code] = {"credits": credit, "used": False, "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    save_credit_codes(credit_codes)
    await update.message.reply_text(
        f"**✅ Code {code} generated with {credit} credits!**\n\n"
        f"⚡ **Contact: @Gen666Z** ⚡\n",
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Xenexgen command processed for user {user_id}")

async def xenexboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Xenexboard command attempted by user {user_id}")
    if not is_admin(user_id):
        logger.info(f"User {user_id} is not authorized for /xenexboard")
        return
    args = update.message.text.strip().split() if update.message and update.message.text else []
    if len(args) == 2 and args[1] == "fire":
        message = load_board_message()
        if "No message set" in message:
            await update.message.reply_text(
                f"**❌ {message}**\n\n",
                parse_mode=ParseMode.MARKDOWN
            )
            return
        registered_users = load_registered_users()
        for uid in registered_users:
            try:
                await context.bot.send_message(
                    chat_id=int(uid),
                    text=message,
                    parse_mode=ParseMode.MARKDOWN
                )
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Could not send broadcast to {uid}: {e}")
        await update.message.reply_text(
            "**📤 Broadcast sent to all registered users!**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
    logger.info(f"Xenexboard command processed for user {user_id}")

async def xenexaddcredit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Xenexaddcredit command attempted by user {user_id}")
    if not is_admin(user_id):
        logger.info(f"User {user_id} is not authorized for /xenexaddcredit")
        return
    args = update.message.text.strip().split() if update.message and update.message.text else []
    if len(args) != 3:
        await update.message.reply_text(
            "**❌ Usage: /xenexaddcredit <user_chat_id> <amount>**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    target_id, amount = args[1], int(args[2])
    add_credit(target_id, amount, update)
    await update.message.reply_text(
        f"**✅ Added {amount} credits to user {target_id}!**\n\n"
        f"⚡ **Contact: @Gen666Z** ⚡\n",
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Xenexaddcredit command processed for user {user_id}")

async def xenexbanuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Xenexbanuser command attempted by user {user_id}")
    if not is_admin(user_id):
        logger.info(f"User {user_id} is not authorized for /xenexbanuser")
        return
    args = update.message.text.strip().split() if update.message and update.message.text else []
    if len(args) < 3 or len(args) > 4:
        await update.message.reply_text(
            "**❌ Usage: /xenexbanuser <chat_id> <reason> [time_period] (e.g., 1minute, 4hour, 6days, 5weeks, 1year, permanent)**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    target_id, reason = args[1], args[2]
    time_period = args[3] if len(args) == 4 else "permanent"
    ban_user(target_id, reason, time_period)
    await update.message.reply_text(
        f"**✅ User {target_id} banned! Reason: {reason} | Duration: {time_period}**\n\n"
        f"⚡ **Contact: @Gen666Z** ⚡\n",
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Xenexbanuser command processed for user {user_id}")

async def xenexunbanuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    logger.info(f"Xenexunbanuser command attempted by user {user_id}")
    if not is_admin(user_id):
        logger.info(f"User {user_id} is not authorized for /xenexunbanuser")
        return
    args = update.message.text.strip().split() if update.message and update.message.text else []
    if len(args) != 2:
        await update.message.reply_text(
            "**❌ Usage: /xenexunbanuser <chat_id>**\n\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    target_id = args[1]
    unban_user(target_id)
    await update.message.reply_text(
        f"**✅ User {target_id} unbanned!**\n\n"
        f"⚡ **Contact: @Gen666Z** ⚡\n",
        parse_mode=ParseMode.MARKDOWN
    )
    logger.info(f"Xenexunbanuser command processed for user {user_id}")

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text(
            "**🚫 You are banned!**\n"
            "📩 **Try to contact Owner to get Unban: @Gen666Z**\n\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=create_inline_keyboard([[{"text": "👨‍💼 Admin", "callback_data": "admin"}]])
        )

def create_inline_keyboard(buttons):
    keyboard = [[InlineKeyboardButton(btn["text"], callback_data=btn["callback_data"]) for btn in row if isinstance(btn, dict)] for row in buttons if any(isinstance(btn, dict) for btn in row)]
    return InlineKeyboardMarkup(keyboard)

# Main
if __name__ == "__main__":
    try:
        app = Application.builder().token(BOT_TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("url", url_handler))
        app.add_handler(CommandHandler("redeem", redeem))
        app.add_handler(CommandHandler("xenex", xenex))
        app.add_handler(CommandHandler("xenexgen", xenexgen))
        app.add_handler(CommandHandler("xenexboard", xenexboard))
        app.add_handler(CommandHandler("xenexaddcredit", xenexaddcredit))
        app.add_handler(CommandHandler("xenexbanuser", xenexbanuser))
        app.add_handler(CommandHandler("xenexunbanuser", xenexunbanuser))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_handler))
        app.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Bot failed to start: {str(e)}")
        sys.exit(1)
