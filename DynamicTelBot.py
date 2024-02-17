## Created by Squandor for python3
## Updated by Waltervl for Domoticz 2023.2 and up
## Updated by Waltervl to enhance functionality
import os
import sys
import time
import random
import datetime
import telepot
import urllib
import urllib3
import json
import re
import base64
import configparser as ConfigParser
from random import randint
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from collections import Counter

########### Config ###############
Config = ConfigParser.ConfigParser()
if os.path.isfile('config.ini'):
    Config.read('config.ini')
    url = Config.get('config', 'url')
    bot_token = Config.get('config', 'bot_token')
    unames = Config.get('config', 'unames').split(',')
else:
    Config.add_section('config')
    Config.set('config','url', input('Url (http://0.0.0.0:8080): '))
    Config.set('config','bot_token',input('Bot token: '))
    Config.set('config','unames',input('Usernames (user1, user2, user3): '))
    url = Config.get('config', 'url')
    bot_token = Config.get('config', 'bot_token')
    unames = Config.get('config', 'unames').split(',')
    cfgfile = open("config.ini",'w')
    Config.write(cfgfile)
    cfgfile.close()
##################################


def getRandom():
   return randint(0, 9)

def getDomoticzUrl(url):
    http= urllib3.PoolManager()
    try:
        _res = json.loads(http.request('GET', url).data.decode('utf-8'))
    except:
        _res = ''
    return _res

def getSelectorNames(_idx):
    print('getSelectorNames(_idx)')
    #print(_idx)
    _levelActions = base64.b64decode(getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&rid=' + _idx)['result'][0]['LevelNames']).decode('utf-8').split('|')
    #print(_levelActions)
    _lvls = 0
    _levels = []
    for _level in _levelActions:
        _obj = {}
        _obj['Name'] = _level
        if _lvls != 0:
            _obj['level'] = str(_lvls) + '0'
        else:
            _obj['level'] = '0'
        _lvls += 1
        _levels.append(_obj)
    return _levels

def getIDXByName(name, _devices):
    print('getIDXByName(name, _devices)')
    print(name)
    #print(_devices)
    _idx = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for i in _devices:
        if i['Name'].lower() == name.lower():
            _idx['idx'] = i['idx']
            if 'SubType' in i:
                _idx['type'] = i['SubType'].replace(' ', '_')
            else:
                _idx['type'] = i['Type'].replace(' ', '_')
            if _idx['type'].lower() == 'selector_switch':
                _idx['levels'] = getSelectorNames(i['idx'])
            break
        if re.search('.*' + name.lower() + '.*', i['Name'].lower().strip()):
            _sugObject = {}
            _sugObject['idx'] = i['idx']
            if 'SubType' in i:
                _sugObject['type'] = i['SubType'].replace(' ', '_')
            else:
                _sugObject['type'] = i['Type'].replace(' ', '_')
            _sugObject['Name'] = i['Name']
            if _sugObject['type'].lower() == 'selector_switch':
                _sugObject['levels'] = getSelectorNames(i['idx'])
            _idx['suggestions'].append(_sugObject)
    return _idx
    
def getIDXByType(_devices):
    print('getIDXByType(_devices)')
    _idx = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for i in _devices:
            _sugObject = {}
            _sugObject['idx'] = i['idx']
            if 'SubType' in i:
                _sugObject['type'] = i['SubType'].replace(' ', '_')
            else:
                _sugObject['type'] = i['Type'].replace(' ', '_')
            _sugObject['Name'] = i['Name']
            if _sugObject['type'].lower() == 'selector_switch':
                _sugObject['levels'] = getSelectorNames(i['idx'])
            _idx['suggestions'].append(_sugObject)
    return _idx

def getNameByIDX(dev, _devices):
    print('getNameByIDX(dev, _devices)')
    #print(_devices)
    for i in _devices:
        if i['idx'] == dev['idx']:
            _type = ''
            if 'SubType' in i:
                _type = i['SubType'].replace(' ', '_')
            else:
                _type = i['Type'].replace(' ', '_')
            if _type.lower() == dev['type'].lower():
                _status = ''
                if _type.lower() == 'selector_switch':
                    _stateCount = i['Status'].replace('Set Level: ', '').replace(' %', '')
                    for i in getSelectorNames(i['idx']):
                        if i['level'] == _stateCount:
                            _status = i['Name'].title()
                else:
                    try:
                        _status = i['Status'].title()
                    except:
                        _status = i['Data']

                return i['Name'].title(), _status

def getDataByIDX(_idx):
    print('getDataByIDX(_idx)')
    #print(_devices)
    _IDXData = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&rid=' + _idx)['result'][0]
    print(_IDXData)
    _type = ''
    _type = _IDXData['SubType'].replace(' ', '_')
    _status = ''
    if _type.lower() == 'selector_switch':
        _stateInt = _IDXData['Level']
        print(getSelectorNames(_idx))
        for i in getSelectorNames(_idx):
            if int(i['level']) == _stateInt:
                _status = i['Name'].title()
    else:
          try:
            _status = _IDXData['Status'].title()
          except:
            _status = _IDXData['Data']

    print(_status)
    _name = ''
    _name = _IDXData['Name'].title()
    print(_name)


    return _name, _status


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('on_callback_query(msg)')
    print(query_data)
    if query_data.lower().split(' ')[0] == '/switch':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=switchlight&idx=' + query_data.lower().split(' ')[1] + '&switchcmd=' + query_data.lower().split(' ')[2].title().replace('Level=', 'level=').strip()
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed'
        else:
            bot_text = 'Running failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=bot_text)
    elif query_data.lower().split(' ')[0] == '/group':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=switchscene&idx=' + query_data.lower().split(' ')[1] + '&switchcmd=' + query_data.lower().split(' ')[2].title().replace('Level=', 'level=').strip()
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed'
        else:
            bot_text = 'Er ging iets mis met het uitvoeren: ' + runUrl
        bot.answerCallbackQuery(query_id, text=bot_text)
    elif query_data.lower().split(' ')[0] == '/utility':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=getdevices&rid=' + query_data.lower().split(' ')[1]
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed'
        else:
            bot_text = 'Running failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=_res['result'][0]['Data'])
    elif query_data.lower().split(' ')[0] == '/temp':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=getdevices&rid=' + query_data.lower().split(' ')[1]
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed'
        else:
            bot_text = 'Running failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=_res['result'][0]['Data'])
    elif query_data.lower().split(' ')[0] == '/suggestion':
        markup_dyn = None
        _many = False
        _utility = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=utility&used=true')['result']
        _utilityTypes = sorted(Counter(x['SubType'].lower() for x in _utility if 'SubType' in x)) + sorted(Counter(x['Type'].lower() for x in _utility if 'Type' in x))
        _temps = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=temp&used=true')['result']
        _tempTypes = sorted(Counter(x['SubType'].lower() for x in _temps if 'SubType' in x)) + sorted(Counter(x['Type'].lower() for x in _temps if 'Type' in x))
        #_switches = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=switch&used=true')['result']
        #_switchTypes = sorted(Counter(x['SubType'].lower() for x in _switches if 'SubType' in x)) + sorted(Counter(x['Type'].lower() for x in _switches if 'Type' in x))
        _switchTypes=['rgb', 'rgbww', 'security panel', 'switch', 'color switch',  'light/switch', 'lighting 2']
        #print(_switchTypes)
        if query_data.lower().split(' ')[2] in _switchTypes:
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
            ])
        elif query_data.lower().split(' ')[2] == 'group':
            _callbackCommand = '/group ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
            ])
        elif query_data.lower().split(' ')[2] in _tempTypes:
            _callbackCommand = '/temp ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = None
        elif query_data.lower().split(' ')[2] in _utilityTypes:
            _callbackCommand = '/utility ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = None
        elif query_data.lower().split(' ')[2] == 'selector_switch':
            _arr = []
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1] + ' '
            for i in getSelectorNames(query_data.lower().split(' ')[1]):
                _arr.append(
                InlineKeyboardButton(text=i['Name'], callback_data=_callbackCommand + 'Set%20Level&level=' + i['level'])
                )

            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
            if len(_arr) > 3:
                _many = True
        _name, _state = getNameByIDX({'idx': query_data.lower().split(' ')[1], 'type': query_data.lower().split(' ')[2]}, getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=light&used=true')['result'] + getDomoticzUrl(url + '/json.htm?type=command&param=getscenes')['result'] + getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=utility&used=true')['result'] + getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=temp&used=true')['result'])
        _name2, _state2 = getDataByIDX(query_data.lower().split(' ')[1])
        if _many:
            #bot.sendMessage(int(query_data.split(' ')[3]), 'The ' + query_data.lower().split(' ')[2].title() + ' ' + _name + ' is currently ' + _state + '. What do you want to do?')
            bot.sendMessage(int(query_data.split(' ')[3]), 'The device ' + _name2 + ' is currently ' + _state2 + '. What do you want to do?')
            counter = 0
            multipleMark = []
            for i in _arr:
                if len(multipleMark) == 3:
                    bot.sendMessage(int(query_data.split(' ')[3]), 'Page ' + str(counter), reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                    multipleMark[:] = []
                    _send = True
                    counter += 1
                else:
                    multipleMark.append(i)
                    _send = False
            if _send == False:
                bot.sendMessage(int(query_data.split(' ')[3]), 'Page ' + str(counter), reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
        else:
            bot.sendMessage(int(query_data.split(' ')[3]), 'The device' + ' ' + _name + ' is currently ' + _state + '. What do you want to do?', reply_markup=markup_dyn)

def handle(msg):
   print('handle(msg)')
   #print(msg)
   global url, unames, car_location_idx
   chat_id = msg['chat']['id']
   command = msg['text']
   user = msg['from']['first_name']
   markup_main = ReplyKeyboardMarkup(keyboard=[['Dashboard'], ['Device Tabs']],one_time_keyboard=False, resize_keyboard=True)
   markup_device_tabs = ReplyKeyboardMarkup(keyboard=[['Switches','Grp Scenes','Temperature'], ['Utility','Weather'], ['Back']], one_time_keyboard=False, resize_keyboard=True)
   run = False
   if user.lower() in unames:
       if command.lower() != '/start':
           command = command.lower().replace('/', '')
       if command.lower() == '/start':
           bot.sendMessage(chat_id, 'What can I do for you?', reply_markup=markup_main)
       if command.lower() == 'back':
           bot.sendMessage(chat_id, 'What can I do for you?', reply_markup=markup_main)
       if command.lower() == 'device tabs':
           bot.sendMessage(chat_id, 'Select device from keyboard:', reply_markup=markup_device_tabs)
       if command.lower() == 'dashboard':
           _favorites = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&used=true&filter=all&favorite=1')['result']
           _idx = getIDXByType(_favorites)
           if len(_idx['suggestions']) > 0:
                       print('suggestions dashboard')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       #bot.sendMessage(chat_id, 'Dashboard')
                       if len(_arr) > 3:
                           counter= 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'Dashboard', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No dashboard Device found')
             
       if command.lower() == 'switches':
           _switches = getDomoticzUrl(url + '/json.htm?type=command&param=getlightswitches')['result']
           _idx = getIDXByType(_switches)
           if len(_idx['suggestions']) > 0:
                       print('suggestions switches')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       #bot.sendMessage(chat_id, 'Dashboard')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All Switches', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No switch Device found')
             
       if command.lower() == 'grp scenes':
           _groups = getDomoticzUrl(url + '/json.htm?type=command&param=getscenes')['result']
           _idx = getIDXByType(_groups)
           if len(_idx['suggestions']) > 0:
                       print('suggestions groups')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       #bot.sendMessage(chat_id, 'Dashboard')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All Group/Scene Devices', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No Group/Scene Device found')
       if command.lower() == 'temperature':
           _temps = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=temp&used=true')['result']
           _idx = getIDXByType(_temps)
           if len(_idx['suggestions']) > 0:
                       print('suggestions temperature')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       #bot.sendMessage(chat_id, 'Dashboard')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All Temperature Sensors', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No Temperature Sensors found')
       if command.lower() == 'weather':
           _temps = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=weather&used=true')['result']
           _idx = getIDXByType(_temps)
           if len(_idx['suggestions']) > 0:
                       print('suggestions weather')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       #bot.sendMessage(chat_id, 'Dashboard')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All weather Sensors', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No Weather Sensors found')
             
       elif command.lower() == 'utility':
           _utility = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=utility&used=true')['result']
           _idx = getIDXByType(_utility)
           if len(_idx['suggestions']) > 0:
                       print('suggestions uitility')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       #bot.sendMessage(chat_id, 'Dashboard')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All Utility Devices', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No Utility Sensors found')
             
       else:
           if command.lower() != '':
               _switches = getDomoticzUrl(url + '/json.htm?type=command&param=getlightswitches')['result']
               _groups = getDomoticzUrl(url + '/json.htm?type=command&param=getscenes')['result']
               _temps = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=temp&used=true')['result']
               _utility = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=utility&used=true')['result']
               _utilityTypes = sorted(Counter(x['SubType'].lower() for x in _utility if 'SubType' in x)) + sorted(Counter(x['Type'].lower() for x in _utility if 'Type' in x))
               _tempTypes = sorted(Counter(x['SubType'].lower() for x in _temps if 'SubType' in x)) + sorted(Counter(x['Type'].lower() for x in _temps if 'Type' in x))

               _devices = _switches + _groups + _utility + _temps
               _idx = getIDXByName(command.lower(), _devices)
               if _idx['idx'] != '':
                   print('_idx[idx]')
                   print(_idx['idx'])
                   if _idx['type'].lower() == 'switch' or _idx['type'].lower() == 'x10':
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
                       ])
                   elif _idx['type'].lower() == 'scene' or _idx['type'].lower() == 'group':
                       _callbackCommand = '/group ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
                       ])
                   elif _idx['type'].lower() in _tempTypes:
                       _callbackCommand = '/temp ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='Show status', callback_data=_callbackCommand + 'status')],
                       ])
                   elif _idx['type'].lower() == 'selector_switch':
                       _arr = []
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       for i in _idx['levels']:
                           _arr.append(
                           InlineKeyboardButton(text=i['Name'], callback_data=_callbackCommand + 'Set%20Level&level=' + i['level'])
                           )
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                   elif _idx['type'].lower() in _utilityTypes:
                       _callbackCommand = '/utility ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='Show status', callback_data=_callbackCommand + 'status')],
                       ])
                   bot.sendMessage(chat_id, 'What do you want to do with the switch ' + str(chat_id) + ' ' + command.lower() + '?', reply_markup=markup_dyn)
               else:
                   if len(_idx['suggestions']) > 0:
                       print('suggestions')
                       print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       bot.sendMessage(chat_id, 'Could not find the device, did you mean any of these devices?')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, 'Page ' + str(counter), reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, 'Page ' + str(counter), reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'Page 0', reply_markup=markup_dyn)
                   else:
                       bot.sendMessage(chat_id, 'Device not found')
       if run:
           getDomoticzUrl(url)

## huisserver
bot = telepot.Bot(bot_token)
MessageLoop(bot, {'chat': handle,
                  'callback_query': on_callback_query}).run_as_thread()
print('I am listening...')

while 1:
    time.sleep(10)
