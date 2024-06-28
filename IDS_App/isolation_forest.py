import psutil
import time
import pandas as pd
from sklearn.ensemble import IsolationForest

def collect_cpu_usage(duration=3600, interval=5):
    
    data = []
    start_time = time.time()
    while time.time() - start_time < duration:
        timestamp = time.time()
        cpu_usage = psutil.cpu_percent(interval=1)
        data.append((timestamp, cpu_usage))
        time.sleep(interval - 1) 
    return pd.DataFrame(data, columns=["timestamp", "cpu_usage"])
print("Running")
cpu_data = collect_cpu_usage()
cpu_data.to_csv("cpu_usage_data.csv", index=False)

cpu_data['timestamp'] = pd.to_datetime(cpu_data['timestamp'], unit='s')
cpu_data.set_index('timestamp', inplace=True)
cpu_data_resampled = cpu_data.resample('1T').mean()  

model = IsolationForest(contamination=0.1)  
model.fit(cpu_data_resampled[['cpu_usage']])

def monitor_cpu_usage(model, threshold):
    new_data = []
    while True:
        current_time = pd.Timestamp.now()
        current_cpu_usage = psutil.cpu_percent(interval=1)
        new_data.append((current_time, current_cpu_usage))
        
        
        prediction = model.predict([[current_cpu_usage]])
        if prediction == -1 or current_cpu_usage > threshold:
            print(f"Anomaly detected at {current_time}: {current_cpu_usage}%")
            

        
        if len(new_data) >= 60:  
            new_df = pd.DataFrame(new_data, columns=['timestamp', 'cpu_usage'])
            new_df.set_index('timestamp', inplace=True)
            retrain_model(new_df, model)
            new_data = []  


def retrain_model(new_data, model):
    global cpu_data_resampled
    combined_data = pd.concat([historical_data_resampled, new_data.resample('1T').mean()])
    model.fit(combined_data[['cpu_usage']])
    cpu_data_resampled = combined_data  
    cpu_data_resampled.to_csv("cpu_usage_data.csv", index=False)
    print("Model retrained with new data.")


monitor_cpu_usage(model, threshold=80)