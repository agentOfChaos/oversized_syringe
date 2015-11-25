def cmp_to_key(mycmp):
    'Convert a cmp= function into a key= function'
    class K(object):
        def __init__(self, obj, *args):
            self.obj = obj
        def __lt__(self, other):
            return mycmp(self.obj, other.obj) < 0
        def __gt__(self, other):
            return mycmp(self.obj, other.obj) > 0
        def __eq__(self, other):
            return mycmp(self.obj, other.obj) == 0
        def __le__(self, other):
            return mycmp(self.obj, other.obj) <= 0
        def __ge__(self, other):
            return mycmp(self.obj, other.obj) >= 0
        def __ne__(self, other):
            return mycmp(self.obj, other.obj) != 0
    return K

def asciicompare(fa, fb):
    a = fa.name
    b = fb.name
    stopat = min(len(a), len(b))
    for i in range(stopat):
        ai = a[i]
        bi = b[i]
        if ai == '_': ai = '~'
        if bi == '_': bi = '~'
        if ord(ai) < ord(bi):
            return -1
        elif ord(ai) > ord(bi):
            return 1
    if len(a) == len(b):
        return 0
    elif len(a) < len(b):
        return 1
    else:
        return -1