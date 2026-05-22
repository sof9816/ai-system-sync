#!/usr/bin/env python3
"""
Telegram bot command handler for skorpion_claw_bot.
Shows inline keyboard buttons when user types /commands.
Also handles /start, /help, and all slash commands.
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Bot token from .env
TOKEN = "8213387754:AAH7wCdy6mMUe6UKVVIAum4HmIQ0dml70y0"
ALLOWED_USER = "38814376"


def run_hermes_cmd(cmd: str) -> str:
    """Run a hermes CLI command and return output."""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout.strip() or result.stderr.strip() or "Done."
    except subprocess.TimeoutExpired:
        return "Command timed out."
    except Exception as e:
        return f"Error: {e}"


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start."""
    await update.message.reply_text(
        "☠️ GT Hermes System\n\n"
        "Type /commands for buttons\n"
        "Or use /help for all commands",
    )


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help."""
    text = (
        "📋 Available Commands:\n\n"
        "/status — System health\n"
        "/digest — Run daily digest\n"
        "/backup — Trigger GitHub backup\n"
        "/audit — Run security audit\n"
        "/skills — List skills\n"
        "/agents — Show swarm agents\n"
        "/pi — Quick pi.dev task\n"
        "/memory — Recent memory\n"
        "/docs — Documentation link\n"
        "/commands — Show button menu"
    )
    await update.message.reply_text(text)


async def commands_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /commands — show inline keyboard buttons."""
    keyboard = [
        [
            InlineKeyboardButton("📊 Status", callback_data="status"),
            InlineKeyboardButton("📰 Digest", callback_data="digest"),
        ],
        [
            InlineKeyboardButton("💾 Backup", callback_data="backup"),
            InlineKeyboardButton("🔒 Audit", callback_data="audit"),
        ],
        [
            InlineKeyboardButton("⚡ Skills", callback_data="skills"),
            InlineKeyboardButton("🤖 Agents", callback_data="agents"),
        ],
        [
            InlineKeyboardButton("💻 Pi Task", callback_data="pi"),
            InlineKeyboardButton("🧠 Memory", callback_data="memory"),
        ],
        [
            InlineKeyboardButton("📖 Docs", callback_data="docs"),
            InlineKeyboardButton("❓ Help", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "GT Hermes Control Panel:",
        reply_markup=reply_markup,
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle button clicks."""
    query = update.callback_query
    await query.answer()

    action = query.data
    user_id = str(update.effective_user.id)

    if user_id != ALLOWED_USER:
        await query.edit_message_text("⛔ Unauthorized.")
        return

    handlers = {
        "status": handle_status,
        "digest": handle_digest,
        "backup": handle_backup,
        "audit": handle_audit,
        "skills": handle_skills,
        "agents": handle_agents,
        "pi": handle_pi,
        "memory": handle_memory,
        "docs": handle_docs,
        "help": handle_help_callback,
    }

    handler = handlers.get(action)
    if handler:
        await handler(query)
    else:
        await query.edit_message_text(f"Unknown action: {action}")


async def handle_status(query):
    """Show system status."""
    output = run_hermes_cmd("hermes gateway status 2>&1 | head -20")
    cron = run_hermes_cmd("hermes cron list 2>&1 | grep -E 'Name:|Status' | head -10")
    text = f"📊 System Status:\n\n```\n{output}\n\nCrons:\n{cron}\n```"
    await query.edit_message_text(text, parse_mode="Markdown")


async def handle_digest(query):
    """Trigger daily digest."""
    await query.edit_message_text("📰 Triggering daily digest...")
    output = run_hermes_cmd("hermes cron run 9a2440921b32 2>&1")
    await query.edit_message_text(f"📰 Digest triggered:\n```\n{output}\n```", parse_mode="Markdown")


async def handle_backup(query):
    """Trigger backup."""
    await query.edit_message_text("💾 Triggering backup...")
    output = run_hermes_cmd("bash ~/.hermes/scripts/hermes-backup.sh 2>&1 | tail -20")
    await query.edit_message_text(f"💾 Backup result:\n```\n{output}\n```", parse_mode="Markdown")


async def handle_audit(query):
    """Run security audit."""
    await query.edit_message_text("🔒 Running security audit...")
    output = run_hermes_cmd("bash ~/.hermes/scripts/security-audit.sh 2>&1")
    await query.edit_message_text(f"🔒 Audit result:\n```\n{output}\n```", parse_mode="Markdown")


async def handle_skills(query):
    """List skills count."""
    output = run_hermes_cmd("hermes skills list 2>&1 | grep -c 'enabled'")
    await query.edit_message_text(f"⚡ Active skills: {output.strip()}")


async def handle_agents(query):
    """Show agents."""
    output = run_hermes_cmd("hermes agents list 2>&1 || echo 'No active agents'")
    await query.edit_message_text(f"🤖 Agents:\n```\n{output}\n```", parse_mode="Markdown")


async def handle_pi(query):
    """Quick pi info."""
    output = run_hermes_cmd("pi --version 2>&1 && pi --list-models 2>&1 | grep -i kimi")
    await query.edit_message_text(f"💻 Pi Status:\n```\n{output}\n```", parse_mode="Markdown")


async def handle_memory(query):
    """Show memory files."""
    output = run_hermes_cmd("ls -la ~/.hermes/memories/ 2>&1")
    await query.edit_message_text(f"🧠 Memory files:\n```\n{output}\n```", parse_mode="Markdown")


async def handle_docs(query):
    """Link to docs."""
    await query.edit_message_text(
        "📖 Documentation:\n\n"
        "GitHub: https://github.com/sof9816/ai-skills/blob/main/README.md\n"
        "Obsidian: GT Vault/hermes/GT AI System — Complete Documentation.md\n"
        "Telegram: /commands for buttons, /help for text list"
    )


async def handle_help_callback(query):
    """Show help text."""
    text = (
        "📋 Commands:\n\n"
        "/status — System health\n"
        "/digest — Run daily digest\n"
        "/backup — Trigger backup\n"
        "/audit — Run security audit\n"
        "/skills — List skills\n"
        "/agents — Show agents\n"
        "/pi — Quick pi task\n"
        "/memory — Recent memory\n"
        "/docs — Documentation\n"
        "/commands — Button menu"
    )
    await query.edit_message_text(text)


async def slash_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle direct slash commands (fallback)."""
    text = update.message.text.lower()
    user_id = str(update.effective_user.id)

    if user_id != ALLOWED_USER:
        await update.message.reply_text("⛔ Unauthorized.")
        return

    # Map slash commands to actions
    command_map = {
        "/status": handle_status,
        "/digest": handle_digest,
        "/backup": handle_backup,
        "/audit": handle_audit,
        "/skills": handle_skills,
        "/agents": handle_agents,
        "/pi": handle_pi,
        "/memory": handle_memory,
        "/docs": handle_docs,
    }

    cmd = text.split()[0]
    handler = command_map.get(cmd)

    if handler:
        # Create a fake query object
        class FakeQuery:
            def __init__(self, msg):
                self.msg = msg
            async def edit_message_text(self, text, parse_mode=None):
                await self.msg.reply_text(text, parse_mode=parse_mode)

        await handler(FakeQuery(update.message))
    else:
        await update.message.reply_text("Unknown command. Type /commands for buttons or /help for list.")


def main():
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    # Command handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    application.add_handler(CommandHandler("commands", commands_handler))

    # Button handler
    application.add_handler(CallbackQueryHandler(button_handler))

    # Slash command fallback
    application.add_handler(MessageHandler(filters.COMMAND, slash_command_handler))

    print("Starting skorpion_claw_bot command handler...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
