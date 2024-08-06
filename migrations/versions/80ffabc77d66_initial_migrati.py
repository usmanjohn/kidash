"""Initial migrati

Revision ID: 80ffabc77d66
Revises: 7bbc7fb173d4
Create Date: 2024-08-06 19:24:25.763324

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '80ffabc77d66'
down_revision = '7bbc7fb173d4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('upload_main',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=256), nullable=False),
    sa.Column('s3_key', sa.String(length=256), nullable=False),
    sa.Column('upload_date', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('upload_support',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('filename', sa.String(length=256), nullable=False),
    sa.Column('s3_key', sa.String(length=256), nullable=False),
    sa.Column('upload_date', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.drop_table('upload_2')
    op.drop_table('upload_1')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('upload_1',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('filename', sa.VARCHAR(length=256), autoincrement=False, nullable=False),
    sa.Column('s3_key', sa.VARCHAR(length=256), autoincrement=False, nullable=False),
    sa.Column('upload_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='upload_1_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='upload_1_pkey')
    )
    op.create_table('upload_2',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('filename', sa.VARCHAR(length=256), autoincrement=False, nullable=False),
    sa.Column('s3_key', sa.VARCHAR(length=256), autoincrement=False, nullable=False),
    sa.Column('upload_date', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('user_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name='upload_2_user_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='upload_2_pkey')
    )
    op.drop_table('upload_support')
    op.drop_table('upload_main')
    # ### end Alembic commands ###
