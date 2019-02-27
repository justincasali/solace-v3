import botocore.session
import json
import os

# Status constants
RECEIVED, QUEUED = "received", "queued"

# AWS session
session = botocore.session.get_session()

# Sqs client
sqs = session.create_client("sqs")

# Backup queue url
backup_queue = sqs.get_queue_url(QueueName=os.environ["BACKUP_QUEUE"])["QueueUrl"]

# Restore queue url
restore_queue = sqs.get_queue_url(QueueName=os.environ["RESTORE_QUEUE"])["QueueUrl"]

# Dynamodb client
dynamodb = session.create_client("dynamodb")

# Backup table
backup_table = os.environ["BACKUP_TABLE"]

# Restore Table
restore_table = os.environ["RESTORE_TABLE"]


# Entry point
def lambda_handler(event, context):

    # Load message from json
    message = json.loads(event["Records"][0]["body"])

    # Add timestamp to message
    message["timestamp"] = event["Records"][0]["attributes"]["SentTimestamp"]

    # Backup action
    if message["action"] == "backup":

        # Build table key
        message["key"] = "-".join([message["table-region"], message["table-name"]])

        # Write entry to db
        dynamodb.put_item(TableName=backup_table, Item={
            "key":           {"S": message["key"]},
            "timestamp":     {"N": message["timestamp"]},
            "table-region":  {"S": message["table-region"]},
            "table-name":    {"S": message["table-name"]},
            "bucket-region": {"S": message["bucket-region"]},
            "bucket-name":   {"S": message["bucket-name"]},
            "bucket-prefix": {"S": message["bucket-prefix"]},
            "status":        {"S": RECEIVED}
        })

        # Send message
        sqs.send_message(QueueUrl=backup_queue, MessageBody=json.dumps(message))

        # Complete
        return

    # Restore action
    if message["action"] == "restore":

        # Build table key
        message["key"] = "-".join([message["bucket-region"], message["bucket-name"], message["bucket-prefix"]])

        # Write entry to db
        dynamodb.put_item(TableName=backup_table, Item={
            "key":           {"S": message["key"]},
            "timestamp":     {"N": message["timestamp"]},
            "bucket-region": {"S": message["bucket-region"]},
            "bucket-name":   {"S": message["bucket-name"]},
            "bucket-prefix": {"S": message["bucket-prefix"]},
            "table-region":  {"S": message["table-region"]},
            "table-name":    {"S": message["table-name"]},
            "status":        {"S": RECEIVED}
        })

        # Send message
        sqs.send_message(QueueUrl=restore_queue, MessageBody=json.dumps(message))

        # Complete
        return

    # Error on invalid action
    raise Exception("invalid request action")
