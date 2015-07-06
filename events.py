# -*- coding:utf-8 -*-

import json
import time

import requests

import urls
import personal

# Variables global
import globalvar

# Logger
# logger = logging.getLogger("quotes")
# hdlr = logging.FileHandler('Logs/quotes-' + time.strftime("%d-%M-%Y") + '.log')
# formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
# hdlr.setFormatter(formatter)
# logger.addHandler(hdlr)
# logger.setLevel(logging.INFO)


def on_state(state):
    """Tell the user when the Lighstreamer connection state changes

    :param state:
    :return:
    """
    print state


def process_price_update(item, my_update_field):
    """Process à lighstreamer price update

    :param item:
    :param my_update_field:
    :return:
    """
    # Mise en sommeil du logger de flux LS
    # logger.info(str(my_update_field))

    bid, ask = my_update_field
    sum_point = 0
    point_profit = 0
    # calcul du pnl pour chaque pos de l'epic actif
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        # on récupère l'epic
        epic = deal.get('epic')
        # on récupère le sens pour chaque pos
        direction = deal.get('direction')
        # on récupère l'open pour chaque pos
        open_level = deal.get('open_level')
        # on récupère le TP pour chaque pos
        tp = deal.get('limit_level')
        # on récupère le SL pour chaque pos
        sl = deal.get('stop_level')
        # on récupère la size pour chaque pos
        size = deal.get('size')
        # on récupère un T/F indiquant si la position est en stop garantie
        guaranteed_stop = deal.get('guaranteedStop')

        # calcul pnl en points de chaque position
        # Exclusion des lignes qui ne sont pas dans bon epic
        #  +
        # Move du stop level si la distance avec l'open level est suffisante.
        # TODO: Optim : Faire 2 fonctions distinctes.
        if epic == personal.epic:
            if direction == 'BUY':
                distance_to = ((float(ask) - float(open_level))
                               * globalvar.scaling_factor)
            elif direction == 'SELL':
                distance_to = ((float(open_level) - float(bid))
                               * globalvar.scaling_factor)
                
            pos_pnl_per_lot = round(distance_to, 1)
            pos_pnl = round(distance_to * float(size), 1)
            sum_point += pos_pnl
            # print("deal_id,pos_pnl_per_lot, pos_pnl, size, distance_to",
            #       deal_id, pos_pnl_per_lot, pos_pnl, size, distance_to,
            #       sum_point)
            
            if globalvar.is_auto_stop_to_open_level:
                if guaranteed_stop :
                    # print(" guaranteed_stop", deal_id)
                    stop_min_distance = globalvar.min_controlled_risk_stop_distance
                else:
                    # print(" NOT guaranteed_stop", deal_id)
                    stop_min_distance = globalvar.min_normal_stop_or_limit_distance
                             
                if (((direction == 'BUY' and (sl < open_level or sl is None))
                      or 
                        (direction == 'SELL' and (sl > open_level or sl is None) )
                    ) and distance_to >= stop_min_distance):
                    print("processPriceUpdate:"
                          "try to move the stop to the open level",
                          sl, open_level)
                    update_limit(deal_id, open_level, tp)
        else:
            pos_pnl_per_lot = 'N/A'
            pos_pnl = 'N/A'
            
        globalvar.dict_open_position[deal_id]['pnl'] = pos_pnl
        globalvar.dict_open_position[deal_id]['pnlperlot'] = pos_pnl_per_lot
        
        # print("deal_id, float(open_level)", deal_id, float(open_level))
        # print("pos_pnl_per_lot",pos_pnl_per_lot)
        # print("pos_pnl", pos_pnl)
                              
    # print("Après la boucle For du dico de position")

    window.update_price(bid, ask, sum_point)


def process_balance_update(item, my_update_field):
    """Process an update of the users trading account balance

    :param item:
    :param my_update_field:
    :return:
    """
    # print("--- processBalanceUpdate ---")
    # print(my_update_field)
    globalvar.balance, pnl, globalvar.deposit = my_update_field
    # Deplacement du code qui compte le nb de pos
    # et la taille agregee des lots pour l'epic donne dans processPositionUpdate
    # Ajout deposit
    window.update_balance(globalvar.balance, pnl, globalvar.deposit)


def process_position_update(item, my_update_field):
    """Process an update when an OPU message occured

    :param item:
    :param my_update_field:
    :return:
    """
    # Fonction appelé sur reception d'un LS OPU #_#
    # print("--- processPositionUpdate ----")

    # DEBUG
    # print("    message OPU : \n    %s"%my_update_field)
    # print ("Type %s"%type(my_update_field))

    if my_update_field[0] is not None:
        # maroxe + falex
        opu = next(json.loads(field) for field in my_update_field
                   if field is not None)
        opu_ordo = [opu.get(u'status'), opu.get(u'direction'), opu.get(u'size'),
                    opu.get(u'level'), opu.get(u'limitLevel'),
                    opu.get(u'stopLevel'), opu.get(u'guaranteedStop'),
                    opu.get(u'limitDistance'), opu.get(u'stopDistance'),
                    opu.get(u'dealStatus'), opu.get(u'dealId'),
                    opu.get(u'reason'), opu.get(u'epic'), opu.get(u'expiry'),
                    opu.get(u'affectedDeals'), opu.get(u'dealReference')]
        # Envoi des evenements OPU dans la sous fenêtre OPU
        window.add_opu_message(opu_ordo)

        # Trois messages 'status' à gérer :
        # 'OPEN' = Ouverture d'un nouveau ticket :
        #     Size = taille de l'ouverture
        # 'DELETED' = Fermeture d'un ticket existant :
        #     Size = Taille restante du ticket avant de tomber à Zéro.
        #     Message deleted = le ticket est complétement fermé
        #                       il n'en reste plus rien.
        # 'UPDATED' = MaJ du ticket (taille, SL, TP, trailling) :
        #     Size = Nouvelle taille du ticket avec ce qui reste.
        deal_id = opu.get(u'dealId')
        if opu.get('status') == u'OPEN':
            # print("Ouverture position")
            # open_values = [opu.get(u'epic'), opu.get(u'size'),
            #                opu.get(u'direction'), opu.get(u'level'),
            #                opu.get(u'limitLevel'), opu.get(u'stopLevel')]
            # MàJ avec la v2 du dico
            open_values = {'epic': opu.get(u'epic'),
                           'size': opu.get(u'size'),
                           'direction': opu.get(u'direction'),
                           'open_level': opu.get(u'level'),
                           'limit_level': opu.get(u'limitLevel'),
                           'stop_level': opu.get(u'stopLevel'),
                           'guaranteedStop': opu.get(u'guaranteedStop'),
                           'pnlperlot': 'N/A',
                           'pnl': 'N/A'
                           }
            # Enregistrement de la position dans le dico
            globalvar.dict_open_position.update({deal_id: open_values})
            # Envoi le dictionnaire à afficher
            window.set_open_positions(globalvar.dict_open_position)
            pru = compute_pru(personal.epic)
            window.update_pru(pru)
            update_count_ticket()
        elif opu.get('status') == u'DELETED':
            # print("Fermeture position")
            try:
                del globalvar.dict_open_position[deal_id]
            except KeyError:
                print("Erreur MaJ dico positions ouvertes")
                pass
            # print(globalvar.dict_open_position)
            # Envoi le dictionnaire à afficher
            window.set_open_positions(globalvar.dict_open_position)
            pru = compute_pru(personal.epic)
            window.update_pru(pru)
            update_count_ticket()

            # Guilux modif pouir afficher le PNL Journalier
            # Calcul du PNL journalier
            pnl_euro, pnl_points, pnl_points_per_lot, nb_trades = get_daily_pnl()
            window.update_pnl_daily(pnl_euro, pnl_points,
                                   pnl_points_per_lot, nb_trades)

        elif opu.get('status') == u'UPDATED':
            # print("Mise a jour ticket")
            # udpate_values = [opu.get(u'epic'), opu.get(u'size'),
            #                  opu.get(u'direction'), opu.get(u'level'),
            #                  opu.get(u'limitLevel'), opu.get(u'stopLevel')]
            # MàJ avec la v2 du dico
            udpate_values = {'epic': opu.get(u'epic'), 'size': opu.get(u'size'),
                             'direction': opu.get(u'direction'),
                             'open_level': opu.get(u'level'),
                             'limit_level': opu.get(u'limitLevel'),
                             'stop_level': opu.get(u'stopLevel'),
                             'guaranteedStop': opu.get(u'guaranteedStop'),
                             'pnlperlot': 'N/A',
                             'pnl': 'N/A'
                             }
            # MàJ du dico
            globalvar.dict_open_position[deal_id] = udpate_values
            # print(globalvar.dict_open_position)
            # Envoi le dictionnaire à afficher
            window.set_open_positions(globalvar.dict_open_position)
            pru = compute_pru(personal.epic)
            window.update_pru(pru)
            update_count_ticket()
            
            # Guilux modif pouir afficher le PNL Journalier
            # Calcul du PNL journalier
            (pnl_euro, pnl_points, pnl_points_per_lot, nb_trades) \
                = get_daily_pnl()
            window.update_pnl_daily(pnl_euro, pnl_points,
                                   pnl_points_per_lot, nb_trades)

        else:
            print("Autre status non gere : %s", opu.get('status'))
    # else:
    #     print("   message OPU = None ou vide")
    # print ("---Fin---")


def update_count_ticket():
    # print("--- update_countTicket ---")
    # V1.14.2 :
    # - Correction en mode calcul local pour ne pas génére
    #   de requete REST "inutile" en cas de trop nombreux message
    # Externalisation de la fonction
    # Déplacement de cette requete, dans PositionUpdate
    #   sinon je genere trop de requete /position
    #   (et ca ne sert a rien en dehors des modifications)
    # r = requests.get(urls.positionsurl,
    #                  headers=urls.fullheaders,
    #                  proxies=personal.proxies)
    # s = json.loads(r.content).get("positions")
    # Ajout Falex pour l'epic en cours
    #   je somme la taille des positions Sell et Buy
    size_to_buy = 0
    size_to_sell = 0
    nb_ticket = 0
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        # on récupère l'epic pour chaque pos
        epic = deal.get('epic')
        # on récupère le sens pour chaque pos
        direction = deal.get('direction')
        # on récupère la taille pour chaque pos
        size = deal.get('size')
        # d = p.get("position").get("direction")
        # s = p.get("position").get("dealSize")
        # e = p.get("market").get("epic")
        if epic == personal.epic:
            if direction == "BUY":
                size_to_buy += size
                nb_ticket += 1
            elif direction == "SELL":
                size_to_sell += size
                nb_ticket += 1
    window.update_pos(nb_ticket, size_to_buy, size_to_sell)
    # print ("---Fin---")


def process_trade_update(item, my_update_field):
    """
    Add by falex
    :param item:
    :param my_update_field:
    :return:
    """
    # Fonction appelé sur reception d'un LS CONFIRMS #_#
    # DEBUG
    # print("--- processTradeUpdate ---")
    # print("globalvar.deal_size_delta = ",globalvar.deal_size_delta)
    # print("my_update_field ==>>> ",my_update_field)

    if my_update_field[0] is not None:
        # DEBUG
        # print("my_update_field ==>>>", my_update_field)
        message = next(json.loads(field)
                       for field in my_update_field if field is not None)
        direction = message.get(u'direction')
        # status = message.get(u'status')
        # dealId = message.get(u'dealId')
        # dealReference = message.get(u'dealReference')
        deal_status = message.get(u'dealStatus')
        reason = message.get(u'reason')
        # if message.get(u'affectedDeals') != None:
        if deal_status == u'ACCEPTED':
            # Suppression d'un bout de ticket
            # si la taille demandé est inférieur à la taille min du contrat
            for f in message.get(u'affectedDeals'):
                aff_deals_id = f.get(u'dealId')
                aff_status = f.get(u'status')
                # if (aff_deals_id == dealId and aff_status == u'OPENED' and
                #             globalvar.deal_size_delta > 0):
                #     # Jusqu'à présent dealId et AffDealsId
                #     # avaient la même référence à l'ouverture.
                if (aff_status == u'OPENED' and globalvar.deal_size_delta > 0):
                # Modification des conditions d'entrée
                # si status OPENED et globalvar.deal_size_delta > 0
                    # DEBUG
                    # print("Je sort %s de la position" %
                    #       globalvar.deal_size_delta)

                    # UPDATE avec le affected Deal Id
                    body = {"dealId": aff_deals_id,
                            "direction": "SELL",
                            "size": globalvar.deal_size_delta,
                            "orderType": "MARKET"
                            }
                    # ajustement de la direction dans l'ordre DELETE
                    # en fonction du sens d'ouverture
                    if direction == "SELL":
                        body['direction'] = "BUY"
                    # DEBUG
                    # print("data ", body)
                    # print("headers ", urls.deleteheaders)
                    r = requests.post(urls.closeorderurl,
                                      data=json.dumps(body),
                                      headers=urls.deleteheaders,
                                      proxies=personal.proxies)
        else:
            # Problème dans l'ordre, création d'un dictionnaire similaire à OPU
            # pour l'nevoyer à l'affichage dans le fenêrte d'évenemnt
            opu_ordo = [deal_status, reason]
            # Envoi des evenements OPU dans la sous fenêtre OPU
            window.add_opu_message(opu_ordo)
        # print("Post DELETE Status code -> ", r.status_code)
    # print("----Fin----")


def get_open_positions():
    """Process the set the openposition from an empty list,
    the number of tick and aggregate lot for the current epic

    :return:
    """
    # print("--- get_openPositions ---")

    r = requests.get(urls.positionsurl, headers=urls.fullheaders,
                     proxies=personal.proxies)
    s = json.loads(r.content).get("positions")
    print("--- get_openPositions ---\n    Code %s" % r.status_code)
    globalvar.dict_open_position = {}  # Ajout 1.14.2
    size_to_buy = 0
    size_to_sell = 0
    nb_ticket = 0
    for p in s:
        # DealID
        deal_id = p.get("position").get("dealId")
        # Sens
        d = p.get("position").get("direction")
        # Taille du contrat
        s = p.get("position").get("dealSize")
        # Cours d'ouverture
        ol = p.get("position").get("openLevel")
        # SL
        sl = p.get("position").get("stopLevel")
        # TP
        ll = p.get("position").get("limitLevel")
        # sous-jacent
        e = p.get("market").get("epic")
        # Stop Garantie
        guaranteed_stop = p.get("position").get("controlledRisk")
        if e == personal.epic:
            if d == "BUY":
                size_to_buy += s
                nb_ticket += 1
            elif d == "SELL":
                size_to_sell += s
                nb_ticket += 1
        # Ajout position dans le dictionnaire
        # "dealdId":[epic, size, direction, openLevel, TP, SL]`
        # globalvar.dict_open_position.update({deal_id:[e,s, d, ol, ll, sl]})
        # MàJ avec la v2 du dico
        new_deal = {"epic": e,
                    "size": s,
                    "direction": d,
                    "open_level": ol,
                    "limit_level": ll,
                    "stop_level": sl,
                    "guaranteedStop": guaranteed_stop,
                    "pnlperlot": 'N/A',
                    "pnl": 'N/A'}
        globalvar.dict_open_position.update({deal_id: new_deal})
    window.update_pos(nb_ticket, size_to_buy, size_to_sell)
    # print("Envoi de =>>>>>>>>>> ", globalvar.dict_open_position)
    window.set_open_positions(globalvar.dict_open_position)  # Ok
    pru = compute_pru(personal.epic)
    window.update_pru(pru)
    # print ("---Fin---")


def delete(deal_id, direction, req_deal_size):
    """Process de suppresion d'un ticket en fonction de :
     - son deal_id
     - sa direction
     - et sa taille.

    :param deal_id:
    :param direction:
    :param req_deal_size:
    :return:
    """
    # print("--- events.delete ---")
    print("Ticket %s a supprimer" % deal_id)

    body = {"dealId": deal_id,
            "direction": "SELL",
            "size": req_deal_size,
            "orderType": "MARKET"
            }
    # print(body)
    if direction == "SELL":
        # ajustement de la direction dans l'ordre DELETE
        # en fonction du sens d'ouverture
        body['direction'] = "BUY"

    r = requests.post(urls.closeorderurl, data=json.dumps(body),
                      headers=urls.deleteheaders, proxies=personal.proxies)

    print("--- delete ---\n    Code %s" % r.status_code)
    if r.status_code != 200:
        # Si message d'erreur alors
        # on force le refresh des positions en local avec une R REST
        get_open_positions()
    # print("--- FIN : Events.delete ---")


def update_limit(deal_id, sl_level, tp_level):
    """

    :param deal_id:
    :param sl_level: Stop Loss level
    :param tp_level: Take Profit level
    :return:
    """
    # DEBUG
    print(" --- updateLimit ---")
    print("Ticket %s a updater SL = %s TP = %s" % (deal_id, sl_level, tp_level))
    body = {"limitLevel": tp_level, "stopLevel": sl_level}
    r = requests.put(urls.updateorderurl % deal_id, data=json.dumps(body),
                     headers=urls.fullheaders, proxies=personal.proxies)
    print("--- updateLimit ---\n    Code %s" % r.status_code)
    # print("--- FIN : Events.updateLimit ---")


def compute_pru(epic):
    """calcul du Prix de Revient Unitaire (PRU)
    about: fonction que j'ai du mettre ici pour pouvoir l'utiliser
           dans main et events.
    :param epic:
    :return: PRU value
    """
    pru = 0
    size = 0
    for deal_id in globalvar.dict_open_position:
        deal = globalvar.dict_open_position.get(deal_id)
        if deal.get('epic') == epic:
            o = float(deal.get('open_level'))
            s = deal.get('size')
            pru += (o * s)
            size = size + s
    try:
        pru = round(float(pru/size), 5)  # Arrondi à 5 décimales
    except ZeroDivisionError:
        pru = None
    return pru


def get_daily_pnl():
    """Retourne le PNL en Euro, en points et le nombre de trades passés
    sur la journée

    :return: 3 vars : (pnl_euro, pnl_points, nb_trades)

    NOTE: Fonction dans main, déplacer dans events pour pouvoir être utilisé
    dans main et event sans imports de main dans events
    """

    # PNL en Euro
    pnl_euro = 0.0
    # Nombre de trades
    nb_trades = 0
    # PNL en points
    pnl_points = 0.0
    # PNL en points par lot
    pnl_points_per_lot = 0.0
    size = 0.0

    # recup de la date du jour
    daydate = time.strftime('%d-%m-%Y', time.localtime())
    # Formatage de l'url avec la date du jour
    # url = 'https://%s/gateway/deal/history/transactions/ALL/%s/%s' % \
    #       (urls.ig_host, daydate, daydate)
    r = requests.get(urls.transactionhistoryurl % (daydate, daydate),
                     headers=urls.fullheaders, proxies=personal.proxies)
    s = json.loads(r.content).get(u'transactions')

    for gain in s:
        if gain.get(u'transactionType') == 'ORDRE':
            # On ne calcule que si le type de la transaction est "ordre"

            # Calcul du PNL Journalier en Euro             
            # on recupere le pnl de la transaction
            b = gain.get(u'profitAndLoss')
            # on supprime le 'E'
            b = b[1:]
            # on supprime la ',' ex 2,500.50 -> 2500.50
            b = b.replace(',', '')
            # on additionne toutes les transactions
            pnl_euro += float(b)

            # Calcul du nombre de point                    
            # recupere openlevel
            openLevel = gain.get(u'openLevel')
            # recupere closelevel
            closeLevel = gain.get(u'closeLevel')

            # recupere la taille pour avoir le sens (+ ou -)
            size =  float(gain.get(u'size'))
            # print("getDailyPnl : size ", size)
            
            distance_to_close = float(closeLevel) - float(openLevel)
            
            # on arrondi pour ne pas avoir 0,2999999 point
            diff_level = round(distance_to_close * size, 1)
            diff_level_per_lot = round(distance_to_close * size / abs(size), 1)
            
            # print("closeLevel,openLevel,size,diff_level,"
            #       "diff_level_per_lot,distance_to_close",
            #       closeLevel, openLevel, size, diff_level, diff_level_per_lot,
            #       distance_to_close)
            # on additionne les points (+ et -)
            pnl_points += diff_level
            pnl_points_per_lot += diff_level_per_lot
            
            # Incrementation du nombre de trades
            nb_trades += 1
            
    # print("getDailyPnl : renvoi des 4 variables (pnl_euro, pnl_points"
    #       ", pnl_points_per_lot, nb_trades)",
    #       pnl_euro, pnl_points, pnl_points_per_lot, nb_trades)
    return pnl_euro, pnl_points, pnl_points_per_lot, nb_trades
