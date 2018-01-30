from src.command.Command import Command
from src.domain.models.exceptions import WrapperException


class StartDiscussionCommand(Command):
    def __init__(self, slack_client_wrapper, portal_client_wrapper, slack_team_id, submission, slack_user_id):
        super().__init__(slack_team_id=slack_team_id, slack_client_wrapper=slack_client_wrapper,
                         portal_client_wrapper=portal_client_wrapper)
        self.submission = submission
        self.slack_user_id = slack_user_id

    def execute(self):
        self.logger.info(f'Executing StartDiscussionCommand for {self.slack_team_id}')
        try:
            self._create_topic()
            # TODO creating a new discussion [next ticket]
            # TODO send DM to user informing them of the creation of their session
        except WrapperException:
            self.logger.error(f'Topic submission failed. Submission: {self.submission}')
            self.slack_client_wrapper.send_dm_to_user(slack_team_id=self.slack_team_id,
                                                      slack_user_id=self.slack_user_id,
                                                      text='Sorry, your topic submission failed for some unknown reason'
                                                           ' :see_no_evil: Please contact support@solutionloft.com')

    def _create_topic(self):
        # TODO [CCS-60] move tag parsing to useful validation (maybe derived attr on Submission)
        tag_names = [x.strip() for x in self.submission.tags.split(',')]
        topic = self.portal_client_wrapper.create_topic(title=self.submission.title,
                                                        description=self.submission.description,
                                                        original_poster_slack_user_id=self.slack_user_id,
                                                        tag_names=tag_names)
        # TODO [CCS-15] caching user info to avoid relying on error
        # if portal errors due to lack of user info..
        #   fetch user info
        #   re-send the info to portal w/ addition of user info
        pass
