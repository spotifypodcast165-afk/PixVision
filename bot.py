"""
Pixflipt Bot - Complete Working Version
No OpenCV needed - uses only Pillow
"""

import os
import io
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from PIL import Image, ImageDraw, ImageFont
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import tempfile

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("BOT_TOKEN not found! Please set it in environment variables.")

# Create application
app = Application.builder().token(TOKEN).build()

# ============ COMMAND HANDLERS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    
    welcome = f"""
👋 **Welcome to Pixflipt Bot, {user.first_name}!**

I'm your complete image processing assistant!

**✨ What I can do:**
🔄 Convert JPG ↔ PNG ↔ WEBP
📏 Resize & Compress images
💧 Add text watermark
📄 Convert images to PDF
📦 Bulk image processing

**🚀 How to use:**
1. Click "Get Started" below
2. Choose an action
3. Send your image(s)
4. Get your processed result!

Click the button below to begin!
"""
    
    keyboard = [[InlineKeyboardButton("🚀 Get Started", callback_data="main_menu")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command"""
    help_text = """
📚 **Help & Commands**

**Commands:**
/start - Start the bot
/help - Show this help

**Features:**

🔄 **Convert Images**
- JPG → PNG
- PNG → JPG
- PNG → WEBP
- WEBP → PNG
- Bulk conversion supported

📏 **Resize Images**
- Preset sizes (Instagram, Twitter, etc.)
- Custom dimensions
- Percentage scaling
- Automatic compression

💧 **Add Watermark**
- Custom text
- Auto-positioned
- Semi-transparent
- Professional look

📄 **Convert to PDF**
- Single or multiple images
- Auto-fit to page
- High quality

**Tips:**
- Send multiple images for bulk operations
- Use high-quality images for best results
- Processing takes a few seconds
"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# ============ MENU HANDLERS ============

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show main menu"""
    query = update.callback_query
    await query.answer()
    
    menu = "🎯 **Choose an action:**\n\nSelect what you want to do:"
    
    keyboard = [
        [InlineKeyboardButton("🔄 Convert Image", callback_data="convert")],
        [InlineKeyboardButton("📏 Resize Image", callback_data="resize")],
        [InlineKeyboardButton("💧 Add Watermark", callback_data="watermark")],
        [InlineKeyboardButton("📄 Convert to PDF", callback_data="pdf")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(menu, reply_markup=reply_markup, parse_mode='Markdown')

# ============ CONVERSION HANDLERS ============

async def show_convert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show conversion options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [
            InlineKeyboardButton("JPG → PNG", callback_data="conv_jpg_png"),
            InlineKeyboardButton("PNG → JPG", callback_data="conv_png_jpg"),
        ],
        [
            InlineKeyboardButton("PNG → WEBP", callback_data="conv_png_webp"),
            InlineKeyboardButton("WEBP → PNG", callback_data="conv_webp_png"),
        ],
        [
            InlineKeyboardButton("JPG → WEBP", callback_data="conv_jpg_webp"),
            InlineKeyboardButton("WEBP → JPG", callback_data="conv_webp_jpg"),
        ],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "🔄 **Select conversion format:**\n\nChoose what you want to convert to:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle conversion selection"""
    query = update.callback_query
    await query.answer()
    
    # Store conversion type
    conversion_type = query.data.replace('conv_', '')
    context.user_data['conversion_type'] = conversion_type
    
    # Get format names for display
    parts = conversion_type.split('_')
    from_format = parts[0].upper()
    to_format = parts[1].upper()
    
    await query.edit_message_text(
        f"🔄 **Converting {from_format} → {to_format}**\n\n"
        f"Send me your {from_format} image(s).\n"
        f"I'll convert them to {to_format}.\n\n"
        "📌 You can send multiple images for bulk conversion!",
        parse_mode='Markdown'
    )

# ============ RESIZE HANDLERS ============

async def show_resize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show resize options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📱 Instagram Post (1080x1080)", callback_data="resize_1080_1080")],
        [InlineKeyboardButton("📱 Instagram Story (1080x1920)", callback_data="resize_1080_1920")],
        [InlineKeyboardButton("🐦 Twitter Post (1200x675)", callback_data="resize_1200_675")],
        [InlineKeyboardButton("📘 Facebook Post (1200x630)", callback_data="resize_1200_630")],
        [InlineKeyboardButton("🎬 YouTube Thumbnail (1280x720)", callback_data="resize_1280_720")],
        [InlineKeyboardButton("✏️ Custom Size", callback_data="resize_custom")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "📏 **Choose a size:**\n\nSelect a preset or choose custom:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_resize(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle resize selection"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "resize_custom":
        context.user_data['resize_mode'] = 'custom'
        await query.edit_message_text(
            "✏️ **Custom Resize**\n\n"
            "Send me the dimensions:\n"
            "• `width height` (e.g., `800 600`)\n"
            "• Or percentage (e.g., `50%`)\n\n"
            "Example: `1920 1080` or `75%`\n\n"
            "Then send your image!",
            parse_mode='Markdown'
        )
    else:
        # Preset size
        size = query.data.replace('resize_', '')
        width, height = map(int, size.split('_'))
        context.user_data['resize_width'] = width
        context.user_data['resize_height'] = height
        context.user_data['resize_mode'] = 'preset'
        
        await query.edit_message_text(
            f"✅ Set to **{width}x{height}**\n\n"
            "📤 Now send me your image to resize!",
            parse_mode='Markdown'
        )

# ============ WATERMARK HANDLERS ============

async def show_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show watermark options"""
    query = update.callback_query
    await query.answer()
    
    keyboard = [
        [InlineKeyboardButton("📝 Add Text Watermark", callback_data="watermark_text")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="main_menu")],
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(
        "💧 **Add Watermark**\n\n"
        "Add a professional text watermark to your images.\n\n"
        "Features:\n"
        "• Custom text\n"
        "• Auto-positioned\n"
        "• Semi-transparent\n"
        "• Professional look\n\n"
        "Click below to start!",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle watermark text request"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['watermark_mode'] = 'waiting_text'
    await query.edit_message_text(
        "📝 **Send me the watermark text**\n\n"
        "Example: `© MyName 2024`\n\n"
        "After sending text, send your image!",
        parse_mode='Markdown'
    )

# ============ PDF HANDLERS ============

async def show_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show PDF conversion option"""
    query = update.callback_query
    await query.answer()
    
    context.user_data['conversion_type'] = 'image_pdf'
    
    await query.edit_message_text(
        "📄 **Convert to PDF**\n\n"
        "Send me one or more images to convert to PDF.\n"
        "I'll combine them into a single PDF file.\n\n"
        "📌 You can send multiple images at once!\n"
        "✅ Each image will be on a separate page.",
        parse_mode='Markdown'
    )

# ============ TEXT INPUT HANDLER ============

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input from users"""
    text = update.message.text.strip()
    
    # Watermark text
    if context.user_data.get('watermark_mode') == 'waiting_text':
        context.user_data['watermark_text'] = text
        context.user_data['watermark_mode'] = 'ready'
        await update.message.reply_text(
            f"✅ Watermark text set: **{text}**\n\n"
            "📤 Now send me your image!",
            parse_mode='Markdown'
        )
        return
    
    # Custom resize dimensions
    if context.user_data.get('resize_mode') == 'custom':
        try:
            if text.endswith('%'):
                # Percentage
                percentage = float(text[:-1])
                if 1 <= percentage <= 1000:
                    context.user_data['resize_percentage'] = percentage / 100
                    context.user_data['resize_mode'] = 'percentage'
                    await update.message.reply_text(
                        f"✅ Set to {text} of original size\n\n"
                        "📤 Now send your image to resize!"
                    )
                else:
                    await update.message.reply_text("❌ Percentage must be between 1% and 1000%")
            else:
                # Width height
                parts = text.split()
                if len(parts) == 2:
                    width = int(parts[0])
                    height = int(parts[1])
                    if width > 0 and height > 0 and width <= 10000 and height <= 10000:
                        context.user_data['resize_width'] = width
                        context.user_data['resize_height'] = height
                        context.user_data['resize_mode'] = 'custom_size'
                        await update.message.reply_text(
                            f"✅ Set to **{width}x{height}**\n\n"
                            "📤 Now send your image to resize!",
                            parse_mode='Markdown'
                        )
                    else:
                        await update.message.reply_text("❌ Dimensions must be between 1 and 10000")
                else:
                    await update.message.reply_text(
                        "❌ Use format: `width height` or `percentage%`\n"
                        "Example: `800 600` or `50%`"
                    )
        except ValueError:
            await update.message.reply_text(
                "❌ Invalid input. Use: `width height` or `percentage%`"
            )

# ============ IMAGE HANDLER ============

async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming images"""
    try:
        # Check if user is in a conversion mode
        conversion_type = context.user_data.get('conversion_type')
        resize_mode = context.user_data.get('resize_mode')
        watermark_mode = context.user_data.get('watermark_mode')
        
        # If no mode selected, ask user to choose
        if not any([conversion_type, resize_mode, watermark_mode]):
            keyboard = [[InlineKeyboardButton("📋 Show Menu", callback_data="main_menu")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.message.reply_text(
                "📸 **Image received!**\n\n"
                "Please select an action from the menu first.",
                reply_markup=reply_markup,
                parse_mode='Markdown'
            )
            return
        
        # Get the image file
        if update.message.photo:
            file = await update.message.photo[-1].get_file()
        else:
            file = await update.message.document.get_file()
        
        await update.message.reply_text("⏳ Processing your image... Please wait.")
        
        # Download image
        image_bytes = await file.download_as_bytearray()
        image = Image.open(io.BytesIO(image_bytes))
        
        # Process based on mode
        if conversion_type == 'image_pdf':
            await process_pdf(update, context, image)
        elif conversion_type:
            await process_conversion(update, context, image)
        elif resize_mode:
            await process_resize(update, context, image)
        elif watermark_mode == 'ready':
            await process_watermark(update, context, image)
        else:
            await update.message.reply_text("❌ Unknown operation. Please try again.")
            
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        await update.message.reply_text(
            "❌ Failed to process the image. Please try again with a different image."
        )

# ============ PROCESSING FUNCTIONS ============

async def process_conversion(update: Update, context: ContextTypes.DEFAULT_TYPE, image):
    """Convert image to different format"""
    conv_type = context.user_data.get('conversion_type')
    
    format_map = {
        'jpg_png': ('JPEG', 'PNG'),
        'png_jpg': ('PNG', 'JPEG'),
        'png_webp': ('PNG', 'WEBP'),
        'webp_png': ('WEBP', 'PNG'),
        'jpg_webp': ('JPEG', 'WEBP'),
        'webp_jpg': ('WEBP', 'JPEG'),
    }
    
    if conv_type not in format_map:
        await update.message.reply_text("❌ Unknown conversion type")
        return
    
    from_format, to_format = format_map[conv_type]
    
    try:
        # Handle conversion
        if to_format == 'JPEG' and image.mode == 'RGBA':
            # Convert RGBA to RGB for JPEG
            bg = Image.new('RGB', image.size, (255, 255, 255))
            bg.paste(image, mask=image.split()[3])
            image = bg
        elif to_format == 'JPEG':
            image = image.convert('RGB')
        elif to_format == 'PNG' and image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Save converted image
        bio = io.BytesIO()
        save_format = 'JPEG' if to_format == 'JPEG' else to_format
        image.save(bio, format=save_format, quality=95, optimize=True)
        bio.seek(0)
        
        # Get file extension
        ext = 'jpg' if to_format == 'JPEG' else to_format.lower()
        
        await update.message.reply_document(
            document=bio,
            filename=f"converted.{ext}",
            caption=f"✅ Successfully converted {from_format} → {to_format}!"
        )
        
        # Clear conversion data
        context.user_data.pop('conversion_type', None)
        
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        await update.message.reply_text("❌ Failed to convert image.")

async def process_resize(update: Update, context: ContextTypes.DEFAULT_TYPE, image):
    """Resize image"""
    mode = context.user_data.get('resize_mode')
    original_size = len(image.tobytes())
    
    try:
        # Calculate new dimensions
        if mode == 'percentage':
            scale = context.user_data.get('resize_percentage', 1)
            new_width = int(image.width * scale)
            new_height = int(image.height * scale)
        elif mode == 'custom_size':
            new_width = context.user_data.get('resize_width', image.width)
            new_height = context.user_data.get('resize_height', image.height)
        else:  # preset
            new_width = context.user_data.get('resize_width', image.width)
            new_height = context.user_data.get('resize_height', image.height)
        
        # Resize image
        resized = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save resized image
        bio = io.BytesIO()
        format_name = image.format or 'PNG'
        if format_name == 'PNG':
            resized.save(bio, format='PNG', optimize=True)
        else:
            resized.save(bio, format='JPEG', quality=90, optimize=True)
        bio.seek(0)
        
        # Calculate compression
        new_size = len(bio.getvalue())
        compression = ((1 - (new_size / original_size)) * 100) if original_size > 0 else 0
        
        caption = f"""
✅ **Resized successfully!**

📐 Original: {image.width}x{image.height}
📐 New: {new_width}x{new_height}
📊 Original size: {original_size / 1024:.1f} KB
📊 New size: {new_size / 1024:.1f} KB
💾 Saved: {compression:.1f}%
"""
        
        await update.message.reply_document(
            document=bio,
            filename=f"resized_{new_width}x{new_height}.{format_name.lower()}",
            caption=caption,
            parse_mode='Markdown'
        )
        
        # Clear resize data
        context.user_data.pop('resize_mode', None)
        context.user_data.pop('resize_width', None)
        context.user_data.pop('resize_height', None)
        context.user_data.pop('resize_percentage', None)
        
    except Exception as e:
        logger.error(f"Resize error: {e}")
        await update.message.reply_text("❌ Failed to resize image.")

async def process_watermark(update: Update, context: ContextTypes.DEFAULT_TYPE, image):
    """Add watermark to image"""
    watermark_text = context.user_data.get('watermark_text', '© Watermark')
    
    try:
        # Convert to RGBA for transparency
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # Create overlay
        overlay = Image.new('RGBA', image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        
        # Calculate font size
        font_size = min(image.width, image.height) // 20
        font_size = max(16, min(font_size, 80))
        
        # Try to load font
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", font_size)
        except:
            try:
                font = ImageFont.truetype("arial.ttf", font_size)
            except:
                font = ImageFont.load_default()
        
        # Get text size
        text_bbox = draw.textbbox((0, 0), watermark_text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        # Position - bottom right
        padding = 20
        x = image.width - text_width - padding
        y = image.height - text_height - padding
        
        # Draw shadow
        draw.text((x+2, y+2), watermark_text, font=font, fill=(0, 0, 0, 64))
        # Draw main text
        draw.text((x, y), watermark_text, font=font, fill=(255, 255, 255, 180))
        
        # Merge overlay with original
        watermarked = Image.alpha_composite(image, overlay)
        
        # Save
        bio = io.BytesIO()
        watermarked.save(bio, format='PNG', optimize=True)
        bio.seek(0)
        
        await update.message.reply_document(
            document=bio,
            filename="watermarked.png",
            caption=f"✅ Watermark added: **{watermark_text}**",
            parse_mode='Markdown'
        )
        
        # Clear watermark data
        context.user_data.pop('watermark_text', None)
        context.user_data.pop('watermark_mode', None)
        
    except Exception as e:
        logger.error(f"Watermark error: {e}")
        await update.message.reply_text("❌ Failed to add watermark.")

async def process_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE, image):
    """Convert image to PDF"""
    try:
        pdf_buffer = io.BytesIO()
        c = canvas.Canvas(pdf_buffer, pagesize=letter)
        
        # Get image dimensions
        width, height = image.size
        
        # Scale to fit page
        page_width, page_height = letter
        scale = min(page_width / width, page_height / height) * 0.9
        
        new_width = width * scale
        new_height = height * scale
        x = (page_width - new_width) / 2
        y = (page_height - new_height) / 2
        
        # Save temp image
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            # Convert to RGB if needed
            if image.mode == 'RGBA':
                bg = Image.new('RGB', image.size, (255, 255, 255))
                bg.paste(image, mask=image.split()[3])
                bg.save(tmp.name, 'JPEG', quality=95)
            else:
                image.convert('RGB').save(tmp.name, 'JPEG', quality=95)
            
            c.drawImage(tmp.name, x, y, width=new_width, height=new_height)
            os.unlink(tmp.name)
        
        c.save()
        pdf_buffer.seek(0)
        
        await update.message.reply_document(
            document=pdf_buffer,
            filename="converted.pdf",
            caption="✅ Successfully converted to PDF!"
        )
        
        context.user_data.pop('conversion_type', None)
        
    except Exception as e:
        logger.error(f"PDF conversion error: {e}")
        await update.message.reply_text("❌ Failed to convert to PDF.")

# ============ SETUP HANDLERS ============

def setup_handlers():
    """Setup all handlers"""
    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # Callback handlers
    app.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    app.add_handler(CallbackQueryHandler(show_convert, pattern="^convert$"))
    app.add_handler(CallbackQueryHandler(show_resize, pattern="^resize$"))
    app.add_handler(CallbackQueryHandler(show_watermark, pattern="^watermark$"))
    app.add_handler(CallbackQueryHandler(show_pdf, pattern="^pdf$"))
    app.add_handler(CallbackQueryHandler(handle_conversion, pattern="^conv_"))
    app.add_handler(CallbackQueryHandler(handle_resize, pattern="^resize_"))
    app.add_handler(CallbackQueryHandler(handle_watermark, pattern="^watermark_text$"))
    
    # Message handlers
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

# ============ MAIN EXECUTION ============

if __name__ == '__main__':
    try:
        # Setup handlers
        setup_handlers()
        
        # Get port
        port = int(os.environ.get('PORT', 10000))
        
        # Run bot
        if os.environ.get('RENDER'):
            webhook_url = os.environ.get('RENDER_EXTERNAL_URL')
            if webhook_url:
                print(f"🚀 Starting bot with webhook on {webhook_url}")
                app.run_webhook(
                    listen="0.0.0.0",
                    port=port,
                    url_path=TOKEN,
                    webhook_url=f"{webhook_url}/{TOKEN}"
                )
        else:
            print("🚀 Starting bot with polling...")
            app.run_polling(allowed_updates=Update.ALL_TYPES)
            
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        print(f"❌ Error: {e}")
