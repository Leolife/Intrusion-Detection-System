import os
import psutil
import pynvml
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
        self._fit_model(self.usage_data)

    def load_usage_data(self):
        usage_data = pd.read_csv("usage_data.csv")
        usage_data['timestamp'] = pd.to_datetime(usage_data['timestamp'])
        usage_data.set_index('timestamp', inplace=True)
        return usage_data

    def _compute_norm_stats(self, data_values):
        """Compute and cache mean/std as numpy arrays for fast normalization."""
        self._norm_mean = np.nanmean(data_values, axis=0)
        self._norm_std = np.nanstd(data_values, axis=0, ddof=1)
        # Avoid division by zero: where std is 0, set to 1 (result will be 0 - 0 / 1 = 0)
        self._norm_std[self._norm_std == 0] = 1.0

    def _normalize(self, values):
        """Z-score normalize using cached mean/std. Works on 1-D or 2-D arrays."""
        result = (values - self._norm_mean) / self._norm_std
        result = np.nan_to_num(result, nan=0.0, posinf=0.0, neginf=0.0)
        return result

    def _fit_model(self, data):
        """Compute normalization stats, normalize data, fit model, and set score threshold."""
        data_values = data.values.astype(np.float64)
        self._compute_norm_stats(data_values)
        normalized = self._normalize(data_values)

        self.model = IsolationForest(contamination='auto')
        self.model.fit(normalized)

        training_scores = self.model.decision_function(normalized)
        self.score_threshold = np.percentile(training_scores, 1)

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
                gpus = pynvml.getGPUs()
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
                gpus = pynvml.getGPUs()
                gpu_usage = gpus[0].load * 100 if gpus else 0
            except:
                gpu_usage = 0

            current_usage = [cpu_usage, mem_usage, net_usage, gpu_usage]
            new_data.append((current_time, *current_usage))

            current_array = np.array(current_usage, dtype=np.float64).reshape(1, -1)
            normalized_current_array = self._normalize(current_array)

            anomaly_score = self.model.decision_function(normalized_current_array)[0]

            threshold_exceeded = (  # only want to apply the threshold to CPU, memory, and GPU
                    cpu_usage > threshold or
                    mem_usage > threshold or
                    (isinstance(gpu_usage, (int, float)) and gpu_usage > threshold)
            )

            if threshold_exceeded or anomaly_score < self.score_threshold:
                anomaly_message = (f"Anomaly detected at {current_time} (score: {anomaly_score:.4f}): "
                                   f"\n\tCPU: {cpu_usage}% "
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

        self._fit_model(combined_data)
        self.usage_data = combined_data
        self.usage_data.to_csv("usage_data.csv", index=True)
        print(f"{pd.Timestamp.now()}: Model retrained with new data.\n")  # printed to terminal
        with open("retraining_logs.txt", "a") as file:
            file.write(f"{pd.Timestamp.now()}: Model retrained with new data.\n")

    def begin_monitor(self, callback):
        return self.monitor_usage(95, callback)
