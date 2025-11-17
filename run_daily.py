#!/usr/bin/env python3
import json
import os
import datetime
from fitbit import Fitbit
import matplotlib.pyplot as plt
import numpy as np

import get_fitbit_data
import get_hevy_data_v2
import oldComponents.combine_datasets_v2 as combine_datasets_v2
import oldComponents.plot_combined_data as plot_combined_data
import combine_datasets_v3
import plot_combined_data_v2
import average
import notion
import compress
import llm
import gmail_controller

# ------------------------
# Main entry
# ------------------------
def main():

    print("Getting Fitbit Data")
    get_fitbit_data.main()

    print("Getting Hevy Data")
    get_hevy_data_v2.main()

    print("Combining datasets")
    combine_datasets_v3.main()

    print("Get Averages")
    average.get_averages()

    print("Uploading data to Notion")
    notion.push_averages()

    # print("Backfilling data to Notion")
    # notion.push_all_metrics()

    print("Uploading daily metrics")
    notion.push_daily_metrics()

    # print("Add missing days since last time run")
    # yesterday = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
    # print(yesterday)
    # notion.push_missing_metrics(yesterday)

    print("Compress previous data")
    compress.run_create_llm_payload()

    print("Send to LLM")
    llm.run_llm()

    print("Format response and send to email")
    gmail_controller.create_and_send_email()


    # print("Calculate one rep maxes")


    # print("Generating graphs and dashboard")
    # plot_combined_data_v2.main()
    

if __name__ == "__main__":
    main()
