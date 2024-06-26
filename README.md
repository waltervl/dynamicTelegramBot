# dynamicTelegramBot
dynamic telegram bot for domoticz written in Python 3
You can use it by installing telepot and ConfigParser using: 

```  sudo pip3 install telepot-x ConfigParser```

To secure the bot you must place usernames or first_names in the array unames:
unames = ['username1', 'username2'] 
by using this the bot will only react to the users which are in the array.

# What can it do?
Using this bot you can ask him for an switch/scene/group/temperature/utility switch. 
After the bot found the device it will ask you what you want to do with it (on,off)

If the device is an selector switch the bot will build special keyboard in telegram where you can find you're selector options from domoticz. 
If the device is a sensor it will show only the status.

But sometimes you don't know the full name of the device or you forget an character, in that case the bot will look for devices that could be the device that you want and will come with suggestions. 

So for example if you have 2 switches called livingroomSpeaker, livingroomLights

If you type livingroomspeaker to the bot it will come with the switch and asks you what you want to do (on or off)

but if you type living the bot will make an suggestions and asks if you meant one of the following devices and comes with livingroomSpeaker and livingroomLights.

When typing /start a menu will appear instead of the normal keyboard where you can choose to show all favorite devices on the dashboard or switch to show all your Rooms or show the default device tabs (switches, group/scene, utility, weather). Then you can show all devices of the selected room or device tab.

# First run
You need to start the bot manually for the first time because it will ask you for information to create an config:
- url: <domoticz_url> (http://192.168.1.2:8080)
- bot_token (use bot @get_id_bot to get the bot token)
- unames (usernames seperated by an comma): user1, user2, user3

after that an config.ini will be created and it can be run from the systemd service.

# Systemd script
Thanks to so help someone made an easy service file so you can easy run the bot using the systemd service. 
The example is in the repo. 
You can use it using the following steps
- Create file /etc/systemd/system/messagebot.service
- Copy example service code to /etc/systemd/system/messagebot.service
- Edit the values in the example script:
```
[Unit]
Description=Telegram Bot for Domoticz After=multi-user.target
[Service]
Type=idle
User=<username>
ExecStart=/usr/bin/python /home/username/scripts/telegram/dynamicTelegramBot/squandorDynamicTelBot.py
WorkingDirectory=/home/username/scripts/telegram/dynamicTelegramBot/
[Install]
WantedBy=multi-user.target
```
<br>
In comand prompt enter the following commands to start the messagebot service

```
sudo chmod 655 /etc/systemd/system/messagebot.service
sudo systemctl daemon-reload
sudo systemctl enable messagebot.service
sudo systemctl start messagebot.service
sudo systemctl status messagebot.service
```

# Examples:<br>
Switch<br>
![alt text](https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112037-099.png?raw=true)

Dashboard<br>
![alt text](https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112114-551.png?raw=true)

Suggestion<br>
![alt text](https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112644-379.png?raw=true)

Cameras<br>
![alt text](https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-111953-857.png?raw=true)

Rooms<br>
![alt text](https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112217-349.png?raw=true)

