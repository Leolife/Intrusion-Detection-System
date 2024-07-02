import psutil
import GPUtil
import time
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestMonitor:

    def __init__(self):
        usage_data = self.collect_usage_data()
        usage_data.to_csv("cpu_usage_data.csv", index=False)

        usage_data['timestamp'] = pd.to_datetime(usage_data['timestamp'], unit='s')
        usage_data.set_index('timestamp', inplace=True)
        self.usage_data_resampled = usage_data.resample('1min').mean()

        # Handle potential division by zero during normalization
        self.normalized_data = self.usage_data_resampled.copy()
        for column in self.normalized_data.columns:
            mean = self.normalized_data[column].mean()
            std = self.normalized_data[column].std()
            if std == 0:
                self.normalized_data[column] = 0  # or another appropriate value
            else:
                self.normalized_data[column] = (self.normalized_data[column] - mean) / std

        # Remove any remaining NaN values
        self.normalized_data = self.normalized_data.fillna(0)

        self.model = IsolationForest(contamination=0.01)  # small % to reduce false positives; subject to change
        self.model.fit(self.normalized_data)

    def collect_usage_data(self, duration=60, interval=5):
        data = []
        start_time = time.time()
        while time.time() - start_time < duration:
            timestamp = time.time()
            cpu_usage = psutil.cpu_percent(interval=1)
            mem_usage = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()
            net_usage = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # in MB
            try:  # ensure that there exists GPU(s) on the machine
                gpus = GPUtil.getGPUs()
                gpu_usage = gpus[0].load * 100 if gpus else 0
            except:
                gpu_usage = 0

            data.append((timestamp, cpu_usage, mem_usage, net_usage, gpu_usage))
            time.sleep(interval - 1)
        return pd.DataFrame(data, columns=["timestamp", "cpu_usage", "mem_usage", "net_usage", "gpu_usage"])

    def monitor_cpu_usage(self, threshold):  # threshold for a hard-coded % to take a snapshot
        new_data = []
        while True:
            current_time = pd.Timestamp.now()
            cpu_usage = psutil.cpu_percent(interval=1)
            mem_usage = psutil.virtual_memory().percent
            net_io = psutil.net_io_counters()
            net_usage = (net_io.bytes_sent + net_io.bytes_recv) / (1024 * 1024)  # in MB
            try:  # ensure that there exists GPU(s) on the machine
                gpus = GPUtil.getGPUs()
                gpu_usage = gpus[0].load * 100 if gpus else 0
            except:
                gpu_usage = 0

            current_usage = [cpu_usage, mem_usage, net_usage, gpu_usage]
            new_data.append((current_time, *current_usage))

            current_data_df = pd.DataFrame([current_usage],
                                           columns=['cpu_usage', 'mem_usage', 'net_usage', 'gpu_usage'])

            normalized_current = current_data_df.copy()
            for column in normalized_current.columns:
                mean = self.usage_data_resampled[column].mean()
                std = self.usage_data_resampled[column].std()
                if std == 0:
                    normalized_current[column] = 0
                else:
                    normalized_current[column] = (normalized_current[column] - mean) / std

            # Replace any infinite values with 0
            normalized_current = normalized_current.replace([np.inf, -np.inf], 0)

            # Fill any remaining NaN values with 0
            normalized_current = normalized_current.fillna(0)

            # Ensure the data is in the correct format for the model
            normalized_current_array = normalized_current.values.astype(np.float64)

            prediction = self.model.predict(normalized_current)

            latest_resampled = self.usage_data_resampled.iloc[-1]
            is_above_baseline = (current_data_df.values > latest_resampled.values).any()

            if is_above_baseline and (prediction == -1 or any(metric > threshold for metric in current_usage)):
                return f"Anomaly detected at {current_time}: {current_usage}"

            if len(new_data) >= 60:
                new_df = pd.DataFrame(new_data,
                                      columns=['timestamp', 'cpu_usage', 'mem_usage', 'net_usage', 'gpu_usage'])
                new_df.set_index('timestamp', inplace=True)
                self.retrain_model(new_df)
                new_data = []

    def retrain_model(self, new_data):
        combined_data = pd.concat([self.usage_data_resampled, new_data.resample('1min').mean()])

        # Handle potential division by zero during normalization
        self.normalized_data = combined_data.copy()
        for column in self.normalized_data.columns:
            mean = self.normalized_data[column].mean()
            std = self.normalized_data[column].std()
            if std == 0:
                self.normalized_data[column] = 0  # or another appropriate value
            else:
                self.normalized_data[column] = (self.normalized_data[column] - mean) / std

        # Replace any infinite values with 0
        self.normalized_data = self.normalized_data.replace([np.inf, -np.inf], 0)

        # Remove any remaining NaN values
        self.normalized_data = self.normalized_data.fillna(0)

        # Ensure the data is in the correct format for the model
        normalized_data_array = self.normalized_data.values.astype(np.float64)

        self.model.fit(normalized_data_array)
        self.usage_data_resampled = combined_data
        self.usage_data_resampled.to_csv("usage_data.csv", index=False)
        print("Model retrained with new data.")

    def begin_monitor(self):
        return self.monitor_cpu_usage(95)
