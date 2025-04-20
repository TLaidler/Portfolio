import os
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
# from xgboost import XGBClassifier
from BorutaShap import BorutaShap

# load data
path = "C:/Users/thiago.cunha/Transfero/Asset Management - Gestora - Gestora/13 - Research/results"
main_df = os.path.join(
    path,
    'main_dataframe_06.csv'
)
scores_df = os.path.join(
    path,
    'scores_06.csv'
)

raw_X = pd.read_csv(main_df, sep=';')
raw_y = pd.read_csv(scores_df)

raw_y = (raw_y['score'] > 0).astype(bool)

# n_samples = 10_000
# random_indices = raw_X.sample(n=n_samples, random_state=42).index

X = raw_X.loc[:, :].iloc[:, 0:2]
y = raw_y.loc[:]

# some analysis
proportion = y.mean()
proportion

feature_selector = BorutaShap(
    importance_measure='shap',
    classification=True
)

# BorutaShap
feature_selector.fit(X=X, y=y, n_trials=20, random_state=0)

# result
feature_selector.plot(which_features='all',
                      X_size=8, figsize=(12, 8),
                      y_scale='log')

# result table
data = feature_selector.history_x.iloc[1:]
data['index'] = data.index
data = pd.melt(data, id_vars='index', var_name='Methods')

decision_mapper = feature_selector.create_mapping_of_features_to_attribute(
    maps=['Tentative', 'Rejected', 'Accepted', 'Shadow'])
data['Decision'] = data['Methods'].map(decision_mapper)
data.drop(['index'], axis=1, inplace=True)

stats_df = data.groupby('Methods').agg(
    meanImp=('value', 'mean'),
    medianImp=('value', 'mean'),
    minImp=('value', 'min'),
    MaxImp=('value', 'max'),
    Status=('Decision', 'first')
).reset_index()

stats_df = stats_df.sort_values(by='medianImp', ascending=False)

print(stats_df)

print('finished')