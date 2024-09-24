from os import getenv, stat, path, rename
from watchdog.events import FileSystemEventHandler
from datetime import datetime
from nite_howl import NiteHowl, minute
from utils.utils import Utils
import pandas as pd
import toml

class Insomnia(FileSystemEventHandler):
    def __init__(self) -> None:
        broker = getenv('BROKER')
        topic = getenv('TOPIC')
        group = getenv('GROUP')
        self.utils = Utils()
        self.howler = NiteHowl(broker, group, str(topic).split(","), "collector")

    def on_modified(self, event) -> None:
        minute.register("info", f"File modified: {stat(event.src_path)} AND {event}")

    def on_created(self, event) -> None:
        try:
            file_path = str(event.src_path)
            csv_split = file_path.split('/')
            self.registry = csv_split[2]
            if self.registry == ".deleted" and not event.is_directory and len(csv_split) < 4:
                return
            self.subregistry = csv_split[3]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_ext = file_path.split('.')[-1]
            new_file_name = f"{self.registry}_{timestamp}.{file_ext}"
            new_path = path.join('/'.join(csv_split[:-1]), new_file_name)
            rename(file_path, new_path)
            self.manipulate(new_path)
        except Exception as e:
            minute.register("error", f"Error handling created event: {e}")

    def on_deleted(self, event) -> None:
        minute.register("info", f"File deleted: {event}")
        
    def manipulate(self, path):
        ENV_PATH = getenv('ENV_PATH')
        with open(f"{ENV_PATH}/rocky.toml", "r") as file:
            config_file = toml.load(file)
            try:
                if (
                    self.registry != "vtigercrm"
                    and self.registry != "healthsherpa"
                    and self.registry in config_file
                ):
                    df = pd.read_csv(path)
                    df['issuer'] = self.registry
                    if len(config_file[self.registry]["id"]) > 1 and isinstance(
                        config_file[self.registry]["id"], list
                    ):
                        id = config_file[self.registry]["id"]
                        df = df.query(f"{id[0]} == {id[1]}")
                        id = config_file[self.registry]["id"][0]
                    else:
                        id = config_file[self.registry]["id"]
                    if len(config_file[self.registry]["date"]) > 1 and isinstance(
                        config_file[self.registry]["date"], list
                    ):
                        column = config_file[self.registry]["date"][0]
                        values = config_file[self.registry]["date"][1:]
                        last_day_current_month = self.utils.last_day_current_month()
                        last_day_of_two_months_ago = (
                            self.utils.last_day_two_months_ago()
                        )
                        query = " or ".join(
                            f"{column} == '{value}'" for value in values
                        )
                        df = df.query(query)
                        df_copy = df.copy()
                        df_copy[ "Paid Through Date"] = df_copy.apply(
                            lambda row: last_day_current_month
                            if row[column[1:-1]] == values[0]
                            else (
                                last_day_of_two_months_ago
                                if row[column[1:-1]] == values[1]
                                else None
                            ),
                            axis=1,
                        )
                        date = "Paid Through Date"
                    else:
                        date = config_file[self.registry]["date"]
                    if conditions := config_file.get(self.registry, {}).get("condition"):
                        for condition in conditions:
                            field_date = condition['column']
                            if field_date == 'End_Date':
                                df[field_date] = df[field_date].replace({'1/1/2099': self.utils.last_day_last_month()})
                            elif field_date == 'Broker Term Date':
                                df[field_date] = df[field_date].replace({'12/31/9999': self.utils.last_day_last_month()})
                        
                        df = df.query(
                            " & ".join(
                                [
                                    self.utils.condition_str(df, condition)
                                    for condition in conditions
                                    if config_file[self.registry]["condition"]
                                ]
                            )
                        )
                    df = df.drop_duplicates(subset=[id])
                # self.salesOrder(registry, df[[id, date]], script)
                    minute.register("info", "Prepare for sending")
                    self.howler.send("mask", msg=df, key=self.registry, headers = {"subregistry": self.subregistry})
            except Exception as e:
                raise e