from src import create_app, slack_agent_repository
from src.config import config
from tests.factories.coreapifactories import SlackAgentFactory
from tests.testresources import TestSlackClient


class TestInitializingSlackApplicationInstallations:
    fake_slack_agent = SlackAgentFactory.build()
    fake_slack_team_id = fake_slack_agent.slack_team.id
    fake_slack_access_token = fake_slack_agent.slack_application_installation.access_token
    fake_slack_bot_access_token = fake_slack_agent.slack_application_installation.bot_access_token
    fake_slack_bot_user_id = fake_slack_agent.slack_application_installation.bot_user_id

    def test_installations_initialized_on_startup(self, mocker, core_api_client):
        mocker.spy(core_api_client, 'query')

        self._queue_response_from_core_api(core_api_client=core_api_client)

        create_app(core_api_client=core_api_client, SlackClientClass=TestSlackClient,
                   slack_verification_tokens='anything',
                   core_api_verification_token=config['CORE_API_VERIFICATION_TOKEN'])

        assert core_api_client.query.call_count == 1
        assert slack_agent_repository.get_slack_access_token(
            slack_team_id=self.fake_slack_team_id) == self.fake_slack_access_token
        assert slack_agent_repository.get_slack_bot_access_token(
            slack_team_id=self.fake_slack_team_id) == self.fake_slack_bot_access_token
        assert slack_agent_repository.get_slack_bot_user_id(
            slack_team_id=self.fake_slack_team_id) == self.fake_slack_bot_user_id

    def _queue_response_from_core_api(self, core_api_client):
        core_api_client.set_next_response({
            'data': {
                'slackAgents': [{
                    'status': self.fake_slack_agent.status,
                    'topicChannelId': self.fake_slack_agent.topic_channel_id,
                    'slackTeam': {
                        'id': self.fake_slack_team_id
                    },
                    'slackApplicationInstallation': {
                        'accessToken': self.fake_slack_access_token,
                        'installer': {
                            'id': self.fake_slack_agent.slack_application_installation.installer.id,
                        },
                        'botAccessToken': self.fake_slack_bot_access_token,
                        'botUserId': self.fake_slack_bot_user_id,
                    },
                }]
            }
        })
