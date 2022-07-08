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
    import redis
except Exception as e :
    print(e)
else:
    print("redis-py : OK")
    r = redis.Redis(host="localhost", port=6379, db=0)
    promux = r.hmget("feed:14","value", "time")
    value = promux[0].decode()
    ts = promux[1].decode()
    print("{} W/m2".format(value))
    print("age : {}".format(ts))

print("<br><br><br>")
