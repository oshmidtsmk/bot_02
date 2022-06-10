#DB

from telegram.ext import (Updater, CommandHandler, ConversationHandler, MessageHandler,
                                                Filters, CallbackContext)
from telegram import KeyboardButton, ReplyKeyboardMarkup, Update
from data_source import DataSource
import os
import threading
import time
import datetime # needed to convert time sting to datetime object needed for the db.
import logging
import sys

MODE = "prod"
TOKEN = "5113468715:AAEI6SJIZfh_MdkhSRKDMr2h7EYbKsEgBL4"
#MODE = os.getenv("MODE")
#TOKEN = os.getenv("TOKEN")
ENTER_MESSAGE, ENTER_TIME = range(2)  #Two states of add reminder btn.
ADD_REMINDER_TEXT = 'Add Reminder ⏰'
INTERVAL = 30 # frequency of checking reminders.
DATABASE_URL = "postgres://eehcracordzsii:4eb0ceaee3ca1072898ffee53b5d26163ed2f7f0fd6ff82dd7bb5300ff2f5d93@ec2-54-228-32-29.eu-west-1.compute.amazonaws.com:5432/d44hf4rj4drtg8"
#"postgres://bot_02_user:password@localhost:5432/bot_02"
#"postgres://eehcracordzsii:4eb0ceaee3ca1072898ffee53b5d26163ed2f7f0fd6ff82dd7bb5300ff2f5d93@ec2-54-228-32-29.eu-west-1.compute.amazonaws.com:5432/d44hf4rj4drtg8"

datasource = DataSource(DATABASE_URL) # is needed to save entered message and data in the dict.
#dataSource = DataSource(os.environ.get("DATABASE_URL"))
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')# basic configuration of logger.
logger = logging.getLogger()

if MODE == "dev":
    def run():
        logger.info("Start in DEV mode")
        updater.start_polling()
elif MODE == "prod":
    def run():
        logger.info("Start in PROD mode")
        updater.start_webhook(listen="0.0.0.0", port=int(os.environ.get("PORT", "8443")), url_path=TOKEN,
                              webhook_url="https://{}.herokuapp.com/{}".format(os.environ.get("APP_NAME"), TOKEN))
else:
    logger.error("No mode specified!")
    sys.exit(1)


def start_handler(update, context):  #(update:Update, context: CallbackContext) are available due to use_context = True for the updater.
#CallbackContext contains user_data wich is the dict. For each update for the same user this dict willl be the same.
    update.message.reply_text("Hello, creator!", reply_markup = add_reminder_button())

def add_reminder_button():
    keybord = [[KeyboardButton(ADD_REMINDER_TEXT)]]
    return ReplyKeyboardMarkup(keybord)


def add_reminder_handler(update, context): #or I could add #(update: Update, context: CallbackContext)
    """ ask the user to enter the message and pass control to the next date """
    update.message.reply_text("Please enter a message of the reminder")
    return ENTER_MESSAGE

def enter_message_handler(update, context): #or I could add #(update: Update, context: CallbackContext)
    """ extract the entered message and save it in the context and after all ask the user to enter the time """
    update.message.reply_text("Please add the time")
    #saving the netered message in the user_data dict with assignins to the custom key of the dec the value of the text.
    context.user_data['message_text'] = update.message.text
    return ENTER_TIME # Returning the next state of the add_reminder btn.

def enter_time_handler(update, context): #or I could add #(update: Update, context: CallbackContext)
    """ Combine together message and time to some object and save it to the in-memory dictionary """
    message_text = context.user_data['message_text'] #extract previously saved message text
    time = datetime.datetime.strptime(update.message.text, '%d/%m/%Y %H:%M') #converting the sting to the time object that is needed for the DB.
    message_data = datasource.create_reminder(update.message.chat_id, message_text, time) #saving the msg and time in the dict.
    #notifying the user about susccesfully save reminder
    update.message.reply_text("Your reminder: "+ message_data.__repr__())
    return ConversationHandler.END #ending the  converstion.

    #Accordingly, we need to create some class that will hold mentioned properties.

def start_reminders_task():
    """ create and run the thread that will calling the function to check if teh the reminder shoud be fired. """
    thread = threading.Thread(target = check_reminders, args=())
    thread.deamon = True #you should consider the daemon thread as a thread that runs in the background without worrying about shutting it down.
    thread.start()

def check_reminders():
    """ Check each 30 sec if the conditon to send riminder is True and send the reminider if it is. """
    while True:
        for reminder_data in datasource.get_all_reminders():
            if reminder_data.should_be_fired():
                datasource.fire_reminder(reminder_data.reminder_id)
                updater.bot.send_message(reminder_data.chat_id, reminder_data.message)
        time.sleep(INTERVAL)

if __name__ == '__main__':
    # Updater is the core class that recieves updates from the bot and passes them to dispatcher
    updater = Updater(TOKEN, use_context=True) #the dispatcher will create single context for entire update. As a result, the CallbackContext object will be available with the Update object in the handler
    #dispatcher class diptaptches all kinds for updates to its registeres handlers
    # CallbackContext contains a very useful property which names user_data
        #It's a dictionary that can be used to keep any data in. For each update from the same user it will be the same dictionary.
    updater.dispatcher.add_handler(CommandHandler("start", start_handler))
    #conv_handler used to hold a conversation through Telegram updates by managing collections of other handlers
    #Here you can also define a state for TIMEOUT to define the behavior when conversation_timeout is exceeded
        #and a state for WAITING to define behavior when a new update is received
        #while the previous handler is not finished.
    conv_handler = ConversationHandler(
        entry_points = [MessageHandler(Filters.regex(ADD_REMINDER_TEXT), add_reminder_handler)], # Regex, which will match a message and follow it to add_reminder_handler.
        states = {
            ENTER_MESSAGE: [MessageHandler(Filters.all, enter_message_handler)],
            ENTER_TIME: [MessageHandler(Filters.all, enter_time_handler)]
        },
        fallbacks = [] #is used if the user is currently in a conversation but the state has no associated handler. You could use this for a /cancel command or to let the user know their message was not recognized.
    )
    updater.dispatcher.add_handler(conv_handler)
    datasource.create_tables()
    run()
    start_reminders_task()



# the updater can
