#!/usr/bin/env python3

print("hello")

print("my friend")

try:
   import redis
except Exception as e :
   print(e)


"""
try:
    r = redis.Redis(host="localhost", port=6379, db=0)
except Exception as e:
    print(e)
else:
    promux = r.hmget("feed:1","value", "time")
    value = promux[0].decode()
    ts = promux[1].decode()

    print(value)
    print(ts)
"""

print("fin")
