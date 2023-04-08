import pandas as pd
import datetime
import logging
import os
import sys

args = sys.argv
# args = ['a', 'dai']
if args[1] == 'dai':
    CURRENCY_NAME = 'dai'
    CURRENCY_SYMBOL = 'DAIIRT'
    FOLDER_NAME = 'dai'
elif args[1] == 'bitcoin':
    CURRENCY_NAME = 'btc'
    CURRENCY_SYMBOL = 'BTCIRT'
    FOLDER_NAME = 'bitcoin'

files_folder_path = os.path.join(FOLDER_NAME, 'Files')

try:
    total_actionable_orders = pd.read_csv(os.path.join(files_folder_path, 'total_actionable_orders.csv'))
except FileNotFoundError:
    total_actionable_orders = pd.DataFrame(
        columns=['buy_price', 'buy_amount', 'buy_id', 'sell_price', 'sell_amount', 'sell_id'])

with open(os.path.join(files_folder_path, 'token.txt'), 'r') as f:
    token = f.read()


def get_configs():
    result = dict({})

    configs = pd.read_excel(os.path.join(files_folder_path, 'configs.xlsx'))

    tp_coefficient = configs[CURRENCY_NAME][configs['name'] == 'tp_coefficient'].values[0]
    tp_coefficient = 1 + tp_coefficient / 100

    buy_prices_gap_percent = configs[CURRENCY_NAME][configs['name'] == 'buy_prices_gap_percent'].values[0]

    minimum_buy_value = configs[CURRENCY_NAME][configs['name'] == 'minimum_buy_value'].values[0]

    stop_loss = configs[CURRENCY_NAME][configs['name'] == 'stop_loss'].values[0]

    new_sell_price_dist_from_bid_after_stop_loss = \
        configs[CURRENCY_NAME][configs['name'] == 'new_sell_price_dist_from_bid_after_stop_loss'].values[0]

    distance_from_current_price = \
        configs[CURRENCY_NAME][configs['name'] == 'distance_from_current_price'].values[0]

    max_distance_from_current_price_for_buy = \
        configs[CURRENCY_NAME][configs['name'] == 'max_distance_from_current_price_for_buy'].values[0]

    stop_job = configs[CURRENCY_NAME][configs['name'] == 'stop_job'].values[0]
    stop_job = True if stop_job.lower() == 'yes' else False

    send_whats_msg = configs[CURRENCY_NAME][configs['name'] == 'send_whats_msg'].values[0]
    send_whats_msg = True if send_whats_msg.lower() == 'yes' else False

    sleep_seconds = configs[CURRENCY_NAME][configs['name'] == 'sleep_seconds'].values[0]

    result['tp_coefficient'] = tp_coefficient
    result['buy_prices_gap_percent'] = buy_prices_gap_percent
    result['minimum_buy_value'] = minimum_buy_value
    result['stop_loss'] = stop_loss
    result['new_sell_price_dist_from_bid_after_stop_loss'] = new_sell_price_dist_from_bid_after_stop_loss
    result['distance_from_current_price'] = distance_from_current_price
    result['max_distance_from_current_price_for_buy'] = max_distance_from_current_price_for_buy
    result['stop_job'] = stop_job
    result['send_whats_msg'] = send_whats_msg
    result['sleep_seconds'] = sleep_seconds

    return result


def setup_logger():
    log_folder_path = os.path.join(FOLDER_NAME, 'Log')
    if not os.path.exists(log_folder_path):
        os.mkdir(log_folder_path)

    today = datetime.date.today().strftime('%Y-%m-%d')
    today_log_path = os.path.join(log_folder_path, today)
    if not os.path.exists(today_log_path):
        os.mkdir(today_log_path)

    now = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')

    logger = logging.getLogger()
    logger.setLevel(logging.NOTSET)

    h1 = logging.FileHandler(os.path.join(today_log_path, f'DEBUG.log'), mode='a')
    h2 = logging.FileHandler(os.path.join(today_log_path, f'INFO.log'), mode='a')
    h3 = logging.FileHandler(os.path.join(today_log_path, f'WARN.log'), mode='a')
    h4 = logging.FileHandler(os.path.join(today_log_path, f'ERROR.log'), mode='a')
    h5 = logging.FileHandler(os.path.join(today_log_path, f'CRITICAL.log'), mode='a')

    h1.setLevel(logging.DEBUG)
    h2.setLevel(logging.INFO)
    h3.setLevel(logging.WARN)
    h4.setLevel(logging.ERROR)
    h5.setLevel(logging.CRITICAL)

    formatter = logging.Formatter('[%(levelname)s] - [%(asctime)s] -- %(message)s')

    h1.setFormatter(formatter)
    h2.setFormatter(formatter)
    h3.setFormatter(formatter)
    h4.setFormatter(formatter)
    h5.setFormatter(formatter)

    logger.addHandler(h1)
    logger.addHandler(h2)
    logger.addHandler(h3)
    logger.addHandler(h4)
    logger.addHandler(h5)
    return logger


logger = setup_logger()
