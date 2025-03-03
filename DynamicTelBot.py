#!/usr/bin/env python3
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
import urllib.request
import urllib3
import socket
import json
import re
import base64
import configparser as ConfigParser
from random import randint
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
from collections import Counter
import telepot.api

telepot.api._pools = {
    'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=6, timeout=20),
}

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
socket.setdefaulttimeout(10)

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
    _levelActions = base64.b64decode(getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&rid=' + _idx)['result'][0]['LevelNames']).decode('utf-8').split('|')
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

def getSetpointConfig(_idx):
    print('getSetpointConfig(_idx)')
    _configdata = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&rid=' + _idx)['result'][0]
    _config =[]
    _config.append(_configdata['vunit'])
    _config.append(_configdata['step'])
    _config.append(_configdata['min'])
    _config.append(_configdata['max'])
    #print(_config)
    return _config

def getIDXByName(name, _devices):
    print('getIDXByName(name, _devices)')
    #print(name)
    #print(_devices)
    _idx = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for i in _devices:
        if i['Name'].lower() == name.lower():
            _idx['idx'] = i['idx']
            if 'SwitchType' in i:
                _idx['type'] = i['SwitchType'].replace(' ', '_').replace('/', '_')
            elif 'SubType' in i:
                _idx['type'] = i['SubType'].replace(' ', '_')
            elif 'Type' in i:
                _idx['type'] = i['Type'].replace(' ', '_')
            else:
                _idx['type'] = 'camera'
            if _idx['type'].lower() == 'selector':
                _idx['levels'] = getSelectorNames(i['idx'])
            elif _idx['type'].lower() == 'setpoint':
                _idx['levels'] = getSetpointConfig(i['idx'])
            break
        if re.search('.*' + name.lower() + '.*', i['Name'].lower().strip()):
            _sugObject = {}
            _sugObject['idx'] = i['idx']
            if 'SwitchType' in i:
                _sugObject['type'] = i['SwitchType'].replace(' ', '_').replace('/', '_')
            elif 'SubType' in i:
                _sugObject['type'] = i['SubType'].replace(' ', '_')
            elif 'Type' in i:
                _sugObject['type'] = i['Type'].replace(' ', '_')
            else:
                _sugObject['type'] = 'camera'
            _sugObject['Name'] = i['Name']
            if _sugObject['type'].lower() == 'selector':
                _sugObject['levels'] = getSelectorNames(i['idx'])
            elif _sugObject['type'].lower() == 'setpoint':
                _sugObject['levels'] = getSetpointConfig(i['idx'])
            _idx['suggestions'].append(_sugObject)
    #print(_idx)
    return _idx
    
def getIDXByType(_devices):
    print('getIDXByType(_devices)')
    #print(_devices)
    _idx_sug = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for i in _devices:
            _sugObject = {}
            _sugObject['idx'] = i['idx']
            if 'SwitchType' in i:
                _sugObject['type'] = i['SwitchType'].replace(' ', '_').replace('/', '_')
            elif 'SubType' in i:
                _sugObject['type'] = i['SubType'].replace(' ', '_')
            else:
                _sugObject['type'] = i['Type'].replace(' ', '_')
            _sugObject['Name'] = i['Name']
            if _sugObject['type'].lower() == 'selector':
                _sugObject['levels'] = getSelectorNames(i['idx'])
            elif _sugObject['type'].lower() == 'setpoint':
                _sugObject['levels'] = getSetpointConfig(i['idx'])

            _idx_sug['suggestions'].append(_sugObject)
    #print('-------')
    #print(_idx_sug)
    return _idx_sug

def getIDXRooms(_devices):
    print('getIDXRooms(_devices)')
    #print(_devices)
    _idx_sug = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for i in _devices:
        if i['Devices'] > 0:
            _sugObject = {}
            _sugObject['idx'] = i['idx']
            _sugObject['type'] = 'room'
            _sugObject['Name'] = i['Name']
            _idx_sug['suggestions'].append(_sugObject)
    return _idx_sug

def getCameras(_devices):
    print('getCameras(_devices)')
    #print(_devices)
    _idx_sug = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for i in _devices:
            _sugObject = {}
            _sugObject['idx'] = i['idx']
            _sugObject['type'] = 'camera'
            _sugObject['Address'] = i['Address']
            _sugObject['Name'] = i['Name']
            _sugObject['ImageURL'] = i['ImageURL']            
            _idx_sug['suggestions'].append(_sugObject)
    return _idx_sug

def getNameByIDX(dev, _devices):
    print('getNameByIDX(dev, _devices)')
    #print(_devices)
    for i in _devices:
        if i['idx'] == dev['idx']:
            _type = ''
            if 'SwitchType' in i:
                _type = i['SwitchType'].replace(' ', '_').replace('/', '_')
            elif 'SubType' in i:
                _type = i['SubType'].replace(' ', '_')
            else:
                _type = i['Type'].replace(' ', '_')
            if _type.lower() == dev['type'].lower():
                _status = ''
                if _type.lower() == 'selector':
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

def getDataByIDX(_data_idx, _type):
    print('getDataByIDX(_data_idx)')
    #print(_devices)
    if _type.lower() == 'scene' or _type.lower() == 'group':
        _IDXData = getDomoticzUrl(url + '/json.htm?type=command&param=getscenes&rid=' + _data_idx)['result'][0]
    elif _type.lower() == 'camera' :
        _IDXData = getDomoticzUrl(url + '/json.htm?type=command&param=getcameras&rid=' + _data_idx)['result'][0]
    else:
        _IDXData = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&rid=' + _data_idx)['result'][0]
    #print(_data_idx, _type)
    #print(_IDXData)
    #_type = ''
    #if 'SwitchType' in _IDXData:
    #    _type = _IDXData['SwitchType'].replace(' ', '_').replace('/', '_')
    #elif 'SubType' in _IDXData:
    #   _type = _IDXData['SubType'].replace(' ', '_')
    #else:
    #   _type = _IDXData['Type'].replace(' ', '_')
    _status = ''
    if _type.lower() == 'selector':
        _stateInt = _IDXData['Level']
        for i in getSelectorNames(_data_idx):
            if int(i['level']) == _stateInt:
                _status = i['Name'].title()
    elif _type.lower() == 'setpoint':
        _config = getSetpointConfig(_data_idx)
        _status = _IDXData['Data'] + ' ' + _config[0]
    elif _type.lower() == 'kwh':
        _status = 'Current ' + _IDXData['Usage'] + ', Today ' + _IDXData['CounterToday'] + ', Total ' + _IDXData['Data']
    elif _type.lower() == 'energy':
        _status = 'Current Usage ' + _IDXData['Usage'] + ', Current Deliv ' + _IDXData['UsageDeliv'] + ', Today Usage ' + _IDXData['CounterToday'] + ', Today Deliv ' + _IDXData['CounterDelivToday'] + ', Total Usage ' + _IDXData['Counter'] + ' kWh, Total Deliv ' + _IDXData['CounterDeliv'] + ' kWh'
    elif _type.lower() == 'gas':
        _status = 'Today ' + _IDXData['CounterToday'] + ', Total ' + _IDXData['Data']
    elif _type.lower() == 'rainbyrate':
        _status = 'Current ' + _IDXData['RainRate'] + ' mm/h , Today ' + _IDXData['Rain'] + ' mm'
    elif _type.lower() == 'tfa':
        _status = 'Speed ' + _IDXData['Speed'] + 'km/h, Direction ' + _IDXData['DirectionStr'] + ', Gusts ' + _IDXData['Gust'] + ' km/h'
    elif _type.lower() == 'camera':
        _status = 'Use camera devices button to get all cameras'
    else:
          try:
            _status = _IDXData['Status'].title()
          except:
            _status = _IDXData['Data']


    _name = ''
    _name = _IDXData['Name'].title()
    #print('name: ' + _name + ', type: ' + _type + ', status: ' + _status)

    return _name, _status


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('on_callback_query(msg)')
    #print(query_data)
    if query_data.lower().split(' ')[0] == '/switch':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=switchlight&idx=' + query_data.lower().split(' ')[1] + '&switchcmd=' + query_data.lower().split(' ')[2].title().replace('Level=', 'level=').strip()
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed, Switch ' + query_data.lower().split(' ')[2].title()
        else:
            bot_text = 'Command failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=bot_text)
    elif query_data.lower().split(' ')[0] == '/group':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=switchscene&idx=' + query_data.lower().split(' ')[1] + '&switchcmd=' + query_data.lower().split(' ')[2].title().replace('Level=', 'level=').strip()
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed'
        else:
            bot_text = 'Command failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=bot_text)
    elif query_data.lower().split(' ')[0] == '/setpoint':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=setsetpoint&idx=' + query_data.lower().split(' ')[1] + '&setpoint=' + query_data.lower().split(' ')[2]
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Setpoint succesfully set to ' + query_data.lower().split(' ')[2]
        else:
            bot_text = 'Command failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=bot_text)
    elif query_data.lower().split(' ')[0] == '/utility':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=getdevices&rid=' + query_data.lower().split(' ')[1]
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed'
        else:
            bot_text = 'Command failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=_res['result'][0]['Data'])
    elif query_data.lower().split(' ')[0] == '/temp':
        bot_text = ''
        runUrl = url + '/json.htm?type=command&param=getdevices&rid=' + query_data.lower().split(' ')[1]
        _res = getDomoticzUrl(runUrl)
        if _res['status'].lower() == 'ok':
            bot_text = 'Command executed'
        else:
            bot_text = 'Command failed: ' + runUrl
        bot.answerCallbackQuery(query_id, text=_res['result'][0]['Data'])
    elif query_data.lower().split(' ')[0] == '/room':
           print('callback room')
           bot_text = ''
           runUrl = url + '/json.htm?type=command&param=getdevices&plan=' + query_data.lower().split(' ')[1]
           try:
              _roomdevices = getDomoticzUrl(runUrl)['result']
           except KeyError:
               _roomdevices = {}
            
           _idx = getIDXByType(_roomdevices)
           if len(_idx['suggestions']) > 0:
                       print('suggestions room')
                       bot.sendMessage(int(query_data.split(' ')[3]), '** Room Devices **')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _settypes = ['on_off', 'dimmer', 'group','scene','setpoint','x10', 'venetian_blinds_us', 'venetian_blinds_eu', 'blinds_percentage', 'blinds_+_stop', 'push_on_button']
                           if i['type'].lower() in _settypes:
                               _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + query_data.split(' ')[3]))
                           else:
                              _name, _state = getDataByIDX(i['idx'],i['type'])
                              bot.sendMessage(int(query_data.split(' ')[3]), _name + ': ' + _state + '.', reply_markup=None)
                       
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       if len(_arr) > 0:
                           bot.sendMessage(int(query_data.split(' ')[3]), '** Switches, Scenes and Groups in Room **')
                       if len(_arr) > 3:
                           counter= 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(int(query_data.split(' ')[3]), '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   multipleMark.append(i)
                                   send = True
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(int(query_data.split(' ')[3]), '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       elif  1 <= len(_arr) <= 3:
                           bot.sendMessage(int(query_data.split(' ')[3]), '-', reply_markup=markup_dyn)
           else:
             bot.sendMessage(int(query_data.split(' ')[3]), 'No room Device found')

    elif query_data.lower().split(' ')[0] == '/suggestion':
        print('callback suggestion')
        #print(query_data.lower())
        markup_dyn = None
        _many = False
        _utility = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=utility&used=true')['result']
        _utilityTypes = sorted(Counter(x['SubType'].lower() for x in _utility if 'SubType' in x)) + sorted(Counter(x['Type'].lower() for x in _utility if 'Type' in x))
        _temps = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=temp&used=true')['result']
        _tempTypes = sorted(Counter(x['SubType'].lower() for x in _temps if 'SubType' in x)) + sorted(Counter(x['Type'].lower() for x in _temps if 'Type' in x))
        #_switchTypes=['on_off', 'dimmer', 'blinds_percentage']
        #print(_switchTypes)
        if query_data.lower().split(' ')[2] == 'on_off' or query_data.lower().split(' ')[2] == 'blinds':
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
            ])
        elif query_data.lower().split(' ')[2] == 'group' :
            _callbackCommand = '/group ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
            ])
        elif query_data.lower().split(' ')[2] == 'scene':
            _callbackCommand = '/group ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on')],
            ])
        elif query_data.lower().split(' ')[2] == 'push_on_button':
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on')],
            ])
        elif query_data.lower().split(' ')[2] == 'room':
            _callbackCommand = '/room ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on')],
            ])
        elif query_data.lower().split(' ')[2] in _tempTypes:
            _callbackCommand = '/temp ' + query_data.lower().split(' ')[1]+ ' '
            markup_dyn = None
        elif query_data.lower().split(' ')[2] in _utilityTypes:
            if query_data.lower().split(' ')[2] == 'setpoint':
                _arr = []
                _callbackCommand = '/setpoint ' + query_data.lower().split(' ')[1] + ' '
                print('making setpoint buttons')
                _setpointlist = ['15','17','20','22']
                _config = getSetpointConfig(query_data.lower().split(' ')[1])
                _SPmin = _config[2]
                _SPmax = _config[3]
                _SPstep = _config[1]
                if int(_SPmin) == -200 and int(_SPmax) == 200 and _SPstep == 0.5:
                  _SPmin = 14
                  _SPmax = 25
                  _SPstep = 1                  
                for i in range(int(_SPmin), int(_SPmax), int(_SPstep)):
                    _arr.append(InlineKeyboardButton(text=str(i), callback_data=_callbackCommand + str(i)))

                markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                if len(_arr) > 3:
                    _many = True
            else:
               _callbackCommand = '/utility ' + query_data.lower().split(' ')[1]+ ' '
               markup_dyn = None
        elif query_data.lower().split(' ')[2] == 'selector':
            _arr = []
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1] + ' '
            for i in getSelectorNames(query_data.lower().split(' ')[1]):
                _arr.append(
                InlineKeyboardButton(text=i['Name'], callback_data=_callbackCommand + 'Set%20Level&level=' + i['level'])
                )

            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
            if len(_arr) > 3:
                _many = True
        elif query_data.lower().split(' ')[2] == 'dimmer' or query_data.lower().split(' ')[2] == 'blinds_percentage':
            _arr = []
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1] + ' '
            _dimmerlevels = ['On', 'on'],['20', 'Set%20Level&level=20'],['50', 'Set%20Level&level=50'],['70', 'Set%20Level&level=70'],['100', 'Set%20Level&level=100'],['Off', 'off']
            for i in _dimmerlevels:
                _arr.append(
                InlineKeyboardButton(text=i[0], callback_data=_callbackCommand + i[1])
                )
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
        elif query_data.lower().split(' ')[2] == 'blinds_+_stop':
            _arr = []
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1] + ' '
            _dimmerlevels = ['Open', 'open'],['Stop', 'stop'],['Close', 'close'],['20', 'Set%20Level&level=20'],['50', 'Set%20Level&level=50'],['70', 'Set%20Level&level=70'],['100', 'Set%20Level&level=100']
            for i in _dimmerlevels:
                _arr.append(
                InlineKeyboardButton(text=i[0], callback_data=_callbackCommand + i[1])
                )
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
        elif query_data.lower().split(' ')[2] == 'venetian_blinds_us' or query_data.lower().split(' ')[2] == 'venetian_blinds_eu':
            _arr = []
            _callbackCommand = '/switch ' + query_data.lower().split(' ')[1] + ' '
            _dimmerlevels = ['Open', 'open'],['Stop', 'stop'],['Close', 'close']
            for i in _dimmerlevels:
                _arr.append(
                InlineKeyboardButton(text=i[0], callback_data=_callbackCommand + i[1])
                )
            markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
        _name2, _state2 = getDataByIDX(query_data.lower().split(' ')[1], query_data.lower().split(' ')[2])
        if _many:
            bot.sendMessage(int(query_data.split(' ')[3]), _name2 + ' is currently ' + _state2 + '.')
            counter = 0
            multipleMark = []
            for i in _arr:
                if len(multipleMark) == 6:
                    bot.sendMessage(int(query_data.split(' ')[3]), 'SET:', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                    multipleMark[:] = []
                    multipleMark.append(i)
                    _send = False
                    counter += 1
                else:
                    multipleMark.append(i)
                    _send = False
            if _send == False:
                bot.sendMessage(int(query_data.split(' ')[3]), 'SET:', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
        else:
            bot.sendMessage(int(query_data.split(' ')[3]), _name2 + ' is currently ' + _state2 + '.', reply_markup=markup_dyn)

def handle(msg):
   print('handle(msg)')
   #print(msg)
   global url, unames, car_location_idx
   chat_id = msg['chat']['id']
   command = msg['text']
   try:
       user = msg['from']['username']
   except KeyError: 
	   user = msg['from']['first_name']
   markup_main = ReplyKeyboardMarkup(keyboard=[['Dashboard'], ['Device Tabs', 'Rooms']],one_time_keyboard=False, resize_keyboard=True)
   markup_device_tabs = ReplyKeyboardMarkup(keyboard=[['Switches','Grp Scenes','Temperature'], ['Utility','Weather','Cameras'], ['Back']], one_time_keyboard=False, resize_keyboard=True)
   markup_dyn = None
   run = False
   if user.lower() in unames:
       if command.lower() != '/start':
           command = command.lower().replace('/', '')
       if command.lower() == '/start':
           bot.sendMessage(chat_id, 'What can I do for you?', reply_markup=markup_main)
       elif command.lower() == 'back':
           bot.sendMessage(chat_id, 'What can I do for you?', reply_markup=markup_main)
       elif command.lower() == 'device tabs':
           bot.sendMessage(chat_id, 'Select device tab from keyboard:', reply_markup=markup_device_tabs)
       elif command.lower() == 'dashboard':
           _favorites = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&used=true&filter=all&favorite=1')['result']
           _idx = getIDXByType(_favorites)
           if len(_idx['suggestions']) > 0:
                       print('suggestions dashboard')
                       bot.sendMessage(chat_id, '** Dashboard Devices **')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _settypes = ['on_off', 'dimmer', 'group','scene','setpoint','x10', 'venetian_blinds_us', 'venetian_blinds_eu', 'blinds_percentage', 'blinds_+_stop', 'push_on_button']
                           if i['type'].lower() in _settypes:
                               _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))
                           else:
                              _name, _state = getDataByIDX(i['idx'],i['type'])
                              bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)
                       
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       bot.sendMessage(chat_id, '** Switches, Scenes and Groups in Dashboard **')
                       if len(_arr) > 3:
                           counter= 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   multipleMark.append(i)
                                   send = False
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
             
       elif command.lower() == 'switches':
           _switches = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=light&used=true')['result']
           _idx = getIDXByType(_switches)
           _switchTypes=['on_off', 'selector', 'dimmer', 'venetian_blinds_us', 'venetian_blinds_eu', 'blinds_percentage', 'blinds_+_stop', 'push_on_button']
           if len(_idx['suggestions']) > 0:
                       print('suggestions switches')
                       bot.sendMessage(chat_id, '** Switches/Lights/Sensors read only**')
                       _arr = []
                       for i in _idx['suggestions']:
                           if i['type'].lower() in _switchTypes:
                               _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))
                           else:
                              _name, _state = getDataByIDX(i['idx'],i['type'])
                              bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)
 
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       bot.sendMessage(chat_id, '** Switches/Lights **')
                       if len(_arr) > 3:
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   multipleMark.append(i)
                                   send = False
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All Switches', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No switch Device found')
             
       elif command.lower() == 'grp scenes':
           _groups = getDomoticzUrl(url + '/json.htm?type=command&param=getscenes')['result']
           _idx = getIDXByType(_groups)
           if len(_idx['suggestions']) > 0:
                       print('suggestions groups')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   multipleMark.append(i)
                                   send = False
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
       
       elif command.lower() == 'cameras':
           _cameras = getDomoticzUrl(url + '/json.htm?type=command&param=getcameras')['result']
           _idx = getCameras(_cameras)
           if len(_idx['suggestions']) > 0:
                       print('suggestions camera')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                              _name = i['Name']
                              _address = i['Address']
                              _imageurl = i['ImageURL']
                              bot.sendMessage(chat_id, _name, reply_markup=None)
                              _url = 'http://'+_address+_imageurl
                              _file_name = 'camera0'+i['idx']+'.jpg'
                              try:
                                  urllib.request.urlretrieve(_url, _file_name)
                                  bot.sendPhoto(chat_id, open(_file_name, 'rb') )
                              except timeout:
                                  bot.sendMessage(chat_id, 'timeout error on: '+_name, reply_markup=None)   
           else:
             bot.sendMessage(chat_id, 'No cameras found')
       
       elif command.lower() == 'temperature':
           _temps = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=temp&used=true')['result']
           _idx = getIDXByType(_temps)
           if len(_idx['suggestions']) > 0:
                       print('suggestions temperature')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                              _name, _state = getDataByIDX(i['idx'], i['type'])
                              bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)
           else:
             bot.sendMessage(chat_id, 'No Temperature Sensors found')
       elif command.lower() == 'weather':
           _weather = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=weather&used=true')['result']
           _idx = getIDXByType(_weather)
           if len(_idx['suggestions']) > 0:
                       print('suggestions weather')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                              _name, _state = getDataByIDX(i['idx'], i['type'])
                              bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)
           else:
             bot.sendMessage(chat_id, 'No Weather Sensors found')

       elif command.lower() == 'rooms':
           _rooms = getDomoticzUrl(url + '/json.htm?type=command&param=getplans&order=name&used=true')['result']
           _idx = getIDXRooms(_rooms)
           if len(_idx['suggestions']) > 0:
                       print('suggestions rooms')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                               _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/room ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       #print(markup_dyn)
                       bot.sendMessage(chat_id, '** Rooms **')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   multipleMark.append(i)
                                   send = False
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All Rooms Devices', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No Rooms found')
                          
       elif command.lower() == 'utility':
           _utility = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=utility&used=true')['result']
           _idx = getIDXByType(_utility)
           if len(_idx['suggestions']) > 0:
                       print('suggestions utility')
                       #print(_idx['suggestions'])
                       _arr = []
                       for i in _idx['suggestions']:
                           if i['type'].lower() == 'setpoint':
                               _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))
                           else:
                              _name, _state = getDataByIDX(i['idx'],i['type'])
                              bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       bot.sendMessage(chat_id, '** Setpoints **')
                       if len(_arr) > 3:
                           counter = 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   multipleMark.append(i)
                                   send = False
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       else:
                           bot.sendMessage(chat_id, 'All Utility Devices', reply_markup=markup_dyn)
           else:
             bot.sendMessage(chat_id, 'No Utility Devices found')
             
       else:
           if command.lower() != '':
               _alldevices = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&used=true')['result']
               #_switches = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=light&used=true')['result']
               _groups = getDomoticzUrl(url + '/json.htm?type=command&param=getscenes')['result']
               _temps = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=temp&used=true')['result']
               _utility = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=utility&used=true')['result']
               _cameras = getDomoticzUrl(url + '/json.htm?type=command&param=getcameras')['result']
               _weather = getDomoticzUrl(url + '/json.htm?type=command&param=getdevices&filter=weather&used=true')['result']
               _utilityTypes = sorted(Counter(x['SubType'].lower().replace(' ', '_').replace('/', '_') for x in _utility if 'SubType' in x)) + sorted(Counter(x['Type'].lower().replace(' ', '_').replace('/', '_') for x in _utility if 'Type' in x))
               _tempTypes = sorted(Counter(x['SubType'].lower().replace(' ', '_').replace('/', '_') for x in _temps if 'SubType' in x)) + sorted(Counter(x['Type'].lower().replace(' ', '_').replace('/', '_') for x in _temps if 'Type' in x))
               _WeatherTypes = sorted(Counter(x['SubType'].lower().replace(' ', '_').replace('/', '_') for x in _weather if 'SubType' in x)) + sorted(Counter(x['Type'].lower().replace(' ', '_').replace('/', '_') for x in _weather if 'Type' in x))

               print('command: ' +command.lower())
               _devices = _alldevices + _groups + _cameras
               _idx = getIDXByName(command.lower(), _devices)
               if _idx['idx'] != '':
                   print('_idx[idx]')
                   print(_idx['idx'] + ' , ' + _idx['type'])
                   _switchTypes = ['on_off', 'blinds', 'x10']
                   if _idx['type'].lower() in _switchTypes:
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
                       ])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'group':
                       _callbackCommand = '/group ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'), InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off')],
                       ])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'scene':
                       _callbackCommand = '/group ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on')],
                       ])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'push_on_button':
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[
                       [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on')],
                       ])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() in _tempTypes:
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       markup_dyn = None
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'selector':
                       _arr = []
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       for i in _idx['levels']:
                           _arr.append(
                           InlineKeyboardButton(text=i['Name'], callback_data=_callbackCommand + 'Set%20Level&level=' + i['level'])
                           )
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'dimmer' or _idx['type'].lower() == 'blinds_percentage':
                       _arr = []
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       _dimmerlevels = ['On', 'on'],['20', 'Set%20Level&level=20'],['50', 'Set%20Level&level=50'],['70', 'Set%20Level&level=70'],['100', 'Set%20Level&level=100'],['Off', 'off']
                       for i in _dimmerlevels:
                           _arr.append(
                           InlineKeyboardButton(text=i[0], callback_data=_callbackCommand + i[1])
                           )
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'blinds_+_stop':
                       _arr = []
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       _dimmerlevels = ['Open', 'open'],['Stop', 'stop'],['Close', 'close'],['20', 'Set%20Level&level=20'],['50', 'Set%20Level&level=50'],['70', 'Set%20Level&level=70'],['100', 'Set%20Level&level=100']
                       for i in _dimmerlevels:
                           _arr.append(
                           InlineKeyboardButton(text=i[0], callback_data=_callbackCommand + i[1])
                           )
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'venetian_blinds_us' or _idx['type'].lower() == 'venetian_blinds_eu':
                       _arr = []
                       _callbackCommand = '/switch ' + _idx['idx'] + ' '
                       _dimmerlevels = ['Open', 'open'],['Stop', 'stop'],['Close', 'close']
                       for i in _dimmerlevels:
                           _arr.append(
                           InlineKeyboardButton(text=i[0], callback_data=_callbackCommand + i[1])
                           )
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() == 'setpoint':
                       _arr = []
                       _callbackCommand = '/setpoint ' + _idx['idx'] + ' '
                       _config = getSetpointConfig(_idx['idx'])
                       _SPmin = _config[2]
                       _SPmax = _config[3]
                       _SPstep = _config[1]
                       if int(_SPmin) == -200 and int(_SPmax) == 200 and _SPstep == 0.5:
                           _SPmin = 14
                           _SPmax = 25
                           _SPstep = 1                  
                       for i in range(int(_SPmin), int(_SPmax), int(_SPstep)):
                           _arr.append(InlineKeyboardButton(text=str(i), callback_data=_callbackCommand + str(i)))                       

                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)

                   elif _idx['type'].lower() in _utilityTypes:
                       _callbackCommand = '/utility ' + _idx['idx'] + ' '
                       markup_dyn = None
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   elif _idx['type'].lower() in _WeatherTypes:
                       _callbackCommand = '/weather ' + _idx['idx'] + ' '
                       markup_dyn = None
                       _name, _state = getDataByIDX(_idx['idx'], _idx['type'])
                       bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup_dyn)
                   else:
                    bot.sendMessage(chat_id, 'No action programmed for ' + command.lower() + ' type ' + _idx['type'].lower()+ '?', reply_markup=markup_dyn)
               else:
                   if len(_idx['suggestions']) > 0:
                       print('handle suggestions')
                       #print(_idx['suggestions'])
                       _arr = []
                       Scounter= 0
                       _settypes = ['on_off', 'selector', 'dimmer', 'group','scene','setpoint','x10','room','blinds_percentage','venetian_blinds_us','venetian_blinds_eu','blinds_+_stop', 'push_on_button']
                       for i in _idx['suggestions']:
                           if i['type'].lower() in _settypes:
                               _arr.append(InlineKeyboardButton(text=i['Name'], callback_data='/suggestion ' + i['idx'] + ' ' + i['type'] + ' ' + str(chat_id)))
                           else:
                              _name, _state = getDataByIDX(i['idx'],i['type'])
                              if Scounter == 0: 
                                 bot.sendMessage(chat_id, '** Found Sensor Devices **')
                              bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)
                              Scounter += 1
                       
                       markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr])
                       if len(_arr) > 3:
                           bot.sendMessage(chat_id, '** Found Switches and Setpoints **')
                           
                       if len(_arr) > 3:
                           counter= 0
                           multipleMark = []
                           for i in _arr:
                               if len(multipleMark) == 3:
                                   bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                                   multipleMark[:] = []
                                   multipleMark.append(i)
                                   send = False
                                   counter += 1
                               else:
                                   multipleMark.append(i)
                                   send = False
                           if send == False:
                               bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[multipleMark]))
                       elif len(_arr) > 0 < 3:
                           bot.sendMessage(chat_id, '** Found Switches and Setpoints **', reply_markup=markup_dyn)
                   else:
                       bot.sendMessage(chat_id, command.title() + ' device not found!')
           else:
             bot.sendMessage(chat_id, 'No Device found')

       if run:
           getDomoticzUrl(url)

## Listening
bot = telepot.Bot(bot_token)
MessageLoop(bot, {'chat': handle,
                  'callback_query': on_callback_query}).run_as_thread()
print('I am listening...')

while True:
	try:
		self.bot.sendMessage(chat_id, message, **kwargs)
		break
	except telepot.exception.TelegramError as e:
		raise e
	except Exception as e:
		time.sleep(2) # wait 2 more second to send again
