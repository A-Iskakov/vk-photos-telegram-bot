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


import os
from datetime import time
from sys import stdout

from telegram import ChatAction, InputMediaPhoto, ParseMode
from telegram.ext import Updater, CommandHandler

from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USE_WEBHOOK, TELEGRAM_BOT_EXTERNAL_URL, TELEGRAM_GROUP, \
    ALLOWED_IDS
from vk_data import VKApi

# import logging
# logging.basicConfig(level=logging.DEBUG,
#                     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if 'PORT' in os.environ:
    PORT = int(os.environ['PORT'])
else:
    PORT = 8080

GENERAL_VK = VKApi()


def send_photos_on_schedule(context):
    media = []
    for _ in range(1, 6):
        photo_url, text = GENERAL_VK.get_random_photo()

        if photo_url:
            media.append(InputMediaPhoto(caption=text, media=photo_url))

    if media:
        context.bot.send_message(chat_id=TELEGRAM_GROUP, text='Фотографии сегодняшего дня')
        context.bot.send_chat_action(chat_id=TELEGRAM_GROUP, action=ChatAction.UPLOAD_PHOTO)
        context.bot.send_media_group(chat_id=TELEGRAM_GROUP, media=media)


def send_photos(update, context):
    # print(update.effective_message.chat_id)

    if update.message.chat_id in ALLOWED_IDS:
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_PHOTO)
        media = []
        for _ in range(1, 6):
            photo_url, text = GENERAL_VK.get_random_photo()

            if photo_url:
                # update.message.reply_text(
                #     text_message,
                #     parse_mode=ParseMode.HTML)
                media.append(InputMediaPhoto(caption=text, media=photo_url, parse_mode=ParseMode.HTML))

        update.message.reply_media_group(media, disable_notification=True)
    else:
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.TYPING)
        update.message.reply_text('Access restricted')


def main():
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    job_queue = updater.job_queue

    job_queue.run_daily(send_photos_on_schedule, time(6, 55))

    dispatcher = updater.dispatcher

    send_photos_handler = CommandHandler('photos', send_photos)
    dispatcher.add_handler(send_photos_handler)

    # echo_handler = MessageHandler(Filters.all, send_photos)
    # dispatcher.add_handler(echo_handler)

    if TELEGRAM_BOT_USE_WEBHOOK:
        # set up webhook
        updater.start_webhook(listen='127.0.0.1', port=PORT, url_path=TELEGRAM_BOT_TOKEN)
        updater.bot.set_webhook(url=f'{TELEGRAM_BOT_EXTERNAL_URL}/{TELEGRAM_BOT_TOKEN}')
    else:
        # if webhook couldn't be set up
        updater.start_polling()

    stdout.write(f'Telegram bot coroutine has started\n{updater.bot.get_me()}\n')
    updater.idle()


if __name__ == "__main__":
    main()

# app = main()
