import standalone_app
from events.coms import MessageTypes
from fastapi.testclient import TestClient

# def test_event():
#     client = TestClient(standalone_app.app)
#     with client.websocket_connect('/nostr') as ws:
#         ws.send_json([MessageTypes.Event.value, {"id": "asdajsda", "pubkey": "asdjasjd", "created_at": 129312931,
#         "kind": 1, "tags": [['e', 15,  'asdla']], "content": "co co", "sig": "asjdasjd"}])
#         data = ws.receive_json()

# def test_req():
#     client = TestClient(standalone_app.app)
#     with client.websocket_connect('/nostr') as ws:
#         ws.send_json([MessageTypes.Req.value, {}])
#         data = ws.receive_json()
