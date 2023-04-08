import time
from configs import logger
import requests
import pandas as pd
import json
from configs import *
import numpy as np
from whatsapp import send_msg


def get_orderbook(symbol='all'):
    url = f"https://api.nobitex.ir/v2/orderbook/{symbol}"
    response = requests.request("GET", url)
    return response.json()


def get_best_ask_bid(symbol):
    orderbook = get_orderbook(symbol)
    best_bid = orderbook['bids'][0][0]
    best_ask = orderbook['asks'][0][0]
    return float(best_ask), float(best_bid)


def get_trades(symbol):
    url = "https://api.nobitex.ir/v2/trades"
    payload = {'symbol': symbol}
    response = requests.request("POST", url, data=payload)
    return pd.DataFrame(response.json()['trades'])


def get_market_stats(src, dest='rls'):
    url = "https://api.nobitex.ir/market/stats"
    payload = {'srcCurrency': src,
               'dstCurrency': dest}
    response = requests.request("POST", url, data=payload)
    return response.json()['stats'][f'{src}-{dest}']


def get_orders_list(src, dest='rls', status='all', type=None):
    url = "https://api.nobitex.ir/market/orders/list"
    payload = json.dumps({
        "srcCurrency": src,
        "dstCurrency": dest,
        "details": 2,
        "status": status,
        "type": type
    })
    headers = {
        'Authorization': f'Token {token}',
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 401:
        logger.error('Nobitex did not accept request, probably token has been expired')
        # send_msg('Nobitex did not accept request, probably token has been expired')
    return pd.DataFrame(response.json()['orders'])


def get_order_status(order_id):
    url = "https://api.nobitex.ir/market/orders/status"
    payload = json.dumps({"id": order_id})
    headers = {
        'Authorization': f'Token {token}',
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def get_prices_of_not_closed_buy_positions(buy_orders_list, sell_orders_list, total_actionable_orders):
    try:
        if len(total_actionable_orders) == 0:
            return []
        without_sell_order_buy_ids = total_actionable_orders.loc[
            np.isnan(total_actionable_orders['sell_id']), 'buy_id'].values
        with_sell_order_positions = total_actionable_orders[~np.isnan(total_actionable_orders['sell_id'])]

        not_sold_buy_ids = with_sell_order_positions.loc[with_sell_order_positions['sell_id'].isin(
            sell_orders_list['id'][sell_orders_list['status'] == 'Active']), 'buy_id']

        not_closed_buy_ids = np.concatenate([without_sell_order_buy_ids, not_sold_buy_ids])

        not_closed_buy_prices = buy_orders_list.loc[(buy_orders_list['status'] == 'Active') | (
            buy_orders_list['id'].isin(not_closed_buy_ids)), 'price']

        not_closed_buy_prices = list(map(float, not_closed_buy_prices))
    except AttributeError:
        not_closed_buy_prices = []
    return not_closed_buy_prices


def get_min_max_prices_of_not_closed_buy_positions(buy_orders_list, sell_orders_list, total_actionable_orders):
    min_not_closed_buy_price = None
    max_not_closed_buy_price = None
    try:
        without_sell_order_buy_ids = total_actionable_orders['buy_id'].values[
            np.isnan(total_actionable_orders['sell_id'])]
        with_sell_order_positions = total_actionable_orders[~np.isnan(total_actionable_orders['sell_id'])]

        not_sold_buy_ids = with_sell_order_positions['buy_id'][
            with_sell_order_positions['sell_id'].isin(sell_orders_list['id'][sell_orders_list['status'] == 'Active'])]

        not_closed_buy_ids = np.concatenate([without_sell_order_buy_ids, not_sold_buy_ids])

        min_not_closed_buy_price = float(min(buy_orders_list['price'][
                                                 (buy_orders_list['status'] == 'Active') | (
                                                     buy_orders_list['id'].isin(not_closed_buy_ids))]))
        max_not_closed_buy_price = float(max(buy_orders_list['price'][
                                                 (buy_orders_list['status'] == 'Active') | (
                                                     buy_orders_list['id'].isin(not_closed_buy_ids))]))
    except:
        max_not_closed_buy_price = None
        min_not_closed_buy_price = None
    return min_not_closed_buy_price, max_not_closed_buy_price


def cancel_all_orders(src, dest, execution='market', hours=None):
    url = "https://api.nobitex.ir/market/orders/cancel-old"
    payload = json.dumps({
        "execution": execution,
        "srcCurrency": src,
        "dstCurrency": dest,
        "hours": hours
    })
    headers = {
        'Authorization': f'Token {token}',
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.status_code


def cancel_an_order(order_id):
    url = "https://api.nobitex.ir/market/orders/update-status"
    payload = json.dumps({
        "order": str(order_id),
        "status": "canceled"
    })
    headers = {
        'Authorization': f'Token {token}',
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def buy(src, dest, value, price, execution='limit'):
    url = "https://api.nobitex.ir/market/orders/add"
    volume = value / price
    floor_volume = np.round(volume - 0.5 * 10 ** (-6), 6)
    payload = json.dumps({
        "type": 'buy',
        "srcCurrency": src,
        "dstCurrency": dest,
        "amount": str(floor_volume),
        "price": price,
        "execution": execution
    })
    headers = {
        'Authorization': f'Token {token}',
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def sell(src, dest, volume, price, execution='limit'):
    url = "https://api.nobitex.ir/market/orders/add"
    # volume = value / price
    # floor_volume = np.round(volume - 0.5 * 10 ** (-6), 6)
    payload = json.dumps({
        "type": 'sell',
        "srcCurrency": src,
        "dstCurrency": dest,
        "amount": str(volume),
        "price": price,
        "execution": execution
    })
    headers = {
        'Authorization': f'Token {token}',
        'content-type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=payload)
    return response.json()


def balance(symbol):
    url = "https://api.nobitex.ir/users/wallets/balance"
    payload = {'currency': symbol}
    headers = {'Authorization': f'Token {token}'}
    response = requests.request("POST", url, headers=headers, data=payload)
    return float(response.json()['balance'])


def equities(currency=None):
    url = "https://api.nobitex.ir/users/wallets/list"
    headers = {
        'Authorization': f'Token {token}'
    }
    response = requests.request("POST", url, headers=headers)
    wallets = response.json()['wallets']
    wallets_df = pd.DataFrame(wallets)
    wallets_df['balance'] = wallets_df['balance'].astype(float)
    equities_df = wallets_df.loc[wallets_df['balance'] > 0]
    if currency:
        equities_df = equities_df[equities_df['currency'] == currency]
    return equities_df


def total_estimated_equity(current_price, sell_orders_list, balance_currency, balance_rls):
    with_current_price = int(balance_rls + balance_currency * current_price)
    sell_orders_volume = sum(sell_orders_list['amount'][sell_orders_list['status'] == 'Active'].astype(float))
    sell_orders_value = int(
        sum(sell_orders_list['totalOrderPrice'][sell_orders_list['status'] == 'Active'].astype(float)))
    with_done_sell_orders = int(
        balance_rls + (balance_currency - sell_orders_volume) * current_price + sell_orders_value)
    return {'with_current_price': with_current_price, 'with_done_sell_orders': with_done_sell_orders}


def are_prices_in_range(price_list, order_type, configs):
    alpha_for_sell = configs['stop_loss'] / 100
    alpha_for_buy = configs['max_distance_from_current_price_for_buy'] / 100
    allowed_distance = configs['distance_from_current_price']

    stats = get_market_stats(CURRENCY_NAME)
    best_ask = float(stats['latest'])
    best_bid = float(stats['latest'])
    price_list = np.array(price_list)
    price_list = np.array(list(map(float, price_list)))
    if order_type == 'buy':
        criteria_price = best_ask * (1 - alpha_for_buy)
        criteria_price_2 = best_ask * (1 - allowed_distance)
        validity = (criteria_price_2 - price_list) * (price_list - criteria_price)
    elif order_type == 'sell':
        criteria_price = best_bid * (1 + alpha_for_sell)
        validity = (price_list - best_bid) * (criteria_price - price_list)
    return validity >= 0


def open_new_pending_position(prices_of_not_closed_buy_positions=None, symbol=None, src=None, dest=None, configs=None):
    def _calculate_buy_price(prices_of_not_closed_buy_positions, configs):
        orderbook = get_orderbook(symbol)
        asks = orderbook['asks']
        best_ask = float(asks[0][0])
        if not prices_of_not_closed_buy_positions:
            new_buy_price = (1 - configs['distance_from_current_price'] / 100) * best_ask
        else:
            prices_of_not_closed_buy_positions = np.array(prices_of_not_closed_buy_positions)
            candidate_buy_price = (1 - configs['distance_from_current_price'] / 100) * best_ask
            next_try = True
            while next_try:
                min_distance_from_positions = np.nanmin(
                    np.abs(prices_of_not_closed_buy_positions / candidate_buy_price - 1))
                if 100 * min_distance_from_positions >= configs['buy_prices_gap_percent']:
                    new_buy_price = candidate_buy_price
                    break
                else:
                    if all((prices_of_not_closed_buy_positions >= candidate_buy_price) | (
                            prices_of_not_closed_buy_positions < candidate_buy_price * (
                            1 - configs['buy_prices_gap_percent'] / 100))):
                        upper_bound_price = np.nanmin(prices_of_not_closed_buy_positions[
                                                          prices_of_not_closed_buy_positions >= candidate_buy_price])
                        candidate_buy_price = upper_bound_price * (1 - configs['buy_prices_gap_percent'] / 100)
                    else:
                        lower_bound_price = np.nanmax(prices_of_not_closed_buy_positions[
                                                          prices_of_not_closed_buy_positions < candidate_buy_price])
                        candidate_buy_price = lower_bound_price * (1 - configs['buy_prices_gap_percent'] / 100)
        if ~are_prices_in_range([new_buy_price], 'buy', configs)[0]:
            new_buy_price = -1
        return new_buy_price

    def _get_active_cash():
        all_equities = equities()
        active_cash = all_equities.loc[all_equities['currency'] == 'rls', 'activeBalance']
        return float(active_cash)

    buy_value = configs['minimum_buy_value'] + np.random.randint(1, 99, 1)[0] * 10000

    active_cash = _get_active_cash()
    if active_cash > buy_value:
        new_buy_price = _calculate_buy_price(prices_of_not_closed_buy_positions, configs)
        response = buy(src, dest, buy_value, new_buy_price, 'limit')
        return response
    return {'status': 'failed'}


def save_new_buy_order_to_total_actionable_orders(response, total_actionable_orders):
    if response['status'] == 'ok':
        order = response['order']
        new_record = {'buy_id': int(order['id']), 'buy_amount': order['amount'], 'buy_price': order['price']}
        total_actionable_orders = pd.concat([total_actionable_orders, pd.DataFrame([new_record])])
    return total_actionable_orders


def save_new_sell_order_to_total_actionable_orders(response, total_actionable_orders, buy_id=None):
    if response['status'] == 'ok':
        order = response['order']
        row_index = total_actionable_orders['buy_id'] == buy_id
        total_actionable_orders.loc[row_index, 'sell_id'] = int(order['id'])
        total_actionable_orders.loc[row_index, 'sell_amount'] = order['amount']
        total_actionable_orders.loc[row_index, 'sell_price'] = order['price']
    return total_actionable_orders


def sell_remaining_equities(src, symbol, total_actionable_orders, buy_orders_list, configs):
    def _refine_sell_price(sell_price, alpha, stop_loss, best_ask, best_bid):
        best_bid = float(best_bid)
        if sell_price <= best_bid:
            return best_bid
        if sell_price > best_bid * (1 + stop_loss):
            return best_bid * (1 + alpha)
        return sell_price

    if any(pd.isnull(total_actionable_orders['sell_id'])):
        best_ask, best_bid = get_best_ask_bid(symbol)
        alpha = configs['new_sell_price_dist_from_bid_after_stop_loss'] / 100
        stop_loss = configs['stop_loss'] / 100

        total_actionable_orders['refined_sell_price'] = total_actionable_orders['buy_price'].astype(float) * configs[
            'tp_coefficient']
        total_actionable_orders['refined_sell_price'] = total_actionable_orders['refined_sell_price'].astype(int)
        total_actionable_orders['refined_sell_price'] = total_actionable_orders['refined_sell_price'] \
            .apply(lambda x: _refine_sell_price(x, alpha, stop_loss, best_ask, best_bid))
        total_actionable_orders.sort_values('refined_sell_price', inplace=True)

        for buy_id in total_actionable_orders.loc[pd.isnull(total_actionable_orders['sell_id']), 'buy_id']:
            if buy_id in buy_orders_list['id'].values:
                if buy_orders_list.loc[buy_orders_list['id'] == buy_id, 'status'].iloc[0] == 'Done':
                    buy_price = total_actionable_orders.loc[total_actionable_orders['buy_id'] == buy_id, 'buy_price']
                    sell_price = int(float(buy_price) * configs['tp_coefficient'])
                    sell_price = _refine_sell_price(sell_price, alpha, stop_loss, best_ask, best_bid)
                    sell_volume = total_actionable_orders.loc[total_actionable_orders['buy_id'] == buy_id, 'buy_amount']
                    equity_for_sale = equities(src)['activeBalance'].iloc[0]
                    sell_volume = max(float(sell_volume), configs['minimum_buy_value'] / sell_price)
                    sell_volume = min(float(sell_volume), float(equity_for_sale))
                    response = sell(src, 'rls', sell_volume, sell_price, 'limit')
                    return response, buy_id
    return {'status': 'failed'}, None


def was_transaction_successful(response):
    if not response:
        return False
    elif response['status'] == 'ok':
        order_id = response['order']['id']
        order_type = response['order']['type']
        orders_list = get_orders_list(src=CURRENCY_NAME, type=order_type)
        time.sleep(10)
        if order_id in orders_list['id'].values:
            return True
        else:
            logger.critical(
                f'ATTENTION: we have a response with status = ok BUT order_id in not in orders list, order id = {order_id}')
            return False
    return False


def cancel_pending_positions(total_actionable_orders, buy_orders_list, sell_orders_list, msg, configs):
    active_buy_orders = buy_orders_list[(buy_orders_list['status'] == 'Active') & (~buy_orders_list['partial'])]
    active_sell_orders = sell_orders_list[(sell_orders_list['status'] == 'Active') & (~sell_orders_list['partial'])]

    def _get_not_tracking_position_ids():
        not_tracking_buy_ids = active_buy_orders.loc[
            ~active_buy_orders['id'].isin(total_actionable_orders['buy_id']), 'id']
        not_tracking_sell_ids = active_sell_orders.loc[
            ~active_sell_orders['id'].isin(total_actionable_orders['sell_id']), 'id']
        not_tracking_ids = pd.concat([not_tracking_sell_ids, not_tracking_buy_ids])
        return not_tracking_ids

    def _get_out_of_range_pending_positions_ids(configs):

        out_of_range_buy_ids = []
        if len(active_buy_orders) > 0:
            out_of_range_buy_ids = active_buy_orders.loc[
                ~are_prices_in_range(active_buy_orders['price'].astype(float), 'buy', configs), 'id']

        out_of_range_sell_ids = []
        if len(active_sell_orders) > 0:
            out_of_range_sell_ids = active_sell_orders.loc[
                ~are_prices_in_range(active_sell_orders['price'].astype(float), 'sell', configs), 'id']

        out_of_range_ids = np.concatenate([out_of_range_buy_ids, out_of_range_sell_ids])
        return out_of_range_ids

    not_tracking_ids = _get_not_tracking_position_ids()
    out_of_range_ids = _get_out_of_range_pending_positions_ids(configs)
    ids_for_cancel = np.concatenate([out_of_range_ids, not_tracking_ids])
    if len(ids_for_cancel) > 0:

        for id in ids_for_cancel:
            id = int(id)
            response = cancel_an_order(id)
            if response['status'] == 'ok':
                logger.warning(f'order with id = {id} cancelled')
                msg = msg + f'\n order with id = {id} cancelled'
                if id in total_actionable_orders['buy_id'].values:
                    total_actionable_orders = total_actionable_orders[total_actionable_orders['buy_id'] != id]
                elif id in total_actionable_orders['sell_id'].values:
                    total_actionable_orders.loc[total_actionable_orders['sell_id'] == id, 'sell_amount'] = None
                    total_actionable_orders.loc[total_actionable_orders['sell_id'] == id, 'sell_price'] = None
                    total_actionable_orders.loc[total_actionable_orders['sell_id'] == id, 'sell_id'] = None
            total_actionable_orders.to_csv(os.path.join(files_folder_path, 'total_actionable_orders.csv'), index=False)
    return msg


def update_total_actionable_orders(total_actionable_orders, buy_orders_list, sell_orders_list):
    if len(total_actionable_orders) > 0:
        total_actionable_orders = total_actionable_orders[total_actionable_orders['buy_id'].isin(buy_orders_list['id'])]

        done_buy_ids = []
        if len(buy_orders_list) > 0:
            canceled_buy_ids = buy_orders_list.loc[buy_orders_list['status'] == 'Canceled', 'id']
            total_actionable_orders = total_actionable_orders[~total_actionable_orders['buy_id'].isin(canceled_buy_ids)]

            done_buy_ids = buy_orders_list.loc[buy_orders_list['status'] == 'Done', 'id']
        done_sell_ids = []
        if len(sell_orders_list) > 0:
            canceled_sell_ids = sell_orders_list.loc[sell_orders_list['status'] == 'Canceled', 'id']
            total_actionable_orders.loc[
                total_actionable_orders['sell_id'].isin(canceled_sell_ids), 'sell_amount'] = None
            total_actionable_orders.loc[total_actionable_orders['sell_id'].isin(canceled_sell_ids), 'sell_price'] = None
            total_actionable_orders.loc[total_actionable_orders['sell_id'].isin(canceled_sell_ids), 'sell_id'] = None

            done_sell_ids = sell_orders_list.loc[sell_orders_list['status'] == 'Done', 'id']

        total_actionable_orders = total_actionable_orders[~((total_actionable_orders['buy_id'].isin(done_buy_ids)) & (
            total_actionable_orders['sell_id'].isin(done_sell_ids)))]
        total_actionable_orders.to_csv(os.path.join(files_folder_path, 'total_actionable_orders.csv'), index=False)
    return total_actionable_orders
