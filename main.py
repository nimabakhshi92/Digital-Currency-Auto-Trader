import pandas as pd
import pywhatkit
from functions import *
from whatsapp import send_msg
from configs import *
import datetime
import time

logger.info('Program started')
counter = 1
max_iteration = 1
msg = ''
while counter <= max_iteration:
    logger.info(f'Come into the while loop, counter = {counter}')
    try:
        logger.debug(f'Read configs, counter = {counter}')
        configs = get_configs()
        if configs['stop_job']:
            break

        logger.info(f'Update actionable orders, counter = {counter}')
        buy_orders_list = get_orders_list(CURRENCY_NAME, type='buy')
        sell_orders_list = get_orders_list(CURRENCY_NAME, type='sell')
        total_actionable_orders = update_total_actionable_orders(total_actionable_orders, buy_orders_list,
                                                                 sell_orders_list)
        time.sleep(5)

        # min_not_closed_buy_price, max_not_closed_buy_price = get_min_max_prices_of_not_closed_buy_positions(
        #     buy_orders_list,
        #     sell_orders_list,
        #     total_actionable_orders)

        logger.info(f'Open new pending position, counter = {counter}')
        prices_of_not_closed_buy_positions = get_prices_of_not_closed_buy_positions(buy_orders_list, sell_orders_list,
                                                                                    total_actionable_orders)
        response = open_new_pending_position(prices_of_not_closed_buy_positions, symbol=CURRENCY_SYMBOL,
                                             src=CURRENCY_NAME,
                                             dest='rls',
                                             configs=configs)
        if was_transaction_successful(response):
            last_buy_price = float(response['order']['price'])
            logger.warning(
                f'buy order accepted. order_id = {response["order"]["id"]},'
                f' order_amount = {response["order"]["amount"]},'
                f' order_price = {response["order"]["price"]}'
            )
            msg = msg + f'\n a buy order placed at price: {last_buy_price}'
            total_actionable_orders = save_new_buy_order_to_total_actionable_orders(response, total_actionable_orders)
            total_actionable_orders.to_csv(os.path.join(files_folder_path, 'total_actionable_orders.csv'), index=False)
        else:
            print('\n no more buy orders placed')

        time.sleep(5)

        logger.info(f'Update actionable orders, counter = {counter}')
        buy_orders_list = get_orders_list(CURRENCY_NAME, type='buy')
        sell_orders_list = get_orders_list(CURRENCY_NAME, type='sell')
        total_actionable_orders = update_total_actionable_orders(total_actionable_orders, buy_orders_list,
                                                                 sell_orders_list)

        logger.info(f'Sell remaining equities, counter = {counter}')
        response, buy_id = sell_remaining_equities(CURRENCY_NAME, CURRENCY_SYMBOL, total_actionable_orders,
                                                   buy_orders_list, configs)
        if was_transaction_successful(response):
            last_sell_price = float(response['order']['price'])
            buy_price = float(buy_orders_list.loc[buy_orders_list['id'] == buy_id, 'price'])
            logger.warning(
                f'sell order accepted. order_id = {response["order"]["id"]}, '
                f'order_amount = {response["order"]["amount"]}, '
                f'order_price = {response["order"]["price"]}, '
                f'equivalent buy price = {buy_price}'
            )
            msg = msg + f'\n a sell order placed at price: {last_sell_price}, due to a buy transaction at price {buy_price}'
            total_actionable_orders = save_new_sell_order_to_total_actionable_orders(response, total_actionable_orders,
                                                                                     buy_id)
            total_actionable_orders.to_csv(os.path.join(files_folder_path, 'total_actionable_orders.csv'), index=False)
        else:
            print('\n no more sell orders placed')

        time.sleep(5)
        logger.info(f'Update actionable orders, counter = {counter}')
        buy_orders_list = get_orders_list(CURRENCY_NAME, type='buy')
        sell_orders_list = get_orders_list(CURRENCY_NAME, type='sell')
        total_actionable_orders = update_total_actionable_orders(total_actionable_orders, buy_orders_list,
                                                                 sell_orders_list)
        logger.info(f'Cancel pending positions, counter = {counter}')
        new_msg = cancel_pending_positions(total_actionable_orders, buy_orders_list, sell_orders_list, msg, configs)
        if new_msg is not None:
            msg = new_msg

        logger.info(f'Reporting, counter = {counter}')
        currency = balance(CURRENCY_NAME)
        rls = int(float(balance('rls')))
        current_price = int(get_market_stats(CURRENCY_NAME)['latest'])
        sell_orders_list = get_orders_list(CURRENCY_NAME, type='sell')
        our_estimated_equity = total_estimated_equity(current_price, sell_orders_list, currency, rls)
        if msg != '':
            msg = msg + f'\nbalance summary: \nCurrency: {currency}  {CURRENCY_NAME}\nCash: {rls} rial' \
                        f'\ntotal estimated equity: \n' \
                        f'with current price : {our_estimated_equity["with_current_price"]} rial' \
                        f'\nwith done sell orders : {our_estimated_equity["with_done_sell_orders"]} rial'
            if configs['send_whats_msg']:
                send_msg(msg)
            msg = ''

        time.sleep(5)

        logger.info(f'Update actionable orders, counter = {counter}')
        buy_orders_list = get_orders_list(CURRENCY_NAME, type='buy')
        sell_orders_list = get_orders_list(CURRENCY_NAME, type='sell')
        total_actionable_orders = update_total_actionable_orders(total_actionable_orders, buy_orders_list,
                                                                 sell_orders_list)

    except Exception as e:
        print(e)
    logger.info(f'Sleep for next iteration, counter = {counter}')
    t = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"sleeping {configs['sleep_seconds']} seconds, time = {t}")
    time.sleep(configs['sleep_seconds'])
    counter = counter + 1
