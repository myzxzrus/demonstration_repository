"""0.0.1_init

Revision ID: 82c157bd105f
Revises: 
Create Date: 2022-06-21 20:23:40.017927

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82c157bd105f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('id', sa.TEXT(), nullable=False),
    sa.Column('created_utc', sa.TIMESTAMP(), nullable=False),
    sa.Column('updated_utc', sa.TIMESTAMP(), nullable=False),
    sa.Column('lastname', sa.TEXT(), nullable=True),
    sa.Column('firstname', sa.TEXT(), nullable=True),
    sa.Column('middlename', sa.TEXT(), nullable=True),
    sa.Column('email', sa.TEXT(), nullable=True),
    sa.Column('phone', sa.TEXT(), nullable=True),
    sa.Column('gender', sa.TEXT(), nullable=True),
    sa.Column('birthday', sa.DATE(), nullable=True),
    sa.Column('login', sa.TEXT(), nullable=False),
    sa.Column('password', sa.TEXT(), nullable=False),
    sa.Column('is_locked', sa.BOOLEAN(), nullable=False),
    sa.Column('is_admin', sa.BOOLEAN(), nullable=False),
    sa.Column('is_superadmin', sa.BOOLEAN(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    schema='vision'
    )
    # ### end Alembic commands ###

    op.create_table('reset_password',
    sa.Column('id', sa.TEXT(), nullable=False),
    sa.Column('created_utc', sa.TIMESTAMP(), nullable=False),
    sa.Column('disabled_utc', sa.TIMESTAMP(), nullable=False),
    sa.Column('user_id', sa.TEXT(), nullable=False),
    sa.Column('secret_key', sa.String(length=6), nullable=False),
    sa.Column('email', sa.TEXT(), nullable=False),
    sa.Column('is_reset', sa.BOOLEAN(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['vision.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='vision'
    )

    op.create_table('games',
    sa.Column('id', sa.TEXT(), nullable=False),
    sa.Column('created_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('name', sa.TEXT(), nullable=False),
    sa.Column('code_name', sa.TEXT(), nullable=False),
    sa.Column('descriptions', sa.TEXT(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='vision'
    )

    op.execute("""INSERT INTO "vision"."games"("id", "created_utc", "updated_utc", "name", "code_name", "descriptions") VALUES('681082bf-83c5-4861-a121-b51941e22d04', '2023-02-02 21:12:33.743019'::timestamp,   '2023-02-02 21:12:33.743019'::timestamp, 'палитра', 'palitra', 'Игра палитра')""")
    op.execute("""INSERT INTO "vision"."games"("id", "created_utc", "updated_utc", "name", "code_name", "descriptions") VALUES('bf4c6f0c-db2d-4942-8a0b-99e646665164', '2023-02-02 21:12:33.743019'::timestamp,   '2023-02-02 21:12:33.743019'::timestamp, 'объем', 'volume', 'Игра объем')""")

    op.create_table('games_played',
    sa.Column('id', sa.TEXT(), nullable=False),
    sa.Column('created_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('user_id', sa.TEXT(), nullable=False),
    sa.Column('game_id', sa.TEXT(), nullable=False),
    sa.Column('points', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['vision.users.id'], ),
    sa.ForeignKeyConstraint(['game_id'], ['vision.games.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='vision'
    )

    op.create_table('users_photo',
    sa.Column('id', sa.TEXT(), nullable=False),
    sa.Column('created_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('user_id', sa.TEXT(), nullable=False),
    sa.Column('filename', sa.TEXT(), nullable=False),
    sa.Column('content_type', sa.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['vision.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id'),
    schema='vision'
    )

    op.create_table('allowed_games',
    sa.Column('id', sa.TEXT(), nullable=False),
    sa.Column('created_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('user_id', sa.TEXT(), nullable=False),
    sa.Column('game_id', sa.TEXT(), nullable=False),
    sa.ForeignKeyConstraint(['game_id'], ['vision.games.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['vision.users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='vision'
    )

    op.create_table('audit',
    sa.Column('id', sa.TEXT(), nullable=False),
    sa.Column('created_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_utc', sa.TIMESTAMP(), server_default=sa.text('now()'), nullable=False),
    sa.Column('user', sa.TEXT(), nullable=False),
    sa.Column('action', sa.TEXT(), nullable=False),
    sa.Column('date', sa.TIMESTAMP(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    schema='vision'
    )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('allowed_games', schema='vision')
    op.drop_table('users_photo', schema='vision')
    op.drop_table('games_played', schema='vision')
    op.drop_table('games', schema='vision')
    op.drop_table('reset_password', schema='vision')
    op.drop_table('users', schema='vision')
    op.drop_table('audit', schema='vision')
    # ### end Alembic commands ###
