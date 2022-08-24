variable ProjectID{
    type= string      
 }

variable region{
    type= string
    default ="us-central1"    
 }

variable zone{
    type= string 
    default ="us-central1-a"   
 }

variable DeploymentName{
    type= string  
   
 }
  
variable boomiAuthenticationType{ 
    type= string
    default="Token or Password"
 }

variable boomiUserEmailID{
    type= string
 }

variable boomiPasswordORboomiAPIToken{
    type = string
    sensitive = true
 } 

variable boomiAccountID{
    type= string
 }    

variable AtomName{
    type= string    
 }

variable machineType{
    type= string  
    default= "e2-standard-4"  
 }

variable gcp_services_list {
  description = "The list of GCP APIs necessary for the project."
  type        = list(string)
  default     = ["cloudfunctions.googleapis.com",
"compute.googleapis.com",
"storage.googleapis.com"]
 }


