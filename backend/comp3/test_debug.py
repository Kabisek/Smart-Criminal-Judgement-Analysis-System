import sys
sys.path.insert(0, '../')
from src.core.models import AppealPredictor
import numpy as np

# Get paths
model_path = '../../data/models/improved_model.pkl'
selector_path = '../../data/models/feature_selector.pkl'
encoder_path = '../../data/models/label_encoder.pkl'
x_train_path = 'X_train_improved.csv'
bert_emb_path = 'bert_embeddings_train.npy'
dataset_path = 'dataset_cleaned_final.csv'
y_train_path = 'y_train_improved.npy'

predictor = AppealPredictor(
    model_path=model_path,
    selector_path=selector_path,
    label_encoder_path=encoder_path,
    x_train_path=x_train_path,
    bert_embeddings_path=bert_emb_path,
    dataset_path=dataset_path,
    y_train_path=y_train_path
)

case_desc = "The accused was convicted by the High Court for rape under Section 363."
bert_emb = np.random.randn(768)

result = predictor.find_similar_cases(case_desc, bert_emb, top_k=1)
print("Similar Case Data:")
print(result[0])
print("\nKeys in similar case:", list(result[0].keys()))
print("\nOffence value:", result[0].get('offence'))
print("High Court value:", result[0].get('high_court'))
print("Conviction Status value:", result[0].get('conviction_status'))
