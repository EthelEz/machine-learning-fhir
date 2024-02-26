import pandas as pd
from pycaret.classification import load_model, predict_model
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from enum import Enum
import requests

from access_token import get_access_token
from dotenv import load_dotenv, find_dotenv
import asyncio

_ = load_dotenv(find_dotenv())

api_url = os.environ["api_url"]

# Define the FHIR API endpoint
FHIR_API_ENDPOINT = os.environ["api_url"]

# Create the FastAPI app
app = FastAPI()

# Load trained Pipeline
model = load_model("fhir_ethnicity_classifier")

# Pydantic models for request and response
class Patient_data(BaseModel):
    id: str
    name: dict
    code: str
    
class Observation_data(BaseModel):
    elapsed_time_days: float
    age: float
    gender: str
    race: str
    blood_leukocytes_volume: float
    blood_erythrocyte_volume: float
    blood_hemoglobin_volume: float
    blood_hematocrit_volume: float
    mcv_count: float
    mch_count: float
    mchc_count: float
    erythrocyte_distribution_width_count: float
    platelets_volume_count: float
    platelet_mean_volume_count: float

# Define an enum for prediction types
class PredictionEnum(str, Enum):
    Latino = "Hispanic or Latino"
    African = "Not Hispanic or Latino"

# Define output pydantic model with the Enum
class OutputModel(BaseModel):
    prediction: PredictionEnum

# Define predict function
@app.post("/predict", response_model=OutputModel)
def predict(data: Observation_data):
    """
    This is the endpoint that helps in testing the predicted model using Postman.
    """
    data_df = pd.DataFrame([data.dict()])
    predictions = predict_model(model, data=data_df)
    prediction_column = predictions.columns[14]  # Assuming the prediction column is the first column

    # Transform integer prediction to string based on conditions
    prediction_value = int(predictions[prediction_column].iloc[0])
    prediction_str = PredictionEnum.Latino if prediction_value == 1 else PredictionEnum.African

    return {"prediction": prediction_str}

@app.post("/send_to_fhir")
async def send_to_fhir(patient: Patient_data, observation: Observation_data):
    """
    This is the endpoint that helps send the predicted variable to the FHIR API.
    """

    token = await get_access_token()

    headers = {'Content-Type': 'application/json', 'authorization': f'Bearer {token}'}
    # Convert the input observation data into a DataFrame
    input_data = pd.DataFrame(observation.dict(), index=[0])
    
    # Make predictions using the loaded model
    predictions = predict_model(model, data=input_data)
    prediction_column = predictions.columns[14]  # Assuming the prediction column is the first column

    # Extract the predicted class label from the predictions
    prediction_value = int(predictions[prediction_column].iloc[0])
    prediction_str = PredictionEnum.Latino if prediction_value == 1 else PredictionEnum.African
    
    # Convert the prediction to FHIR-compliant format
    fhir_prediction = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "9279-2",
                    "display": "Prediction"
                }
            ]
        },
        "interpretation": [
            {
                "coding": [
                    {
                        "system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretationPrediction",
                        "code": "prediction",
                        "display": prediction_str
                    }
                ]
            }
        ]
    }

    # Add patient information to the FHIR-compliant prediction data
    fhir_prediction['subject'] = {
        "reference": f"Patient/{patient.id}"  # Accessing patient attributes directly
    }
    
    # Construct the conditional URL to check if the resource exists
    conditional_url = f"{FHIR_API_ENDPOINT}?subject=Patient/{patient.id}&code={patient.code}"
    
    # Check if the resource exists
    conditional_response = requests.get(conditional_url, headers=headers)

    patient_name = patient.name.get('firstname', 'Unknown')

    # If the resource doesn't exist, use POST to create it
    if conditional_response.json().get('total', 0) == 0:
        response = requests.post(FHIR_API_ENDPOINT, json=fhir_prediction, headers=headers)
        if response.status_code == 201:
            # Resource was created
            return {"message": f"Prediction data of {patient_name} successfully sent to FHIR API"}
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to create prediction data in FHIR API")
    
    # If the resource exists, use PUT to update it
    elif conditional_response.json().get('total', 0) != 0:
        resource_id = conditional_response.json()['entry'][0]['resource']['id']
        # Construct the URL with the resource ID
        put_url = f"{FHIR_API_ENDPOINT}/{resource_id}"
        fhir_prediction['id'] = resource_id
        response = requests.put(put_url, json=fhir_prediction, headers=headers)
        # print("PUT Request Response:", response.status_code, response.text)
        if response.status_code == 200:
            # Resource was updated successfully
            return {"message": f"Prediction data of {patient_name} successfully updated in FHIR API"}
        else:
            raise HTTPException(status_code=response.status_code, detail=f"Failed to update {patient_name} prediction data in FHIR API")
    
    else:
        # Other status codes (e.g., 4xx or 5xx) indicating an error
        raise HTTPException(status_code=500, detail="Unexpected error occurred while checking resource in FHIR API")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8005)
