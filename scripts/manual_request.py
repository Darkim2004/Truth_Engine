import requests


def main() -> None:
    response = requests.post(
        "http://127.0.0.1:5001/elabora_completo",
        json={"mode": "testo", "data": "Elon Musk ha comprato Twitter nel 2022"},
        headers={"Origin": "http://127.0.0.1:5001"},
        timeout=120,
    )
    print("Status:", response.status_code)
    print("Data:", response.text)


if __name__ == "__main__":
    main()
