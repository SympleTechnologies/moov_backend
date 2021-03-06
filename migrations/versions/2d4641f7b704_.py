"""empty message

Revision ID: 2d4641f7b704
Revises: f10eb3222220
Create Date: 2018-03-27 18:32:12.305669

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d4641f7b704'
down_revision = 'f10eb3222220'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ForgotPassword',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('user_id', sa.String(), nullable=True),
    sa.Column('temp_password', sa.String(), nullable=True),
    sa.Column('used', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['User.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'User', sa.Column('reset_password', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'User', 'reset_password')
    op.drop_table('ForgotPassword')
    # ### end Alembic commands ###
