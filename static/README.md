# Bible Study Assistant - Web Chat Interface

This directory contains the web-based chat interface for the Bible Study Assistant, adapted from [unfoldingWord/bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine).

**Note:** This is a derived version for web demo purposes. For full documentation on the underlying engine, see the [original repository](https://github.com/unfoldingWord/bt-servant-engine).

## Features

- **Clean, modern UI** - Responsive design that works on desktop and mobile
- **Real-time chat** - Send messages and receive intelligent responses
- **Persistent user sessions** - User ID stored in browser localStorage
- **Typing indicators** - Visual feedback while processing
- **Sample questions** - Quick-start prompts for common queries
- **Error handling** - Graceful error messages and retry capability

## Files

- `index.html` - Single-page web chat application (HTML + CSS + JavaScript)

## Usage

### Access the Chat Interface

Once the server is running, access the chat interface at:

```
http://localhost:8000/
```

The root URL automatically redirects to the chat interface.

### Direct Access

You can also access it directly at:

```
http://localhost:8000/static/index.html
```

## How It Works

1. **User sends a message** - JavaScript captures the input and sends a POST request to `/api/chat/`
2. **Backend processes** - The message goes through the RAG engine and intent routing (same engine as [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine))
3. **Response received** - Assistant's response(s) are displayed in the chat
4. **Session maintained** - User ID and session ID are preserved for context

For details on the intent system and orchestration, see the [bt-servant-engine documentation](https://github.com/unfoldingWord/bt-servant-engine).

## API Integration

The interface communicates with the backend via the `/api/chat/` endpoint:

**Request:**
```json
{
  "message": "Summarize Titus 1",
  "user_id": "unique-user-id",
  "session_id": "session-id"
}
```

**Response:**
```json
{
  "user_id": "unique-user-id",
  "message_id": "message-id",
  "responses": [
    {
      "content": "Titus 1 begins with Paul's greeting...",
      "type": "text"
    }
  ],
  "processing_time_seconds": 2.145,
  "session_id": "session-id"
}
```

## Customization

The interface is self-contained in a single HTML file with embedded CSS and JavaScript. To customize:

- **Colors/Theme** - Modify the CSS variables and gradient colors
**Sample Questions** - Update the `.sample-question` divs in the HTML (currently showing: Summarize Titus 1, Show John 3:16–18, Translation challenges for John 1:1?, Important words in Romans 1)
- **Layout** - Adjust the flexbox layout in the `.chat-container` styles
- **Behavior** - Modify the JavaScript functions for different UX patterns

## Browser Compatibility

Works on all modern browsers:
- Chrome/Edge 90+
- Firefox 88+
- Safari 14+
- Mobile browsers (iOS Safari, Chrome Mobile)

## Technical Details

- **No build step required** - Pure HTML/CSS/JS
- **No external dependencies** - All code is self-contained
- **LocalStorage** - User ID persisted across sessions
- **Fetch API** - Modern HTTP requests
- **ES6+** - Modern JavaScript features

## Future Enhancements

Web-specific improvements (this derived version):
- **Streaming responses** - WebSocket or SSE for real-time streaming
- **Message history** - Persist conversations in browser
- **Bookmarks** - Save favorite passages or answers
- **Study notes** - Annotate and organize findings
- **Dark mode** - Theme toggle
- **Export chat** - Download conversation history

Core engine improvements: Contribute to [bt-servant-engine](https://github.com/unfoldingWord/bt-servant-engine)