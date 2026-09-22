/**
 * Centralized Deterministic AWS Service Colors
 * Stable across all renders, charts, legends, and tables.
 */

export const AWS_SERVICE_COLORS: Record<string, string> = {
  // Compute
  'Amazon Elastic Compute Cloud - Compute': '#FF9900', // AWS Orange
  'EC2 - Compute': '#FF9900',
  'AWS Lambda': '#ED7100',
  'Amazon Elastic Kubernetes Service': '#326CE5', // Kubernetes Blue
  'Amazon Elastic Container Service': '#FF4F8B',

  // Storage
  'Amazon Simple Storage Service': '#569A31', // S3 Green
  'Amazon Elastic Block Store': '#7AA116',
  'Amazon Elastic File System': '#2E73B8',

  // Database
  'Amazon Relational Database Service': '#3B48CC', // RDS Blue
  'Amazon DynamoDB': '#4D27AA', // DynamoDB Indigo
  'Amazon Aurora': '#2E5B88',
  'Amazon ElastiCache': '#C925D1',

  // Networking
  'Amazon Virtual Private Cloud': '#8C4FFF',
  'Elastic Load Balancing': '#E7157B',
  'AWS Data Transfer': '#00A4A6',
  'Amazon Route 53': '#734A12',
  'NAT Gateway': '#0097A7',

  // Monitoring & Security
  'Amazon CloudWatch': '#E05243',
  'AWS CloudTrail': '#B83280',
  'AWS Key Management Service': '#CC2264',
  'AWS WAF': '#D13212',

  // Analytics
  'Amazon OpenSearch Service': '#0052CC',
  'Amazon Athena': '#D86600',
  'Amazon Redshift': '#AA223F',

  // Fallback / Other
  'Other': '#64748B',
};

// Fallback palette for dynamically discovered services
const PALETTE_FALLBACK = [
  '#0284c7', '#0d9488', '#16a34a', '#ca8a04',
  '#ea580c', '#e11d48', '#9333ea', '#4f46e5',
  '#2563eb', '#059669', '#d97706', '#dc2626',
];

/**
 * Returns a stable, deterministic hex color string for any AWS service.
 */
export function getServiceColor(serviceName: string): string {
  if (AWS_SERVICE_COLORS[serviceName]) {
    return AWS_SERVICE_COLORS[serviceName];
  }

  // Check substring matches
  const lower = serviceName.toLowerCase();
  if (lower.includes('ec2') || lower.includes('compute')) return AWS_SERVICE_COLORS['EC2 - Compute'];
  if (lower.includes('s3') || lower.includes('storage')) return AWS_SERVICE_COLORS['Amazon Simple Storage Service'];
  if (lower.includes('rds') || lower.includes('relational database')) return AWS_SERVICE_COLORS['Amazon Relational Database Service'];
  if (lower.includes('dynamodb')) return AWS_SERVICE_COLORS['Amazon DynamoDB'];
  if (lower.includes('lambda')) return AWS_SERVICE_COLORS['AWS Lambda'];
  if (lower.includes('cloudwatch')) return AWS_SERVICE_COLORS['Amazon CloudWatch'];
  if (lower.includes('data transfer')) return AWS_SERVICE_COLORS['AWS Data Transfer'];
  if (lower.includes('nat gateway') || lower.includes('vpc')) return AWS_SERVICE_COLORS['Amazon Virtual Private Cloud'];
  if (lower.includes('eks') || lower.includes('kubernetes')) return AWS_SERVICE_COLORS['Amazon Elastic Kubernetes Service'];
  if (lower.includes('opensearch') || lower.includes('elasticsearch')) return AWS_SERVICE_COLORS['Amazon OpenSearch Service'];

  // Deterministic DJB2 hash of the string to pick a stable color from fallback palette
  let hash = 5381;
  for (let i = 0; i < serviceName.length; i++) {
    hash = ((hash << 5) + hash) + serviceName.charCodeAt(i);
  }
  const index = Math.abs(hash) % PALETTE_FALLBACK.length;
  return PALETTE_FALLBACK[index];
}

