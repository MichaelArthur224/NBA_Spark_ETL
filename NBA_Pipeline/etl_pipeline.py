from nba_api.stats.static import players
from nba_api.stats.endpoints import playergamelog
from pyspark.sql import SparkSession
from pyspark.sql.functions import avg, max, min, stddev
from pyspark.sql.window import Window
from pyspark.sql.functions import avg as spark_avg
import pandas as pd
import os

# Load Spark
def get_spark():
    return SparkSession.builder \
        .appName("NBA Spark ETL") \
        .master("local[*]") \
        .config("spark.ui.showConsoleProgress", "false") \
        .getOrCreate()

# ETL Function
def run_etl(player_name, season="2024-25"):
    spark = get_spark()
    spark.sparkContext.setLogLevel("ERROR")

    # Find Players
    player = players.find_players_by_full_name(player_name)
    if not player:
        raise Exception(f"Player not found: {player_name}")
    player_id = player[0]["id"]

    # Pull From NBA API
    gamelog = playergamelog.PlayerGameLog(
        player_id=player_id,
        season=season
    )
    df = gamelog.get_data_frames()[0]
    # Create Spark Dataframe
    spark_df = spark.createDataFrame(df)
    spark_df = spark_df.select(
        "GAME_DATE",
        "MATCHUP",
        "PTS",
        "REB",
        "AST"
    )

    # Create Rolling Average
    window = Window.orderBy("GAME_DATE").rowsBetween(-4, 0)
    spark_df = spark_df.withColumn(
        "rolling_5_avg_pts",
        spark_avg("PTS").over(window)
    )

    # Get All Stats
    summary_df = spark_df.agg(
        avg("PTS").alias("avg_pts"),
        avg("REB").alias("avg_reb"),
        avg("AST").alias("avg_ast"),
        max("PTS").alias("career_high"),
        min("PTS").alias("career_low"),
        stddev("PTS").alias("consistency")
    )

    # Clean Player_key
    player_key = player_name.strip().replace(" ", "_").lower()
    os.makedirs("data/lake", exist_ok=True)
    game_path = f"data/lake/{player_key}_games.csv"
    summary_path = f"data/lake/{player_key}_summary.csv"
    # Convert to Pandas
    games_pd = spark_df.toPandas()
    summary_pd = summary_df.toPandas()

    # Format Data
    games_pd["rolling_5_avg_pts"] = games_pd["rolling_5_avg_pts"].round(2)
    summary_cols = ["avg_pts", "avg_reb", "avg_ast", "consistency"]
    summary_pd[summary_cols] = summary_pd[summary_cols].round(2)
    summary_pd["career_high"] = summary_pd["career_high"].round(2)
    summary_pd["career_low"] = summary_pd["career_low"].round(2)

    # Save Files
    games_pd.to_csv(game_path, index=False)
    summary_pd.to_csv(summary_path, index=False)

    return player_key