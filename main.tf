
provider "google" {
  project = var.projectID
  region  = var.region
  zone   = var.zone
}

resource "google_project_service" "enable_google_apis" {
  count   = length(var.gcp_services_list)
  project = var.projectID
  service = var.gcp_services_list[count.index] 
  disable_on_destroy=false
  disable_dependent_services =false
}
resource "google_service_account" "sa" {
  project      = var.projectID
  account_id   = "${var.deploymentName}-sa"
  display_name = "Service Account"

  depends_on = [
    google_project_service.enable_google_apis
  ]
}

resource "google_project_iam_member" "sa_iam" {
  project = var.projectID
  role    = "roles/storage.admin"
  member  = "serviceAccount:${google_service_account.sa.email}"
  depends_on = [
    google_service_account.sa
  ]

}

data "archive_file" "source" {
    type        = "zip"
    source_dir  = "./scripts"
    output_path = "/tmp/index.zip"
}

resource "google_storage_bucket" "bucket" {
  name = format("%s-bucket", var.deploymentName)
  location = var.region
  
}

resource "google_storage_bucket_object" "zip" {
    source       = data.archive_file.source.output_path
    content_type = "application/zip"    
    name         = "index.zip"
    bucket       = google_storage_bucket.bucket.name    
    depends_on   = [
        google_storage_bucket.bucket,  
        data.archive_file.source
    ]
}
resource "google_cloudfunctions_function" "function" {
  name = format("%s-LicenseValidation", var.deploymentName) 
  description = "Boomi License Validation"
  runtime     = "python37"
  service_account_email = google_service_account.sa.email
  available_memory_mb   = 256
  timeout               = 60
  source_archive_bucket = google_storage_bucket.bucket.name
  source_archive_object = google_storage_bucket_object.zip.name
  trigger_http          = true
  entry_point           = "handler"    
}

locals {
  set_sensitive = sensitive(true)
}

resource "null_resource" "callfunction" {
provisioner "local-exec" {
   command=<<EOF
   curl -m 70 -X POST "https://${var.region}-${var.projectID}.cloudfunctions.net/${var.deploymentName}-LicenseValidation" -H "Authorization:bearer $(gcloud auth print-identity-token)" -H "Content-Type:application/json" -d '{"BoomiUsername":"${var.boomiUserEmailID}","boomiAuthenticationType":"${var.boomiAuthenticationType}","BoomiPassword":"${var.boomiPasswordORboomiAPIToken}","BoomiAccountID":"${var.boomiAccountID}","TokenType":"atom","TokenTimeout":"60","bucketname": "${var.deploymentName}-bucket","set_sensitive":"${local.set_sensitive}"}'
EOF
}
depends_on = [
    google_cloudfunctions_function.function
  ]
}

resource "google_compute_network" "vpc_network" {
  name = format("%s-vpc-network", var.deploymentName)
  auto_create_subnetworks = false
  depends_on = [
    google_cloudfunctions_function.function
  ]
}

resource "google_compute_subnetwork" "public-subnetwork" {
 name = format("%s-public-subnetwork", var.deploymentName)
 ip_cidr_range = "192.168.0.0/21"
 private_ip_google_access= true
 region = var.region
 network = google_compute_network.vpc_network.name
 depends_on = [
    google_compute_network.vpc_network
  ]
}

resource "google_compute_subnetwork" "private-subnetwork" {
 name = format("%s-private-subnetwork", var.deploymentName)
 ip_cidr_range = "192.168.8.0/21"
 region = var.region
 network = google_compute_network.vpc_network.name
 depends_on = [
    google_compute_network.vpc_network
  ]
}

resource "google_compute_router" "router" {
  name = format("%s-router", var.deploymentName)
  region  = var.region
  network = google_compute_network.vpc_network.name
   depends_on = [
    google_compute_subnetwork.private-subnetwork
  ]
}

resource "google_compute_router_nat" "nat_manual" {
  name = format("%s-nat", var.deploymentName)
  router = google_compute_router.router.name
  region = var.region
  nat_ip_allocate_option = "AUTO_ONLY"
  source_subnetwork_ip_ranges_to_nat = "LIST_OF_SUBNETWORKS"
  subnetwork {
    name                    = google_compute_subnetwork.private-subnetwork.id
    source_ip_ranges_to_nat = ["ALL_IP_RANGES"]
  }
  log_config {
    enable = true
    filter = "ERRORS_ONLY"
  }
  depends_on = [
    google_compute_router.router
  ]
}

data "template_file" "default" {
  template = file("${path.module}/bash-script.sh")
  vars = {
    boomiAuthenticationType= "${var.boomiAuthenticationType}"
    boomiUserEmailID="${var.boomiUserEmailID}"
    boomiPasswordORboomiAPIToken = "${var.boomiPasswordORboomiAPIToken}"
    boomiAccountID="${var.boomiAccountID}"
    atomName= "${var.atomName}"  
    deploymentName="${var.deploymentName}" 

  }
  depends_on = [
    google_compute_subnetwork.private-subnetwork
  ]
}

resource "google_compute_firewall" "firewall1" {
  name = format("%s-firewall1", var.deploymentName)
  network = google_compute_network.vpc_network.name
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["0.0.0.0/0"] 
  target_tags   = ["externalssh"]
  depends_on = [
    google_compute_subnetwork.public-subnetwork
  ] 

}
resource "google_compute_firewall" "firewall2" {
  name = format("%s-firewall2", var.deploymentName)
  network = google_compute_network.vpc_network.name
  allow {
    protocol = "tcp"
    ports    = ["22"]
  }
  source_ranges = ["192.168.0.0/21"] 
  target_tags   = ["internalssh"]
  depends_on = [
    google_compute_subnetwork.private-subnetwork
  ]
}

resource "google_compute_instance" "vm1" {
  name = format("%s-bastion-host", var.deploymentName)
  machine_type = var.machineType
  tags = ["externalssh"]
  boot_disk {
    initialize_params {
      image = "centos-cloud/centos-7"
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.name
    subnetwork = google_compute_subnetwork.public-subnetwork.name

    access_config {    
    }
  }
  depends_on = [
    google_compute_subnetwork.public-subnetwork
  ]
}

resource "google_compute_instance" "vm2" {
  name = format("%s-boomi-instance", var.deploymentName)
  machine_type = var.machineType
   tags = ["internalssh"] 

  boot_disk {
    initialize_params {
      image = "centos-cloud/centos-7"
    }
  }

  network_interface {
    network = google_compute_network.vpc_network.name
    subnetwork = google_compute_subnetwork.private-subnetwork.name
  }
  metadata_startup_script = data.template_file.default.rendered
  service_account {
    email  = google_service_account.sa.email
    scopes = ["cloud-platform"]
  }
  depends_on = [
    google_compute_subnetwork.private-subnetwork
  ]
}



