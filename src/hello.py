from slack_sdk import WebClient


def main():
    client = WebClient()
    response = client.api_test()
    print(response)


if __name__ == "__main__":
    main()
