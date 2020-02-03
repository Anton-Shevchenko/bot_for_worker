from django.shortcuts import render
import telebot
from telebot import types
from .models import Worker, Pause, Statistic
import datetime
from datetime import timedelta
from datetime import timezone
import pytz

API_TOKEN = '1062766086:AAGDCBiJK4C_VLKDs3D_s7CPIlDrL1t5_78'
bot = telebot.TeleBot(API_TOKEN)

tz = pytz.timezone('Etc/GMT-2')
def list(request):
    post()
    return render(request, 'main/list.html', {})


def post():
    # Handle '/start' and '/help'
    @bot.message_handler(commands=['start'])
    def start(message):
        stat = Statistic.objects.filter(worker_id=message.chat.id,
                                        current_day=datetime.datetime.today().strftime('%Y-%m-%d'))
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if stat:
            markup.row('📊 Статистика')
        else:
            markup.row('✅ В сети', '🚫 Не в сети')
            markup.row('📊 Статистика')
        bot.send_message(chat_id=message.chat.id, text='Привет', reply_markup=markup)

    @bot.message_handler(func=lambda message: True, content_types=['text'])
    def select(message):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        if message.text == '✅ В сети':
            markup.row('🏢 Офис', '🏠 Дом')
            markup.row('✖ Отмена')
            bot.send_message(chat_id=message.chat.id, text='Работа', reply_markup=markup)

        elif message.text == '🚫 Не в сети':
            markup.row('🔕 Отгул', '💊️ Больничный')
            markup.row('✖ Отмена')
            bot.send_message(chat_id=message.chat.id, text='🚫 Не в сети', reply_markup=markup)

        elif message.text == '💊️ Больничный':
            markup = types.InlineKeyboardMarkup()
            sick_one = types.InlineKeyboardButton(text='от 1⃣ до 3⃣ дней', callback_data='|от 1 до 3 дней')
            sick_two = types.InlineKeyboardButton(text='от 3⃣ до 5⃣ дней', callback_data='|от 3 до 5 дней')
            sick_three = types.InlineKeyboardButton(text='более 5⃣ дней', callback_data='|более 5⃣ дней')
            markup.add(sick_one)
            markup.add(sick_two)
            markup.add(sick_three)
            bot.send_message(chat_id=message.chat.id, text='💊️ Больничный', reply_markup=markup)

        elif message.text == '🔕 Отгул':
            obj, created = Statistic.objects.update_or_create(worker_id=message.chat.id,
                                                              current_day=datetime.datetime.today().strftime(
                                                                  '%Y-%m-%d'))
            obj.wait = 2
            obj.save()
            bot.send_message(chat_id=message.chat.id, text='📝 Укажите причину')

        elif message.text == '✖ Отмена':
            try:
                worker = Statistic.objects.get(worker_id=message.chat.id,
                                           current_day=datetime.datetime.today().strftime('%Y-%m-%d'))
                worker.delete()
            except:
                pass

            markup.row('✅ В сети', '🚫 Не в сети')
            markup.row('📊 Статистика')
            bot.send_message(chat_id=message.chat.id, text='✖ Отмена', reply_markup=markup)


        elif message.text == '🏢 Офис' or message.text == '🏠 Дом':
            get, create = Statistic.objects.get_or_create(worker_id=message.chat.id,
                                            current_day=datetime.datetime.today().strftime('%Y-%m-%d'))
            get.wait = 1
            get.place = message.text
            get.save()
            bot.send_message(chat_id=message.chat.id, text='📝 Опишите вашу задачу')

        elif message.text == '⏸ Пауза':
            stat = Statistic.objects.filter(worker_id=message.chat.id, current_status='Активный').first()
            stat.current_status = 'Пауза'
            stat.save()
            get, pause = Pause.objects.get_or_create(statistic_id=stat.id)
            get.start_pause = datetime.datetime.now(pytz.utc)
            get.save()
            markup.row('▶  Продолжить', '⏹️ Стоп')
            markup.row('📊 Статистика')
            bot.send_message(chat_id=message.chat.id, text='⏸ Пауза', reply_markup=markup)

        elif message.text == '⏹️ Стоп':
            stat = Statistic.objects.filter(worker_id=message.chat.id, current_day=datetime.datetime.today().strftime('%Y-%m-%d')).first()
            stat.current_status = 'Закончил'
            stat.end_time = datetime.datetime.now(tz=tz)
            stat.save()
            get, pause = Pause.objects.get_or_create(statistic_id=stat.id)
            markup.row('☑ Завершить')
            diff_time = str(datetime.datetime.now(pytz.utc) - stat.start_time).split(".")[0]
            bot.send_message(chat_id=message.chat.id,
                             text='⚙️ Задача: ' + stat.task + '\n' +
                                  '⏳️ Время начала: ' + str((stat.start_time+timedelta(hours=2)).strftime('%H:%M')) + '\n' +
                                  '🍽 Обед: ' + str(get.start_pause) + '\n' +
                                  '⌛️ Время ухода: ' + str(stat.end_time.strftime('%H:%M')) + '\n' +
                                  '〰️〰️〰️〰️〰️〰️〰️〰️〰️〰 ' + '\n' +
                                  '⏱ Отработано часов: ' + diff_time + '\n' +
                                  '🍽 Время обеда: ' + str(get.total_time).split('.')[0] + '\n' +
                                  '〰️〰️〰️〰️〰️〰️〰️〰️〰️〰 ',
                             reply_markup=markup)

        elif message.text == '▶  Продолжить':
            stat = Statistic.objects.filter(worker_id=message.chat.id, current_status='Пауза').first()
            stat.current_status = 'Активный'
            stat.save()
            pause = Pause.objects.get(statistic_id=stat.id)
            pause.total_time += datetime.datetime.now(pytz.utc) - pause.start_pause
            pause.save()
            markup.row('⏸ Пауза', '⏹️ Стоп')
            markup.row('📊 Статистика')
            bot.send_message(chat_id=message.chat.id, text='▶  Продолжить', reply_markup=markup)

        elif message.text == '☑ Готово':
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.row('📊 Статистика',)
            bot.send_message(chat_id=message.chat.id, text='Ждем на работе', reply_markup=markup)

        elif message.text == '☑ Завершить':
            stat = Statistic.objects.filter(worker_id=message.chat.id,
                                            current_day=datetime.datetime.today().strftime('%Y-%m-%d'))
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if stat:
                markup.row('📊 Статистика')
            else:
                markup.row('✅ В сети', '🚫 Не в сети', '📊 Статистика')
            bot.send_message(chat_id=message.chat.id, text='😃 Спасибо! До завтра!', reply_markup=markup)

        elif message.text == '☑️ Спасибо!':
            markup.row('📊 Статистика')
            bot.send_message(chat_id=message.chat.id, text='До завтра', reply_markup=markup)

        elif message.text == '📊 Статистика':
            markup = types.InlineKeyboardMarkup()
            workers = Worker.objects.all()
            for i in workers:
                worker = types.InlineKeyboardButton(text='👤️' + i.name, callback_data=i.telegram_id)
                markup.add(worker)

            bot.send_message(chat_id=message.chat.id,
                             text='☑️ Выберите сотрудника:',
                             reply_markup=markup,
                             parse_mode='HTML')
            stat = Statistic.objects.filter(worker_id=message.chat.id,
                                                           current_day=datetime.datetime.today().strftime(
                                                               '%Y-%m-%d')).first()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            if stat == None:
                markup.row('✅ В сети', '🚫 Не в сети')
                markup.row('📊 Статистика')
                bot.send_message(chat_id=message.chat.id, text='Новый день', reply_markup=markup)

        else:
            try:
                stat = Statistic.objects.filter(worker_id=message.chat.id,
                                                current_day=datetime.datetime.today().strftime('%Y-%m-%d')).first()
                if stat:
                    if stat.wait == 1:
                        markup.row('⏸ Пауза', '⏹️ Стоп')
                        markup.row('📊 Статистика')
                        stat.wait = 0
                        stat.start_time = datetime.datetime.now()
                        stat.current_status = 'Активный'
                        stat.task = message.text
                        stat.save()
                        text = '⚙️ Текущая задача: ' + message.text + '\n' + '⏳ Время начала: ' + str(
                            datetime.datetime.now().strftime('%H:%M')) + '\n' + '〰️〰️〰️〰️〰️〰️〰️〰️〰️〰️ ' + '\n' + '😃 Хорошего дня!'

                        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=markup)
                    if stat.wait == 2:
                        markup.row('☑ Готово')
                        markup.row('✖ Отмена')
                        stat.task = message.text
                        stat.start_time = datetime.datetime.now()
                        stat.save()
                        text = '📅Отгул: ' + str(datetime.datetime.now()) + '\n' + '⚠️ Причина: ' + message.text
                        bot.send_message(chat_id=message.chat.id, text=text, reply_markup=markup)
            except Exception as e:
                bot.send_message(chat_id=message.chat.id, text=e)

        @bot.callback_query_handler(func=lambda call: True)
        def handle_query(call):
            if call.data[0] == '|':
                stat, create = Statistic.objects.get_or_create(worker_id=call.message.chat.id,
                                                               current_day=datetime.datetime.today().strftime(
                                                                  '%Y-%m-%d'))
                worker = Worker.objects.filter(telegram_id=call.message.chat.id).first()
                worker.sick = datetime.datetime.now()
                worker.save()
                stat.task = call.data[1:]
                stat.current_status = '💊️ Больничный'
                stat.start_time = datetime.datetime.now()
                stat.save()
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.row('☑️ Спасибо!')
                markup.row('✖ Отмена')
                text = '💊️ Больничный: ' + call.data[1:] +  '\n' + '💪️ Быстрого выздоравления!'
                bot.send_message(chat_id=call.message.chat.id,
                                 text=text,
                                 reply_markup=markup)
            else:
                stat = Statistic.objects.filter(worker_id=call.data,
                                                                 current_day=datetime.datetime.today().strftime(
                                                                  '%Y-%m-%d')).first()
                worker = Worker.objects.filter(telegram_id=call.data).first()
                if worker.sick:
                    bot.send_message(chat_id=call.message.chat.id,
                                    text='На больничном  с ' + str(worker.sick))

                if stat == None:
                    bot.send_message(chat_id=call.message.chat.id,
                                     text='Не в сети')
                    return
                get, pause = Pause.objects.get_or_create(statistic_id=stat.id)
                try:
                    markup = types.InlineKeyboardMarkup()
                    sender = types.InlineKeyboardButton(text='💬 Написать', url='https://telegram.dog/'+worker.alias)
                    markup.add(sender)
                    if not stat.end_time:
                        end = '-'
                    else:
                        end = (stat.end_time+timedelta(hours=2)).strftime('%H:%M')

                    if not stat.start_time:
                        start = '-'
                    else:
                        start = (stat.start_time+timedelta(hours=2)).strftime('%H:%M')

                    bot.send_message(chat_id=call.message.chat.id,
                                     text='👤️ ' + worker.name + '\n' +
                                          '☑ Статус: ' + stat.current_status + ' ('+ stat.place +')'+'\n' +
                                          '〰️〰️〰️〰️〰️〰️〰️〰️〰️〰' + '\n' +
                                          '⚙️ Текущая задача: ' + str(stat.task) + '\n' +
                                          '⏳️ Время начала: ' + str(start) + '\n' +
                                          '🍽 Обед: ' + str(get.total_time).split('.')[0] + '\n' +
                                          '⌛️ Время ухода: ' + str(end),
                                     reply_markup=markup)

                except Exception as e:
                    bot.send_message(chat_id=message.chat.id, text=e)

    bot.polling()
