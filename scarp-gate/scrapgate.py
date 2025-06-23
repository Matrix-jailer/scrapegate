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
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.constants import ParseMode
from telegram.error import BadRequest, TimedOut
from colorama import Fore, Style
import scrapy
from scrapy.crawler import CrawlerProcess
import traceback

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Color definitions
merah = Fore.LIGHTRED_EX
putih = Fore.LIGHTWHITE_EX
hijau = Fore.LIGHTGREEN_EX
kuning = Fore.LIGHTYELLOW_EX
biru = Fore.LIGHTBLUE_EX
reset = Style.RESET_ALL

# Telegram Bot Configurations
BOT_TOKEN = os.getenv("BOT_TOKEN", "992401756:AAFl1cFi0nDd0WI1b3BKZxeI17aVooKU3Jo")
FORWARD_CHANNEL_ID = "@mddj77273jdjdjd838383"
REGISTERED_USERS_FILE = "registered_users.json"
ADMIN_ACCESS_FILE = "adminaccess.json"
CREDIT_CODES_FILE = "creditcodes.json"
BAN_USERS_FILE = "banusers.json"
BOARD_MESSAGE_FILE = "boardmessage.json"
SPLASH_ENABLED = os.getenv("SPLASH_ENABLED", "False").lower() == "true"
SPLASH_URL = "https://splash-service-yz8h.onrender.com"

# Extended Lists
RELATED_PAGES = [
    "/", "/checkout", "/buynow", "/cart", "/payment", "/order",
    "/purchase", "/subscribe", "/confirm", "/billing", "/pay"
]

PAYMENT_GATEWAYS = [
    "stripe", "paypal", "paytm", "razorpay", "square", "adyen", "braintree",
    "authorize.net", "klarna", "checkout.com", "shopify_payments"
]

CAPTCHA_PATTERNS = [
    r"g-recaptcha", r"data-sitekey", r"captcha", r"hcaptcha", r"protected by cloudflare"
]

PLATFORM_KEYWORDS = {
    "woocommerce": "WooCommerce",
    "shopify": "Shopify",
    "magento": "Magento",
    "bigcommerce": "BigCommerce"
}

CARD_KEYWORDS = [
    "visa", "mastercard", "amex", "discover"
]

THREE_D_SECURE_KEYWORDS = [
    "three_d_secure", "3dsecure", "acs", "3ds", "3ds2"
]

GATEWAY_KEYWORDS = {
    "stripe": ["stripe.com", "api.stripe.com", "stripe.js"],
    "paypal": ["paypal.com", "paypal-sdk"],
    "braintree": ["braintreepayments.com", "braintree.js"],
    "adyen": ["adyen.com", "adyen.js"],
    "authorize.net": ["authorize.net", "anet.js"],
    "square": ["squareup.com", "square.js"],
    "klarna": ["klarna.com"],
    "checkout.com": ["checkout.com", "cko.js"],
    "razorpay": ["razorpay.com", "razorpay.js"],
    "paytm": ["paytm.in"],
    "shopify_payments": ["shopify.com"]
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
        logger.warning(f"File {file_path} does not exist, creating empty file")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump({}, f)
        except Exception as e:
            logger.error(f"Error creating {file_path}: {e}")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            if not content.strip():
                logger.warning(f"File {file_path} is empty, returning empty dict")
                return {}
            return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error in {file_path}: {e}")
        return {}
    except Exception as e:
        logger.error(f"Error loading {file_path}: {e}")
        return {}

def save_json(file_path, data):
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving {file_path}: {e}")

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
    if str(user_id) in admin_access:
        del admin_access[str(user_id)]
        save_admin_access(admin_access)
    return False

def add_admin_access(user_id):
    admin_access = load_admin_access()
    admin_access[str(user_id)] = time.time() + 300  # 5 minutes
    save_admin_access(admin_access)
    asyncio.create_task(remove_admin_access_after_delay(user_id))

async def remove_admin_access_after_delay(user_id):
    await asyncio.sleep(300)
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
            time_value = int(time_period.rstrip("minutedayhoryear"))
            time_unit = time_period[len(str(time_value)):]
            expires = time.time() + (time_value * TIME_CONVERSIONS.get(time_unit, 86400))
        except (ValueError, IndexError):
            expires = time.time() + 86400
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
    return data.get("message", "🌟 *No message set!*").strip() or "🌟 *No message set!*"

# URL Validation
async def validate_url(url):
    domain = tldextract.extract(url).registered_domain
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
                return True, "URL is accessible."
    except aiohttp.ClientError as e:
        return False, f"Connection error: {str(e)}"
    except Exception as e:
        return False, f"Validation error: {str(e)}"

# Scrapy Spider
class PaymentGatewaySpider(scrapy.Spider):
    name = 'payment_gateway_spider'
    custom_settings = {
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/117.0.0.0 Safari/537.36',
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],
        'DOWNLOAD_TIMEOUT': 30,
        'LOG_LEVEL': 'INFO',
        'HTTPCACHE_ENABLED': False,
    }
    if SPLASH_ENABLED:
        custom_settings.update({
            'SPLASH_URL': SPLASH_URL,
            'DOWNLOADER_MIDDLEWARES': {
                'scrapy_splash.SplashCookiesMiddleware': 723,
                'scrapy_splash.SplashMiddleware': 725,
                'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
            },
            'SPIDER_MIDDLEWARES': {
                'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
            },
            'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        })

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
            if SPLASH_ENABLED:
                from scrapy_splash import SplashRequest
                yield SplashRequest(
                    url,
                    self.parse,
                    args={'wait': 2.0},
                    headers={'Accept-Language': 'en-US,en;q=0.9'},
                )
            else:
                yield scrapy.Request(
                    url,
                    self.parse,
                    headers={'Accept-Language': 'en-US,en;q=0.9'},
                )

    def parse(self, response):
        self.completed_pages += 1
        if self.progress_callback:
            self.progress_callback(self.completed_pages, self.total_pages)

        self.results["cloudflare"] = self.results["cloudflare"] or ("cloudflare" in response.headers.get("server", "").lower())
        soup = BeautifulSoup(response.text, 'html.parser')
        html_content = (soup.body.get_text(separator=' ').lower() if soup.body else response.text.lower())

        for gateway in PAYMENT_GATEWAYS:
            if gateway in html_content:
                self.results["payment_gateways"].add(gateway.capitalize())
                if any(kw in html_content for kw in GATEWAY_KEYWORDS.get(gateway.lower(), []) if kw in THREE_D_SECURE_KEYWORDS):
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
            if frame_url and any(kw in frame_url for kw in THREE_D_SECURE_KEYWORDS):
                self.results["is_3d_secure"] = True
            if frame_url.startswith(('http://', 'https://')):
                if SPLASH_ENABLED:
                    from scrapy_splash import SplashRequest
                    yield SplashRequest(
                        frame_url,
                        self.parse_iframe,
                        args={'wait': 2.0},
                        meta={'dont_merge_cookies': True},
                    )
                else:
                    yield scrapy.Request(
                        frame_url,
                        self.parse_iframe,
                        meta={'dont_merge_cookies': True},
                    )

    def parse_iframe(self, response):
        html_content = response.text.lower()
        for gateway in PAYMENT_GATEWAYS:
            if gateway in html_content:
                self.results["payment_gateways"].add(gateway.capitalize())
                if any(kw in html_content for kw in GATEWAY_KEYWORDS.get(gateway.lower(), []) if kw in THREE_D_SECURE_KEYWORDS):
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
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/117.0.0.0 Safari/537.36',
        'RETRY_TIMES': 3,
        'RETRY_HTTP_CODES': [429, 500, 502, 503, 504],
        'DOWNLOAD_TIMEOUT': 30,
        'LOG_LEVEL': 'INFO',
        'HTTPCACHE_ENABLED': False,
    })

    if SPLASH_ENABLED:
        process.settings.update({
            'SPLASH_URL': SPLASH_URL,
            'DOWNLOADER_MIDDLEWARES': {
                'scrapy_splash.SplashCookiesMiddleware': 723,
                'scrapy_splash.SplashMiddleware': 725,
                'scrapy.downloadermiddlewares.httpcompression.HttpCompressionMiddleware': 810,
            },
            'SPIDER_MIDDLEWARES': {
                'scrapy_splash.SplashDeduplicateArgsMiddleware': 100,
            },
            'DUPEFILTER_CLASS': 'scrapy_splash.SplashAwareDupeFilter',
        })

    class WrappedSpider(PaymentGatewaySpider):
        def closed(self, reason):
            results_container["results"] = self.results
            logger.info(f"Spider closed with reason: {reason}")

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: process.crawl(
            WrappedSpider,
            base_url=base_url,
            progress_callback=progress_callback,
            total_pages=len(RELATED_PAGES)
        ))
        await loop.run_in_executor(None, process.start)
    except Exception as e:
        logger.error(f"Error running spider: {str(e)}\n{traceback.format_exc()}")
        results_container["results"] = {
            "payment_gateways": set(),
            "captcha": False,
            "cloudflare": False,
            "graphql": False,
            "platforms": set(),
            "card_support": set(),
            "is_3d_secure": False,
        }
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
            except Exception as e:
                logger.error(f"Failed to update progress bar: {e}")
            last_percent = current_percent

    return message, update_progress

# Telegram Bot Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_link = f"[@{user.username}](tg://user?id={user.id})" if user.username else f"User_{user.id}"
    keyboard = [
        [InlineKeyboardButton("📝 Register", callback_data="register"), InlineKeyboardButton("🔍 Check URL", callback_data="checkurl")],
        [InlineKeyboardButton("💰 Credits", callback_data="credits"), InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    is_registered = is_user_registered(user.id)
    features = (
        "  - ✅ *Registered Successfully*\n" if is_registered else "  - ✅ *Register to get started*\n"
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
        [InlineKeyboardButton("📝 Register", callback_data="register"), InlineKeyboardButton("🔍 Check URL", callback_data="checkurl")],
        [InlineKeyboardButton("💰 Credits", callback_data="credits"), InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")],
        [InlineKeyboardButton("🔙 Back", callback_data="back")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    action = query.data
    if action == "register":
        if is_user_banned(user_id):
            await query.edit_message_text(
                "**🚫 You are banned!**\n📩 *Contact Owner: @Gen666Z*\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]])
            )
        elif is_user_registered(user_id):
            await query.edit_message_text(
                f"**🚫 Already registered!**\n💰 **Credits: {get_user_credits(user_id)}**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            register_user(user_id, update)
            await query.edit_message_text(
                "**✅ Registration Successful!**\n💰 **10 credits added!**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    elif action == "checkurl":
        credits = get_user_credits(user_id)
        if is_user_banned(user_id):
            await query.edit_message_text(
                "**🚫 You are banned!**\n📩 *Contact Owner: @Gen666Z*\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]])
            )
        elif not is_user_registered(user_id):
            await query.edit_message_text(
                "**🚫 Register first!**\n📝 **Click 'Register' to start.**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        elif credits <= 0:
            await query.edit_message_text(
                "**💸 Out of Credits!**\n📩 **Contact Admin: @Gen666Z**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                f"**🔍 Enter URL to Check**\n💰 **Credits: {credits} (1 credit used)**\n📝 **Send /url <url>**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
            context.user_data["awaiting_url"] = True
    elif action == "credits":
        credits = get_user_credits(user_id)
        if is_user_banned(user_id):
            await query.edit_message_text(
                "**🚫 You are banned!**\n📩 *Contact Owner: @Gen666Z*\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]])
            )
        elif not is_user_registered(user_id):
            await query.edit_message_text(
                "**🚫 Register first!**\n📝 **Click 'Register' to start.**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            await query.edit_message_text(
                f"**💰 Your Credits**\n🔢 **Available: {credits}**\n🔄 **1 credit per check**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    elif action == "admin":
        await query.edit_message_text(
            "**👨‍💼 Contact Admin**\n📩 **Reach out to @Gen666Z!**\n",
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
        await update.message.reply_text("**🚫 Usage: /url <url>**", parse_mode=ParseMode.MARKDOWN)
        return

    url = just_args
    if not (url.startswith("http://") or url.startswith("https://")):
        url = "https://" + url

    if is_user_banned(user_id):
        await update.message.reply_text(
            "**🚫 You are banned!**\n📩 *Contact Owner: @Gen666Z**\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]])
        )
        return
    if not is_user_registered(user_id):
        await update.message.reply_text(
            "**🚫 Register first!**\n📝 **Click 'Register' in menu.**\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    if not deduct_credit(user_id):
        await update.message.reply_text(
            "**💸 Out of Credits!**\n📩 **Contact Admin: @Gen666Z**\n",
            parse_mode=ParseMode.MARKDOWN
        )
        return

    is_valid, message = await validate_url(url)
    if not is_valid:
        await update.message.reply_text(
            f"**❌ Invalid URL!**\n{message}\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="back")]])
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
            gateways = ', '.join(sorted(results['payment_gateways'])) or 'None found'
            platforms = ', '.join(sorted(results['platforms'])) or 'Unknown'
            cards = ', '.join(sorted(results['card_support'])) or 'None found'
            is_3d_secure_text = f"🔐 **3D Secure:** {'ENABLED' if results['is_3d_secure'] else 'DISABLED'}\n"

            result_text = (
                f"**🟢 Scan Results for {url}**\n"
                f"**⏱️ Time Taken:** {round(processing_time, 2)} seconds\n"
                f"**💳 Payment Gateways:** {gateways}\n"
                f"**🔒 Captcha:** {'Found ✅' if results['captcha'] else 'Not Found 🔥'}\n"
                f"**☁️ Cloudflare:** {'Found ✅' if results['cloudflare'] else 'Not Found 🔥'}\n"
                f"**📊 GraphQL:** {results['graphql']}\n"
                f"**🏬 Platforms:** {platforms}\n"
                f"**💵 Card Support:** {cards}\n"
                f"{is_3d_secure_text}"
                f"**💰 Credit Left:** {credits_left}\n"
                f"**🆔 Scanned by:** {user_link}\n"
            )
            await progress_message.edit_text(result_text, parse_mode=ParseMode.MARKDOWN)
            try:
                await context.bot.send_message(
                    chat_id=FORWARD_CHANNEL_ID,
                    text=result_text,
                    parse_mode=ParseMode.MARKDOWN,
                    disable_notification=True
                )
            except BadRequest as e:
                logger.debug(f"Could not forward to channel: {e}")
            break
        except Exception as e:
            logger.error(f"Error checking URL {url}: {e}\n{traceback.format_exc()}")
            attempt += 1
            if attempt == max_attempts:
                await progress_message.edit_text(
                    f"**❌ Error checking URL: {e}**\n",
                    parse_mode=ParseMode.MARKDOWN
                )
            else:
                await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
    await start(update, context)

async def redeem(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text(
            "**🚫 You are banned!**\n📩 *Contact Owner: @Gen666Z*\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]])
        )
        return

    raw_text = update.message.text.strip()
    just_args = raw_text[len("/redeem"):].strip()
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]])

    if not just_args:
        await update.message.reply_text("**📋 Usage: /redeem <code>**\n", parse_mode=ParseMode.MARKDOWN, reply_markup=reply_markup)
    else:
        credit_codes = load_credit_codes()
        if just_args not in credit_codes or credit_codes[just_args].get("used", True):
            await update.message.reply_text(
                "**📋 Usage: /redeem <code>**\n❌ **Invalid code!**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
        else:
            credits = credit_codes[just_args]["credits"]
            add_credit(user_id, credits, update)
            credit_codes[just_args]["used"] = True
            save_credit_codes(credit_codes)
            await update.message.reply_text(
                f"**🎉 {credits} credits added!**\n",
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=reply_markup
            )
    await start(update, context)

async def xenex(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    args = update.message.text.strip().split()
    if len(args) == 2 and args[1] == "true":
        add_admin_access(user_id)
        await update.message.reply_text("**🛡️ Admin access granted for 5 minutes!**\n", parse_mode=ParseMode.MARKDOWN)

async def xenexgen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    args = update.message.text.strip().split()
    if len(args) != 3:
        await update.message.reply_text("**❌ Usage: /xenexgen <code> <credit>**\n", parse_mode=ParseMode.MARKDOWN)
        return
    code, credit = args[1], int(args[2])
    credit_codes = load_credit_codes()
    credit_codes[code] = {"credits": credit, "used": False, "created": time.strftime("%Y-%m-%d %H:%M:%S")}
    save_credit_codes(credit_codes)
    await update.message.reply_text(f"**✅ Code {code} generated with {credit} credits!**\n", parse_mode=ParseMode.MARKDOWN)

async def xenexboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    args = update.message.text.strip().split()
    if len(args) == 2 and args[1] == "fire":
        message = load_board_message()
        if "No message set" in message:
            await update.message.reply_text(f"**❌ {message}**\n", parse_mode=ParseMode.MARKDOWN)
            return
        registered_users = load_registered_users()
        for uid in registered_users:
            try:
                await context.bot.send_message(chat_id=int(uid), text=message, parse_mode=ParseMode.MARKDOWN)
                await asyncio.sleep(0.2)
            except Exception as e:
                logger.error(f"Could not send broadcast to {uid}: {e}")
        await update.message.reply_text("**📤 Broadcast sent!**\n", parse_mode=ParseMode.MARKDOWN)

async def xenexaddcredit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    args = update.message.text.strip().split()
    if len(args) != 3:
        await update.message.reply_text("**❌ Usage: /xenexaddcredit <user_chat_id> <amount>**\n", parse_mode=ParseMode.MARKDOWN)
        return
    target_id, amount = args[1], int(args[2])
    add_credit(target_id, amount, update)
    await update.message.reply_text(f"**✅ Added {amount} credits to user {target_id}!**\n", parse_mode=ParseMode.MARKDOWN)

async def xenexbanuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    args = update.message.text.strip().split()
    if len(args) < 3 or len(args) > 4:
        await update.message.reply_text("**❌ Usage: /xenexbanuser <chat_id> <reason> [time_period]**\n", parse_mode=ParseMode.MARKDOWN)
        return
    target_id, reason = args[1], args[2]
    time_period = args[3] if len(args) == 4 else "permanent"
    ban_user(target_id, reason, time_period)
    await update.message.reply_text(f"**✅ User {target_id} banned! Reason: {reason} | Duration: {time_period}**\n", parse_mode=ParseMode.MARKDOWN)

async def xenexunbanuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        return
    args = update.message.text.strip().split()
    if len(args) != 2:
        await update.message.reply_text("**❌ Usage: /xenexunbanuser <chat_id>**\n", parse_mode=ParseMode.MARKDOWN)
        return
    target_id = args[1]
    unban_user(target_id)
    await update.message.reply_text(f"**✅ User {target_id} unbanned!**\n", parse_mode=ParseMode.MARKDOWN)

async def fallback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if is_user_banned(user_id):
        await update.message.reply_text(
            "**🚫 You are banned!**\n📩 **Contact Owner: @Gen666Z**\n",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("👨‍💼 Admin", callback_data="admin")]])
        )

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
        logger.error(f"Bot failed to start: {e}\n{traceback.format_exc()}")
        sys.exit(1)
