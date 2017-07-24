import argparse
import smtplib
from datetime import datetime
from time import sleep

from sense_hat import *

from meteo_props import *

SENSE = SenseHat()
PROPERTIES = MeteoProps()  # Properties for sending email.

# SETTINGS = {
#     "measuring_interval": 60,
#     "statistics": "m",
#     "notification_interval": 43200,
#     "discretisation": 1800,
#     "logging": False,
#     "notification": False
# }



# Measuring interval
# [seconds]
# default: every minute
MEASURING_INTERVAL = 60

# Data evaluation; m: Median, a: Average
# [string]
# default: Median
STATISTICS = "m"

# Email notification interval
# [seconds]
# default: every 12 hours
NOTIFY_INTERVAL = 43200

# Enable/Disable Email notification
# [boolean]
# default: false
NOTIFY = False

# Discretisation of measurements
# [seconds]
# default: every 30 minutes
DISCRETISATION = 1800

# Write data to local json file
# [boolean]
# default: False
# DOCUMENTATION = False

# Send alert Email if measurements exceed certain values
# [double]
# default: no alert
# alert_t = 999;
# alert_h = 999;

# Enable/disable debug logging
# [boolean]
# default: False
LOGGING = False


# instantiate parser
PARSER = argparse.ArgumentParser(description='Monitoring indoor temperature and relative humidity')

# add parser arguments
PARSER.add_argument('-m', type=int,
                    action='store', default=MEASURING_INTERVAL,
                    help='Measuring interval in seconds (default: every 60 seconds)')

PARSER.add_argument('-n', type=int,
                    action='store', default=NOTIFY_INTERVAL,
                    help='Notification interval in seconds (default: every 12 hours)'+
                    '\nNotification has to be manually enabled with argument [--notify]')

PARSER.add_argument('-d', type=int,
                    action='store', default=DISCRETISATION,
                    help='Discretisation of measurements in seconds (default: every 30 minutes)')

PARSER.add_argument('-s', choices=['m', 'a'],
                    action='store', default=STATISTICS,
                    help='Data evaluation; m: Median, a: Average (default: Median)')

PARSER.add_argument('--log', action='store_true',
                    help='Enable debug logging (default: False)')

PARSER.add_argument('--notify', action='store_true',
                    help='Enable Email notification (default: False)')


# parse arguments
ARGS = PARSER.parse_args()

# check arguments
if ARGS.n < ARGS.m:
    PARSER.error("Notification interval has to be larger than measuring interval!")

MEASURING_INTERVAL = ARGS.m
NOTIFY_INTERVAL = ARGS.n
NOTIFY = ARGS.notify
DISCRETISATION = ARGS.d
STATISTICS = ARGS.s
LOGGING = ARGS.log


def create_message(temp, hum):
    """
    Create notification message

    :param temp:
    :param hum:
    :return: message
    """

    st = "median" if STATISTICS == "m" else "average"
    s = "hours" if NOTIFY_INTERVAL > 3600 else "minutes"
    time = round((NOTIFY_INTERVAL/3600), 0) if NOTIFY_INTERVAL > 3600 else round((NOTIFY_INTERVAL/60), 0)

    mt = "The " + st + " temperature for the last " + time + " " + s + " is: " + temp
    mh = "The " + st + " humidity for the last " + time + " " + s + " is: " + hum

    msg = mt + "\n" + mh

    return msg


# send notification via email
def send_notification(t, h):

    msg = create_message(t, h)
    send_mail(msg)


# logic for sending email
def send_mail(msg):
    """
    Send E-Mail to address specified in meteo_props.py

    :param msg: message to send as String
    :return: none
    """

    pw = PROPERTIES.from_mail_pw
    fm = PROPERTIES.from_mail
    tm = PROPERTIES.to_mail

    server = smtplib.SMTP('smtp.gmail.com', '587')
    server.starttls()
    server.login(fm, pw)
    server.sendmail(fm, tm, msg)
    server.quit()

    if LOGGING:
        print("mail successfully sent at: ", datetime.datetime.now())


def median(alist):
    srtd = sorted(alist)
    length = len(alist)
    mid = length//2

    if length % 2 == 0:
        return (srtd[mid] + srtd[mid - 1]) / 2
    else:
        return srtd[mid]


def mean(alist):
    """
    Calculate median of a given list

    :param alist: list with values
    :return: median
    """
    # TODO: Check if alist is empty or of size 1

    return sum(alist) / len(alist)


def stat(alist):
    # TODO: Check if alist is empty or of size 1
    return median(alist) if STATISTICS == "m" else mean(alist)


def get_cpu_temperature():
    temp_file = open("/sys/class/thermal/thermal_zone0/temp")
    cpu_temp = temp_file.read()
    temp_file.close()

    if LOGGING:
        print("CPU Temp: " + str(round(cpu_temp,1)))

    return float(cpu_temp)/1000


def get_ambient_temperature():

    hat_temp_h = SENSE.get_temperature_from_humidity()
    hat_temp_p = SENSE.get_temperature_from_pressure()

    if hat_temp_p != 0 & hat_temp_h != 0:

        return round(((hat_temp_h + hat_temp_p) / 2), 1)

    else:
        get_ambient_temperature()


def get_relative_humidity():
    return round(SENSE.get_humidity(), 1)


def main():

    h_list = []
    t_list = []
    h_list_discrete = []
    t_list_discrete = []

    start_time_n = datetime
    start_time_d = start_time_n

    while True:

        measured_temp = get_ambient_temperature
        measured_humidity = get_relative_humidity()

        t_list.append(measured_temp)
        h_list.append(measured_humidity)

        # Diskretisierung der Daten
        # TODO: Vergleich von Zeitunterschied
        if datetime - start_time_d >= DISCRETISATION:

            temp = stat(t_list)
            humidity = stat(h_list)

            t_list_discrete.append(temp)
            h_list_discrete.append(humidity)

            t_list.clear()
            h_list.clear()

            start_time_d = datetime

        # send notification
        # TODO: Vergleich von Zeitunterschied
        if datetime - start_time_n >= NOTIFY_INTERVAL:

            send_notification(stat(t_list_discrete), stat(h_list_discrete))

            t_list_discrete.clear()
            h_list_discrete.clear()

            start_time_n = datetime

        # check system temperature
        cpu_temp = get_cpu_temperature()
        if cpu_temp > 60:
            send_mail("HIGH CPU TEMPERATURE!!: ", cpu_temp)

        sleep(MEASURING_INTERVAL)


def joystick():

    test = ""


def initialize():

    main()

    # joystick()


initialize()
