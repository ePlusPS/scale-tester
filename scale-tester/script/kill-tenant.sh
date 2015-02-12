# A simple script for whacking a block of tenants and users
for i in `seq 0 999`;
do
    TENANT="tenant-test-$i"
    USER="tenant-test-$i-0"

    echo keystone tenant-delete $TENANT
    keystone tenant-delete $TENANT

    echo keystone user-delete $USER
    keystone user-delete $USER
done
