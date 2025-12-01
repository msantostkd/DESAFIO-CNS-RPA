import requests
from requests.auth import HTTPBasicAuth

url = "https://oauth.hm.bb.com.br/oauth/token"

client_id = "eyJpZCI6ImU0NTYiLCJjb2RpZ29QdWJsaWNhZG9yIjowLCJjb2RpZ29Tb2Z0d2FyZSI6MTYzMDUwLCJzZXF1ZW5jaWFsSW5zdGFsYWNhbyI6MX0"
client_secret = "eyJpZCI6IjkzY2Q2NGQtNWE5Yy00ZTA5LTk4ZmEtYmI0ZDcyMDIyMyIsImNvZGlnb1B1YmxpY2Fkb3IiOjAsImNvZGlnb1NvZnR3YXJlIjoxNjMwNTAsInNlcXVlbmNpYWxJbnN0YWxhY2FvIjoxLCJzZXF1ZW5jaWFsQ3JlZGVuY2lhbCI6MiwiYW1iaWVudGUiOiJob21vbG9nYWNhbyIsImlhdCI6MTc2NDA3NjYwMzQ5OX0"

payload = {
    "grant_type": "client_credentials",
    
}

response = requests.post(
    url,
    data=payload,
    auth=HTTPBasicAuth(client_id, client_secret),
    headers={
        "Content-Type": "application/x-www-form-urlencoded"
    }
)

print("Status code:", response.status_code)
print("Resposta:")
print(response.json())
