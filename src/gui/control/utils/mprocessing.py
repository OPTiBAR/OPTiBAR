
import multiprocessing
import subprocess

class Subprocess(multiprocessing.Process):
    def __init__(self, out):
        multiprocessing.Process.__init__(self)
        self.out = out

    def run(self):
        subprocess.Popen(self.out, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.PIPE)