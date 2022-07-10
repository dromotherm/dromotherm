import numpy as np

from datetime import datetime
import time
#from dateutil import tz
from datetime import timezone
from datetime import timedelta
from datetime import tzinfo
import random

"""
timezone
"""
#UTC=tz.gettz('UTC')
UTC=timezone.utc
#CET=tz.gettz('Europe/Paris')
#LOCTZ = tz.gettz('Europe/Paris')
# cf https://docs.python.org/fr/3.6/library/datetime.html#datetime.tzinfo
# chercher datetime.tzinfo dans https://docs.python.org/3/library/datetime.html

ZERO = timedelta(0)
HOUR = timedelta(hours=1)
SECOND = timedelta(seconds=1)
#print(ZERO)
#print(SECOND)

STDOFFSET = timedelta(seconds = -time.timezone)
if time.daylight:
    DSTOFFSET = timedelta(seconds = -time.altzone)
else:
    DSTOFFSET = STDOFFSET

DSTDIFF = DSTOFFSET - STDOFFSET


class LocalTimezone(tzinfo):
    """
    A class capturing the platform's idea of local time.
    (May result in wrong values on historical times in
    timezones where UTC offset and/or the DST rules had
    changed in the past.)

    Cf https://docs.python.org/3/library/datetime.html
    """

    def fromutc(self, dt):
        assert dt.tzinfo is self
        stamp = (dt - datetime(1970, 1, 1, tzinfo=self)) // SECOND
        args = time.localtime(stamp)[:6]
        dst_diff = DSTDIFF // SECOND
        # Detect fold
        fold = (args == time.localtime(stamp - dst_diff))
        return datetime(*args, microsecond=dt.microsecond,
                        tzinfo=self, fold=fold)

    def utcoffset(self, dt):
        if self._isdst(dt):
            return DSTOFFSET
        else:
            return STDOFFSET

    def dst(self, dt):
        if self._isdst(dt):
            return DSTDIFF
        else:
            return ZERO

    def tzname(self, dt):
        return time.tzname[self._isdst(dt)]

    def _isdst(self, dt):
        tt = (dt.year, dt.month, dt.day,
              dt.hour, dt.minute, dt.second,
              dt.weekday(), 0, 0)
        stamp = time.mktime(tt)
        tt = time.localtime(stamp)
        return tt.tm_isdst > 0

LOCTZ = LocalTimezone()


"""
a classic week schedule

fixed working hours each day except saturday and sunday

start at 8 and stop at 17
"""
classic=np.array([ [8,17], [8,17], [8,17], [8,17], [8,17], [-1,-1], [-1,-1] ])

def tsToTuple(ts, tz=LOCTZ):
    """
    ts : unix time stamp en s
    tz : timezone as a datutil object

    return date tuple tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst
    """
    _time=datetime.fromtimestamp(ts, tz)
    _tuple=_time.timetuple()
    return(_tuple)

def tsToHuman(ts, fmt="%Y-%m-%d %H:%M:%S:%z", tz=LOCTZ):
    """
    format a timestamp to something readable by a human
    """
    return datetime.fromtimestamp(ts, tz).strftime(fmt)

def inPeriod(d,m,ps,pe):
    """
    ps : period start as "dd-mm"
    pe : period end
    d : day number in the month
    m : month number
    return boolean : True if day-month in period, False otherwise
    """
    inperiod = False
    ps = ps.split("-")
    pe = pe.split("-")
    # si moins d'un mois
    if int(ps[1]) == int(pe[1]):
        if m == int(ps[1]):
            if d >= int(ps[0]) and d <= int(pe[0]):
                inperiod = True
    # si plus d'un mois, 3 cas de figure
    else:
        if m == int(ps[1]) and d >= int(ps[0]):
            inperiod = True
        if m == int(pe[1]) and d <= int(pe[0]):
            inperiod = True
        if m > int(ps[1]) and m < int(pe[1]):
            inperiod = True
    return inperiod

def biosAgenda(nbpts, step, start, offs, schedule=classic):
    """
    un agenda plus abouti avec prise en compte de jours fériés, voire de périodes de confinement
    ```
    offs =  {
        "2019-offs": [ "01-01", "22-04", "01-05", "08-05", "30-05", "31-05", "10-06", "15-08", "16-08", "01-11", "11-11", ["23-12","25-12"] ],
        "2020-offs": [ "01-01", ["17-03","10-05"], "21-05", "22-05", "01-06", "13-07", "14-07", "11-11", "24-12", "25-12", "31-12"],
        "2021-offs": [ "01-01", "05-04", "13-05", "14-05", "24-05", "14-07", "01-11", "11-11", "12-11", "24-12", "31-12"]
        }
    ```
    """
    time = start
    agenda = np.zeros(nbpts)
    weekend = []
    for i in range(schedule.shape[0]):
        if -1 in schedule[i]:
            weekend.append(i)
    #print(weekend)
    for i in range(0,nbpts):
        tpl = tsToTuple(time)
        y = tpl.tm_year
        d = tpl.tm_mday
        m = tpl.tm_mon
        wd = tpl.tm_wday
        h = tpl.tm_hour
        horaires = schedule[wd]
        # valeur par défaut
        work = 1
        # on applique les jours off s'ils existent
        key = "{}-offs".format(y)
        if key in offs :
          for element in offs[key]:
            if isinstance(element,list):
                if inPeriod(d,m,element[0],element[1]):
                    work = 0
            else:
                off = element.split("-")
                if m == int(off[1]) and d == int(off[0]):
                    work = 0
        # on applique l'agenda hebdo
        if wd in weekend:
            work = 0
        if h not in range(horaires[0], horaires[1]):
            work = 0
        agenda[i] = work
        time+=step
    return agenda


def basicAgenda(nbpts,step,start,summerStart,summerEnd,schedule=classic):
    """
    The very first agenda function, indicating wether people are present or not : 1=work, 0=rest=nobody in the building

    nbpts : number of points the agenda will store

    step : time step in seconds

    start : starting unix time stamp in seconds

    summerStart,summerEnd : unix time stamps to define the summer period

    schedule : numpy array of size (7,2) with the presence hours for each day of the week

    returns : numpy vector of size nbpoints with activity indication (1: human presence , 0: no presence)

    utilisation :
    ```
    start = 1483232400

    summerStart = 1496278800

    summerEnd=1504141200

    step=3600

    nbpts=365*24 # un an avec une donnée à pas horaire

    schedule=np.array([ [6,17], [8,18], [8,17], [8,17], [8,17], [-1,-1], [-1,-1] ])

    agenda=basicAgenda(nbpts,step,start,summerStart,summerEnd,schedule=schedule)
    ```
    """

    verbose=False

    agenda=np.zeros(nbpts)
    time=start
    tpl=tsToTuple(time)
    work=0

    # do we have a summer ?
    summer=False
    if start<summerStart<summerEnd<=start+nbpts*step:
        summer=True
    #print("summer is {}".format(summer))

    # fetching which day of the week have no presence at all if any
    weekend=[]
    for i in range(schedule.shape[0]):
        if -1 in schedule[i]:
            weekend.append(i)

    if verbose:
        print(weekend)

    # initial condition
    horaires=schedule[tpl.tm_wday]
    if tpl.tm_hour in range(horaires[0],horaires[1]):
        if tpl.tm_wday not in weekend:
            work=1

    agenda[0]=work

    previous=tpl

    for i in range(1,nbpts):

        time+=step

        goToNexti=False

        if summer and time<=summerEnd and time>=summerStart:
            agenda[i]=0
            goToNexti=True

        if not goToNexti:
            tpl=tsToTuple(time)
            horaires=schedule[tpl.tm_wday]
            if verbose:
                print("we are day {}".format(tpl.tm_wday))
                print("{} vs {} and {} vs {}".format(tpl.tm_hour,horaires[1],previous.tm_hour,horaires[1]-1))
            if tpl.tm_hour>=horaires[1] and previous.tm_hour<=horaires[1]-1:
                if tpl.tm_wday not in weekend:
                    work=0
            if tpl.tm_hour>=horaires[0] and previous.tm_hour<=horaires[0]-1:
                if tpl.tm_wday not in weekend:
                    work=1
            agenda[i]=int(work)
            previous=tpl

        if verbose:
            print(agenda[i])
            input("press a key")

        #time+=step

    return agenda

def getLevelDuration(agenda, i):
    """
    return the supposed duration of the level in number of steps

    a level = period during which we can see no change in the agenda
    """
    j=i
    while(agenda[j]==agenda[j+1]):
        if j < agenda.shape[0]-2:
            j+=1
        else:
            break
    return j+1-i

def check_step(step):
    """
    vérifie le pas de temps, qui doit être un multiple ou un diviseur de 3600
    """
    if step < 3600 :
        r=3600%step
    if step >= 3600 :
        r=step%3600

    return r

"""
# quelques méthodes pour trouver l'heure précédant l'instant présent
now_ts=time.time()

# la plus évidente
now_tuple=tsToTuple(now_ts)
secsinceLH=now_tuple.tm_min*60+now_tuple.tm_sec
hb=int(now_ts)-secsinceLH
print(datetime.fromtimestamp(hb,LOCTZ))

# en passant par un objet de type date
hb=datetime.fromtimestamp(now_ts,LOCTZ)
hb=hb.replace(minute=0)
hb=hb.replace(second=0)
hb=hb.replace(microsecond=0)
print(hb)

# la plus tirée par les cheveux
hb="{}-{}-{}T{}:{}:{}".format('%02d' % now_tuple.tm_year ,
                              '%02d' % now_tuple.tm_mon,
                              '%02d' % now_tuple.tm_mday,
                              '%02d' % now_tuple.tm_hour,
                              '%02d' % 0,
                              '%02d' % 0)
_hb=datetime.strptime(hb, '%Y-%m-%dT%H:%M:%S')
_hb=_hb.replace(tzinfo=CET)
print(_hb)
"""
def tsToGrid(now_ts,step):
    """
    now_ts : timestamp unix en secondes

    step : pas de temps exprimé en secondes

    la grille de discrétisation est construite avec un pas de temps fixe égal à step

    Elle est calée pour contenir des heures entières

    retourne le point de la grille de discrétisation précédant l'instant donné now_ts
    """
    now_tuple = tsToTuple(now_ts)
    secSinceLastHour = now_tuple.tm_min*60+now_tuple.tm_sec
    lasth_ts = now_ts - secSinceLastHour

    if step < 3600:
        n=3600//step
        for i in range(n+1):
            dis=lasth_ts+i*step
            if  dis > now_ts:
                break
        start_ts=lasth_ts+(i-1)*step
    else:
        start_ts=lasth_ts

    return start_ts

def hmTots(now_ts, hm, tz=LOCTZ):
    """
    now_ts is a very recent unix time stamp we can provide to the method

    hm is the hour of the day as read in the schedule, for example, 17.25 is 17 h 15 min
    """
    hb=datetime.fromtimestamp(now_ts,tz)
    #print(hb)
    #print(hb.tzinfo)
    h = int(hm)
    nm = int(hm * 60)
    #print(nm)
    m = nm - 60*h
    #print(m)
    hb=hb.replace(hour=h)
    hb=hb.replace(minute=m)
    hb=hb.replace(second=0)
    hb=hb.replace(microsecond=0)
    #print(hb)
    return int(datetime.timestamp(hb))
    #return int(hb.strftime("%s"))


def checkStatus(now_ts,schedule,step):
    """
    renvoie un tag précisant le status : open, closed ou none
    le tag open indique l'arrivée du personnel sur le site
    le tag closed indique le départ du soir
    içi l'algorithme calcule les timestamps des horaires d'arrivée et de départ

    une autre méthode aurait pu être :
    ```
    prev_tuple =  tsToTuple(prev)
    if now_tuple.tm_hour == horaires[1] and prev_tuple.tm_hour == horaires[1]-1 :
        leave = True
    ```
    """
    prev = now_ts - step
    now_tuple = tsToTuple(now_ts)

    horaires = schedule[now_tuple.tm_wday]

    status = None
    if -1 not in horaires :
        open = hmTots(now_ts,horaires[0])
        closed = hmTots(now_ts,horaires[1])
        if now_ts >= open and prev < open:
            status = "open"
        if now_ts >= closed and prev < closed:
            status = "closed"

    #if status : print(now_ts,status,open,closed)
    return status

def getRandomStart(start, end, month_min, month_max, year=None):
    """
    tire aléatoirement un timestamp dans un intervalle
    s'assure que le mois du timestamp convient à la saison que l'on veut étudier (hiver, été)
    """
    while True:
        randomts = random.randrange(start, end)
        tpl = tsToTuple(randomts)
        if tpl.tm_mon <= month_max or tpl.tm_mon >=month_min:
            if year is None:
                break
            elif tpl.tm_year == year:
                break
    return randomts

def getContext(ts, common):
    """
    retourne les éléments de contexte au timestamp ts
    common est le dictionnaire des paramètres communs fourni à BIOS
    retourne un dictionnaire :
    {
      "season": "heating" ou "cooling",
      "off" : "yes" ou "no"
    }
    valeur par défaut si rien n'est précisé dans la rubrique common :
    {
      "season":"heating",
      "off":"no"
    }
    """
    tpl = tsToTuple(ts)
    m = tpl.tm_mon
    d = tpl.tm_mday
    out = { "season":"heating", "off":"no"}
    if "summer" in common:
        if inPeriod(d,m,common["summer"][0],common["summer"][1]):
            out["season"] = "cooling"
    # cas des jours fériés
    if "holidays" in common:
        for element in common["holidays"]:
            if isinstance(element, list):
                # on a une période de vacances, matérialisée par une liste
                if inPeriod(d,m,element[0],element[1]):
                    out["off"] = "yes"
            else:
                # on a un jour férié
                # off : day off
                off = element.split("-")
                if m == int(off[1]) and d == int(off[0]):
                    out["off"] = "yes"
    return out
