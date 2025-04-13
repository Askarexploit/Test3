#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import nest_asyncio
nest_asyncio.apply()
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    ConversationHandler,
)
import random
from typing import Dict, Any

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

TOKEN = "token telegram"

# Состояния диалога
MAIN_MENU, DETAILED_TALK = range(2)

# База знаний сценариев
DIALOG_FLOW = {
    "greeting": {
        "patterns": ["привет", "здравствуй", "хай"],
        "responses": [
            "Привет! Как я могу вам помочь сегодня?",
            "Здравствуйте! Что вас беспокоит?",
        ]
    },
    "sadness": {
        "patterns": ["грустно", "одиноко", "тоска"],
        "responses": [
            "Мне жаль это слышать. Когда началось это состояние?",
            "Расскажите подробнее о ваших чувствах.",
            "Что обычно помогает вам в такие моменты?",
        ],
        "follow_up": {
            "question": "Часто ли вы испытываете это чувство?",
            "responses": {
                "yes": "Понимаю. Давайте подумаем, что можно изменить...",
                "no": "Рад, что это редкое состояние. Что улучшает ваше настроение?"
            }
        }
    },
    "anxiety": {
        "patterns": ["тревога", "страх", "волнение"],
        "responses": [
            "Тревога - естественная реакция. Что именно вас беспокоит?",
            "Давайте разберемся с причинами. Опишите ситуацию подробнее.",
        ]
    },
    "happiness": {
        "patterns": ["счастлив", "радость", "восторг"],
        "responses": [
            "Это прекрасно! Что вызвало такие положительные эмоции?",
            "Поделитесь источником вашего счастья!",
        ]
    }
}

# Система контекста
user_context: Dict[int, Dict[str, Any]] = {}

def analyze_text(text: str) -> Dict[str, Any]:
    text_lower = text.lower()
    analysis = {
        "mood": "neutral",
        "keywords": [],
        "urgency": 0
    }
    
    # Определение ключевых слов
    for category, data in DIALOG_FLOW.items():
        for pattern in data["patterns"]:
            if pattern in text_lower:
                analysis["keywords"].append(category)
                analysis["mood"] = category
                analysis["urgency"] += 1
    
    # Простой анализ тональности
    positive_words = {"хорошо", "рад", "счастье"}
    negative_words = {"плохо", "грусть", "страх"}
    
    if any(word in text_lower for word in positive_words):
        analysis["mood"] = "positive"
    elif any(word in text_lower for word in negative_words):
        analysis["mood"] = "negative"
    
    return analysis

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data.clear()
    
    await update.message.reply_text(
        f"👋 Приветствую, {user.first_name}! Я ваш персональный эмоциональный ассистент.\n\n"
        "Вы можете:\n"
        "1. Поделиться текущим состоянием\n"
        "2. Обсудить конкретную ситуацию\n\n"
        "Просто напишите мне о том, что вас волнует."
    )
    return MAIN_MENU

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    text = update.message.text
    analysis = analyze_text(text)
    
    # Сохраняем контекст
    if user_id not in user_context:
        user_context[user_id] = {}
    
    user_context[user_id].update({
        "last_message": text,
        "analysis": analysis
    })
    
    # Логика ответа
    if analysis["mood"] == "sadness":
        response = await handle_sadness(update, context)
    elif analysis["mood"] == "anxiety":
        response = await handle_anxiety(update, context)
    elif analysis["mood"] == "happiness":
        response = await handle_happiness(update, context)
    else:
        response = await default_response(update, context)
    
    await update.message.reply_text(response)
    return MAIN_MENU

async def handle_sadness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    user_id = update.effective_user.id
    responses = DIALOG_FLOW["sadness"]["responses"]
    
    if "sadness_flow" in user_context[user_id]:
        return DIALOG_FLOW["sadness"]["follow_up"]["responses"]["yes"]
    
    user_context[user_id]["sadness_flow"] = True
    return random.choice(responses) + " " + DIALOG_FLOW["sadness"]["follow_up"]["question"]

async def handle_anxiety(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    responses = DIALOG_FLOW["anxiety"]["responses"]
    return random.choice(responses)

async def handle_happiness(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    responses = DIALOG_FLOW["happiness"]["responses"]
    return random.choice(responses) + " 🎉"

async def default_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> str:
    fallback_responses = [
        "Интересно. Можете развить мысль?",
        "Понял вас. Что вы при этом чувствуете?",
        "Расскажите об этом подробнее.",
    ]
    return random.choice(fallback_responses)

def main() -> None:
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            MAIN_MENU: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
            ],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == "__main__":
    main()


# In[ ]:




