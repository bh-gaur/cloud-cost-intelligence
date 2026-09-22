variable "aws_region" {
  type        = string
  default     = "us-east-1"
  description = "AWS region for infrastructure deployment"
}

variable "environment" {
  type        = string
  default     = "production"
  description = "Environment name (production, staging, dev)"
}

variable "instance_type" {
  type        = string
  default     = "t3.medium"
  description = "EC2 instance size"
}

variable "key_name" {
  type        = string
  description = "AWS SSH key pair name"
}

variable "ami_id" {
  type        = string
  default     = ""
  description = "Optional custom Ubuntu AMI ID"
}

variable "disk_size_gb" {
  type        = number
  default     = 30
  description = "Root disk size in GB"
}

variable "allowed_ssh_cidrs" {
  type        = list(string)
  default     = ["0.0.0.0/0"]
  description = "CIDR blocks allowed for SSH access"
}
