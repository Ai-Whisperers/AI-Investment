"""
Pure mathematical ensemble methods for prediction.
Implements ensemble algorithms from scratch without sklearn dependencies.
Optimized for WebAssembly compilation.
"""

import numpy as np
from typing import List, Tuple, Callable, Optional
from ..core.types import (
    Features, Target, Targets, FeatureMatrix, ModelParameters,
    Prediction, Confidence, PredictionResult, ComputationalLimits
)


class SimpleBagging:
    """
    Pure mathematical implementation of bootstrap aggregating.
    No external ML library dependencies.
    """
    
    def __init__(self, n_estimators: int = 10, random_seed: Optional[int] = None):
        self.n_estimators = n_estimators
        self.random_seed = random_seed
        self.models: List[ModelParameters] = []
        self.fitted = False
        
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def fit(self, X: FeatureMatrix, y: Targets) -> None:
        """
        Train ensemble using bootstrap sampling.
        
        Args:
            X: Feature matrix (n_samples x n_features)
            y: Target values
        """
        if X.shape[0] != len(y):
            raise ValueError("X and y must have same number of samples")
        
        if X.shape[0] < 10:
            raise ValueError("Need at least 10 samples for ensemble training")
        
        self.models = []
        n_samples = X.shape[0]
        
        for _ in range(self.n_estimators):
            # Bootstrap sampling
            bootstrap_indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_bootstrap = X[bootstrap_indices]
            y_bootstrap = y[bootstrap_indices]
            
            # Train simple linear model on bootstrap sample
            model_params = self._fit_linear_model(X_bootstrap, y_bootstrap)
            self.models.append(model_params)
        
        self.fitted = True
    
    def predict(self, X: FeatureMatrix) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict using ensemble average.
        
        Args:
            X: Feature matrix for prediction
            
        Returns:
            Tuple of (predictions, confidence_scores)
        """
        if not self.fitted:
            raise ValueError("Model must be fitted before prediction")
        
        if X.shape[1] != len(self.models[0]) - 1:  # -1 for intercept
            raise ValueError("Feature dimension mismatch")
        
        # Get predictions from all models
        model_predictions = []
        for model_params in self.models:
            pred = self._predict_linear_model(X, model_params)
            model_predictions.append(pred)
        
        # Ensemble average
        model_predictions = np.array(model_predictions)
        ensemble_mean = np.mean(model_predictions, axis=0)
        ensemble_std = np.std(model_predictions, axis=0)
        
        # Confidence based on prediction agreement
        # Low std = high agreement = high confidence
        max_std = np.max(ensemble_std) if len(ensemble_std) > 0 else 1.0
        confidence_scores = 1.0 - (ensemble_std / (max_std + 1e-10))
        confidence_scores = np.clip(confidence_scores, 0.1, 1.0)
        
        return ensemble_mean, confidence_scores
    
    def _fit_linear_model(self, X: FeatureMatrix, y: Targets) -> ModelParameters:
        """
        Fit simple linear regression model.
        Pure mathematical implementation using normal equations.
        """
        # Add intercept term
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
        
        try:
            # Normal equations: theta = (X'X)^(-1) X'y
            XtX = X_with_intercept.T @ X_with_intercept
            Xty = X_with_intercept.T @ y
            
            # Add ridge regularization for numerical stability
            ridge_lambda = 1e-6
            XtX += ridge_lambda * np.eye(XtX.shape[0])
            
            theta = np.linalg.solve(XtX, Xty)
            return theta
            
        except np.linalg.LinAlgError:
            # Fallback: use pseudo-inverse
            theta = np.linalg.pinv(X_with_intercept) @ y
            return theta
    
    def _predict_linear_model(self, X: FeatureMatrix, theta: ModelParameters) -> np.ndarray:
        """Make predictions using linear model parameters."""
        X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
        return X_with_intercept @ theta


class SimpleRandomForest:
    """
    Pure mathematical random forest implementation.
    Simplified decision trees for investment prediction.
    """
    
    def __init__(self, n_estimators: int = 50, max_depth: int = 10, 
                 min_samples_split: int = 5, random_seed: Optional[int] = None):
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.trees: List[dict] = []
        self.fitted = False
        
        if random_seed is not None:
            np.random.seed(random_seed)
    
    def fit(self, X: FeatureMatrix, y: Targets) -> None:
        """Train random forest ensemble."""
        if X.shape[0] != len(y):
            raise ValueError("X and y dimension mismatch")
        
        self.trees = []
        n_samples, n_features = X.shape
        
        # Feature subsampling size (sqrt of total features)
        n_feature_subset = max(1, int(np.sqrt(n_features)))
        
        for _ in range(self.n_estimators):
            # Bootstrap sampling
            bootstrap_indices = np.random.choice(n_samples, size=n_samples, replace=True)
            X_bootstrap = X[bootstrap_indices]
            y_bootstrap = y[bootstrap_indices]
            
            # Random feature subset
            feature_indices = np.random.choice(n_features, size=n_feature_subset, replace=False)
            X_subset = X_bootstrap[:, feature_indices]
            
            # Train simple decision tree
            tree = self._build_tree(X_subset, y_bootstrap, feature_indices, depth=0)
            self.trees.append(tree)
        
        self.fitted = True
    
    def predict(self, X: FeatureMatrix) -> Tuple[np.ndarray, np.ndarray]:
        """Predict using random forest ensemble."""
        if not self.fitted:
            raise ValueError("Model must be fitted first")
        
        # Get predictions from all trees
        tree_predictions = []
        for tree in self.trees:
            pred = self._predict_tree(X, tree)
            tree_predictions.append(pred)
        
        # Ensemble average
        tree_predictions = np.array(tree_predictions)
        ensemble_mean = np.mean(tree_predictions, axis=0)
        ensemble_std = np.std(tree_predictions, axis=0)
        
        # Confidence based on prediction variance
        max_std = np.max(ensemble_std) if len(ensemble_std) > 0 else 1.0
        confidence_scores = 1.0 - (ensemble_std / (max_std + 1e-10))
        confidence_scores = np.clip(confidence_scores, 0.1, 1.0)
        
        return ensemble_mean, confidence_scores
    
    def _build_tree(self, X: FeatureMatrix, y: Targets, 
                   feature_indices: np.ndarray, depth: int) -> dict:
        """Build simple decision tree using recursive splitting."""
        
        # Stopping criteria
        if (depth >= self.max_depth or 
            len(y) < self.min_samples_split or 
            len(np.unique(y)) == 1):
            return {"type": "leaf", "value": np.mean(y)}
        
        # Find best split
        best_split = self._find_best_split(X, y)
        if best_split is None:
            return {"type": "leaf", "value": np.mean(y)}
        
        feature_idx, threshold = best_split
        
        # Split data
        left_mask = X[:, feature_idx] <= threshold
        right_mask = ~left_mask
        
        if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
            return {"type": "leaf", "value": np.mean(y)}
        
        # Recursive tree building
        left_tree = self._build_tree(X[left_mask], y[left_mask], feature_indices, depth + 1)
        right_tree = self._build_tree(X[right_mask], y[right_mask], feature_indices, depth + 1)
        
        return {
            "type": "split",
            "feature_idx": feature_indices[feature_idx],  # Map back to original feature index
            "threshold": threshold,
            "left": left_tree,
            "right": right_tree
        }
    
    def _find_best_split(self, X: FeatureMatrix, y: Targets) -> Optional[Tuple[int, float]]:
        """Find best feature and threshold for splitting."""
        best_score = float('inf')
        best_split = None
        
        n_features = X.shape[1]
        
        # Try each feature
        for feature_idx in range(n_features):
            feature_values = X[:, feature_idx]
            unique_values = np.unique(feature_values)
            
            # Try thresholds between unique values
            for i in range(len(unique_values) - 1):
                threshold = (unique_values[i] + unique_values[i + 1]) / 2
                
                # Calculate split quality (mean squared error reduction)
                left_mask = feature_values <= threshold
                right_mask = ~left_mask
                
                if np.sum(left_mask) == 0 or np.sum(right_mask) == 0:
                    continue
                
                # Calculate weighted MSE
                left_mse = np.var(y[left_mask]) if np.sum(left_mask) > 1 else 0
                right_mse = np.var(y[right_mask]) if np.sum(right_mask) > 1 else 0
                
                weighted_mse = (np.sum(left_mask) * left_mse + np.sum(right_mask) * right_mse) / len(y)
                
                if weighted_mse < best_score:
                    best_score = weighted_mse
                    best_split = (feature_idx, threshold)
        
        return best_split
    
    def _predict_tree(self, X: FeatureMatrix, tree: dict) -> np.ndarray:
        """Make predictions using a single tree."""
        predictions = np.zeros(X.shape[0])
        
        for i in range(X.shape[0]):
            predictions[i] = self._predict_sample(X[i], tree)
        
        return predictions
    
    def _predict_sample(self, sample: np.ndarray, tree: dict) -> float:
        """Predict single sample using tree."""
        if tree["type"] == "leaf":
            return tree["value"]
        
        # Navigate tree based on feature value
        if sample[tree["feature_idx"]] <= tree["threshold"]:
            return self._predict_sample(sample, tree["left"])
        else:
            return self._predict_sample(sample, tree["right"])


def create_ensemble_predictor(X: FeatureMatrix, y: Targets, 
                             ensemble_type: str = "bagging") -> Tuple[Callable, float]:
    """
    Factory function to create ensemble predictor.
    
    Args:
        X: Training features
        y: Training targets
        ensemble_type: Type of ensemble ("bagging" or "forest")
        
    Returns:
        Tuple of (predictor_function, training_accuracy)
    """
    if ensemble_type == "bagging":
        model = SimpleBagging(n_estimators=20)
    elif ensemble_type == "forest":
        model = SimpleRandomForest(n_estimators=30, max_depth=8)
    else:
        raise ValueError("Unknown ensemble type")
    
    # Train model
    model.fit(X, y)
    
    # Calculate training accuracy
    train_predictions, _ = model.predict(X)
    train_accuracy = 1.0 - np.mean(np.abs(train_predictions - y)) / np.std(y)
    train_accuracy = max(0.0, train_accuracy)
    
    # Return predictor function
    def predictor(features: FeatureMatrix) -> Tuple[np.ndarray, np.ndarray]:
        return model.predict(features)
    
    return predictor, train_accuracy