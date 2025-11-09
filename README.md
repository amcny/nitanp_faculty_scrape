# NIT Andhra Pradesh Faculty Directory

A modern, responsive web application for browsing and managing faculty information from NIT Andhra Pradesh. Features live data scraping, caching, and real-time updates.

## 🚀 Features

- **Live Faculty Data** - Real-time scraping from NIT AP website
- **Smart Caching** - Instant load times with intelligent data caching
- **Responsive Design** - Fully mobile-optimized interface
- **Advanced Search** - Search faculty by name, title, and department
- **Department Filtering** - Browse faculty by department
- **Contact Information** - Email and phone numbers (when available)
- **Areas of Interest** - View faculty specializations
- **One-Click Refresh** - Update faculty data with a single click
- **Last Updated Timestamp** - See when data was last refreshed
- **Professional UI** - Modern, clean design with wrapped department tabs

## 📋 Tech Stack

### Backend
- **Framework**: Flask
- **Web Server**: Gunicorn
- **Hosting**: Render.com
- **Language**: Python 3.x
- **Libraries**:
  - `requests` - HTTP requests for web scraping
  - `beautifulsoup4` - HTML parsing
  - `flask-cors` - Cross-Origin Resource Sharing
  - `concurrent.futures` - Parallel scraping

### Frontend
- **HTML5** - Semantic markup
- **CSS3** - Modern styling with media queries
- **JavaScript** - Interactive functionality
- **Responsive Design** - Mobile-first approach

## 📁 Project Structure

```
nitap-faculty-scraper/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── Procfile              # Render deployment configuration
└── README.md             # This file
```

## 🔧 Installation & Setup

### Backend Setup (Render)

1. **Create a GitHub Repository**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/YOUR_USERNAME/nitap-faculty-scraper
   git push -u origin main
   ```

2. **Deploy to Render**
   - Visit [render.com](https://render.com)
   - Sign up with GitHub
   - Create new Web Service
   - Connect your GitHub repo
   - Configure:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
     - **Plan**: Free or Pro

3. **Get Your API URL**
   - After deployment, Render provides a URL like: `https://your-app.onrender.com`
   - Your API endpoints:
     - `GET /api/faculty` - Get cached faculty data
     - `POST /api/faculty/refresh` - Refresh live data
     - `GET /api/health` - Health check

### Frontend Setup

Simply open the HTML file in a browser or deploy to any static hosting:
- GitHub Pages
- Netlify
- Vercel
- Any web server

Configure the API URL in the frontend:
```javascript
const backendAPI = "https://your-render-url.onrender.com/api/faculty";
```

## 📖 API Documentation

### Get Faculty Data (Cached)
```
GET /api/faculty

Response:
{
  "status": "success",
  "data": [
    {
      "id": 0,
      "department": "ece",
      "name": "Dr. Erva Rajeswara Reddy",
      "title": "Assistant Professor",
      "image": "http://...",
      "email": "erva@nit.ac.in",
      "number": "+91 9944904249",
      "areas_of_interest": "AI, ML, Blockchain"
    }
  ],
  "count": 150,
  "source": "cache",
  "last_refreshed": "2025-11-10 12:34:56"
}
```

### Refresh Faculty Data (Live Scrape)
```
POST /api/faculty/refresh

Response:
{
  "status": "success",
  "data": [...],
  "count": 150,
  "source": "live",
  "last_refreshed": "2025-11-10 12:50:00",
  "message": "Refreshed! Got 150 faculty"
}
```

### Health Check
```
GET /api/health

Response:
{
  "status": "healthy"
}
```

## 🎯 Usage

### For Users

1. **Open the Website**
   - Visit your deployed frontend URL
   - Faculty data loads from cache instantly

2. **Search Faculty**
   - Type name, title, or department in search box
   - Results filter in real-time

3. **Filter by Department**
   - Click department tab (BIOT, CHEM, CSE, etc.)
   - View faculty in selected department

4. **Refresh Data**
   - Click "🔄 Refresh" button
   - Backend scrapes live data from NIT AP website
   - Wait 30-60 seconds for completion
   - Faculty data updates automatically

5. **View Details**
   - Click on faculty card to see full information
   - Email: Click to send email
   - Phone: Click to call

### For Developers

1. **Local Development**
   ```bash
   # Install dependencies
   pip install -r requirements.txt

   # Run Flask app
   python app.py

   # Access at http://localhost:8000/api/faculty
   ```

2. **Add New Features**
   - Modify `app.py` for backend changes
   - Update frontend HTML/JS/CSS
   - Test locally before deploying

3. **Deploy Updates**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin main
   # Render automatically redeploys
   ```

## 🔄 How It Works

### Data Flow

1. **First User Visit**
   - Website loads
   - Calls `/api/faculty` endpoint
   - Backend loads data from `faculty_cache.json`
   - Data displays instantly (⚡ fast!)

2. **User Clicks Refresh**
   - Website calls `/api/faculty/refresh` endpoint
   - Backend scrapes live from NIT AP website (30-60 sec)
   - Parallel scraping for 10 departments (5 workers)
   - Data saved to `faculty_cache.json`
   - Response sent to frontend
   - UI updates with fresh data

3. **Subsequent Users**
   - Load cached data instantly
   - All users benefit from previous refresh

### Caching Strategy

- **Cache File**: `/tmp/faculty_cache.json`
- **Stores**: Faculty data + timestamp
- **Updated**: Only when user clicks refresh
- **Benefits**:
  - Fast page loads
  - Reduced server load
  - No timeout issues
  - Always available data

## 📱 Responsive Design

- **Desktop (1024px+)**: 4-column grid, full UI
- **Tablet (768px-1023px)**: 2-3 columns, optimized layout
- **Mobile (<768px)**: 1 column, wrapped tabs, touch-friendly
- **Header**: Auto-scales on all devices
- **All Features**: Fully functional on mobile

## 🐛 Troubleshooting

### Issue: Timestamp not showing
**Solution**: Clear browser cache and reload
```bash
# Hard refresh in browser
Ctrl + Shift + R (Windows/Linux)
Cmd + Shift + R (Mac)
```

### Issue: Refresh times out
**Solution**: Check Procfile timeout is set to 300 seconds
```
web: gunicorn --timeout 300 --workers 1 app:app
```

### Issue: No cached data on first load
**Solution**: Click refresh button to generate initial cache

### Issue: CORS errors
**Solution**: Verify `flask-cors` is enabled in `app.py`
```python
from flask_cors import CORS
CORS(app)
```

## 📚 Dependencies

See `requirements.txt`:
- Flask 2.3.3
- requests 2.31.0
- beautifulsoup4 4.12.2
- flask-cors 4.0.0
- gunicorn 21.2.0

## 🚀 Deployment

### Render Deployment Steps

1. Create GitHub repo with: `app.py`, `requirements.txt`, `Procfile`
2. Sign up at [render.com](https://render.com)
3. Connect GitHub account
4. Create Web Service
5. Select repository
6. Set Build & Start commands
7. Deploy!

### Environment Variables (Optional)

No environment variables required for basic setup.

Optional:
```
PORT=8000 (default)
```

## 📞 API Response Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 404 | Not found |
| 500 | Server error |

## 🔐 Data Privacy

- No personal data stored on servers
- Data scraped directly from NIT AP public website
- Cache stored temporarily on server
- CORS enabled for cross-origin requests

## 📊 Performance

- **Initial Load**: <100ms (cached data)
- **Search**: Real-time filtering
- **Refresh**: 30-60 seconds (live scrape)
- **Mobile**: Optimized for all screen sizes

## 🎨 UI Features

- Modern, professional design
- Wrapped department tabs (no horizontal scroll)
- Responsive header with auto-scaling logo
- Touch-friendly buttons and controls
- Smooth transitions and animations
- Clean typography and spacing
- Professional color scheme

## 🔄 Version History

### v1.0.0 (Current)
- Initial release
- Live faculty scraping
- Smart caching system
- Responsive design
- Department filtering
- Search functionality
- Timestamp tracking

## 📝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Commit changes: `git commit -am 'Add feature'`
4. Push to branch: `git push origin feature/your-feature`
5. Submit pull request

## 📄 License

This project is open source and available under the MIT License.

## 👥 Contributors

- Initial Development: Your Team
- Contributor 1
- Contributor 2

## 📧 Support

For issues or questions:
1. Check GitHub Issues
2. Create new issue with description
3. Include browser/device information
4. Attach screenshots if applicable

## 🙏 Acknowledgments

- NIT Andhra Pradesh for faculty data
- Render for hosting
- Open source community for libraries

## 🔗 Links

- **Website**: [Your website URL]
- **Backend API**: https://your-render-url.onrender.com
- **Frontend**: [Your frontend URL]
- **GitHub**: https://github.com/your-username/nitap-faculty-scraper

---

**Last Updated**: November 10, 2025

**Maintained by**: Your Name / Your Team

**Status**: ✅ Active & Maintained