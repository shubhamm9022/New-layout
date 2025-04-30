// /api/upload.js
export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ message: 'Only POST allowed' });
  }

  const token = process.env.GITHUB_TOKEN;
  const { jsonData, filePath } = req.body;

  try {
    const content = Buffer.from(JSON.stringify(jsonData, null, 2)).toString('base64');

    const githubRes = await fetch(`https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/contents/${filePath}`, {
      method: 'PUT',
      headers: {
        Authorization: `token ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        message: `Updated by admin panel - ${new Date().toISOString()}`,
        content,
        committer: {
          name: "Admin Panel",
          email: "admin@yourdomain.com"
        }
      }),
    });

    const data = await githubRes.json();

    if (githubRes.ok) {
      res.status(200).json({ success: true, url: data.content.html_url });
    } else {
      res.status(500).json({ error: data.message || 'Failed to upload' });
    }

  } catch (err) {
    res.status(500).json({ error: err.message });
  }
}
