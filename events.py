# -*- coding:utf-8 -*-

import requests
import json
import logging
import time

import urls
import personal
# import main

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


def processPriceUpdate(item, myUpdateField):
    """Process à lighstreamer price update

    :param item:
    :param myUpdateField:
    :return:
    """
    # logger.info(str(myUpdateField))##Mise en sommeil du logger de flux LS

    bid, ask = myUpdateField
    sum_point = 0
    point_profit = 0
    # calcul du pnl pour chaque pos de l'epic actif
    for dealId in globalvar.dict_openposition:
        deal = globalvar.dict_openposition.get(dealId)
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
        guaranteedStop = deal.get('guaranteedStop')

        # calcul pnl en points de chaque position
        # Exclusion des lignes qui ne sont pas dans bon epic
        #  +
        # Move du stop level si la distance avec l'open level est suffisante.
        ## Optim : Faire 2 fonctions distinctes.
        if epic == personal.epic:
            if direction == 'BUY':
                distance_to = ((float(ask) - float(open_level))
                               * globalvar.scalingFactor)
            elif direction == 'SELL':
                distance_to = ((float(open_level) - float(bid))
                               * globalvar.scalingFactor)
                
            pos_pnlperlot = round(distance_to, 1)
            pos_pnl = round(distance_to * float(size), 1)
            sum_point += pos_pnl
            # print("dealId,pos_pnlperlot, pos_pnl, size, distance_to",
            #       dealId, pos_pnlperlot, pos_pnl, size, distance_to,
            #       sum_point)
            
            if globalvar.is_AutoStop_to_OpenLevel:
                if guaranteedStop :
                    # print(" guaranteedStop", dealId)
                    stopMinDistance = globalvar.minControlledRiskStopDistance
                else:
                    # print(" NOT guaranteedStop", dealId)
                    stopMinDistance = globalvar.minNormalStoporLimitDistance
                             
                if (((direction == 'BUY' and (sl < open_level or sl is None))
                      or 
                        (direction == 'SELL' and (sl > open_level or sl is None) )
                    ) and distance_to >= stopMinDistance):
                    print("processPriceUpdate:"
                          "try to move the stop to the open level",
                          sl, open_level)
                    updateLimit(dealId, open_level, tp)
        else:
            pos_pnlperlot = 'N/A'
            pos_pnl = 'N/A'
            
        globalvar.dict_openposition[dealId]['pnl'] = pos_pnl
        globalvar.dict_openposition[dealId]['pnlperlot'] = pos_pnlperlot
        
        # print("dealId, float(open_level)", dealId, float(open_level))
        # print("pos_pnlperlot",pos_pnlperlot)
        # print("pos_pnl", pos_pnl)
                              
    # print("Après la boucle For du dico de position")

    window.update_price(bid, ask, sum_point)


def processBalanceUpdate(item, myUpdateField):
    """Process an update of the users trading account balance

    :param item:
    :param myUpdateField:
    :return:
    """
    # print("--- processBalanceUpdate ---")
    # print(myUpdateField)
    globalvar.balance, pnl, globalvar.deposit = myUpdateField
    # Deplacement du code qui compte le nb de pos
    # et la taille agregee des lots pour l'epic donne dans processPositionUpdate
    # Ajout deposit
    window.update_balance(globalvar.balance, pnl, globalvar.deposit)


def processPositionUpdate(item, myUpdateField):
    """Process an update when an OPU message occured

    :param item:
    :param myUpdateField:
    :return:
    """
    # Fonction appelé sur reception d'un LS OPU #_#
    # print("--- processPositionUpdate ----")

    # DEBUG#
    # print("    message OPU : \n    %s"%myUpdateField)
    # print ("Type %s"%type(myUpdateField))

    if myUpdateField[0] is not None:
        # maroxe + falex
        opu = next(json.loads(field) for field in myUpdateField
                   if field is not None)
        opu_ordo = [opu.get(u'status'), opu.get(u'direction'), opu.get(u'size'),
                    opu.get(u'level'), opu.get(u'limitLevel'),
                    opu.get(u'stopLevel'), opu.get(u'guaranteedStop'),
                    opu.get(u'limitDistance'), opu.get(u'stopDistance'),
                    opu.get(u'dealStatus'), opu.get(u'dealId'),
                    opu.get(u'reason'), opu.get(u'epic'), opu.get(u'expiry'),
                    opu.get(u'affectedDeals'), opu.get(u'dealReference')]
        # Envoi des evenements OPU dans la sous fenêtre OPU
        window.add_OPUmessage(opu_ordo)

        # Trois messages 'status' à gérer :
        # 'OPEN' = Ouverture d'un nouveau ticket :
        #     Size = taille de l'ouverture
        # 'DELETED' = Fermeture d'un ticket existant :
        #     Size = Taille restante du ticket avant de tomber à Zéro.
        #     Message deleted = le ticket est complétement fermé
        #                       il n'en reste plus rien.
        # 'UPDATED' = MaJ du ticket (taille, SL, TP, trailling) :
        #     Size = Nouvelle taille du ticket avec ce qui reste.
        dealId = opu.get(u'dealId')
        if opu.get('status') == u'OPEN':
            # print("Ouverture position")
            # open_values = [opu.get(u'epic'), opu.get(u'size'),
            #                opu.get(u'direction'), opu.get(u'level'),
            #                opu.get(u'limitLevel'), opu.get(u'stopLevel')]
            # MàJ avec la v2 du dico
            open_values = {'epic': opu.get(u'epic'),
                           'size': opu.get(u'size'),
                           'direction': opu.get(u'direction'),
                           'open_level':opu.get(u'level'),
                           'limit_level':opu.get(u'limitLevel'),
                           'stop_level':opu.get(u'stopLevel'),
                           'guaranteedStop':opu.get(u'guaranteedStop'),
                           'pnlperlot':'N/A',
                           'pnl':'N/A'
                           }
            # Enregistrement de la position dans le dico
            globalvar.dict_openposition.update({dealId:open_values})
            # Envoi le dictionnaire à afficher
            window.set_openpositions(globalvar.dict_openposition)
            pru = PRU(personal.epic)
            window.update_pru(pru)
            update_countTicket()
        elif opu.get('status') == u'DELETED':
            # print("Fermeture position")
            try:
                del globalvar.dict_openposition[dealId]
            except KeyError:
                print("Erreur MaJ dico positions ouvertes")
                pass
            # print(globalvar.dict_openposition)
            # Envoi le dictionnaire à afficher
            window.set_openpositions(globalvar.dict_openposition)
            pru = PRU(personal.epic)
            window.update_pru(pru)
            update_countTicket()

            # Guilux modif pouir afficher le PNL Journalier
            # Calcul du PNL journalier
            pnlEuro, pnlPoints, pnlPointsPerLot, nbTrades = getDailyPnl()
            window.update_pnlDaily(pnlEuro, pnlPoints,
                                   pnlPointsPerLot, nbTrades)

        elif opu.get('status') == u'UPDATED':
            #print("Mise a jour ticket")
            #udpate_values = [opu.get(u'epic'), opu.get(u'size'), opu.get(u'direction'), opu.get(u'level'), opu.get(u'limitLevel'), opu.get(u'stopLevel')]
            #MàJ avec la v2 du dico
            udpate_values = {'epic': opu.get(u'epic'), 'size': opu.get(u'size'),
                             'direction': opu.get(u'direction'),
                             'open_level': opu.get(u'level'),
                             'limit_level':opu.get(u'limitLevel'),
                             'stop_level':opu.get(u'stopLevel'),
                             'guaranteedStop':opu.get(u'guaranteedStop'),
                             'pnlperlot':'N/A',
                             'pnl':'N/A'
                             }
            # MàJ du dico
            globalvar.dict_openposition[dealId] = udpate_values
            # print(globalvar.dict_openposition)
            # Envoi le dictionnaire à afficher
            window.set_openpositions(globalvar.dict_openposition)
            pru = PRU(personal.epic)
            window.update_pru(pru)
            update_countTicket()
            
            # Guilux modif pouir afficher le PNL Journalier
            # Calcul du PNL journalier
            pnlEuro,pnlPoints,pnlPointsPerLot,nbTrades = getDailyPnl()
            window.update_pnlDaily(pnlEuro, pnlPoints,
                                   pnlPointsPerLot, nbTrades)

        else:
            print("Autre status non gere : %s",opu.get('status'))
    # else:
    #     print("   message OPU = None ou vide")
    # print ("---Fin---")


def update_countTicket():
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
    sizeBuy = 0
    sizeSell = 0
    nb_ticket = 0
    for dealId in globalvar.dict_openposition:
        # on récupère l'epic pour chaque pos
        epic = globalvar.dict_openposition.get(dealId).get('epic')
        # on récupère le sens pour chaque pos
        direction = globalvar.dict_openposition.get(dealId).get('direction')
        # on récupère la taille pour chaque pos
        size = globalvar.dict_openposition.get(dealId).get('size')
        # d = p.get("position").get("direction")
        # s = p.get("position").get("dealSize")
        # e = p.get("market").get("epic")
        if (epic == personal.epic):
            if direction == "BUY":
                sizeBuy += size
                nb_ticket += 1
            elif direction == "SELL":
                sizeSell += size
                nb_ticket += 1
    window.update_pos(nb_ticket, sizeBuy, sizeSell)
    # print ("---Fin---")


def processTradeUpdate(item, myUpdateField):
    """
    Add by falex
    :param item:
    :param myUpdateField:
    :return:
    """
    # Fonction appelé sur reception d'un LS CONFIRMS #_#
    # DEBUG#
    # print("--- processTradeUpdate ---")
    # print("globalvar.dealSizeDelta = ",globalvar.dealSizeDelta)
    # print("myUpdateField ==>>> ",myUpdateField)

    if myUpdateField[0] != None:
        # DEBUG#
        # print("myUpdateField ==>>>", myUpdateField)
        message = next(json.loads(field)
                       for field in myUpdateField if field is not None)
        direction = message.get(u'direction')
        status = message.get(u'status')
        dealId = message.get(u'dealId')
        dealReference = message.get(u'dealReference')
        dealStatus = message.get(u'dealStatus')
        reason = message.get(u'reason')
        # if message.get(u'affectedDeals') != None:
        if dealStatus == u'ACCEPTED':
            # Suppression d'un bout de ticket
            # si la taille demandé est inférieur à la taille min du contrat
            for f in message.get(u'affectedDeals'):
                affDealsId = f.get(u'dealId')
                affstatus = f.get(u'status')
                # if (affDealsId == dealId and affstatus == u'OPENED' and
                #             globalvar.dealSizeDelta > 0):
                #     # Jusqu'à présent dealId et AffDealsId
                #     # avaient la même référence à l'ouverture.
                if (affstatus == u'OPENED' and globalvar.dealSizeDelta > 0):
                # Modification des conditions d'entrée
                # si status OPENED et globalvar.dealSizeDelta > 0
                    # DEBUG#
                    # print("Je sort %s de la position" %
                    #       globalvar.dealSizeDelta)

                    # UPDATE avec le affected Deal Id
                    body = {"dealId": affDealsId,
                            "direction": "SELL",
                            "size": globalvar.dealSizeDelta,
                            "orderType": "MARKET"
                            }
                    # ajustement de la direction dans l'ordre DELETE
                    # en fonction du sens d'ouverture
                    if direction == "SELL":
                        body['direction'] = "BUY"
                    # DEBUG#
                    # print("data ", body)
                    # print("headers ", urls.deleteheaders)
                    r = requests.post(urls.closeorderurl,
                                      data=json.dumps(body),
                                      headers=urls.deleteheaders,
                                      proxies=personal.proxies)
        else:
            # Problème dans l'ordre, création d'un dictionnaire similaire à OPU
            # pour l'nevoyer à l'affichage dans le fenêrte d'évenemnt
            opu_ordo = [dealStatus, reason]
            # Envoi des evenements OPU dans la sous fenêtre OPU
            window.add_OPUmessage(opu_ordo)
        # print("Post DELETE Status code -> ", r.status_code)
    # print("----Fin----")


def get_openPositions():
    """Process the set the openposition from an empty list,
    the number of tick and aggregate lot for the current epic

    :return:
    """
    # print("--- get_openPositions ---")

    r = requests.get(urls.positionsurl, headers=urls.fullheaders,
                     proxies=personal.proxies)
    s = json.loads(r.content).get("positions")
    print("--- get_openPositions ---\n    Code %s" % r.status_code)
    globalvar.dict_openposition = {}  # Ajout 1.14.2
    sizeBuy = 0
    sizeSell = 0
    nb_ticket = 0
    for p in s:
        # DealID
        dealId = p.get("position").get("dealId")
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
        guaranteedStop = p.get("position").get("controlledRisk")
        if e == personal.epic:
            if d == "BUY":
                sizeBuy += s
                nb_ticket += 1
            elif d == "SELL":
                sizeSell += s
                nb_ticket += 1
        # Ajout position dans le dictionnaire "dealdId":[epic, size, direction, openLevel, TP, SL]`
        # globalvar.dict_openposition.update({dealId:[e,s, d, ol, ll, sl]})
        # MàJ avec la v2 du dico
        new_deal = {"epic": e,
                    "size": s,
                    "direction": d,
                    "open_level": ol,
                    "limit_level": ll,
                    "stop_level": sl,
                    "guaranteedStop": guaranteedStop,
                    "pnlperlot": 'N/A',
                    "pnl": 'N/A'}
        globalvar.dict_openposition.update({dealId: new_deal})
    window.update_pos(nb_ticket, sizeBuy, sizeSell)
    # print("Envoi de =>>>>>>>>>> ", globalvar.dict_openposition)
    window.set_openpositions(globalvar.dict_openposition)  # Ok
    pru = PRU(personal.epic)
    window.update_pru(pru)
    # print ("---Fin---")


def delete(dealId, direction, reqDealSize):
    """Process de suppresion d'un ticket en fonction de :
     - son dealId
     - sa direction
     - et sa taille.

    :param dealId:
    :param direction:
    :param reqDealSize:
    :return:
    """
    # print("--- events.delete ---")
    print("Ticket %s a supprimer" % dealId)

    body = {"dealId": dealId,
            "direction": "SELL",
            "size": reqDealSize,
            "orderType": "MARKET"
            }
    # print(body)
    if direction == "SELL":
        # ajustement de la direction dans l'ordre DELETE
        # en fonction du sens d'ouverture
        body['direction'] = "BUY"

    r = requests.post(urls.closeorderurl, data=json.dumps(body),
                      headers=urls.deleteheaders, proxies=personal.proxies)

    print("--- delete ---\n    Code %s"%(r.status_code))
    if r.status_code != 200:
        # Si message d'erreur alors
        # on force le refresh des positions en local avec une R REST
        get_openPositions()
    # print("--- FIN : Events.delete ---")


def updateLimit(dealId, SLlevel, TPlevel):
    # DEBUG#
    print(" --- updateLimit ---")
    print("Ticket %s a updater SL = %s TP = %s" %(dealId, SLlevel, TPlevel))
    body = {"limitLevel":TPlevel, "stopLevel":SLlevel}
    r = requests.put(urls.updateorderurl % dealId, data=json.dumps(body),
                     headers=urls.fullheaders, proxies=personal.proxies)
    print("--- updateLimit ---\n    Code %s" % r.status_code)
    # print("--- FIN : Events.updateLimit ---")


def PRU(epic):
    """calcul du Prix de Revient Unitaire (PRU)
    about: fonction que j'ai du mettre ici pour pouvoir l'utiliser
           dans main et events.
    :param epic:
    :return: PRU value
    """
    pru = 0
    size = 0
    for dealId in globalvar.dict_openposition:
        if globalvar.dict_openposition.get(dealId).get('epic') == epic:
            o = float(globalvar.dict_openposition.get(dealId).get('open_level'))
            s = globalvar.dict_openposition.get(dealId).get('size')
            pru += (o * s)
            size = size + s
    try:
        pru = round(float(pru/size), 5)  # Arrondi à 5 décimales
    except ZeroDivisionError:
        pru = None
    return pru


def getDailyPnl():
    """Retourne le PNL en Euro, en points et le nombre de trades passés
    sur la journée

    :return: 3 vars : (pnlEuro, pnlPoints, nbTrades)

    NOTE: Fonction dans main, déplacer dans events pour pouvoir être utilisé
    dans main et event sans imports de main dans events
    """

    pnlEuro=0.0                  # PNL en Euro
    nbTrades=0                   # Nombre de trades
    pnlPoints = 0.0              # PNL en points
    pnlPoints_per_lot= 0.0       # PNL en points par lot
    size=0.0

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
            pnlEuro += float(b)

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
            diffLevel = round(distance_to_close * size, 1)
            diffLevel_per_lot = round(distance_to_close * size / size, 1)
            
            # print("closeLevel,openLevel,size,diffLevel,"
            #       "diffLevel_per_lot,distance_to_close",
            #       closeLevel, openLevel, size, diffLevel, diffLevel_per_lot,
            #       distance_to_close)
            # on additionne les points (+ et -)
            pnlPoints += diffLevel
            pnlPoints_per_lot += diffLevel_per_lot
            
            # Incrementation du nombre de trades
            nbTrades += 1
            
    # print("getDailyPnl : renvoi des 4 variables (pnlEuro, pnlPoints"
    #       ", pnlPoints_per_lot, nbTrades)",
    #       pnlEuro, pnlPoints, pnlPoints_per_lot, nbTrades)
    return pnlEuro, pnlPoints, pnlPoints_per_lot, nbTrades
