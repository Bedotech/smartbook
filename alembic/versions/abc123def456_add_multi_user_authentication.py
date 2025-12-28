"""Add multi-user authentication

Revision ID: abc123def456
Revises: 874b7b402569
Create Date: 2025-12-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = 'abc123def456'
down_revision: Union[str, Sequence[str], None] = '874b7b402569'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add multi-user authentication."""

    # STEP 1: Rename tenants table to properties
    op.rename_table('tenants', 'properties')

    # STEP 2: Rename tenant_id columns to property_id in dependent tables

    # Bookings table
    op.alter_column('bookings', 'tenant_id', new_column_name='property_id')

    # Tax rules table
    op.alter_column('tax_rules', 'tenant_id', new_column_name='property_id')

    # STEP 3: Update indexes
    op.drop_index('ix_bookings_tenant_id', table_name='bookings')
    op.create_index(op.f('ix_bookings_property_id'), 'bookings', ['property_id'], unique=False)

    op.drop_index('ix_tax_rules_tenant_id', table_name='tax_rules')
    op.create_index(op.f('ix_tax_rules_property_id'), 'tax_rules', ['property_id'], unique=False)

    # STEP 4: Update foreign key constraints
    # Drop old constraints
    op.drop_constraint('fk_bookings_tenant_id_tenants', 'bookings', type_='foreignkey')
    op.drop_constraint('fk_tax_rules_tenant_id_tenants', 'tax_rules', type_='foreignkey')

    # Create new constraints
    op.create_foreign_key(
        op.f('fk_bookings_property_id_properties'),
        'bookings',
        'properties',
        ['property_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        op.f('fk_tax_rules_property_id_properties'),
        'tax_rules',
        'properties',
        ['property_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # STEP 5: Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False, comment='User email address (unique)'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='User full name'),
        sa.Column('oauth_provider', sa.String(length=50), nullable=False, comment="OAuth provider (e.g., 'google', 'microsoft')"),
        sa.Column('oauth_provider_id', sa.String(length=255), nullable=False, comment='OAuth provider user ID (e.g., Google sub claim)'),
        sa.Column('oauth_picture_url', sa.String(length=500), nullable=True, comment='Profile picture URL from OAuth provider'),
        sa.Column('role', sa.String(length=50), nullable=False, comment="User role: 'admin' (full access) or 'staff' (view-only)"),
        sa.Column('is_active', sa.Boolean(), nullable=False, comment='Whether user account is active'),
        sa.Column('last_login_at', sa.DateTime(timezone=True), nullable=True, comment='Last successful login timestamp'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
        sa.UniqueConstraint('email', name=op.f('uq_users_email')),
    )

    # Create composite unique constraint for OAuth provider + provider ID
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index('ix_users_oauth', 'users', ['oauth_provider', 'oauth_provider_id'], unique=True)

    # STEP 6: Create user_property_assignments table (many-to-many junction)
    op.create_table(
        'user_property_assignments',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False, comment='Foreign key to users table'),
        sa.Column('property_id', sa.Uuid(), nullable=False, comment='Foreign key to properties table'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=False, comment='When this assignment was created'),
        sa.Column('assigned_by_user_id', sa.Uuid(), nullable=True, comment='Which user created this assignment (NULL for migration)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_property_assignments_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['property_id'], ['properties.id'], name=op.f('fk_user_property_assignments_property_id_properties'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['users.id'], name=op.f('fk_user_property_assignments_assigned_by_user_id_users'), ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_user_property_assignments')),
    )

    # Create indexes for efficient lookups
    op.create_index(op.f('ix_user_property_assignments_user_id'), 'user_property_assignments', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_property_assignments_property_id'), 'user_property_assignments', ['property_id'], unique=False)

    # Create composite unique constraint (user can't be assigned same property twice)
    op.create_index('ix_user_property_unique', 'user_property_assignments', ['user_id', 'property_id'], unique=True)

    # STEP 7: Data migration - create default admin user for each property
    # This ensures backward compatibility
    connection = op.get_bind()

    # Get all properties
    properties_result = connection.execute(
        text("SELECT id, email, name FROM properties")
    )
    properties = properties_result.fetchall()

    for property_id, email, name in properties:
        # Check if user with this email already exists
        existing_user = connection.execute(
            text("SELECT id FROM users WHERE email = :email"),
            {"email": email}
        ).fetchone()

        if existing_user:
            user_id = existing_user[0]
        else:
            # Create new user with placeholder OAuth info (will be updated on first login)
            user_result = connection.execute(
                text("""
                    INSERT INTO users (id, email, name, oauth_provider, oauth_provider_id, role, is_active)
                    VALUES (gen_random_uuid(), :email, :name, :oauth_provider, :oauth_provider_id, :role, :is_active)
                    RETURNING id
                """),
                {
                    "email": email,
                    "name": f"Admin - {name}",
                    "oauth_provider": "placeholder",
                    "oauth_provider_id": f"migration-{property_id}",
                    "role": "admin",
                    "is_active": True
                }
            )
            user_id = user_result.fetchone()[0]

        # Assign user to property
        connection.execute(
            text("""
                INSERT INTO user_property_assignments (id, user_id, property_id, assigned_at)
                VALUES (gen_random_uuid(), :user_id, :property_id, now())
            """),
            {
                "user_id": user_id,
                "property_id": property_id
            }
        )


def downgrade() -> None:
    """Downgrade schema - revert to single-tenant model."""

    # STEP 1: Drop user_property_assignments table
    op.drop_index('ix_user_property_unique', table_name='user_property_assignments')
    op.drop_index(op.f('ix_user_property_assignments_property_id'), table_name='user_property_assignments')
    op.drop_index(op.f('ix_user_property_assignments_user_id'), table_name='user_property_assignments')
    op.drop_table('user_property_assignments')

    # STEP 2: Drop users table
    op.drop_index('ix_users_oauth', table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # STEP 3: Revert foreign key constraints
    op.drop_constraint(op.f('fk_tax_rules_property_id_properties'), 'tax_rules', type_='foreignkey')
    op.drop_constraint(op.f('fk_bookings_property_id_properties'), 'bookings', type_='foreignkey')

    op.create_foreign_key(
        'fk_tax_rules_tenant_id_tenants',
        'tax_rules',
        'tenants',
        ['property_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_foreign_key(
        'fk_bookings_tenant_id_tenants',
        'bookings',
        'tenants',
        ['property_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # STEP 4: Revert indexes
    op.drop_index(op.f('ix_tax_rules_property_id'), table_name='tax_rules')
    op.create_index('ix_tax_rules_tenant_id', 'tax_rules', ['property_id'], unique=False)

    op.drop_index(op.f('ix_bookings_property_id'), table_name='bookings')
    op.create_index('ix_bookings_tenant_id', 'bookings', ['property_id'], unique=False)

    # STEP 5: Rename columns back
    op.alter_column('tax_rules', 'property_id', new_column_name='tenant_id')
    op.alter_column('bookings', 'property_id', new_column_name='tenant_id')

    # STEP 6: Rename table back
    op.rename_table('properties', 'tenants')
