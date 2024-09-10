from os import getenv, stat, path, rename
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from nite_howl import NiteHowl
from .minute import minute, instropetion


class Insomnia(FileSystemEventHandler):
    def __init__(self) -> None:
        broker = getenv('BROKER')
        topic = getenv('TOPIC')
        group = getenv('GROUP')
        self.howler = NiteHowl(broker, topic, group)

    def on_modified(self, event) -> None:
        minute.register(f"File modified: {stat(event.src_path)} AND {event}")

    def on_created(self, event) -> None:
        try:
            file_path = str(event.src_path)
            csv_split = file_path.split('/')
            provider = csv_split[2]
            if provider == ".deleted" and not event.is_directory and len(csv_split) < 4:
                return
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = file_path.split('.')[-1]
            new_file_name = f"{provider}_{timestamp}.{file_ext}"
            new_file_path = path.join('/'.join(csv_split[:-1]), new_file_name)
            rename(file_path, new_file_path)
            self.howler.send(provider, path=new_file_path)
            minute.register(f"File: {new_file_path} send to broker.")
        except Exception as e:
            instropetion.register(f"Error handling created event: {e}")

    def on_deleted(self, event) -> None:
        minute.register(f"File deleted: {event}")