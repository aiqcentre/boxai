import pickle
import numpy as np
import pandas as pd
class BoxOfficeModel:
    def __init__(self, model=None, preprocessor=None, distributor_stats=None):
        """
        Initialize the BoxOfficeModel with model, preprocessor, and distributor statistics.
        Args:
            model: Trained prediction model.
            preprocessor: Preprocessing object for input data.
            distributor_stats: Optional dictionary of distributor statistics.
        """
        self.model = model
        self.preprocessor = preprocessor
        self.distributor_stats = distributor_stats if distributor_stats is not None else {}

    def predict_from_json(self, input_json):
        """
        Predict box office gross from a JSON input.
        Args:
            input_json: Dictionary containing film features.
        Returns:
            Predicted gross as a float.
        """
        return self.predict_new_film(
            censorRating=input_json['censorRating'],
            distributorName=input_json['distributorName'],
            week_date=input_json['week_date'],
            concurrent_films=input_json.get('concurrent_films', [])
        )

    def prepare_input(self, censorRating, distributorName, week_date, concurrent_films):
        """
        Prepare input features for the model from film details and concurrent films.
        Args:
            censorRating: Film's censor rating.
            distributorName: Name of the distributor.
            week_date: Date of the week.
            concurrent_films: List of concurrent films with their features.
        Returns:
            Transformed features for prediction.
        """
        # Build a DataFrame for a single film, matching the expected input for the preprocessor
        row = {
            'censorRating': censorRating,
            'distributorName': distributorName,
            'week_date': week_date,
            'week.theatreCount': np.mean([f.get('week.theatreCount', 0) for f in concurrent_films]) if concurrent_films else 0,
            'week.screenCount': np.mean([f.get('week.screenCount', 0) for f in concurrent_films]) if concurrent_films else 0,
            'weekend.theatreCount': np.mean([f.get('week.theatreCount', 0) for f in concurrent_films]) if concurrent_films else 0,
            'weekend.screenCount': np.mean([f.get('week.screenCount', 0) for f in concurrent_films]) if concurrent_films else 0,
            'week.gross': np.mean([f.get('week.gross', 0) for f in concurrent_films]) if concurrent_films else 0,
            'weekend.gross': np.mean([f.get('weekend.gross', 0) for f in concurrent_films]) if concurrent_films else 0,
        }
        df = pd.DataFrame([row])
        X = self.preprocessor.transform(df)
        return X

    def predict_new_film(self, censorRating, distributorName, week_date, concurrent_films):
        """
        Predict the box office gross for a new film.
        Args:
            censorRating: Film's censor rating.
            distributorName: Name of the distributor.
            week_date: Date of the week.
            concurrent_films: List of concurrent films with their features.
        Returns:
            Predicted gross as a float.
        """
        X = self.prepare_input(censorRating, distributorName, week_date, concurrent_films)
        y_pred = self.model.predict(X)
        return float(np.expm1(y_pred[0]))

    def save(self, path):
        """
        Save the model, preprocessor, and distributor stats to a file.
        Args:
            path: File path to save the model.
        """
        with open(path, 'wb') as f:
            pickle.dump({
                'model': self.model,
                'preprocessor': self.preprocessor,
                'distributor_stats': self.distributor_stats
            }, f)

    @classmethod
    def load(cls, path):
        """
        Load a BoxOfficeModel from a file.
        Args:
            path: File path to load the model from.
        Returns:
            An instance of BoxOfficeModel.
        """
        with open(path, 'rb') as f:
            data = pickle.load(f)
        return cls(
            model=data['model'],
            preprocessor=data['preprocessor'],
            distributor_stats=data.get('distributor_stats', {})
        )

# Example usage for BoxOfficeModel
if __name__ == "__main__":
    model = BoxOfficeModel.load("boxoffice_model.pkl")
    input_json = {
        "censorRating": "PG",
        "distributorName": "Universal",
        "week_date": "2025-09-20",
        "concurrent_films": [
            {"week.gross": 100000, "weekend.gross": 50000, "week.theatreCount": 80, "week.screenCount": 120},
            {"week.gross": 80000, "weekend.gross": 40000, "week.theatreCount": 60, "week.screenCount": 90}
        ]
    }
    predicted_gross = model.predict_from_json(input_json)
    print(f"Predicted first week gross: ${predicted_gross:,.2f}")