
# keystone tenant-list | grep tenant-test | while read line; do
nova list --all-tenants | grep net_ | while read line; do
    # echo "$line" 
    
    vm_id=$(echo "$line" | awk '{print $2}')
    vm_name=$(echo "$line" | awk '{print $4}')
    # echo "$tenant_id, $tenant_name"

    # num_instances=$(nova list --all-tenants --tenant $tenant_id | grep net | wc -l)
    
    #if [$num_instances != "9"] 
    #then
    echo "killing $vm_id , $vm_name"
    nova delete $vm_id
    # fi
    

done
