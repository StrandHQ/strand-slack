from marshmallow import Schema, fields, post_load

from src.domain.models.portal.SlackProfile import SlackProfileSchema


class SlackUser:
    def __init__(self, id, name, real_name=None, is_bot=None, is_admin=None, team_id=None, profile=None):
        self.id = id
        self.name = name
        self.real_name = real_name
        self.is_bot = is_bot
        self.is_admin = is_admin
        self.team_id = team_id
        self.profile = profile


class SlackUserSchema(Schema):
    id = fields.String(required=True)
    name = fields.String(required=True)
    real_name = fields.String()
    is_bot = fields.Boolean()
    is_admin = fields.Boolean()
    team_id = fields.String()
    profile = fields.Nested(SlackProfileSchema)

    @post_load
    def make_slack_user(self, data):
        return SlackUser(**data)
