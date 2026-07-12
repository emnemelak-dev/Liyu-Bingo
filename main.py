import logging
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

# Logging ማዋቀር
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# የጨዋታ መረጃዎችን መያዣ (In-Memory Storage)
games = {}


def generate_bingo_card():
    """5x5 የቢንጎ ካርድ ያዘጋጃል (ከ 1 እስከ 75)"""
    col_B = random.sample(range(1, 16), 5)
    col_I = random.sample(range(16, 31), 5)
    col_N = random.sample(range(31, 46), 5)
    col_G = random.sample(range(46, 61), 5)
    col_O = random.sample(range(61, 76), 5)

    # የመካከለኛው ቦታ (Center) "FREE" ወይም የተሰመረበት ያደርገዋል
    col_N[2] = "FREE"

    card = []
    for row in range(5):
        card.append(
            [
                col_B[row],
                col_I[row],
                col_N[row],
                col_G[row],
                col_O[row],
            ]
        )
    return card


def create_keyboard(card, marked):
    """የቢንጎ ካርዱን ወደ Telegram Inline Buttons ይለውጣል"""
    keyboard = []
    for r in range(5):
        row_buttons = []
        for c in range(5):
            val = card[r][c]
            # ምልክት የተደረገባቸውን ቁጥሮች በ ❌ ወይም ✅ ይለያል
            if (r, c) in marked or val == "FREE":
                text = f"✅ {val}"
            else:
                text = str(val)
            row_buttons.append(
                InlineKeyboardButton(text, callback_data=f"cell_{r}_{c}")
            )
        keyboard.append(row_buttons)

    # ተጨማሪ የጨዋታ አዝራሮች
    keyboard.append(
        [
            InlineKeyboardButton("🎲 ቁጥር ሳብ (Draw)", callback_data="draw_num"),
            InlineKeyboardButton("🏆 BINGO!", callback_data="check_bingo"),
        ]
    )
    return InlineKeyboardMarkup(keyboard)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """የ /start ትዕዛዝ ሲላክ ጨዋታ ይጀምራል"""
    chat_id = update.effective_chat.id
    card = generate_bingo_card()

    games[chat_id] = {
        "card": card,
        "marked": {(2, 2)},  # የመካከለኛው FREE ቦታ ምልክት ተደርጎበታል
        "drawn_numbers": [],
    }

    reply_markup = create_keyboard(card, games[chat_id]["marked"])
    await update.message.reply_text(
        "🎉 **እንኳን ወደ Bingo ጨዋታ በደህና መጡ!** 🎉\n\n"
        "ካርድዎ ከታች ቀርቧል። 'ቁጥር ሳብ' የሚለውን በመጫን ይጫወቱ!",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """የአዝራሮች (Buttons) ምላሽ ማስተናገጃ"""
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    if chat_id not in games:
        await query.edit_message_text(
            "ጨዋታው አልተገኘም። እባክዎ አዲስ ጨዋታ ለመጀመር /start ይበሉ።"
        )
        return

    game = games[chat_id]
    data = query.data

    if data.startswith("cell_"):
        # ተጫዋቹ ሳጥን ሲጫን
        _, r, c = data.split("_")
        r, c = int(r), int(c)
        val = game["card"][r][c]

        if val in game["drawn_numbers"] or val == "FREE":
            game["marked"].add((r, c))
            reply_markup = create_keyboard(game["card"], game["marked"])
            drawn_str = ", ".join(map(str, game["drawn_numbers"]))
            await query.edit_message_text(
                f"የወጡ ቁጥሮች: [{drawn_str}]\nየመጨረሻው የወጣው: **{game['drawn_numbers'][-1] if game['drawn_numbers'] else 'የለም'}**",
                reply_markup=reply_markup,
                parse_mode="Markdown",
            )
        else:
            await query.answer(
                "ይህ ቁጥር ገና አልወጣም! እባክዎ የወጡትን ብቻ ይምረጡ።",
                show_alert=True,
            )

    elif data == "draw_num":
        # አዲስ ቁጥር ማውጣት
        all_nums = set(range(1, 76))
        drawn = set(game["drawn_numbers"])
        remaining = list(all_nums - drawn)

        if not remaining:
            await query.answer("ሁሉም ቁጥሮች ወጥተዋል!", show_alert=True)
            return

        new_num = random.choice(remaining)
        game["drawn_numbers"].append(new_num)

        reply_markup = create_keyboard(game["card"], game["marked"])
        drawn_str = ", ".join(map(str, game["drawn_numbers"]))
        await query.edit_message_text(
            f"የወጡ ቁጥሮች: [{drawn_str}]\nየመጨረሻው የወጣው: **{new_num}**",
            reply_markup=reply_markup,
            parse_mode="Markdown",
        )

    elif data == "check_bingo":
        # BINGO ማለቱን መፈተሽ
        if len(game["marked"]) >= 5:  # በቀላል ደረጃ የተሰራ
            await query.edit_message_text(
                "🎉 **እንኳን ደስ አለዎት! BINGO ብለዋል!** 🏆\n\nአዲስ ጨዋታ ለመጀመር /start ይበሉ።"
            )
            del games[chat_id]
        else:
            await query.answer("ገና ቢንጎ አልሰሩም! ይሞክሩ።", show_alert=True)


def main():
    # ቦት ቶከንዎን (Bot Token) እዚህ ያስገቡ
    BOT_TOKEN = "8680680071:AAH-2szhMnDrstNLtojcWJlerBvTEMYfPf4"

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("ቦቱ መስራት ጀምሯል...")
    app.run_polling()


if __name__ == "__main__":
    main()
