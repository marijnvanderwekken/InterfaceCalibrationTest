document.addEventListener("DOMContentLoaded", () => {
    const clientId = "F1";
    const statusr = document.getElementById("status");
    const wsUrl = `ws://127.0.0.1:8000/ws/${clientId}`;
    let ws = null;

    function connectWebSocket() {
        ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            updateStatus(`Connected to server: ${ws.url}`);
        };

        ws.onmessage = (event) => {
            console.log("Message from server:" + event.data);
            
    
            try {
                const message = JSON.parse(event.data);
                if (message.type_message === "picture") {
                    displayImage(message.data)
                }else if(message.type_message == "status"){
                    const output = document.getElementById("output");
                    output.textContent = message.data;
                }
            } catch (e) {
                console.error("Error parsing message:", e);
            }
        };

        ws.onerror = (error) => {
            updateStatus(`WebSocket error: ${error.message}`);
        };

        ws.onclose = () => {
            updateStatus("Connection closed, reconnecting in 5 seconds...");
            setTimeout(connectWebSocket, 5000);
        };
    }

    function displayImage(base64String) {
        console.log("Message is a picture")
            let img = base64String
            var image = new Image();
            image.src = `data:image/png;base64, ${img}`;
            const imgContainer = document.getElementById("imgContainer");
            imgContainer.innerHTML = "";
            imgContainer.appendChild(image);
            console.log(base64String)
    }

    function sendMessageToServer(message) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message: "command", data: message }));
            updateStatus(`Sent command: ${message}`);
        } else {
            updateStatus("WebSocket is not open");
        }
    }

    function sendStatusUpdate(type, message) {
        if (ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type_message: type, data: message}));
            updateStatus(`Sent message: ${message}`);
        } else {
            updateStatus("WebSocket is not open");
        }
    }
   

    function updateStatus(message) {
        statusr.textContent = message;
        console.log(message);
    }


    window.sendMessageToServer = sendMessageToServer;
    window.sendStatusUpdate = sendStatusUpdate;

    connectWebSocket(); 
});
