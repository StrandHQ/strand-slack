import re

from src.command.Command import Command
from src.domain.models.coreapi.SlackUser import SlackUserSchema
from src.domain.models.exceptions.WrapperException import WrapperException


class ForwardMessageCommand(Command):
    def __init__(self, slack_client_wrapper, core_api_client_wrapper, team_id, event):
        super().__init__(slack_client_wrapper=slack_client_wrapper, core_api_client_wrapper=core_api_client_wrapper,
                         slack_team_id=team_id)
        self.slack_event = event

    def execute(self):
        """Forward message onward to the core_api for storage"""
        log_message = f'Executing ForwardMessageCommand for {self.slack_team_id} with message {self.slack_event}'
        self.logger.info(log_message)
        if self._is_discussion_message():
            try:
                if self.slack_event.is_reply:
                    self.core_api_client_wrapper.create_reply_from_slack(text=self.slack_event.text,
                                                                         slack_channel_id=self.slack_event.channel,
                                                                         slack_event_ts=self.slack_event.ts,
                                                                         slack_thread_ts=self.slack_event.thread_ts,
                                                                         author_slack_user_id=self.slack_event.user)
                else:
                    # regular message
                    self.core_api_client_wrapper.create_message_from_slack(text=self.slack_event.text,
                                                                           slack_channel_id=self.slack_event.channel,
                                                                           slack_event_ts=self.slack_event.ts,
                                                                           author_slack_user_id=self.slack_event.user)
            except WrapperException as e:
                # TODO [SLA-15/SLA-81] caching user info to avoid relying on error
                if e.errors and e.errors[0]['message'] == 'User matching query does not exist.':
                    self.logger.info('Tried to forward message for unknown user. Retrying with user creation.')
                    slack_user_info = self.slack_client_wrapper.get_user_info(slack_user_id=self.slack_event.user,
                                                                              slack_team_id=self.slack_team_id)
                    slack_user = SlackUserSchema().load(slack_user_info).data
                    if self.slack_event.is_reply:
                        self.core_api_client_wrapper.create_reply_and_user_as_author_from_slack(
                            text=self.slack_event.text,
                            slack_channel_id=self.slack_event.channel,
                            slack_event_ts=self.slack_event.ts,
                            slack_thread_ts=self.slack_event.thread_ts,
                            slack_user=slack_user
                        )
                    else:
                        # regular message
                        self.core_api_client_wrapper.create_message_and_user_as_author_from_slack(
                            text=self.slack_event.text,
                            slack_channel_id=self.slack_event.channel,
                            slack_event_ts=self.slack_event.ts,
                            slack_user=slack_user
                        )
                else:
                    self.logger.error(f'Failed to store message: {self.slack_event}')
                    raise e

    def _is_discussion_message(self):
        # TODO [SLA-81] This check should happen via db in processor
        calling_channel_id = self.slack_event.channel
        calling_channel_info = self.slack_client_wrapper.get_channel_info(slack_team_id=self.slack_team_id,
                                                                          slack_channel_id=calling_channel_id)
        calling_channel_name = calling_channel_info['name']
        return re.fullmatch(pattern=r'discussion-(\d+)', string=calling_channel_name) is not None
