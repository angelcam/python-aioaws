from .aws import AWS, AWSException


class SQS:
    """Basic implementation of Amazon SQS.
    """

    SVC_NAME = 'sqs'
    VERSION = '2012-11-05'

    def __init__(self, region, account_id, access_key, secret_key, loop=None):
        """Create a new SQS client. The client should be created only within
        a coroutine as it contains an aiohttp ClientSession.

        :param region: AWS region
        :param account_id: AWS account ID
        :param access_key: AWS access key
        :param secret_key: AWS secret access key
        :param loop: asyncio event loop
        """
        self.__region = region
        self.__account_id = account_id

        self.__common_params = {
            'Version': SQS.VERSION
        }

        self.__aws = AWS(
            region,
            SQS.SVC_NAME,
            access_key,
            secret_key,
            loop=loop)

    def __get_queue_url(self, queue):
        """Get URL for a gicen queue name.

        :param queue: queue name
        :return: queue URL (string)
        """
        return 'https://%s.%s.amazonaws.com/%s/%s' % (
            SQS.SVC_NAME,
            self.__region,
            self.__account_id,
            queue)

    def __parse_received_message(self, message):
        """Parse a given SQS message.

        :param message: SQS message (lxml object)
        :return: SQS message (dict)
        """
        result = {
            'Body': message.Body.text,
            'MD5OfBody': message.MD5OfBody.text,
            'ReceiptHandle': message.ReceiptHandle.text,
            'Attributes': {}
        }
        for attr in message.Attribute:
            result['Attributes'][attr.Name.text] = attr.Value.text
        return result

    async def send_message(self, queue, message,
                           delay_seconds=None):
        """Send a given message to a given queue.

        :param queue: name of an SQS queue
        :param message: message
        :param delay_seconds: the DelaySeconds parameter (see the AWS docs)
        :return: message ID
        """
        url = self.__get_queue_url(queue)
        params = {
            'Action': 'SendMessage',
            'MessageBody': message
        }
        if delay_seconds:
            params['DelaySeconds'] = delay_seconds
        params.update(self.__common_params)
        response = await self.__aws.get(url, params)
        return response.SendMessageResult.MessageId.text

    async def receive_messages(self, queue,
                               max_messages=None,
                               wait_time=None,
                               visibility_timeout=None):
        """Receive messages from a given queue.

        :param queue: name of an SQS queue
        :param max_messages: the MaxNumberOfMessages parameter (see the AWS
        docs)
        :param wait_time: the WaitTimeSeconds parameter (see the AWS docs)
        :param visibility_timeout: the VisibilityTimeout parameter (see the AWS
        docs)
        :return: list of received messages (a list of dicts)
        """
        url = self.__get_queue_url(queue)
        params = {
            'Action': 'ReceiveMessage',
            'AttributeName': 'All'
        }
        if max_messages:
            params['MaxNumberOfMessages'] = max_messages
        if visibility_timeout:
            params['VisibilityTimeout'] = visibility_timeout
        if wait_time:
            params['WaitTimeSeconds'] = wait_time
        params.update(self.__common_params)
        response = await self.__aws.get(url, params)
        if response.ReceiveMessageResult == '':
            return []
        messages = response.ReceiveMessageResult.Message
        return [self.__parse_received_message(msg) for msg in messages]

    async def delete_message(self, queue, receipt_handle):
        """Delete a given message from a given queue.

        :param queue: name of an SQS queue
        :param receipt_handle: message receipt handle
        :return: request ID
        """
        url = self.__get_queue_url(queue)
        params = {
            'Action': 'DeleteMessage',
            'ReceiptHandle': receipt_handle
        }
        params.update(self.__common_params)
        response = await self.__aws.get(url, params)
        return response.ResponseMetadata.RequestId.text

    async def delete_messages(self, queue, receipt_handles):
        """Delete a given list of messages from a given queue.

        :param queue: name of an SQS queue
        :param receipt_handles: list of receipt handles
        :return: a list errors (or Nones)
        """
        url = self.__get_queue_url(queue)
        result = [None for h in receipt_handles]
        start = 0
        while start < len(receipt_handles):
            # get receipt handles subset (max 10 handles):
            end = start + 10
            if end > len(receipt_handles):
                end = len(receipt_handles)
            delete_handles = receipt_handles[start:end]
            # get request parameters:
            params = {
                'Action': 'DeleteMessageBatch'
            }
            params.update(self.__common_params)
            for i in range(end - start):
                eid = i + 1
                pid = 'DeleteMessageBatchRequestEntry.%d.Id' % eid
                prh = 'DeleteMessageBatchRequestEntry.%d.ReceiptHandle' % eid
                params[pid] = start + i
                params[prh] = delete_handles[i]
            # perform request:
            response = await self.__aws.get(url, params)
            # process response:
            bresult = response.DeleteMessageBatchResult
            errors = []
            if hasattr(bresult, 'BatchResultErrorEntry'):
                errors = bresult.BatchResultErrorEntry
            for err in errors:
                index = int(err.Id.text)
                status = int(err.Code.text)
                reason = err.Message.text
                result[index] = AWSException(status, reason)
            # update position:
            start += 10
        return result
