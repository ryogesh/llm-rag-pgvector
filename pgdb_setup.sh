# Refer: https://www.postgresql.org/download/linux/ubuntu/
sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt $(lsb_release -cs 2>/dev/null)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

# Import the repository signing key:
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

# Update the package lists:
apt-get update

# Install the latest version of PostgreSQL.
# If you want a specific version, use 'postgresql-12' or similar instead of 'postgresql':
apt-get -y install postgresql-server-14 postgresql-server-dev-14

echo "host    all             all             192.168.0.0/16          scram-sha-256" > /etc/postgresql/14/main/pg_hba.conf


sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/14/main/postgresql.conf
sed -i "s/shared_buffers = 128MB/shared_buffers = 256MB/" /etc/postgresql/14/main/postgresql.conf
sed -i "s/#maintenance_work_mem = 64MB/maintenance_work_mem = 512MB/" /etc/postgresql/14/main/postgresql.conf
sed -i "s/#jit = on/jit = off/" /etc/postgresql/14/main/postgresql.conf

systemctl restart postgresql
