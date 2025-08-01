const ws = new WebSocket('ws://localhost:8000/ws/chat/');
ws.onopen = () => {
    console.log('WebSocket connected!');
    ws.send(JSON.stringify({message: 'Hello from browser!'}));
};
ws.onmessage = (event) => {
    console.log('Received:', JSON.parse(event.data));
};
ws.onerror = (error) => console.log('WebSocket error:', error);