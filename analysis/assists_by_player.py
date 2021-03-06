import sys, os
assert sys.version_info >= (3, 5) # make sure we have Python 3.5+
from pyspark.sql import SparkSession, functions, types, Row
from pyspark import SparkConf, SparkContext
app_name = "NCAA Basketball"
spark = SparkSession.builder.appName(app_name).getOrCreate()
assert spark.version >= '2.3' # make sure we have Spark 2.3+
spark.sparkContext.setLogLevel('WARN')

# Main
def main(input, output):
    df = spark.read.parquet(input)

    # Assist Analysis
    df_score = df.filter((df['Action'] == 'Three Point Jumper') \
                         | (df['Action'] == 'Layup') \
                         | (df['Action'] == 'Two Point Jumper') \
                         | (df['Action'] == 'Dunk')) \
        .withColumn('ScoringPlayer', df['Player']) \
        .withColumn('ScoringAction', df['Action']) \
        .select('Year', 'Date', 'Seconds_Left', 'Division', 'Gender', 'Team', 'Action', 'ScoringPlayer', 'ScoringAction', 'File_Team')
    df_assist = df.filter(df['Action'] == 'Assist') \
        .withColumn('AssistingPlayer', df['Player']) \
        .select('Date', 'Seconds_Left', 'Division', 'Gender', 'Team', 'Action', 'AssistingPlayer', 'File_Team')
    df_joined = df_score.join(df_assist, ['Date', 'Seconds_Left', 'Division', 'Gender', 'Team', 'File_Team']) \
        .select('Gender','Division', 'Year', 'Team','ScoringAction', 'ScoringPlayer', 'AssistingPlayer')
    df_joined = df_joined.groupby('Gender','Division', 'Year', 'Team','ScoringPlayer', 'AssistingPlayer') \
        .agg(functions.count('*').alias('TotalAssists'))
    df_joined = df_joined.sort(df_joined['TotalAssists'].desc())

    # Can coalecse because there will only be a few hundred rows max
    df_joined.where(df_joined['TotalAssists'] > 50).coalesce(1).write.csv(output, mode='overwrite', header=True, compression='gzip')

if __name__ == '__main__':
    input = sys.argv[1]
    output = sys.argv[2]
    main(input, output)
