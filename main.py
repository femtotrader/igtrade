# -*- coding:utf-8 -*-

# Version 1.17.1 splanquart/falex du 2015 06 29
# Sur base 1.17

# Ajouts fonctionnels / modifications / corrections :
# - Correction du GetDAilyPnL
# - Snake_type des variables

# L3 Scalping
# Import Librairies système
import os
import glob
import time
import logging
import requests
import json
import threading

import wx

# Import modules programme
import igls
import gui_main
import gui_login
import urls
import events
import personal
# Variables global
import globalvar


# definition de la variable d'environnement pour les certificats SSL
# -> à faire pour l'application, à ne pas mettre pour l'utilisation direct
#    dans python
# os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.getcwd(), 'cacert.pem')


def buy(event):
    order(event, "BUY", globalvar.request_deal_size, globalvar.is_force_open,
          globalvar.sl_point, globalvar.tp_point,
          globalvar.is_guaranteed_stop_trading)


def sell(event):
    order(event, "SELL", globalvar.request_deal_size, globalvar.is_force_open,
          globalvar.sl_point, globalvar.tp_point,
          globalvar.is_guaranteed_stop_trading)


def order(event, direction, req_deal_size, is_force_open,
          SLpoint, TPpoint, isStopGuaranteed):
    expiry = '-'
    if req_deal_size < globalvar.min_deal_size:
        globalvar.deal_size_delta = globalvar.min_deal_size - req_deal_size
        req_deal_size = globalvar.min_deal_size
    else:
        globalvar.deal_size_delta = 0
    body = {"currencyCode": globalvar.currency_code, "epic": personal.epic,
            "expiry": expiry, "direction": direction, "size": req_deal_size,
            "forceOpen": is_force_open, "orderType": "MARKET",
            "limitDistance": TPpoint, "stopDistance": SLpoint,
            "guaranteedStop": isStopGuaranteed
            }
    r = requests.post(urls.neworderurl, data=json.dumps(body),
                      headers=urls.fullheaders, proxies=personal.proxies)

    if r.status_code == 200:
        dealReference = r.json().get(u'dealReference')
        print("-- Fonction order ---\n   Ok Code %s" % r.status_code)
        # Debug dans la console, je met en commentaire car le message d'erreur
        # du trade apparait dans la sous-fenêtre OPU###
        # print("-- Fonction order --- Order Ok\n"
        #       "    Code %s\n    Reponse %s" % (r.status_code, r.content))
        # r = requests.get(urls.confirmsurl % dealReference,
        #                  headers=urls.fullheaders, proxies=personal.proxies)
        # if r.status_code == 200:
        #     s = json.loads(r.content)
        #     # print("-- Fonction order --- Confirms Ok\n    Code %s\n"
        #     #       "    URL %s\n    Reponse %s" %
        #     #       (r.status_code, urls.confirmsurl % dealReference,
        #     #        r.content))
        #     print("-- Fonction order --- Confirms Ok\n    Code %s\n"
        #           "    URL %s\n    Status %s\n    Reason %s\n"
        #           "    dealStatus %s" %
        #           (r.status_code, urls.confirmsurl % dealReference,
        #            s.get(u'status'), s.get(u'reason'), s.get(u'dealStatus')))
        # else:
        #     print("--- Fonction order --- Confirms Erreur\n"
        #           "    Erreur Code %s\n    URL %s\n    Reponse %s" %
        #           (r.status_code, urls.confirmsurl % dealReference,
        #            r.content))
    else:
        print("--- Fonction order ---\n"
              "    Erreur Code %s\n"
              "    Body %s\n"
              "    Reponse %s" % (r.status_code, body, r.content))


def calculate_pivots():
    r = requests.get(urls.pricesurl % (personal.epic, 'DAY'),
                     headers=urls.fullheaders, proxies=personal.proxies)
    s = json.loads(r.content).get('prices')[0]

    h = (s.get('highPrice').get('ask') + s.get('highPrice').get('bid')) / 2
    b = (s.get('lowPrice').get('ask') + s.get('lowPrice').get('bid')) / 2
    c = (s.get('closePrice').get('ask') + s.get('closePrice').get('bid')) / 2

    pivot = (h + b + c) / 3
    s1 = (2 * pivot) - h
    s2 = pivot - (h - b)
    s3 = b - 2 * (h - pivot)
    r1 = (2 * pivot) - b
    r2 = pivot + (h - b)
    r3 = h + 2 * (pivot - b)

    return s3, s2, s1, pivot, r1, r2, r3


def polling_markets_details(period=60):
    """Lance la comman de getmarketDetail dans un thread toute les 'period'
    secondes pour mettre à jour les variables de deadling du contrat.

    :param period:
    :return:
    """
    while True:
        (globalvar.min_deal_size, globalvar.currency_code, globalvar.value_of_one_pip,
         globalvar.scaling_factor, globalvar.min_normal_stop_or_limit_distance,
         globalvar.min_controlled_risk_stop_distance) = get_markets_details()
        # DEBUG START
        # globalvar.min_normal_stop_or_limit_distance += random.randint(1,10)
        # print("pollingMarketsDetails %ssecondes %s - minStopNormal=%s - "
        #       "minStopG=%s" % (period, datetime.datetime.now(),
        #                        globalvar.min_normal_stop_or_limit_distance,
        #                        globalvar.min_controlled_risk_stop_distance))
        # DEBUG END
        time.sleep(period)


def get_markets_details():
    """Ajout falex pour récuperation du min_deal_size de l'epic choisi

    :return:
    """
    # print("getMarketDetails URL %s---"%urls.marketsurl % (personal.epic))
    # print("getMarketDetails header %s---"%urls.fullheaders)
    # Utilisation du header Version:2
    # car bug avec Version:1 -> Error 500 {error system},
    # j'ai envoyé un message sur labs.ig.com le 31/05/2015
    r = requests.get(urls.marketsurl % personal.epic,
                     headers=urls.fullheaders_v2, proxies=personal.proxies)
    # print("getMarketDetails r.content %s" % r.content)
    j = json.loads(r.content)

    i = j.get(u'instrument')  # Sous-partie instrument
    value_of_one_pip = float(i.get(u'valueOfOnePip'))
    ic = i.get(u'currencies')  
    # #Ajout 2015 03 09 pour recuperer la monnnais d'échange du sous-jacent
    # currencies_code = ic[0].get(u'name')

    # Correction en version2 'name' devient
    # 'code' la monnnais d'échange du sous-jacent
    currencies_code = ic[0].get(u'code')

    dealing_rules = j.get(u'dealingRules')  # Sous-partie dealingRules
    # print(dR)
    min_deal_size = 0
    dm = dealing_rules.get(u'minDealSize')
    if dm.get(u'unit') == u'POINTS':
        min_deal_size = dm.get(u'value')
    
    min_normal_stop_or_limit_distance = None
    nsd = dealing_rules.get(u'minNormalStopOrLimitDistance')
    # print(nsd)
    if nsd.get(u'unit') == u'POINTS':
        min_normal_stop_or_limit_distance = nsd.get(u'value')
        # print("min_normal_stop_or_limit_distance %s" %
        #       min_normal_stop_or_limit_distance)
         
    min_controlled_risk_stop_distance = None
    csd = dealing_rules.get(u'minControlledRiskStopDistance')
    # print(csd)
    if nsd.get(u'unit') == u'POINTS':
        min_controlled_risk_stop_distance = csd.get(u'value')
        # print("min_controlled_risk_stop_distance %s" %
        #       min_controlled_risk_stop_distance)
         
    s = j.get(u'snapshot')  # Sous-partie snapshot
    scaling_factor = float(s.get(u'scalingFactor'))
    # print("--- Function getMarketsDetails ---  ", min_deal_size,
    #       currencies_code, value_of_one_pip, value_of_one_pip,
    #       min_normal_stop_or_limit_distance, min_controlled_risk_stop_distance)
    # print("--- Function getMarketsDetails ---  ", min_deal_size,
    #       currencies_code, value_of_one_pip, value_of_one_pip)
    # renvoi une valeur en point et la monnaie d'execution, la valeur d'un pip
    return (min_deal_size, currencies_code, value_of_one_pip, scaling_factor,
            min_normal_stop_or_limit_distance,
            min_controlled_risk_stop_distance)


def get_daily_prices():
    url = 'https://%s/gateway/deal/prices/%s/%s/%d' % \
          (urls.ig_host, personal.epic, 'MINUTE', 100000)
    r = requests.get(url, headers=urls.fullheaders, proxies=personal.proxies)
    s = json.loads(r.content)
    import pickle
    with open('Logs/quotesobjectv2.pickle', 'w') as f:
        pickle.dump(s, f)


def on_key_press(event):
    # print(" Fonction Main OnKeyPress ")
    code = event.GetKeyCode()
    if globalvar.is_keyboard_trading:
        # if code == wx.WXK_UP:
        #     print("Up")
        #     events.get_openPositions()
        if code == wx.WXK_CONTROL:
            print("Ctrl/Cmd")
            last_pos_id = globalvar.dict_open_position.keys()[-1]
            last_pos = globalvar.dict_open_position.get(last_pos_id)
            direction = last_pos.get('direction')
            size = globalvar.dict_open_position.get(last_pos_id).get('size')
            # Appel du events-> delete
            events.delete(last_pos_id, direction, size)
        if code == wx.WXK_LEFT:
            print("Left")
            order(event, "SELL", globalvar.request_deal_size,
                  globalvar.is_force_open, globalvar.sl_point, globalvar.tp_point,
                  globalvar.is_guaranteed_stop_trading)
        if code == wx.WXK_RIGHT:
            print("Right")
            order(event, "BUY", globalvar.request_deal_size,
                  globalvar.is_force_open, globalvar.sl_point, globalvar.tp_point,
                  globalvar.is_guaranteed_stop_trading)
        if code == wx.WXK_DOWN:
            print("Down")
            # Appel de la fonction pour fermer tous les ordres ouverts
            # avec une copie du dictionnaire
            close_all()
        """
        if code == wx.WXK_ESCAPE:
            print("Escape")
        if code == wx.WXK_RETURN:
            print("Return")
        """
    event.Skip()
    # print(" Fin ")


def close_all_button(event):
    close_all()


def close_all():
    # print ("--- Fonction CloseAll ---")
    for deal_id_to_delete, v in globalvar.dict_open_position.items():
        direction = v.get('direction')
        size = v.get('size')
        # Appel du events-> delete
        events.delete(deal_id_to_delete, direction, size)
    # print(" Fin ")


def close_all_epic_button(event):
    # print ("--- Fonction Close All epic ---")
    for deal_id_to_delete, v in globalvar.dict_open_position.items():
        if v.get('epic') == personal.epic:
            direction = v.get('direction')
            size = v.get('size')
            # Appel du events-> delete
            events.delete(deal_id_to_delete, direction, size)
    # print("--- Fin Close All epic ---")


def sl_to_zero(event):
    # print("SL to 0 ", personal.epic)
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        if deal.get('epic') == personal.epic:
            o = float(deal.get('open_level'))
            tp = deal.get('limit_level')
            events.update_limit(deal_id, o, tp)


def sl_to_zero_spread(event):
    # print("SL to 0 - spread ", personal.epic)
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        if deal.get('epic') == personal.epic:
            o = float(deal.get('open_level'))
            o = o - (globalvar.spread/globalvar.scaling_factor)
            tp = deal.get('limit_level')
            events.update_limit(deal_id, o, tp)


def tp_to_zero(event):
    # print("TP to 0 - ", personal.epic)
    # print("globalvar.dict_open_position", globalvar.dict_open_position)
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        if deal.get('epic') == personal.epic:
            o = float(deal.get('open_level'))
            sl = deal.get('stop_level')
            events.update_limit(deal_id, sl, o)


def sl_to_pru(event):
    # print("SL to PRU ", personal.epic)
    pru = events.compute_pru(personal.epic)
    # print("PRU = %s" % pru)
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        if deal.get('epic') == personal.epic:
            tp = deal.get('limit_level')
            events.update_limit(deal_id, pru, tp)


def SLtoPRU(event):
    # print("SL to PRU ", personal.epic)
    pru = events.compute_pru(personal.epic)
    # print("PRU = %s" % pru)
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        if deal.get('epic') == personal.epic:
            tp = deal.get('limit_level')
            events.update_limit(deal_id, pru, tp)


def main(event):
    logging_window.on_close()

    # Connecting to IG
    urls.set_urls()
    print("Connecting as %s" % personal.username)
    logger_debug.info("Connecting as %s" % personal.username)
    r = requests.post(urls.sessionurl, data=json.dumps(urls.payload),
                      headers=urls.headers, proxies=personal.proxies)
    if r.status_code != 200:
        print("--- Login Error ---\n"
              "    Erreur Code %s, Reponse %s" % (r.status_code, r.content))
        logger_debug.error("--- Login Error ---\n"
                           "    Erreur Code %s, Reponse %s" %
                           (r.status_code, r.content))
    else:
        print("--- Login Ok ---\n    Code %s" % r.status_code)
        logger_debug.info("--- Login Ok ---\n    Code %s" % r.status_code)

        cst = r.headers.get('cst')
        # X-Security-Token du compte par défaut
        xsecuritytoken = r.headers.get('x-security-token')

        # Création du fullheader pour les prochaines requetes avec Version:2
        urls.fullheaders = {'content-type': 'application/json; charset=UTF-8',
                            'Accept': 'application/json; charset=UTF-8',
                            'version': 1, 'X-IG-API-KEY': personal.api_key,
                            'CST': cst, 'X-SECURITY-TOKEN': xsecuritytoken
                            }

        # Création du fullheader pour les prochaines requetes avec Version:2
        urls.fullheaders_v2 = {
            'content-type': 'application/json; charset=UTF-8',
            'Accept': 'application/json; charset=UTF-8',
            'version': 2, 'X-IG-API-KEY': personal.api_key,
            'CST': cst, 'X-SECURITY-TOKEN': xsecuritytoken
        }

        # Bug chez IG, donc ajout d'un header _method DELETE
        # a defaut de pouvoir utiliser la directive DELETE
        urls.deleteheaders = {'content-type': 'application/json; charset=UTF-8',
                              'Accept': 'application/json; charset=UTF-8',
                              'version': 1,  'X-IG-API-KEY': personal.api_key,
                              'CST': cst, 'X-SECURITY-TOKEN': xsecuritytoken,
                              '_method': 'DELETE'}

        # Bug chez IG, donc ajout d'un header _method DELETE
        # a defaut de pouvoir utiliser la directive DELETE avec Version:2
        urls.deleteheaders_v2 = {
            'content-type': 'application/json; charset=UTF-8',
            'Accept': 'application/json; charset=UTF-8', 'version': 2,
            'X-IG-API-KEY': personal.api_key, 'CST': cst,
            'X-SECURITY-TOKEN': xsecuritytoken, '_method': 'DELETE'
        }
        body = r.json()

        # Recupére l'url d'accès à LS
        lightstreamer_end_point = body.get(u'lightstreamerEndpoint')
        # Récupére le clientId
        client_id = body.get(u'clientId')
        # Récupére l'Id du compte actif
        current_account_id = body.get(u'currentAccountId')
        # récupére le dictionnaire avec les comptes disponibles
        accounts = body.get(u'accounts')

        # Impression de la liste des sous-comptes
        if len(accounts) > 1:
            print("Sous-comptes :")
            for i in accounts:
                print("--> ID: %s - Name: %s - Type:%s - Preferred:%s" %
                      (i.get(u'accountId'), i.get(u'accountName'),
                       i.get(u'accountType'), i.get(u'preferred')))

        # Switching de compte si necessaire
        new_id_account = accounts[int(personal.account_nb)].get(u'accountId')
        if current_account_id != new_id_account:
            # print("Current et compte selectionne sont different, "
            #       "Il faut switch le compte avant de l'utiliser")
            # Il faut switcher le compte
            switching_body = {u'accountId': new_id_account,
                              u'defaultAccount': ''}
            r = requests.put(urls.sessionurl, data=json.dumps(switching_body),
                             headers=urls.fullheaders, proxies=personal.proxies)
            if r.status_code != 200:
                print(" --- Switching Error ---\n    Erreur Code %s" %
                      r.status_code)
                logger_debug.info(" --- Switching Error ---\n"
                                  "    Erreur Code %s" % r.status_code)
            else:
                print("--- Switching Ok ---\n    Vers le compte %s" %
                      accounts[int(personal.account_nb)].get(u'accountId'))
                logger_debug.info("--- Switching Ok ---\n"
                                  "    Vers le compte %s" %
                                  accounts[int(personal.account_nb)].get(u'accountId'))
                # X-Security-Token du compte selectionné
                xsecuritytoken = r.headers.get('x-security-token')
                # MàJ du fullheader pour les prochaines requetes
                urls.fullheaders = {
                    'content-type': 'application/json; charset=UTF-8',
                    'Accept': 'application/json; charset=UTF-8', 'version': 1,
                    'X-IG-API-KEY': personal.api_key, 'CST': cst,
                    'X-SECURITY-TOKEN': xsecuritytoken
                }

        # Depending on how many accounts you have with IG the '0' may need
        # to change to select the correct one (spread bet, CFD account etc)
        # Update with the user account choices.
        account_id = accounts[int(personal.account_nb)].get(u'accountId')
        account_name = accounts[int(personal.account_nb)].get(u'accountName')

        # Connexion LS
        client = igls.LsClient(lightstreamer_end_point + "/lightstreamer/")
        client.on_state.listen(events.on_state)
        client.create_session(username=account_id,
                              password='CST-' + cst + '|XST-' + xsecuritytoken,
                              adapter_set='')

        # Binding sur les differents flux de stream et fonctions associés
        price_table = igls.Table(client,
                                mode=igls.MODE_MERGE,
                                item_ids='MARKET:%s' % personal.epic,
                                schema="OFFER BID",
                                )
        
        price_table.on_update.listen(events.process_price_update)

        # Ajout DEPOSIT pour test
        balance_table = igls.Table(client,
                                  mode=igls.MODE_MERGE,
                                  item_ids='ACCOUNT:' + account_id,
                                  schema='AVAILABLE_CASH PNL DEPOSIT',
                                  )

        balance_table.on_update.listen(events.process_balance_update)

        # Modif falex
        # Je garde uniquement OPU pour avoir
        # les updates de status des positions en cours
        position_table = igls.Table(client,
                                   mode=igls.MODE_DISTINCT,
                                   item_ids='TRADE:' + account_id,
                                   schema='OPU',
                                   )

        position_table.on_update.listen(events.process_position_update)

        # Ajout falex
        # Je ne garde que CONFIRMS
        trade_table = igls.Table(client,
                                mode=igls.MODE_DISTINCT,
                                item_ids='TRADE:' + account_id,
                                schema='CONFIRMS',
                                )

        trade_table.on_update.listen(events.process_trade_update)

        pivots = calculate_pivots()  # Calcul les PP en Daily/formule classique

        # Récupére la taille min d'ouverture d'un ticket et la monnaie d'échange
        (globalvar.min_deal_size, globalvar.currency_code,
         globalvar.value_of_one_pip, globalvar.scaling_factor,
         globalvar.min_normal_stop_or_limit_distance,
         globalvar.min_controlled_risk_stop_distance) = get_markets_details()

        # DEBUG
        # print("Main retour fonction getMarketsDetails ==>>\n    ",
        #       globalvar.min_deal_size, globalvar.currency_code,
        #       globalvar.value_of_one_pip, globalvar.scaling_factor,
        #       globalvar.min_normal_stop_or_limit_distance,
        #       globalvar.min_controlled_risk_stop_distance)
        # globalvar.currency_code = EUR, AUD, USD, GBP, ...
        width = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_X)
        height = wx.SystemSettings.GetMetric(wx.SYS_SCREEN_Y)
        WIN_SIZE = (width/2.6, height/1.3)

        epic_shortname = globalvar.epic_to_shortname_dict.get(personal.epic)
        window = gui_main.Window(None, pivots=pivots,
                                 title='L3 scalping - ' + globalvar.version +
                                       ' - ' + account_id + " - " + account_name +
                                       " - " + epic_shortname,
                                 currencyCode=globalvar.currency_code,
                                 size=WIN_SIZE)
        window.buy_button.Bind(wx.EVT_BUTTON, buy)
        window.sell_button.Bind(wx.EVT_BUTTON, sell)
        window.lot_size.Bind(wx.EVT_TEXT, window.update_size_lot)
        window.sl_point.Bind(wx.EVT_TEXT, window.update_sl_point)
        window.tp_point.Bind(wx.EVT_TEXT, window.update_tp_point)
        window.sl_currency.Bind(wx.EVT_TEXT, window.update_SL_ccy_percentage)
        window.sl_percentage.Bind(wx.EVT_TEXT, window.update_SL_ccy_percentage)
        window.is_force_open_box.Bind(wx.EVT_CHECKBOX, window.update_force_open)

        window.is_keyboard_trading_box.Bind(wx.EVT_CHECKBOX,
                                            window.update_keyboard_trading)
        window.is_auto_stop_to_open_level_box.Bind(wx.EVT_CHECKBOX,
                                                 window.update_auto_stop_to_open_level)
        window.open_positions_list.Bind(wx.EVT_LIST_ITEM_SELECTED,
                                       window.OnClick_openpositionslist)
        # Intercepte l'équivalent du key-down.
        window.panel.Bind(wx.EVT_CHAR_HOOK, on_key_press)
        window.close_all_button.Bind(wx.EVT_BUTTON, close_all_button)
        window.is_guaranteed_stop_trading_box.Bind(wx.EVT_CHECKBOX,
                                                  window.update_guaranteed_stop_trading)
        window.sl_to_zero_button.Bind(wx.EVT_BUTTON, sl_to_zero)
        window.tp_to_zero_button.Bind(wx.EVT_BUTTON, tp_to_zero)
        window.sl_to_pru_button.Bind(wx.EVT_BUTTON, sl_to_pru)
        window.close_all_epic_button.Bind(wx.EVT_BUTTON, close_all_epic_button)
        # Transmet la variable windows au module events sans passer par
        # la directive globale
        events.window = window

        # Charge la liste des positions en stock à l'ouverture du programme
        events.get_open_positions()

        # Ajout Guilux pour afficher le PNL Journalier
        # Calcul du PNL journalier
        (pnl_euro, pnl_points, pnl_points_per_lot, nb_trades) = \
            events.get_daily_pnl()
        window.update_pnl_daily(pnl_euro, pnl_points, pnl_points_per_lot,
                               nb_trades)
        
        # Polling toutes les X secondes des caracteristiques du contrat.
        polling_thread = threading.Thread(target=polling_markets_details,
                                          args=(60,))
        polling_thread.start()
        

if __name__ == '__main__':
    # logueur console
    # on crée un log file par jour uniquement
    base_log_file = os.getcwd() + '//Logs//'
    # today = datetime.datetime.now().strftime('%Y-%m-%d')
    today = time.strftime('%Y-%m-%d')
    log_file = base_log_file + 'Debug-' + str(today) + '.log'
    list_log_files = glob.glob(base_log_file + '*.log')
    if log_file in list_log_files:
        log_file = log_file
    else:
        log_file = base_log_file + 'Debug-' + str(today) + '.log'

    # configuration du logger
    logger_debug = logging.getLogger()
    debug_handler = logging.FileHandler(log_file)
    debug_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    debug_handler.setFormatter(debug_formatter)
    logger_debug.addHandler(debug_handler)
    logger_debug.setLevel(logging.DEBUG)

    # Login Window
    app = wx.App()
    logging_window = gui_login.LogWindow(None, 'L3 scalping V%s - Login' %
                                         globalvar.version)
    logging_window.btn_conn.Bind(wx.EVT_BUTTON, main)
    app.MainLoop()
