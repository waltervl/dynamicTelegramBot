#!/usr/bin/env python3
## Created by Squandor for python3
## Updated by Waltervl for Domoticz 2023.2 and up
## Updated by Waltervl to enhance functionality
import os
import time
import telepot
import urllib.error
import urllib.parse
import urllib.request
import urllib3
import socket
import json
import re
import base64
import configparser as ConfigParser
from decimal import Decimal, InvalidOperation
from telepot.loop import MessageLoop
from telepot.namedtuple import ReplyKeyboardMarkup
from telepot.namedtuple import InlineKeyboardMarkup, InlineKeyboardButton
import telepot.api

telepot.api._pools = {
    'default': urllib3.PoolManager(num_pools=3, maxsize=10, retries=6, timeout=20),
}

DOMOTICZ_HTTP = urllib3.PoolManager()
DEFAULT_DOMOTICZ_RESPONSE = {'status': 'ERR', 'result': []}
SETTABLE_TYPES = set([
    'on_off', 'dimmer', 'group', 'scene', 'setpoint', 'x10',
    'venetian_blinds_us', 'venetian_blinds_eu', 'blinds_percentage',
    'blinds_+_stop', 'push_on_button',
])
SWITCH_TYPES = set([
    'on_off', 'selector', 'dimmer', 'venetian_blinds_us',
    'venetian_blinds_eu', 'blinds_percentage', 'blinds_+_stop',
    'push_on_button',
])


def load_config():
    config = ConfigParser.ConfigParser()
    if os.path.isfile('config.ini'):
        config.read('config.ini')
    else:
        config.add_section('config')
        config.set('config', 'url', input('Url (http://0.0.0.0:8080): '))
        config.set('config', 'bot_token', input('Bot token: '))
        config.set('config', 'unames', input('Usernames (user1, user2, user3): '))
        with open('config.ini', 'w') as cfgfile:
            config.write(cfgfile)

    url = config.get('config', 'url')
    bot_token = config.get('config', 'bot_token')
    unames = [uname.strip().lower() for uname in config.get('config', 'unames').split(',') if uname.strip()]
    return config, url, bot_token, unames


########### Config ###############
Config, url, bot_token, unames = load_config()
##################################
socket.setdefaulttimeout(10)


def build_domoticz_url(param, **params):
    query = {'type': 'command', 'param': param}
    query.update(params)
    return url + '/json.htm?' + urllib.parse.urlencode(query)


def getDomoticzUrl(request_url):
    try:
        resp = DOMOTICZ_HTTP.request('GET', request_url, timeout=urllib3.Timeout(connect=5.0, read=10.0))
        if getattr(resp, 'status', None) and resp.status != 200:
            print('getDomoticzUrl: HTTP', resp.status, 'for', request_url)
            return DEFAULT_DOMOTICZ_RESPONSE.copy()
        raw = resp.data.decode('utf-8') if resp.data is not None else ''
        if not raw:
            print('getDomoticzUrl: empty response for', request_url)
            return DEFAULT_DOMOTICZ_RESPONSE.copy()
        try:
            return json.loads(raw)
        except ValueError as err:
            print('getDomoticzUrl: JSON decode error:', err, 'response:', raw)
            return DEFAULT_DOMOTICZ_RESPONSE.copy()
    except (urllib3.exceptions.HTTPError, socket.timeout, UnicodeDecodeError) as err:
        print('getDomoticzUrl: request error for', request_url, ':', err)
        return DEFAULT_DOMOTICZ_RESPONSE.copy()


def domoticz_request(param, **params):
    return getDomoticzUrl(build_domoticz_url(param, **params))


def get_result_list(response):
    result = response.get('result')
    if isinstance(result, list):
        return result
    return []


def get_first_result(response):
    result = get_result_list(response)
    if result:
        return result[0]
    return {}


def get_device_type(device):
    for key in ('SwitchType', 'SubType', 'Type'):
        value = device.get(key)
        if value:
            return value.replace(' ', '_').replace('/', '_')
    return 'camera'


def get_device_types(devices):
    return sorted(set(get_device_type(device).lower() for device in devices))


def getSelectorNames(_idx):
    print('getSelectorNames(_idx)')
    _configdata = get_first_result(domoticz_request('getdevices', rid=_idx))
    _level_names = _configdata.get('LevelNames', '')
    if not _level_names:
        return []

    try:
        _levelActions = base64.b64decode(_level_names).decode('utf-8').split('|')
    except (TypeError, ValueError, UnicodeDecodeError, base64.binascii.Error):
        return []

    _levels = []
    for _lvls, _level in enumerate(_levelActions):
        _levels.append({
            'Name': _level,
            'level': '0' if _lvls == 0 else str(_lvls) + '0'
        })
    return _levels


def getSetpointConfig(_idx):
    print('getSetpointConfig(_idx)')
    _configdata = get_first_result(domoticz_request('getdevices', rid=_idx))
    return [
        _configdata.get('vunit', ''),
        _configdata.get('step', 1),
        _configdata.get('min', 0),
        _configdata.get('max', 0),
    ]


def build_device_entry(device):
    _type = get_device_type(device)
    _entry = {
        'idx': str(device.get('idx', '')),
        'suggestions': [],
        'type': _type,
        'levels': [],
        'Name': device.get('Name', ''),
    }
    if _type.lower() == 'selector':
        _entry['levels'] = getSelectorNames(_entry['idx'])
    elif _type.lower() == 'setpoint':
        _entry['levels'] = getSetpointConfig(_entry['idx'])
    return _entry


def getIDXByName(name, _devices):
    print('getIDXByName(name, _devices)')
    _idx = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    _pattern = re.compile('.*' + re.escape(name.lower()) + '.*')
    for device in _devices:
        _name = device.get('Name', '')
        if _name.lower() == name.lower():
            _entry = build_device_entry(device)
            _idx['idx'] = _entry['idx']
            _idx['type'] = _entry['type']
            _idx['levels'] = _entry['levels']
            break
        if _pattern.search(_name.lower().strip()):
            _idx['suggestions'].append(build_device_entry(device))
    return _idx


def getIDXByType(_devices):
    print('getIDXByType(_devices)')
    _idx_sug = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for device in _devices:
        _idx_sug['suggestions'].append(build_device_entry(device))
    return _idx_sug


def getIDXRooms(_devices):
    print('getIDXRooms(_devices)')
    _idx_sug = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for device in _devices:
        if device.get('Devices', 0) > 0:
            _idx_sug['suggestions'].append({
                'idx': str(device.get('idx', '')),
                'type': 'room',
                'Name': device.get('Name', ''),
            })
    return _idx_sug


def getCameras(_devices):
    print('getCameras(_devices)')
    _idx_sug = {'idx': '', 'suggestions': [], 'type': '', 'levels': []}
    for device in _devices:
        _idx_sug['suggestions'].append({
            'idx': str(device.get('idx', '')),
            'type': 'camera',
            'Address': device.get('Address', ''),
            'Name': device.get('Name', ''),
            'ImageURL': device.get('ImageURL', ''),
        })
    return _idx_sug


def get_status_value(device):
    _status = device.get('Status')
    if _status:
        return _status.title()
    return device.get('Data', '')


def getNameByIDX(dev, _devices):
    print('getNameByIDX(dev, _devices)')
    for device in _devices:
        if str(device.get('idx', '')) == str(dev.get('idx', '')):
            _type = get_device_type(device)
            if _type.lower() == dev.get('type', '').lower():
                if _type.lower() == 'selector':
                    _status = ''
                    _stateCount = str(device.get('Status', '')).replace('Set Level: ', '').replace(' %', '')
                    for selector in getSelectorNames(device.get('idx', '')):
                        if selector['level'] == _stateCount:
                            _status = selector['Name'].title()
                            break
                else:
                    _status = get_status_value(device)
                return device.get('Name', '').title(), _status
    return '', ''


def get_data_response(_data_idx, _type):
    if _type.lower() in ('scene', 'group'):
        return get_first_result(domoticz_request('getscenes', rid=_data_idx))
    if _type.lower() == 'camera':
        return get_first_result(domoticz_request('getcameras', rid=_data_idx))
    return get_first_result(domoticz_request('getdevices', rid=_data_idx))


def get_selector_status(_data_idx, _IDXData):
    _stateInt = _IDXData.get('Level')
    try:
        _stateInt = int(_stateInt)
    except (TypeError, ValueError):
        return ''

    for selector in getSelectorNames(_data_idx):
        try:
            if int(selector['level']) == _stateInt:
                return selector['Name'].title()
        except (TypeError, ValueError, KeyError):
            pass
    return ''


def get_setpoint_status(_data_idx, _IDXData):
    _config = getSetpointConfig(_data_idx)
    _unit = _config[0]
    _data = _IDXData.get('Data', '')
    if _unit:
        return (_data + ' ' + _unit).strip()
    return _data


def getDataByIDX(_data_idx, _type):
    print('getDataByIDX(_data_idx)')
    _IDXData = get_data_response(_data_idx, _type)
    if not _IDXData:
        return '', ''

    _status = ''
    if _type.lower() == 'selector':
        _status = get_selector_status(_data_idx, _IDXData)
    elif _type.lower() == 'setpoint':
        _status = get_setpoint_status(_data_idx, _IDXData)
    elif _type.lower() == 'kwh':
        _status = 'Current ' + _IDXData.get('Usage', '') + ', Today ' + _IDXData.get('CounterToday', '') + ', Total ' + _IDXData.get('Data', '')
    elif _type.lower() == 'energy':
        _status = (
            'Current Usage ' + _IDXData.get('Usage', '') +
            ', Current Deliv ' + _IDXData.get('UsageDeliv', '') +
            ', Today Usage ' + _IDXData.get('CounterToday', '') +
            ', Today Deliv ' + _IDXData.get('CounterDelivToday', '') +
            ', Total Usage ' + _IDXData.get('Counter', '') + ' kWh, Total Deliv ' +
            _IDXData.get('CounterDeliv', '') + ' kWh'
        )
    elif _type.lower() == 'gas':
        _status = 'Today ' + _IDXData.get('CounterToday', '') + ', Total ' + _IDXData.get('Data', '')
    elif _type.lower() == 'rainbyrate':
        _status = 'Current ' + _IDXData.get('RainRate', '') + ' mm/h , Today ' + _IDXData.get('Rain', '') + ' mm'
    elif _type.lower() == 'tfa':
        _status = 'Speed ' + _IDXData.get('Speed', '') + 'km/h, Direction ' + _IDXData.get('DirectionStr', '') + ', Gusts ' + _IDXData.get('Gust', '') + ' km/h'
    elif _type.lower() == 'camera':
        _status = 'Use camera devices button to get all cameras'
    else:
        _status = get_status_value(_IDXData)

    _name = _IDXData.get('Name', '').title()
    return _name, _status


def chunked(items, size):
    return [items[index:index + size] for index in range(0, len(items), size)]


def send_button_rows(chat_id, buttons, row_size=3, prefix='-'):
    for row in chunked(buttons, row_size):
        bot.sendMessage(chat_id, prefix, reply_markup=InlineKeyboardMarkup(inline_keyboard=[row]))


def send_device_status(chat_id, device_idx, device_type):
    _name, _state = getDataByIDX(device_idx, device_type)
    if _name or _state:
        bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)


def send_actionable_list(chat_id, suggestions, actionable_types, callback_prefix, single_text, empty_text,
                         intro_text=None, action_header=None, row_size=3, always_action_header=False):
    if not suggestions:
        bot.sendMessage(chat_id, empty_text)
        return

    if intro_text:
        bot.sendMessage(chat_id, intro_text)

    _arr = []
    for device in suggestions:
        if device['type'].lower() in actionable_types:
            _arr.append(
                InlineKeyboardButton(
                    text=device['Name'],
                    callback_data=callback_prefix + device['idx'] + ' ' + device['type'] + ' ' + str(chat_id)
                )
            )
        else:
            send_device_status(chat_id, device['idx'], device['type'])

    if action_header and (always_action_header or _arr):
        bot.sendMessage(chat_id, action_header)

    if len(_arr) > row_size:
        send_button_rows(chat_id, _arr, row_size=row_size, prefix='-')
    elif _arr:
        bot.sendMessage(chat_id, single_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[_arr]))


def get_decimal(value, default):
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal(str(default))


def format_decimal_value(value):
    if value == value.to_integral():
        return str(int(value))
    return format(value.normalize(), 'f').rstrip('0').rstrip('.')


def get_setpoint_values(config):
    _SPstep = get_decimal(config[1], 1)
    _SPmin = get_decimal(config[2], 0)
    _SPmax = get_decimal(config[3], 0)

    if _SPmin == Decimal('-200') and _SPmax == Decimal('200') and _SPstep == Decimal('0.5'):
        _SPmin = Decimal('14')
        _SPmax = Decimal('25')
        _SPstep = Decimal('1')

    if _SPstep <= 0:
        return []

    _values = []
    _current = _SPmin
    _guard = 0
    while _current < _SPmax and _guard < 1000:
        _values.append(format_decimal_value(_current))
        _current += _SPstep
        _guard += 1
    return _values


def build_action_buttons(device_idx, device_type, levels=None):
    _type = device_type.lower()
    if _type in ('on_off', 'blinds', 'x10'):
        _callbackCommand = '/switch ' + device_idx + ' '
        return [
            InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'),
            InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off'),
        ]
    if _type == 'group':
        _callbackCommand = '/group ' + device_idx + ' '
        return [
            InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on'),
            InlineKeyboardButton(text='Off', callback_data=_callbackCommand + 'off'),
        ]
    if _type == 'scene':
        _callbackCommand = '/group ' + device_idx + ' '
        return [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on')]
    if _type == 'push_on_button':
        _callbackCommand = '/switch ' + device_idx + ' '
        return [InlineKeyboardButton(text='On', callback_data=_callbackCommand + 'on')]
    if _type == 'selector':
        _callbackCommand = '/switch ' + device_idx + ' '
        _levels = levels if levels is not None else getSelectorNames(device_idx)
        return [
            InlineKeyboardButton(text=level['Name'], callback_data=_callbackCommand + 'Set%20Level&level=' + level['level'])
            for level in _levels
        ]
    if _type in ('dimmer', 'blinds_percentage'):
        _callbackCommand = '/switch ' + device_idx + ' '
        _dimmerlevels = [
            ('On', 'on'),
            ('20', 'Set%20Level&level=20'),
            ('50', 'Set%20Level&level=50'),
            ('70', 'Set%20Level&level=70'),
            ('100', 'Set%20Level&level=100'),
            ('Off', 'off'),
        ]
        return [InlineKeyboardButton(text=level[0], callback_data=_callbackCommand + level[1]) for level in _dimmerlevels]
    if _type == 'blinds_+_stop':
        _callbackCommand = '/switch ' + device_idx + ' '
        _dimmerlevels = [
            ('Open', 'open'),
            ('Stop', 'stop'),
            ('Close', 'close'),
            ('20', 'Set%20Level&level=20'),
            ('50', 'Set%20Level&level=50'),
            ('70', 'Set%20Level&level=70'),
            ('100', 'Set%20Level&level=100'),
        ]
        return [InlineKeyboardButton(text=level[0], callback_data=_callbackCommand + level[1]) for level in _dimmerlevels]
    if _type in ('venetian_blinds_us', 'venetian_blinds_eu'):
        _callbackCommand = '/switch ' + device_idx + ' '
        _dimmerlevels = [('Open', 'open'), ('Stop', 'stop'), ('Close', 'close')]
        return [InlineKeyboardButton(text=level[0], callback_data=_callbackCommand + level[1]) for level in _dimmerlevels]
    if _type == 'setpoint':
        _callbackCommand = '/setpoint ' + device_idx + ' '
        _config = levels if levels is not None else getSetpointConfig(device_idx)
        return [
            InlineKeyboardButton(text=value, callback_data=_callbackCommand + value)
            for value in get_setpoint_values(_config)
        ]
    return []


def send_device_action_message(chat_id, device_idx, device_type, levels=None):
    buttons = build_action_buttons(device_idx, device_type, levels=levels)
    markup = InlineKeyboardMarkup(inline_keyboard=[buttons]) if buttons else None
    _name, _state = getDataByIDX(device_idx, device_type)
    bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=markup)


def send_camera_messages(chat_id, cameras):
    if not cameras:
        bot.sendMessage(chat_id, 'No cameras found')
        return

    _camera_dir = os.path.join('/tmp', 'dynamicTelegramBot')
    os.makedirs(_camera_dir, exist_ok=True)
    for camera in cameras:
        _name = camera['Name']
        _address = camera.get('Address', '')
        _imageurl = camera.get('ImageURL', '')
        bot.sendMessage(chat_id, _name, reply_markup=None)
        _url = 'http://' + _address + _imageurl
        _file_name = os.path.join(_camera_dir, 'camera0' + camera['idx'] + '.jpg')
        try:
            urllib.request.urlretrieve(_url, _file_name)
            with open(_file_name, 'rb') as camera_file:
                bot.sendPhoto(chat_id, camera_file)
        except (socket.timeout, urllib.error.URLError, OSError):
            bot.sendMessage(chat_id, 'timeout error on: ' + _name, reply_markup=None)


def get_message_types(*device_lists):
    _types = set()
    for device_list in device_lists:
        _types.update(get_device_types(device_list))
    return _types


def normalize_switch_command(command):
    return command.title().replace('Level=', 'level=').strip()


def handle_switch_callback(query_id, parts):
    runUrl = url + '/json.htm?type=command&param=switchlight&idx=' + parts[1] + '&switchcmd=' + normalize_switch_command(parts[2].lower())
    _res = getDomoticzUrl(runUrl)
    if _res.get('status', 'ERR').lower() == 'ok':
        bot_text = 'Command executed, Switch ' + parts[2].lower().title()
    else:
        bot_text = 'Command failed: ' + runUrl
    bot.answerCallbackQuery(query_id, text=bot_text)


def handle_group_callback(query_id, parts):
    runUrl = url + '/json.htm?type=command&param=switchscene&idx=' + parts[1] + '&switchcmd=' + normalize_switch_command(parts[2].lower())
    _res = getDomoticzUrl(runUrl)
    if _res.get('status', 'ERR').lower() == 'ok':
        bot_text = 'Command executed'
    else:
        bot_text = 'Command failed: ' + runUrl
    bot.answerCallbackQuery(query_id, text=bot_text)


def handle_setpoint_callback(query_id, parts):
    runUrl = url + '/json.htm?type=command&param=setsetpoint&idx=' + parts[1] + '&setpoint=' + parts[2].lower()
    _res = getDomoticzUrl(runUrl)
    if _res.get('status', 'ERR').lower() == 'ok':
        bot_text = 'Setpoint succesfully set to ' + parts[2].lower()
    else:
        bot_text = 'Command failed: ' + runUrl
    bot.answerCallbackQuery(query_id, text=bot_text)


def handle_data_callback(query_id, parts):
    runUrl = build_domoticz_url('getdevices', rid=parts[1])
    _res = getDomoticzUrl(runUrl)
    if _res.get('status', 'ERR').lower() == 'ok':
        _data = get_first_result(_res).get('Data', '')
        bot.answerCallbackQuery(query_id, text=_data if _data else 'Command executed')
    else:
        bot.answerCallbackQuery(query_id, text='Command failed: ' + runUrl)


def handle_room_callback(parts):
    print('callback room')
    _roomdevices = get_result_list(domoticz_request('getdevices', plan=parts[1]))
    _idx = getIDXByType(_roomdevices)
    chat_id = int(parts[3])
    if len(_idx['suggestions']) > 0:
        bot.sendMessage(chat_id, '** Room Devices **')
        _arr = []
        for device in _idx['suggestions']:
            if device['type'].lower() in SETTABLE_TYPES:
                _arr.append(InlineKeyboardButton(text=device['Name'], callback_data='/suggestion ' + device['idx'] + ' ' + device['type'] + ' ' + parts[3]))
            else:
                send_device_status(chat_id, device['idx'], device['type'])

        if _arr:
            bot.sendMessage(chat_id, '** Switches, Scenes and Groups in Room **')
            if len(_arr) > 3:
                send_button_rows(chat_id, _arr, row_size=3, prefix='-')
            else:
                bot.sendMessage(chat_id, '-', reply_markup=InlineKeyboardMarkup(inline_keyboard=[_arr]))
    else:
        bot.sendMessage(chat_id, 'No room Device found')


def handle_suggestion_callback(parts):
    print('callback suggestion')
    _utility = get_result_list(domoticz_request('getdevices', filter='utility', used='true'))
    _temps = get_result_list(domoticz_request('getdevices', filter='temp', used='true'))
    _utilityTypes = set(get_device_types(_utility))
    _tempTypes = set(get_device_types(_temps))

    _device_type = parts[2].lower()
    _name2, _state2 = getDataByIDX(parts[1], parts[2])
    _many = False
    _arr = build_action_buttons(parts[1], parts[2])
    markup_dyn = InlineKeyboardMarkup(inline_keyboard=[_arr]) if _arr else None

    if _device_type in _utilityTypes and _device_type == 'setpoint':
        _many = len(_arr) > 3
    elif _device_type == 'selector':
        _many = len(_arr) > 3
    elif _device_type in _tempTypes or (_device_type in _utilityTypes and _device_type != 'setpoint'):
        markup_dyn = None

    if _many:
        chat_id = int(parts[3])
        bot.sendMessage(chat_id, _name2 + ' is currently ' + _state2 + '.')
        send_button_rows(chat_id, _arr, row_size=6, prefix='SET:')
    else:
        bot.sendMessage(int(parts[3]), _name2 + ' is currently ' + _state2 + '.', reply_markup=markup_dyn)


def on_callback_query(msg):
    query_id, from_id, query_data = telepot.glance(msg, flavor='callback_query')
    print('on_callback_query(msg)')
    parts = query_data.split(' ')
    if len(parts) < 2:
        bot.answerCallbackQuery(query_id, text='Command failed: ' + query_data)
        return

    command = parts[0].lower()
    if command == '/switch' and len(parts) >= 3:
        handle_switch_callback(query_id, parts)
    elif command == '/group' and len(parts) >= 3:
        handle_group_callback(query_id, parts)
    elif command == '/setpoint' and len(parts) >= 3:
        handle_setpoint_callback(query_id, parts)
    elif command in ('/utility', '/temp') and len(parts) >= 2:
        handle_data_callback(query_id, parts)
    elif command == '/room' and len(parts) >= 4:
        handle_room_callback(parts)
    elif command == '/suggestion' and len(parts) >= 4:
        handle_suggestion_callback(parts)
    else:
        bot.answerCallbackQuery(query_id, text='Command failed: ' + query_data)


def get_reply_markups():
    markup_main = ReplyKeyboardMarkup(
        keyboard=[['Dashboard'], ['Device Tabs', 'Rooms']],
        one_time_keyboard=False,
        resize_keyboard=True
    )
    markup_device_tabs = ReplyKeyboardMarkup(
        keyboard=[['Switches', 'Grp Scenes', 'Temperature'], ['Utility', 'Weather', 'Cameras'], ['Back']],
        one_time_keyboard=False,
        resize_keyboard=True
    )
    return markup_main, markup_device_tabs


def handle_dashboard(chat_id):
    _favorites = get_result_list(domoticz_request('getdevices', used='true', filter='all', favorite='1'))
    _idx = getIDXByType(_favorites)
    send_actionable_list(
        chat_id,
        _idx['suggestions'],
        SETTABLE_TYPES,
        '/suggestion ',
        'Dashboard',
        'No dashboard Device found',
        intro_text='** Dashboard Devices **',
        action_header='** Switches, Scenes and Groups in Dashboard **',
        always_action_header=True,
    )


def handle_switches(chat_id):
    _switches = get_result_list(domoticz_request('getdevices', filter='light', used='true'))
    _idx = getIDXByType(_switches)
    send_actionable_list(
        chat_id,
        _idx['suggestions'],
        SWITCH_TYPES,
        '/suggestion ',
        'All Switches',
        'No switch Device found',
        intro_text='** Switches/Lights/Sensors read only**',
        action_header='** Switches/Lights **',
        always_action_header=True,
    )


def handle_scenes(chat_id):
    _groups = get_result_list(domoticz_request('getscenes'))
    _idx = getIDXByType(_groups)
    send_actionable_list(
        chat_id,
        _idx['suggestions'],
        get_message_types(_groups),
        '/suggestion ',
        'All Group/Scene Devices',
        'No Group/Scene Device found',
    )


def handle_cameras(chat_id):
    _cameras = get_result_list(domoticz_request('getcameras'))
    _idx = getCameras(_cameras)
    send_camera_messages(chat_id, _idx['suggestions'])


def handle_read_only_list(chat_id, filter_name, empty_text):
    _devices = get_result_list(domoticz_request('getdevices', filter=filter_name, used='true'))
    _idx = getIDXByType(_devices)
    if len(_idx['suggestions']) > 0:
        for device in _idx['suggestions']:
            send_device_status(chat_id, device['idx'], device['type'])
    else:
        bot.sendMessage(chat_id, empty_text)


def handle_rooms(chat_id):
    _rooms = get_result_list(domoticz_request('getplans', order='name', used='true'))
    _idx = getIDXRooms(_rooms)
    if len(_idx['suggestions']) > 0:
        bot.sendMessage(chat_id, '** Rooms **')
        _arr = [
            InlineKeyboardButton(text=device['Name'], callback_data='/room ' + device['idx'] + ' ' + device['type'] + ' ' + str(chat_id))
            for device in _idx['suggestions']
        ]
        if len(_arr) > 3:
            send_button_rows(chat_id, _arr, row_size=3, prefix='-')
        else:
            bot.sendMessage(chat_id, 'All Rooms Devices', reply_markup=InlineKeyboardMarkup(inline_keyboard=[_arr]))
    else:
        bot.sendMessage(chat_id, 'No Rooms found')


def handle_utility(chat_id):
    _utility = get_result_list(domoticz_request('getdevices', filter='utility', used='true'))
    _idx = getIDXByType(_utility)
    send_actionable_list(
        chat_id,
        _idx['suggestions'],
        set(['setpoint']),
        '/suggestion ',
        'All Utility Devices',
        'No Utility Devices found',
        action_header='** Setpoints **',
        always_action_header=True,
    )


def handle_search(chat_id, command):
    _alldevices = get_result_list(domoticz_request('getdevices', used='true'))
    _groups = get_result_list(domoticz_request('getscenes'))
    _temps = get_result_list(domoticz_request('getdevices', filter='temp', used='true'))
    _utility = get_result_list(domoticz_request('getdevices', filter='utility', used='true'))
    _cameras = get_result_list(domoticz_request('getcameras'))
    _weather = get_result_list(domoticz_request('getdevices', filter='weather', used='true'))

    _utilityTypes = set(get_device_types(_utility))
    _tempTypes = set(get_device_types(_temps))
    _WeatherTypes = set(get_device_types(_weather))

    print('command: ' + command.lower())
    _devices = _alldevices + _groups + _cameras
    _idx = getIDXByName(command.lower(), _devices)
    if _idx['idx'] != '':
        print('_idx[idx]')
        print(_idx['idx'] + ' , ' + _idx['type'])
        if _idx['type'].lower() in ('on_off', 'blinds', 'x10'):
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() == 'group':
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() == 'scene':
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() == 'push_on_button':
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() in _tempTypes:
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() == 'selector':
            send_device_action_message(chat_id, _idx['idx'], _idx['type'], levels=_idx['levels'])
        elif _idx['type'].lower() in ('dimmer', 'blinds_percentage'):
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() == 'blinds_+_stop':
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() in ('venetian_blinds_us', 'venetian_blinds_eu'):
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() == 'setpoint':
            send_device_action_message(chat_id, _idx['idx'], _idx['type'], levels=_idx['levels'])
        elif _idx['type'].lower() in _utilityTypes:
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        elif _idx['type'].lower() in _WeatherTypes:
            send_device_action_message(chat_id, _idx['idx'], _idx['type'])
        else:
            bot.sendMessage(chat_id, 'No action programmed for ' + command.lower() + ' type ' + _idx['type'].lower() + '?', reply_markup=None)
    else:
        if len(_idx['suggestions']) > 0:
            _arr = []
            _sensor_counter = 0
            _search_types = set([
                'on_off', 'selector', 'dimmer', 'group', 'scene', 'setpoint', 'x10',
                'room', 'blinds_percentage', 'venetian_blinds_us', 'venetian_blinds_eu',
                'blinds_+_stop', 'push_on_button',
            ])
            for device in _idx['suggestions']:
                if device['type'].lower() in _search_types:
                    _arr.append(InlineKeyboardButton(text=device['Name'], callback_data='/suggestion ' + device['idx'] + ' ' + device['type'] + ' ' + str(chat_id)))
                else:
                    _name, _state = getDataByIDX(device['idx'], device['type'])
                    if _sensor_counter == 0:
                        bot.sendMessage(chat_id, '** Found Sensor Devices **')
                    bot.sendMessage(chat_id, _name + ': ' + _state + '.', reply_markup=None)
                    _sensor_counter += 1

            if len(_arr) > 3:
                bot.sendMessage(chat_id, '** Found Switches and Setpoints **')
                send_button_rows(chat_id, _arr, row_size=3, prefix='-')
            elif _arr:
                bot.sendMessage(chat_id, '** Found Switches and Setpoints **', reply_markup=InlineKeyboardMarkup(inline_keyboard=[_arr]))
        else:
            bot.sendMessage(chat_id, command.title() + ' device not found!')


def handle(msg):
    print('handle(msg)')
    chat_id = msg['chat']['id']
    command = msg.get('text', '')
    try:
        user = msg['from']['username']
    except KeyError:
        user = msg['from'].get('first_name', '')

    markup_main, markup_device_tabs = get_reply_markups()
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
            handle_dashboard(chat_id)
        elif command.lower() == 'switches':
            handle_switches(chat_id)
        elif command.lower() == 'grp scenes':
            handle_scenes(chat_id)
        elif command.lower() == 'cameras':
            handle_cameras(chat_id)
        elif command.lower() == 'temperature':
            handle_read_only_list(chat_id, 'temp', 'No Temperature Sensors found')
        elif command.lower() == 'weather':
            handle_read_only_list(chat_id, 'weather', 'No Weather Sensors found')
        elif command.lower() == 'rooms':
            handle_rooms(chat_id)
        elif command.lower() == 'utility':
            handle_utility(chat_id)
        elif command.lower() != '':
            handle_search(chat_id, command)
        else:
            bot.sendMessage(chat_id, 'No Device found')


## Listening
bot = telepot.Bot(bot_token)
MessageLoop(bot, {'chat': handle,
                  'callback_query': on_callback_query}).run_as_thread()
print('I am listening...')

while True:
    time.sleep(10)
