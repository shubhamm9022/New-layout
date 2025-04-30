require('dotenv').config();
const express = require('express');
const cors = require('cors');
const bodyParser = require('body-parser');
const auth = require('basic-auth');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(cors());
app.use(bodyParser.json());

// Basic Authentication Middleware
const authenticate = (req, res, next) => {
  const credentials = auth(req);
  if (!credentials || 
      credentials.name !== process.env.ADMIN_USERNAME || 
      credentials.pass !== process.env.ADMIN_PASSWORD) {
    res.set('WWW-Authenticate', 'Basic realm="HEXA Admin"');
    return res.status(401).send('Authentication required');
  }
  next();
};

// GitHub API Config
const githubConfig = {
  repoOwner: 'shubhamm9022',
  repoName: 'New-layout',
  filePath: 'movies.json',
  branch: 'main'
};

// Routes
app.get('/api/movies', authenticate, async (req, res) => {
  try {
    const response = await axios.get(
      `https://api.github.com/repos/${githubConfig.repoOwner}/${githubConfig.repoName}/contents/${githubConfig.filePath}?ref=${githubConfig.branch}`,
      {
        headers: {
          'Authorization': `token ${process.env.GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json'
        }
      }
    );
    const content = Buffer.from(response.data.content, 'base64').toString();
    res.json(JSON.parse(content));
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/movies', authenticate, async (req, res) => {
  try {
    // Similar to your existing addMovieToGitHub logic
    // Implement your movie update logic here
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`);
});
