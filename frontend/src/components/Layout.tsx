import React from 'react';
import { Outlet, Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Container, Box } from '@mui/material';

const Layout: React.FC = () => {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <AppBar position="static">
        <Toolbar>
          <Typography variant="h6" component={Link} to="/" sx={{ color: 'white', textDecoration: 'none' }}>
            Trading Bot
          </Typography>
          <Box sx={{ ml: 3, display: 'flex', gap: 2 }}>
            <Link to="/strategies" style={{ color: 'white' }}>Strategies</Link>
            <Link to="/portfolio" style={{ color: 'white' }}>Portfolio</Link>
            <Link to="/signals" style={{ color: 'white' }}>Signals</Link>
          </Box>
        </Toolbar>
      </AppBar>
      <Container component="main" sx={{ flex: 1, py: 3 }}>
        <Outlet />
      </Container>
    </Box>
  );
};

export default Layout;
