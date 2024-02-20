import asyncio
import os

from access_token import get_access_token
from extract import extract_from_fhir_api

import pandas as pd
from pycaret.classification import *

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

async def main():

    bearer_token = await get_access_token()

    api_url = os.environ["api_url"]

    # Call the extract_from_fhir_api function to extract data
    df = await extract_from_fhir_api(api_url, bearer_token)
    # df.to_csv("fhir_data_modified.csv")

    # Now you have a DataFrame containing the extracted data
    # print(data_df.head())  # Example: Print the first few rows of the DataFrame
    cat_features = ['gender', 'race']

    experiment = setup(data = df, target = 'ethnicity', categorical_features = cat_features)

    best_model = compare_models()

    predict_model(best_model, df.tail())

    save_model(best_model, model_name='fhir_ethnicity_classifier')

if __name__ == "__main__":
    # Run the main function asynchronously
    asyncio.run(main())