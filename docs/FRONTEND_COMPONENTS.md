# Frontend Component Examples

Complete React component examples for the Pattern Discovery Agent frontend.

## Table of Contents

1. [Layout Components](#layout-components)
2. [Dashboard Components](#dashboard-components)
3. [Pattern Visualization](#pattern-visualization)
4. [Repository Components](#repository-components)
5. [Configuration Components](#configuration-components)
6. [Deployment Components](#deployment-components)

---

## Layout Components

### Main Layout with Navigation

```typescript
// src/components/layout/Layout.tsx
import { useState } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  AppBar,
  Box,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Typography,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Folder as FolderIcon,
  Category as CategoryIcon,
  Settings as SettingsIcon,
  CloudUpload as DeploymentIcon,
  Hub as AgentsIcon,
} from '@mui/icons-material';
import HealthIndicator from '../common/HealthIndicator';

const drawerWidth = 240;

const menuItems = [
  { text: 'Dashboard', icon: <DashboardIcon />, path: '/' },
  { text: 'Repositories', icon: <FolderIcon />, path: '/repositories' },
  { text: 'Patterns', icon: <CategoryIcon />, path: '/patterns' },
  { text: 'Deployment', icon: <DeploymentIcon />, path: '/deployment' },
  { text: 'Agents', icon: <AgentsIcon />, path: '/agents' },
  { text: 'Configuration', icon: <SettingsIcon />, path: '/configuration' },
];

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <Box>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          Dev Nexus
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => (
          <ListItem key={item.text} disablePadding>
            <ListItemButton
              selected={location.pathname === item.path}
              onClick={() => {
                navigate(item.path);
                setMobileOpen(false);
              }}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            Pattern Discovery Agent
          </Typography>
          <HealthIndicator />
        </Toolbar>
      </AppBar>

      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{ keepMounted: true }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>

      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
        }}
      >
        <Outlet />
      </Box>
    </Box>
  );
}
```

---

## Dashboard Components

### Statistics Cards

```typescript
// src/components/dashboard/StatCard.tsx
import { Card, CardContent, Typography, Box, Skeleton } from '@mui/material';
import { ReactNode } from 'react';

interface StatCardProps {
  title: string;
  value: string | number;
  icon: ReactNode;
  color?: 'primary' | 'secondary' | 'success' | 'error' | 'warning' | 'info';
  loading?: boolean;
}

export default function StatCard({
  title,
  value,
  icon,
  color = 'primary',
  loading = false,
}: StatCardProps) {
  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Box sx={{ color: `${color}.main`, mr: 1 }}>{icon}</Box>
          <Typography variant="subtitle2" color="text.secondary">
            {title}
          </Typography>
        </Box>
        {loading ? (
          <Skeleton variant="text" width="60%" height={40} />
        ) : (
          <Typography variant="h3" color={`${color}.main`}>
            {value}
          </Typography>
        )}
      </CardContent>
    </Card>
  );
}
```

### Complete Dashboard Page

```typescript
// src/pages/Dashboard.tsx
import { Grid, Typography, Paper, Box } from '@mui/material';
import {
  CheckCircle,
  Folder,
  Category,
  Hub,
} from '@mui/icons-material';
import { useHealth, useRepositories, useCrossRepoPatterns, useExternalAgents } from '../hooks/usePatterns';
import StatCard from '../components/dashboard/StatCard';
import RecentActivity from '../components/dashboard/RecentActivity';
import PatternSummaryChart from '../components/dashboard/PatternSummaryChart';

export default function Dashboard() {
  const { data: health, isLoading: healthLoading } = useHealth();
  const { data: repos, isLoading: reposLoading } = useRepositories();
  const { data: patterns, isLoading: patternsLoading } = useCrossRepoPatterns();
  const { data: agents, isLoading: agentsLoading } = useExternalAgents();

  const healthyAgents = agents?.agents.filter(a => a.status === 'healthy').length || 0;

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Pattern Discovery Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Stat Cards */}
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Service Status"
            value={health?.status || 'Unknown'}
            icon={<CheckCircle />}
            color="success"
            loading={healthLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Repositories"
            value={repos?.total_count || 0}
            icon={<Folder />}
            color="primary"
            loading={reposLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Cross-Repo Patterns"
            value={patterns?.total_patterns || 0}
            icon={<Category />}
            color="secondary"
            loading={patternsLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Connected Agents"
            value={`${healthyAgents}/${agents?.agents.length || 0}`}
            icon={<Hub />}
            color="info"
            loading={agentsLoading}
          />
        </Grid>

        {/* Pattern Summary Chart */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, height: '400px' }}>
            <Typography variant="h6" gutterBottom>
              Pattern Distribution
            </Typography>
            <PatternSummaryChart repositories={repos?.repositories || []} />
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 3, height: '400px', overflow: 'auto' }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <RecentActivity repositories={repos?.repositories || []} />
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
```

### Pattern Summary Chart

```typescript
// src/components/dashboard/PatternSummaryChart.tsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Repository } from '../../services/a2aClient';

interface PatternSummaryChartProps {
  repositories: Repository[];
}

export default function PatternSummaryChart({ repositories }: PatternSummaryChartProps) {
  const data = repositories.slice(0, 10).map(repo => ({
    name: repo.name.split('/')[1] || repo.name,
    patterns: repo.latest_patterns?.patterns?.length || 0,
    decisions: repo.latest_patterns?.decisions?.length || 0,
    components: repo.latest_patterns?.reusable_components?.length || 0,
  }));

  return (
    <ResponsiveContainer width="100%" height="90%">
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Bar dataKey="patterns" fill="#8884d8" name="Patterns" />
        <Bar dataKey="decisions" fill="#82ca9d" name="Decisions" />
        <Bar dataKey="components" fill="#ffc658" name="Components" />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

---

## Pattern Visualization

### Interactive Pattern Network Graph

```typescript
// src/components/patterns/PatternNetworkGraph.tsx
import { useEffect, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Box, Paper, Typography, CircularProgress } from '@mui/material';
import { useCrossRepoPatterns, useRepositories } from '../../hooks/usePatterns';

export default function PatternNetworkGraph() {
  const { data: patterns, isLoading: patternsLoading } = useCrossRepoPatterns();
  const { data: repos, isLoading: reposLoading } = useRepositories();
  const graphRef = useRef<any>();

  const isLoading = patternsLoading || reposLoading;

  // Transform data for force graph
  const graphData = {
    nodes: [
      // Repository nodes
      ...(repos?.repositories || []).map(repo => ({
        id: repo.name,
        name: repo.name,
        type: 'repository',
        val: 10,
      })),
      // Pattern nodes
      ...(patterns?.patterns || []).map(pattern => ({
        id: pattern.pattern_name,
        name: pattern.pattern_name,
        type: 'pattern',
        val: pattern.occurrences * 5,
      })),
    ],
    links: (patterns?.patterns || []).flatMap(pattern =>
      pattern.repositories.map(repo => ({
        source: repo,
        target: pattern.pattern_name,
      }))
    ),
  };

  useEffect(() => {
    if (graphRef.current) {
      // Zoom to fit
      graphRef.current.zoomToFit(400);
    }
  }, [graphData]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="600px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Pattern Relationship Network
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Blue circles: Repositories | Orange circles: Patterns
      </Typography>
      <Box sx={{ height: '600px', border: '1px solid #ddd', borderRadius: 1 }}>
        <ForceGraph2D
          ref={graphRef}
          graphData={graphData}
          nodeLabel="name"
          nodeColor={node => (node.type === 'repository' ? '#1976d2' : '#ff9800')}
          nodeRelSize={6}
          linkColor={() => '#999'}
          linkWidth={1}
          linkDirectionalParticles={2}
          linkDirectionalParticleWidth={2}
          onNodeClick={(node) => {
            console.log('Node clicked:', node);
          }}
        />
      </Box>
    </Paper>
  );
}
```

### Pattern List View

```typescript
// src/components/patterns/PatternList.tsx
import { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Chip,
  TextField,
  Grid,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import { ExpandMore, Code } from '@mui/icons-material';
import { useCrossRepoPatterns } from '../../hooks/usePatterns';

export default function PatternList() {
  const [searchTerm, setSearchTerm] = useState('');
  const { data, isLoading } = useCrossRepoPatterns();

  const filteredPatterns = data?.patterns.filter(pattern =>
    pattern.pattern_name.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <Box>
      <TextField
        fullWidth
        label="Search patterns..."
        variant="outlined"
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        sx={{ mb: 3 }}
      />

      {isLoading ? (
        <Typography>Loading patterns...</Typography>
      ) : (
        <Grid container spacing={2}>
          {filteredPatterns.map((pattern) => (
            <Grid item xs={12} key={pattern.pattern_name}>
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMore />}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, width: '100%' }}>
                    <Code />
                    <Typography variant="h6">{pattern.pattern_name}</Typography>
                    <Chip
                      label={`${pattern.occurrences} repos`}
                      color="primary"
                      size="small"
                    />
                  </Box>
                </AccordionSummary>
                <AccordionDetails>
                  <Typography variant="subtitle2" gutterBottom>
                    Used in repositories:
                  </Typography>
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                    {pattern.repositories.map(repo => (
                      <Chip key={repo} label={repo} variant="outlined" />
                    ))}
                  </Box>

                  {pattern.variations.length > 0 && (
                    <>
                      <Typography variant="subtitle2" gutterBottom>
                        Variations:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {pattern.variations.map((variation, idx) => (
                          <Chip key={idx} label={variation} size="small" />
                        ))}
                      </Box>
                    </>
                  )}
                </AccordionDetails>
              </Accordion>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
}
```

---

## Repository Components

### Repository Card

```typescript
// src/components/repository/RepositoryCard.tsx
import {
  Card,
  CardContent,
  Typography,
  Box,
  Chip,
  Button,
  CardActions,
} from '@mui/material';
import { Folder, AccessTime, Code } from '@mui/icons-material';
import { Repository } from '../../services/a2aClient';
import { formatDistanceToNow } from 'date-fns';

interface RepositoryCardProps {
  repository: Repository;
  onViewDetails: (repo: Repository) => void;
}

export default function RepositoryCard({ repository, onViewDetails }: RepositoryCardProps) {
  const lastUpdate = new Date(repository.last_updated);

  return (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
          <Folder color="primary" />
          <Typography variant="h6" component="div">
            {repository.name}
          </Typography>
        </Box>

        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <Chip
            icon={<Code />}
            label={`${repository.latest_patterns?.patterns?.length || 0} patterns`}
            size="small"
            color="primary"
            variant="outlined"
          />
          <Chip
            icon={<AccessTime />}
            label={formatDistanceToNow(lastUpdate, { addSuffix: true })}
            size="small"
            variant="outlined"
          />
        </Box>

        <Typography variant="body2" color="text.secondary">
          Domain: {repository.latest_patterns?.problem_domain || 'Unknown'}
        </Typography>

        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 2 }}>
          {repository.latest_patterns?.keywords?.slice(0, 5).map((keyword, idx) => (
            <Chip key={idx} label={keyword} size="small" />
          ))}
        </Box>
      </CardContent>

      <CardActions>
        <Button size="small" onClick={() => onViewDetails(repository)}>
          View Details
        </Button>
      </CardActions>
    </Card>
  );
}
```

### Repository Details Dialog

```typescript
// src/components/repository/RepositoryDetailsDialog.tsx
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Box,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText,
  Chip,
} from '@mui/material';
import { useState } from 'react';
import { Repository } from '../../services/a2aClient';
import { useDeploymentInfo } from '../../hooks/usePatterns';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel({ children, value, index }: TabPanelProps) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box sx={{ py: 2 }}>{children}</Box>}
    </div>
  );
}

interface RepositoryDetailsDialogProps {
  repository: Repository | null;
  open: boolean;
  onClose: () => void;
}

export default function RepositoryDetailsDialog({
  repository,
  open,
  onClose,
}: RepositoryDetailsDialogProps) {
  const [tabValue, setTabValue] = useState(0);
  const { data: deployment } = useDeploymentInfo(repository?.name || '', {
    enabled: open && !!repository,
  });

  if (!repository) return null;

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>{repository.name}</DialogTitle>
      <DialogContent>
        <Tabs value={tabValue} onChange={(_, v) => setTabValue(v)}>
          <Tab label="Patterns" />
          <Tab label="Decisions" />
          <Tab label="Components" />
          <Tab label="Deployment" />
        </Tabs>

        <TabPanel value={tabValue} index={0}>
          <List>
            {repository.latest_patterns?.patterns?.map((pattern, idx) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={pattern.name}
                  secondary={
                    <>
                      <Typography variant="body2">{pattern.description}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        Context: {pattern.context}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <List>
            {repository.latest_patterns?.decisions?.map((decision, idx) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={decision.what}
                  secondary={
                    <>
                      <Typography variant="body2">Why: {decision.why}</Typography>
                      <Typography variant="caption">
                        Alternatives: {decision.alternatives}
                      </Typography>
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <List>
            {repository.latest_patterns?.reusable_components?.map((component, idx) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={component.name}
                  secondary={
                    <>
                      <Typography variant="body2">{component.purpose}</Typography>
                      <Chip label={component.location} size="small" sx={{ mt: 1 }} />
                    </>
                  }
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <Typography variant="subtitle2" gutterBottom>
            CI/CD Platform
          </Typography>
          <Chip label={deployment?.deployment?.ci_cd_platform || 'Unknown'} sx={{ mb: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            Deployment Scripts
          </Typography>
          <List>
            {deployment?.deployment?.scripts?.map((script, idx) => (
              <ListItem key={idx}>
                <ListItemText
                  primary={script.name}
                  secondary={script.description}
                />
              </ListItem>
            ))}
          </List>
        </TabPanel>
      </DialogContent>

      <DialogActions>
        <Button onClick={onClose}>Close</Button>
      </DialogActions>
    </Dialog>
  );
}
```

---

## Configuration Components

### Configuration Editor

```typescript
// src/components/configuration/ConfigurationEditor.tsx
import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
} from '@mui/material';
import { Save } from '@mui/icons-material';
import toast from 'react-hot-toast';

interface Config {
  apiUrl: string;
  authToken: string;
  notificationsEnabled: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
}

export default function ConfigurationEditor() {
  const [config, setConfig] = useState<Config>({
    apiUrl: import.meta.env.VITE_API_BASE_URL || '',
    authToken: '',
    notificationsEnabled: true,
    autoRefresh: true,
    refreshInterval: 60,
  });

  const [isSaving, setIsSaving] = useState(false);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      // Save to localStorage (or send to backend)
      localStorage.setItem('app-config', JSON.stringify(config));
      toast.success('Configuration saved successfully!');
    } catch (error) {
      toast.error('Failed to save configuration');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Configuration
      </Typography>

      <Alert severity="info" sx={{ mb: 3 }}>
        Changes will be saved to your browser's local storage.
      </Alert>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        {/* API Settings */}
        <Box>
          <Typography variant="h6" gutterBottom>
            API Settings
          </Typography>
          <TextField
            fullWidth
            label="API Base URL"
            value={config.apiUrl}
            onChange={(e) => setConfig({ ...config, apiUrl: e.target.value })}
            helperText="Backend API endpoint URL"
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Authentication Token"
            type="password"
            value={config.authToken}
            onChange={(e) => setConfig({ ...config, authToken: e.target.value })}
            helperText="Optional: For protected A2A endpoints"
          />
        </Box>

        <Divider />

        {/* App Settings */}
        <Box>
          <Typography variant="h6" gutterBottom>
            Application Settings
          </Typography>
          <FormControlLabel
            control={
              <Switch
                checked={config.notificationsEnabled}
                onChange={(e) =>
                  setConfig({ ...config, notificationsEnabled: e.target.checked })
                }
              />
            }
            label="Enable notifications"
          />
          <FormControlLabel
            control={
              <Switch
                checked={config.autoRefresh}
                onChange={(e) => setConfig({ ...config, autoRefresh: e.target.checked })}
              />
            }
            label="Auto-refresh data"
          />
          {config.autoRefresh && (
            <TextField
              type="number"
              label="Refresh Interval (seconds)"
              value={config.refreshInterval}
              onChange={(e) =>
                setConfig({ ...config, refreshInterval: parseInt(e.target.value) })
              }
              sx={{ mt: 2, width: '200px' }}
              inputProps={{ min: 10, max: 300 }}
            />
          )}
        </Box>

        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2 }}>
          <Button
            variant="contained"
            startIcon={<Save />}
            onClick={handleSave}
            disabled={isSaving}
          >
            {isSaving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
}
```

---

## Deployment Components

### Lessons Learned List

```typescript
// src/components/deployment/LessonsLearnedList.tsx
import {
  List,
  ListItem,
  ListItemText,
  Chip,
  Box,
  Typography,
  Paper,
} from '@mui/material';
import { format } from 'date-fns';
import { LessonLearned } from '../../services/a2aClient';

interface LessonsLearnedListProps {
  lessons: LessonLearned[];
}

export default function LessonsLearnedList({ lessons }: LessonsLearnedListProps) {
  const getImpactColor = (impact: string) => {
    switch (impact.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  return (
    <Paper sx={{ p: 2 }}>
      <Typography variant="h6" gutterBottom>
        Lessons Learned
      </Typography>
      <List>
        {lessons.map((lesson, idx) => (
          <ListItem key={idx} alignItems="flex-start" divider>
            <ListItemText
              primary={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="subtitle1">{lesson.title}</Typography>
                  <Chip
                    label={lesson.impact}
                    size="small"
                    color={getImpactColor(lesson.impact)}
                  />
                  <Chip label={lesson.category} size="small" variant="outlined" />
                </Box>
              }
              secondary={
                <>
                  <Typography variant="body2" sx={{ mb: 1 }}>
                    {lesson.description}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {format(new Date(lesson.date), 'PPP')}
                  </Typography>
                </>
              }
            />
          </ListItem>
        ))}
      </List>
    </Paper>
  );
}
```

---

## Common Components

### Health Indicator

```typescript
// src/components/common/HealthIndicator.tsx
import { Chip, CircularProgress } from '@mui/material';
import { CheckCircle, Error } from '@mui/icons-material';
import { useHealth } from '../../hooks/usePatterns';

export default function HealthIndicator() {
  const { data, isLoading, isError } = useHealth();

  if (isLoading) return <CircularProgress size={20} />;
  if (isError)
    return (
      <Chip icon={<Error />} label="Error" color="error" size="small" />
    );

  return (
    <Chip
      icon={<CheckCircle />}
      label={data?.status || 'Unknown'}
      color={data?.status === 'healthy' ? 'success' : 'warning'}
      size="small"
    />
  );
}
```

---

## Next Steps

1. Copy components to your frontend project
2. Customize styling to match your brand
3. Add error boundaries for production
4. Implement loading skeletons
5. Add unit tests for components
6. Set up Storybook for component development

For complete setup instructions, see `FRONTEND_SETUP.md`.
For API integration details, see `FRONTEND_API_CLIENT.md`.
