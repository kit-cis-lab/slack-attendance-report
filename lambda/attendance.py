import ast
import calendar
import json
import os
from datetime import datetime

import boto3
from slack_sdk import WebClient


def handler(event, context):
    secret = get_secret()
    if secret is None:
        return {"statusCode": 500, "body": json.dumps("Error getting secret.")}

    client = WebClient(token=secret["SLACK_BOT_TOKEN"])

    channel_id = secret["SLACK_CHANNEL_ID"]
    first_timestamp = get_first_timestamp()
    last_timestamp  = get_last_timestamp()  # fmt: skip

    # 今月のメッセージ履歴を取得する
    history = client.conversations_history(
        channel=channel_id,
        oldest=first_timestamp,
        latest=last_timestamp,
    )

    # ユーザーIDとユーザー名の対応を作成する
    user_map = get_user_map(client, channel_id)

    # ユーザーごとの出勤数
    attd_cnt = {}

    for post in history["messages"]:
        # リアクションがあるメッセージのみを対象とする
        if "reactions" in post.keys():
            reactions = post["reactions"]
            for reaction in reactions:
                # リアクションが出勤の場合
                if reaction["name"] == "出勤_syukkin":
                    # リアクションをつけたユーザーをループする
                    for user_id in reaction["users"]:
                        # ユーザーの出勤回数をカウントアップする
                        user_name = user_map[user_id]
                        if user_name in attd_cnt:
                            attd_cnt[user_name] += 1
                        else:
                            attd_cnt[user_name] = 1

    # 誰も1回も出勤しなかった場合
    if len(attd_cnt) == 0:
        return {"statusCode": 200, "body": json.dumps("No attendance.")}

    # 出勤数ランキングのテキストを作成する
    ranking_text = create_ranking_text(attd_cnt)

    # ランキングをSlackに投稿する
    client.chat_postMessage(
        channel=channel_id,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*今月の出勤数ランキング*"
                }
            },
            {
                "type": "divider"
            },
            {
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': ranking_text
                }
            }
        ],
    )  # fmt: skip

    return {"statusCode": 200, "body": json.dumps("Success!")}


def get_secret():
    """Secrets Managerからシークレットを取得する関数"""
    region_name = "ap-northeast-1"

    session = boto3.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    secret_arn = os.getenv("SECRET_ARN")
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_arn)
    except Exception as e:
        print(f"Error getting secret: {e}")
        return None

    if "SecretString" in get_secret_value_response:
        secret = get_secret_value_response["SecretString"]
        return ast.literal_eval(secret)
    else:
        return None


def get_first_timestamp() -> int:
    """今月の初日の0時0分0秒のタイムスタンプを取得する関数"""
    today = datetime.today()

    first_dt = datetime(today.year, today.month, 1, 0, 0, 0)
    return int(first_dt.timestamp())


def get_last_timestamp() -> int:
    """今月の最終日の23時59分59秒のタイムスタンプを取得する関数"""
    today = datetime.today()

    last_day = calendar.monthrange(today.year, today.month)[1]
    last_dt = datetime(today.year, today.month, last_day, 23, 59, 59)
    return int(last_dt.timestamp())


def get_user_map(client: WebClient, channel_id: str) -> dict:
    """ユーザーIDとユーザー名の対応を取得する関数"""
    channel_user_list = client.conversations_members(channel=channel_id)
    all_user_list = client.users_list()["members"]

    user_map = {}
    for channel_user_id in channel_user_list["members"]:
        for user in all_user_list:
            if channel_user_id == user["id"]:
                user_map[channel_user_id] = user["profile"]["real_name"]
                break

    return user_map


def create_ranking_text(attd_cnt: dict) -> str:
    """出勤数ランキングのテキストを作成する関数"""
    sort_attd_cnt = sorted(attd_cnt.items(), key=lambda x: x[1], reverse=True)

    text = ""
    rank = 0
    prev = float("inf")
    for user_name, cnt in sort_attd_cnt:
        if cnt < prev:
            rank += 1
            prev = cnt

        text += f"{rank}位\t{user_name}\t{cnt}回\n"

    return text
