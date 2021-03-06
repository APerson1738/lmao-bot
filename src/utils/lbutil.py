import io
import json

### UTILITY FUNCTIONS ###

# Returns a list of valid prefix permutations
def get_permutations(prefix):
    prefixes = []
    prefixes.append(prefix[0].lower() + prefix[1:] + " ")
    prefixes.append(prefix[0].upper() + prefix[1:] + " ")
    prefixes.append(prefix.lower() + " ")
    prefixes.append(prefix.upper() + " ")
    prefixes.append(prefixes[0][:-1])
    prefixes.append(prefixes[1][:-1])
    prefixes.append(prefixes[2][:-1])
    prefixes.append(prefixes[3][:-1])
    return prefixes

# Utility function for finding the next occurrence of little_string in big_string after the index of n
def find_next(big_string, little_string, n):
    substr = big_string[n + 1:]
    return (substr.find(little_string) + len(big_string) - len(substr))

#TODO: Wait I feel like there's something built in that can do the same thing...
def find_nth(big_string, little_string, n):
    """Utility function for finding the nth occurrence of little_string in big_string"""
    index = big_string.find(little_string)
    for i in range(n - 1):
        if index == -1:
            return index
        index += big_string[index + 1:].find(little_string) + 1
    return index

# Returns a time dictionary with day, hour, minute, and second from t in seconds
def dhms_time(t):
    s = round(t)
    m = int(s / 60)
    s -= m * 60
    h = int(m / 60)
    m -= h * 60
    d = int(h / 24)
    h -= d * 24
    return {"d": d, "h": h, "m": m, "s": s}

# Returns an English message which displays time in days, hours, minutes, and seconds from t in seconds
def eng_time(t, seconds=True):
    t_msg = ""
    t_obj = dhms_time(t)
    d = t_obj["d"]
    h = t_obj["h"]
    m = t_obj["m"]
    s = t_obj["s"]
    if d > 0:
        t_msg += f"{d} day(s), "
    if seconds:
        if h > 0:
            t_msg += f"{h} hour(s), "
        if m > 0:
            t_msg += f"{m} minute(s) and "
        t_msg += f"{s} second(s)"
    else:
        if h > 0:
            t_msg += f"{h} hour(s) and "
        t_msg += f"{m} minute(s)"
    return t_msg

# Parses time from a string of characters, returning a dictionary containing different time categorizations
def parse_time(time: str):
    char_is_int = []
    t = ""
    for char in time:
        try:
            x = int(char)
            char_is_int.append(True)
        except ValueError:
            if char.strip() == "":
                continue
            else:
                char_is_int.append(False)
        t += char.lower()
    pos = {"d": t.find("d"), "h": t.find("h"), "m": t.find("m"), "s": t.find("s")}
    for key, value in pos.items():
        index = value
        if index < 1 or not char_is_int[index - 1]:
            index = find_next(t, key, index)
        pos[key] = index
    order = []
    for key, value in pos.items():
        if value >= 0:
            for i in range(0, len(order) + 1):
                if i == len(order):
                    order.append((key, value))
                    break
                if value < order[i][1]:
                    order.insert(i, (key, value))
                    break
    times = {"d": 0, "h": 0, "m": 0, "s": 0}
    for tup in order:
        num_str = ""
        for i in range(tup[1] - 1, -1, -1):
            if not char_is_int[i]:
                break
            num_str = t[i] + num_str
        try:
            times[tup[0]] = int(num_str)
        except ValueError:
            times[tup[0]] = 0

    return times

def get_seconds_from_dict(time: dict):
    return time["d"] * 24 * 60 * 60 + time["h"] * 60 * 60 + time["m"] * 60 + time["s"]

def get_emoji(name):
    """Gets an emoji's code listed in emojis.json by its name."""
    with io.open("../data/emojis.json") as f:
        emojis = json.load(f)
    return emojis.get(name)

def get_emoji_id(name):
    emoji = get_emoji(name)
    if emoji is None:
        return None
    colon = find_nth(emoji, ":", 2)
    bracket = emoji.find(">")
    return int(emoji[colon + 1:bracket])

def parse_chance(string):
    flag = "chance"
    chance_index = string.find(flag) + len(flag)
    try:
        chance = int(string[chance_index:].replace(".", " ").replace(",", "").split()[0])
        if chance > 100:
            chance = 100
        elif chance < 0:
            chance = 0
    except ValueError:
        chance = 50
    return chance

def print_duration(time, brackets=True):
    t = dhms_time(time)
    h = t["h"] + 24 * t["d"]
    m = str(t["m"])
    s = str(t["s"])
    if len(s) < 2:
        s = "0" + s
    m = str(m)
    if len(m) < 2:
        m = "0" + m
    if h > 0:
        out = f"{h}:{m}:{s}"
    else:
        out = f"{m}:{s}"
    if brackets:
        out = f"[{out}]"
    return out

def print_date(yyyymmdd):
    return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"

# Utility function for determining if an object is an integer
#def is_int(s):
#    try:
#        int(s)
#        return True
#    except ValueError:
#        return False
