def split_tips_by_department(total_tips, staff_members):
    kitchen_pool = total_tips/2
    service_pool = total_tips/2
    
    kitchen_hours = 0
    service_hours = 0 
    
    for member in staff_members:
        if member.department == "Kitchen":
            kitchen_hours += member.hours
        else:
            service_hours += member.hours
        
        
    kitchen_rate = kitchen_pool / kitchen_hours
    service_rate = service_pool / service_hours
    
    for mem