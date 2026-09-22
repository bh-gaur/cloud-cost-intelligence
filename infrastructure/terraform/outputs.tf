output "instance_id" {
  value       = aws_instance.finops_server.id
  description = "EC2 Instance ID"
}

output "public_ip" {
  value       = aws_eip.finops_eip.public_ip
  description = "Public Elastic IP address"
}

output "ssh_command" {
  value       = "ssh -i ~/.ssh/${var.key_name}.pem ubuntu@${aws_eip.finops_eip.public_ip}"
  description = "Command to SSH into server"
}

output "application_url" {
  value       = "http://${aws_eip.finops_eip.public_ip}"
  description = "Application URL"
}
