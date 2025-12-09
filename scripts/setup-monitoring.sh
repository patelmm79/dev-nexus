#!/bin/bash
# Setup Cloud Monitoring Alerts for dev-nexus

set -e

# Configuration
PROJECT_ID="${GCP_PROJECT_ID:-}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="pattern-discovery-agent"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation
if [ -z "$PROJECT_ID" ]; then
    echo -e "${RED}Error: GCP_PROJECT_ID environment variable not set${NC}"
    echo "Usage: export GCP_PROJECT_ID=your-project-id"
    exit 1
fi

echo "================================================"
echo "Setting up Cloud Monitoring for dev-nexus"
echo "================================================"
echo "Project:  $PROJECT_ID"
echo "Region:   $REGION"
echo "Service:  $SERVICE_NAME"
echo

# Step 1: Create notification channels
echo -e "${YELLOW}Step 1: Creating notification channels...${NC}"
echo "Please provide notification channel details (or press Enter to skip):"

read -p "Email for alerts (optional): " ALERT_EMAIL

if [ -n "$ALERT_EMAIL" ]; then
    echo "Creating email notification channel..."
    CHANNEL_ID=$(gcloud alpha monitoring channels create \
        --display-name="Dev-Nexus Alerts" \
        --type=email \
        --channel-labels=email_address="$ALERT_EMAIL" \
        --project="$PROJECT_ID" \
        --format="value(name)" 2>/dev/null || echo "")

    if [ -n "$CHANNEL_ID" ]; then
        echo -e "${GREEN}✓ Email notification channel created: $CHANNEL_ID${NC}"
    else
        echo -e "${YELLOW}⚠ Email channel already exists or failed to create${NC}"
        CHANNEL_ID=$(gcloud alpha monitoring channels list \
            --filter="displayName='Dev-Nexus Alerts'" \
            --project="$PROJECT_ID" \
            --format="value(name)" | head -1)
    fi
else
    echo -e "${YELLOW}Skipping notification channel creation${NC}"
    CHANNEL_ID=""
fi

# Step 2: Create alert policies
echo
echo -e "${YELLOW}Step 2: Creating alert policies...${NC}"

# Alert 1: High Error Rate
echo "Creating high error rate alert..."
cat > /tmp/alert-high-error-rate.json <<EOF
{
  "displayName": "Dev-Nexus High Error Rate",
  "documentation": {
    "content": "Error rate exceeded 5% for 5 minutes.\nCheck logs: gcloud logging read \"resource.type=cloud_run_revision AND severity>=ERROR\" --limit=50",
    "mimeType": "text/markdown"
  },
  "conditions": [{
    "displayName": "Error rate > 5%",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\"",
      "comparison": "COMPARISON_GT",
      "thresholdValue": 0.05,
      "duration": "300s",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_RATE"
      }]
    }
  }],
  "combiner": "OR",
  "enabled": true
}
EOF

if [ -n "$CHANNEL_ID" ]; then
    gcloud alpha monitoring policies create \
        --notification-channels="$CHANNEL_ID" \
        --policy-from-file=/tmp/alert-high-error-rate.json \
        --project="$PROJECT_ID" 2>/dev/null && \
        echo -e "${GREEN}✓ High error rate alert created${NC}" || \
        echo -e "${YELLOW}⚠ High error rate alert already exists or failed${NC}"
else
    gcloud alpha monitoring policies create \
        --policy-from-file=/tmp/alert-high-error-rate.json \
        --project="$PROJECT_ID" 2>/dev/null && \
        echo -e "${GREEN}✓ High error rate alert created (no notifications)${NC}" || \
        echo -e "${YELLOW}⚠ High error rate alert already exists or failed${NC}"
fi

# Alert 2: High Latency
echo "Creating high latency alert..."
cat > /tmp/alert-high-latency.json <<EOF
{
  "displayName": "Dev-Nexus High Latency",
  "documentation": {
    "content": "P95 latency exceeded 5 seconds for 5 minutes.\nConsider scaling up resources or investigating slow operations.",
    "mimeType": "text/markdown"
  },
  "conditions": [{
    "displayName": "P95 latency > 5000ms",
    "conditionThreshold": {
      "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
      "comparison": "COMPARISON_GT",
      "thresholdValue": 5000,
      "duration": "300s",
      "aggregations": [{
        "alignmentPeriod": "60s",
        "perSeriesAligner": "ALIGN_DELTA",
        "crossSeriesReducer": "REDUCE_PERCENTILE_95"
      }]
    }
  }],
  "combiner": "OR",
  "enabled": true
}
EOF

if [ -n "$CHANNEL_ID" ]; then
    gcloud alpha monitoring policies create \
        --notification-channels="$CHANNEL_ID" \
        --policy-from-file=/tmp/alert-high-latency.json \
        --project="$PROJECT_ID" 2>/dev/null && \
        echo -e "${GREEN}✓ High latency alert created${NC}" || \
        echo -e "${YELLOW}⚠ High latency alert already exists or failed${NC}"
else
    gcloud alpha monitoring policies create \
        --policy-from-file=/tmp/alert-high-latency.json \
        --project="$PROJECT_ID" 2>/dev/null && \
        echo -e "${GREEN}✓ High latency alert created (no notifications)${NC}" || \
        echo -e "${YELLOW}⚠ High latency alert already exists or failed${NC}"
fi

# Step 3: Create uptime check
echo
echo -e "${YELLOW}Step 3: Creating uptime check...${NC}"

SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --project=$PROJECT_ID \
    --format="value(status.url)" 2>/dev/null || echo "")

if [ -n "$SERVICE_URL" ]; then
    # Extract host from URL
    HOST=$(echo $SERVICE_URL | sed 's|https://||' | sed 's|/.*||')

    cat > /tmp/uptime-check.json <<EOF
{
  "displayName": "Dev-Nexus Health Check",
  "monitoredResource": {
    "type": "uptime_url",
    "labels": {
      "project_id": "${PROJECT_ID}",
      "host": "${HOST}"
    }
  },
  "httpCheck": {
    "path": "/health",
    "port": 443,
    "useSsl": true,
    "validateSsl": true
  },
  "period": "60s",
  "timeout": "10s"
}
EOF

    gcloud monitoring uptime create \
        --config-from-file=/tmp/uptime-check.json \
        --project="$PROJECT_ID" 2>/dev/null && \
        echo -e "${GREEN}✓ Uptime check created${NC}" || \
        echo -e "${YELLOW}⚠ Uptime check already exists or failed${NC}"
else
    echo -e "${YELLOW}⚠ Service not deployed yet, skipping uptime check${NC}"
fi

# Step 4: Create custom dashboard
echo
echo -e "${YELLOW}Step 4: Creating monitoring dashboard...${NC}"

cat > /tmp/dashboard.json <<EOF
{
  "displayName": "Dev-Nexus Overview",
  "mosaicLayout": {
    "columns": 12,
    "tiles": [
      {
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Request Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Latency (P50, P95, P99)",
          "xyChart": {
            "dataSets": [
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_50"
                    }
                  }
                },
                "plotType": "LINE"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_95"
                    }
                  }
                },
                "plotType": "LINE"
              },
              {
                "timeSeriesQuery": {
                  "timeSeriesFilter": {
                    "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_latencies\"",
                    "aggregation": {
                      "alignmentPeriod": "60s",
                      "perSeriesAligner": "ALIGN_DELTA",
                      "crossSeriesReducer": "REDUCE_PERCENTILE_99"
                    }
                  }
                },
                "plotType": "LINE"
              }
            ]
          }
        }
      },
      {
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Instance Count",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/container/instance_count\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_MEAN"
                  }
                }
              }
            }]
          }
        }
      },
      {
        "xPos": 6,
        "yPos": 4,
        "width": 6,
        "height": 4,
        "widget": {
          "title": "Error Rate",
          "xyChart": {
            "dataSets": [{
              "timeSeriesQuery": {
                "timeSeriesFilter": {
                  "filter": "resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"${SERVICE_NAME}\" AND metric.type=\"run.googleapis.com/request_count\" AND metric.labels.response_code_class=\"5xx\"",
                  "aggregation": {
                    "alignmentPeriod": "60s",
                    "perSeriesAligner": "ALIGN_RATE"
                  }
                }
              }
            }]
          }
        }
      }
    ]
  }
}
EOF

gcloud monitoring dashboards create \
    --config-from-file=/tmp/dashboard.json \
    --project="$PROJECT_ID" 2>/dev/null && \
    echo -e "${GREEN}✓ Monitoring dashboard created${NC}" || \
    echo -e "${YELLOW}⚠ Dashboard already exists or failed${NC}"

# Cleanup temp files
rm -f /tmp/alert-*.json /tmp/uptime-check.json /tmp/dashboard.json

echo
echo "================================================"
echo -e "${GREEN}Monitoring setup complete!${NC}"
echo "================================================"
echo

if [ -n "$CHANNEL_ID" ]; then
    echo "Notification channel: $CHANNEL_ID"
fi

if [ -n "$SERVICE_URL" ]; then
    echo "Service URL: $SERVICE_URL"
fi

echo
echo "View monitoring in Cloud Console:"
echo "- Dashboards: https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
echo "- Alerts: https://console.cloud.google.com/monitoring/alerting?project=$PROJECT_ID"
echo "- Uptime checks: https://console.cloud.google.com/monitoring/uptime?project=$PROJECT_ID"
echo

echo "Next steps:"
echo "1. Review and customize alert policies as needed"
echo "2. Add more notification channels (Slack, PagerDuty, etc.)"
echo "3. Test alerts by triggering conditions"
echo "4. Create additional dashboards for specific metrics"
echo
