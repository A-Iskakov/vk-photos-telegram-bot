from datetime import time
from functools import wraps

from sys import stdout

from telegram import ChatAction, InputMediaPhoto

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters

from settings import TELEGRAM_BOT_TOKEN, TELEGRAM_BOT_USE_WEBHOOK, TELEGRAM_BOT_EXTERNAL_URL, TELEGRAM_GROUP

from vk_data import VKApi


def send_typing_action_decorator(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_PHOTO)
        return func(update, context, *args, **kwargs)

    return command_func


def send_stats_on_schedule(context):
    media = []
    for _ in range(1, 6):
        photo_url, text = VKApi().get_random_photo()

        if photo_url:
            media.append(InputMediaPhoto(caption=text, media=photo_url))

    if media:
        context.bot.send_message(chat_id=TELEGRAM_GROUP, text='Фотографии сегодняшего дня')
        context.bot.send_chat_action(chat_id=TELEGRAM_GROUP, action=ChatAction.UPLOAD_PHOTO)
        context.bot.send_media_group(chat_id=TELEGRAM_GROUP, media=media)


def send_photos(update, context):
    # print(update.effective_message.chat_id)

    if update.message.chat_id == TELEGRAM_GROUP:
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_PHOTO)
        media = []
        for _ in range(1, 6):
            photo_url, text = VKApi().get_random_photo()

            if photo_url:
                # update.message.reply_text(
                #     text_message,
                #     parse_mode=ParseMode.HTML)
                media.append(InputMediaPhoto(caption=text, media=photo_url))

        update.message.reply_media_group(media, disable_notification=True)
    else:
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id, action=ChatAction.UPLOAD_PHOTO)
        update.message.reply_text('Access restricted')


if __name__ == "__main__":

    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    job_queue = updater.job_queue

    job_queue.run_daily(send_stats_on_schedule, time(21, 53))

    dispatcher = updater.dispatcher

    send_stats_handler = CommandHandler('photos', send_photos)
    dispatcher.add_handler(send_stats_handler)

    echo_handler = MessageHandler(Filters.all, send_photos)
    dispatcher.add_handler(echo_handler)

    if TELEGRAM_BOT_USE_WEBHOOK:
        # set up webhook
        updater.start_webhook(listen='127.0.0.1', port=8001, url_path=TELEGRAM_BOT_TOKEN)
        updater.bot.set_webhook(url=f'{TELEGRAM_BOT_EXTERNAL_URL}/{TELEGRAM_BOT_TOKEN}')
    else:
        # if webhook couldn't be set up
        updater.start_polling()

    stdout.write(f'Telegram bot coroutine has started\n{updater.bot.get_me()}\n')
    updater.idle()
