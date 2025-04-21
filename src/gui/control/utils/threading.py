from threading import Thread
from typing import Dict, Callable
import requests


class TaskThread(Thread):
    def __init__(self, fun, *args, **kwargs):
        super().__init__()
        self.daemon = True
        self.fun = fun
        self.args = args
        self.kwargs = kwargs
    def run(self):
        self.response = self.fun(*self.args, **self.kwargs)

def threaded(fun):
    """decorator function to run a function in another thread
    generates a new thread, runs the function in the new thread, and returns the thread

    Args:
        fun ([type]): the function to be run in the new thread
    """
    def inner_fun(*args, **kwargs) -> Thread:
        thread = TaskThread(fun, *args, **kwargs)
        thread.start()
        return thread
    return inner_fun

class Monitor():
    """to perform thread monitoring
    """
    def __init__(self, root) -> None:
        self.root = root
        self._stop = False
    
    def run(self, thread, fun, **kwargs):
        """
        to monitor the thread and run the fun by passing the response to it
        all the fun arguments should be passed as named arguments to this method
        the fun should get a response argument.

        Args:
            thread ([type]): the thread to be monitored
            fun ([type]): the function to be
        """
        def inner_fun():
            if thread.is_alive():
                self.root.after(200, lambda: inner_fun())
            elif not self._stop:
                response = thread.response
                fun(**kwargs, response = response)
        inner_fun()
    
    def stop(self):
        self._stop = True


@threaded    
def tr_request(method, url, json:Dict=None, headers:Dict= None):
    response = None
    try:
        response = getattr(requests, method)(url, json=json, headers=headers, timeout=5)
    except (requests.ConnectionError, requests.Timeout) as exception:
        pass
    return response
    