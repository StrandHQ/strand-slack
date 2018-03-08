from http.__init__ import HTTPStatus

from flask import Flask, jsonify
from marshmallow import ValidationError

from src.blueprints import slack, portal
from src.common.logging import get_logger
from src.domain.models.exceptions.RepositoryException import RepositoryException
from src.domain.models.exceptions.UnauthorizedException import UnauthorizedException
from src.domain.models.exceptions.UnexpectedSlackException import UnexpectedSlackException
from src.domain.models.exceptions.WrapperException import WrapperException
from src.domain.repositories.SlackAgentRepository import slack_agent_repository
from src.wrappers.PortalClientWrapper import PortalClientWrapper
from src.wrappers.SlackClientWrapper import SlackClientWrapper


def handle_slack_integration_exception(error):
    logger = get_logger('Flask')
    response = jsonify({'error': error.message if error.message else repr(error)})
    response.status_code = HTTPStatus.INTERNAL_SERVER_ERROR
    logger.error(response.data)
    return response


def handle_validation_exception(error):
    logger = get_logger('Flask')
    response = jsonify({'error': error.messages})
    response.status_code = HTTPStatus.BAD_REQUEST
    logger.error(response.data)
    return response


def handle_authorization_exception(error):
    logger = get_logger('Flask')
    response = jsonify({'error': error.message if error.message else repr(error)})
    response.status_code = HTTPStatus.UNAUTHORIZED
    logger.error(response.data)
    return response


def create_app(portal_client, SlackClientClass, slack_verification_tokens, portal_verification_token):
    app = Flask(__name__)

    app.register_blueprint(portal.blueprint, url_prefix='/portal')
    app.register_blueprint(slack.blueprint, url_prefix='/slack')

    app.add_url_rule('/health', None, lambda: 'Ok')

    app.register_error_handler(UnauthorizedException, handle_authorization_exception)
    app.register_error_handler(ValidationError, handle_validation_exception)
    app.register_error_handler(RepositoryException, handle_slack_integration_exception)
    app.register_error_handler(UnexpectedSlackException, handle_slack_integration_exception)
    app.register_error_handler(WrapperException, handle_slack_integration_exception)

    init_wrappers(app=app, portal_client=portal_client, SlackClientClass=SlackClientClass)
    init_authentication(app=app, slack_verification_tokens=slack_verification_tokens,
                        portal_verification_token=portal_verification_token)

    return app


def init_wrappers(app, portal_client, SlackClientClass):
    app.portal_client_wrapper = PortalClientWrapper(portal_client=portal_client)
    slack_agents = app.portal_client_wrapper.get_slack_agents()
    slack_agent_repository.set_slack_agents(slack_agents=slack_agents)
    app.slack_client_wrapper = SlackClientWrapper(SlackClientClass=SlackClientClass)


def init_authentication(app, slack_verification_tokens, portal_verification_token):
    app.slack_verification_tokens = slack_verification_tokens
    app.portal_verification_token = portal_verification_token
