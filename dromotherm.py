#!/usr/bin/env python3
import time
import signal
import logging
import json
import numpy as np
from modbusTools import *

"Test telechargement Prince"

# intervalle de pilotage
interval = 10

#Réglages généraux à ne pas toucher
common = {
    "modbus_ip": '192.168.2.1',
    "tcp_port": 503,
    "rtu_port": '/dev/ttyUSB1',
    "baudrate": 9600
}

"""
Tuto pour le fichier dromotherm.py

Tout se passe dans la fonction "action" (rechercher "def action(self):").
Dans la fonction action est présent un exemple de contrôle des pompes et variateurs.
On peut aussi choisir l'intervalle de pilotage (ici toutes les 10s). attention, comme les données sont mises à jour toutes les 30s, mettre un intervalle trop bas est inutile.

Dans le fichier, il y a des slaves et des feeds :
   Les slaves sont les éléments à contrôler (relais, sortie 4-20mA pour variateur...)
   Les feeds sont des entrées (pour lire les valeurs reçues des capteurs)

Pour les slaves :
   id : numéro du module promux à contrôler
   address : numéro de la sortie du module promux à contrôler
   type : digital ou analog,
      digital pour un module tout ou rien (ex : relais, digital output),
      analog pour un module à sortie continue (ex : 4-20mA, 0-10v)
   mode : different pour digital ou analog
      digital : stop, run ou auto (permet de préciser le mode de fonctionnement de la sortie)
      analog : forced ou auto (permet de préciser le mode de fonctionnement de la sortie)
   value : pour les modules de type analog, donne la valeur forcée si mode=forced

Pour les feeds :
   pour chaque feed, on met une liste sous la forme [1, 12, 27, 3].
   Les nombres entiers inscrits correspondent aux identifiants de feeds (voir onglet feeds sur la page web) que l'on souhaite récupérer et moyenner dans le feed.
   exemple : si on met dans feeds "road_temp" : [10,23, 2], read("road_temp") récupère la moyenne des feeds aux identifiants 10, 23 et 2 de la page web "feeds".
   Pour info, un survol d'un feed dans l'onglet feeds de la page web permet de connaître son numéro d'identifiant.


NOTE : les fichiers .conf utilisés par l'interface web sont dans /etc/bios/

Les fichiers .conf dans /opt/openenergymonitor/BIOS2/hardware ne sont que des versions pour réaliser des tests de fonctionnement des matériels.
Les exécutables du répertoire hardware sont tjrs à lancer une fois avant d'installer le service correspondant.
Lors de la première exécution, le fichier conf est initialisé par l'exécutable, dans ce même dossier hardware.
Lorsqu'on installe le service, l'installateur copie le fichier conf résidant dans hardware vers /etc/bios
"""

##Définition du type slaves et feeds, mais réglage à faire dans le fichier dromotherm.conf!!!
##Ici il s'agit uniquement d'un exemple
slaves = {
    "road_pump": {"id": 37, "address": 0, "mode": "stop", "type": "digital"},
    "storage_pump": {"id": 37, "address": 1, "mode": "stop", "type": "digital"},
    "PAC_pump": {"id": 37, "address": 2, "mode": "stop", "type": "digital"},
    "PAC": {"id": 37, "address": 3, "mode": "stop", "type": "digital"},
    "road_pump_variator": {"id": 38, "address": 7, "type": "analog"}
}
feeds = {
    "road_temp": {"feeds" : [24,26], "fakeValue":25},
    "Text":{"feeds":[13,20], "fakeValue":34}
}

def modbusWriteCoil(modbusCon, id, address, val):
    """
    écriture sur un coil/bobine puis lecture de la valeur écrite

    val : 0/1 ou False/True
    """
    message = {}
    message["success"] = False
    rq = modbusCon.write_coil(address, val, unit=id)
    if rq.isError():
        message["text"] = "erreur d'écriture - {}".format(rq)
    else:
        rr = modbusCon.read_coils(address, 1, unit=id)
        if rr.isError():
            message["text"] = "erreur de lecture - {}".format(rr)
        else:
            if rr.bits[0] == val:
                message["success"] = True
                message["text"] = "modbus unit {} > {} écrit sur coil {}".format(id,val,address)
            else :
                message["text"] = "modbus unit {} coil {} > la valeur lue ne correspond pas à la valeur écrite".format(id,address)
    return message

class Dromotherm:
    def __init__(self, confname):
        self._confname = confname
        self._conf = {}
        self._conf["common"] = common
        self._conf["slaves"] = slaves
        self._conf["feeds"] = feeds
        self._interval = interval
        self._exit = False
        self._start = int(time.time())
        self._ts = self._start
        self._log = logging.getLogger("dromotherm")
        self._log.setLevel("DEBUG")
        self._log.info("............OPENING DROMOTHERM............")

    def createConfFile(self):
        with open(self._confname, "w") as f:
            json.dump(self._conf, f, indent=4)

    def checkConf(self):
        try:
            with open(self._confname) as f:
                conf =  json.loads(f.read())
                if "interval" in conf:
                    self._interval = conf["interval"]
                if conf != self._conf:
                    self._log.debug("changement de configuration")
                    self._conf = conf
        except FileNotFoundError as e:
            self._log.debug(e)
            self.createConfFile()
        except Exception as e:
            import os
            if os.stat(self._confname).st_size == 0:
                self.createConfFile()
            self._log.debug(e)

    def run(self):
        signal.signal(signal.SIGINT, self._sigint_handler)
        signal.signal(signal.SIGTERM, self._sigint_handler)
        if not self._exit:
            self._ts = int(time.time())
            self._log.debug("starting dromotherm at {}".format(self._ts))

        while not self._exit:
            now = int(time.time())
            self.checkConf()
            if now - self._ts > self._interval :
                self._ts = now
                self.action()
            time.sleep(0.1)

    def action(self):
        """
        Cette fonction est la seule fonction à éditer. Plusieurs versions de contrôle pourront être explorées, fonction des résultats de la thèse.
        :return:
        """

        self._log.debug("Action")

        # On récupère heure et minute pour les scenarios quotidiens
        #heureActuelle = (int(int(time.time())/3600)%24)+2
        #minuteActuelle = (int(int(time.time())/60)%60)
        import os,sys
        current_dir=sys.path[0]
        parent_dir=os.path.dirname(current_dir)
        sys.path.insert(0, parent_dir)
        from planning import tsToTuple
        now = int(time.time())
        heureActuelle = int(tsToTuple(now).tm_hour)
        minuteActuelle = int(tsToTuple(now).tm_min)

        c = self.connexion()
        if c.connect():
            #Action sur la pompe de la chaussée : 3 cas, stop, run, et auto
            self._log.info("Action sur {}, mode : {}".format("road_pump",self._conf["slaves"]["road_pump"]["mode"]))
            if self._conf["slaves"]["road_pump"]["mode"] == "stop":
                self.write(c, "road_pump", False)
            if self._conf["slaves"]["road_pump"]["mode"] == "run":
                self.write(c, "road_pump", True)
            if self._conf["slaves"]["road_pump"]["mode"] == "auto":
                self._log.info("Test sur Text : {}".format(self.read("Text")))
                self._log.info("Test sur Tint : {}".format(self.read("Tint")))
                # Le mode auto est à écrire, ici juste un premier exemple
                if self.read("Tint") > 27:  #si on est dans la plage horaire 8h-20h on allume la pompe
                    self._log.info("road_pump True")
                    self.write(c, "road_pump", True)
                else:
                    self._log.info("road_pump False")
                    self.write(c, "road_pump", False)

            '''#Action sur la pompe pour la PAC : 3 cas, stop, run, et auto
            self._log.info("Action sur {}, mode : {}".format("PAC_pump",self._conf["slaves"]["PAC_pump"]["mode"]))
            if self._conf["slaves"]["PAC_pump"]["mode"] == "stop":
                self.write(c, "PAC_pump", False)
            if self._conf["slaves"]["PAC_pump"]["mode"] == "run":
                self.write(c, "PAC_pump", True)
            if self._conf["slaves"]["PAC_pump"]["mode"] == "auto":
                # Le mode auto est à écrire, ici juste un premier exemple
                if heureActuelle > 8 and heureActuelle < 20: #si on est dans la plage horaire 8h-20h on allume la pompe
                    self.write(c, "PAC_pump", True)
                else:
                    self.write(c, "PAC_pump", False)

            #Action sur la pompe du stockage : 3 cas, stop, run, et auto
            self._log.info(
                "Action sur {}, mode : {}".format("storage_pump", self._conf["slaves"]["storage_pump"]["mode"]))
            if self._conf["slaves"]["storage_pump"]["mode"] == "stop":
                self.write(c, "storage_pump", False)
            if self._conf["slaves"]["storage_pump"]["mode"] == "run":
                self.write(c, "storage_pump", True)
            if self._conf["slaves"]["storage_pump"]["mode"] == "auto":
                # Le mode auto est à écrire, ici juste un premier exemple
                if self.read("road_temp") > 27:  #si road_temps supérieur à 27, on allume la pompe
                    self.write(c, "storage_pump", True)
                else:
                    self.write(c, "storage_pump", False)'''

            #Action sur le variateur de la pompe de la chaussée : 2 cas, forced et auto
            self._log.info(
                "Action sur {}, mode : {}".format("road_pump_variator", self._conf["slaves"]["road_pump_variator"]["mode"]))
            if self._conf["slaves"]["road_pump_variator"]["mode"] == "forced":
                self.write(c, "road_pump_variator", self._conf["slaves"]["road_pump_variator"]["value"])
            if self._conf["slaves"]["road_pump_variator"]["mode"] == "auto":
                # Le mode auto est à écrire, ici juste un premier exemple
                self.write(c, "road_pump_variator", 0.5) #On met le variateur à 0.5 (50%) de sa puissance

            c.close()
            if not c.is_socket_open():
                self._log.debug("All queries finished - modbus connection is closed")
                self._log.debug("--------------------------------")

    def read(self, name):
        """
        Cette fonction permet de lire un des feeds réglés dans le fichier dromotherm.conf
        :param name: le nom du feed que l'on cherche dans dromotherm.conf, le programme fait automatiquement la moyenne des numéros de feed identifiés.
        :return:
        """
        try:
            import redis
        except Exception as e:
            #self._log.error(e)
            return self._conf["feeds"][name]["fakeValue"]

        r = redis.Redis(host="localhost", port=6379, db=0)
        nbs = self._conf["feeds"][name]["feeds"]
        values = []
        for nb in nbs:
            feed = r.hmget("feed:{}".format(nb),"value", "time")
            values.append(float(feed[0].decode()))
            # Verification age des données
            ts = int(feed[1].decode())
            age = abs(int(time.time())-ts)
            if age>60:
                self._log.info("Attention, data ancienne, age : {}s".format(age))
        return np.mean(values)

    def write(self, c, name, value):
        """
        Cette fonction permet d'ecrire sur les registres des promux.
        :c: connexion vers le bus établie
        :param name: le nom du slave sur lequel on souhaite effectuer une action
        :param value: la valeur a envoyer. Deux cas existent, "digital" et "analog".
        - "digital" on peut envoyer dans value True ou False
        - "analog" on peut envoyer dans value une valeur flottante, comprise entre 0 et 1.
        :return:
        """
        type = self._conf["slaves"][name]["type"]
        id = self._conf["slaves"][name]["id"]
        address = self._conf["slaves"][name]["address"]
        if type == "digital":
            message = modbusWriteCoil(c, id, address, value)
            self._log.debug(message)
        if type == "analog":
            if value<0 or value>1:
                self._log.error("Impossible d'avoir une value non comprise entre 0 et 1")
                return
            if not pymodbus_found:
                self._log.debug("Adress {} id {} valeurConvertie {}".format(address, id, int(value * 4095.0)))
                return
            message = modbusWrite(c, address, "h", id, int(value * 4095.0))
            self._log.debug(message)

    def connexion(self):
        pass

    def _sigint_handler(self, signal, frame):
        """
        Réception du signal de fermeture
        """
        self._log.info("signal de fermeture reçu")
        self._exit = True

    def close(self):
        self._log.info("fermeture :-)")

class fakeConnection():
    def __init__(self):
        pass
    def connect(self):
        return True
    def write_coil(self, address, val, unit):
        return fakeModbusResult()
    def close(self):
        return
    def is_socket_open(self):
        return

class fakeModbusResult():
    def __init__(self):
        pass
    def isError(self):
        return True

class DromothermTCP(Dromotherm):
    def connexion(self):
        if pymodbus_found:
            from pymodbus.client.sync import ModbusTcpClient as Client
            modbus_ip = self._conf["common"]["modbus_ip"]
            tcp_port = self._conf["common"]["tcp_port"]
            return Client(modbus_ip, tcp_port)
        else:
            return fakeConnection()

class DromothermRTU(Dromotherm):
    def connexion(self):
        if pymodbus_found:
            from pymodbus.client.sync import ModbusSerialClient as Client
            rtu_port = self._conf["common"]["rtu_port"]
            baudrate = self._conf["common"]["baudrate"]
            return Client(port=rtu_port, method="rtu", baudrate=baudrate)
        else:
            return  fakeConnection()

if __name__ == "__main__":
    import argparse
    import sys
    # Command line arguments parser
    parser = argparse.ArgumentParser(description='dromotherm')
    # Log file
    parser.add_argument('--log', action='store')
    # on donne à args.conf une valeur par défaut pour qu'il existe forcément
    if sys.path[0][0:2]=="C:":
       parser.add_argument("--conf", action="store", default="{}/dromotherm.conf".format("D:/Utilisateurs/sevif/Documents/GitHub/dromothermCabane"))
    else:
       parser.add_argument("--conf", action="store", default="{}/dromotherm.conf".format(sys.path[0]))
    parser.add_argument("--mode", action="store", default="tcp")
    args = parser.parse_args()

    logger = logging.getLogger("dromotherm")
    if args.log:
        # journalisation dans un fichier
        import logging.handlers
        loghandler = logging.handlers.RotatingFileHandler(args.log, maxBytes=5000 * 1024, backupCount=1)
    else:
        # journalisation à l'écran
        loghandler = logging.StreamHandler()

    # not using %(name)s
    loghandler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(message)s'))
    logger.addHandler(loghandler)

    if args.mode == "rtu":
        loop = DromothermRTU(args.conf)
    else:
        loop = DromothermTCP(args.conf)
    loop.run()
    loop.close()
