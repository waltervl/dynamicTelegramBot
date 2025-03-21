# dynamicTelegramBot
Dynamic telegram bot for Domoticz written in Python 3

# What can it do?
With this bot you can monitor and control your Domoticz devices outside your internal home network.
When typing /start a menu will appear instead of the normal keyboard where you can choose to show all favorite devices on the dashboard or switch to show all your Rooms or show the default device tabs (switches, group/scene, utility, weather, cameras). Then you can show all devices of the selected room or device tab.

Using this bot you can ask him for a switch/scene/group/temperature/utility switch. 
After the bot found the device it will ask you what you want to do with it (on,off)

If the device is an selector switch the bot will build special keyboard in telegram where you can find you're selector options from domoticz. 
If the device is a sensor it will show only the status.
For other devices like energy, temperature, weather it will show its status.
For cameras it will show a snapshot of that camera.

But sometimes you don't know the full name of the device or you forget a character, in that case the bot will look for devices that could be the device that you want and will come with suggestions. 

So for example if you have 2 switches called livingroomSpeaker, livingroomLights

If you type livingroomspeaker to the bot it will come with the switch and asks you what you want to do (on or off)

but if you type living the bot will make an suggestions and asks if you meant one of the following devices and comes with livingroomSpeaker and livingroomLights.

# Installation
1. Prerequisites: Installing telepot-x and ConfigParser using: 
```sudo pip3 install telepot-x ConfigParser```
2. Download the file DynamicTelBot.py and store it somewhere on your system, eg /home/username/scripts/telegram/dynamicTelegramBot/DynamicTelBot.py
3. Create a telegram bot to communicate with Domoticz, see for instructions for example https://www.domoticz.com/wiki/Telegram_Bot

# First run
You need to start the bot manually (eg ```python3 DynamicTelBot.py```) for the first time because it will ask you for information to create a config.ini file:
- url: <domoticz_url> (eg http://192.168.1.2:8080)
- bot_token: (use bot @get_id_bot to get the bot token), see also https://www.domoticz.com/wiki/Telegram_Bot
- unames: (Telegram usernames seperated by a comma: user1, user2, user3). By using this the bot will only react to the users which are in the array.

After that an config.ini will be created and it can be run from the systemd service if needed.

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
ExecStart=/usr/bin/python /home/username/scripts/telegram/dynamicTelegramBot/DynamicTelBot.py
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

<img src="https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112037-099.png?raw=true" alt="Switch example" style="width:40%; height:auto;">

<img src="https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112114-551.png?raw=true" alt="Dashboard example" style="width:40%; height:auto;">

<img src="https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112644-379.png?raw=true" alt="Suggestion example" style="width:40%; height:auto;">

<img src="https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-111953-857.png?raw=true" alt="Cameras example" style="width:40%; height:auto;">

<img src="https://github.com/waltervl/dynamicTelegramBot/blob/master/screenshots/Screenshot_20240403-112217-349.png?raw=true" alt="Rooms example" style="width:40%; height:auto;">

# Known Issues
After some time (hours) of not being in use the bot will reconnect to telegram. This will take around a minute. 
So when you ask for a device after some time the bot will answer but then reconnects so a next command is not being processed for a minute or even skipped and needs to be resend.
