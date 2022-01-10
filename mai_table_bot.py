from datetime import date
from bs4 import BeautifulSoup

import telebot
import datetime
import os
import re
import requests
import sqlite3
import time


transcripts = {
	"Пн": "Понедельник",
	"Вт": "Вторник",
	"Ср": "Среда",
	"Чт": "Четверг",
	"Пт": "Пятница",
	"Сб": "Суббота",
	"ЛК": "лекция",
	"ПЗ": "семинар",
	"ЛР": "л/р"
}

alpha = 'АаБбВвГгДдЕеЁёЖжЗзИиййКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЪъЫыЬьЭэЮюЯя0123456789- '

PATTERN_GROUP_NAME = 'М[0-9И][ОЗВ]-\d\d\d[БСАМ]'

def get_params_for_request(keyword):
	"""
	Creates parameters based on the user's choice between today's or 
	tomorrow's schedule, the schedule for the current week or the next week
	"""
	def day_from_datetime(dt):
		dt = str(dt)
		return dt[8:] + '.' + dt[5:7]

	
	if keyword == "today":
		day = date.today()
		day = day_from_datetime(day)
		return (int(date.today().strftime("%W")) - 34, day, False)

	elif keyword == "tomorrow":
		day = date.today() + datetime.timedelta(days=1)
		day = day_from_datetime(day)
		if date.today().isoweekday() == 7:
			return int(date.today().strftime("%W")) - 34 + 1, day, False
		return int(date.today().strftime("%W")) - 34, day, False

	elif keyword == "curr_week":
		return int(date.today().strftime("%W")) - 34, None, True

	elif keyword == "next_week":
		return int(date.today().strftime("%W")) - 34 + 1, None, True


def make_request(group_name, week):
	"""
	Getting HTML-page of chosen week from university website.
	"""
	url = "https://mai.ru/education/schedule/detail.php?group=" + group_name + '&' + "week=" + str(week)
	page = requests.get(url)
	return page.text


def make_response(page, day, is_week, week):
	"""
	I don't know why this shit works, but it is. According to user's choice
	between schedules, it creates different strings of schedule to send (ans variable).
	"""

	page = BeautifulSoup(page, 'html.parser')
	boards = page.find_all(class_="sc-container")
	if not is_week:
		for board in boards:
			try:
				if board.find(class_="sc-table-col sc-day-header sc-gray").text[:-2] == day:
					info_desk = board.find(class_="sc-table-row")
					break
			except AttributeError:
				if board.find(class_="sc-table-col sc-day-header sc-blue").text[:-2] == day:
					info_desk = board.find(class_="sc-table-row")
					break

		subjects = info_desk.find_all(class_="sc-title")
		time_ranges = info_desk.find_all(class_="sc-table-col sc-item-time")
		rooms = info_desk.find_all(class_="sc-table-col sc-item-location")
		rooms = [rooms[i] for i in range(len(rooms)) if i % 2 == 1]
		
		for i in range(len(rooms)):    
			rooms[i] = rooms[i].text

		line = ''
		for i in range(len(rooms)): 
			for char in rooms[i]:
				if char in alpha:
					line += char
			rooms[i] = line
			line = ''
		
		ans = "Расписание на " + day + ":\n"
		counter = 1
		for i in range(len(subjects)):
			line = time_ranges[i].get_text() + ' - ' + subjects[i].get_text() + ', ' + rooms[i] + "\n"
			ans += line
		return ans
	else:
		ans = f'Расписание на {week}-ую учебную неделю.\n'

		for board in boards:
			day = board.find(class_="sc-day").text
			info_desk = board.find(class_="sc-table-row")

			subjects = info_desk.find_all(class_="sc-title")
			time_ranges = info_desk.find_all(class_="sc-table-col sc-item-time")
			subject_types = info_desk.find_all(class_="sc-table-col sc-item-type")
			rooms = info_desk.find_all(class_="sc-table-col sc-item-location")
			rooms = [rooms[i] for i in range(len(rooms)) if i % 2 == 1]
			
			for i in range(len(rooms)):    
				rooms[i] = rooms[i].text

			line = ''
			for i in range(len(rooms)): 
				for char in rooms[i]:
					if char in alpha:
						line += char
				rooms[i] = line
				line = ''
			
			ans += transcripts[day] + ":\n"
			counter = 1
			for i in range(len(subjects)):
				line = (time_ranges[i].get_text()[0:5] + 
					' - ' + subjects[i].get_text() + 
					', ' + transcripts[subject_types[i].get_text()[:-1]] +
					', ' + rooms[i] + "\n")
				ans += line
			ans += '\n'

		return ans
	

def main_action(keyword, group_name):
	"""
	Groups all previous funcs in united scenario of creating schedule message.
	"""
	week, day, is_week = get_params_for_request(keyword)
	page = make_request(group_name, week)
	response = make_response(page, day, is_week, week)
	return response


with open('token.txt', 'r') as token_file:
	token = token_file.read().strip()	

bot = telebot.TeleBot(token)

@bot.message_handler(commands=['start'])
def start_handler(message):
	bot.send_message(message.chat.id, """
		Привет, я знаю расписание любой группы в МАИ и могу его подсказать. 
		Чтобы получить расписание, напиши название своей группы. Например, М8О-101Б-21. 
		Чтобы познакомиться с другими функциями, воспользуйся /help.

		P.S. Сейчас в МАИ сессия, потому до начала следующего учебного семестра функция расписания работать не будет.
		""")


@bot.message_handler(commands=['help']) #TODO дописать расшифровку названий групп
def help_handler(message):
	bot.send_message(message.chat.id, """
Чтобы получить расписание, просто напиши полное название своей группы. 
К примеру, М8О-101Б-21, где 
М - Москва, 
8 - номер факультета, 
О - очная форма обучения, 
101 - номер группы, 
Б - бакалавриат,
21 - год поступления.

Чтобы создать избранный запрос, нажми на кнопку "сделать избранным" под расписанием. Ты сможешь вызвать его снова командой /fav.

Если потерялся в универе - /map
""")


@bot.message_handler(commands=['fav'])
def fav_handler(message):
	conn = sqlite3.connect("fav_query_db.db")
	cursor = conn.cursor()
	cursor.execute("SELECT keyword, group_name FROM fav_querys WHERE chat_id=?", (message.chat.id, ))
	if cursor.fetchone() == None:
		bot.send_message(message.chat.id, "Сначала создайте избранный запрос")
	else:
		cursor.execute("SELECT keyword, group_name FROM fav_querys WHERE chat_id=?", (message.chat.id, ))
		keyword, group_name = cursor.fetchone()
		response = main_action(keyword, group_name)
		bot.send_message(message.chat.id, response)


@bot.message_handler(commands=['map'])
def send_map(message):
	map_img = open('/home/fefta/coding/projects/MAItable_bot/map.jpg', 'rb')
	bot.send_photo(message.chat.id, map_img)
	map_img.close()


@bot.message_handler(regexp=PATTERN_GROUP_NAME) #TODO добавить первичную проверку имени группы, т.е. если такой группы нет, то сообщение об этом должно вернуться сразу
def group_name_handler(message):
	keyboard = telebot.types.InlineKeyboardMarkup()
	today_button = telebot.types.InlineKeyboardButton(text="На сегодня", callback_data="today::" + message.text + "::ordinary_query")
	tomorrow_button = telebot.types.InlineKeyboardButton(text="На завтра", callback_data="tomorrow::" + message.text + "::ordinary_query")
	curr_week_button = telebot.types.InlineKeyboardButton(text="На эту неделю", callback_data="curr_week::" + message.text + "::ordinary_query")
	next_week_button = telebot.types.InlineKeyboardButton(text="На следующую неделю", callback_data="next_week::" + message.text + "::ordinary_query")
	keyboard.add(today_button, tomorrow_button, curr_week_button, next_week_button)
	bot.send_message(message.chat.id, "Ок, какое расписание вам нужно?", reply_markup=keyboard)


@bot.callback_query_handler(func=lambda call: True)
def choice_button_handler(call): #обрабатывает запросы от кнопок расписания
	"""
	keyword - выбор расписания: на сегодня, на завтра и т.д.
	group_name - имя группы

	"""
	data = call.data.split('::')
	keyword, group_name = data[:-1]
	if data[-1] == "ordinary_query":
		response = main_action(keyword, group_name)
		keyboard = telebot.types.InlineKeyboardMarkup()
		add_to_fav_button = telebot.types.InlineKeyboardButton(text="сделать избранным", callback_data= keyword + "::" + group_name + "::fav_query")
		keyboard.add(add_to_fav_button)
		bot.send_message(call.message.chat.id, response, reply_markup=keyboard)
	else:
		conn = sqlite3.connect("fav_query_db.db")
		cursor = conn.cursor()

		cursor.execute("SELECT * FROM fav_querys WHERE chat_id=?", (call.message.chat.id, ))
		if cursor.fetchone() == None:
			cursor.execute("INSERT INTO fav_querys VALUES (?, ?, ?)", (call.message.chat.id, data[0], data[1]))
			bot.send_message(call.message.chat.id, "Запрос сохранен. Теперь ты всегда cможешь повторить его командой /fav")
		else:
			cursor.execute("UPDATE fav_querys SET keyword=?, group_name=? WHERE chat_id=?", (keyword, group_name, call.message.chat.id))
			bot.send_message(call.message.chat.id, "Запрос обновлен. Теперь ты всегда cможешь повторить его командой /fav")
		conn.commit()
		conn.close()

if __name__ == '__main__':
    while True:
        try:
            bot.polling(none_stop=True, interval=0)
        except Exception as err:
            print(err)
            time.sleep(5)
