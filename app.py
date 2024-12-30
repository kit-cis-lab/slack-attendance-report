import os

import aws_cdk as cdk

from slack_attendance_report.slack_attendance_report_stack import SlackAttendanceReport

if __name__ == "__main__":
    app = cdk.App()
    SlackAttendanceReport(
        app,
        "SlackAttendanceReport",
        env={
            "region": os.environ["CDK_DEFAULT_REGION"],
            "account": os.environ["CDK_DEFAULT_ACCOUNT"],
        },
    )
    app.synth()
