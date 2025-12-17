/**
 * Recent Activity Component - Unified activity feed
 * Place in: dev-nexus-frontend/src/components/activity/RecentActivity.tsx
 */

import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  Button,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Stack,
  Divider,
  Tooltip,
  IconButton,
  SelectChangeEvent,
} from '@mui/material';
import {
  Timeline as TimelineIcon,
  BugReport as BugIcon,
  School as LessonIcon,
  Rocket as DeploymentIcon,
  Analytics as AnalysisIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
} from '@mui/icons-material';
import { useRecentActions } from '../../hooks/useAgents';
import { formatDistanceToNow } from 'date-fns';

interface RecentActivityProps {
  repository?: string;  // Optional repository filter
  defaultLimit?: number;
}

interface Action {
  action_type: 'analysis' | 'lesson' | 'deployment' | 'runtime_issue';
  repository: string;
  timestamp: string;
  reference_id: string;
  metadata: Record<string, any>;
}

interface PaginationInfo {
  limit: number;
  offset: number;
  has_more: boolean;
  next_offset: number | null;
  total_pages: number;
}

interface RecentActionsResponse {
  success: boolean;
  count?: number;
  returned?: number;
  actions?: Action[];
  pagination?: PaginationInfo;
  error?: string;
}

export default function RecentActivity({
  repository,
  defaultLimit = 20
}: RecentActivityProps) {
  const [limit] = useState(defaultLimit);
  const [offset, setOffset] = useState(0);
  const [actionTypeFilter, setActionTypeFilter] = useState<string[]>([]);

  const {
    data,
    isLoading,
    error,
    refetch
  } = useRecentActions(limit, offset, actionTypeFilter, repository);

  const typedData = data as RecentActionsResponse | undefined;

  // Action type metadata for rendering
  const actionTypeConfig = {
    analysis: {
      icon: <AnalysisIcon />,
      color: '#1976d2',
      bgColor: '#e3f2fd',
      label: 'Analysis',
    },
    lesson: {
      icon: <LessonIcon />,
      color: '#9c27b0',
      bgColor: '#f3e5f5',
      label: 'Lesson Learned',
    },
    deployment: {
      icon: <DeploymentIcon />,
      color: '#2e7d32',
      bgColor: '#e8f5e9',
      label: 'Deployment',
    },
    runtime_issue: {
      icon: <BugIcon />,
      color: '#d32f2f',
      bgColor: '#ffebee',
      label: 'Runtime Issue',
    },
  };

  const handleFilterChange = (event: SelectChangeEvent<string[]>) => {
    const value = event.target.value;
    setActionTypeFilter(typeof value === 'string' ? value.split(',') : value);
    setOffset(0); // Reset to first page
  };

  const handleLoadMore = () => {
    if (typedData?.pagination?.next_offset !== null && typedData?.pagination?.next_offset !== undefined) {
      setOffset(typedData.pagination.next_offset);
    }
  };

  const handleReset = () => {
    setOffset(0);
    setActionTypeFilter([]);
    refetch();
  };

  // Render action details based on type
  const renderActionDetails = (action: Action) => {
    const { action_type, metadata } = action;

    switch (action_type) {
      case 'analysis':
        return `${metadata.patterns_count} patterns, ${metadata.decisions_count} decisions`;

      case 'lesson':
        return `${metadata.category} - ${metadata.impact} impact`;

      case 'deployment':
        return metadata.description || 'Deployment updated';

      case 'runtime_issue':
        return `${metadata.severity} ${metadata.issue_type} in ${metadata.service_type}`;

      default:
        return 'Unknown action';
    }
  };

  // Render severity chip for runtime issues
  const renderSeverityChip = (severity: string) => {
    const severityColors: Record<string, 'error' | 'warning' | 'info' | 'default'> = {
      critical: 'error',
      high: 'error',
      medium: 'warning',
      low: 'info',
    };

    return (
      <Chip
        label={severity}
        size="small"
        color={severityColors[severity] || 'default'}
        variant="filled"
      />
    );
  };

  if (error) {
    return (
      <Alert severity="error" sx={{ mb: 2 }}>
        Failed to load recent activity: {(error as Error).message}
      </Alert>
    );
  }

  const actions: Action[] = typedData?.actions || [];
  const pagination = typedData?.pagination;

  return (
    <Card>
      <CardHeader
        avatar={<TimelineIcon />}
        title={
          <Typography variant="h6">
            {repository ? `Activity: ${repository}` : 'Recent Activity'}
          </Typography>
        }
        action={
          <Stack direction="row" spacing={1}>
            <Tooltip title="Refresh">
              <IconButton onClick={() => refetch()} size="small" disabled={isLoading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Stack>
        }
      />

      <Divider />

      {/* Filters */}
      <Box sx={{ p: 2, bgcolor: 'background.default' }}>
        <Stack direction="row" spacing={2} alignItems="center" flexWrap="wrap">
          <FilterIcon fontSize="small" />
          <FormControl size="small" sx={{ minWidth: 200 }}>
            <InputLabel>Filter by type</InputLabel>
            <Select
              multiple
              value={actionTypeFilter}
              onChange={handleFilterChange}
              label="Filter by type"
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => (
                    <Chip
                      key={value}
                      label={actionTypeConfig[value as keyof typeof actionTypeConfig]?.label || value}
                      size="small"
                    />
                  ))}
                </Box>
              )}
            >
              <MenuItem value="analysis">Analysis Runs</MenuItem>
              <MenuItem value="lesson">Lessons Learned</MenuItem>
              <MenuItem value="deployment">Deployments</MenuItem>
              <MenuItem value="runtime_issue">Runtime Issues</MenuItem>
            </Select>
          </FormControl>
          {actionTypeFilter.length > 0 && (
            <Button size="small" onClick={handleReset}>
              Clear Filters
            </Button>
          )}
        </Stack>
      </Box>

      <Divider />

      <CardContent sx={{ p: 0 }}>
        {isLoading ? (
          <Box display="flex" justifyContent="center" p={4}>
            <CircularProgress />
          </Box>
        ) : actions.length === 0 ? (
          <Box p={4} textAlign="center">
            <Typography color="text.secondary">
              No recent activity found
            </Typography>
          </Box>
        ) : (
          <>
            <List>
              {actions.map((action, index) => {
                const config = actionTypeConfig[action.action_type];

                return (
                  <React.Fragment key={`${action.action_type}-${action.reference_id}-${index}`}>
                    <ListItem alignItems="flex-start">
                      <ListItemAvatar>
                        <Avatar
                          sx={{
                            bgcolor: config.bgColor,
                            color: config.color,
                          }}
                        >
                          {config.icon}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={
                          <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
                            <Typography variant="subtitle2">
                              {config.label}
                            </Typography>
                            {action.action_type === 'runtime_issue' &&
                              renderSeverityChip(action.metadata.severity)
                            }
                            <Chip
                              label={action.repository}
                              size="small"
                              variant="outlined"
                            />
                          </Stack>
                        }
                        secondary={
                          <>
                            <Typography
                              component="span"
                              variant="body2"
                              color="text.primary"
                              sx={{ display: 'block', mt: 0.5 }}
                            >
                              {renderActionDetails(action)}
                            </Typography>
                            <Typography
                              component="span"
                              variant="caption"
                              color="text.secondary"
                            >
                              {formatDistanceToNow(new Date(action.timestamp), {
                                addSuffix: true,
                              })}
                            </Typography>
                          </>
                        }
                      />
                    </ListItem>
                    {index < actions.length - 1 && <Divider variant="inset" component="li" />}
                  </React.Fragment>
                );
              })}
            </List>

            {/* Pagination */}
            {pagination && (
              <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: 'background.default' }}>
                <Typography variant="caption" color="text.secondary">
                  Showing {offset + 1} - {offset + (typedData?.returned || 0)} of {typedData?.count || 0} actions
                </Typography>
                {pagination.has_more && (
                  <Button
                    variant="outlined"
                    onClick={handleLoadMore}
                    disabled={isLoading}
                  >
                    Load More
                  </Button>
                )}
              </Box>
            )}
          </>
        )}
      </CardContent>
    </Card>
  );
}
