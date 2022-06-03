import datetime


class ReminderData:
    """ hold mentioned properties needed for saving messaage and the time in MemoryDataSource dict. """


    def __init__(self, row): #row is needed for db.
        self.reminder_id = row[0]
        self.chat_id = row[1]
        self.message = row[2]
        self.time = row[3]
        self.fired = row[4]

    def __repr__(self):
        return f"Message: {self.message}; At Time: {self.time.strftime('%d/%m/%Y %H:%M')}"
        #return "Message: {0}; At Time: {1}".format(self.message, self.time.strftime('%d/%m/%Y %H:%M'))

    def should_be_fired(self):
        """ conditaions to fire the reminder. """
        return self.fired is False and datetime.datetime.today() >= self.time
