import requests
r = requests.post(
    'http://127.0.0.1:5002/elabora_completo',
    json={'mode':'testo', 'data':'Elon Musk ha comprato Twitter nel 2022'},
    headers={'Origin': 'http://127.0.0.1:5500'}
)
print("Status:", r.status_code)
print("Data:", r.text)
