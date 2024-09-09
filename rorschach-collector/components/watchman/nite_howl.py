from io import BytesIO
import pyarrow.csv as csv
import pyarrow.parquet as pq
from kafka import KafkaProducer

class NiteHowl:
    
    def __init__(self, broker, topic) -> None:
        self.broker = broker
        self.topic = topic
        self.producer = KafkaProducer(bootstrap_servers=broker)
    
    def package(self, dataframe) -> BytesIO:
        parquet_buffer = BytesIO()
        with pq.ParquetWriter(parquet_buffer, dataframe.schema) as writer:
            writer.write_table(dataframe)
            
        parquet_buffer.seek(0)
        return parquet_buffer
        
    def send(self, path):
        dataframe = csv.read_csv(path)
        parquet_buffer = self.package(dataframe)
        self.producer.send(self.topic, value=parquet_buffer.getvalue())
        self.producer.flush()
        