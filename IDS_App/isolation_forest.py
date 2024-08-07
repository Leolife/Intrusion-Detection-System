import os
import psutil
import GPUtil
import time
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest


class IsolationForestMonitor:

    def __init__(self, load_existing=False):
        if load_existing and os.path.exists("usage_data.csv"):
            usage_data = self.load_usage_data()
        else:
            usage_data = self.collect_usage_data()
            usage_data.set_index('timestamp', inplace=True)

        # Save with index (timestamp) included
        usage_data.to_csv("usage_data.csv", index=True)

        self.usage_data = usage_data

        # Handle potential division by zero during normalization
        self.normalized_data = self.usage_data.copy()
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
        self.model.fit(self.normalized_data.values)

    def load_usage_data(self):
        usage_data = pd.read_csv("usage_data.csv")
        usage_data['timestamp'] = pd.to_datetime(usage_data['timestamp'])
        usage_data.set_index('timestamp', inplace=True)
        return usage_data

    def collect_usage_data(self, duration=3600, interval=5):  # anomaly detection will begin after the first duration
        data = []
        start_time = time.time()
        while time.time() - start_time < duration:
            timestamp = pd.Timestamp.now().floor('s')
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

    def monitor_usage(self, threshold, callback):  # threshold for a hard-coded % to take a snapshot
        new_data = []
        while True:
            current_time = pd.Timestamp.now().floor('s')
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
                mean = self.usage_data[column].mean()
                std = self.usage_data[column].std()
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

            prediction = self.model.predict(normalized_current_array)

            latest_resampled = self.usage_data.iloc[-1]
            if isinstance(gpu_usage, (int, float)):
                is_above_baseline = (current_data_df.values[0] > latest_resampled.values).any()
            else:
                # If GPU usage is "N/A" compare only CPU, Memory, Network
                is_above_baseline = (current_data_df.values[0][:3] > latest_resampled.values[:3]).any()

            threshold_exceeded = (  # only want to apply the threshold to CPU, memory, and GPU
                    cpu_usage > threshold or
                    mem_usage > threshold or
                    (isinstance(gpu_usage, (int, float)) and gpu_usage > threshold)
            )

            if threshold_exceeded or (is_above_baseline and prediction == -1):
                anomaly_message = (f"Anomaly detected at {current_time}: \n\tCPU: {cpu_usage}% "
                                   f"\n\tMemory: {mem_usage}% \n\tNetwork: {net_usage:.2f} MB "
                                   f"\n\tGPU: {gpu_usage}{'%' if isinstance(gpu_usage, (int, float)) else ''}")
                callback(anomaly_message)

            if len(new_data) >= 60:
                new_df = pd.DataFrame(new_data,
                                      columns=['timestamp', 'cpu_usage', 'mem_usage', 'net_usage', 'gpu_usage'])
                new_df.set_index('timestamp', inplace=True)
                self.retrain_model(new_df)
                new_data = []

            time.sleep(5)

    def retrain_model(self, new_data):
        # Replace 'N/A' with 0 in gpu_usage column
        new_data['gpu_usage'] = new_data['gpu_usage'].apply(lambda x: 0 if x == "N/A" else x)

        # Ensure gpu_usage is numeric
        new_data['gpu_usage'] = pd.to_numeric(new_data['gpu_usage'], errors='coerce')

        # Resample new data to match existing data
        #new_data_resampled = new_data.resample('1min').mean()

        # Combine with existing data (without resampling)
        combined_data = pd.concat([self.usage_data, new_data])

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
        self.usage_data = combined_data
        self.usage_data.to_csv("usage_data.csv", index=True)
        print(f"{pd.Timestamp.now()}: Model retrained with new data.\n")  # printed to terminal
        with open("retraining_logs.txt", "a") as file:
            file.write(f"{pd.Timestamp.now()}: Model retrained with new data.\n")

    def begin_monitor(self, callback):
        return self.monitor_usage(95, callback)
