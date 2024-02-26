import pandas as pd
from pycaret.classification import load_model, predict_model
from fastapi import FastAPI, HTTPException
import uvicorn
from pydantic import BaseModel
from enum import Enum
import requests

from access_token import get_access_token

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

app = FastAPI()

# Load the trained model using PyCaret
model = load_model('fhir_ethnicity_classifier')

# Define the FHIR API endpoint
api_url = os.environ["api_url"]

# Define input pydantic model
class InputModel(BaseModel):
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
    African = "African"

# Define output pydantic model with the Enum
class OutputModel(BaseModel):
    prediction: PredictionEnum

# Define predict function
@app.post("/predict", response_model=OutputModel)
def predict(data: InputModel):
    data_df = pd.DataFrame([data.dict()])
    predictions = predict_model(model, data=data_df)
    prediction_column = predictions.columns[14]  # Assuming the prediction column is the first column

    # Transform integer prediction to string based on conditions
    prediction_value = int(predictions[prediction_column].iloc[0])
    prediction_str = PredictionEnum.Latino if prediction_value == 1 else PredictionEnum.African

    return {"prediction": prediction_str}

# Define the endpoint for sending data to the FHIR API
@app.post("/send_to_fhir")
async def send_to_fhir(patient: Patient, observation: Observation):
    # Get input data from the request
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get input data and patient information from the request
    input_data = pd.DataFrame(observation.dict(), index=[0])
    
    # Make predictions using the loaded model
    predictions = predict_model(model, data=input_data)
    prediction_column = predictions.columns[14]  # Assuming the prediction column is the first column

    # Extract the predicted class label from the predictions
    prediction_value = int(predictions[prediction_column].iloc[0])
    print(prediction_value)
    prediction_str = PredictionEnum.Latino if prediction_value == 1 else PredictionEnum.African
    
    # Convert the prediction to FHIR-compliant format
    fhir_prediction = {
        "resourceType": "Observation",
        "status": "final",
        "code": {
            "coding": [
                {
                    "system": "http://loinc.org",
                    "code": "9279-1",
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
        "reference": f"Patient/{patient.id}"
    }
    
    # Send the FHIR-compliant prediction data to the FHIR API
    response = requests.post(FHIR_API_ENDPOINT, json=fhir_prediction, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 201:
        patient_name = patient.name.get('firstname', 'Unknown')
        return {"message": f"Prediction data of {patient_name} successfully sent to FHIR API"}
    else:
        raise HTTPException(status_code=response.status_code, detail="Failed to send prediction data to FHIR API")

if __name__ == '__main__':
    uvicorn.run(app, host="127.0.0.1", port=8005)
