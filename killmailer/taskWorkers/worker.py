
from .models import Task
import threading
from django.utils import timezone
import logging

class Worker(object):
    log = logging.getLogger(__name__)

    def __init__(self, function, args=None):
        self.task = Task()
        self.task.save()
        self.started = False
        self.thread = None

        self.id = self.task.pk
        self.hash = self.task.hash

        self.function = function
        self.args=args

    def start(self):
        if(self.started):
            return
        self.started=True
        t = threading.Thread(target=self.__wrapper)
        t.setDaemon(True)
        self.thread=t
        self.task.started_at=timezone.now()
        self.task.status=Task.RUNNING
        self.task.save()
        t.start()

    def __wrapper(self):
        try:
            if self.args is None:
                self.function()
            else:
                self.function(*self.args)
        except Exception as ex:
            self.set_error(str(ex))
            self.log.exception('Exception occured in a task')
        self.finish()

    def set_progress(self, percent):
        self.task.progress=percent
        self.task.save()

    def set_error(self, error):
        self.task.has_error=True
        self.task.error=error
        self.task.save()

    def finish(self):
        self.task.status=Task.DONE
        self.task.finished_at=timezone.now()
        self.task.save()



        


