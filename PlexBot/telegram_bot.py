"""
This file handles the telegram bot and it's functionality.
"""

import logging
import sys
import os
from threading import Thread
from functools import wraps
import traceback
# import datetime
# import weakref
# import shelve
# import signal
from emoji import emojize
import telegram
from telegram import (ReplyKeyboardMarkup,
                      # InlineKeyboardButton,
                      # InlineKeyboardMarkup,
                      ParseMode,
                      ChatAction)
from telegram.ext import (Updater,
                          CommandHandler,
                          MessageHandler,
                          Filters,
                          ConversationHandler,
                          # CallbackQueryHandler,
                          PicklePersistence)
from telegram.utils.helpers import mention_html
from .plex_api import Plex

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# General Fuctions
def token_required(func):
    """Resrict the wrapped functions to only be able to be called by admins"""
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        # user_id = update.effective_user.id
        def has_token(userdata):
            return True

        if has_token(context):
            return func(update, context, *args, **kwargs)
        else:
            pass
    return wrapped


def restricted_developer(func):
    """Restrict the wrapped methods to only be able to be called by admins"""
    @wraps(func)
    def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id not in str(os.getenv('DEVELOPER')):
            update.message.reply_text('You don\'t have purmission to do this.')
            logger.debug('Unauthorized access attempt by %s with ID: %s',
                         update.effective_user.first_name, user_id)
            return
        return func(update, context, *args, **kwargs)
    return wrapped


def send_typing_action(func):
    """Sends typing action while processing func command."""

    @wraps(func)
    def command_func(update, context, *args, **kwargs):
        context.bot.send_chat_action(chat_id=update.effective_message.chat_id,
                                     action=ChatAction.TYPING)
        return func(update, context,  *args, **kwargs)

    return command_func


def shutdown(signum, frame):
    """This function is called during shutdown and allows
    for last actions to be performed befor the proces exits
    """
    del frame  # Unused
    logger.debug("Statring shoutdown routine")


# Non member Functions
def help_message(update, context):
    """Show help messgae to user"""
    del context  # unused
    text = "This bot will inform you about the current state of coffee\n\
        /help\t\t diplay this help message\n\
        /start\t\t subscribe to the update list"

    # user_id = update.effective_user.id
    update.message.reply_text(text)


@restricted_developer
def manual_error(update, context):
    """Manualy raise error"""
    raise Exception('ErrorCommand')


# Other options
def error(update, context):
    """Log Errors caused by Updates."""
    # we want to notify the user of this problem.
    # This will always work, but not notify users if the update is an
    # callback or inline query, or a poll update.
    # In case you want this, keep in mind that sending the message
    # could fail
    if update.effective_message:
        text = "Hey. I'm sorry to inform you that an error happened while \
            I tried to handle your update. " \
               "My developer(s) will be notified."
        update.effective_message.reply_text(text)

    # This traceback is created with accessing the traceback object
    # from the sys.exc_info, which is returned as the
    # third value of the returned tuple. Then we use the traceback.format_tb
    # to get the traceback as a string, which
    # for a weird reason separates the line breaks in a list,
    # but keeps the linebreaks itself. So just joining an
    # empty string works fine.
    trace = "".join(traceback.format_tb(sys.exc_info()[2]))

    # lets try to get as much information from the telegram update as possible
    payload = ""

    # normally, we always have an user.
    # If not, its either a channel or a poll update.
    if update.effective_user:
        mention = mention_html(update.effective_user.id,
                               update.effective_user.first_name)
        payload += f' with the user {mention}'

    # there are more situations when you don't get a chat
    if update.effective_chat:
        payload += f' within the chat <i>{update.effective_chat.title}</i>'
        if update.effective_chat.username:
            payload += f' (@{update.effective_chat.username})'

    # but only one where you have an empty payload by now: A poll (buuuh)
    if update.poll:
        payload += f' with the poll id {update.poll.id}.'
    # lets put this in a "well" formatted text
    text = f"Hey.\n The error <code>{context.error}</code> \
        happened{payload}. The full traceback:\n\n\
        <code>{trace}</code>"
    # and send it to the dev(s)
    context.bot.send_message(
        str(os.getenv('DEVELOPER')),
        text,
        parse_mode=ParseMode.HTML)
    # we raise the error again, so the logger module catches it.
    # If you don't use the logger module, use it.
    raise Exception(text)


# Conversation handler stages
CHOICE, PASSWORD = range(2)


def start(update, context):
    """Start bot conversation"""

    del context  # unused
    reply_keyboard = [['sign-in', 'sing-out', '/cancel']]

    update.message.reply_text(
        'Hi! My I am the Plex Media bot.\n'
        'I will provide you accsess to your media stored on you plex serve.\n'
        'So I can funtion propperly you will first have to \
            sign in to you Plex account.\n'
        'Send /cancel to stop talking to me.\n\n'
        'Do you wnat to signin or signout?',
        reply_markup=ReplyKeyboardMarkup(reply_keyboard,
                                         one_time_keyboard=True))
    return CHOICE


# Conversation functions
def signin(update, context):
    """Initiate substribtion proccess"""
    # del context  # unused
    user = update.message.from_user
    logger.info("%s is trying to subscribe", user.first_name)
    update.message.reply_text('Please enter your username',
                              reply_markup=telegram.ReplyKeyboardRemove())
    return PASSWORD


def password(update, context):
    """Initiate substribtion proccess"""

    def login(username, password):
        plex = Plex(username=username, password=password, server='Server')
        return True
    # del context  # unused

    # user = update.message.from_user
    update.message.reply_text('Please enter your password',
                              reply_markup=telegram.ReplyKeyboardRemove())

    if login('username', 'password'):
        return ConversationHandler.END
    return CHOICE


# def password(update, context):
#     """Check password"""
#     del context  # unused
#     reply_keyboard = [['subscribe', 'unsubscribe', '/cancel']]
#     user = update.message.from_user
#     if update.message.text == str(PASSWORD):
#         logger.info("%s has entered the correct password", user.first_name)
#         try:
#             # DB.Add("Subscribers",update.message.chat["id"])
#             my_chat_ids.add(update.message.chat["id"])
#             logger.debug("%s has been added to the DB", user.first_name)
#             update.message.reply_text('You have sucsessfully signed up')
#             return ConversationHandler.END
#         except Exception as error_message:
#             logger.warning("%s could not to added to DB", user.first_name)
#             logger.info(error_message)
#             return ConversationHandler.END
#     else:
#         logger.info("%s Entered the wrong password", user.first_name)
#         update.message.reply_text('You have endered the wrong password\n'
#                                   'what do you want to do?',
#                                   reply_markup=ReplyKeyboardMarkup(
#                                       reply_keyboard,
#                                       one_time_keyboard=True)
#                                   )
#         return CHOICE


def cancel(update, context):
    """Cancel conversation"""
    del context  # unused
    user = update.message.from_user
    logger.debug("User %s canceled the conversation.", user.first_name)
    smiley = emojize(":smiley:", use_aliases=True)
    update.message.reply_text(f'Okey, let\'s talk another time {smiley}',
                              reply_markup=telegram.ReplyKeyboardRemove())
    return ConversationHandler.END


def remove(update, context):
    """Remove user from subscribtion list"""
    del context  # unused
    user = update.message.from_user
    try:
        # DB.Remove("Subscribers", update.message.chat["id"])
        # my_chat_ids.remove(update.message.chat["id"])
        # update.message.reply_text(
        #     'You have sucsessfully been removed from the mailing list')
        # logger.info("%s has been removed from the BD", user.first_name)
        return ConversationHandler.END
    except Exception as error_message:
        logger.warning("%s is not in the BD", user.first_name)
        logger.info(error_message)
        return ConversationHandler.END


conv_handler = ConversationHandler(
    entry_points=[CommandHandler('start', start)],
    states={
        CHOICE: [MessageHandler(Filters.regex('sign-out'), remove),
                 MessageHandler(Filters.regex('sign-in'), signin),
                 CommandHandler('cancel', cancel)],
        PASSWORD: [CommandHandler('cancel', cancel),
                   MessageHandler(Filters.all, password)],
    },
    fallbacks=[CommandHandler('cancel', error)])


def start_bot():
    logger.info('Startting bot')
    logger.debug('Token: %s', os.getenv('TELEGRAM_TOKEN'))

    # Get bot
    bot = telegram.Bot(token=str(os.getenv("TELEGRAM_TOKEN")))
    logger.debug('Using: %s', bot)

    # Displaying password and PID
    logger.debug("PID: %s", str(os.getpid()))

    # Create the Updater and pass it your bot's token.
    pickle_persistence = PicklePersistence(filename='bot_DB')

    updater = Updater(token=str(os.getenv("TELEGRAM_TOKEN")),
                      persistence=pickle_persistence,
                      use_context=True,
                      user_sig_handler=shutdown)

    def stop_and_restart():
        """Gracefully stop the Updater \
            and replace the current process with a new one"""
        updater.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)

    def restart(update, context):
        """Restart the telegram bot"""
        del context  # unused
        user = update.message.from_user
        logger.debug("%s hast triggered a restat of the bot",
                     user.first_name)
        update.message.reply_text('Bot is restarting...')
        Thread(target=stop_and_restart).start()

    # job_queue = updater.job_queue

    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    dispatcher.add_error_handler(error)  # log all errors
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(CommandHandler('error', manual_error))
    dispatcher.add_handler(CommandHandler('restart',
                                          restart,
                                          filters=Filters.user(
                                              username=os.getenv('sysadmin'))))

    # Seduled eventes
    # job_queue.run_repeating(update_coffee_state, interval=2, first=0)
    # job_queue.run_repeating(machine_off,
    #                        interval=datetime.timedelta(hours=24, minutes=0),
    #                        first=datetime.time(hour=17, minute=0))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()
