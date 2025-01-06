# -*- coding: utf-8 -*-
"""LSTM_HP_tuning_dataset.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1xTIb6RELI1wwliLZDs5upvgeOJyTduvQ
"""

!pip install --upgrade scikit-learn scikeras[tensorflow]
!pip install scikeras[tensorflow]

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.model_selection import train_test_split
from keras.models import Sequential
from keras.layers import LSTM, Dense, Dropout
import matplotlib.pyplot as plt

from google.colab import files


# Upload the dataset manually
uploaded = files.upload()

# Assuming the dataset is named 'stock_prices.csv'
df = pd.read_csv("HistoricalData_1736175120859.csv")
print(df.head())

data=df

# Assume 'Close' column contains the stock prices
target = df['Close/Last'].values

# Preprocess the data
data['Date'] = pd.to_datetime(data['Date'])
for col in ['Close/Last', 'Open', 'High', 'Low']:
    # Ensure the column is a string before applying .str.replace
    data[col] = data[col].astype(str).str.replace('$', '', regex=False).astype(float)

# Sort by date
data.sort_values(by='Date', inplace=True)

# Feature selection
features = ['Open', 'High', 'Low', 'Volume']
target = 'Close/Last'

# Normalize the data
scaler = MinMaxScaler()
# Ensure all columns are numeric and handle missing values
data[features + [target]] = data[features + [target]].apply(pd.to_numeric, errors='coerce')
data = data.dropna()  # Drop rows with NaN values
scaled_data = scaler.fit_transform(data[features + [target]])

# Prepare the sequences for LSTM
def create_sequences(data, seq_length):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length, :-1])
        y.append(data[i + seq_length, -1])
    return np.array(X), np.array(y)

sequence_length = 10  # Hyperparameter
data_sequences, target_sequences = create_sequences(scaled_data, sequence_length)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(data_sequences, target_sequences, test_size=0.2, random_state=42)

# Define the LSTM model
def build_lstm(optimizer='adam', dropout_rate=0.2, units=50):
    model = Sequential()
    model.add(LSTM(units=units, return_sequences=True, input_shape=(X_train.shape[1], X_train.shape[2])))
    model.add(Dropout(dropout_rate))
    model.add(LSTM(units=units))
    model.add(Dropout(dropout_rate))
    model.add(Dense(1))
    model.compile(optimizer=optimizer, loss='mean_squared_error')
    return model

# Hyperparameter tuning manually
param_grid = {
    'optimizer': ['adam', 'rmsprop'],
    'dropout_rate': [0.2, 0.3],
    'units': [50, 100],
    'batch_size': [16, 32],
    'epochs': [50, 100]
}

best_loss = float('inf')
best_params = None
best_model = None

for optimizer in param_grid['optimizer']:
    for dropout_rate in param_grid['dropout_rate']:
        for units in param_grid['units']:
            for batch_size in param_grid['batch_size']:
                for epochs in param_grid['epochs']:
                    print(f"Training with optimizer={optimizer}, dropout_rate={dropout_rate}, units={units}, batch_size={batch_size}, epochs={epochs}")
                    model = build_lstm(optimizer=optimizer, dropout_rate=dropout_rate, units=units)
                    model.fit(X_train, y_train, epochs=epochs, batch_size=batch_size, verbose=0)
                    loss = model.evaluate(X_test, y_test, verbose=0)
                    print(f"Loss: {loss}")

                    if loss < best_loss:
                        best_loss = loss
                        best_params = {
                            'optimizer': optimizer,
                            'dropout_rate': dropout_rate,
                            'units': units,
                            'batch_size': batch_size,
                            'epochs': epochs
                        }
                        best_model = model

print("Best parameters found: ", best_params)

# Predict
predicted = best_model.predict(X_test)

# Inverse transform to get actual values
# Create a dummy array to match the scaler's input shape for inverse transformation
dummy_features = np.zeros((predicted.shape[0], len(features)))  # Matching the feature columns
dummy_data = np.hstack((dummy_features, predicted.reshape(-1, 1)))

# Inverse transform to get actual predicted values
predicted_actual = scaler.inverse_transform(dummy_data)[:, -1]

# Similarly, process the test target values
dummy_test_features = np.zeros((y_test.shape[0], len(features)))
dummy_test_data = np.hstack((dummy_test_features, y_test.reshape(-1, 1)))
y_test_actual = scaler.inverse_transform(dummy_test_data)[:, -1]

# Plot results
plt.figure(figsize=(12, 6))
plt.plot(y_test_actual, label='Actual')
plt.plot(predicted_actual, label='Predicted')
plt.legend()
plt.title('LSTM Predictions vs Actual Data')
plt.show()