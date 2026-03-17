from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import mapped_column, relationship

from infrastructure.db.models.base import Base


class OAuthAccount(Base):
    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("provider", "oauth_subject", name="uq_oauth_provider_subject"),)

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = mapped_column(String(32), nullable=False, index=True)
    oauth_subject = mapped_column(String(128), nullable=False, index=True)

    user = relationship("User", back_populates="oauth_accounts", lazy="selectin")
