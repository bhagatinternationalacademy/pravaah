from django.db import connection
sql_commands = [
"CREATE TABLE IF NOT EXISTS `users` (\n  `id` bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  `password` varchar(128) NOT NULL,\n  `last_login` datetime NULL,\n  `is_superuser` tinyint(1) NOT NULL DEFAULT 0,\n  `username` varchar(150) NOT NULL UNIQUE,\n  `first_name` varchar(150) NOT NULL,\n  `last_name` varchar(150) NOT NULL,\n  `email` varchar(254) NOT NULL,\n  `is_staff` tinyint(1) NOT NULL DEFAULT 0,\n  `is_active` tinyint(1) NOT NULL DEFAULT 1,\n  `date_joined` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP\n) ENGINE=InnoDB;",
"CREATE TABLE IF NOT EXISTS `roles` (\n  `role_id` bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  `role_name` varchar(50) NOT NULL UNIQUE,\n  `description` text,\n  `status` varchar(20) NOT NULL DEFAULT 'Active'\n) ENGINE=InnoDB;",
"CREATE TABLE IF NOT EXISTS `user_roles` (\n  `user_role_id` bigint NOT NULL AUTO_INCREMENT PRIMARY KEY,\n  `user_id` bigint NOT NULL,\n  `role_id` bigint NOT NULL,\n  UNIQUE KEY `uniq_user_role` (`user_id`,`role_id`),\n  CONSTRAINT `fk_user_roles_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,\n  CONSTRAINT `fk_user_roles_role` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`) ON DELETE CASCADE\n) ENGINE=InnoDB;"
]
cur = connection.cursor()
for s in sql_commands:
    print('Executing:', s.split('\n')[0])
    cur.execute(s)
print('OK')
# mark migration as applied
from django.db.migrations.recorder import MigrationRecorder
MigrationRecorder.Migration.objects.get_or_create(app='accounts', name='0001_initial')
print('migration recorded')
