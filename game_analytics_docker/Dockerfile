# Dockerfile
FROM mysql:8.0

# Add configuration properly with the [mysqld] group
RUN echo "[mysqld]" >> /etc/mysql/my.cnf && \
    echo "default_authentication_plugin=mysql_native_password" >> /etc/mysql/my.cnf && \
    echo "character-set-server=utf8mb4" >> /etc/mysql/my.cnf && \
    echo "collation-server=utf8mb4_unicode_ci" >> /etc/mysql/my.cnf

COPY platform_analytics_dump.sql /docker-entrypoint-initdb.d/