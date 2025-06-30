# VMware Dashboard Queries

Based on the actual VMware data structure found in Sumo Logic:

## Data Sources Available:
- **vmware/metrics**: 84,783 messages with performance metrics
- **vmware/events**: 14,771 messages with vCenter events

## Sample Data Structure:

### Metrics Format:
```
metric=datastore_read type=host hostname=192.168.100.110 vcenter=192.168.100.120 15705 1751316400
```

### Events Format (contains cluster/datacenter info):
```
message=...,,,computeResource=TBC-Site01-Cluster01,,,datacenter=Datacenter,,,
```

## Dashboard Queries:

### Panel 1: VM Host Performance Overview
```sql
_sourceCategory="vmware/metrics" 
| parse "metric=* type=* hostname=* vcenter=* * *" as metric_name, type, hostname, vcenter, value, timestamp
| where type="host"
| timeslice 5m
| sum(value) as total_value by _timeslice, hostname, metric_name
| transpose row _timeslice column metric_name
```

### Panel 2: Host List with Basic Info
```sql
_sourceCategory="vmware/metrics" 
| parse "metric=* type=* hostname=* vcenter=* * *" as metric_name, type, hostname, vcenter, value, timestamp
| count by hostname, vcenter
| fields hostname, vcenter, _count
| sort by _count desc
```

### Panel 3: Cluster Information from Events
```sql
_sourceCategory="vmware/events"
| parse regex "computeResource=(?<cluster>[^,]+)"
| parse regex "datacenter=(?<datacenter>[^,]+)"
| count by cluster, datacenter
| where cluster != ""
```

### Panel 4: Available Metrics by Host
```sql
_sourceCategory="vmware/metrics" 
| parse "metric=* type=* hostname=* vcenter=* * *" as metric_name, type, hostname, vcenter, value, timestamp
| count by hostname, metric_name
| sort by hostname, metric_name
```

### Panel 5: Disk Performance Metrics
```sql
_sourceCategory="vmware/metrics" 
| parse "metric=* type=* hostname=* vcenter=* * *" as metric_name, type, hostname, vcenter, value, timestamp
| where metric_name matches "*disk*"
| timeslice 5m
| avg(value) as avg_value by _timeslice, hostname, metric_name
| transpose row _timeslice column metric_name
```

### Panel 6: Datastore Read/Write Activity
```sql
_sourceCategory="vmware/metrics" 
| parse "metric=* type=* hostname=* vcenter=* * *" as metric_name, type, hostname, vcenter, value, timestamp
| where metric_name matches "*datastore*"
| timeslice 5m
| sum(value) as total_ops by _timeslice, hostname, metric_name
| transpose row _timeslice column metric_name
```

### Panel 7: Recent VMware Events
```sql
_sourceCategory="vmware/events"
| parse regex "message=(?<event_message>[^,]+)"
| parse regex "computeResource=(?<cluster>[^,]+)"
| parse regex "datacenter=(?<datacenter>[^,]+)"
| fields _messagetime, event_message, cluster, datacenter
| sort by _messagetime desc
| limit 20
```

### Panel 8: Event Types Summary
```sql
_sourceCategory="vmware/events"
| parse regex "eventType=(?<event_type>[^,]+)"
| count by event_type
| sort by _count desc
```

## Notes:
- The actual VM configuration data (CPU count, memory size, disk details) is not visible in the current metrics
- Available metrics focus on performance (latency, read/write operations) rather than configuration
- Cluster and datacenter information is available in the events stream
- To get VM configuration details, you would need to enable additional vCenter receivers or use vCenter API directly

## Next Steps:
To get the VM configuration data you originally requested (CPU count, memory size, disk configuration), you would need:
1. Additional vCenter receiver configuration to collect inventory data
2. Direct vCenter API integration
3. Or VMware vRealize/vROps integration if available