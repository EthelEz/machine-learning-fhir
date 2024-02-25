from flask import Flask, request, jsonify
from pycaret.classification import load_model, predict_model
import pandas as pd
import requests
import uvicorn

from dotenv import load_dotenv, find_dotenv

_ = load_dotenv(find_dotenv())

app = Flask(__name__)

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
@app.route('/send_to_fhir', methods=['POST'])
async def send_to_fhir():
    # Get input data from the request
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Get input data and patient information from the request
    data = request.json
    patient_data = data.get('patient')
    observation_data = data.get('observation')
    
    # Convert the input observation data into a DataFrame
    input_data = pd.DataFrame(observation_data, index=[0])
    
    # Make predictions using the loaded model
    predictions = predict_model(model, data=input_data)
    
    # Extract the predicted class label from the predictions
    prediction_value = predictions.iloc[0][-1]  # Assuming the last column contains the predicted class label
    
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
              "display": "Hispanic or Latino" if prediction_value == 'Hispanic or Latino' else "Not Hispanic or Latino"
            }
          ]
        }
      ]
    }
    
    # Add patient information to the FHIR-compliant prediction data
    if patient_data:
        fhir_prediction['subject'] = {
            "reference": f"Patient/{patient_data.get('id')}"  # Assuming patient id is provided in the patient data
        }
    
    # Send the FHIR-compliant prediction data to the FHIR API
    response = requests.post(FHIR_API_ENDPOINT, json=fhir_prediction, headers=headers)
    
    # Check if the request was successful
    if response.status_code == 201:
        patient_name = patient_data.get('name').get('firstname') if patient_data.get('name') else 'Unknown'
        return jsonify({"message": f"Prediction data of {patient_name} successfully sent to FHIR API"})
    else:
        return jsonify({"message": "Failed to send prediction data to FHIR API"}), response.status_code

if __name__ == '__main__':
    app.run(debug=True)
