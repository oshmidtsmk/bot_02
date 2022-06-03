from message_data import ReminderData


class MemoryDataSource:
    """ Saving reminder to the dictionary """

    def __init__(self):
        self.reminders = dict()

    def add_reminder(self, chat_id, message, time):
        message_data = ReminderData(message, time)
        self.reminders[chat_id] = message_data #The key is the chat id because it's unique for each chatbAnd in this way, the bot will be able to distinguish reminders of different users.
        return message_data
