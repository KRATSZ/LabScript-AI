import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { motion } from 'framer-motion';

const MotionCard = motion(Card);

interface FeatureCardProps {
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  delay?: number;
}

const FeatureCard: React.FC<FeatureCardProps> = ({ 
  title, 
  description, 
  icon, 
  color,
  delay = 0
}) => {
  return (
    <MotionCard
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay }}
      whileHover={{ 
        y: -10,
        boxShadow: '0 10px 30px rgba(0, 0, 0, 0.1)',
      }}
      sx={{ 
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.3s ease, box-shadow 0.3s ease',
        cursor: 'default',
      }}
    >
      <CardContent sx={{ flexGrow: 1, p: 3 }}>
        <Box
          sx={{
            mb: 2.5,
            display: 'inline-flex',
            p: 1.5,
            borderRadius: 2,
            bgcolor: `${color}15`, // 15% opacity of the color
          }}
        >
          <Box sx={{ color: color }}>
            {icon}
          </Box>
        </Box>
        
        <Typography variant="h6" component="h3" gutterBottom fontWeight={600}>
          {title}
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          {description}
        </Typography>
      </CardContent>
    </MotionCard>
  );
};

export default FeatureCard;