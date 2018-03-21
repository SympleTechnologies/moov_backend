"""empty message

Revision ID: 90b97df7f038
Revises: 9d0a424f9e32
Create Date: 2018-03-21 12:46:34.678644

"""
from alembic import op
import sqlalchemy as sa

from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision = '90b97df7f038'
down_revision = '9d0a424f9e32'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('RateMe',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('rating_type', ENUM('no_ratings', 'one', 'two', 'three', 'four', 'five', name='ratingstype'), nullable=False),
    sa.Column('ratee_id', sa.String(), nullable=True),
    sa.Column('rater_id', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('modified_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ratee_id'], ['User.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['rater_id'], ['User.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'DriverInfo', sa.Column('available_car_slots', sa.Integer(), nullable=True))
    op.add_column(u'DriverInfo', sa.Column('car_slots', sa.Integer(), nullable=False))
    op.add_column(u'DriverInfo', sa.Column('destination_latitude', sa.Float(), nullable=True))
    op.add_column(u'DriverInfo', sa.Column('destination_longitude', sa.Float(), nullable=True))
    op.add_column(u'DriverInfo', sa.Column('location_latitude', sa.Float(), nullable=True))
    op.add_column(u'DriverInfo', sa.Column('location_longitude', sa.Float(), nullable=True))
    op.add_column(u'DriverInfo', sa.Column('on_trip_with', sa.JSON(), nullable=True))
    op.add_column(u'DriverInfo', sa.Column('status', sa.Boolean(), nullable=True))
    op.add_column(u'User', sa.Column('ratings', sa.Integer(), nullable=True))
    op.add_column(u'User', sa.Column('user_id', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'User', ['user_id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'User', type_='unique')
    op.drop_column(u'User', 'user_id')
    op.drop_column(u'User', 'ratings')
    op.drop_column(u'DriverInfo', 'status')
    op.drop_column(u'DriverInfo', 'on_trip_with')
    op.drop_column(u'DriverInfo', 'location_longitude')
    op.drop_column(u'DriverInfo', 'location_latitude')
    op.drop_column(u'DriverInfo', 'destination_longitude')
    op.drop_column(u'DriverInfo', 'destination_latitude')
    op.drop_column(u'DriverInfo', 'car_slots')
    op.drop_column(u'DriverInfo', 'available_car_slots')
    op.drop_table('RateMe')
    # ### end Alembic commands ###
