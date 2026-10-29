# Infrastructure as Code (IaC) - Terraform Cloud Architecture
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Dedicated Secure Secret Management via Secret Manager
resource "google_secret_manager_secret" "gemini_api_key" {
  secret_id = "gemini-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "gemini_api_key_version" {
  secret      = google_secret_manager_secret.gemini_api_key.id
  secret_data = var.gemini_api_key_secret_data
}

# Cloud Run Containerized Microservice Deployment
resource "google_cloud_run_v2_service" "meal_agent_service" {
  name     = "family-meal-concierge-agent"
  location = var.region

  template {
    containers {
      image = "gcr.io/${var.project_id}/family-meal-planner-agent:latest"
      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
      }
      env {
        name = "GEMINI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.gemini_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
  }
}

output "service_url" {
  value       = google_cloud_run_v2_service.meal_agent_service.uri
  description = "Public URL of deployed Meal Concierge Agent"
}
