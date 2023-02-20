import datetime
import telebot
import sqlite3
import time
from   threading import Thread



########################################################################################################################
TOKEN = "/Your Token/"
bot = telebot.TeleBot(TOKEN)
########################################################################################################################
connect = sqlite3.connect('intro_cmds.db', check_same_thread=False)

cursor_intro = connect.cursor()
cursor_intro.execute("SELECT data FROM intro_cmds")
########################################################################################################################
cursor_cal = connect.cursor()

########################################################################################################################
@bot.message_handler(func=lambda message: message.text in refresh_intro())
def text_handler(msg):
    print(msg.chat.id)
    save_msg_id(msg.message_id)

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row('дедлайны', 'удалим смс','поменяем лексикон')
    save_msg_id(bot.send_message(msg.chat.id, 'слышу',reply_markup=keyboard).id)
    bot.register_next_step_handler(msg, step)



def step(msg):
    save_msg_id(msg.message_id)
    text = msg.text
    if text == 'поменяем лексикон':
        save_msg_id(bot.send_message(msg.chat.id, 'окей, погнали').id)
        time.sleep(0.5)
        save_msg_id(bot.send_message(msg.chat.id, 'реагирую на это:').id)
        time.sleep(0.5)
        save_msg_id(bot.send_message(msg.chat.id, '\n'.join(refresh_intro())).id)
        bot.register_next_step_handler(msg, handling_changes)
    elif text == 'дедлайны':

        if refresh_deadlines() == []:
            save_msg_id(bot.send_message(msg.chat.id, 'дедлайнов нет').id)
        else:
            save_msg_id(bot.send_message(msg.chat.id, '\n'.join(refresh_deadlines())).id)
            bot.register_next_step_handler(msg, delete_deadline)

    elif text == 'удалим смс':
        sqlite_select_query = """SELECT * from msg_id"""
        cursor_intro.execute(sqlite_select_query)
        records = cursor_intro.fetchall()
        for id in records:
            try:
                bot.delete_message(msg.chat.id, id[0])
                cursor_cal.execute("DELETE FROM msg_id WHERE id='{}';".format(id[0]))
            except:
                pass

        cursor_cal.execute("DELETE FROM msg_id;")
        connect.commit()


    else:
        wrong_ask(msg)







def delete_deadline(msg):
    save_msg_id(msg.message_id)
    text = str(msg.text).split(' ', 1)
    if text[0] == 'удалим':
        if text[1] == 'все':
            cursor_cal.execute("DELETE FROM deadlines;")
        else:
            cursor_cal.execute("DELETE FROM deadlines WHERE title='{}';".format(text[1]))
        save_msg_id(bot.send_message(msg.chat.id, 'четко').id)
        time.sleep(0.5)
        save_msg_id(bot.send_message(msg.chat.id, 'теперь:').id)
        if refresh_deadlines() == []:
            save_msg_id(bot.send_message(msg.chat.id, 'дедлайнов нет').id)

        else:
            save_msg_id(bot.send_message(msg.chat.id, '\n'.join(refresh_deadlines())).id)
    else:
        save_msg_id(bot.send_message(msg.chat.id, 'ну лан').id)



def handling_changes(msg):
    save_msg_id(msg.message_id)
    text = str(msg.text).split(' ', 1)
    if text[0] == 'добавим':
        sqlite_select_query = """SELECT * from intro_cmds"""
        cursor_intro.execute(sqlite_select_query)
        records = cursor_intro.fetchall()
        new_phrase = (len(records), text[1])
        cursor_intro.execute("INSERT INTO intro_cmds VALUES(?, ?);", new_phrase)

        save_msg_id(bot.send_message(msg.chat.id,'четко').id)
        time.sleep(0.5)
        save_msg_id(bot.send_message(msg.chat.id,'теперь:').id)
        save_msg_id(bot.send_message(msg.chat.id, '\n'.join(refresh_intro())).id)

    elif text[0] == 'удалим':
        cursor_intro.execute("DELETE FROM intro_cmds WHERE data='{}';".format(text[1]))
        save_msg_id(bot.send_message(msg.chat.id,'четко').id)
        time.sleep(0.5)
        save_msg_id(bot.send_message(msg.chat.id,'теперь:').id)

        save_msg_id(bot.send_message(msg.chat.id, '\n'.join(refresh_intro())).id)
    else:
        wrong_ask(msg)

########################################################################################################################


@bot.message_handler(func=lambda message: True)
def text_handler(msg):


    months = []
    days = []
    isMonthsIncluded = False
    data_m, data_d = refresh_calendar()

    for word in str(msg.text).split(' '):
        if word in data_m:
            months.append(word)
            isMonthsIncluded = True
        if word in data_d:
            days.append(word)

    if not isMonthsIncluded:
        return
    save_msg_id(msg.message_id)
    dates = [' '.join([x, y]) for x in days for y in months]
    dates.append('нет')

    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for data in dates:
        keyboard.add(telebot.types.KeyboardButton(data))
    save_msg_id(bot.send_message(msg.chat.id, 'поставить дедлайн?', reply_markup=keyboard).id)

    bot.register_next_step_handler(msg, name_deadline)


def name_deadline(msg):
    save_msg_id(msg.message_id)
    text = msg.text
    if text == 'нет':
        save_msg_id(bot.send_message(msg.chat.id, 'ну и иди в жопу').id)
    else:
        date = str(msg.text).split(' ')
        save_msg_id(bot.send_message(msg.chat.id, 'как назовем?').id)
        bot.register_next_step_handler(msg, make_deadline, date)



def make_deadline(msg, date):
    save_msg_id(msg.message_id)
    new_event = (msg.text, int(date[0]), date[1], 0, 0, 0)
    cursor_cal.execute("INSERT INTO deadlines VALUES(?, ?, ?, ?, ?, ?);", new_event)
    refresh_calendar()

    save_msg_id(bot.send_message(msg.chat.id, 'четко').id)
    time.sleep(0.5)
    save_msg_id(bot.send_message(msg.chat.id, 'текущие дедлайны').id)

    save_msg_id(bot.send_message(msg.chat.id, '\n'.join(refresh_deadlines())).id)

########################################################################################################################


def checking_deadlines():
    while True:
        all_months = ["январ", "феврал", "март", "апрел", "ма", "июн", "июл", "август", "сентябр", "октябр", "ноябр", "декабр"]
        refresh_deadlines()
        month = datetime.datetime.today().month
        day = datetime.datetime.today().day
        cursor_cal.execute("SELECT * FROM deadlines")
        deadlines = [obj for obj in cursor_cal.fetchall()]
        print(deadlines)
        for event in deadlines:
            day_week_futher = datetime.datetime.now() + datetime.timedelta(days = 7)

            numberMonthDead = 0
            for mon in range(len(all_months)):
                if all_months[mon] in event[2]:
                    numberMonthDead = mon + 1
            if day_week_futher.month >= numberMonthDead:
                if day_week_futher.day >= event[1]:
                    if event[3] == 0:
                        save_msg_id(bot.send_message(-1001740334149,
                                                     "{} - осталась неделя, дедлайн: {} {}".format(event[0], event[1], event[2])).id)
                        cursor_cal.execute("DELETE FROM deadlines WHERE title='{}';".format(event[0]))
                        refresh_deadlines()
                        event = (event[0], event[1], event[2], 1, event[4], event[5])
                        cursor_cal.execute("INSERT INTO deadlines VALUES(?, ?, ?, ?, ?, ?);", event)
                        refresh_calendar()




            day_3days_further = datetime.datetime.now() + datetime.timedelta(days=3)

            numberMonthDead = 0
            for mon in range(len(all_months)):
                if all_months[mon] in event[2]:
                    numberMonthDead = mon + 1
            if day_3days_further.month >= numberMonthDead:
                if day_3days_further.day >= event[1]:
                    if event[4] == 0:
                        save_msg_id(bot.send_message(-1001740334149,
                                         "{} - осталось три дня, дедлайн: {} {}".format(event[0], event[1], event[2])).id)
                        cursor_cal.execute("DELETE FROM deadlines WHERE title='{}';".format(event[0]))
                        refresh_deadlines()
                        event = (event[0], event[1], event[2], event[3], 1, event[5])
                        cursor_cal.execute("INSERT INTO deadlines VALUES(?, ?, ?, ?, ?, ?);", event)
                        refresh_calendar()






            day_futher = datetime.datetime.now() + datetime.timedelta(days=1)

            numberMonthDead = 0
            for mon in range(len(all_months)):
                if all_months[mon] in event[2]:
                    numberMonthDead = mon + 1
            if  day_futher.month >= numberMonthDead:
                if  day_futher.day >= event[1]:
                    if event[5] == 0:
                        save_msg_id(bot.send_message(-1001740334149,
                                         "{} - остался ДЕНЬ, дедлайн: {} {}".format(event[0], event[1], event[2])).id)
                        cursor_cal.execute("DELETE FROM deadlines WHERE title='{}';".format(event[0]))
                        refresh_deadlines()
                        event = (event[0], event[1], event[2], event[3], event[4], 1)
                        cursor_cal.execute("INSERT INTO deadlines VALUES(?, ?, ?, ?, ?, ?);", event)
                        refresh_calendar()

            day_today = datetime.datetime.now()

            numberMonthDead = 0
            for mon in range(len(all_months)):
                if all_months[mon] in event[2]:
                    numberMonthDead = mon + 1
            if day_today.month >= numberMonthDead:
                if day_today.day >= event[1]:
                    save_msg_id(bot.send_message(-1001740334149,
                                     "{} - дедлайн закрылся: {} {}".format(event[0], event[1], event[2])).id)
                    cursor_cal.execute("DELETE FROM deadlines WHERE title='{}';".format(event[0]))
                    refresh_deadlines()


        time.sleep(60)










########################################################################################################################

def save_msg_id(id):
    id = (str(id))
    cursor_cal.execute("INSERT INTO msg_id VALUES(?);", [id])
    connect.commit()

def refresh_intro():
    connect.commit()
    cursor_intro.execute("SELECT data FROM intro_cmds")
    intro_cmds = [obj[0] for obj in cursor_intro.fetchall()]
    return intro_cmds

def wrong_ask(msg):
    save_msg_id(msg.message_id)
    save_msg_id(bot.send_message(msg.chat.id, 'ничего не понял').id)
    time.sleep(0.5)
    save_msg_id(bot.send_message(msg.chat.id, 'иди нахуй').id)

def refresh_calendar():
    connect.commit()
    cursor_cal.execute("SELECT months FROM months")
    months = [obj[0] for obj in cursor_cal.fetchall()]
    cursor_cal.execute("SELECT numbers FROM numbers")
    numbers = [str(obj[0]) for obj in cursor_cal.fetchall()]
    return months, numbers

def refresh_deadlines():
    connect.commit()
    cursor_cal.execute("SELECT * FROM deadlines")

    deadlines = [' '.join([obj[0], str(obj[1]), obj[2]]) for obj in cursor_cal.fetchall()]
    return deadlines

def main():
    th = Thread(target=checking_deadlines)
    th.start()
    
    bot.polling()

if __name__ == '__main__':
    main()

