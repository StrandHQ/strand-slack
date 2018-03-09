from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from src.utilities.database import Base


class Bot(Base):
    __tablename__ = 'bot'

    access_token = Column(String)
    user_id = Column(String)

    agent_slack_team_id = Column(String, ForeignKey('agent.slack_team_id'), primary_key=True)
    agent = relationship('Agent', back_populates='bot')
