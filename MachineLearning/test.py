import json
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained("ealvaradob/bert-finetuned-phishing")
model = AutoModelForSequenceClassification.from_pretrained("ealvaradob/bert-finetuned-phishing")

# Load the input file
with open("C:\\Users\\Branden\\MobilePhishingProject\\output_data\\1uAdSmiL_All_Targets\\0a4d6721462424a1dd3fd339c7fa0ce70c975cda\\page_sources.json", "r") as file:
    data = json.load(file)

# Loop through each entry in the file
predictions = []
for entry in data:
    text = entry["text"]

    # Tokenize the text
    inputs = tokenizer(text, return_tensors="pt", truncation=True)

    # Get model output
    with torch.no_grad():
        outputs = model(**inputs)

    # Calculate probabilities and predicted class
    logits = outputs.logits
    probabilities = F.softmax(logits, dim=1)
    predicted_class = torch.argmax(probabilities, dim=1).item()
    confidence_score = probabilities[0][predicted_class].item()

    # Append result
    predictions.append({
        "text": text,
        "predicted_class": predicted_class,
        "confidence_score": confidence_score
    })

# Print or save predictions
for prediction in predictions:
    print(f"Text: {prediction['text']}")
    print(f"Predicted Class: {prediction['predicted_class']}, Confidence Score: {prediction['confidence_score']:.2f}\n")
