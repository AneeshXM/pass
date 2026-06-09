# API Documentation

## Base URL
```
http://localhost/api/v1
```

## Authentication

All API endpoints (except `/auth/login`, `/auth/refresh`, and `/auth/password-reset`) require authentication using JWT Bearer tokens.

### Authentication Flow

1. **Login**: `POST /auth/login`
   - Returns access token and refresh token
   - If MFA is enabled, returns partial token requiring MFA verification

2. **MFA Verification**: `POST /auth/verify-mfa`
   - Required when MFA is enabled
   - Returns full access and refresh tokens

3. **Token Refresh**: `POST /auth/refresh`
   - Use refresh token to get new access token

---

## Endpoints

### Authentication

#### POST /auth/login
Login with email and password.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

#### POST /auth/verify-mfa
Verify MFA code after login.

**Headers:** `Authorization: Bearer <partial_token>`

**Query Parameters:**
- `code`: 6-digit TOTP code or backup code

#### POST /auth/refresh
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

#### POST /auth/logout
Logout current user.

**Headers:** `Authorization: Bearer <token>`

#### GET /auth/me
Get current user info.

**Headers:** `Authorization: Bearer <token>`

**Response:**
```json
{
  "id": 1,
  "email": "admin@passwordmanager.local",
  "username": "admin",
  "full_name": "System Administrator",
  "is_active": true,
  "is_superuser": true,
  "role_id": 1,
  "mfa_enabled": false
}
```

---

### Users

#### GET /users/
List all users (admin only).

**Headers:** `Authorization: Bearer <admin_token>`

**Query Parameters:**
- `skip`: Pagination offset (default: 0)
- `limit`: Page size (default: 100)
- `search`: Search by email, name, or username
- `role_id`: Filter by role

#### POST /users/
Create new user (admin only).

**Request:**
```json
{
  "email": "newuser@example.com",
  "username": "newuser",
  "full_name": "New User",
  "password": "SecurePass123!"
}
```

#### GET /users/me
Get current user profile.

#### PUT /users/me
Update current user profile.

**Request:**
```json
{
  "full_name": "Updated Name",
  "phone": "+1234567890"
}
```

#### PUT /users/me/password
Change current user password.

**Request:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

#### POST /users/{id}/activate
Activate user (admin only).

#### POST /users/{id}/deactivate
Deactivate user (admin only).

---

### Vaults

#### GET /vaults/
List all vaults accessible by current user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `skip`: Pagination offset
- `limit`: Page size
- `search`: Search by vault name
- `shared_only`: Filter shared vaults only

#### POST /vaults/
Create new vault.

**Request:**
```json
{
  "name": "Work Accounts",
  "description": "Work-related credentials",
  "icon": "briefcase",
  "color": "#4F46E5",
  "is_shared": false
}
```

#### GET /vaults/{id}
Get vault details.

#### PUT /vaults/{id}
Update vault.

#### DELETE /vaults/{id}
Delete vault (owner only).

#### POST /vaults/{id}/share
Share vault with another user.

**Query Parameters:**
- `user_id`: User ID to share with
- `can_read`: Read permission (default: true)
- `can_write`: Write permission (default: false)
- `can_share`: Share permission (default: false)
- `can_delete`: Delete permission (default: false)

#### DELETE /vaults/{id}/share/{user_id}
Remove vault sharing.

---

### Credentials

#### GET /credentials/
List credentials in a vault.

**Query Parameters:**
- `vault_id`: Vault ID (required)
- `skip`: Pagination offset
- `limit`: Page size
- `search`: Search credentials
- `favorites_only`: Show only favorites

#### POST /credentials/
Create new credential.

**Request:**
```json
{
  "name": "Gmail",
  "url": "https://gmail.com",
  "username": "user@gmail.com",
  "password": "encrypted_password",
  "notes": "Personal email",
  "vault_id": 1,
  "expires_at": "2025-12-31"
}
```

#### GET /credentials/{id}
Get credential (without password).

#### GET /credentials/{id}/password
Get credential with decrypted password.

#### PUT /credentials/{id}
Update credential.

#### DELETE /credentials/{id}
Delete credential.

#### POST /credentials/{id}/favorite
Toggle favorite status.

#### GET /credentials/all/
List all credentials across all vaults.

---

### Tags

#### GET /tags/
List tags for a vault.

**Query Parameters:**
- `vault_id`: Vault ID (required)

#### POST /tags/
Create new tag.

**Request:**
```json
{
  "name": "important",
  "color": "#EF4444",
  "vault_id": 1
}
```

#### DELETE /tags/{id}
Delete tag.

---

### Groups

#### GET /groups/
List groups current user is member of.

#### POST /groups/
Create new group.

**Request:**
```json
{
  "name": "Engineering Team",
  "description": "Engineering department"
}
```

#### POST /groups/{id}/members
Add members to group.

**Request:**
```json
{
  "user_ids": [1, 2, 3]
}
```

#### DELETE /groups/{id}/members
Remove member from group.

**Query Parameters:**
- `user_id`: User ID to remove

---

### Audit

#### GET /audit/logs
List audit logs (admin only).

**Query Parameters:**
- `skip`: Pagination offset
- `limit`: Page size
- `user_id`: Filter by user
- `action`: Filter by action type
- `resource_type`: Filter by resource type
- `start_date`: Filter from date
- `end_date`: Filter to date

#### GET /audit/logs/me
List current user's audit logs.

#### GET /audit/dashboard
Get dashboard statistics.

**Response:**
```json
{
  "total_vaults": 5,
  "total_credentials": 25,
  "shared_vaults": 2,
  "expiring_credentials": 3,
  "recent_activity": 15,
  "favorites_count": 8
}
```

---

### MFA

#### GET /mfa/status
Get MFA status.

**Response:**
```json
{
  "enabled": true,
  "has_recovery_codes": true
}
```

#### POST /mfa/setup
Setup MFA (generate secret and QR code).

**Response:**
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code": "base64_encoded_qr_image",
  "backup_codes": ["ABCD1234", "EFGH5678", ...]
}
```

#### POST /mfa/enable
Enable MFA after verification.

**Request:**
```json
{
  "password": "current_password",
  "code": "123456"
}
```

#### POST /mfa/disable
Disable MFA.

**Request:**
```json
{
  "password": "current_password",
  "code": "123456"
}
```

#### POST /mfa/verify
Verify MFA code.

**Request:**
```json
{
  "code": "123456"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message description"
}
```

### Common Status Codes

- `200 OK`: Success
- `201 Created`: Resource created
- `204 No Content`: Resource deleted
- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Invalid or expired token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

---

## Rate Limiting

- General API: 100 requests per minute per user
- Authentication endpoints: 20 requests per minute per IP
- Login: 5 attempts per minute, then 15-minute lockout