"""phase3: membership plans and memberships

Revision ID: 7dd8de8571c1
Revises: bec5fb5053bb
Create Date: 2026-08-25 01:06:23.066527

"""
from __future__ import annotations

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '7dd8de8571c1'
down_revision: str | Sequence[str] | None = 'bec5fb5053bb'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Membership plans (Phase 3)
    op.create_table(
        'membership_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_membership_plans_is_active'), 'membership_plans', ['is_active'], unique=False)

    # Payments placeholder (Phase 3; fields filled in by Phase 4 migration)
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('provider', sa.String(length=40), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reference', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_payments_user_id'), 'payments', ['user_id'], unique=False)

    # Memberships
    op.create_table(
        'memberships',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'ACTIVE', 'EXPIRED', 'CANCELLED', name='membership_status', native_enum=False, length=20), nullable=False),
        sa.Column('price_cents', sa.Integer(), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False),
        sa.Column('activated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('payment_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['payments.id'], ondelete='SET NULL', name='fk_memberships_payment_id', use_alter=True),
        sa.ForeignKeyConstraint(['plan_id'], ['membership_plans.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('payment_id', 'uq_memberships_payment_id'),
    )
    op.create_index(op.f('ix_memberships_end_date'), 'memberships', ['end_date'], unique=False)
    op.create_index(op.f('ix_memberships_plan_id'), 'memberships', ['plan_id'], unique=False)
    op.create_index(op.f('ix_memberships_user_id'), 'memberships', ['user_id'], unique=False)
    op.create_index(op.f('ix_memberships_user_status'), 'memberships', ['user_id', 'status'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_memberships_user_status'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_user_id'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_plan_id'), table_name='memberships')
    op.drop_index(op.f('ix_memberships_end_date'), table_name='memberships')
    op.drop_table('memberships')
    op.drop_index(op.f('ix_payments_user_id'), table_name='payments')
    op.drop_table('payments')
    op.drop_index(op.f('ix_membership_plans_is_active'), table_name='membership_plans')
    op.drop_table('membership_plans')