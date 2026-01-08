"""
Remaining Useful Life (RUL) Forecaster - Production-Ready Implementation

Uses LSTM/GRU for sequence-to-one prediction of remaining useful life.
Supports both cycle-based and time-based RUL estimation.
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import joblib


class RULDataset(Dataset):
    """PyTorch dataset for RUL sequences."""
    
    def __init__(
        self,
        sequences: np.ndarray,
        targets: np.ndarray
    ):
        self.sequences = torch.FloatTensor(sequences)
        self.targets = torch.FloatTensor(targets)
    
    def __len__(self):
        return len(self.sequences)
    
    def __getitem__(self, idx):
        return self.sequences[idx], self.targets[idx]


class LSTMForecaster(nn.Module):
    """LSTM-based RUL forecaster network."""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
    ):
        super().__init__()
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        
        self.fc = nn.Sequential(
            nn.Linear(hidden_size, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 1),
        )
    
    def forward(self, x):
        # x: (batch, seq_len, features)
        lstm_out, _ = self.lstm(x)
        # Take last timestep
        last_hidden = lstm_out[:, -1, :]
        # Predict RUL
        rul = self.fc(last_hidden)
        return rul.squeeze(-1)


class RULForecaster:
    """
    Production-ready RUL forecaster.
    
    Features:
    - LSTM-based sequence modeling
    - Configurable sequence length
    - Confidence intervals via dropout at inference
    - Model versioning and serialization
    """
    
    def __init__(
        self,
        sequence_length: int = 50,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.2,
        max_rul: float = 130.0,
        model_version: str = "1.0.0",
        device: Optional[str] = None,
    ):
        self.sequence_length = sequence_length
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.dropout = dropout
        self.max_rul = max_rul
        self.model_version = model_version
        
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        
        self.feature_scaler = StandardScaler()
        self.rul_scaler = MinMaxScaler(feature_range=(0, 1))
        
        self.model: Optional[LSTMForecaster] = None
        self.feature_names: List[str] = []
        self.is_fitted = False
        self.training_stats: Dict[str, Any] = {}
    
    def _create_sequences(
        self,
        df: pd.DataFrame,
        rul_column: str = "RUL"
    ) -> Tuple[np.ndarray, np.ndarray]:
        """Create sequences from dataframe."""
        feature_cols = [c for c in df.columns if c != rul_column]
        features = df[feature_cols].values
        rul = df[rul_column].values
        
        sequences = []
        targets = []
        
        for i in range(len(features) - self.sequence_length):
            seq = features[i:i + self.sequence_length]
            target = rul[i + self.sequence_length - 1]
            sequences.append(seq)
            targets.append(target)
        
        return np.array(sequences), np.array(targets)
    
    def fit(
        self,
        data: pd.DataFrame,
        rul_column: str = "RUL",
        epochs: int = 50,
        batch_size: int = 32,
        learning_rate: float = 0.001,
        validation_split: float = 0.2,
        verbose: bool = True,
    ) -> "RULForecaster":
        """
        Train the RUL forecaster.
        
        Args:
            data: Training data with features and RUL column
            rul_column: Name of the RUL target column
            epochs: Training epochs
            batch_size: Batch size
            learning_rate: Learning rate
            validation_split: Fraction for validation
            verbose: Print training progress
        
        Returns:
            Self for chaining
        """
        self.feature_names = [c for c in data.columns if c != rul_column]
        n_features = len(self.feature_names)
        
        # Scale features
        feature_data = data[self.feature_names].values
        scaled_features = self.feature_scaler.fit_transform(feature_data)
        
        # Scale RUL (clip to max)
        rul_data = np.clip(data[rul_column].values, 0, self.max_rul).reshape(-1, 1)
        scaled_rul = self.rul_scaler.fit_transform(rul_data).flatten()
        
        # Create combined dataframe
        scaled_df = pd.DataFrame(scaled_features, columns=self.feature_names)
        scaled_df[rul_column] = scaled_rul
        
        # Create sequences
        X, y = self._create_sequences(scaled_df, rul_column)
        
        # Split train/val
        split_idx = int(len(X) * (1 - validation_split))
        X_train, X_val = X[:split_idx], X[split_idx:]
        y_train, y_val = y[:split_idx], y[split_idx:]
        
        # Create data loaders
        train_dataset = RULDataset(X_train, y_train)
        val_dataset = RULDataset(X_val, y_val)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)
        
        # Initialize model
        self.model = LSTMForecaster(
            input_size=n_features,
            hidden_size=self.hidden_size,
            num_layers=self.num_layers,
            dropout=self.dropout,
        ).to(self.device)
        
        # Training setup
        criterion = nn.MSELoss()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=learning_rate)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            optimizer, mode="min", factor=0.5, patience=5
        )
        
        best_val_loss = float("inf")
        history = {"train_loss": [], "val_loss": []}
        
        # Training loop
        for epoch in range(epochs):
            # Train
            self.model.train()
            train_loss = 0.0
            for X_batch, y_batch in train_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                
                optimizer.zero_grad()
                predictions = self.model(X_batch)
                loss = criterion(predictions, y_batch)
                loss.backward()
                optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            
            # Validate
            self.model.eval()
            val_loss = 0.0
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    X_batch = X_batch.to(self.device)
                    y_batch = y_batch.to(self.device)
                    
                    predictions = self.model(X_batch)
                    loss = criterion(predictions, y_batch)
                    val_loss += loss.item()
            
            val_loss /= len(val_loader)
            
            scheduler.step(val_loss)
            
            history["train_loss"].append(train_loss)
            history["val_loss"].append(val_loss)
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f} - Val Loss: {val_loss:.4f}")
        
        # Store training stats
        self.training_stats = {
            "n_samples": len(data),
            "n_features": n_features,
            "sequence_length": self.sequence_length,
            "epochs": epochs,
            "final_train_loss": history["train_loss"][-1],
            "final_val_loss": history["val_loss"][-1],
            "best_val_loss": best_val_loss,
            "trained_at": datetime.utcnow().isoformat(),
            "model_version": self.model_version,
        }
        
        self.is_fitted = True
        return self
    
    def predict(
        self,
        sequences: np.ndarray,
        return_confidence: bool = True,
        n_samples: int = 10,
    ) -> Dict[str, Any]:
        """
        Predict RUL for sequences.
        
        Args:
            sequences: Array of shape (n_samples, sequence_length, n_features)
            return_confidence: Whether to return confidence intervals
            n_samples: Number of dropout samples for confidence
        
        Returns:
            Dictionary with predictions and confidence intervals
        """
        if not self.is_fitted or self.model is None:
            raise ValueError("Model not fitted. Call fit() first.")
        
        # Scale features
        original_shape = sequences.shape
        flat_features = sequences.reshape(-1, original_shape[-1])
        scaled_flat = self.feature_scaler.transform(flat_features)
        scaled_sequences = scaled_flat.reshape(original_shape)
        
        X = torch.FloatTensor(scaled_sequences).to(self.device)
        
        if return_confidence:
            # MC Dropout for uncertainty estimation
            self.model.train()  # Enable dropout
            predictions_list = []
            
            with torch.no_grad():
                for _ in range(n_samples):
                    pred = self.model(X).cpu().numpy()
                    predictions_list.append(pred)
            
            predictions_array = np.array(predictions_list)
            mean_pred = predictions_array.mean(axis=0)
            std_pred = predictions_array.std(axis=0)
            
            # Inverse transform
            mean_rul = self.rul_scaler.inverse_transform(mean_pred.reshape(-1, 1)).flatten()
            
            return {
                "rul_estimate": mean_rul.tolist(),
                "confidence_lower": (mean_rul - 1.96 * std_pred * self.max_rul).tolist(),
                "confidence_upper": (mean_rul + 1.96 * std_pred * self.max_rul).tolist(),
                "uncertainty": (std_pred * self.max_rul).tolist(),
                "model_version": self.model_version,
            }
        else:
            self.model.eval()
            with torch.no_grad():
                pred = self.model(X).cpu().numpy()
            
            rul = self.rul_scaler.inverse_transform(pred.reshape(-1, 1)).flatten()
            
            return {
                "rul_estimate": rul.tolist(),
                "model_version": self.model_version,
            }
    
    def predict_single(
        self,
        recent_data: pd.DataFrame,
    ) -> Dict[str, Any]:
        """
        Predict RUL for a single asset given its recent data.
        
        Args:
            recent_data: DataFrame with recent metrics (at least sequence_length rows)
        
        Returns:
            RUL prediction with confidence
        """
        if len(recent_data) < self.sequence_length:
            return {
                "error": f"Need at least {self.sequence_length} data points",
                "rul_estimate": None,
            }
        
        # Take last sequence_length rows
        sequence = recent_data[self.feature_names].tail(self.sequence_length).values
        sequence = sequence.reshape(1, self.sequence_length, -1)
        
        return self.predict(sequence)
    
    def save(self, path: str) -> None:
        """Save model to disk."""
        model_data = {
            "model_state_dict": self.model.state_dict() if self.model else None,
            "feature_scaler": self.feature_scaler,
            "rul_scaler": self.rul_scaler,
            "feature_names": self.feature_names,
            "training_stats": self.training_stats,
            "model_version": self.model_version,
            "sequence_length": self.sequence_length,
            "hidden_size": self.hidden_size,
            "num_layers": self.num_layers,
            "dropout": self.dropout,
            "max_rul": self.max_rul,
        }
        torch.save(model_data, path)
    
    @classmethod
    def load(cls, path: str, device: Optional[str] = None) -> "RULForecaster":
        """Load model from disk."""
        model_data = torch.load(path, map_location="cpu")
        
        forecaster = cls(
            sequence_length=model_data["sequence_length"],
            hidden_size=model_data["hidden_size"],
            num_layers=model_data["num_layers"],
            dropout=model_data["dropout"],
            max_rul=model_data["max_rul"],
            model_version=model_data["model_version"],
            device=device,
        )
        
        forecaster.feature_scaler = model_data["feature_scaler"]
        forecaster.rul_scaler = model_data["rul_scaler"]
        forecaster.feature_names = model_data["feature_names"]
        forecaster.training_stats = model_data["training_stats"]
        
        n_features = len(forecaster.feature_names)
        forecaster.model = LSTMForecaster(
            input_size=n_features,
            hidden_size=forecaster.hidden_size,
            num_layers=forecaster.num_layers,
            dropout=forecaster.dropout,
        ).to(forecaster.device)
        
        forecaster.model.load_state_dict(model_data["model_state_dict"])
        forecaster.is_fitted = True
        
        return forecaster
