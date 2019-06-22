#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# import webapp2
#
# class MainHandler(webapp2.RequestHandler):
#     def get(self):
#         self.response.write('Hello world!')


import logging
import os
from datetime import time
from sys import stdout

from telegram import ChatAction, InputMediaPhoto, InlineKeyboardButton, InlineKeyboardMarkup, \
    ParseMode
from telegram.error import TimedOut, BadRequest
from telegram.ext import Updater, CommandHandler, run_async, MessageHandler, Filters, ConversationHandler, \
    CallbackQueryHandler

from cloud_firestore import FirestoreData
from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USE_WEBHOOK, TELEGRAM_BOT_EXTERNAL_URL, TELEGRAM_GROUP, \
    ALLOWED_IDS, VK_API_OWNER_ID, VK_AUTH_URL
from vk_data import VKApi

# logging.basicConfig(level=logging.WARNING,
#                     # format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#                     )

if 'PORT' in os.environ:
    PORT = int(os.environ['PORT'])
else:
    PORT = 8080

GENERAL_VK = VKApi()
GENERAL_FIRESTORE = FirestoreData()
CHOOSING = 1

choose_button_list = [
    [InlineKeyboardButton("Да \U0001F44D", callback_data='yes'),
     InlineKeyboardButton("Нет \U0001F631", callback_data='no')],
    [InlineKeyboardButton("А как это? \U0001F914", callback_data='how')]
]
choose_markup = InlineKeyboardMarkup(choose_button_list)

url_button = [[InlineKeyboardButton("Авторизировать приложение в VK", url=VK_AUTH_URL)]]
url_markup = InlineKeyboardMarkup(url_button)

@run_async
def send_photos_on_schedule(context):
    media = []
    for _ in range(1, 8):
        photo_url, text = GENERAL_VK.get_random_photo()

        if photo_url:
            if len(text) > 1024:
                text = text[:1023]

            media.append(InputMediaPhoto(caption=text, media=photo_url))

    if media:
        context.bot.send_message(chat_id=TELEGRAM_GROUP, text='Фотографии сегодняшего дня')
        context.bot.send_chat_action(chat_id=TELEGRAM_GROUP, action=ChatAction.UPLOAD_PHOTO)
        context.bot.send_media_group(chat_id=TELEGRAM_GROUP, media=media, disable_notification=True, timeout=90)


@run_async
def send_photos(update, context):
    # print(update.effective_message.chat_id)

    if update.message.chat_id in ALLOWED_IDS:
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_PHOTO)
        media = []
        for i in range(1, 8):
            photo_url, text = GENERAL_VK.get_random_photo()

            if photo_url:
                text_length = len(text)
                if text_length > 1024:
                    text = text[:1023]
                # logging.error(text)
                media.append(InputMediaPhoto(caption=text, media=photo_url))

        try:
            update.message.reply_media_group(media, disable_notification=True, timeout=90)
        except TimedOut:
            update.message.reply_text('VK server timeout, try again')
        except BadRequest:
            error_message = [input_media.caption for input_media in media]
            logging.warning(f'error with {error_message}')
            update.message.reply_text('VK server timeout, try again')
            raise

    else:
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        update.message.reply_text('Access restricted')


@run_async
def start_command(update, context):
    if context.args:
        if context.args[0] == 'vk-auth':
            update.message.reply_text('Авторизируйся по ссылке, скопируй результат в адресной строке и вышли мне сюда',
                                      reply_markup=url_markup)


@run_async
def replied_message(update, context):
    # print('replied_message')
    # print(update)
    # print(context.user_data)
    if update.effective_chat.id in ALLOWED_IDS:
        # print(bool('photo' in update.effective_message.reply_to_message))
        if update.effective_message.reply_to_message.photo:
            # print(update.effective_message.reply_to_message.caption)
            context.user_data['comment'] = update.effective_message.text
            index = update.effective_message.reply_to_message.caption.find('@')
            context.user_data['photo_id'] = update.effective_message.reply_to_message.caption[:index]

            context.user_data['message_id'] = update.message.reply_text(
                f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>,'
                ' опубликовать твой коммент в VK?',
                reply_markup=choose_markup, quote=True, parse_mode=ParseMode.HTML).message_id

            return CHOOSING
    return ConversationHandler.END


@run_async
def callback_query(update, context):
    # print('callback_query')
    # print(update.callback_query.data)
    # print(context.user_data)
    if update.callback_query.data == 'how':
        context.bot.answer_callback_query(update.callback_query.id,
                                          text='Твой комментарий отсюда отправится прямиком под эту фотку '
                                               'в VK на память.\nДля этого нужно один единстенный раз, авторизироваться'
                                               ' через Telegram в VK', show_alert=True)
        return CHOOSING
    if update.callback_query.data == 'yes':
        vk_data = GENERAL_FIRESTORE.get_data_from_firestore(update.effective_user.id)
        if vk_data:
            if GENERAL_VK.create_comment_on_photo(context.user_data['photo_id'],
                                                  VK_API_OWNER_ID,
                                                  vk_data['vk_token'],
                                                  context.user_data['comment']):

                context.bot.answer_callback_query(update.callback_query.id, text='Коммент оставлен \U0001F44D')
            else:
                context.bot.answer_callback_query(update.callback_query.id, text='Произошла ошибка \U0001F61E')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id,
                                     text=f'<a href="tg://user?id={update.effective_user.id}">{update.effective_user.first_name}</a>,'
                                     ' для этого нужно один единстенный раз, авторизироваться'
                                     'через Telegram в VK',
                                     quote=True, parse_mode=ParseMode.HTML)
            context.bot.answer_callback_query(update.callback_query.id,
                                              text='Чтобы оставлять комментарии авторизируйся через VK',
                                              url=f'https://t.me/{context.bot.username}?start=vk-auth',
                                              show_alert=True)

    else:
        context.bot.answer_callback_query(update.callback_query.id, text='Хорошо \U0001F61E')
    context.bot.delete_message(chat_id=update.effective_chat.id, message_id=context.user_data['message_id'])
    return ConversationHandler.END


@run_async
def done(update, context, *args, **kwargs):
    if 'comment' in context.user_data:
        del context.user_data['comment']
    if 'photo_id' in context.user_data:
        del context.user_data['photo_id']

    update.message.reply_text('Что-то пошло не так')
    return ConversationHandler.END


@run_async
def vk_auth_string(update, context, *args, **kwargs):
    start_index = update.message.text.find('token=') + 6
    end_index = update.message.text.find('&expires_in')
    GENERAL_FIRESTORE.add_data_from_firestore(update.effective_user.id, update.message.text[start_index:end_index],
                                              first_name=update.effective_user.first_name,
                                              last_name=update.effective_user.last_name,
                                              telegram_username=update.effective_user.username)
    update.message.reply_text('Все тип-топ, теперь ты можешь отправлять комменты в VK из Telegram группы \U0001F44D')
    context.bot.send_message(chat_id=TELEGRAM_GROUP, text=f'Теперь <a href="tg://user?id={update.effective_user.id}">'
    f'{update.effective_user.first_name} </a>'
    f'может отправлять комменты в VK! Похлопаем \U0001F44F', parse_mode=ParseMode.HTML)


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    job_queue = updater.job_queue

    job_queue.run_daily(send_photos_on_schedule, time(6, 55))

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler('photos', send_photos))

    # dispatcher.add_handler(CommandHandler('time', start_comand))

    dispatcher.add_handler(CommandHandler('start', start_command))
    dispatcher.add_handler(MessageHandler(Filters.regex('^https://oauth.vk.com/blank.html'), vk_auth_string))

    # echo_handler = MessageHandler(Filters.all, send_photos)
    # dispatcher.add_handler(echo_handler)

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(Filters.reply, replied_message)],

        states={
            CHOOSING: [CallbackQueryHandler(callback_query)],
            # ConversationHandler.TIMEOUT: [MessageHandler(Filters.all, done)],
        },
        # conversation_timeout=10,
        # per_user=True,

        # per_message=True,

        fallbacks=[MessageHandler(Filters.all, done)],
        # name="my_conversation",
        # persistent=True
    )
    dispatcher.add_handler(conv_handler)

    if TELEGRAM_BOT_USE_WEBHOOK:
        # set up webhook
        updater.start_webhook(listen='127.0.0.1', port=PORT, url_path=TELEGRAM_BOT_TOKEN)
        updater.bot.set_webhook(url=f'{TELEGRAM_BOT_EXTERNAL_URL}/{TELEGRAM_BOT_TOKEN}')
    else:
        # if webhook couldn't be set up
        updater.start_polling()

    job_queue.start()
    stdout.write(f'Telegram bot coroutine has started\n{updater.bot.get_me()}\n')
    updater.idle()


if __name__ == "__main__":
    main()

# app = main()
