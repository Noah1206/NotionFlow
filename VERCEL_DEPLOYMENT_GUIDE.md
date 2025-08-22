# Vercel Deployment Guide for NotionFlow

## Prerequisites
- Vercel account (sign up at https://vercel.com)
- GitHub repository connected (already set up at https://github.com/Noah1206/NotionFlow)
- Environment variables ready (see `.env.example`)

## Deployment Steps

### 1. Connect to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click "Add New Project"
3. Import from GitHub repository:
   - Search for "NotionFlow"
   - Select the repository `Noah1206/NotionFlow`
   - Click "Import"

### 2. Configure Project Settings

1. **Framework Preset**: Select "Other"
2. **Root Directory**: Leave as `./` (default)
3. **Build & Output Settings**:
   - Build Command: Leave empty (using default)
   - Output Directory: Leave as default
   - Install Command: `pip install -r requirements.txt`

### 3. Configure Environment Variables

Click on "Environment Variables" and add the following:

#### Required Variables:
```
SUPABASE_URL=<your-supabase-url>
SUPABASE_API_KEY=<your-supabase-anon-key>
SUPABASE_SERVICE_ROLE_KEY=<your-service-role-key>
API_KEY_ENCRYPTION_KEY=<your-encryption-key>
FLASK_SECRET_KEY=<your-flask-secret-key>
FLASK_ENV=production
```

#### Optional OAuth Variables:
```
GITHUB_CLIENT_ID=<your-github-client-id>
GITHUB_CLIENT_SECRET=<your-github-client-secret>
NOTION_CLIENT_ID=<your-notion-client-id>
NOTION_CLIENT_SECRET=<your-notion-client-secret>
SLACK_CLIENT_ID=<your-slack-client-id>
SLACK_CLIENT_SECRET=<your-slack-client-secret>
```

### 4. Deploy

1. Click "Deploy" button
2. Wait for the deployment to complete (usually 2-5 minutes)
3. Your app will be available at: `https://[your-project-name].vercel.app`

## Automatic Deployments

Vercel automatically deploys when you push to the main branch:
- Every push to `main` triggers a production deployment
- Pull requests create preview deployments

## Custom Domain (Optional)

1. Go to your project settings in Vercel
2. Navigate to "Domains"
3. Add your custom domain
4. Follow DNS configuration instructions

## Monitoring & Logs

- **Functions**: Check function logs in Vercel dashboard under "Functions" tab
- **Analytics**: Available in the "Analytics" tab
- **Errors**: View error logs in "Functions" → "Logs"

## Troubleshooting

### Common Issues:

1. **Module Import Errors**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility (3.9+)

2. **Environment Variables Not Working**
   - Verify all required variables are set
   - Redeploy after adding/changing variables

3. **Static Files Not Loading**
   - Check `vercel.json` routes configuration
   - Verify static file paths are correct

4. **Function Timeout**
   - Default timeout is 30 seconds
   - Can be adjusted in `vercel.json` if needed

### Support

For issues specific to:
- **Vercel**: Check [Vercel Documentation](https://vercel.com/docs)
- **NotionFlow**: Open an issue on GitHub

## Local Development

To test Vercel functions locally:

```bash
# Install Vercel CLI
npm i -g vercel

# Run development server
vercel dev
```

## Security Notes

- Never commit `.env` files to git
- Use Vercel's environment variables for sensitive data
- Rotate API keys regularly
- Enable 2FA on both GitHub and Vercel accounts

---

Last updated: 2025-08-22