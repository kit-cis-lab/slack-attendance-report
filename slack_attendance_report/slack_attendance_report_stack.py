import os

import aws_cdk as cdk
from aws_cdk import Duration
from aws_cdk import SecretValue
from aws_cdk import Stack
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_secretsmanager as secretsmanager
from constructs import Construct
from dotenv import load_dotenv


class SlackAttendanceReport(Stack):
    load_dotenv()

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Secrets Managerを作成
        secret_manager = secretsmanager.Secret(
            self,
            "SlackAttendanceReportSecrets",
            secret_object_value={
                "SLACK_BOT_TOKEN": SecretValue.unsafe_plain_text(os.getenv("SLACK_BOT_TOKEN")),
                "SLACK_CHANNEL_ID": SecretValue.unsafe_plain_text( os.getenv("SLACK_CHANNEL_ID")),
            },
        )  # fmt: skip

        # Lambda実行用のIAMロールを作成
        lambda_role = iam.Role(
            self,
            "SlackAttendanceReportLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
        )

        # Secrets Managerへのアクセスを許可するポリシーを作成
        sm_policy_sttmt = iam.PolicyStatement(
            actions=[
                "secretsmanager:GetSecretValue",
                "secretsmanager:DescribeSecret",
            ],
            resources=["*"],
        )

        # IAMロールにポリシーを適用
        lambda_role.add_to_policy(sm_policy_sttmt)

        # Slack SDKのLambda Layerを作成
        slack_sdk_layer = lambda_.LayerVersion(
            self,
            "SlackSDKLayer",
            code=lambda_.Code.from_asset(
                os.path.join(
                    os.path.dirname(__file__),
                    "layers",
                )
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
        )

        # Lambda関数の定義
        attd_function = lambda_.Function(
            self,
            "SlackAttendanceReportLambda",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="attendance.handler",
            code=lambda_.Code.from_asset("lambda"),
            timeout=Duration.seconds(30),
            role=lambda_role,
            layers=[slack_sdk_layer],
            environment={
                "SECRET_ARN": secret_manager.secret_arn,
            },
        )

        # Event BridgeでLambdaを定期実行する
        schedule = events.Rule(
            self,
            "SlackAttendanceReportSchedule",
            # 分 時 日 月 曜日 年
            # 0  3  L *  ?   *
            schedule=events.Schedule.cron(
                year="*",
                month="*",
                day="L",
                hour="3",
                minute="0",
            ),
            targets=[targets.LambdaFunction(attd_function)],
        )

        cdk.CfnOutput(self, "FunctionName", value=attd_function.function_name)
