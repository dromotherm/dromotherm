#!/usr/bin/env python3

try:
    import pymodbus
except Exception as e:
    print(e)
else:
    print("pymodbus : OK")
 
try:
    import numpy as np
except Exception as e:
    print(e)
else:
    print("numpy : OK")

try:
    import click, redis
except Exception as e:
    print(e)
else:
    @click.command()
    @click.option('--nb', type=int, default=14, prompt='numéro du flux PHPFINA')
    def getLastValue(nb):
        r = redis.Redis(host="localhost", port=6379, db=0)
        promux = r.hmget("feed:{}".format(nb),"value", "time")
        value = promux[0].decode()
        ts = promux[1].decode()
        print("valeur lue dans redis : {}".format(value))
        print("age selon redis : {} s".format(ts))
    print("redis-py : OK")
    print("click@pallets : OK")
    getlastValue()
 
print("<br><br><br>")
