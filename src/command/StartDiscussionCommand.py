from src.command.Command import Command
from src.command.model.message.message_models import ChannelTopicShareMessage
from src.command.model.message.TopicChannelTopicShareMessage import TopicChannelTopicShareMessage
from src.command.model.message.formatted_text import discussion_initiation_dm
from src.command.model.message.messages import TOPIC_CHANNEL_INTRO_MESSAGE, DiscussionInitiationMessage
from src.domain.models.exceptions.WrapperException import WrapperException
from src.domain.models.portal.SlackUser import SlackUserSchema
from src.domain.models.slack.Channel import ChannelSchema
from src.domain.models.slack.requests.elements.Message import MessageSchema
from src.domain.repositories.SlackAgentRepository import slack_agent_repository


class StartDiscussionCommand(Command):
    def __init__(self, slack_client_wrapper, portal_client_wrapper, slack_team_id, submission, slack_user_id,
                 slack_channel_id):
        super().__init__(slack_team_id=slack_team_id, slack_client_wrapper=slack_client_wrapper,
                         portal_client_wrapper=portal_client_wrapper)
        self.submission = submission
        self.slack_user_id = slack_user_id
        self.slack_channel_id = slack_channel_id

    def execute(self):
        """
            Start discussion by:
                1) Persist Discussion
                2) Create Channel for Discussion
                3) Invite bot & OP to Channel
                4) Post the OP's topic
                5) Update topic channel with the topic
                6) DM the OP with details
        """
        self.logger.info(f'Executing StartDiscussionCommand for {self.slack_team_id}')
        try:
            topic = self._create_topic()
            slack_channel = self._create_channel(topic=topic)
            self.portal_client_wrapper.create_discussion(topic_id=topic.id, slack_channel=slack_channel,
                                                         slack_team_id=self.slack_team_id)
            slack_bot_user_id = slack_agent_repository.get_slack_bot_user_id(slack_team_id=self.slack_team_id)

            # invite bot
            self.slack_client_wrapper.invite_user_to_channel(slack_team_id=self.slack_team_id,
                                                             slack_channel_id=slack_channel.id,
                                                             slack_user_id=slack_bot_user_id)

            # invite original poster
            installer_slack_user_id = slack_agent_repository.get_installer_slack_user_id(self.slack_team_id)
            if installer_slack_user_id != self.slack_user_id:  # Slack auto-adds the oauth'd user
                self.slack_client_wrapper.invite_user_to_channel(slack_team_id=self.slack_team_id,
                                                                 slack_channel_id=slack_channel.id,
                                                                 slack_user_id=self.slack_user_id)

            DISCUSSION_INITIATION_MESSAGE = DiscussionInitiationMessage(
                original_poster_slack_user_id=self.slack_user_id,
                title=self.submission.title,
                description=self.submission.description,
                tags=self.submission.tags
            )
            self.slack_client_wrapper.send_message(slack_team_id=self.slack_team_id,
                                                   slack_channel_id=slack_channel.id,
                                                   text=DISCUSSION_INITIATION_MESSAGE.text,
                                                   attachments=DISCUSSION_INITIATION_MESSAGE.as_dict()['attachments'])

            self._add_topic_to_topic_channel(topic=topic, original_poster_slack_user_id=self.slack_user_id,
                                             discussion_channel_id=slack_channel.id)

            # TODO: Move this type of logic to a service
            if self.submission.share_with_current_channel:
                self._add_topic_to_channel(topic=topic, original_poster_slack_user_id=self.slack_user_id,
                                           discussion_channel_id=slack_channel.id, channel_id=self.slack_channel_id)

            self.slack_client_wrapper.send_dm_to_user(slack_team_id=self.slack_team_id,
                                                      slack_user_id=self.slack_user_id,
                                                      text=discussion_initiation_dm(slack_channel_id=slack_channel.id))
        except WrapperException as e:
            self.logger.error(f'Starting discussion failed. Submission: {self.submission}. Error: {e}')
            self.slack_client_wrapper.send_dm_to_user(slack_team_id=self.slack_team_id,
                                                      slack_user_id=self.slack_user_id,
                                                      text='Sorry, starting your discussion failed for some reason'
                                                           ' :see_no_evil: Please contact support@solutionloft.com')

    def _create_topic(self):
        # TODO [SLA-60] move tag parsing to useful validation (maybe derived attr on Submission)
        tag_names = [x.strip() for x in self.submission.tags.split(',')]
        try:
            topic = self.portal_client_wrapper.create_topic(title=self.submission.title,
                                                            description=self.submission.description,
                                                            original_poster_slack_user_id=self.slack_user_id,
                                                            tag_names=tag_names)
        except WrapperException as e:
            # TODO [SLA-15] caching user info to avoid relying on error
            if e.errors and e.errors[0]['message'] == 'SlackUser matching query does not exist.':
                self.logger.info('Tried to create topic for unknown user. Retrying with user creation.')
                slack_user_info = self.slack_client_wrapper.get_user_info(slack_user_id=self.slack_user_id,
                                                                          slack_team_id=self.slack_team_id)
                slack_user = SlackUserSchema().load(slack_user_info).data
                topic = self.portal_client_wrapper.create_topic_and_user_as_original_poster(
                    title=self.submission.title,
                    description=self.submission.description,
                    slack_user=slack_user,
                    tag_names=tag_names
                )
            else:
                raise e

        return topic

    def _create_channel(self, topic):
        channel_name = f'discussion-{topic.id}'
        slack_channel_info = self.slack_client_wrapper.create_channel(slack_team_id=self.slack_team_id,
                                                                      channel_name=channel_name)
        return ChannelSchema().load(slack_channel_info).data

    def _add_topic_to_topic_channel(self, topic, original_poster_slack_user_id, discussion_channel_id):
        topic_channel_id = slack_agent_repository.get_topic_channel_id(slack_team_id=self.slack_team_id)
        intro_message_info = self.slack_client_wrapper.get_last_channel_message(slack_team_id=self.slack_team_id,
                                                                                slack_channel_id=topic_channel_id)
        intro_message = MessageSchema().load(intro_message_info).data
        topic_channel_post = TopicChannelTopicShareMessage(original_poster_user_id=original_poster_slack_user_id,
                                                           discussion_channel_id=discussion_channel_id,
                                                           title=topic.title,
                                                           tag_names=[tag.name for tag in topic.tags])
        self.slack_client_wrapper.update_message(slack_team_id=self.slack_team_id, slack_channel_id=topic_channel_id,
                                                 new_text=topic_channel_post.text,
                                                 attachments=topic_channel_post.attachments,
                                                 message_ts=intro_message.ts)
        self.slack_client_wrapper.send_message(
            slack_team_id=self.slack_team_id,
            slack_channel_id=topic_channel_id,
            text=TOPIC_CHANNEL_INTRO_MESSAGE.text,
            attachments=TOPIC_CHANNEL_INTRO_MESSAGE.as_dict()['attachments']
        )

    def _add_topic_to_channel(self, topic, original_poster_slack_user_id, discussion_channel_id, channel_id):
        channel_post = ChannelTopicShareMessage(original_poster_user_id=original_poster_slack_user_id,
                                                discussion_channel_id=discussion_channel_id,
                                                title=topic.title,
                                                tag_names=[tag.name for tag in topic.tags])
        self.slack_client_wrapper.send_message(
            slack_team_id=self.slack_team_id,
            slack_channel_id=channel_id,
            text=channel_post.text,
            attachments=channel_post.attachments
        )
