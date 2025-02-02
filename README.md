# Slack Attendance Report

[情報知能システム研究室][CIS] の出勤数ランキングを毎月最終日にSlackに投稿するSlack App

## 環境構築

[uv][uv] を使用して仮想環境を作成する．

```
uv sync
```

[コードで学ぶAWS入門][labc] の付録を参考にしてAWSの環境構築を済ませる．

- AWSアカウントの取得
- AWSシークレットキーの作成
- AWS CLIのインストール
- AWS CDKのインストール

`slack_attendance_report/layers/python/` に `slack-sdk` をインストールする．

```
pip install slack-sdk -t slack_attendance_report/layers/python/
```

`.env` ファイルを作成して内容を記述する

```
cp .env.sample .env
```

## デプロイ方法

デプロイ

```
cdk deploy
```

スタックの削除

```
cdk destroy
```

[uv]: https://docs.astral.sh/uv/
[CIS]: https://vega.is.kit.ac.jp/
[labc]: https://tomomano.github.io/learn-aws-by-coding/
