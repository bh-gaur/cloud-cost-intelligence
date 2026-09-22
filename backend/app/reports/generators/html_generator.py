"""
HTML Report Generator
Produces executive-ready, print-friendly FinOps report with modern styling.
"""

from typing import Any, Dict
from jinja2 import Template


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AWS Cost Intelligence Executive Report</title>
  <style>
    @media print {
      body { font-size: 12px; background: #fff !important; }
      .no-print { display: none; }
      .page-break { page-break-after: always; }
      .card { border: 1px solid #ddd !important; box-shadow: none !important; }
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      color: #1e293b;
      background-color: #f8fafc;
      padding: 32px;
      line-height: 1.5;
    }
    .header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      border-bottom: 2px solid #e2e8f0;
      padding-bottom: 20px;
      margin-bottom: 28px;
    }
    .brand { font-size: 24px; font-weight: 700; color: #0f172a; }
    .brand span { color: #2563eb; }
    .meta-info { font-size: 13px; color: #64748b; text-align: right; }
    
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-bottom: 28px;
    }
    .kpi-card {
      background: #ffffff;
      padding: 20px;
      border-radius: 8px;
      border: 1px solid #e2e8f0;
      box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .kpi-title { font-size: 12px; font-weight: 600; text-transform: uppercase; color: #64748b; letter-spacing: 0.5px; }
    .kpi-value { font-size: 24px; font-weight: 700; color: #0f172a; margin-top: 4px; }
    .kpi-badge {
      display: inline-block;
      margin-top: 8px;
      font-size: 12px;
      font-weight: 600;
      padding: 2px 8px;
      border-radius: 4px;
    }
    .badge-up { background: #fee2e2; color: #dc2626; }
    .badge-down { background: #dcfce7; color: #16a34a; }
    .badge-savings { background: #e0e7ff; color: #4338ca; }
    
    .section-title {
      font-size: 18px;
      font-weight: 700;
      color: #0f172a;
      margin: 28px 0 14px 0;
      display: flex;
      align-items: center;
      gap: 8px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      background: #ffffff;
      border-radius: 8px;
      overflow: hidden;
      border: 1px solid #e2e8f0;
      margin-bottom: 28px;
      font-size: 13px;
    }
    th {
      background: #f1f5f9;
      text-align: left;
      padding: 12px 16px;
      font-weight: 600;
      color: #475569;
      border-bottom: 1px solid #e2e8f0;
    }
    td {
      padding: 12px 16px;
      border-bottom: 1px solid #f1f5f9;
      color: #1e293b;
    }
    tr:last-child td { border-bottom: none; }
    tr:hover { background: #f8fafc; }
    
    .priority-pill {
      font-size: 11px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      text-transform: uppercase;
    }
    .p-high { background: #fee2e2; color: #b91c1c; }
    .p-med { background: #fef3c7; color: #b45309; }
    .p-low { background: #f1f5f9; color: #475569; }

    .footer {
      border-top: 1px solid #e2e8f0;
      padding-top: 16px;
      font-size: 12px;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
    }
  </style>
</head>
<body>

  <div class="header">
    <div>
      <div class="brand">AWS <span>Cost Intelligence</span></div>
      <p style="font-size: 14px; color: #64748b; margin-top: 4px;">Executive Cloud Spend & FinOps Optimization Report</p>
    </div>
    <div class="meta-info">
      <p><strong>Period:</strong> {{ start_date }} to {{ end_date }}</p>
      <p><strong>Scope:</strong> {{ account_id }}</p>
      <p><strong>Generated:</strong> {{ generated_at }}</p>
    </div>
  </div>

  <div class="kpi-grid">
    <div class="kpi-card">
      <div class="kpi-title">Total Spend</div>
      <div class="kpi-value">${{ "{:,.2f}".format(total_cost) }}</div>
      <div class="kpi-badge {{ 'badge-up' if percentage_change > 0 else 'badge-down' }}">
        {{ "+" if percentage_change > 0 else "" }}{{ "{:.2f}".format(percentage_change) }}% vs prev
      </div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Previous Period Spend</div>
      <div class="kpi-value">${{ "{:,.2f}".format(previous_cost) }}</div>
      <div style="font-size: 12px; color: #64748b; margin-top: 8px;">Baseline comparison</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Potential Monthly Savings</div>
      <div class="kpi-value" style="color: #16a34a;">${{ "{:,.2f}".format(potential_monthly_savings) }}</div>
      <div class="kpi-badge badge-savings">11 FinOps Rules Analyzed</div>
    </div>
    <div class="kpi-card">
      <div class="kpi-title">Active Anomalies</div>
      <div class="kpi-value" style="color: {{ '#dc2626' if anomalies|length > 0 else '#16a34a' }};">
        {{ anomalies|length }}
      </div>
      <div style="font-size: 12px; color: #64748b; margin-top: 8px;">Spikes detected</div>
    </div>
  </div>

  <div class="section-title">Top AWS Services by Spend</div>
  <table>
    <thead>
      <tr>
        <th>Service Name</th>
        <th>Category</th>
        <th>Period Cost (USD)</th>
        <th>% of Total</th>
        <th>Trend</th>
      </tr>
    </thead>
    <tbody>
      {% for svc in services %}
      <tr>
        <td><strong>{{ svc.service }}</strong></td>
        <td>{{ svc.category }}</td>
        <td>${{ "{:,.2f}".format(svc.current_cost) }}</td>
        <td>{{ "{:.2f}".format(svc.percentage_of_total) }}%</td>
        <td>{{ svc.trend.upper() }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="section-title">Account & Multi-Account Breakdown</div>
  <table>
    <thead>
      <tr>
        <th>Account Name</th>
        <th>Account ID</th>
        <th>Cost (USD)</th>
        <th>% of Total</th>
      </tr>
    </thead>
    <tbody>
      {% for acc in accounts %}
      <tr>
        <td><strong>{{ acc.account_name }}</strong></td>
        <td><code>{{ acc.account_id }}</code></td>
        <td>${{ "{:,.2f}".format(acc.monthly_cost) }}</td>
        <td>{{ "{:.2f}".format(acc.percentage_of_total) }}%</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="section-title">FinOps Optimization & Potential Savings</div>
  <table>
    <thead>
      <tr>
        <th>Rule</th>
        <th>Resource ID</th>
        <th>Service</th>
        <th>Est. Monthly Savings</th>
        <th>Priority</th>
        <th>Confidence</th>
        <th>Action Required</th>
      </tr>
    </thead>
    <tbody>
      {% for rec in recommendations %}
      <tr>
        <td><strong>{{ rec.rule_name }}</strong></td>
        <td><code>{{ rec.resource_id }}</code></td>
        <td>{{ rec.service }}</td>
        <td style="color: #16a34a; font-weight: 600;">${{ "{:,.2f}".format(rec.estimated_monthly_savings) }}</td>
        <td>
          <span class="priority-pill {{ 'p-high' if rec.priority == 'HIGH' else ('p-med' if rec.priority == 'MEDIUM' else 'p-low') }}">
            {{ rec.priority }}
          </span>
        </td>
        <td>{{ rec.confidence }}</td>
        <td>{{ rec.action_required }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="footer">
    <span>Generated autonomously by AWS Cost Intelligence Platform (cloud-cost-intelligence)</span>
    <span>Confidential - For Internal FinOps Use Only</span>
  </div>

</body>
</html>
"""


class HTMLReportGenerator:
    def generate(self, data: Dict[str, Any]) -> str:
        """Renders the executive HTML template with supplied report model data."""
        template = Template(HTML_TEMPLATE)
        return template.render(**data)

