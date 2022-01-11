# mai-schedule-bot
bot provides you with schedules of all university groups taken from MAI websitee

it's main feature now is inactive because of exams in mai

## Setting up
1. clone a repo
```
git clone https://github.com/fefefefta/mai-schedule-bot
```
2. set up a database
```
sqlite3 fav_querys_db.db
```
```
sqlite> CREATE TABLE fav_querys(
	      chat_id INTEGER,
	      keyword TEXT,
	      group_name TEXT
        );
```
3. put your token in token.txt in project dir

4. get all packages from requirements.txt
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```

## How to use

1. start the bot

```
python3 mai_table_bot.py
```
2. send */help* to bot 
