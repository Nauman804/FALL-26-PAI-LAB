import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


def load_data(train_path: str, test_path: str):
    """Load training and test datasets from CSV files."""
    train = pd.read_csv(train_path)
    test = pd.read_csv(test_path)
    return train, test


def perform_eda(df: pd.DataFrame, name: str = "Dataset", plot: bool = False):
    """Perform exploratory data analysis on a dataframe and print results.

    Args:
        df: the dataframe to analyze
        name: label used in printed headers
        plot: whether to render matplotlib figures (turn off for non-interactive runs)
    """
    print(f"\n=== EDA for {name} ===")
    print("Shape:", df.shape)
    print("Info:\n", df.info())
    print("Summary statistics:\n", df.describe(include='all'))
    print("Missing values:\n", df.isna().sum())

    if 'Transported' in df.columns:
        sns.countplot(x='Transported', data=df)
        plt.title('Target Distribution')
        if plot:
            plt.show()
        else:
            plt.clf()

    # correlation for numeric columns
    numeric = df.select_dtypes(include=[np.number])
    if not numeric.empty:
        corr = numeric.corr()
        plt.figure(figsize=(10, 8))
        sns.heatmap(corr, annot=True, fmt='.2f', cmap='coolwarm')
        plt.title('Correlation Matrix (numeric)')
        if plot:
            plt.show()
        else:
            plt.clf()


def feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """Create derived features that may help model performance.

    - Extract deck, number, and side from `Cabin`.
    - Compute total and log-transformed spend across entertainment categories.
    - Bin age into coarse groups and flag missing ages.
    - Create count features for planets/destinations and indicators for missing values.
    """
    df = df.copy()
    # cabin details
    df['Cabin'] = df['Cabin'].fillna('Unknown')
    df['CabinDeck'] = df['Cabin'].astype(str).str.split('/').str[0].str[0]
    df['CabinNum'] = df['Cabin'].astype(str).str.extract(r"(\d+)").astype(float)
    df['CabinSide'] = df['Cabin'].astype(str).str[-1]
    df['CabinNum_missing'] = df['CabinNum'].isna().astype(int)

    # surname / group features
    if 'Name' in df.columns:
        df['Surname'] = df['Name'].astype(str).str.split().str[-1]
        df['GroupSize'] = df.groupby('Surname')['Surname'].transform('count')
        df['IsAlone'] = (df['GroupSize'] == 1).astype(int)

    # spending features
    for c in ['RoomService', 'FoodCourt', 'ShoppingMall', 'Spa', 'VRDeck']:
        if c not in df.columns:
            df[c] = 0
    df['TotalSpend'] = (
        df['RoomService'].fillna(0)
        + df['FoodCourt'].fillna(0)
        + df['ShoppingMall'].fillna(0)
        + df['Spa'].fillna(0)
        + df['VRDeck'].fillna(0)
    )
    df['LogTotalSpend'] = np.log1p(df['TotalSpend'])

    # age groups
    df['Age_missing'] = df['Age'].isna().astype(int)
    df['AgeGroup'] = pd.cut(df['Age'], bins=[-1, 12, 18, 30, 50, 80, 120],
                             labels=['child', 'teen', 'young', 'adult', 'mid', 'senior'])

    # fill other missing categories and make missing indicators
    for cat in ['HomePlanet', 'Destination']:
        if cat in df.columns:
            df[f'{cat}_missing'] = df[cat].isna().astype(int)
            df[cat] = df[cat].fillna('Unknown')

    # frequency counts
    if 'HomePlanet' in df.columns:
        df['HomePlanet_count'] = df['HomePlanet'].map(df['HomePlanet'].value_counts())
    if 'Destination' in df.columns:
        df['Destination_count'] = df['Destination'].map(df['Destination'].value_counts())

    return df


def preprocess_data(df: pd.DataFrame, drop_target: bool = True):
    """Prepare features from dataframe by dropping unneeded columns and separating target.

    Returns:
        data: feature dataframe without target
        y: target series or None
    """
    data = df.copy()
    y = None
    if drop_target and 'Transported' in data.columns:
        y = data.pop('Transported')

    # apply engineering before removing source columns
    data = feature_engineering(data)

    # drop identifiers / high cardinality text
    for col in ['PassengerId', 'Name', 'Cabin']:
        if col in data.columns:
            data.drop(columns=[col], inplace=True)

    # fix boolean-like columns stored as string
    if 'CryoSleep' in data.columns:
        data['CryoSleep'] = data['CryoSleep'].map({'True': True, 'False': False})
    if 'VIP' in data.columns:
        data['VIP'] = data['VIP'].map({'True': True, 'False': False})

    return data, y


def build_preprocessor(df: pd.DataFrame, fit: bool = False, preprocessor=None):
    """Construct or apply a ColumnTransformer for numeric and categorical features.

    Args:
        df: raw feature dataframe
        fit: if True build and fit a new preprocessor, otherwise apply existing one.
        preprocessor: existing fitted transformer to use when fit=False.

    Returns:
        X_transformed: numpy array of transformed features
        df: original dataframe (unchanged)
        preprocessor: fitted transformer (when fit=True) or passed-in preprocessor
    """
    # determine columns
    num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'bool']).columns.tolist()

    numeric_transformer = Pipeline(
        steps=[
            ('imputer', SimpleImputer(strategy='median')),
            ('scaler', StandardScaler())
        ]
    )
    categorical_transformer = Pipeline(
        steps=[
            ('imputer', SimpleImputer(strategy='constant', fill_value='Missing')),
            # request dense output for compatibility with some classifiers
            # use sparse_output=False for newer sklearn versions
            ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
        ]
    )

    if fit or preprocessor is None:
        preprocessor = ColumnTransformer(
            transformers=[
                ('num', numeric_transformer, num_cols),
                ('cat', categorical_transformer, cat_cols)
            ], remainder='drop'
        )
        X_transformed = preprocessor.fit_transform(df)
    else:
        X_transformed = preprocessor.transform(df)

    return X_transformed, df, preprocessor


def split_data(X, y, test_size=0.2, random_state=42):
    """Split features and target into training and validation sets."""
    return train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)


def build_and_evaluate(models: dict, X_train, X_val, y_train, y_val):
    """Train given models and evaluate them, returning their results."""
    results = {}
    for name, model in models.items():
        print(f"\n-- Training {name} --")
        model.fit(X_train, y_train)
        preds = model.predict(X_val)
        acc = accuracy_score(y_val, preds)
        cm = confusion_matrix(y_val, preds)
        report = classification_report(y_train, model.predict(X_train))
        print(f"Accuracy on validation: {acc:.4f}")
        print("Confusion Matrix:\n", cm)
        print("Classification Report (train):\n", report)
        results[name] = {
            'model': model,
            'accuracy': acc,
            'confusion_matrix': cm
        }
    return results


from sklearn.model_selection import RandomizedSearchCV
from sklearn.model_selection import ParameterGrid
import random

def tune_model(model, param_grid, X, y, cv=3, scoring='accuracy'):
    """Perform hyperparameter search (grid or randomized) for a given model.

    If the total number of combinations exceeds 20, a randomized search with
    20 iterations is used to save time.
    """
    total = sum(1 for _ in ParameterGrid(param_grid))
    if total > 20:
        print(f"Grid has {total} combos; using RandomizedSearchCV with 20 iterations")
        search = RandomizedSearchCV(model, param_grid, cv=cv, scoring=scoring,
                                    n_iter=20, n_jobs=-1, random_state=42)
    else:
        search = GridSearchCV(model, param_grid, cv=cv, scoring=scoring, n_jobs=-1)

    search.fit(X, y)
    print(f"Best params: {search.best_params_}")
    print(f"Best score: {search.best_score_:.4f}")
    return search.best_estimator_


def train_final_and_predict(best_model, preprocessor, train_df, test_df):
    """Train best model on full training set and generate submission for test data."""
    # preprocess training set
    raw_X_full, y_full = preprocess_data(train_df, drop_target=True)
    X_full = preprocessor.transform(raw_X_full)
    best_model.fit(X_full, y_full)

    # preprocess test set using the fitted preprocessor
    raw_X_test, _ = preprocess_data(test_df, drop_target=False)
    X_test = preprocessor.transform(raw_X_test)

    preds = best_model.predict(X_test)
    submission = pd.DataFrame({'PassengerId': test_df['PassengerId'], 'Transported': preds})
    submission.to_csv('submission.csv', index=False)
    print("Submission file saved to submission.csv")


def main():
    train_path = 'train.csv'
    test_path = 'test.csv'

    train_df, test_df = load_data(train_path, test_path)

    perform_eda(train_df, name='Train')
    perform_eda(test_df, name='Test')

    # initial preprocessing to get raw feature dataframe and target
    raw_X, y = preprocess_data(train_df, drop_target=True)
    # build and fit preprocessor on raw training features
    X, _, preprocessor = build_preprocessor(raw_X, fit=True)
    X_train, X_val, y_train, y_val = split_data(X, y)

    # initialize models including lightgbm
    from lightgbm import LGBMClassifier
    models = {
        'LogisticRegression': Pipeline([
            ('clf', LogisticRegression(max_iter=1000, random_state=42))
        ]),
        'RandomForest': Pipeline([
            ('clf', RandomForestClassifier(random_state=42))
        ]),
        'GradientBoosting': Pipeline([
            ('clf', HistGradientBoostingClassifier(max_iter=100,
                                                   early_stopping=True,
                                                   random_state=42))
        ]),
        'LGBM': Pipeline([
            ('clf', LGBMClassifier(random_state=42))
        ])
    }

    results = build_and_evaluate(models, X_train, X_val, y_train, y_val)

    # hyperparameter grids for each model type – reduced sizes for faster tuning
    grids = {
        'RandomForest': {
            'clf__n_estimators': [100, 200],
            'clf__max_depth': [None, 10, 20],
        },
        'GradientBoosting': {
            'clf__learning_rate': [0.01, 0.05, 0.1],
            'clf__max_iter': [100, 200],
            'clf__max_depth': [3, 5]
        },
        'LogisticRegression': {
            'clf__C': [0.1, 1, 10],
            'clf__penalty': ['l2']
        },
        'LGBM': {
            'clf__n_estimators': [100, 200],
            'clf__learning_rate': [0.01, 0.05, 0.1],
            'clf__num_leaves': [31, 50]
        }
    }

    # limit tuning to top two baseline models
    sorted_baseline = sorted(results.items(), key=lambda kv: kv[1]['accuracy'], reverse=True)
    to_tune = [sorted_baseline[i][0] for i in range(min(2, len(sorted_baseline)))]
    print(f"\nModels selected for tuning: {to_tune}")

    tuned_models = {}
    tuned_scores = {}
    for name in to_tune:
        print(f"\nTuning {name}...")
        pipe = models[name]
        tuned = tune_model(pipe, grids[name], X_train, y_train)
        tuned_models[name] = tuned
        score = accuracy_score(y_val, tuned.predict(X_val))
        tuned_scores[name] = score
        print(f"Validation accuracy for tuned {name}: {score:.4f}")

    # select best and second-best
    best_name = max(tuned_scores, key=tuned_scores.get)
    second_name = sorted(tuned_scores, key=tuned_scores.get, reverse=True)[1]
    print(f"\nBest tuned model: {best_name} ({tuned_scores[best_name]:.4f})")
    print(f"Second-best tuned model: {second_name} ({tuned_scores[second_name]:.4f})")

    # build a voting ensemble of top two
    from sklearn.ensemble import VotingClassifier
    ensemble = VotingClassifier(
        estimators=[(best_name, tuned_models[best_name]),
                    (second_name, tuned_models[second_name])],
        voting='soft'
    )
    ensemble.fit(X_train, y_train)
    ensemble_score = accuracy_score(y_val, ensemble.predict(X_val))
    print(f"Voting ensemble validation accuracy: {ensemble_score:.4f}")

    # choose final model (ensemble if better)
    if ensemble_score > tuned_scores[best_name]:
        best_model = ensemble
        print(f"Ensemble selected as final model")
    else:
        best_model = tuned_models[best_name]
        print(f"Single model {best_name} selected as final model")

    # retrain on full data and predict with final pipeline
    train_final_and_predict(best_model, preprocessor, train_df, test_df)


if __name__ == '__main__':
    main()
