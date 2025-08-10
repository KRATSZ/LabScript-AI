import React, { useState } from 'react';
import { 
  Box, 
  Typography, 
  Tabs, 
  Tab, 
  Grid, 
  Card, 
  CardContent, 
  Chip,
  Paper,
  InputBase,
  IconButton,
  Divider,
  Tooltip,
  useTheme,
  alpha,
  Badge,
  Stack
} from '@mui/material';
import { Search, Filter, Package, GripVertical } from 'lucide-react';
import { useAppContext, LabwareItem } from '../../context/AppContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`labware-tabpanel-${index}`}
      aria-labelledby={`labware-tab-${index}`}
    >
      {value === index && (
        <Box sx={{ py: 3, minHeight: 300 }}>
          {children}
        </Box>
      )}
    </div>
  );
};

// Updated labware data with simplified names
const labwareData: Record<string, LabwareItem[]> = {
  tipRacks: [
    // OT-2 Tips
    { type: 'tipRack', name: 'opentrons_96_tiprack_10ul', displayName: '10µL Tips' },
    { type: 'tipRack', name: 'opentrons_96_tiprack_20ul', displayName: '20µL Tips' },
    { type: 'tipRack', name: 'opentrons_96_tiprack_300ul', displayName: '300µL Tips' },
    { type: 'tipRack', name: 'opentrons_96_tiprack_1000ul', displayName: '1000µL Tips' },
    // Flex Tips
    { type: 'tipRack', name: 'opentrons_flex_96_tiprack_50ul', displayName: '50µL Flex Tips' },
    { type: 'tipRack', name: 'opentrons_flex_96_tiprack_200ul', displayName: '200µL Flex Tips' },
    { type: 'tipRack', name: 'opentrons_flex_96_tiprack_1000ul', displayName: '1000µL Flex Tips' },
    // Filter Tips
    { type: 'tipRack', name: 'opentrons_96_filtertiprack_200ul', displayName: '200µL Filter Tips' },
    { type: 'tipRack', name: 'opentrons_96_filtertiprack_1000ul', displayName: '1000µL Filter Tips' },
  ],
  plates: [
    // Standard plates
    { type: 'plate', name: 'corning_96_wellplate_360ul_flat', displayName: '96 Well 360µL' },
    { type: 'plate', name: 'nest_96_wellplate_200ul_flat', displayName: '96 Well 200µL' },
    { type: 'plate', name: 'nest_96_wellplate_100ul_pcr_full_skirt', displayName: '96 PCR 100µL' },
    // Deep well
    { type: 'plate', name: 'nest_96_wellplate_2ml_deep', displayName: '96 Deep Well 2mL' },
    // 384-well
    { type: 'plate', name: 'corning_384_wellplate_112ul_flat', displayName: '384 Well 112µL' },
    // Culture plates
    { type: 'plate', name: 'corning_6_wellplate_16.8ml_flat', displayName: '6 Well 16.8mL' },
    { type: 'plate', name: 'corning_12_wellplate_6.9ml_flat', displayName: '12 Well 6.9mL' },
    { type: 'plate', name: 'corning_24_wellplate_3.4ml_flat', displayName: '24 Well 3.4mL' },
  ],
  reservoirs: [
    { type: 'reservoir', name: 'nest_12_reservoir_15ml', displayName: '12-Well 15mL' },
    { type: 'reservoir', name: 'usascientific_12_reservoir_22ml', displayName: '12-Well 22mL' },
    { type: 'reservoir', name: 'agilent_1_reservoir_290ml', displayName: '1-Well 290mL' },
    { type: 'reservoir', name: 'nest_1_reservoir_195ml', displayName: '1-Well 195mL' },
  ],
  modules: [
    { type: 'module', name: 'temperature module gen2', displayName: 'Temperature Mod' },
    { type: 'module', name: 'magnetic module gen2', displayName: 'Magnetic Mod' },
    { type: 'module', name: 'thermocycler module', displayName: 'Thermocycler' },
    { type: 'module', name: 'heater shaker module', displayName: 'Heater-Shaker' },
  ],
  tubes: [
    { type: 'tube', name: 'opentrons_24_aluminumblock_nest_1.5ml_snapcap', displayName: '24x 1.5mL Tubes' },
    { type: 'tube', name: 'opentrons_24_aluminumblock_generic_2ml_screwcap', displayName: '24x 2mL Tubes' },
    { type: 'tube', name: 'opentrons_15_tuberack_falcon_15ml_conical', displayName: '15x 15mL Conical' },
    { type: 'tube', name: 'opentrons_6_tuberack_falcon_50ml_conical', displayName: '6x 50mL Conical' },
    { type: 'tube', name: 'opentrons_10_tuberack_falcon_4x50ml_6x15ml_conical', displayName: '4x 50mL + 6x 15mL' },
  ]
};

const LabwareLibrary: React.FC = () => {
  const { state } = useAppContext();
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  
  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };
  
  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchQuery(event.target.value);
  };

  const handleDragStart = (e: React.DragEvent<HTMLDivElement>, labware: LabwareItem) => {
    e.dataTransfer.setData('application/json', JSON.stringify(labware));
  };

  const handleDragEnd = () => {
    // Drag end logic if needed
  };
  
  const categories = ['Tip Racks', 'Plates', 'Reservoirs', 'Modules', 'Tubes'];
  const categoryKeys = ['tipRacks', 'plates', 'reservoirs', 'modules', 'tubes'];
  
  // Function to get filtered labware for a specific category based on robot model
  const getFilteredLabware = (categoryKey: string, labwareItems: LabwareItem[]) => {
    if (categoryKey === 'tipRacks') {
      if (state.robotModel === 'OT-2') {
        // For OT-2: only allow 20ul, 300ul, 1000ul tips, exclude flex and 1000ul filter tips
        return labwareItems.filter(tip => {
          const name = tip.name.toLowerCase();
          // Exclude flex tips and 1000ul filter tips
          if (name.includes('flex') || (name.includes('filter') && name.includes('1000ul'))) {
            return false;
          }
          // Only include 20ul, 300ul, 1000ul (non-filter)
          return name.includes('20ul') || name.includes('300ul') || 
                 (name.includes('1000ul') && !name.includes('filter'));
        });
      } else if (state.robotModel === 'Flex') {
        // For Flex: only flex tips
        const flexTips = ['50ul', '200ul', '1000ul'];
        return labwareItems.filter(tip => flexTips.some(size => tip.name.includes(size) && tip.name.includes('flex')));
      }
    }
    return labwareItems;
  };

  // Get labware for current tab and filter by robot model
  let currentLabware = labwareData[categoryKeys[tabValue]] || [];
  currentLabware = getFilteredLabware(categoryKeys[tabValue], currentLabware);

  const filteredLabware = currentLabware.filter(item => 
    item.displayName.toLowerCase().includes(searchQuery.toLowerCase()) ||
    item.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Function to get the actual count for each category based on robot model
  const getCategoryCount = (categoryKey: string) => {
    const items = labwareData[categoryKey] || [];
    return getFilteredLabware(categoryKey, items).length;
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'tipRack': return { main: theme.palette.primary.main, bg: alpha(theme.palette.primary.main, 0.1) };
      case 'plate': return { main: theme.palette.secondary.main, bg: alpha(theme.palette.secondary.main, 0.1) };
      case 'reservoir': return { main: theme.palette.info.main, bg: alpha(theme.palette.info.main, 0.1) };
      case 'module': return { main: theme.palette.success.main, bg: alpha(theme.palette.success.main, 0.1) };
      case 'tube': return { main: theme.palette.warning.main, bg: alpha(theme.palette.warning.main, 0.1) };
      default: return { main: theme.palette.grey[500], bg: alpha(theme.palette.grey[500], 0.1) };
    }
  };

  return (
    <Card 
      elevation={0}
      sx={{
        borderRadius: 3,
        border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
        background: `linear-gradient(135deg, ${alpha(theme.palette.background.paper, 0.8)} 0%, ${alpha(theme.palette.background.paper, 0.95)} 100%)`,
        backdropFilter: 'blur(10px)',
        transition: 'all 0.3s ease-in-out',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: `0 8px 32px ${alpha(theme.palette.primary.main, 0.15)}`,
        },
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <CardContent sx={{ p: 4, display: 'flex', flexDirection: 'column', flexGrow: 1 }}>
        {/* Header */}
        <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
          <Box
            sx={{
              p: 1.5,
              borderRadius: 2,
              background: `linear-gradient(45deg, ${alpha(theme.palette.info.main, 0.1)}, ${alpha(theme.palette.success.main, 0.1)})`,
            }}
          >
            <Package size={24} color={theme.palette.info.main} />
          </Box>
          <Box>
            <Typography variant="h6" component="h3" sx={{ fontWeight: 700 }}>
              Labware Library
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Drag labware to the deck configuration above
            </Typography>
          </Box>
          <Box sx={{ ml: 'auto' }}>
            <Badge badgeContent={filteredLabware.length} color="primary">
              <Chip 
                label="Available"
                variant="outlined"
                size="small"
                sx={{ fontWeight: 500 }}
              />
            </Badge>
          </Box>
        </Stack>

        {/* Search bar */}
        <Paper
          component="form"
          sx={{
            p: '8px 16px',
            display: 'flex',
            alignItems: 'center',
            width: '100%',
            mb: 3,
            border: `1px solid ${alpha(theme.palette.primary.main, 0.1)}`,
            borderRadius: 2,
            background: alpha(theme.palette.background.default, 0.5),
            transition: 'all 0.3s ease',
            '&:hover': {
              border: `1px solid ${alpha(theme.palette.primary.main, 0.3)}`,
              background: alpha(theme.palette.background.default, 0.8),
            },
            '&:focus-within': {
              border: `1px solid ${theme.palette.primary.main}`,
              background: alpha(theme.palette.background.default, 1),
              boxShadow: `0 4px 12px ${alpha(theme.palette.primary.main, 0.15)}`,
            }
          }}
        >
          <IconButton sx={{ p: '8px' }} aria-label="search">
            <Search size={20} />
          </IconButton>
          <InputBase
            sx={{ ml: 1, flex: 1, fontSize: '0.9rem' }}
            placeholder="Search labware..."
            value={searchQuery}
            onChange={handleSearchChange}
          />
          <Divider sx={{ height: 28, m: 0.5 }} orientation="vertical" />
          <Tooltip title="Filter options" arrow>
            <IconButton sx={{ p: '8px' }} aria-label="filter">
              <Filter size={20} />
            </IconButton>
          </Tooltip>
        </Paper>
        
        {/* Category tabs */}
        <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
          <Tabs 
            value={tabValue} 
            onChange={handleTabChange}
            variant="scrollable"
            scrollButtons="auto"
            aria-label="labware categories"
            sx={{
              '& .MuiTab-root': {
                fontWeight: 600,
                fontSize: '0.9rem',
                textTransform: 'none',
                minHeight: 48,
                '&.Mui-selected': {
                  color: theme.palette.primary.main,
                }
              },
              '& .MuiTabs-indicator': {
                height: 3,
                borderRadius: '3px 3px 0 0',
                background: `linear-gradient(45deg, ${theme.palette.primary.main}, ${theme.palette.secondary.main})`,
              }
            }}
          >
            {categories.map((category, index) => (
              <Tab 
                key={index} 
                label={
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    {category}
                    <Chip 
                      label={getCategoryCount(categoryKeys[index])}
                      size="small"
                      sx={{ 
                        height: 20, 
                        fontSize: '0.7rem',
                        color: index === tabValue ? theme.palette.primary.main : theme.palette.text.secondary,
                        borderColor: index === tabValue ? theme.palette.primary.main : theme.palette.text.secondary,
                      }}
                      variant="outlined"
                    />
                  </Box>
                }
                id={`labware-tab-${index}`}
                aria-controls={`labware-tabpanel-${index}`}
              />
            ))}
          </Tabs>
        </Box>
        
        {/* Tab panels */}
        <Box sx={{ flexGrow: 1, overflowY: 'auto', pr: 1, mr: -1 }}>
          {categories.map((category, index) => (
            <TabPanel key={index} value={tabValue} index={index}>
              {filteredLabware.length > 0 ? (
                <Grid container spacing={2}>
                  {filteredLabware.map((labware, i) => {
                    const typeColor = getTypeColor(labware.type);
                    return (
                      <Grid item xs={6} sm={4} md={4} key={i}>
                        <Card
                          variant="outlined"
                          draggable
                          onDragStart={(e) => handleDragStart(e, labware)}
                          onDragEnd={handleDragEnd}
                          sx={{
                            cursor: 'grab',
                            transition: 'all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275)',
                            border: `1px solid ${alpha(typeColor.main, 0.12)}`,
                            background: `linear-gradient(145deg, ${alpha(theme.palette.background.paper, 0.95)} 0%, ${alpha(theme.palette.background.paper, 0.85)} 100%)`,
                            backdropFilter: 'blur(12px)',
                            position: 'relative',
                            overflow: 'hidden',
                            aspectRatio: '1 / 1',
                            display: 'flex',
                            flexDirection: 'column',
                            borderRadius: 3,
                            boxShadow: `0 2px 12px ${alpha(typeColor.main, 0.08)}`,
                            '&::before': {
                              content: '""',
                              position: 'absolute',
                              top: 0,
                              left: 0,
                              right: 0,
                              height: '3px',
                              background: `linear-gradient(90deg, ${typeColor.main}, ${alpha(typeColor.main, 0.6)})`,
                              borderRadius: '12px 12px 0 0',
                            },
                            '&::after': {
                              content: '""',
                              position: 'absolute',
                              top: -2,
                              left: -2,
                              right: -2,
                              bottom: -2,
                              background: `linear-gradient(45deg, ${alpha(typeColor.main, 0.1)}, transparent, ${alpha(typeColor.main, 0.1)})`,
                              borderRadius: 'inherit',
                              zIndex: -1,
                              opacity: 0,
                              transition: 'opacity 0.3s ease',
                            },
                            '&:hover': {
                              transform: 'translateY(-6px) scale(1.03)',
                              boxShadow: `0 12px 40px ${alpha(typeColor.main, 0.2)}`,
                              border: `1px solid ${alpha(typeColor.main, 0.3)}`,
                              zIndex: 3,
                              '&::before': {
                                height: '4px',
                                background: `linear-gradient(90deg, ${typeColor.main}, ${theme.palette.common.white})`,
                              },
                              '&::after': {
                                opacity: 1,
                              }
                            },
                            '&:active': {
                              cursor: 'grabbing',
                              transform: 'translateY(-3px) scale(1.01)',
                            },
                          }}
                        >
                          <CardContent sx={{ 
                            p: 2.5, 
                            display: 'flex', 
                            flexDirection: 'column', 
                            justifyContent: 'space-between', 
                            flexGrow: 1,
                            position: 'relative',
                            height: '100%'
                          }}>
                            <Box sx={{ textAlign: 'center', mt: 1 }}>
                              <Typography variant="subtitle2" sx={{ 
                                fontWeight: 700, 
                                fontSize: '0.95rem',
                                color: theme.palette.text.primary,
                                lineHeight: 1.2,
                                mb: 1.5,
                                letterSpacing: '0.02em'
                              }}>
                                {labware.displayName}
                              </Typography>
                            </Box>
                            
                            <Stack spacing={1.5} alignItems="center" sx={{ mt: 'auto' }}>
                              <Box sx={{
                                width: 40,
                                height: 40,
                                borderRadius: '50%',
                                background: `linear-gradient(135deg, ${alpha(typeColor.main, 0.2)}, ${alpha(typeColor.main, 0.05)})`,
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                border: `2px solid ${alpha(typeColor.main, 0.25)}`,
                                mb: 1
                              }}>
                                <Package size={18} color={typeColor.main} />
                              </Box>
                              
                              <Chip 
                                size="small" 
                                label={labware.type} 
                                sx={{ 
                                  bgcolor: alpha(typeColor.main, 0.1),
                                  color: typeColor.main,
                                  border: `1px solid ${alpha(typeColor.main, 0.25)}`,
                                  fontWeight: 700,
                                  fontSize: '0.7rem',
                                  height: 24,
                                  letterSpacing: '0.5px',
                                  textTransform: 'uppercase',
                                  '& .MuiChip-label': {
                                    px: 1.5,
                                  }
                                }} 
                              />
                              
                              <Tooltip title="Drag to Deck Configuration" placement="bottom" arrow>
                                <Box sx={{
                                  cursor: 'grab',
                                  color: alpha(theme.palette.text.secondary, 0.5),
                                  transition: 'all 0.2s ease',
                                  padding: 0.5,
                                  borderRadius: 1,
                                  '&:hover': {
                                    color: typeColor.main,
                                    background: alpha(typeColor.main, 0.1),
                                    transform: 'scale(1.1)',
                                  }
                                }}>
                                  <GripVertical size={16} />
                                </Box>
                              </Tooltip>
                            </Stack>
                          </CardContent>
                        </Card>
                      </Grid>
                    );
                  })}
                </Grid>
              ) : (
                <Box sx={{ 
                  py: 6, 
                  textAlign: 'center',
                  borderRadius: 2,
                  background: alpha(theme.palette.background.default, 0.3),
                  border: `1px dashed ${alpha(theme.palette.text.secondary, 0.3)}`,
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                }}>
                  <Package size={48} style={{ opacity: 0.3, marginBottom: 16 }} color={theme.palette.text.secondary} />
                  <Typography variant="h6" color="text.secondary" sx={{ fontWeight: 500, mb: 1 }}>
                    No matching {category.toLowerCase()} found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Please try adjusting your search criteria or select another category
                  </Typography>
                </Box>
              )}
            </TabPanel>
          ))}
        </Box>
      </CardContent>
    </Card>
  );
};

export default LabwareLibrary;