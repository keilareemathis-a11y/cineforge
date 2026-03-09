"""add shot_version status, image_url, video_url, prompt, style

Revision ID: a3f8b1c2d4e5
Revises: 715423cb9dea
Create Date: 2026-03-09 02:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f8b1c2d4e5'
down_revision: Union[str, Sequence[str], None] = '715423cb9dea'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add status, image_url, video_url, prompt, style columns to shot_versions."""
    op.add_column('shot_versions', sa.Column('status', sa.String(), nullable=False, server_default='queued'))
    op.add_column('shot_versions', sa.Column('image_url', sa.String(), nullable=True))
    op.add_column('shot_versions', sa.Column('video_url', sa.String(), nullable=True))
    op.add_column('shot_versions', sa.Column('prompt', sa.Text(), nullable=True))
    op.add_column('shot_versions', sa.Column('style', sa.String(), nullable=True))


def downgrade() -> None:
    """Remove added columns from shot_versions."""
    op.drop_column('shot_versions', 'style')
    op.drop_column('shot_versions', 'prompt')
    op.drop_column('shot_versions', 'video_url')
    op.drop_column('shot_versions', 'image_url')
    op.drop_column('shot_versions', 'status')
