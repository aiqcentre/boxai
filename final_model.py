
import matplotlib.pyplot as plt
from sklearn.tree import ExtraTreeRegressor
import duckdb
import pandas as pd
import json
import numpy as np
from sklearn.model_selection import train_test_split, RandomizedSearchCV
from sklearn.metrics import mean_absolute_percentage_error, mean_squared_error, r2_score, make_scorer
import warnings
from boxoffice_preprocessor import BoxOfficePreprocessor
warnings.filterwarnings('ignore')

DB_PATH = 'data/numero.duckdb'

def get_data(limit=100):
    """
    Retrieve data from the DuckDB database.
    Args:
        limit: Number of rows to retrieve (unused).
    Returns:
        DataFrame containing the data from the first table in the database.
    """
    with duckdb.connect(DB_PATH) as con:
        table_name = con.execute("SHOW TABLES").fetchall()
        df = con.execute(f"SELECT * FROM {table_name[0][0]}").df()
    return df

def JSON_to_DF(df_json):
    """
    Convert a JSON DataFrame to a normalized DataFrame of films.
    Args:
        df_json: DataFrame containing JSON data with a 'data' column.
    Returns:
        DataFrame with expanded film features.
    """
    df = df_json.copy()
    df['films'] = df['data'].dropna().apply(lambda x: json.loads(x)['films'])
    df = df.explode('films').reset_index(drop=True)
    json_expanded = pd.json_normalize(df['films'])
    json_expanded.columns = [f"data.films.{col}" for col in json_expanded.columns]
    df = df.drop(columns=['data', 'films']).join(json_expanded)
    df.columns = [col.replace("data.films.", "") for col in df.columns]
    return df



def evaluate_predictions(y_true, y_pred, model_name):
    """
    Print evaluation metrics for model predictions.
    Args:
        y_true: True target values.
        y_pred: Predicted values.
        model_name: Name of the model for display.
    """
    mape = mean_absolute_percentage_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"\n{model_name} Metrics:")
    print(f"MAPE: {mape:.2%}")
    print(f"RMSE: {rmse:.2f}")
    print(f"R2 Score: {r2:.4f}")


df_json = get_data()
df = JSON_to_DF(df_json)
# Calculate total gross for each movie
df['total_gross'] = df['week.gross'].fillna(0) + df['weekend.gross'].fillna(0)

threshold = df['total_gross'].quantile(0.95)
df['category'] = df['total_gross'].apply(lambda x: 'Blockbuster' if x > threshold else 'Normal')
df = df[df['category'] == 'Normal']
df = df[df['openingDay.gross'].notna()]
# Use BoxOfficePreprocessor for all feature engineering
preprocessor = BoxOfficePreprocessor()
X, y = preprocessor.fit(df)
X = X.fillna(0)
# Calculate distributor_stats for OOP model
distributor_stats = {}
for name, group in df.groupby('distributorName'):
    mean_gross = group['total_gross'].mean()
    target_enc = group['total_gross'].mean()
    distributor_stats[name] = {'mean_gross': mean_gross, 'target_enc': target_enc}
param_dist = {
    'max_depth': [5, 10, 20, None],
    'min_samples_split': [2, 5, 10],
    'max_features': ['sqrt', 'log2', None]
}
mape_scorer = make_scorer(mean_absolute_percentage_error, greater_is_better=False)
print("\n=== Running Randomized Search for ExtraTreeRegressor (concurrent films model) ===")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
grid_search = RandomizedSearchCV(
    estimator=ExtraTreeRegressor(),
    param_distributions=param_dist,
    n_iter=20,
    scoring=mape_scorer,
    n_jobs=-1,
    verbose=1,
    random_state=42
)
grid_search.fit(X_train, y_train)
best_params = grid_search.best_params_
best_score = grid_search.best_score_
best_model = grid_search.best_estimator_
print(f"\nBest Parameters:")
for param, value in best_params.items():
    print(f"{param}: {value}")
print(f"\nBest MAPE: {-best_score:.4f}")
# Evaluate on test split

# Evaluate on test split
y_pred = best_model.predict(X_test)
y_test_orig = np.expm1(y_test)
y_pred_orig = np.expm1(y_pred)
evaluate_predictions(y_test_orig, y_pred_orig, "ExtraTreeRegressor - Test")

# K-Fold Cross Validation
from sklearn.model_selection import KFold
kf = KFold(n_splits=5, shuffle=True, random_state=42)
mape_scores, rmse_scores, r2_scores = [], [], []
print("\n=== K-Fold Cross Validation ===")
for fold, (train_idx, val_idx) in enumerate(kf.split(X)):
    X_train_cv, X_val_cv = X.iloc[train_idx], X.iloc[val_idx]
    y_train_cv, y_val_cv = y.iloc[train_idx], y.iloc[val_idx]
    model_cv = ExtraTreeRegressor(**best_model.get_params())
    model_cv.fit(X_train_cv, y_train_cv)
    y_pred_cv = model_cv.predict(X_val_cv)
    y_val_orig = np.expm1(y_val_cv)
    y_pred_orig_cv = np.expm1(y_pred_cv)
    mape = mean_absolute_percentage_error(y_val_orig, y_pred_orig_cv)
    rmse = np.sqrt(mean_squared_error(y_val_orig, y_pred_orig_cv))
    r2 = r2_score(y_val_orig, y_pred_orig_cv)
    mape_scores.append(mape)
    rmse_scores.append(rmse)
    r2_scores.append(r2)
    print(f"Fold {fold+1}: MAPE={mape:.2%}, RMSE={rmse:.2f}, R2={r2:.4f}")
print(f"\nMean MAPE: {np.mean(mape_scores):.2%}")
print(f"Mean RMSE: {np.mean(rmse_scores):.2f}")
print(f"Mean R2: {np.mean(r2_scores):.4f}")

# Save model and preprocessor to pickle
import pickle
with open('boxoffice_model.pkl', 'wb') as f:
    pickle.dump({
        'model': best_model,
        'preprocessor': preprocessor,
        'distributor_stats': distributor_stats
    }, f)
print("\nModel, preprocessor, and distributor_stats saved to boxoffice_model.pkl")
