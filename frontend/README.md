# 🌐 ASTA3 Voice Biometric - Web Frontend

Beautiful web interface to test your voice verification system!

---

## ✅ Frontend is RUNNING!

**URL**: http://localhost:5173/index.html

---

## 🎨 Features

### ✨ What You Can Do

1. **See System Status** - Real-time server health, model status, profile count
2. **Select Profile** - Choose from ASTA3 or other available profiles
3. **Upload Audio** - Drag & drop or click to select WAV files
4. **Verify** - Test speaker verification with beautiful visual feedback
5. **View Results** - See similarity scores, threshold, and verification status

### 🎯 Visual Feedback

- ✅ **Green** - Verified (same speaker)
- ❌ **Red** - Rejected (different speaker)
- **Score Bar** - Visual representation of similarity
- **Real-time Status** - Auto-refreshes every 10 seconds

---

## 🚀 How to Use

### Step 1: Make Sure Servers are Running

```bash
# Backend (Terminal 1)
cd backend
python main.py
# Should be on: http://localhost:8000

# Frontend (Terminal 2)
cd frontend
python serve.py
# Should be on: http://localhost:5173
```

### Step 2: Open in Browser

Open: **http://localhost:5173/index.html**

### Step 3: Test Verification

1. **Select Profile**: Choose "ASTA3" from dropdown
2. **Select Audio**: Click "Click to select WAV file"
3. **Browse**: Navigate to `../DATA/` folder
4. **Pick a Sample**:
   - ✅ Use `sample_0062.wav` (should VERIFY)
   - ❌ Use `sample_0004.wav` (should REJECT)
5. **Click "Verify Audio"**: See results!

---

## 📁 Test Samples

### ✅ Will VERIFY (Training Samples)

Try these files from the DATA folder:
```
sample_0062.wav  →  Score: ~0.86 ✅
sample_0060.wav  →  Score: ~0.87 ✅
sample_0067.wav  →  Score: ~0.84 ✅
sample_0061.wav  →  Score: ~0.84 ✅
sample_0063.wav  →  Score: ~0.83 ✅
```

Expected: Green result, high score (0.80+)

### ❌ Will REJECT (Different Speakers)

Try these files:
```
sample_0004.wav  →  Score: ~0.23 ❌
sample_0005.wav  →  Score: ~0.20 ❌
sample_0006.wav  →  Score: ~0.39 ❌
```

Expected: Red result, low score (0.15-0.40)

---

## 🖼️ Interface Features

### System Status Card
- Server health indicator
- Model loaded status
- Number of profiles
- Server uptime

### Verification Section
- Profile dropdown selector
- File upload with drag & drop
- Visual file selection feedback
- Verify button (enabled when ready)

### Results Display
- ✅ Verified or ❌ Rejected status
- Similarity score (0-1 range)
- Percentage bar visualization
- Threshold comparison
- Clear success/failure message

### Info Section
- Sample recommendations
- Which files will verify/reject
- Helpful testing tips

---

## 🎨 Design Features

- **Modern gradient design** - Purple/blue theme
- **Responsive layout** - Works on desktop and mobile
- **Smooth animations** - Slide-in results, hover effects
- **Color-coded feedback** - Green for success, red for failure
- **Real-time updates** - Auto-refresh system status
- **Progress indicators** - Loading spinners during verification

---

## 🔧 Technical Details

### Frontend Stack
- **HTML5** - Structure
- **CSS3** - Styling with gradients, animations
- **Vanilla JavaScript** - No frameworks needed
- **Fetch API** - API communication

### API Integration
- Connects to: `http://localhost:8000`
- Endpoints used:
  - `GET /api/health` - System status
  - `GET /api/profiles` - List profiles
  - `POST /api/verify` - Verify audio

### File Upload
- Accepts: `.wav` files only
- Method: `multipart/form-data`
- Auto-validates file selection

---

## 📋 Requirements

- **Backend running** on port 8000
- **Frontend server** on port 5173 (or just open HTML file)
- **Modern browser** (Chrome, Firefox, Edge, Safari)
- **JavaScript enabled**

---

## 🚨 Troubleshooting

### "Server not responding" error

**Solution**: Make sure backend is running
```bash
cd backend
python main.py
```

### Can't select files

**Solution**: Make sure you're using WAV files from the DATA folder

### CORS errors in console

**Solution**: Use the provided `serve.py` server instead of opening HTML directly

### Results not showing

**Solution**: Check browser console (F12) for errors

---

## 🔄 Alternative: Open HTML Directly

If you don't want to run `serve.py`:

1. Open `index.html` directly in browser
2. May have CORS issues
3. Better to use the Python server

---

## 📊 What to Expect

### Successful Verification ✅
```
Profile: ASTA3
Similarity Score: 0.8607 (86.1%)
Threshold: 0.6000
Status: VERIFIED
Message: Speaker identity confirmed! Access granted.
```

### Rejected Verification ❌
```
Profile: ASTA3
Similarity Score: 0.2252 (22.5%)
Threshold: 0.6000
Status: REJECTED
Message: Speaker identity does not match. Access denied.
```

---

## 🎯 Quick Test Workflow

1. **Open**: http://localhost:5173/index.html
2. **Check**: Status should show "HEALTHY" with ASTA3 available
3. **Select**: "ASTA3" profile
4. **Upload**: `sample_0062.wav` from DATA folder
5. **Verify**: Click verify button
6. **Result**: Should see green "VERIFIED" with score ~0.86
7. **Try again**: With `sample_0004.wav`
8. **Result**: Should see red "REJECTED" with score ~0.23

---

## 💡 Tips

- **Test both types**: Try verified and rejected samples
- **Watch the score**: See how different speakers score differently
- **Compare results**: Test multiple samples to see patterns
- **Use training samples**: For reliable verification results
- **Check system status**: Refresh page to update status

---

## 🎉 You're All Set!

Your voice biometric system now has a beautiful web interface!

**Frontend**: http://localhost:5173/index.html  
**Backend**: http://localhost:8000  
**Status**: Both running ✅

Ready to test voice verification! 🎤
