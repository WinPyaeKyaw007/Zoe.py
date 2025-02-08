import sqlite3
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# Bot Token & Admin ID
TOKEN = "7710600587:AAEcO-1HW7FmIRNY4aYm_6D3rZtnPrY7JgY"
ADMIN_ID = 1794465007

# Database Initialization
conn = sqlite3.connect("users.db", check_same_thread=False)
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
conn.commit()

# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Start Command
async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    # Check if user is already in DB
    cursor.execute("SELECT user_id FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone() is None:
        cursor.execute("INSERT INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()

    # Get Total Users Count
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    welcome_msg = (
        "Hd Quality Bot ပါရှင့် \n"
        "Video လေးတွေကို မကြာမကြာသလို ဒီ Bot လေးကနေ ပို့ပေးနေမှာပါရှင့်\n"
        "Update အသစ်လေးတွေကိုလဲ စောင့်မျော်ပေးကြပါအုံးရှင့်\n\n"
        f"👥 Total Members: {total_users}"
    )

    await update.message.reply_text(welcome_msg)

    # Notify Admin
    await context.bot.send_message(chat_id=ADMIN_ID, text=f"🔔 New User Joined: {user_id}\n👥 Total Members: {total_users}")

# Broadcast Command (Admin Only)
async def broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to send broadcasts!")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Please provide a message to send!")
        return

    message = " ".join(context.args)

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    for user in users:
        try:
            await context.bot.send_message(chat_id=user[0], text=message)
        except Exception as e:
            logging.warning(f"Failed to send message to {user[0]}: {e}")

    await update.message.reply_text("✅ Broadcast Sent!")

# User Messages Forward to Admin
async def forward_to_admin(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    message = update.message.text

    forward_text = f"📩 Message from {user_id}:\n\n{message}"
    await context.bot.send_message(chat_id=ADMIN_ID, text=forward_text)

# Admin Media Broadcast (Photo/Video)
async def media_broadcast(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id

    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to send broadcasts!")
        return

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()

    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        caption = update.message.caption if update.message.caption else ""
        for user in users:
            try:
                await context.bot.send_photo(chat_id=user[0], photo=file_id, caption=caption)
            except Exception as e:
                logging.warning(f"Failed to send photo to {user[0]}: {e}")

    elif update.message.video:
        file_id = update.message.video.file_id
        caption = update.message.caption if update.message.caption else ""
        for user in users:
            try:
                await context.bot.send_video(chat_id=user[0], video=file_id, caption=caption)
            except Exception as e:
                logging.warning(f"Failed to send video to {user[0]}: {e}")

    await update.message.reply_text("✅ Media Broadcast Sent!")

# Admin Command to Get User List
async def list_members(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to view the member list!")
        return

    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    total_users = len(users)

    user_list = "\n".join([f"👤 {user[0]}" for user in users])
    await update.message.reply_text(f"👥 Total Members: {total_users}\n\n{user_list}")

# Command Handlers
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("broadcast", broadcast))
    application.add_handler(CommandHandler("members", list_members))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_to_admin))
    application.add_handler(MessageHandler(filters.PHOTO | filters.VIDEO, media_broadcast))

    application.run_polling()

if name == "main":
    main()
