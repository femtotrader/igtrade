# -*- coding:utf-8 -*-

# Fichier de definition/stockage des variables globales du programme.
import collections

version = "1.17"

# Variables Instrument
minDealSize = None  # Affectation de la valeur à la connexion
currencyCode = None  # Monnaie utilise par l'epic
valueOfOnePip = None  # Valeur en monnaie d'un pip
scalingFactor = None  # Valeur du facteur d'échelle
spread = None  # Valeur du spread
# Distance en point/pips du Stop-Normal à l'ouverture
minNormalStoporLimitDistance = None
# Distance en point/pips du Stop-Garantie à l'ouverture
minControlledRiskStopDistance = None

########################################
# V1 du dictionnaire de position ouverte
# Dictionnaire avec la référence du dealID comme "Key"
# et value une liste avec les éléments[epic, size, direction, level, TP, SL]
# dict_openposition = collections.OrderedDict()
########################################
# V2 du dictionnaire de position ouverte
# Sous la forme {"dealId": {"epic": '',
#                           "size": '',
#                           "direction": '',
#                           "open_level": '',
#                           "limit_level": '',
#                           "stop_level": '',
#                           "pnl": ''},
#                 "dealId": { ... }
#                 }
dict_openposition = collections.OrderedDict()

# List pour ordonner les key des postions
list_key = ["epic", "size", "direction", "open_level", "limit_level",
            "stop_level", "guaranteedStop", "pnlperlot", "pnl"]

# Variable "Ticket"
requestDealSize = 1
dealSizeDelta = 0  # Init a 0
isForceOpen = True
SLpoint = ''
TPpoint = ''
SLcurrency = ''
SLpercentage = '' 

# Variable Programme
isGuaranteedStopTrading = False

# Positionne a false pour forcer l'utilisateur a cliquer sur la case
# pour ne pas passer des trades
isKeyBoardTrading = False

is_AutoStop_to_OpenLevel = False


# Variable account
balance = 0
deposit = 0

epic_dict = {
    "Japon 225 au comptant (Mini-contrat 1$)" : "IX.D.NIKKEI.IFM.IP",
    "Japon 225 au comptant (Contrat PLEIN 5$)" : "IX.D.NIKKEI.IFD.IP",
    "Australie 200 au comptant (Mini-contrat 5$A)" : "IX.D.ASX.IFM.IP",
    "EU Stocks 50 au comptant (Mini-Contrat 2E)"	: "IX.D.STXE.IFM.IP",
    "FTSE 100 au comptant (Mini-Contrat 1E)" : "IX.D.FTSE.IFE.IP",
    "FTSE 100 au comptant (Mini-contrat 2GBP)" : "IX.D.FTSE.IFM.IP",
    "France 40 au comptant (Mini-contrat 1E)" : "IX.D.CAC.IMF.IP",
    "France 40 au comptant (Contrat PLEIN 10E)" : "IX.D.CAC.IDF.IP",
    "Allemagne 30 au comptant (Mini-contrat 5E)" : "IX.D.DAX.IMF.IP",
    "Allemagne 30 au comptant (Contrat PLEIN 25E)" : "IX.D.DAX.IDF.IP",
    "Espagne 35  au comptant (Mini-contrat 2E)" : "IX.D.IBEX.IFM.IP",
    "US Tech 100 au comptant (Mini-contrat 20$)" : "IX.D.NASDAQ.IFM.IP",
    "US 500 au comptant (Mini-contrat 50$)" : "IX.D.SPTRD.IFM.IP",
    "US 500 au comptant (Contrat 1E)" : "IX.D.SPTRD.IFE.IP",
    "Wall Street au comptant (Mini-contrat 2$)" : "IX.D.DOW.IMF.IP",
    "Wall Street au comptant (Contrat 1E)" : "IX.D.DOW.IFE.IP",
    "Wall Street au comptant (Contrat PLEIN 10$)" : "IX.D.DOW.IDF.IP",
    "US Russel 2000 au comptant (Mini-Contrat 100$)" : "TM.D.RUS2000.IFM.IP",
    "FX au comptant (mini) AUD/USD"	: "CS.D.AUDUSD.MINI.IP",
    "FX au comptant (mini) EUR/CHF"	: "CS.D.EURCHF.MINI.IP",
    "FX au comptant (mini) EUR/GBP"	: "CS.D.EURGBP.MINI.IP",
    "FX au comptant (mini) EUR/JPY"	: "CS.D.EURJPY.MINI.IP",
    "FX au comptant (mini) EUR/USD"	: "CS.D.EURUSD.MINI.IP",
    "FX au comptant (mini) GBP/USD"	: "CS.D.GBPUSD.MINI.IP",
    "FX au comptant (mini) USD/CAD"	: "CS.D.USDCAD.MINI.IP",
    "FX au comptant (mini) USD/CHF"	: "CS.D.USDCHF.MINI.IP",
    "FX au comptant (mini) USD/JPY"	: "CS.D.USDJPY.MINI.IP",
    "FX au comptant (mini) CHF/JPY"	: "CS.D.CHFJPY.MINI.IP",
    "FX au comptant (mini) EUR/CAD"	: "CS.D.EURCAD.MINI.IP",
    "FX au comptant (mini) GBP/JPY"	: "CS.D.GBPJPY.MINI.IP",
    "FX au comptant (mini) AUD/JPY"	: "CS.D.AUDJPY.MINI.IP",
    "Bund au comptant (Mini-contrat 1E)" : "CC.D.FGBL.UME.IP",
    "Bund au comptant (Contrat PLEIN 10E)" : "CC.D.FGBL.UNC.IP",
    "US Brut Léger au comptant (Mini-contrat 1E)" : "CC.D.CL.UME.IP",
    "US Brut Léger au comptant (Contrat PLEIN 10$)" : "CC.D.CL.UNC.IP",
    "Brut Brent au comptant (Contrat Plein 10$)" : "CC.D.LCO.UNC.IP",
    "Brut Brent au comptant (Contrat 1E)" : "CC.D.LCO.UME.IP",
    }
# Dictionnaire pour afficher des noms court et inteligible a la place de l'epic
# A COMPLETER
epic_to_shortname_dict = {
    "IX.D.ASX.IFM.IP" : "miniAustralie200(5AUD)",
    "IX.D.STXE.IFM.IP" : "miniEU50(2E)",
    "IX.D.FTSE.IFE.IP" : "miniFTSE100(1E)",
    "IX.D.FTSE.IFM.IP" : "miniFTSE100(2GBP)",
    "IX.D.CAC.IMF.IP" : "miniCAC40(1E)",
    "IX.D.DAX.IMF.IP" : "miniDAX30(5E)",
    "IX.D.IBEX.IFM.IP" : "miniES35(2E)",
    "IX.D.NASDAQ.IFM.IP" : "miniUSTech100(20$)",
    "IX.D.SPTRD.IFM.IP" : "miniSP500(50$)",
    "IX.D.SPTRD.IFE.IP" : "miniSP500(1E)",
    "IX.D.DOW.IMF.IP" : "miniDJIA30(2$)",
    "IX.D.DOW.IFE.IP" : "miniDJIA30(1E)",
    "IX.D.DAX.IDF.IP" : "DAX30(25E)",
    "IX.D.DOW.IDF.IP" : "DJIA30(10$)",
    "IX.D.CAC.IDF.IP" : "CAC40(10E)",
    "IX.D.NIKKEI.IFM.IP" : "miniJapon225(1$)",
    "IX.D.NIKKEI.IFD.IP" : "Japon225 (5$)",
    "TM.D.RUS2000.IFM.IP" : "miniRUSS2000 (100$)",
    "CS.D.AUDUSD.MINI.IP" : "mini AUD/USD",
    "CS.D.EURCHF.MINI.IP" : "mini EUR/CHF",
    "CS.D.EURGBP.MINI.IP" : "mini EUR/GBP",
    "CS.D.EURJPY.MINI.IP" : "mini EUR/JPY",
    "CS.D.EURUSD.MINI.IP" : "mini EUR/USD",
    "CS.D.GBPUSD.MINI.IP" : "mini GBP/USD",
    "CS.D.USDCAD.MINI.IP" : "mini USD/CAD",
    "CS.D.USDCHF.MINI.IP" : "mini USD/CHF",
    "CS.D.USDJPY.MINI.IP" : "mini USD/JPY",
    "CS.D.CHFJPY.MINI.IP" : "mini CHF/JPY",
    "CS.D.EURCAD.MINI.IP" : "mini EUR/CAD",
    "CS.D.GBPJPY.MINI.IP" : "mini GBP/JPY",
    "CS.D.AUDJPY.MINI.IP" : "mini AUD/JPY",
    "CC.D.FGBL.UME.IP" : "Bund(1E)",
    "CC.D.FGBL.UNC.IP" : "Bund(10$)",
    "CC.D.CL.UME.IP" : "US Brut Léger(1E)",
    "CC.D.CL.UNC.IP" : "US Brut Léger(10$)",
    "CC.D.LCO.UNC.IP" : "Brut Brent(10$)",
    "CC.D.LCO.UME.IP" : "Brut Brent(1E)",
    }
