"""
grab every document one by one from documents folder
for every document:
    generate a unique id
    send the doc to docling -- get back a docling document
    upload the dd to drive -> get back a link to it
    store in db : unique id < - > docling document google drive link < - > document title
    
    one more responsibility:
    build this:
         "document_id": "doc_moh_fever_guidelines_v3",
        "title": "Ministry of Health National Fever Management Guidelines",
        "issuing_authority": "Ministry of Health & Family Welfare",
        "version": "3.0",
        "publication_date": "2023-04-01",



"""