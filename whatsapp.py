import pywhatkit as pwt
import time


def get_current_hour_and_minutes():
    current_time = time.localtime()
    hour = current_time.tm_hour
    minutes = current_time.tm_min
    return hour, minutes


def send_msg(msg):
    hour, minutes = get_current_hour_and_minutes()
    pwt.sendwhatmsg_to_group('EXgiOsLa8QCERgOqjWwm2T', msg, hour, minutes + 2, 25, True)
