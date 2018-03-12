import factory.fuzzy
from pytest_factoryboy import register

from src.models.slack.elements.SlackAction import SlackAction
from src.models.slack.elements.SlackBot import SlackBot
from src.models.slack.elements.SlackChannel import SlackChannel
from src.models.slack.elements.SlackEvent import SlackEvent
from src.models.slack.elements.SlackFile import SlackFile
from src.models.slack.elements.SlackMessage import SlackMessage
from src.models.slack.elements.SlackOption import SlackOption
from src.models.slack.elements.SlackSubmission import SlackSubmission
from src.models.slack.elements.SlackTeam import SlackTeam
from src.models.slack.elements.SlackUser import SlackUser
from src.models.slack.requests.SlackEventRequest import SlackEventRequest
from src.models.slack.requests.SlackInteractiveComponentRequest import SlackInteractiveComponentRequest
from src.models.slack.requests.SlackSlashCommandRequest import SlackSlashCommandRequest
from src.models.slack.responses.SlackOauthAccessResponse import SlackOauthAccessResponse


class MessageFactory(factory.Factory):
    class Meta:
        model = SlackMessage

    text = factory.Faker('paragraph')
    ts = factory.Faker('msisdn')


class OptionFactory(factory.Factory):
    class Meta:
        model = SlackOption

    value = factory.Faker('word')


class ActionFactory(factory.Factory):
    class Meta:
        model = SlackAction

    name = factory.Faker('word')
    selected_options = factory.List([OptionFactory.build()])


class TeamFactory(factory.Factory):
    class Meta:
        model = SlackTeam

    id = factory.Faker('bban')


class UserFactory(factory.Factory):
    class Meta:
        model = SlackUser

    id = factory.Faker('bban')


class ChannelFactory(factory.Factory):
    class Meta:
        model = SlackChannel

    id = factory.fuzzy.FuzzyText(length=9, prefix='C')
    name = factory.Faker('word')


class SubmissionFactory(factory.Factory):
    class Meta:
        model = SlackSubmission

    title = factory.Faker('paragraph')
    description = factory.Faker('paragraph')
    tags = factory.Faker('paragraph')
    share_with_current_channel = False


class FileFactory(factory.Factory):
    class Meta:
        model = SlackFile

    id = factory.Faker('bban')
    public_url_shared = factory.Faker('url')
    permalink_public = False


class EventFactory(factory.Factory):
    class Meta:
        model = SlackEvent

    type = factory.Faker('word')
    user = factory.Faker('bban')
    channel = factory.fuzzy.FuzzyText(length=9, prefix='C')
    text = factory.Faker('paragraph')
    ts = factory.Faker('msisdn')
    subtype = factory.Faker('word')
    file = factory.SubFactory(FileFactory)


class SlackBotFactory(factory.Factory):
    class Meta:
        model = SlackBot

    bot_user_id = factory.Faker('bban')
    bot_access_token = factory.Faker('md5')


#  TOP LEVEL

class InteractiveComponentRequestFactory(factory.Factory):
    class Meta:
        model = SlackInteractiveComponentRequest

    type = factory.Faker('word')
    callback_id = factory.Faker('word')
    team = factory.SubFactory(TeamFactory)
    user = factory.SubFactory(UserFactory)
    channel = factory.SubFactory(ChannelFactory)
    response_url = factory.Faker('url')
    trigger_id = factory.Faker('md5')


class SlashCommandRequestFactory(factory.Factory):
    class Meta:
        model = SlackSlashCommandRequest

    team_id = factory.Faker('bban')
    user_id = factory.Faker('bban')
    command = factory.Faker('word')
    response_url = factory.Faker('url')
    trigger_id = factory.Faker('md5')
    channel_id = factory.Faker('bban')


class EventRequestFactory(factory.Factory):
    class Meta:
        model = SlackEventRequest

    type = factory.Faker('word')
    challenge = factory.Faker('md5')
    team_id = factory.Faker('bban')
    event = factory.SubFactory(EventFactory)


@register
class SlackOauthAccessResponseFactory(factory.Factory):
    class Meta:
        model = SlackOauthAccessResponse

    access_token = factory.Faker('md5')
    scope = factory.Faker('sentence')
    team_name = factory.Faker('last_name')
    team_id = factory.Faker('bban')
    bot = factory.SubFactory(SlackBotFactory)
