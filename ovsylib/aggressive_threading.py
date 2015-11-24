from multiprocessing import Pool, Manager, cpu_count
from threading import Semaphore
from queue import Queue
import math

def getMaxThreads():
    return cpu_count()

def worker(func, args, sem):
    ret = func(*args)
    sem.release()
    return ret

class Broker:

    def __init__(self, max_needed_threads, greed=1, debugmode=False):
        """
        :param max_needed_threads: exactly what is says, to avoid wasting resources
        :param greed: multiplied with cpu_count(), gives the number of spawned subprocesses
        :param debugmode:
        """
        self.debugmode = debugmode
        self.maxthreads = min(math.ceil(getMaxThreads() * greed), max_needed_threads)
        self.threadcontrol = Queue()
        self.pool = Pool(processes=self.maxthreads)
        self.unid = 0
        self.freespots = Manager().Semaphore(self.maxthreads)

    def appendNfire(self, func, args):
        """ launch (runs in a subprocess) a function func, with arguments specified in the tuple args.
         :returns true upon success """
        try:
            self.freespots.acquire()
            assert isinstance(args, tuple)
            if self.debugmode:
                print("Spawning thread #%d" % self.unid)
            r = self.pool.apply_async(worker, [func, args, self.freespots])
            self.threadcontrol.put((self.unid, r))
            self.unid += 1
            return True
        except ValueError:
            self.freespots.release()
            return False

    def collect(self):
        """ generator of the launched functions' results, yields them in the same order as
         the function launching order """
        while not self.threadcontrol.empty():
            cnt = self.threadcontrol.get()
            r = cnt[1]
            res = r.get()
            if self.debugmode:
                print("Collecting thread #%d" % cnt[0])
            yield res

    def stop(self):
        """ closes the subthreads """
        self.pool.close()
        self.pool.join()

    def abort(self):
        """ kills the subthreads with fire """
        self.freespots.release()  # this will release a stuck appendNfire()
        self.pool.terminate()
        self.pool.join()