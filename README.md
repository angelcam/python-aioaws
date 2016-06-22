# aioaws

Asynchronous AWS client library based on Python 3.5+ asyncio. Currently, only
basic SNS and SQS methods are supported.

## Installation

Add this repository to your requirements.txt:

```
-e git+https://bitbucket.org/angelcam/python-aioaws.git#egg=aioaws
```

and run:

```bash
pip install -r requirements.txt
```

## Usage example

```python
from aioaws import SNS, SQS

# AWS region and account identification

region     = '...'
account_id = '...'
access_key = '...'
secret_key = '...'

...

# SNS example:

sns = SNS(region, access_key, secret_key)

topic_arn = 'arn:aws:sns:...'

# subscribing:

await sns.subscribe(topic_arn, 'http', 'http://my_host/my_endpoint')

...

await sns.confirm_subscription(topic_arn, token)

# sending a message:

await sns.publish(topic_arn, 'my message')

...

# SQS example:

sqs = SQS(region, account_id, access_key, secret_key)

# sending a message:

await sqs.send_message('my-queue', 'my message')

# receiving messages:

messages = await sqs.receive_messages('my-queue',
        max_messages = 10,
        wait_time    = 10)

# deleting a message:

await sqs.delete_message('my-queue', receipt_handle)

```

Received messages will have the following form:

```
[
  {
    'ReceiptHandle' : '...',
    'MD5OfBody'     : '0123abcd',
    'Body'          : 'my message',
    'Attributes'    : {
      'ApproximateReceiveCount'          : '1',
      'SentTimestamp'                    : '123',
      'ApproximateFirstReceiveTimestamp' : '123',
      'SenderId'                         : '...'
    }
  },
  ...
]
```
