#!/usr/bin/env python3

print("hello")

print("my friend")
try:
    import pymodbus
except Exception as e:
    print(e)
else:
    print("pymodbus is here")
 
try:
    import numpy as np
except Exception as e:
    print(e)
else:
    print("numpy is here")

try:
    import redis
except Exception as e :
    print(e)
else:
    print("redis-py also :-)")
    r = redis.Redis(host="localhost", port=6379, db=0)
    promux = r.hmget("feed:1","value", "time")
    value = promux[0].decode()
    ts = promux[1].decode()
    print(value)
    print(ts)

print("fin")
