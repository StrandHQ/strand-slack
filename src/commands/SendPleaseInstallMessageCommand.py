from src.commands.Command import Command
from src.models.slack.outgoing.messages import PleaseInstallSlackMessage


class SendPleaseInstallMessageCommand(Command):
    def __init__(self, slack_client_wrapper, slack_team_id, slack_user_id, slack_channel_id, use_bot_token=True):
        super().__init__(slack_client_wrapper=slack_client_wrapper)
        self.slack_team_id = slack_team_id
        self.slack_user_id = slack_user_id
        self.slack_channel_id = slack_channel_id
        self.use_bot_token = use_bot_token

    def execute(self):
        log_msg = f'Executing SendPleaseInstallMessageCommand for {self.slack_team_id} with user {self.slack_user_id}'
        self.logger.info(log_msg)
        self.slack_client_wrapper.send_ephemeral_message(slack_team_id=self.slack_team_id,
                                                         slack_channel_id=self.slack_channel_id,
                                                         slack_user_id=self.slack_user_id,
                                                         text=PleaseInstallSlackMessage().text,
                                                         use_bot_token=self.use_bot_token)
