import logging
import time
import os
from watchdog.observers.polling import PollingObserver
from .insomnia import Insomnia

class Watch:
    path = str(os.getenv('ROOT_PATH'))

    def sniff(self):
        logging.info(f"start watching directory {self.path!r}")
        event_handler = Insomnia()
        observer = PollingObserver()
        observer.schedule(event_handler, self.path, recursive=True)
        observer.start()
        try:
            while True:
                time.sleep(1)
        except Exception as e:
            logging.error(f"Error in observer loop: {e}")
        finally:
            observer.stop()
            observer.join()
