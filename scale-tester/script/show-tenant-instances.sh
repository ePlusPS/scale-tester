
keystone tenant-list | grep tenant-test | while read line; do
    # echo "$line" 
    
    tenant_id=$(echo "$line" | awk '{print $2}')
    tenant_name=$(echo "$line" | awk '{print $4}')
    # echo "$tenant_id, $tenant_name"

    num_instances=$(nova list --all-tenants --tenant $tenant_id | grep net | wc -l)
    
    #if [$num_instances != "9"] 
    #then
    echo "$tenant_name , $num_instances"
    # fi
    

done
