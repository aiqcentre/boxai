import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler, LabelEncoder

class BoxOfficePreprocessor:
    def __init__(self):
        """
        Initialize the BoxOfficePreprocessor with scaler, label encoders, and feature lists.
        """
        self.scaler = None
        self.le_censor = None
        self.le_dist = None
        self.numeric_columns = [
            'week.theatreCount', 'week.screenCount',
            'weekend.theatreCount', 'weekend.screenCount',
            'concurrent_mean_gross', 'concurrent_median_gross',
            'is_weekend', 'is_holiday',
            'distributor_mean_gross', 'distributor_target_enc'
        ]
        self.categorical_columns = ['week_month', 'week_dayofweek']
        self.feature_names = None

    def prepare_concurrent_features(self, df):
        """
        Prepare features for each film, including concurrent film statistics and date-based features.
        Args:
            df: DataFrame containing film data.
        Returns:
            DataFrame of processed features for each film.
        """
        df['first_week_gross'] = df['week.gross'].fillna(0) + df['weekend.gross'].fillna(0)
        features = []
        distributor_gross = df.groupby('distributorName')['first_week_gross'].mean().to_dict()
        distributor_target_enc = df.groupby('distributorName')['first_week_gross'].mean().to_dict()
        for idx, row in df.iterrows():
            date = row['releaseDate'] if 'releaseDate' in row else row.get('week_date', None)
            censor = row['censorRating']
            dist = row['distributorName']
            if 'releaseDate' in df:
                concurrent = df[(df['releaseDate'] == date) & (df.index != idx)]
            else:
                concurrent = df[(df['week_date'] == date) & (df.index != idx)]
            gross_list = concurrent['first_week_gross'].values if len(concurrent) > 0 else [0]
            week_dt = pd.to_datetime(date)
            is_weekend = int(week_dt.dayofweek >= 5)
            is_holiday = int(week_dt.strftime('%m-%d') in ['01-01', '12-25'])
            dist_mean_gross = distributor_gross.get(dist, 0)
            dist_target_enc = distributor_target_enc.get(dist, 0)
            features.append({
                'week.theatreCount': row.get('week.theatreCount', 0),
                'week.screenCount': row.get('week.screenCount', 0),
                'weekend.theatreCount': row.get('weekend.theatreCount', 0),
                'weekend.screenCount': row.get('weekend.screenCount', 0),
                'concurrent_mean_gross': np.mean(gross_list),
                'concurrent_median_gross': np.median(gross_list),
                'censorRating': censor,
                'distributorName': dist,
                'first_week_gross': row['first_week_gross'],
                'is_weekend': is_weekend,
                'is_holiday': is_holiday,
                'distributor_mean_gross': dist_mean_gross,
                'distributor_target_enc': dist_target_enc,
                'week_date': date
            })
        features_df = pd.DataFrame(features)
        return features_df

    def fit(self, df):
        """
        Fit the preprocessor on the input DataFrame and return processed features and target.
        Args:
            df: DataFrame containing training film data.
        Returns:
            X: Processed feature DataFrame.
            y: Target values (log-transformed first week gross).
        """
        features_df = self.prepare_concurrent_features(df)
        features_df['week_month'] = pd.to_datetime(features_df['week_date']).dt.month
        features_df['week_dayofweek'] = pd.to_datetime(features_df['week_date']).dt.dayofweek
        X_numeric = features_df[self.numeric_columns].copy()
        for col in ['concurrent_mean_gross', 'concurrent_median_gross', 'week.theatreCount', 'week.screenCount', 'weekend.theatreCount', 'weekend.screenCount', 'distributor_mean_gross', 'distributor_target_enc']:
            X_numeric[col] = np.log1p(X_numeric[col])
        self.scaler = StandardScaler()
        X_numeric[self.numeric_columns] = self.scaler.fit_transform(X_numeric[self.numeric_columns])
        X_categorical = pd.get_dummies(features_df[self.categorical_columns], columns=self.categorical_columns, prefix=['month', 'dow'])
        self.le_censor = LabelEncoder()
        self.le_dist = LabelEncoder()
        censor_enc = self.le_censor.fit_transform(features_df['censorRating'])
        dist_enc = self.le_dist.fit_transform(features_df['distributorName'])
        X_cat = pd.DataFrame({
            'censorRating_enc': censor_enc,
            'distributorName_enc': dist_enc
        })
        X = pd.concat([X_numeric, X_categorical, X_cat], axis=1)
        self.feature_names = X.columns.tolist()
        y = np.log1p(features_df['first_week_gross']) if 'first_week_gross' in features_df else None
        return X, y

    def transform(self, df):
        """
        Transform new data using the fitted preprocessor, matching training features.
        Args:
            df: DataFrame containing new film data.
        Returns:
            X: Processed feature DataFrame for prediction.
        """
        features_df = self.prepare_concurrent_features(df)
        features_df['week_month'] = pd.to_datetime(features_df['week_date']).dt.month
        features_df['week_dayofweek'] = pd.to_datetime(features_df['week_date']).dt.dayofweek
        X_numeric = features_df[self.numeric_columns].copy()
        for col in ['concurrent_mean_gross', 'concurrent_median_gross', 'week.theatreCount', 'week.screenCount', 'weekend.theatreCount', 'weekend.screenCount', 'distributor_mean_gross', 'distributor_target_enc']:
            X_numeric[col] = np.log1p(X_numeric[col])
        X_numeric[self.numeric_columns] = self.scaler.transform(X_numeric[self.numeric_columns])
        X_categorical = pd.get_dummies(features_df[self.categorical_columns], columns=self.categorical_columns, prefix=['month', 'dow'])
        censor_enc = self.le_censor.transform(features_df['censorRating'])
        dist_enc = self.le_dist.transform(features_df['distributorName'])
        X_cat = pd.DataFrame({
            'censorRating_enc': censor_enc,
            'distributorName_enc': dist_enc
        })
        X = pd.concat([X_numeric, X_categorical, X_cat], axis=1)
        # Add missing columns as zeros (for one-hot)
        for col in self.feature_names:
            if col not in X.columns:
                X[col] = 0
        X = X[self.feature_names]
        return X
