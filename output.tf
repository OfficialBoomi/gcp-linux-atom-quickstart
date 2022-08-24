
output "Bastion_Host" {

  value=google_compute_instance.vm1.name

}

output "Boomi_instance" {

  value=google_compute_instance.vm2.name

}

output "External_IP_of_Bastion_host" {  
    
  value = "${google_compute_instance.vm1[*].network_interface.0.access_config.0.nat_ip}"  
}


output "NOTE"{  

 
 value =  "Each deployment takes about 5 minutes to complete. It may take another 2 minutes for atom to show up on the platform after the deployment is completed"
 
}


