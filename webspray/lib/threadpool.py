import logging
import threading
from time import sleep
from queue import Queue, Empty

log = logging.getLogger('webspray.threadpool')


class ThreadPool:

    def __init__(self, max_workers=100, name=''):

        self.threads = int(max_workers)
        self.pool = [None] * self.threads
        self.name = name
        self.result_queue = Queue()


    @staticmethod
    def execute(func, result_queue, entry, *args, **kwargs):
        '''
        Executes given function and places return value in result queue
        '''

        try:

            if args is None:
                args = ()
            if kwargs is None:
                kwargs = {}

            try:
                result = func(entry, *args, **kwargs)
            except Exception as e:
                import traceback
                traceback.format_exc(e)


            try:
                if result:
                    result_queue.put(result)
            except Exception:
                pass

        except KeyboardInterrupt:
            pass


    def map(self, iterable, callback, name='', *args, **kwargs):

        for entry in iterable:

            for result in self.results:
                yield result

            extended_args = (entry,) + args
            self.submit(callback, name, *extended_args, **kwargs)

            for result in self.results:
                yield result

        # wait for threads to finish
        for result in self.results_wait():
            yield result


    def submit(self, callback, *args, name='', **kwargs):

        started = False
        while not started:
            for i,t in enumerate(self.pool):

                if t is None or not t.is_alive():
                    extended_args=(callback, self.result_queue) + args
                    self.pool[i] = threading.Thread(target=self.execute, name=f'{self.name}_{name}', args=extended_args, kwargs=kwargs)
                    self.pool[i].start()
                    started = True
                    break
            sleep(.01)



    @property
    def results(self):

        while 1:
            try:
                yield self.result_queue.get_nowait()
            except Empty:
                sleep(.01)
                break


    def results_wait(self):

        while 1:
            finished_threads = [t is None or not t.is_alive() for t in self.pool]
            for result in self.results:
                yield result
            if all(finished_threads):
                break
            for result in self.results:
                yield result
            else:
                sleep(.01)


    def __iter__(self):

        for result in self.results_wait():
            yield result


    def __enter__(self):

        return self


    def __exit__(self, exception_type, exception_value, traceback):
        '''
        Make sure the queue is empty before exiting
        '''

        try:
            while 1:
                try:
                    self.result_queue.get_nowait()
                except Empty:
                    break
        except:
            pass