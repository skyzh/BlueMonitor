import serial
import struct
import logging
import time
import numpy
from firebase import firebase

from config import config
import const

arduino = serial.Serial(config["serial"]["port"], config["serial"]["baudrate"])

FORMAT = '%(asctime)-15s %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger('Monitor')
logger.setLevel('INFO')

publish = {}
firebase = firebase.FirebaseApplication('https://bluesense-9e31b.firebaseio.com/', authentication=firebase.FirebaseAuthentication(config["firebase"]["secret"], config["firebase"]["email"]))

def establish():
    __zero_count = 0
    while True:
        __data = arduino.read()
        if __data == b"\x00":
            __zero_count = __zero_count + 1
        else:
            __zero_count = 0
            logger.info('broken packet found, retrying...')
        if __zero_count == const.PACKET_SIZE:
            logger.info('empty packet found')
            yield True
            break

def report_error(level, message):
    result = firebase.post('/error', { "level": level, "message": message, "time": time.time() })

def report():
    data = { k: numpy.mean(v) for (k, v) in publish.items() }
    data["time"] = time.time()
    result = firebase.post('/data', data)
    for (k, v) in publish.items():
        v = []

def verify(data):
    content = data[:-2]
    _hash = 0
    for i in content:
        _hash = (_hash + i) % 65536
    (hash, ) = struct.unpack("<H", data[-2:])
    return hash == _hash

def process(data):
    (message_id, response_id, command_id) = struct.unpack_from("<HHH", data)
    data = data[6:]
    if command_id in const.DATA_MAP:
        (value, ) = struct.unpack(const.DATA_MAP[command_id][0], data[:4])
        __key = const.DATA_MAP[command_id][1]
        if not (__key in publish):
            publish[__key] = []
        publish[__key].append(value)
    elif command_id == const.DATA_CMD_FAILED_DHT:
        logger.warning('failed to read dht data')
        report_error(0, 'failed to read dht data')
    elif  command_id == const.DATA_CMD_FAILED_PM:
        logger.warning('failed to read pm data')
        report_error(0, 'failed to read pm data')

def retrive():
    lstReport = time.time()
    while True:
        __data = arduino.read(const.PACKET_SIZE)
        if not verify(__data):
            logger.info('broken packet found, disconnected')
            report_error(0, 'broken packet found, disconnected')
            break
        process(__data)
        if time.time() - lstReport > const.REPORT_TIME:
            lstReport = time.time()
            report()

def loop():
    while True:
        report_error(1, 'establishing connection...')
        logger.info('establishing connection...')
        yield from establish()
        report_error(2, 'connection established, retriving data...')
        logger.info('connection established, retriving data...')
        yield from retrive()

try:
    report_error(1, 'program started')
    for i in loop():
        pass
except KeyboardInterrupt:
    logger.info('user interrupt')