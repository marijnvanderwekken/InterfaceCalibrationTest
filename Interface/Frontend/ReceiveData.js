const ws = new WebSocket("ws://127.0.0.1:8000/ws");
ws.onopen = () => {
    console.log("Connected to server");
};

ws.onmessage = (event) => {
    console.log("Message from server:", event.data);
    const output = document.getElementById("output");
    output.textContent = event.data;
};

ws.onerror = (error) => {
    console.error("error:", error);
};

ws.onclose = () => {
    console.log("connection closed");
};
