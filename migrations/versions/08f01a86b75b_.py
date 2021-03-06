"""empty message

Revision ID: 08f01a86b75b
Revises: c8edf8c9e8ce
Create Date: 2018-04-24 23:05:30.307313

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '08f01a86b75b'
down_revision = 'c8edf8c9e8ce'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(u'AdmissionType_school_id_fkey', 'AdmissionType', type_='foreignkey')
    op.create_foreign_key(None, 'AdmissionType', 'SchoolInfo', ['school_id'], ['id'], ondelete='SET NULL')
    op.add_column('ForgotPassword', sa.Column('school_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'ForgotPassword', 'SchoolInfo', ['school_id'], ['id'], ondelete='SET NULL')
    op.add_column('PercentagePrice', sa.Column('school_id', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'PercentagePrice', ['school_id'])
    op.create_foreign_key(None, 'PercentagePrice', 'SchoolInfo', ['school_id'], ['id'])
    op.add_column('SchoolInfo', sa.Column('admin_status', sa.Boolean(), nullable=True))
    op.add_column('SchoolInfo', sa.Column('alias', sa.String(), nullable=True))
    op.add_column('SchoolInfo', sa.Column('email', sa.String(), nullable=False))
    op.add_column('SchoolInfo', sa.Column('name', sa.String(), nullable=False))
    op.add_column('SchoolInfo', sa.Column('password', sa.String(), nullable=True))
    op.add_column('SchoolInfo', sa.Column('reset_password', sa.Boolean(), nullable=True))
    op.add_column('SchoolInfo', sa.Column('user_type_id', sa.String(), nullable=True))
    op.alter_column('SchoolInfo', 'account_number',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.alter_column('SchoolInfo', 'bank_name',
               existing_type=sa.VARCHAR(),
               nullable=False)
    op.drop_constraint(u'SchoolInfo_school_id_key', 'SchoolInfo', type_='unique')
    op.create_unique_constraint(None, 'SchoolInfo', ['email'])
    op.create_unique_constraint(None, 'SchoolInfo', ['name'])
    op.drop_constraint(u'SchoolInfo_school_id_fkey', 'SchoolInfo', type_='foreignkey')
    op.create_foreign_key(None, 'SchoolInfo', 'UserType', ['user_type_id'], ['id'], ondelete='SET NULL')
    op.drop_column('SchoolInfo', 'school_id')
    op.add_column('User', sa.Column('school_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'User', 'SchoolInfo', ['school_id'], ['id'])
    op.add_column('Wallet', sa.Column('school_id', sa.String(), nullable=True))
    op.create_foreign_key(None, 'Wallet', 'SchoolInfo', ['school_id'], ['id'])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'Wallet', type_='foreignkey')
    op.drop_column('Wallet', 'school_id')
    op.drop_constraint(None, 'User', type_='foreignkey')
    op.drop_column('User', 'school_id')
    op.add_column('SchoolInfo', sa.Column('school_id', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'SchoolInfo', type_='foreignkey')
    op.create_foreign_key(u'SchoolInfo_school_id_fkey', 'SchoolInfo', 'User', ['school_id'], ['id'])
    op.drop_constraint(None, 'SchoolInfo', type_='unique')
    op.drop_constraint(None, 'SchoolInfo', type_='unique')
    op.create_unique_constraint(u'SchoolInfo_school_id_key', 'SchoolInfo', ['school_id'])
    op.alter_column('SchoolInfo', 'bank_name',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.alter_column('SchoolInfo', 'account_number',
               existing_type=sa.VARCHAR(),
               nullable=True)
    op.drop_column('SchoolInfo', 'user_type_id')
    op.drop_column('SchoolInfo', 'reset_password')
    op.drop_column('SchoolInfo', 'password')
    op.drop_column('SchoolInfo', 'name')
    op.drop_column('SchoolInfo', 'email')
    op.drop_column('SchoolInfo', 'alias')
    op.drop_column('SchoolInfo', 'admin_status')
    op.drop_constraint(None, 'PercentagePrice', type_='foreignkey')
    op.drop_constraint(None, 'PercentagePrice', type_='unique')
    op.drop_column('PercentagePrice', 'school_id')
    op.drop_constraint(None, 'ForgotPassword', type_='foreignkey')
    op.drop_column('ForgotPassword', 'school_id')
    op.drop_constraint(None, 'AdmissionType', type_='foreignkey')
    op.create_foreign_key(u'AdmissionType_school_id_fkey', 'AdmissionType', 'User', ['school_id'], ['id'], ondelete=u'SET NULL')
    # ### end Alembic commands ###
