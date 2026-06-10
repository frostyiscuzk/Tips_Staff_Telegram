import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ConversationHandler, filters, ContextTypes
)
from staff import StaffMember
from tip_pool import TipPool

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

MAIN_MENU, ASK_TOTAL, ASK_DEPT_ORDER, ASK_NAME, ASK_HOURS, ASK_SHARE = range(6)

DEPT_EMOJI = {"Kitchen": "🍳", "Service": "🍽️"}

RESET_ROW = [InlineKeyboardButton("🔄 Reset", callback_data="reset")]


# ── Keyboards ────────────────────────────────────────────────────────────────

def main_menu_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 New Tip Split", callback_data="new_split")],
    ])


def reset_kb():
    return InlineKeyboardMarkup([RESET_ROW])


def dept_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🍳 Kitchen", callback_data="dept_kitchen"),
            InlineKeyboardButton("🍽️ Service", callback_data="dept_service"),
        ],
        RESET_ROW,
    ])


def share_kb():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Full Share", callback_data="share_full"),
            InlineKeyboardButton("Half Share", callback_data="share_half"),
        ],
        RESET_ROW,
    ])


def done_kb(dept):
    emoji = DEPT_EMOJI[dept]
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"✅ Done with {emoji} {dept}", callback_data="done_dept")],
        RESET_ROW,
    ])


# ── Text helpers ──────────────────────────────────────────────────────────────

def roster_text(members):
    if not members:
        return ""
    lines = ["📋 *Staff so far:*"]
    for m in members:
        share = "full" if m.multiplier == 1.0 else "½"
        lines.append(f"  {DEPT_EMOJI[m.department]} {m.name} · {m.hours}h · {share}")
    return "\n".join(lines)


def result_text(pool):
    kitchen = [m for m in pool.members if m.department == "Kitchen"]
    service = [m for m in pool.members if m.department == "Service"]
    lines = [f"💰 *€{pool.total_tips:.2f} split*\n"]
    lines.append("🍳 *Kitchen*")
    for m in kitchen:
        share = " ½" if m.multiplier != 1.0 else ""
        lines.append(f"  {m.name} {m.hours}h{share} → *€{m.tips:.2f}*")
    lines.append("\n🍽️ *Service*")
    for m in service:
        share = " ½" if m.multiplier != 1.0 else ""
        lines.append(f"  {m.name} {m.hours}h{share} → *€{m.tips:.2f}*")
    lines.append(f"\n✅ Total: *€{sum(m.tips for m in pool.members):.2f}*")
    return "\n".join(lines)


MENU_TEXT = "👋 *Tip Split Bot*\n\nReady when you are!"


# ── Handlers ──────────────────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        MENU_TEXT, parse_mode="Markdown", reply_markup=main_menu_kb()
    )
    return MAIN_MENU


async def reset_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🔄 Reset!")
    context.user_data.clear()
    await query.edit_message_text(
        MENU_TEXT, parse_mode="Markdown", reply_markup=main_menu_kb()
    )
    return MAIN_MENU


async def main_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💰 *New Tip Split*\n\nEnter total tips today (€):",
        parse_mode="Markdown",
        reply_markup=reset_kb(),
    )
    return ASK_TOTAL


async def got_total(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        total = float(update.message.text.replace(",", "."))
        if total <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ Enter a positive number, e.g. `350`",
            parse_mode="Markdown", reply_markup=reset_kb(),
        )
        return ASK_TOTAL

    context.user_data["pool"] = TipPool(total)
    await update.message.reply_text(
        f"✅ *€{total:.2f}* set!\n\nWhich department goes first?",
        parse_mode="Markdown",
        reply_markup=dept_kb(),
    )
    return ASK_DEPT_ORDER


async def got_dept_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    dept = "Kitchen" if query.data == "dept_kitchen" else "Service"
    other = "Service" if dept == "Kitchen" else "Kitchen"
    context.user_data.update(current_dept=dept, other_dept=other, switched=False)
    emoji = DEPT_EMOJI[dept]
    await query.edit_message_text(
        f"{emoji} *{dept} crew*\n\nEnter first name:",
        parse_mode="Markdown",
        reply_markup=done_kb(dept),
    )
    return ASK_NAME


async def got_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    context.user_data["name"] = name
    await update.message.reply_text(
        f"👤 *{name}*\n\n⏱️ Hours worked?",
        parse_mode="Markdown",
        reply_markup=reset_kb(),
    )
    return ASK_HOURS


async def done_dept_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    pool = context.user_data.get("pool")
    if pool is None:
        await query.answer("Session expired — starting over.")
        await query.edit_message_text(
            MENU_TEXT, parse_mode="Markdown", reply_markup=main_menu_kb()
        )
        return MAIN_MENU

    current_dept = context.user_data["current_dept"]
    other_dept = context.user_data["other_dept"]
    switched = context.user_data["switched"]

    if not any(m.department == current_dept for m in pool.members):
        await query.answer(
            f"⚠️ Add at least one person to {current_dept} first!",
            show_alert=True,
        )
        return ASK_NAME

    await query.answer()

    if not switched:
        context.user_data.update(current_dept=other_dept, other_dept=current_dept, switched=True)
        emoji = DEPT_EMOJI[other_dept]
        await query.edit_message_text(
            f"{emoji} *{other_dept} crew*\n\nEnter first name:",
            parse_mode="Markdown",
            reply_markup=done_kb(other_dept),
        )
        return ASK_NAME

    pool.split()
    await query.edit_message_text(
        result_text(pool),
        parse_mode="Markdown",
        reply_markup=main_menu_kb(),
    )
    return MAIN_MENU


async def got_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        hours = float(update.message.text.replace(",", "."))
        if hours <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "⚠️ Enter a positive number, e.g. `7.5`",
            parse_mode="Markdown", reply_markup=reset_kb(),
        )
        return ASK_HOURS

    context.user_data["hours"] = hours
    name = context.user_data["name"]
    await update.message.reply_text(
        f"👤 *{name}* · {hours}h\n\nShare type?",
        parse_mode="Markdown",
        reply_markup=share_kb(),
    )
    return ASK_SHARE


async def got_share(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    pool = context.user_data.get("pool")
    if pool is None:
        await query.answer("Session expired — starting over.")
        await query.edit_message_text(
            MENU_TEXT, parse_mode="Markdown", reply_markup=main_menu_kb()
        )
        return MAIN_MENU

    await query.answer()
    multiplier = 1.0 if query.data == "share_full" else 0.5
    member = StaffMember(
        context.user_data["name"],
        context.user_data["hours"],
        context.user_data["current_dept"],
        multiplier,
    )
    pool.add_member(member)
    current_dept = context.user_data["current_dept"]
    roster = roster_text(pool.members)
    await query.edit_message_text(
        f"✅ *{member.name}* added\n\n{roster}\n\n{DEPT_EMOJI[current_dept]} Enter next {current_dept} name:",
        parse_mode="Markdown",
        reply_markup=done_kb(current_dept),
    )
    return ASK_NAME


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Cancelled.", reply_markup=main_menu_kb())
    return MAIN_MENU


async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        MENU_TEXT, parse_mode="Markdown", reply_markup=main_menu_kb()
    )
    return MAIN_MENU


# Matches the "🔄 Reset" text sent by the old persistent reply keyboard,
# or anyone typing "reset" manually.
RESET_TEXT_FILTER = filters.Regex(r"(?i)^(🔄 )?reset!?$")


async def stale_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Catches taps on buttons from old/expired messages so they don't spin forever
    query = update.callback_query
    await query.answer("This menu has expired — use /start", show_alert=True)


# ── App ───────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TOKEN).build()

    reset_btn = CallbackQueryHandler(reset_callback, pattern="^reset$")
    reset_text = MessageHandler(RESET_TEXT_FILTER, reset_command)
    reset_cmd = CommandHandler("reset", reset_command)

    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            reset_btn,
            reset_text,
            reset_cmd,
        ],
        states={
            MAIN_MENU: [
                reset_btn, reset_text, reset_cmd,
                CallbackQueryHandler(main_menu_callback, pattern="^new_split$"),
            ],
            ASK_TOTAL: [
                reset_btn, reset_text, reset_cmd,
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_total),
            ],
            ASK_DEPT_ORDER: [
                reset_btn, reset_text, reset_cmd,
                CallbackQueryHandler(got_dept_order, pattern="^dept_(kitchen|service)$"),
            ],
            ASK_NAME: [
                reset_btn, reset_text, reset_cmd,
                CallbackQueryHandler(done_dept_callback, pattern="^done_dept$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_name),
            ],
            ASK_HOURS: [
                reset_btn, reset_text, reset_cmd,
                MessageHandler(filters.TEXT & ~filters.COMMAND, got_hours),
            ],
            ASK_SHARE: [
                reset_btn, reset_text, reset_cmd,
                CallbackQueryHandler(got_share, pattern="^share_(full|half)$"),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            reset_cmd,
        ],
        allow_reentry=True,
    )

    app.add_handler(conv)
    # Any callback not consumed by the conversation gets answered here,
    # otherwise Telegram shows an endless loading spinner on the button.
    app.add_handler(CallbackQueryHandler(stale_button), group=1)
    print("Bot running")
    app.run_polling()


if __name__ == "__main__":
    main()
