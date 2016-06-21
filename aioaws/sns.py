import json

from .aws import AWS

class SNS:
    """Basic implementation of Amazon SNS.
    """

    SVC_NAME = 'sns'
    VERSION  = '2010-03-31'

    def __init__(self, region, access_key, secret_key, loop=None):
        """Create a new SNS client.

        :param region: AWS region
        :param access_key: AWS access key
        :param secret_key: AWS secret access key
        :param loop: asyncio event loop
        """
        self.__url = 'https://%s.%s.amazonaws.com/' % (SNS.SVC_NAME, region)

        self.__common_params = {
            'Version' : SNS.VERSION
        }

        self.__aws = AWS(region, SNS.SVC_NAME, access_key, secret_key, loop=loop)

    async def subscribe(self, topic_arn, protocol, endpoint):
        """Subscribe to a given SNS topic.

        :param topic_arn: SNS topic ARN
        :param protocol: SNS protocol
        :param endpoint: subscription endpoint
        :return: subscription ARN (in case no confirmation is needed)
        """
        params = {
            'Action'   : 'Subscribe',
            'TopicArn' : topic_arn,
            'Protocol' : protocol,
            'Endpoint' : endpoint
        }
        params.update(self.__common_params)
        response = await self.__aws.get(self.__url, params)
        return response.SubscribeResult.SubscriptionArn.text

    async def confirm_subscription(self, topic_arn, token,
        auth_unsubscribe = None):
        """Confirm a given subscription.

        :param topic_arn: SNS topic ARN
        :param token: confirmation token (received on the corresponding
        subscription endpoint)
        :param auth_unsubscribe: if authorization is required to unsubscribe
        :return: subscription ARN
        """
        params = {
            'Action'   : 'ConfirmSubscription',
            'TopicArn' : topic_arn,
            'Token'    : token
        }
        if auth_unsubscribe is not None:
            param['AuthenticateOnUnsubscribe'] = str(auth_unsubscribe).lower()
        params.update(self.__common_params)
        response = await self.__aws.get(self.__url, params)
        return response.ConfirmSubscriptionResult.SubscriptionArn.text

    async def publish(self, topic_arn, message,
        subject = None,
        target_arn = None,
        message_structure = None):
        """Publish a given message to a given SNS topic.

        :param topic_arn: SNS topic ARN
        :param message: message text or dict for structured messages
        :param subject: optional message subject
        :param target_arn: topic ARN or endpoint ARN but not both
        :param message_structure: "json" for separate messages for every
        protocol
        :return: message ID
        """
        assert message_structure in (None, 'json')
        if message_structure == 'json':
            message = json.dumps(message)
        params = {
            'Action'  : 'Publish',
            'Message' : message
        }
        if subject:
            params['Subject'] = subject
        if message_structure:
            params['MessageStructure'] = message_structure
        if topic_arn:
            params['TopicArn'] = topic_arn
        if target_arn:
            params['TargetArn'] = target_arn
        params.update(self.__common_params)
        response = await self.__aws.get(self.__url, params)
        return response.PublishResult.MessageId.text
