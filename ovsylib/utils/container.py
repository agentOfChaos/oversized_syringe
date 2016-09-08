

class HydraAgent:

    def notify(self, hydra):
        return


class HydraContainer:

    """
    Container for a value, useful for 2 uses:
    1) allow passing immutable types (i.e. integer) by reference
    2) keep a value synchronized among multiple users
    """

    def __init__(self, value):
        self._value = value
        self.observers = {}

    def __call__(self, *args, **kwargs):
        if len(args) == 0:
            return self.value
        elif len(args) == 1:
            self.value = args[0]

    @property
    def value(self):
        return self.value

    @value.setter
    def value(self, newval):
        self._value = newval
        self._notify_all()

    def _notify_all(self):
        for observer, remaining in self.observers.items():
            observer.notify(self)
            if remaining > 0:
                self.observers[observer] = remaining - 1
                if self.observers[observer] == 0:
                    self.unsubscribe(observer)

    def subscribe(self, observer, unsub_after=-1):
        assert isinstance(observer, HydraAgent)
        self.observers[observer] = unsub_after

    def unsubscribe(self, observer):
        if observer in self.observers.keys():
            del self.observers[observer]
            return True
        return False


class FileWriterCallback(HydraAgent):

    """
    Specific observer, that, when the observed HydraContainer is updated,
    writes the new value into a specific position inside a file, after processing
    the value with a formatfunction
    """

    def __init__(self, file, position, formatfunction):
        self.file = file
        self.position = position
        self.formatfunction = formatfunction

    def notify(self, hydra):
        savedseek = self.file.tell()
        self.file.seek(self.position)
        self.file.write(self.formatfunction(hydra.value))
        self.file.seek(savedseek)

