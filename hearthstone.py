from telegram.ext import Updater
import urllib.request as ur
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup, Update
from telegram.ext import CallbackContext, Filters
from telegram.ext import CommandHandler, MessageHandler, ConversationHandler
from bs4 import BeautifulSoup

# CARLOS MANUEL POZUELO RIVAS - HEARTHSTONE LIBRARY SCRAPPER

# Text strings
SELECT_SET = '-> Select set'
GO_BACK = '-> Search cards'
SELECT_CLASS = '-> Select class'

# Conversation status
CONFIG, SET, CLASS = range(3)

current_set = {}
current_set_value = {}

current_class = {}
current_class_value = {}

TOKEN = ''

def get (url):
    req = ur.Request(url)
    req.add_header('User-Agent', 'Chrome/71.0.3578.98 Safari/537.36')
    f = ur.urlopen(req)

    s = f.read().decode()
    f.close()
    return s

def search_sets():
    doc = get(f'https://www.hearthstonetopdecks.com/cards/')
    soup = BeautifulSoup(doc, 'html.parser')
    all_sets = soup.find('select', {'name':'set'}).find_all('option')
    values = {}
    for set in all_sets:
        values[set.string] = set['value']
    return values

def search_classes():
    doc = get(f'https://www.hearthstonetopdecks.com/cards/')
    soup = BeautifulSoup(doc, 'html.parser')
    all_classes = soup.find('select', {'name':'class'}).find_all('option')
    values = {}
    for set in all_classes:
        values[set.string] = set['value']
    return values

def change_set(update: Update, context: CallbackContext):
    sets = search_sets()
    buttons = []
    for set in sets:
        buttons.append([set])
    # print(buttons)
    set = 'All Sets'
    if update.effective_user in current_set:
        set = current_set[update.effective_user]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Select desired set. Current set is {set}", reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    return SET

def change_class(update: Update, context: CallbackContext):
    classes = search_classes()
    buttons = []
    for c_class in classes:
        buttons.append([c_class])
    c_class = 'All Classes'
    if update.effective_user in current_class:
        c_class = current_class[update.effective_user]
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Select desired class. Current class is {c_class}", reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    return CLASS


def set_set(update: Update, context: CallbackContext):
    current_set[update.effective_user] = update.message.text
    current_set_value[update.effective_user] = search_sets()[update.message.text]
    data = current_set[update.effective_user]
    # print(current_set)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Set changed succesfully. Current set is {data}.")
    return configure(update,context)

def set_class(update: Update, context: CallbackContext):
    current_class[update.effective_user] = update.message.text
    current_class_value[update.effective_user] = search_classes()[update.message.text]
    data = current_class[update.effective_user]
    # print(current_set)
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Class changed succesfully. Current class is {data}.")
    return configure(update,context)

def search(update: Update, context: CallbackContext):
    if update.effective_user not in current_set_value:
        current_set_value[update.effective_user] = ''
    if update.effective_user not in current_class_value:
        current_class_value[update.effective_user] = ''
    doc = get(f'https://www.hearthstonetopdecks.com/cards/?st={update.message.text}&class={current_class_value[update.effective_user]}&set={current_set_value[update.effective_user]}')
    soup = BeautifulSoup(doc, 'html.parser')
    cards = soup.find_all("div", {"class": "card-item"})
    if len(cards) > 5:
        context.bot.send_message(chat_id=update.effective_chat.id, text=f'⚠ {len(cards)} results found. Only 5 results will be shown ⚠')
        del cards[5:]
    if len(cards) == 0:
        context.bot.send_photo(chat_id=update.effective_chat.id, photo='http://www.hearthcards.net/cards/11e3248a.jpg', caption='Card not found! Sorry!')
        return ConversationHandler.END
    for card in cards:
        img = card.find("img")['src']
        link = card.find('a')
        details = get(link['href'])
        soup_detail = BeautifulSoup(details, 'html.parser')
        name = soup_detail.find('h1').string
        flavour = soup_detail.find('em').string
        tags = soup_detail.find('article').find_all('li')
        clase = 'Neutral'
        for tag in tags:
            strong = tag.find('strong').string
            if strong == 'Type:':
                type = tag.find('a').string
            elif strong == 'Class:':
                clase = tag.find('a').string
            elif strong == 'Set:':
                set = tag.find('a').string

        text = f'{name} ({clase} {type.lower()}, {set})\n\n{flavour}'
        context.bot.send_photo(chat_id=update.effective_chat.id, photo=img, caption=text)
        # print (row.prettify())
    return ConversationHandler.END

def start(update: Update, context: CallbackContext):
    context.bot.send_message(chat_id=update.effective_chat.id, text="Hi! Type the name of a card and I'll send you up to 5 results! 😉")

def configure(update: Update, context: CallbackContext):
    buttons = [[KeyboardButton(SELECT_SET), KeyboardButton(SELECT_CLASS), KeyboardButton(GO_BACK)]]
    context.bot.send_message(chat_id=update.effective_chat.id, text="Select additional filters", reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    return CONFIG

def analyze(update: Update, context: CallbackContext):
    if update.message.text == SELECT_SET: return change_set(update, context)
    if update.message.text == SELECT_CLASS: return change_class(update, context)
    return ConversationHandler.END

def main():
    updater = Updater(token=TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    start_handler = CommandHandler('start', start)
    search_handler = MessageHandler(Filters.regex('^[^\/].*'), search)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('configure', configure), search_handler],
        states= {
            CONFIG: [MessageHandler(Filters.text, analyze)],
            SET: [MessageHandler(Filters.text, set_set)],
            CLASS: [MessageHandler(Filters.text, set_class)]
        },
        fallbacks=[CommandHandler('cancel', ConversationHandler.END)],
    )

    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(start_handler)
    updater.start_polling()
    updater.idle()

main()
