"""
Fonctions modbus mutualisées entre les classes
"""
try:
    from pymodbus.constants import Endian
    from pymodbus.payload import BinaryPayloadDecoder
    from pymodbus.payload import BinaryPayloadBuilder
    from pymodbus.client.sync import ModbusTcpClient as ModbusTCPClient
    from pymodbus.client.sync import ModbusSerialClient as Client
except ImportError as e:
    importStatus = e
    pymodbus_found = False
else:
    importStatus = "success"
    pymodbus_found = True

# valid datacodes list and number of registers associated
# in modbus protocol, one register is 16 bits or 2 bytes
valid_datacodes = ({'h': 1, 'H': 1, 'i': 2, 'l': 2, 'I': 2, 'L': 2, 'f': 2, 'q': 4, 'Q': 4, 'd': 4})

def open_modTCP(name, modbus_IP, modbus_port):
    """
    ouvre une connection vers un équipement modbus TCP
    """
    message = {}
    c = ModbusTCPClient(modbus_IP, modbus_port)
    if c.connect():
        message["success"] = True
        message["text"] = "{} - modbusTCP connection opened @ {}:{}".format(name,modbus_IP,modbus_port)
        return message, c
    else:
        message["success"] = False
        message["text"] = "{} - modbusTCP connection failure @ {}:{}".format(name,modbus_IP,modbus_port)
        return message, None

def open_modRTU(port, baudrate):
    """
    ouvre une connexion RTU
    """
    message = {}
    c = Client(port=port, method="rtu", baudrate=baudrate)
    if c.connect():
        message["success"] = True
        message["text"] = "modbus RTU connexion opened port {} - {} bauds".format(port,baudrate)
        return message, c
    else:
        message["success"] = False
        message["text"] = "modbus RTU connexion failure port {} - {} bauds".format(port,baudrate)
        return message, None

def modbusReadSensorOnEnlessRcv(modbusCon, address, unitId):
    """
    Chaque capteur Enless occupe au plus 11 registres dans la table modbus du récepteur:-)

    les 5 premiers registres permettent de déterminer :
    - le type de capteur et donc la nature des données à lire
    - le numéro de série
    - l'age des données (Timer) et la qualité de la réception radio (RSSI)
    """
    from struct import pack, unpack
    message = {}
    message["success"]=False
    payload = {}
    rr=modbusCon.read_holding_registers(address,11,unit=unitId)
    """
    # rr.registers est un tableau de mots
    print("{:04x}{:04x}{:04x}{:04x}{:04x}".format(*rr.registers))
    """
    # remise en forme comme un tableau d'octets
    try :
        datas = b''.join(pack('!H',x) for x in rr.registers)
    except Exception as e:
        message["text"] = e
    else:
        """
        for i in range(len(datas)):
            print("{:02x}".format(datas[i]))
        """
        message["success"]=True
        payload["type"] = "{:02x}".format(datas[0])
        payload["Timer"] = unpack(">H",datas[2:4])[0]
        payload["RSSI"] = datas[5]/2
        message["serial"] = "{:02x}{:02x}{:02x}{:02x}".format(*datas[6:10])
        if datas[0] in [0x01, 0x02, 0x03]:
            payload['temp'] = unpack(">h", datas[10:12])[0]/10
        if datas[0] == 0x02:
            payload['rh'] = unpack(">H", datas[12:14])[0]/10
        if datas[0] == 0x24:
            payload['CO2'] = unpack(">H", datas[10:12])[0]
            payload['temp'] = unpack(">h", datas[12:14])[0]/10
            payload['rh'] = unpack(">H", datas[14:16])[0]/10

    return message, payload

def decode(decoder, datacode):
    """
    décode avec la méthode pymodbus

    decoder : payload decoder retourné par `BinaryPayloadDecoder.fromRegisters`
    """
    val = float('nan')
    if datacode == 'h':
        val = decoder.decode_16bit_int()
    elif datacode == 'H':
        val = decoder.decode_16bit_uint()
    elif datacode in ['i','l']:
        val = decoder.decode_32bit_int()
    elif datacode in ['I','L']:
        val = decoder.decode_32bit_uint()
    elif datacode == 'q':
        val = decoder.decode_64bit_int()
    elif datacode == 'Q':
        val = decoder.decode_64bit_uint()
    elif datacode == 'f':
        val = decoder.decode_32bit_float()
    elif datacode == 'd':
        val = decoder.decode_64bit_float()
    return val

def modbusRead(modbusCon, address, datacode, unitId, mode="holding", **kwargs):
    """
    lecture de données sur un périphérique modbus

    - modbusCon : connexion modbus établie
    - address : adresse à partir de laquelle la lecture doit commencer
    - datacode : type de données (h, H, i, l, I, L, q, Q, f, d)
    - unitId : numéro modbus du périphérique
    - mode : méthode de lecture (input, holding, discrete)

    2 cas de figures :
    - si le paramètre optionnel nb n'est pas précisé, on lit un seul datacode,
    - si nb est précisé, on lit un nombre de datacodes égal à nb

    On a modbus device :
    - input registers are read-only
    - holding registers are read and write and are the most universal registers
    - qd on lit des discrete inputs, on utilise le datacode h par abus de langage pour ne pas alourdir le code

    retourne :
    - un dictionnaire {"success": True/False, "text": message pour le log}
    - la valeur décodée ou le tableau des valeurs décodées

    """
    message = {}
    message["success"] = False
    val = float('nan')
    nb = valid_datacodes[datacode] if "nb" not in kwargs else int(kwargs["nb"])*valid_datacodes[datacode]
    if mode=="holding":
        rr=modbusCon.read_holding_registers(address,nb,unit=unitId)
    if mode=="input":
        rr=modbusCon.read_input_registers(address,nb,unit=unitId)
    if mode == "discrete" :
        rr=modbusCon.read_discrete_inputs(address,nb,unit=unitId)
    if rr.isError():
        message["text"] = "erreur de lecture - {}".format(rr)
    else :
        if nb != valid_datacodes[datacode]:
            val = []
            if mode == "discrete":
                for v in rr.bits :
                    val.append(v)
                message["success"] = True
            else:
                from struct import pack, unpack
                datas = b''.join(pack('!H',x) for x in rr.registers)
                # chaque registre occupe 2 octets
                for i in range(0,2*nb,2*valid_datacodes[datacode]):
                    val.append(unpack(">{}".format(datacode),datas[i:i+2])[0])
                message["success"] = True
                message["text"] = "modbus unit {} : {} registres ont été lus à compter de l'addresse {}".format(unitId, nb, address)
        else:
            if mode == "discrete":
                val = rr.bits[0]
                message["success"] = True
            else:
                try:
                    decoder = BinaryPayloadDecoder.fromRegisters(rr.registers, byteorder=Endian.Big, wordorder=Endian.Big)
                except Exception:
                    message["text"] = "modbus unit {} erreur de lecture sur registre {} : {}".format(unitId,address,rr)
                else:
                    val = decode(decoder, datacode)
                    message["success"] = True
                    message["text"] = "modbus unit {} le registre {} vaut {}".format(unitId,address,val)
    return message, val


def modbusWrite(modbusCon, address, datacode, unitId, value):
    """
    write a value to a given address(register) of a unit according a specified datacode

    return a dictionnary {"success": True or False, "text": message for logging
    """
    builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Big)

    if datacode == 'h':
        builder.add_16bit_int(value)
    elif datacode == 'H':
        builder.add_16bit_uint(value)
    elif datacode in ['i','l']:
        builder.add_32bit_int(value)
    elif datacode in ['I','L']:
        builder.add_32bit_uint(value)
    elif datacode == 'q':
        builder.add_64bit_int(value)
    elif datacode == 'Q':
        builder.add_64bit_uint(value)
    elif datacode == 'f':
        builder.add_32bit_float(value)
    elif datacode == 'd':
        builder.add_64bit_float(value)

    payload = builder.build()

    rq=modbusCon.write_registers(address,payload,skip_encode=True,unit=unitId)

    if rq.isError():
        return {"success": False, "text": "modbus unit {} erreur d'écriture sur registre {} : {}".format(unitId,address,rq)}
    else:
        return {"success": True, "text": "modbus unit {} > {:.2f}({}) écrit sur registre {}".format(unitId,value,datacode,address)}
