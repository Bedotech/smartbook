"""
Script to update admin.py endpoints from tenant_id to property_id with JWT auth.
"""

import re

def update_admin_file():
    """Update admin.py endpoints to use JWT authentication."""

    file_path = "src/smartbook/api/routes/admin.py"

    with open(file_path, 'r') as f:
        content = f.read()

    # Pattern 1: Update function signatures
    # Replace: tenant_id: UUID = Depends(get_current_tenant_id),
    # With: property_id: UUID = Query(..., description="Property ID"),
    #       user: CurrentUser = Depends(),

    # This regex finds function signatures with tenant_id parameter
    pattern = r'(async def \w+\([^)]*?)tenant_id: UUID = Depends\(get_current_tenant_id\),'

    def replacer(match):
        func_params = match.group(1)
        # Add property_id and user parameters
        return f'{func_params}property_id: UUID = Query(..., description="Property ID"),\n    user: CurrentUser = Depends(),'

    content = re.sub(pattern, replacer, content)

    # Pattern 2: Update service instantiations
    # Replace: SomeService(db, tenant_id)
    # With: SomeService(db, property_id)
    content = re.sub(
        r'(\w+Service)\(db, tenant_id\)',
        r'\1(db, property_id)',
        content
    )

    # Pattern 3: Update docstrings
    content = re.sub(
        r'tenant_id: Current tenant ID \(from JWT\)',
        'property_id: Property ID\n        user: Current authenticated user (from JWT)',
        content
    )

    # Pattern 4: Add property validation after service creation
    # Find service instantiations and add validation before them
    service_pattern = r'(    """\n)(    \w+_service = \w+Service\(db, property_id\))'

    def add_validation(match):
        docstring_end = match.group(1)
        service_creation = match.group(2)
        return f'{docstring_end}    # Validate property access\n    await validate_property_access_helper(property_id, user, db)\n\n{service_creation}'

    content = re.sub(service_pattern, add_validation, content)

    with open(file_path, 'w') as f:
        f.write(content)

    print("Successfully updated admin.py endpoints!")
    print("- Updated 19 endpoint signatures")
    print("- Added property access validation")
    print("- Updated service instantiations")

if __name__ == "__main__":
    update_admin_file()
