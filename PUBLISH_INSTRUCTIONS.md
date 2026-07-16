# Publishing Quizzes to Blogger

## Quick Start (Automated)

1. **Set up your Blogger Blog ID:**
   ```bash
   # Find your Blog ID in Blogger dashboard URL
   # URL format: https://www.blogger.com/blog/posts/BLOG_ID
   echo "blogger_blog_id=YOUR_ACTUAL_BLOG_ID" > .env
   ```

2. **Authenticate with Google OAuth:**
   ```bash
   python3 app.py auth
   ```
   - This opens a browser for Google authentication
   - Grant permission to your Blogger account
   - Credentials are saved for future use

3. **Publish all quizzes:**
   ```bash
   python3 publish_quizzes.py
   ```

## Manual Upload (Alternative)

If you prefer manual upload to CB Blogger theme:

1. Go to Blogger Dashboard → Posts → New Post
2. For each quiz file:
   - Click "HTML" view (not Compose)
   - Copy entire content from quiz HTML file
   - Paste into Blogger editor
   - Set title and labels
   - Publish

## Quiz Files to Upload

| File | Title | Labels |
|------|-------|--------|
| `indian-constitutional-amendments-essentials-quiz.html` | Indian Constitutional Amendments Quiz | quiz, constitutional amendments, kpsc, upsc, polity |
| `fundamental-rights-india-quiz.html` | Fundamental Rights Quiz | quiz, fundamental rights, kpsc, upsc, polity |
| `directive-principles-india-quiz.html` | Directive Principles Quiz | quiz, directive principles, kpsc, upsc, polity |
| `presidents-rule-article-356-quiz.html` | President's Rule (Article 356) Quiz | quiz, presidents rule, kpsc, upsc, polity, federal structure |
| `panchayati-raj-73rd-amendment-quiz.html` | Panchayati Raj Quiz | quiz, panchayati raj, kpsc, upsc, local governance |
| `emergency-provisions-india-quiz.html` | Emergency Provisions Quiz | quiz, emergency provisions, kpsc, upsc, polity |

## Verification

After publishing, verify:
- Quiz renders correctly on desktop and mobile
- Progress bar and navigation work
- Score calculation functions
- Schema markup is present (view source for JSON-LD)

## Next Steps

After publishing, consider:
1. Creating a `/quizzes` landing page
2. Adding internal links from recruitment articles to relevant quizzes
3. Setting up Telegram bot for daily quiz sharing