from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission

class User(AbstractUser):
    """
    TABLE 1: users (Extends Django's AbstractUser)
    Contains all foundational credentials, personal details, contact info, 
    and verification statuses for any user accessing PRAVAAH.
    
    Inherited Fields from AbstractUser:
        - id (INT, Primary Key, Auto-increment) -> Acts as user_id
        - username (VARCHAR, Unique)
        - password (VARCHAR) -> Acts as password_hash
        - first_name (VARCHAR)
        - last_name (VARCHAR)
        - is_staff (BOOLEAN)
        - is_active (BOOLEAN)
        - is_superuser (BOOLEAN)
        - date_joined (DATETIME)
    """
    # Custom attributes from registration requirements
    email = models.EmailField(unique=True, max_length=254) # Overriding to ensure strict uniqueness
    mobile = models.CharField(max_length=15, blank=True, null=True)
    
    # Email Verification lifecycle tracking attributes
    is_email_verified = models.BooleanField(default=False)
    email_verification_token = models.CharField(max_length=100, blank=True, null=True)
    token_created_at = models.DateTimeField(blank=True, null=True)
    
    # Chronological timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users' # Forces the database to name the table exactly 'users'

    def __str__(self):
        return f"{self.username} ({self.email})"


class RBACPermissionProxy(models.Model):
    """
    TABLE 2 & 3: roles & permissions Configuration
    
    NOTE ON REPOSITORY NORMALIZATION:
    Django provides two native database tables out-of-the-box:
      - auth_group (Which acts exactly as your 'roles' table)
      - auth_permission (Which acts exactly as your 'permissions' table)
    
    Django also automatically manages the junction join tables:
      - user_roles (via the 'groups' ManyToMany attribute on your User model)
      - role_permissions (via the 'permissions' ManyToMany attribute on the Group model)
    
    This proxy model registers your custom system scopes into the core 
    permissions engine without adding clutter to your physical DB schemas.
    """
    class Meta:
        managed = False  # Tells Django not to create a separate physical layout table
        default_permissions = ()  # Disables default model CRUD hooks
        
        permissions = [
            # User Management & RBAC Module Scopes
            ("can_view_admin_dashboard", "Can view central security dashboard layout"),
            ("can_view_activity_dashboard", "Can view tracking activity summary visuals"),
            ("can_manage_roles", "Can create, update, or delete system groups (roles)"),
            ("can_assign_roles", "Can map user accounts to defined groups/roles"),
            ("can_modify_permissions", "Can alter granular privileges or override system tokens"),
            ("can_view_permission_matrix", "Can view global cross-reference matrix grid"),
            
            # Module Cross-Access Authorization Scopes (For testing across other teams)
            ("can_manage_students", "Can perform operations on student profiles (Team 2)"),
            ("can_manage_trainers", "Can perform operations on trainer profiles (Team 3)"),
            ("can_manage_courses", "Can update training programs and syllabus details (Team 4)"),
            ("can_manage_hostels", "Can allocate or modify room configurations (Team 5)"),
            ("can_manage_finance", "Can process invoices and update payment ledgers (Team 6)"),
        ]


class AuditLog(models.Model):
    """
    TABLE 4: audit_logs
    Tracks every structural database write, verification event, and authentication 
    state action chronologically for compliance tracking.
    """
    id = models.AutoField(primary_key=True) # Explicit unique log entry identifier
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='audit_logs'
    )
    action = models.CharField(max_length=255)  # e.g., "User Registered", "Role Updated", "Logged Out"
    module = models.CharField(max_length=50, default='usermgmt')  # Tracks source module workspace context
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    browser_agent = models.TextField(blank=True, null=True)  # Captures client browser properties for audit logs
    timestamp = models.DateTimeField(auto_now_add=True)  # Equivalent to created_at for chronological sorting

    class Meta:
        db_table = 'audit_logs' # Forces the database to name the table exactly 'audit_logs'
        ordering = ['-timestamp'] # Pulls latest transactional updates first by default

    def __str__(self):
        user_str = self.user.username if self.user else "Anonymous"
        return f"[{self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {user_str} - {self.action}"