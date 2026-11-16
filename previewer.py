import pandas as pd

rows = []
for chunk in pd.read_csv("changelog.csv",
                         usecols=["key", "created", "field", "fromString", "toString"],
                         chunksize=500_000):
    rows.append(chunk[chunk["field"].isin(["labels", "Sprint"])])
ev = pd.concat(rows)

# A. Label removals: fromString set, toString empty
removals = ev[(ev.field == "labels") & ev.fromString.notna() & ev.toString.isna()]
print("label removals:", len(removals))
print(removals.head(5).to_string())

# B. Sprint names containing a comma (would break a comma split)
sprints = ev[ev.field == "Sprint"].toString.dropna()
print("sprint values with >1 comma-separated name:", sprints.str.contains(",").sum())