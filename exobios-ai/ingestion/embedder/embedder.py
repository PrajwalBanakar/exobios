"""
input: stream of chunks + tokens in batches
output: vector embedding for every chunk 
also build the chunk meta data here

fill these

    "ingestion_version": "ing_2026_07_20",
    "chunk_id": "chunk_0F3A9C21",
    "section": "3.2 Diagnostic Criteria",
    "heading": "Dengue Fever - Diagnostic Criteria",
    "page_start": 12,
    "page_end": 12,
    "is_red_flag_chunk": true,

    "text": "Suspected dengue fever should be diagnosed when a patient
    presents with: (1) fever of 2-7 days duration, (2) two or more of: nausea/vomiting, 
    rash, headache, thrombocytopenia (platelet count < 100,000/mm3), positive tourniquet test. 
    Warning signs requiring urgent referral include abdominal pain, persistent vomiting, and mucosal bleeding."

"""