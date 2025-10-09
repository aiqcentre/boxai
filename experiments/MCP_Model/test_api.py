from fastapi.testclient import TestClient
import boxoffice_api as api

client = TestClient(api.app)

print('GET / ->', client.get('/').json())

predict_payload = {
    "censorRating": "PG",
    "distributorName": "Universal",
    "week_date": "2025-09-20",
    "concurrent_films": [
        {"week.gross": 100000, "weekend.gross": 50000, "week.theatreCount": 80, "week.screenCount": 120}
    ]
}
resp = client.post('/predict1', json=predict_payload)
print('/predict1 status:', resp.status_code, 'response:', resp.json())

mcp_payload = {"instances": [predict_payload, predict_payload]}
resp = client.post('/mcp/predict', json=mcp_payload)
print('/mcp/predict status:', resp.status_code, 'response:', resp.json())

resp = client.post('/final_total_predict', json={"wk1_total": 100000})
print('/final_total_predict status:', resp.status_code, 'response:', resp.json())
