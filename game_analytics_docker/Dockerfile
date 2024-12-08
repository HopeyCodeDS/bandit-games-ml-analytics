# Dockerfile
FROM mysql:8.0

# Add configuration properly with the [mysqld] group
RUN echo "[mysqld]" >> /etc/mysql/my.cnf && \
    echo "default_authentication_plugin=mysql_native_password" >> /etc/mysql/my.cnf