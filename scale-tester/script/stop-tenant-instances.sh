
keystone tenant-list | grep data-tenant | while read line; do
    # echo "$line" 
    
    tenant_id=$(echo "$line" | awk '{print $2}')
    tenant_name=$(echo "$line" | awk '{print $4}')
    # echo "$tenant_id, $tenant_name"

    nova list --all-tenants --tenant $tenant_id | grep data-tenant | while read line2; do 
    
        vm_id=$(echo "$line2" | awk '{print $2}')
        vm_name=$(echo "$line2" | awk '{print $4}')
        echo "stopping $vm_id, $vm_name"
        nova stop $vm_id
    done
done
