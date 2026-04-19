LEGAL TRANSLATOR - Complete Bundle
====================================
Languages : English <-> Tamil <-> Sinhala
Base model: facebook/nllb-200-distilled-600M

FOLDER STRUCTURE
-----------------
LEGAL-TRANSLATOR-COMPLETE/
  base_model/        Original NLLB weights
  adapter_tamil/     Tamil LoRA (Phase 1)
  adapter_sinhala/   Tamil+Sinhala LoRA (Phase 2)
  merged_model/      USE THIS for all translation
  metadata.json
  README.txt

REUSE ON ANY COMPUTER
----------------------
pip install transformers torch sentencepiece
python reuse_legal_translator.py

TO RETRAIN
----------
Use base_model/ + adapter_tamil/ or adapter_sinhala/
with the retrain.py script.
