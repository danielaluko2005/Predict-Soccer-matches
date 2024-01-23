import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score,precision_score

matches=pd.read_csv("matches.csv",index_col=0)

print(matches.shape) #Prints how many row and columns is there.

# print(matches["team"].value_counts())

# print(matches.dtypes) #Gets the datatypes of each column.

matches["date"]=pd.to_datetime(matches["date"])

matches["venue_code"]=matches["venue"].astype("category").cat.codes #Converts it to a categorical datatype in canvas and would convert it to integers. So we are converting it to categories then converting it to numbers.

# This creates a new column (opp_code) and it would give every single opponent a category type then after it gives it a code.
matches["opp_code"]=matches["opponent"].astype("category").cat.codes

# Creates a new column called (time) then it converts the type to an integer buyt first replacing the chr(:) with an empty string.

matches["hour"]=matches["time"].str.replace(":.+","",regex=True).astype("int") #Change to integer type.

# Makes a new column (day_code) and makes it a day of the week data type .
matches["day_code"] = matches["date"].dt.dayofweek

# Selects each respective result and if it is a win or false it would save 1 or 0.
matches["target"]=(matches["result"]=="W".upper()).astype("int")

# Random Forest machine learning algorithm. It would get non-linear patterns.

# n_estimators: This parameter determines the number of trees in the random forest. In this case, it's set to 50, meaning the random forest will consist of 50 decision trees.

# min_samples_split: This parameter sets the minimum number of samples required to split an internal node. If a node has fewer samples than this value, it will not be split. In this case, it's set to 10.

# random_state: This parameter is used to seed the random number generator. It ensures reproducibility, meaning that if you run the same code with the same random_state, you'll get the same results. Here, it's set to 1.
rf=RandomForestClassifier(n_estimators=50,min_samples_split=10, random_state=1)

# Train with past data.
train=matches[matches["date"]<"2022-01-01"]
# Train with future data.
test=matches[matches["date"]>"2022-01-01"]

# This is what is being used to predict the outcome.
predictors=["venue_code","opp_code","hour","day_code"]

# This trains the data with each respective expected target and each respective match used to train the algorithm.
rf.fit(train[predictors],train["target"])

# Use the rf method predict to predict the final result.
preds=rf.predict(test[predictors])

# Check the accuracy score by passing the test data results and the predictions.
acc= accuracy_score(test["target"],preds) #To check the accuracy.  

combined=pd.DataFrame(dict(actual=test["target"],prediction=preds))

# print(dict(actual=test["target"],prediction=preds))

print(pd.crosstab(index=combined["actual"],columns=combined["prediction"]))

precision_score(test["target"],preds)

# Group by team and get_group named mancity.
grouped_matches=matches.groupby("team")
group=grouped_matches.get_group("Manchester City")

def rolling_averages(group,cols,new_cols):
    group=group.sort_values("date")
    # Check the form of the club in the last three games based on the stats in (col). The closed="left" ensures that it doesn't consider itslf.
    rolling_stats=group[cols].rolling(3,closed="left").mean()
    # Assigns the mean of the form from the past three games here.
    group[new_cols]=rolling_stats
    # Drop data with Nan data type in any of the new_cols columns.
    group =group.dropna(subset=new_cols)
    return group

cols = ["gf", "ga", "sh", "sot", "dist", "fk", "pk", "pkatt"]
new_cols = [f"{c}_rolling" for c in cols]

rolling_averages(group, cols, new_cols)

matches_rolling =matches.groupby("team").apply(lambda x:rolling_averages(x,cols,new_cols))

matches_rolling.droplevel('team')

matches_rolling.index=range(matches_rolling.shape[0])

def make_predictions(data, predictors):
    train = data[data["date"] < '2022-01-01']
    test = data[data["date"] > '2022-01-01']
    rf.fit(train[predictors], train["target"])
    preds = rf.predict(test[predictors])
    combined = pd.DataFrame(dict(actual=test["target"], predicted=preds), index=test.index)
    precision = precision_score(test["target"], preds)
    return combined, precision

combined, precision = make_predictions(matches_rolling, predictors + new_cols)
print(combined)

combined=combined.merge(matches_rolling[["date","team","opponent","result"]],left_index=True,right_index=True)

# MissingDict is defined as a subclass of dict. This means that MissingDict inherits all the methods and properties of the standard Python dictionary.

# __missing__ is a special method in Python dictionaries that is called when a key is not found. In this case, it's defined as a lambda function that takes self (the dictionary instance) and key (the missing key) as arguments. The lambda function simply returns the missing key itself.
class MissingDict(dict): 
    __missing__ = lambda self, key: key

map_values = {"Brighton and Hove Albion": "Brighton", "Manchester United": "Manchester Utd", "Newcastle United": "Newcastle Utd", "Tottenham Hotspur": "Tottenham", "West Ham United": "West Ham", "Wolverhampton Wanderers": "Wolves"} 
mapping = MissingDict(**map_values)


# combined["new_team"] = combined["team"].map(mapping): This line creates a new column in the combined DataFrame called "new_team". It uses the .map() method with the mapping dictionary (of type MissingDict) to replace values in the "team" column with their corresponding mapped values. If a team name is not found in the mapping, it will retain the original team name
combined["new_team"] = combined["team"].map(mapping)

merged = combined.merge(combined, left_on=["date", "new_team"], right_on=["date", "opponent"])

final_pred=merged[(merged["predicted_x"] == 1) & (merged["predicted_y"] ==0)]["actual_x"].value_counts()

print(final_pred)